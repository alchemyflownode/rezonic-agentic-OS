"""Rez Scanner Worker - Code Analysis"""

import sys
import asyncio
import logging
import ast
import hashlib
from pathlib import Path
from base_worker import BaseWorker

logger = logging.getLogger(__name__)

class RezScannerWorker(BaseWorker):
    """Scanner worker for code analysis and AST parsing"""
    
    def __init__(self, hive_bus=None):
        super().__init__("rez_scanner", hive_bus)
        self.ignored_dirs = {'.git', '__pycache__', 'node_modules', 'venv', 'env', '.next'}
        logger.info("  🔍 RezScannerWorker initialized")
    
    async def health_check(self):
        return {"healthy": True, "worker": "rez_scanner"}
    
    async def process(self, path):
        """Scan a path for code analysis"""
        logger.info(f"Scanning: {path}")
        return {"content": f"Scanned: {path}", "worker": "rez_scanner"}
    
    async def shutdown(self):
        """Shutdown the worker"""
        logger.info("  🔍 RezScannerWorker shutting down")
