from base_worker import Worker

class HarvesterWorker(Worker):
    def __init__(self):
        super().__init__("harvester_worker")
    
    async def execute(self, task: str, **kwargs):
        return {
            "success": True,
            "worker": "harvester_worker",
            "message": f"harvester_worker: {task[:100]}"
        }
