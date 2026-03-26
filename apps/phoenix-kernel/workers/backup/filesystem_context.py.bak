import sys
from pathlib import Path

# Add parent directory to path
parent_dir = Path(__file__).parent.parent
if str(parent_dir) not in sys.path:
    sys.path.insert(0, str(parent_dir))
"""Filesystem Context Worker"""

import sys
import asyncio
import logging
import os
from pathlib import Path
from workers.base_worker import BaseWorker

logger = logging.getLogger(__name__)

class FilesystemContextWorker(BaseWorker):
    """Filesystem worker for context operations"""
    
    def __init__(self, hive_bus=None):
        super().__init__("filesystem", hive_bus)
        logger.info("   FilesystemContextWorker initialized")
    
    async def health_check(self):
        return {"healthy": True, "worker": "filesystem"}
    
    async def process(self, path):
        """Process filesystem context"""
        logger.info(f"Processing path: {path}")
        return {"content": f"Scanned: {path}", "worker": "filesystem"}
    
    async def shutdown(self):
        logger.info("   FilesystemContextWorker shutting down")


