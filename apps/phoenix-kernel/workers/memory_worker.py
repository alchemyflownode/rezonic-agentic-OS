from base_worker import Worker

class MemoryWorker(Worker):
    def __init__(self):
        super().__init__("memory_worker")
    
    async def execute(self, task: str, **kwargs):
        return {"success": True, "message": f"memory_worker: {task[:100]}"}
