"""Brain Worker - General AI processing"""

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

class BrainWorker(Worker):
    """General purpose AI worker"""
    
    def __init__(self, config: Optional[WorkerConfig] = None):
        super().__init__(config)
        self.name = "brain"
        self.description = "General AI Processing"
        self.is_ready = True
    
    async def execute(self, task: str, **kwargs) -> Dict[str, Any]:
        """Process with AI"""
        self.log("info", f"Processing: {task[:50]}...")
        await asyncio.sleep(0.3)
        
        return {
            "status": "success",
            "worker": self.name,
            "content": f"Processed: {task[:50]}...",
            "model": "llama3.2"
        }
    
    async def validate(self, task: str) -> bool:
        """Always returns True - brain handles everything"""
        return True

BrainWorker_CONFIG = {
    "name": "brain",
    "enabled": True,
    "max_concurrent": 10,
    "timeout": 60,
    "requires_gpu": True
}
