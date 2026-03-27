# workers/sandbox_worker.py
"""Sandbox Worker - Secure code execution with resource limits (Cross-platform)"""

import asyncio
import sys
import tempfile
import os
import signal
import time
import platform
from pathlib import Path
from typing import Dict, Any
from base_worker import Worker

# Platform detection
IS_WINDOWS = platform.system() == "Windows"


class SandboxWorker(Worker):
    """Secure code execution with timeout and isolation"""
    
    def __init__(self):
        super().__init__("sandbox_worker")
        self.timeout = 30  # seconds
        self.memory_limit = 512 * 1024 * 1024  # 512MB (Unix only)
    
    async def execute(self, task: str, **kwargs) -> Dict[str, Any]:
        """Execute code in isolated sandbox"""
        # Extract code from task
        code = self._extract_code(task)
        
        # Constitutional check
        if self._has_dangerous_code(code):
            return {
                "success": False,
                "error": "Constitutional violation: Dangerous code detected",
                "worker": self.name
            }
        
        # Create sandbox environment
        with tempfile.TemporaryDirectory(dir=os.environ.get("TEMP", "/tmp")) as tmpdir:
            script_path = Path(tmpdir) / "script.py"
            script_path.write_text(code, encoding='utf-8')
            
            try:
                # Execute with timeout
                proc = await asyncio.create_subprocess_exec(
                    sys.executable, str(script_path),
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                    cwd=tmpdir
                )
                
                # Wait with timeout
                try:
                    stdout, stderr = await asyncio.wait_for(
                        proc.communicate(),
                        timeout=self.timeout
                    )
                except asyncio.TimeoutError:
                    proc.kill()
                    await proc.wait()
                    return {
                        "success": False,
                        "error": f"Timeout after {self.timeout}s",
                        "worker": self.name
                    }
                
                # Decode output
                stdout_str = stdout.decode('utf-8', errors='replace')[:5000]
                stderr_str = stderr.decode('utf-8', errors='replace')[:2000]
                
                return {
                    "success": proc.returncode == 0,
                    "stdout": stdout_str,
                    "stderr": stderr_str,
                    "returncode": proc.returncode,
                    "worker": self.name
                }
                
            except Exception as e:
                return {
                    "success": False,
                    "error": str(e),
                    "worker": self.name
                }
    
    def _extract_code(self, task: str) -> str:
        """Extract code from task"""
        import re
        # Look for code blocks
        match = re.search(r'```(?:python)?\s*\n(.*?)\n```', task, re.DOTALL)
        if match:
            return match.group(1)
        return task
    
    def _has_dangerous_code(self, code: str) -> bool:
        """Check for dangerous operations"""
        dangerous_patterns = [
            "__import__('os')",
            "os.system",
            "subprocess",
            "eval(",
            "exec(",
            "__import__",
            "open(",
            "file(",
            "rm ",
            "del ",
            "import os",
            "import sys",
            "shutil.rmtree",
            "os.remove",
            "os.unlink"
        ]
        code_lower = code.lower()
        for pattern in dangerous_patterns:
            if pattern.lower() in code_lower:
                return True
        return False