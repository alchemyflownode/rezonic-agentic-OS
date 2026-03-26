# workers/base_worker.py
"""
Base Worker Module - Must be importable by all workers
"""

from abc import ABC, abstractmethod
from typing import Dict, Any


class Worker(ABC):
    """Base class for all workers"""
    
    def __init__(self, name: str):
        self.name = name
        self.version = "1.0.0"
        
    @abstractmethod
    async def execute(self, task: str, **kwargs) -> Dict[str, Any]:
        """Execute the worker's main functionality"""
        pass
    
    async def health_check(self) -> Dict[str, Any]:
        """Check worker health"""
        return {
            "name": self.name,
            "version": self.version,
            "status": "healthy"
        }


class BaseWorker(Worker):
    """Alias for Worker - for backward compatibility"""
    pass