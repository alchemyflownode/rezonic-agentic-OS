"""
Execution Worker for Phoenix Coworker

Handles code and command execution in a sandboxed environment.
"""

import subprocess
import tempfile
from pathlib import Path
from typing import Dict, List, Optional, Any
from .base import BaseWorker


class ExecutionWorker(BaseWorker):
    """
    Execution worker for running code and commands.
    
    Provides sandboxed execution with safety checks.
    """
    
    def __init__(self, kernel: Any):
        super().__init__(kernel, "execution")
        
        # Allowed interpreters
        self.allowed_interpreters = {
            "python": "python",
            "python3": "python3",
            "bash": "bash",
            "sh": "sh",
            "node": "node",
        }
        
        # Execution timeout (seconds)
        self.timeout = 30
        
        # Max output size
        self.max_output = 10000
    
    async def run(self):
        """Execution worker doesn't need a continuous loop"""
        while self._running:
            await asyncio.sleep(1)
    
    async def process(self, command: str, context: Dict = None) -> Dict:
        """Process an execution command"""
        context = context or {}
        
        # Check if it's code to execute or a shell command
        if context.get("language"):
            return await self.execute_code(
                context["language"],
                command,
                context.get("timeout", self.timeout)
            )
        else:
            return await self.execute_shell(command, context)
    
    async def execute(self, action: str, parameters: Dict) -> Any:
        """Execute action (for task planner)"""
        if action == "run_command":
            return await self.execute_shell(
                parameters.get("command", ""),
                parameters
            )
        
        elif action == "run_code":
            return await self.execute_code(
                parameters.get("language", "python"),
                parameters.get("code", ""),
                parameters.get("timeout", self.timeout)
            )
        
        return f"[Execution action '{action}' not implemented]"
    
    async def execute_shell(self, command: str, context: Dict = None) -> Dict:
        """
        Execute a shell command.
        
        Args:
            command: The command to execute
            context: Additional context
        
        Returns:
            Execution result
        """
        context = context or {}
        
        # Safety check (already done by kernel, but double-check)
        safe = await self.kernel.safety.check(command, context)
        if safe.risk_level.value == "dangerous":
            return {
                "success": False,
                "error": f"Command blocked: {safe.reason}"
            }
        
        try:
            # Execute with timeout
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=context.get("timeout", self.timeout),
                cwd=context.get("cwd")
            )
            
            stdout = result.stdout[:self.max_output]
            stderr = result.stderr[:self.max_output]
            
            if len(result.stdout) > self.max_output:
                stdout += "\n... (truncated)"
            if len(result.stderr) > self.max_output:
                stderr += "\n... (truncated)"
            
            return {
                "success": result.returncode == 0,
                "returncode": result.returncode,
                "stdout": stdout,
                "stderr": stderr,
                "command": command
            }
        
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "error": f"Command timed out after {self.timeout}s",
                "command": command
            }
        
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "command": command
            }
    
    async def execute_code(
        self,
        language: str,
        code: str,
        timeout: int = None
    ) -> Dict:
        """
        Execute code in a specific language.
        
        Args:
            language: Programming language
            code: Code to execute
            timeout: Execution timeout
        
        Returns:
            Execution result
        """
        timeout = timeout or self.timeout
        
        # Get interpreter
        interpreter = self.allowed_interpreters.get(language.lower())
        if not interpreter:
            return {
                "success": False,
                "error": f"Unsupported language: {language}"
            }
        
        # Create temp file
        suffix = {
            "python": ".py",
            "python3": ".py",
            "bash": ".sh",
            "sh": ".sh",
            "node": ".js",
        }.get(language.lower(), ".txt")
        
        try:
            with tempfile.NamedTemporaryFile(
                mode='w',
                suffix=suffix,
                delete=False
            ) as f:
                f.write(code)
                temp_path = f.name
            
            # Execute
            result = subprocess.run(
                [interpreter, temp_path],
                capture_output=True,
                text=True,
                timeout=timeout
            )
            
            # Cleanup
            Path(temp_path).unlink(missing_ok=True)
            
            stdout = result.stdout[:self.max_output]
            stderr = result.stderr[:self.max_output]
            
            return {
                "success": result.returncode == 0,
                "returncode": result.returncode,
                "stdout": stdout,
                "stderr": stderr,
                "language": language
            }
        
        except subprocess.TimeoutExpired:
            Path(temp_path).unlink(missing_ok=True)
            return {
                "success": False,
                "error": f"Code execution timed out after {timeout}s"
            }
        
        except Exception as e:
            Path(temp_path).unlink(missing_ok=True)
            return {
                "success": False,
                "error": str(e)
            }
    
    async def execute_python(self, code: str, context: Dict = None) -> Dict:
        """Execute Python code with access to context"""
        context = context or {}
        
        # Create execution context
        exec_globals = {
            "__builtins__": __builtins__,
            "kernel": self.kernel,
            "context": context,
            "result": None
        }
        
        # Add safe imports
        safe_modules = [
            "json", "os", "sys", "pathlib", "datetime", 
            "re", "math", "random", "statistics", "itertools",
            "collections", "typing", "hashlib", "base64"
        ]
        
        for mod in safe_modules:
            try:
                exec_globals[mod] = __import__(mod)
            except ImportError:
                pass
        
        try:
            # Execute code
            exec(code, exec_globals)
            
            return {
                "success": True,
                "result": exec_globals.get("result"),
                "output": exec_globals.get("output")
            }
        
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "error_type": type(e).__name__
            }
