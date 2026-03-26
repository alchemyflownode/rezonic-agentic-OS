from base_worker import Worker

class CortexWorker(Worker):
    def __init__(self):
        super().__init__("cortex_worker")
    
    async def execute(self, task: str, **kwargs):
        return {
            "success": True,
            "worker": "cortex_worker",
            "message": f"cortex_worker: {task[:100]}"
        }
