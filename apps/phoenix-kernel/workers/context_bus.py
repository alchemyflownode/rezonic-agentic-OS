from base_worker import Worker

class ContextBus(Worker):
    def __init__(self):
        super().__init__("context_bus")
    
    async def execute(self, task: str, **kwargs):
        return {
            "success": True,
            "worker": "context_bus",
            "message": f"context_bus: {task[:100]}"
        }
