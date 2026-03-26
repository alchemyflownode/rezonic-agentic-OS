class BaseWorker:
    '''Base class for all workers providing common functionality'''
    
    def __init__(self):
        self.name = self.__class__.__name__
        
    async def process(self, task: str) -> dict:
        '''Process a task - override in child classes'''
        return {"result": f"{self.name} processing: {task}"}
        
    def validate(self, task: str) -> bool:
        '''Validate task before processing'''
        return True
        
    def get_status(self) -> dict:
        '''Get worker status'''
        return {
            "name": self.name,
            "active": True,
            "tasks_processed": 0
        }
