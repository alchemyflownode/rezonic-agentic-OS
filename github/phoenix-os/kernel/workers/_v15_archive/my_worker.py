# workers/my_worker.py
import logging
from workers.base_worker import Worker

class MyWorker(Worker):
    """Custom worker for specific functionality."""
    
    def __init__(self):
        super().__init__(
            name="my_worker",
            description="Does something amazing",
            capabilities=["task1", "task2"]
        )
        self.logger = logging.getLogger(__name__)
    
    async def execute(self, task: str, **kwargs) -> dict:
        """
        Execute the worker task.
        
        Args:
            task: Natural language task description
            **kwargs: Additional parameters
            
        Returns:
            Dictionary with execution results
        """
        try:
            # Your logic here
            result = self._process_task(task, **kwargs)
            
            return {
                "success": True,
                "result": result,
                "metadata": {"worker": self.name}
            }
        except Exception as e:
            self.logger.error(f"Worker execution failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "metadata": {"worker": self.name}
            }
    
    def _process_task(self, task: str, **kwargs):
        """Internal processing logic."""
        # Implement your functionality
        return f"Processed: {task}"