"""Base Worker - All workers inherit from this"""
import time

class BaseWorker:
    def __init__(self, name, hive_bus=None):
        self.name = name
        self.hive_bus = hive_bus
        self.start_time = time.time()
    
    async def health_check(self):
        return {"healthy": True, "worker": self.name, "uptime": time.time() - self.start_time}
    
    async def process(self, task):
        return {"content": f"Processing in {self.name}: {task}"}
