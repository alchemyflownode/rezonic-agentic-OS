import sys
from pathlib import Path

# Add parent directory to path
parent_dir = Path(__file__).parent.parent
if str(parent_dir) not in sys.path:
    sys.path.insert(0, str(parent_dir))
"""Agamoto Bridge Worker - External API Integration"""

import sys
import asyncio
import logging
from workers.base_worker import BaseWorker

logger = logging.getLogger(__name__)

class AgamotoBridgeWorker(BaseWorker):
    """Bridge worker for external API connections"""
    
    def __init__(self, hive_bus=None):
        super().__init__("agamato", hive_bus)
        self.connected = False
        logger.info("   AgamotoBridgeWorker initialized")
    
    async def health_check(self):
        return {
            "healthy": True,
            "worker": "agamato",
            "connected": self.connected
        }
    
    async def connect(self, endpoint):
        """Connect to external API"""
        self.connected = True
        logger.info(f"Connected to {endpoint}")
        return {"status": "connected", "endpoint": endpoint}
    
    async def process(self, task):
        """Process through external API"""
        if not self.connected:
            return {"error": "Not connected"}
        return {"content": f"Processed via Agamoto: {task}", "worker": "agamato"}
    
    async def shutdown(self):
        """Shutdown the bridge"""
        self.connected = False
        logger.info("   AgamotoBridgeWorker shutting down")


