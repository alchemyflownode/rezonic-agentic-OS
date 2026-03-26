from base_worker import Worker

class Ps1Router(Worker):
    def __init__(self):
        super().__init__("ps1_router")
    
    async def execute(self, task: str, **kwargs):
        return {
            "success": True,
            "worker": "ps1_router",
            "message": f"ps1_router: {task[:100]}"
        }
