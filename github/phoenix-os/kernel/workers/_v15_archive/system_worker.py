try:
    from workers.base_worker import Worker
except ImportError:
    from base_worker import Worker

class SystemWorker(Worker):
    def __init__(self):
        super().__init__("system_worker")
    
    async def execute(self, task: str, **kwargs):
        self.execution_count = getattr(self, "execution_count", 0) + 1
        self.execution_count = self.execution_count
        return {
            "success": True,
            "worker": "system_worker",
            "message": f"system_worker: {task[:100]}"
        }

    async def health_check(self) -> dict:
        """Return worker health status."""
        return {
            "name": self.name,
            "version": getattr(self, "version", "1.0.0"),
            "status": "healthy" if getattr(self, "_initialized", False) else "not_initialized",
            "initialized": getattr(self, "_initialized", False),
            "executions": getattr(self, "execution_count", 0),
            "errors": getattr(self, "error_count", 0),
        }
