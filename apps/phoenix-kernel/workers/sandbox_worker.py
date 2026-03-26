from base_worker import Worker

class SandboxWorker(Worker):
    def __init__(self):
        super().__init__("sandbox_worker")
    
    async def execute(self, task: str, **kwargs):
        return {
            "success": True,
            "worker": "sandbox_worker",
            "message": f"sandbox_worker: {task[:100]}"
        }
