#!/usr/bin/env python3
"""
workers/memory_worker.py — Sovereign Memory Worker
"""

from __future__ import annotations

import asyncio
import datetime
import hashlib
import json
import logging
import time
from collections import OrderedDict
from pathlib import Path
from typing import Any, Dict, List, Optional

try:
    from workers.base_worker import Worker
except ImportError:
    try:
        from base_worker import Worker
    except ImportError:
        class Worker:
            def __init__(self, name: str = "worker") -> None:
                self.name = name
                self.execution_count = 0
                self.error_count = 0
            async def initialize(self) -> None:
                pass
            async def execute(self, task: str, **kwargs: Any) -> Dict[str, Any]:
                return {"error": "not implemented"}
            async def health_check(self) -> Dict[str, Any]:
                return {"status": "unknown"}

logger = logging.getLogger("phoenix.memory")

MEMORY_CONFIG = {
    "data_dir": "data/memory",
    "max_entries": 10000,
    "max_blueprint_size": 1048576,
    "file_prefix": "bp_",
    "file_extension": ".json",
}


class SovereignMemory:
    def __init__(self, data_dir: str = MEMORY_CONFIG["data_dir"], max_entries: int = MEMORY_CONFIG["max_entries"]) -> None:
        self._data: OrderedDict[str, Dict[str, Any]] = OrderedDict()
        self._data_dir = Path(data_dir)
        self._max_entries = max_entries
        self._write_count = 0
        self._read_count = 0
        self._eviction_count = 0

    def load_from_disk(self) -> int:
        self._data_dir.mkdir(parents=True, exist_ok=True)
        loaded = 0
        prefix = MEMORY_CONFIG["file_prefix"]
        ext = MEMORY_CONFIG["file_extension"]

        for path in sorted(self._data_dir.glob(f"{prefix}*{ext}")):
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
                lock = data.get("drift_lock")
                if lock:
                    self._data[lock] = data
                    loaded += 1
            except Exception:
                pass
        self._evict_if_needed()
        logger.info(f"Loaded {loaded} blueprints")
        return loaded

    def store(self, blueprint: Dict[str, Any], task: str) -> str:
        serialized = json.dumps(blueprint, sort_keys=True, default=str)
        if len(serialized) > MEMORY_CONFIG["max_blueprint_size"]:
            raise ValueError(f"Blueprint too large")

        lock = hashlib.sha256(serialized.encode()).hexdigest()[:16]
        record = {
            "drift_lock": lock,
            "task": task,
            "blueprint": blueprint,
            "timestamp": time.time(),
            "created_at": datetime.datetime.now().isoformat(),
            "size_bytes": len(serialized),
        }

        self._data[lock] = record
        self._data.move_to_end(lock)
        self._write_to_disk(lock, record)
        self._write_count += 1
        self._evict_if_needed()
        return lock

    def get(self, lock: str) -> Optional[Dict[str, Any]]:
        record = self._data.get(lock)
        if record:
            self._data.move_to_end(lock)
            self._read_count += 1
        return record

    def delete(self, lock: str) -> bool:
        if lock not in self._data:
            return False
        del self._data[lock]
        try:
            self._get_path(lock).unlink(missing_ok=True)
        except Exception:
            pass
        return True

    def search(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        q_lower = query.lower()
        matches = []
        for lock, record in self._data.items():
            if q_lower in record.get("task", "").lower():
                matches.append({"drift_lock": lock, "task": record.get("task"), "timestamp": record.get("timestamp", 0)})
        matches.sort(key=lambda x: x["timestamp"], reverse=True)
        return matches[:limit]

    def stats(self) -> Dict[str, Any]:
        total_size = sum(r.get("size_bytes", 0) for r in self._data.values())
        return {
            "total_entries": len(self._data),
            "total_size_bytes": total_size,
            "writes": self._write_count,
            "reads": self._read_count,
            "evictions": self._eviction_count,
        }

    def _get_path(self, lock: str) -> Path:
        prefix = MEMORY_CONFIG["file_prefix"]
        ext = MEMORY_CONFIG["file_extension"]
        return self._data_dir / f"{prefix}{lock}{ext}"

    def _write_to_disk(self, lock: str, record: Dict[str, Any]) -> None:
        target = self._get_path(lock)
        tmp_path = target.with_suffix(".tmp")
        try:
            tmp_path.write_text(json.dumps(record, indent=2, default=str), encoding="utf-8")
            tmp_path.replace(target)
        except Exception as e:
            logger.error(f"Write failed: {e}")

    def _evict_if_needed(self) -> None:
        while len(self._data) > self._max_entries:
            oldest_key, _ = self._data.popitem(last=False)
            self._eviction_count += 1
            try:
                self._get_path(oldest_key).unlink(missing_ok=True)
            except Exception:
                pass


class MemoryWorker(Worker):
    name = "memory"
    version = "2.0.0"

    def __init__(self) -> None:
        super().__init__("memory")
        self._memory = SovereignMemory()
        self._initialized = False

    async def initialize(self) -> None:
        if self._initialized:
            return
        loop = asyncio.get_running_loop()
        try:
            await loop.run_in_executor(None, self._memory.load_from_disk)
            self._initialized = True
            logger.info("MemoryWorker initialized")
        except Exception as e:
            logger.error(f"Init failed: {e}")
            self._initialized = True

    async def execute(self, task: str, **kwargs: Any) -> Dict[str, Any]:
        if not self._initialized:
            await self.initialize()

        self.execution_count += 1
        action = kwargs.get("action", "").lower()
        task_lower = task.lower().strip()

        if action == "store" or task_lower.startswith("store"):
            return await self._do_store(kwargs)
        elif action == "get" or task_lower.startswith("get"):
            return await self._do_get(kwargs)
        elif action == "delete" or task_lower.startswith("delete"):
            return await self._do_delete(kwargs)
        elif action == "search" or task_lower.startswith("search"):
            return await self._do_search(kwargs)
        elif action == "stats" or task_lower.startswith("stats"):
            return await self._do_stats()
        else:
            return await self._do_search({"query": task, "limit": kwargs.get("limit", 10)})

    async def _do_store(self, kwargs: Dict[str, Any]) -> Dict[str, Any]:
        blueprint = kwargs.get("blueprint")
        if not blueprint:
            return self._response(False, error="blueprint required")
        if isinstance(blueprint, str):
            try:
                blueprint = json.loads(blueprint)
            except:
                return self._response(False, error="Invalid JSON")
        task_desc = kwargs.get("task", "untitled")
        loop = asyncio.get_running_loop()
        try:
            lock = await loop.run_in_executor(None, self._memory.store, blueprint, task_desc)
            return self._response(True, drift_lock=lock)
        except Exception as e:
            return self._response(False, error=str(e))

    async def _do_get(self, kwargs: Dict[str, Any]) -> Dict[str, Any]:
        lock = kwargs.get("drift_lock", "")
        if not lock:
            return self._response(False, error="drift_lock required")
        result = self._memory.get(lock)
        if result:
            return self._response(True, blueprint=result)
        return self._response(False, error="Not found")

    async def _do_delete(self, kwargs: Dict[str, Any]) -> Dict[str, Any]:
        lock = kwargs.get("drift_lock", "")
        if not lock:
            return self._response(False, error="drift_lock required")
        deleted = self._memory.delete(lock)
        return self._response(deleted, deleted=lock if deleted else None)

    async def _do_search(self, kwargs: Dict[str, Any]) -> Dict[str, Any]:
        query = kwargs.get("query", "")
        limit = kwargs.get("limit", 10)
        results = self._memory.search(query, limit)
        return self._response(True, results=results, count=len(results))

    async def _do_stats(self) -> Dict[str, Any]:
        stats = self._memory.stats()
        return self._response(True, stats=stats)

    def _response(self, success: bool, **extra: Any) -> Dict[str, Any]:
        return {"success": success, "worker": self.name, "timestamp": datetime.datetime.now().isoformat(), **extra}

    async def health_check(self) -> Dict[str, Any]:
        return {"name": self.name, "status": "healthy", "executions": self.execution_count, "errors": self.error_count}
