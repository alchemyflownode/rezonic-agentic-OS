from base_worker import Worker

class ExchangeWorker(Worker):
    def __init__(self):
        super().__init__("exchange_worker")
    
    async def execute(self, task: str, **kwargs):
        return {
            "success": True,
            "worker": "exchange_worker",
            "message": f"exchange_worker: {task[:100]}"
        }
