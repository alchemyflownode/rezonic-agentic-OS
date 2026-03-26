import sys
from pathlib import Path

# Add parent directory to path
parent_dir = Path(__file__).parent.parent
if str(parent_dir) not in sys.path:
    sys.path.insert(0, str(parent_dir))
"""Rez Scanner Worker - Code Analysis"""

import sys
import asyncio
import logging
import ast
import hashlib
from pathlib import Path
from workers.base_worker import BaseWorker

logger = logging.getLogger(__name__)

class RezScannerWorker(BaseWorker):
    """Scanner worker for code analysis and AST parsing"""
    
    def __init__(self, hive_bus=None):
        super().__init__("rez_scanner", hive_bus)
        self.ignored_dirs = {'.git', '__pycache__', 'node_modules', 'venv', 'env', '.next'}
        logger.info("  ðŸ” RezScannerWorker initialized")
    
    async def health_check(self):
        return {"healthy": True, "worker": "rez_scanner"}
    
    async def process(self, path):
        """Scan a path for code analysis"""
        logger.info(f"Scanning: {path}")
        return {"content": f"Scanned: {path}", "worker": "rez_scanner"}
    
    async def shutdown(self):
        """Shutdown the worker"""
        logger.info("  ðŸ” RezScannerWorker shutting down")


