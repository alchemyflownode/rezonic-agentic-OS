from base_worker import Worker

class ConstitutionalEvaluator(Worker):
    def __init__(self):
        super().__init__("constitutional_evaluator")
    
    async def execute(self, task: str, **kwargs):
        return {
            "success": True,
            "worker": "constitutional_evaluator",
            "message": f"constitutional_evaluator: {task[:100]}"
        }
