import sys
from pathlib import Path

# Add parent directory to path
parent_dir = Path(__file__).parent.parent
if str(parent_dir) not in sys.path:
    sys.path.insert(0, str(parent_dir))
"""Hands Worker - Terminal Execution"""

import sys
import asyncio
import logging
from workers.base_worker import BaseWorker

logger = logging.getLogger(__name__)

class HandsWorker(BaseWorker):
    """Hands worker for terminal execution"""
    
    def __init__(self, hive_bus=None):
        super().__init__("hands", hive_bus)
        logger.info("   HandsWorker initialized")
    
    async def health_check(self):
        return {"healthy": True, "worker": "hands"}
    
    async def process(self, command):
        """Process a terminal command"""
        logger.info(f"Processing command: {command}")
        return {"output": f"Executed: {command}", "worker": "hands"}
    
    async def shutdown(self):
        logger.info("   HandsWorker shutting down")


