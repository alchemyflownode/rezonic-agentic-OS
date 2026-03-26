"""
Worker Registry for Phoenix
"""
class WorkerRegistry:
    def __init__(self):
        self.workers = {}
    
    def register(self, name, worker):
        self.workers[name] = worker
        print(f"  ? Registered: {name}")
    
    def get(self, name):
        return self.workers.get(name)
    
    def list(self):
        return list(self.workers.keys())
    
    def count(self):
        return len(self.workers)
