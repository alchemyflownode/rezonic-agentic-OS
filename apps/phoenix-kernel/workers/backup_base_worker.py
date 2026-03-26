# backend/workers/base_worker.py
from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)

class BaseWorker:
    """The genetic base class empowering all workers with Hive Mind telepathy."""
    
    def __init__(self, name: str):
        self.name = name
        self.memory_bus = None
        
    def set_memory_bus(self, memory_bus):
        self.memory_bus = memory_bus

    async def publish(self, content: str, metadata: Optional[Dict] = None):
        """Broadcast a thought to the entire OS"""
        if self.memory_bus:
            return await self.memory_bus.write(
                worker=self.name,
                task="broadcast",
                content=content,
                metadata=metadata
            )
            
    async def search_context(self, query: str, limit: int = 3, worker_filter: str = None) -> List[str]:
        """Read the recent thoughts of other workers"""
        if self.memory_bus:
            results = await self.memory_bus.search(query=query, limit=limit, worker_filter=worker_filter)
            return results
        return[]

    async def process(self, task: str, memory_bus=None):
        """Process task – auto-generated stub"""
        return {"content": f"Processed: {task[:50]}", "worker": self.name}
    
    async def health_check(self):
        """Return worker health status"""
        return {"worker": self.name, "status": "healthy", "timestamp": __import__('time').time()}
