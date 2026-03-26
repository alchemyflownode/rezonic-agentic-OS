class BaseWorker:
    '''Base class for all workers'''
    
    def __init__(self):
        self.name = self.__class__.__name__
        
    async def process(self, task: str) -> dict:
        return {"result": f"{self.name} processing: {task}"}
