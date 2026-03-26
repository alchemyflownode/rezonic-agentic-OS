from abc import ABC, abstractmethod
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class BaseWorker(ABC):
    """
    Abstract base class for all workers
    """
    def __init__(self, name, hive_bus=None):
        self.name = name
        self.hive_bus = hive_bus
        self.status = "initialized"
        self.created_at = datetime.now().isoformat()
        self.last_active = None
        self.task_count = 0
        self.error_count = 0
        
    @abstractmethod
    async def process(self, task, **kwargs):
        """
        Process a task - must be implemented by subclasses
        """
        pass
        
    def get_status(self):
        """
        Get worker status
        """
        return {
            'name': self.name,
            'status': self.status,
            'type': self.__class__.__name__,
            'created_at': self.created_at,
            'last_active': self.last_active,
            'task_count': self.task_count,
            'error_count': self.error_count
        }
        
    async def emit(self, event, data):
        """
        Emit an event to the hive bus
        """
        if self.hive_bus:
            try:
                await self.hive_bus.emit(event, data)
            except Exception as e:
                logger.error(f"Failed to emit event {event}: {e}")
                
    def record_task(self, success=True):
        """
        Record task completion
        """
        self.task_count += 1
        self.last_active = datetime.now().isoformat()
        if not success:
            self.error_count += 1
            
    def health_check(self):
        """
        Check worker health
        """
        return {
            'healthy': self.error_count < self.task_count * 0.1 if self.task_count > 0 else True,
            'status': self.status,
            'task_count': self.task_count,
            'error_count': self.error_count,
            'last_active': self.last_active
        }
        
    async def shutdown(self):
        """
        Clean shutdown of worker
        """
        logger.info(f"Shutting down worker: {self.name}")
        self.status = "shutdown"
