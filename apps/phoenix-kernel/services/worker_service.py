"""
Worker Service - Manages worker instances and metrics
"""

import asyncio
import time
from typing import Dict, Any, Optional, List
from collections import defaultdict
from dataclasses import dataclass, field

@dataclass
class WorkerMetrics:
    calls: int = 0
    errors: int = 0
    total_duration: float = 0
    last_call: float = 0
    avg_duration: float = 0

class WorkerCache:
    """Cache for worker instances"""
    
    def __init__(self):
        self._instances: Dict[str, Any] = {}
        self._metrics: Dict[str, WorkerMetrics] = defaultdict(WorkerMetrics)
        self._locks: Dict[str, asyncio.Lock] = defaultdict(asyncio.Lock)
        self._stats = {
            'loads': 0,
            'reloads': 0,
            'clears': 0
        }
    
    async def get_worker(self, worker_class, config: Optional[Any] = None) -> Any:
        """Get or create a worker instance"""
        key = worker_class.__name__
        async with self._locks[key]:
            if key not in self._instances:
                if config:
                    self._instances[key] = worker_class(config)
                else:
                    self._instances[key] = worker_class()
                self._stats['loads'] += 1
                print(f"Loaded worker: {key}")
            return self._instances[key]
    
    async def reload_worker(self, worker_name: str) -> bool:
        """Reload a specific worker"""
        async with self._locks[worker_name]:
            if worker_name in self._instances:
                del self._instances[worker_name]
                self._stats['reloads'] += 1
                return True
        return False
    
    def clear(self):
        """Clear all worker instances"""
        self._instances.clear()
        self._stats['clears'] += 1
    
    async def get_metrics(self) -> Dict[str, Any]:
        """Get metrics for all workers"""
        worker_metrics = {}
        for name, worker in self._instances.items():
            if hasattr(worker, 'get_metrics'):
                worker_metrics[name] = await worker.get_metrics()
            else:
                worker_metrics[name] = {
                    'calls': 0,
                    'errors': 0,
                    'avg_duration': 0
                }
        
        return {
            "cache": dict(self._stats),
            "workers": worker_metrics,
            "active_workers": len(self._instances)
        }

class WorkerService:
    """Service for managing workers"""
    
    def __init__(self):
        self._workers: Dict[str, Dict] = {}
        self._metrics: Dict[str, WorkerMetrics] = defaultdict(WorkerMetrics)
        self._locks: Dict[str, asyncio.Lock] = defaultdict(asyncio.Lock)
    
    def register_worker(self, name: str, worker_class: Any, module: str, path: str):
        """Register a worker with the service"""
        self._workers[name] = {
            "class": worker_class,
            "module": module,
            "path": path,
            "loaded_at": time.time(),
            "sce_compliant": hasattr(worker_class, "execute")
        }
    
    async def get_worker(self, name: str) -> Optional[Any]:
        """Get a worker instance by name"""
        if name not in self._workers:
            return None
        
        # Create instance if needed
        if "instance" not in self._workers[name]:
            worker_class = self._workers[name]["class"]
            self._workers[name]["instance"] = worker_class()
        
        return self._workers[name]["instance"]
    
    async def execute(self, worker_name: str, task: str, **kwargs) -> Dict[str, Any]:
        """Execute a task on a worker"""
        start = time.time()
        
        async with self._locks[worker_name]:
            worker = await self.get_worker(worker_name)
            if not worker:
                return {"status": "error", "error": f"Worker {worker_name} not found"}
            
            try:
                if hasattr(worker, 'execute'):
                    result = await worker.execute(task, **kwargs)
                else:
                    result = {"error": f"Worker {worker_name} has no execute method"}
                    success = False
                
                success = "error" not in result
            except Exception as e:
                result = {"error": str(e)}
                success = False
            
            duration = time.time() - start
            
            # Update metrics
            metrics = self._metrics[worker_name]
            metrics.calls += 1
            metrics.total_duration += duration
            metrics.last_call = time.time()
            if not success:
                metrics.errors += 1
            metrics.avg_duration = metrics.total_duration / metrics.calls if metrics.calls > 0 else 0
        
        return {
            "status": "success" if success else "error",
            "result": result,
            "duration": duration,
            "worker": worker_name
        }
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get metrics for all workers"""
        return {
            name: {
                "calls": m.calls,
                "errors": m.errors,
                "avg_duration": m.avg_duration,
                "last_call": m.last_call
            }
            for name, m in self._metrics.items()
        }
    
    def list_workers(self) -> List[Dict[str, Any]]:
        """List all registered workers"""
        return [
            {
                "name": name,
                "module": info["module"],
                "loaded_at": info["loaded_at"],
                "sce_compliant": info["sce_compliant"],
                "metrics": self._metrics.get(name, WorkerMetrics())
            }
            for name, info in self._workers.items()
        ]

# Singleton instance
worker_service = WorkerService()
worker_cache = WorkerCache()