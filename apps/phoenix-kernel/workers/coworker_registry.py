from base_worker import Worker

class CoworkerRegistry(Worker):
    def __init__(self):
        super().__init__("coworker_registry")
    
    async def execute(self, task: str, **kwargs):
        return {
            "success": True,
            "worker": "coworker_registry",
            "message": f"coworker_registry: {task[:100]}"
        }
