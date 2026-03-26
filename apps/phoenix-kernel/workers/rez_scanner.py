from base_worker import Worker

class RezScanner(Worker):
    def __init__(self):
        super().__init__("rez_scanner")
    
    async def execute(self, task: str, **kwargs):
        return {
            "success": True,
            "worker": "rez_scanner",
            "message": f"rez_scanner: {task[:100]}"
        }
