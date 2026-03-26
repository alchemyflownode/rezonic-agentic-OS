from base_worker import Worker

class BacktestEngine(Worker):
    def __init__(self):
        super().__init__("backtest_engine")
    
    async def execute(self, task: str, **kwargs):
        return {
            "success": True,
            "worker": "backtest_engine",
            "message": f"backtest_engine: {task[:100]}"
        }
