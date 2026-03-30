from abc import ABC, abstractmethod
from typing import Dict, Any
import time

class BaseWorker(ABC):
    def __init__(self, name: str, user_id: str):
        self.name = name
        self.user_id = user_id  # ← Critical: tenant scoping
        self.created_at = time.time()
        self.execution_count = 0
        self.error_count = 0
    
    @abstractmethod
    async def execute(self, task: str, **kwargs) -> Dict[str, Any]:
        pass
    
    async def health_check(self) -> Dict:
        return {
            "name": self.name,
            "user_id": self.user_id,  # ← Audit trail
            "status": "healthy",
            "executions": self.execution_count,
            "uptime": time.time() - self.created_at
        }