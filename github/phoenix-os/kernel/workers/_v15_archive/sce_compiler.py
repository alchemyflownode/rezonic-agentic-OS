"""SCE Compiler Worker"""

import asyncio
import json
import hashlib
import sys
from pathlib import Path
from typing import Dict, Any, Optional

# Add paths
parent_dir = Path(__file__).parent.parent
if str(parent_dir) not in sys.path:
    sys.path.insert(0, str(parent_dir))

try:
    from workers.base_worker import Worker, WorkerConfig
except ImportError:
    # Fallback
    from abc import ABC, abstractmethod
    class WorkerConfig:
        def __init__(self, name, **kwargs): self.name = name
    class Worker(ABC):
        def __init__(self, config=None): self.name = config.name if config else "unknown"
        @abstractmethod
        async def execute(self, task, **kwargs): pass

class SCECompiler(Worker):
    """Sovereign Creative Engine Compiler"""
    
    def __init__(self, config: Optional[WorkerConfig] = None):
        super().__init__(config)
        self.name = "sce_compiler"
        self.description = "SCE Protocol Compiler"
        self.is_ready = True
    
    async def execute(self, task: str, **kwargs) -> Dict[str, Any]:
        """Execute compilation"""
        self.log("info", f"Compiling: {task[:50]}...")
        
        # Parse or generate protocol
        try:
            protocol = json.loads(task)
        except:
            protocol = self._generate_protocol(task)
        
        # Simulate compilation
        await asyncio.sleep(0.5)
        
        return {
            "status": "success",
            "worker": self.name,
            "content": f"Compiled SCE protocol with {len(protocol.get('segments', []))} segments",
            "protocol": protocol
        }
    
    async def validate(self, task: str) -> bool:
        """Validate if task can be handled"""
        try:
            data = json.loads(task)
            return isinstance(data, dict) and ('meta' in data or 'segments' in data)
        except:
            keywords = ['sce', 'protocol', 'compile', 'render']
            return any(kw in task.lower() for kw in keywords)
    
    def _generate_protocol(self, task: str) -> dict:
        """Generate a simple protocol"""
        return {
            "meta": {"name": f"Generated: {task[:30]}", "version": "1.0.0"},
            "segments": [
                {"id": 1, "title": "Intro", "duration": 5},
                {"id": 2, "title": "Main", "duration": 10},
                {"id": 3, "title": "Outro", "duration": 5}
            ]
        }

# Worker configuration for auto-loading
SCECompiler_CONFIG = {
    "name": "sce_compiler",
    "enabled": True,
    "max_concurrent": 3,
    "timeout": 120,
    "requires_gpu": False
}
