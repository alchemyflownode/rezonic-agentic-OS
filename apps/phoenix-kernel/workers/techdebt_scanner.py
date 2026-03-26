from base_worker import Worker

class TechdebtScanner(Worker):
    def __init__(self):
        super().__init__("techdebt_scanner")
    
    async def execute(self, task: str, **kwargs):
        return {
            "success": True,
            "worker": "techdebt_scanner",
            "message": f"techdebt_scanner: {task[:100]}"
        }
