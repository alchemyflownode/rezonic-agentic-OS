from base_worker import Worker

class RezstackWorker(Worker):
    def __init__(self):
        super().__init__("rezstack_worker")
    
    async def execute(self, task: str, **kwargs):
        return {
            "success": True,
            "worker": "rezstack_worker",
            "message": f"rezstack_worker: {task[:100]}"
        }
