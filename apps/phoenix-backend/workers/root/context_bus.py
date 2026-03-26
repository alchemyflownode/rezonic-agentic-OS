import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
# backend/workers/context_bus.py
import hashlib
import time
from typing import Optional, List
import logging
import json

logger = logging.getLogger(__name__)

class HiveMemoryBus:
    """Sovereign Context Bus: L1=Cache/Chroma, L2=VFS"""
    def __init__(self, chroma_worker=None, vfs_worker=None):
        self.chroma = chroma_worker
        self.vfs = vfs_worker
        self.recent_cache =[]
        
    def _make_key(self, task: str, worker: str) -> str:
        raw = f"{worker}:{task}:{time.time()}"
        return hashlib.sha256(raw.encode()).hexdigest()[:12]
    
    async def write(self, worker: str, task: str, content: str, metadata: dict = None):
        key = self._make_key(task, worker)
        entry = {
            "worker": worker, 
            "content": content, 
            "timestamp": time.time(), 
            "key": key, 
            "metadata": metadata or {}
        }
        
        # 1. Fast L1 Cache
        self.recent_cache.append(entry)
        if len(self.recent_cache) > 20:
            self.recent_cache.pop(0)
            
        # 2. VFS Persistence
        if self.vfs and hasattr(self.vfs, 'write_context'):
            path = f"/memory/hive_{key}.json"
            try:
                self.vfs.write_context(path, json.dumps(entry))
            except Exception as e:
                logger.warning(f"Failed to write to VFS: {e}")
            
        # 3. Chroma Semantic (If available)
        if self.chroma and hasattr(self.chroma, 'add'):
            try:
                await self.chroma.add(
                    documents=[content], 
                    metadatas=[{"worker": worker}], 
                    ids=[key]
                )
            except Exception:
                pass
                
        return key

    async def search(self, query: str, limit: int = 3, worker_filter: str = None) -> List[str]:
        results =[]
        # Check hot cache first
        for item in reversed(self.recent_cache):
            if worker_filter and item["worker"] != worker_filter: 
                continue
            if not query or query.lower() in item["content"].lower():
                results.append(item["content"])
                if len(results) >= limit: 
                    return results
        return results

    async def process(self, task: str, memory_bus=None):
        """Process task – auto-generated stub"""
        return {"content": f"Processed: {task[:50]}", "worker": self.name}
    
    async def health_check(self):
        """Return worker health status"""
        return {"worker": self.name, "status": "healthy", "timestamp": __import__('time').time()}


    async def store(self, *args, **kwargs):
        """Alias for publish() – maintains compatibility with older workers"""
        return await self.publish(*args, **kwargs)

