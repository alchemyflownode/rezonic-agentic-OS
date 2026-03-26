from base_worker import Worker

class BacktestWorker(Worker):
    def __init__(self):
        super().__init__("backtest_worker")
    
    async def execute(self, task: str, **kwargs):
        return {"success": True, "message": f"backtest_worker: {task[:100]}"}
