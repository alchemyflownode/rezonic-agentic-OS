import sys
from pathlib import Path

# Add parent directory to path
parent_dir = Path(__file__).parent.parent
if str(parent_dir) not in sys.path:
    sys.path.insert(0, str(parent_dir))
"""RezStack Worker - Stack Orchestration"""

import sys
import asyncio
import logging
from workers.base_worker import BaseWorker

logger = logging.getLogger(__name__)

class RezStackWorker(BaseWorker):
    """Stack worker for orchestration"""
    
    def __init__(self, hive_bus=None):
        super().__init__("rezstack", hive_bus)
        self.stack = []
        logger.info("   RezStackWorker initialized")
    
    async def health_check(self):
        return {
            "healthy": True,
            "worker": "rezstack",
            "stack_size": len(self.stack)
        }
    
    async def process(self, task):
        """Process a stack operation"""
        logger.info(f"Processing stack task: {task}")
        self.stack.append(task)
        return {
            "content": f"Stack size: {len(self.stack)}",
            "worker": "rezstack"
        }
    
    async def shutdown(self):
        logger.info("   RezStackWorker shutting down")


