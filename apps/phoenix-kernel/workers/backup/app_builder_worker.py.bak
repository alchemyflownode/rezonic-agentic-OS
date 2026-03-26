import sys
from pathlib import Path

# Add parent directory to path
parent_dir = Path(__file__).parent.parent
if str(parent_dir) not in sys.path:
    sys.path.insert(0, str(parent_dir))
"""App Builder Worker - Application Generation"""

import sys
import asyncio
import logging
from workers.base_worker import BaseWorker

logger = logging.getLogger(__name__)

class AppBuilderWorker(BaseWorker):
    """App builder worker for generating applications"""
    
    def __init__(self, hive_bus=None):
        super().__init__("appbuilder", hive_bus)
        logger.info("   AppBuilderWorker initialized")
    
    async def health_check(self):
        return {"healthy": True, "worker": "appbuilder"}
    
    async def process(self, task):
        """Process app building task"""
        logger.info(f"Building app: {task}")
        return {"content": f"Built: {task}", "worker": "appbuilder"}
    
    async def shutdown(self):
        logger.info("   AppBuilderWorker shutting down")


