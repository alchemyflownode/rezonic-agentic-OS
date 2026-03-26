from base_worker import Worker

class ConstitutionalWorker(Worker):
    def __init__(self):
        super().__init__("constitutional_worker")
    
    async def execute(self, task: str, **kwargs):
        return {
            "success": True,
            "worker": "constitutional_worker",
            "message": f"constitutional_worker: {task[:100]}"
        }
