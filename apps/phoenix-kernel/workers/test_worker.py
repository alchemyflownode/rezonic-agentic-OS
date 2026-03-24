"""Test worker for verification"""

import asyncio
import sys
from pathlib import Path
from typing import Dict, Any, Optional

parent_dir = Path(__file__).parent.parent
if str(parent_dir) not in sys.path:
    sys.path.insert(0, str(parent_dir))

try:
    from workers.base_worker import Worker, WorkerConfig
except ImportError:
    from abc import ABC, abstractmethod
    class WorkerConfig:
        def __init__(self, name, **kwargs): self.name = name
    class Worker(ABC):
        def __init__(self, config=None): self.name = config.name if config else "unknown"
        @abstractmethod
        async def execute(self, task, **kwargs): pass

class TestWorker(Worker):
    """Simple test worker"""
    
    def __init__(self, config: Optional[WorkerConfig] = None):
        super().__init__(config)
        self.name = "test_worker"
        self.description = "Test Worker"
        self.is_ready = True
    
    async def execute(self, task: str, **kwargs) -> Dict[str, Any]:
        """Echo the task"""
        self.log("info", f"Test received: {task[:30]}...")
        return {
            "status": "success",
            "worker": self.name,
            "content": f"Test worker received: {task}"
        }
    
    async def validate(self, task: str) -> bool:
        """Always returns True for testing"""
        return True

TestWorker_CONFIG = {
    "name": "test_worker",
    "enabled": True
}
