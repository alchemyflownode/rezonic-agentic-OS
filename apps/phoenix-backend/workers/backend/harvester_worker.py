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
            return {"content": "✅ Harvester ready for your ChatGPT export!"}
        return {"content": "🌾 Use /harvest <path> to ingest chat history"}
