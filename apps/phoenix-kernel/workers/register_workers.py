from base_worker import Worker

class RegisterWorkers(Worker):
    def __init__(self):
        super().__init__("register_workers")
    
    async def execute(self, task: str, **kwargs):
        return {
            "success": True,
            "worker": "register_workers",
            "message": f"register_workers: {task[:100]}"
        }
