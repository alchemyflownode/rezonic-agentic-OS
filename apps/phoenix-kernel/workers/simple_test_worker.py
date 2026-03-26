from base_worker import Worker

class SimpleTestWorker(Worker):
    def __init__(self):
        super().__init__("simple_test_worker")
    
    async def execute(self, task: str, **kwargs):
        return {
            "success": True,
            "worker": "simple_test_worker",
            "message": f"simple_test_worker: {task[:100]}"
        }
