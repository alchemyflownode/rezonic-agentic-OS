from base_worker import Worker

class CanvasWorker(Worker):
    def __init__(self):
        super().__init__("canvas_worker")
    
    async def execute(self, task: str, **kwargs):
        return {
            "success": True,
            "worker": "canvas_worker",
            "message": f"canvas_worker: {task[:100]}"
        }
