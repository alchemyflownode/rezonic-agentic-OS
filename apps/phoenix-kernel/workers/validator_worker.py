from base_worker import Worker

class ValidatorWorker(Worker):
    def __init__(self):
        super().__init__("validator_worker")
    
    async def execute(self, task: str, **kwargs):
        return {"success": True, "message": f"validator_worker: {task[:100]}"}
