# workers/code_execution_worker.py
"""Code Execution Worker - Sandboxed Python execution"""

from sandbox_worker import SandboxWorker


class CodeExecutionWorker(SandboxWorker):
    """Execute Python code in isolated sandbox"""
    
    def __init__(self):
        super().__init__()
        self.name = "code_execution"
        self.description = "Sandboxed Python code execution with resource limits"
    
    async def execute(self, task: str, **kwargs) -> dict:
        """Execute code with sandbox isolation"""
        # Extract code from task
        code = self._extract_code(task)
        
        # Constitutional check
        if self._has_dangerous_code(code):
            return {
                "success": False,
                "error": "Constitutional violation: Dangerous code detected",
                "worker": self.name
            }
        
        # Run in sandbox
        result = await super().execute(code, **kwargs)
        result["worker"] = self.name
        return result