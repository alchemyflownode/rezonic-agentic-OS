# workers/memory_worker.py
"""Memory Worker - Interface to Rezhive sovereign memory"""

import sys
import json
import hashlib
import time
from pathlib import Path
from typing import Dict, Any, Optional

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from base_worker import Worker


class SimpleMemory:
    """Simple in-memory storage with drift locks"""
    
    def __init__(self):
        self._data: Dict[str, Dict] = {}
        self._load()
    
    def _load(self):
        """Load from disk"""
        memory_dir = Path("data/memory")
        memory_dir.mkdir(parents=True, exist_ok=True)
        for p in memory_dir.glob("bp_*.json"):
            try:
                with open(p, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    lock = data.get("drift_lock") or p.stem[3:]
                    self._data[lock] = data
            except:
                pass
    
    def store(self, blueprint: dict, task: str) -> str:
        """Store blueprint"""
        lock = hashlib.sha256(json.dumps(blueprint, sort_keys=True).encode()).hexdigest()[:16]
        record = {
            "drift_lock": lock,
            "task": task,
            "blueprint": blueprint,
            "timestamp": time.time()
        }
        self._data[lock] = record
        
        # Save to disk
        path = Path(f"data/memory/bp_{lock}.json")
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(record, f, indent=2)
        
        return lock
    
    def get(self, lock: str) -> Optional[Dict]:
        """Get blueprint"""
        return self._data.get(lock)
    
    def search(self, query: str, limit: int = 10) -> list:
        """Search memory"""
        results = []
        q_lower = query.lower()
        for lock, record in self._data.items():
            task_lower = record.get("task", "").lower()
            if q_lower in task_lower:
                results.append({
                    "drift_lock": lock,
                    "task": record.get("task", ""),
                    "timestamp": record.get("timestamp", 0)
                })
        results.sort(key=lambda x: x["timestamp"], reverse=True)
        return results[:limit]
    
    def stats(self) -> Dict:
        """Get statistics"""
        return {
            "total_entries": len(self._data),
            "keys": list(self._data.keys())[-10:]
        }


class MemoryWorker(Worker):
    """Sovereign memory operations"""
    
    def __init__(self):
        super().__init__("memory")
        self._memory = SimpleMemory()
    
    async def execute(self, task: str, **kwargs) -> Dict[str, Any]:
        """Execute memory command"""
        action = kwargs.get("action", "")
        task_lower = task.lower()
        
        if "store" in task_lower or action == "store":
            return await self._store(kwargs.get("blueprint", {}), kwargs.get("task", ""))
        elif "get" in task_lower or action == "get":
            return await self._get(kwargs.get("drift_lock", ""))
        elif "search" in task_lower or action == "search":
            return await self._search(kwargs.get("query", ""), kwargs.get("limit", 10))
        elif "stats" in task_lower or action == "stats":
            return await self._stats()
        else:
            return {"success": False, "error": "Unknown command", "worker": self.name}
    
    async def _store(self, blueprint: dict, task: str) -> Dict:
        """Store blueprint in memory"""
        lock = self._memory.store(blueprint, task)
        return {
            "success": True,
            "drift_lock": lock,
            "worker": self.name
        }
    
    async def _get(self, drift_lock: str) -> Dict:
        """Get blueprint by drift lock"""
        result = self._memory.get(drift_lock)
        if result:
            return {
                "success": True,
                "blueprint": result,
                "worker": self.name
            }
        return {
            "success": False,
            "error": f"Blueprint not found: {drift_lock}",
            "worker": self.name
        }
    
    async def _search(self, query: str, limit: int) -> Dict:
        """Search memory"""
        results = self._memory.search(query, limit)
        return {
            "success": True,
            "results": results,
            "count": len(results),
            "worker": self.name
        }
    
    async def _stats(self) -> Dict:
        """Get memory statistics"""
        stats = self._memory.stats()
        return {
            "success": True,
            "stats": stats,
            "worker": self.name
        }