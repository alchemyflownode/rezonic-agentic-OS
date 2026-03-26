from base_worker import Worker

class PaperTraderWorker(Worker):
    def __init__(self):
        super().__init__("paper_trader_worker")
    
    async def execute(self, task: str, **kwargs):
        return {"success": True, "message": f"paper_trader_worker: {task[:100]}"}
