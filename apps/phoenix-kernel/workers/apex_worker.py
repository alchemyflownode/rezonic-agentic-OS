from base_worker import Worker

class ApexWorker(Worker):
    def __init__(self):
        super().__init__("apex_worker")
    
    async def execute(self, task: str, **kwargs):
        return {
            "success": True,
            "worker": "apex_worker",
            "message": f"apex_worker: {task[:100]}"
        }
