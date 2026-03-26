import sys
from pathlib import Path

# Add parent directory to path
parent_dir = Path(__file__).parent.parent
if str(parent_dir) not in sys.path:
    sys.path.insert(0, str(parent_dir))
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
import logging
logger = logging.getLogger(__name__)

class DreamWorker:
    def __init__(self, memory_bus=None):
        self.memory_bus = memory_bus
        
    def set_memory_bus(self, memory_bus):
        self.memory_bus = memory_bus
        
    async def process(self, task, model=None, memory_bus=None):
        return {'content': '?? DreamWorker ready. Use /dream to evolve strategies.'}


    async def process(self, task: str, memory_bus=None):
        """Process task â€“ auto-generated stub"""
        return {"content": f"Processed: {task[:50]}", "worker": self.name}
    
    async def health_check(self):
        """Return worker health status"""
        return {"worker": self.name, "status": "healthy", "timestamp": __import__('time').time()}


