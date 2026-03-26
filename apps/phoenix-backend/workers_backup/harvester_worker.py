import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
"""Harvester Worker - Ingests ChatGPT/Claude exports"""

import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

class HarvesterWorker:
    """The Soul Eater - Ingests chat exports into the Hive"""
    
    def __init__(self, memory_bus=None):
        self.memory_bus = memory_bus
        
    def set_memory_bus(self, memory_bus):
        self.memory_bus = memory_bus
        
    async def process(self, task: str, model: str = None, memory_bus=None) -> dict:
        if memory_bus:
            self.set_memory_bus(memory_bus)
            
        if task.startswith('/harvest'):
            return {"content": "? Harvester ready for your ChatGPT export!"}
        return {"content": "?? Use /harvest <path> to ingest chat history"}


    async def process(self, task: str, memory_bus=None):
        """Process task – auto-generated stub"""
        return {"content": f"Processed: {task[:50]}", "worker": self.name}
    
    async def health_check(self):
        """Return worker health status"""
        return {"worker": self.name, "status": "healthy", "timestamp": __import__('time').time()}

