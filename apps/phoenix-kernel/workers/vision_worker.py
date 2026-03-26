from base_worker import Worker

class VisionWorker(Worker):
    def __init__(self):
        super().__init__("vision_worker")
    
    async def execute(self, task: str, **kwargs):
        return {"success": True, "message": f"vision_worker: {task[:100]}"}
