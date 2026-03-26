from base_worker import Worker

class HandsWorker(Worker):
    def __init__(self):
        super().__init__("hands_worker")
    
    async def execute(self, task: str, **kwargs):
        return {
            "success": True,
            "worker": "hands_worker",
            "message": f"hands_worker: {task[:100]}"
        }
