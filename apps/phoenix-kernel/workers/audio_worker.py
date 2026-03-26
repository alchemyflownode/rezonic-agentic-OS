from base_worker import Worker

class AudioWorker(Worker):
    def __init__(self):
        super().__init__("audio_worker")
    
    async def execute(self, task: str, **kwargs):
        return {
            "success": True,
            "worker": "audio_worker",
            "message": f"audio_worker: {task[:100]}"
        }
