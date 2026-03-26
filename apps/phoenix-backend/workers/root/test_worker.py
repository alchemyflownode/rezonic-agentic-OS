"""Simple test worker"""
from workers.base_worker import BaseWorker

class TestWorker(BaseWorker):
    def __init__(self):
        super().__init__("test")
    
    async def process(self, task, context=None):
        return {"content": f"Test worker says: {task}"}
