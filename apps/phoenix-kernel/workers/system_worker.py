from base_worker import Worker

class SystemWorker(Worker):
    def __init__(self):
        super().__init__("system_worker")
    
    async def execute(self, task: str, **kwargs):
        return {
            "success": True,
            "worker": "system_worker",
            "message": f"system_worker: {task[:100]}"
        }
