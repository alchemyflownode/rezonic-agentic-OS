# workers/factory.py
"""Sovereign Worker Factory — Eliminates abstract instantiation errors"""

import inspect
import logging
from typing import Dict, Any, Optional, Type, List
from pathlib import Path
from abc import ABC, abstractmethod

logger = logging.getLogger("PHOENIX.WORKER_FACTORY")


class SovereignWorker(ABC):
    """Sovereign Worker Base Class — All workers must inherit from this"""
    
    def __init__(self, name: str):
        self.name = name
        self._verified = False
    
    @abstractmethod
    async def execute(self, task: str, **kwargs) -> Dict[str, Any]:
        """Execute worker task — must be implemented by all concrete workers"""
        pass
    
    def verify(self) -> bool:
        """Verify worker is properly implemented"""
        if self._verified:
            return True
        
        # Check that execute is implemented (not abstract)
        if inspect.isabstract(self.__class__):
            logger.warning(f"Worker {self.name} is still abstract")
            return False
        
        # Check that execute is a coroutine
        if not inspect.iscoroutinefunction(self.execute):
            logger.warning(f"Worker {self.name}.execute is not async")
            return False
        
        self._verified = True
        return True
    
    def health_check(self) -> Dict[str, Any]:
        """Return worker health status"""
        return {
            "name": self.name,
            "verified": self._verified,
            "status": "healthy" if self._verified else "unverified"
        }


class WorkerFactory:
    """Sovereign Worker Factory — Creates only concrete, executable workers"""
    
    def __init__(self):
        self._registry: Dict[str, Type] = {}
        self._instances: Dict[str, SovereignWorker] = {}
    
    def register(self, name: str, worker_class: Type) -> bool:
        """Register a worker class (must be concrete)"""
        # Check if it's a class
        if not inspect.isclass(worker_class):
            logger.warning(f"Cannot register {name}: not a class")
            return False
        
        # Check if it's abstract
        if inspect.isabstract(worker_class):
            logger.warning(f"Cannot register {name}: abstract class")
            return False
        
        # Check if it inherits from SovereignWorker
        if not issubclass(worker_class, SovereignWorker):
            logger.warning(f"Cannot register {name}: does not inherit from SovereignWorker")
            return False
        
        self._registry[name] = worker_class
        logger.info(f"✅ Registered worker: {name}")
        return True
    
    def create(self, name: str, **kwargs) -> Optional[SovereignWorker]:
        """Create a worker instance"""
        worker_class = self._registry.get(name)
        if not worker_class:
            logger.warning(f"Worker {name} not registered")
            return None
        
        try:
            # Pass name as first argument (all SovereignWorkers require name)
            worker = worker_class(name=name, **kwargs)
            
            # Verify the instance
            if worker.verify():
                self._instances[name] = worker
                logger.info(f"✅ Created worker: {name}")
                return worker
            else:
                logger.warning(f"Worker {name} verification failed")
                return None
                
        except Exception as e:
            logger.error(f"Failed to create worker {name}: {e}")
            return None
    
    def get(self, name: str) -> Optional[SovereignWorker]:
        """Get existing worker instance"""
        return self._instances.get(name)
    
    def create_all(self) -> Dict[str, SovereignWorker]:
        """Create instances of all registered workers"""
        workers = {}
        for name in self._registry:
            worker = self.create(name)
            if worker:
                workers[name] = worker
        return workers
    
    def list_registered(self) -> List[str]:
        """List all registered worker names"""
        return list(self._registry.keys())
    
    def list_instances(self) -> List[str]:
        """List all created worker instances"""
        return list(self._instances.keys())


# ============================================
# DEFAULT WORKER IMPLEMENTATIONS
# ============================================

class BaseWorker(SovereignWorker):
    """Base concrete worker — safe to instantiate"""
    
    def __init__(self, name: str):
        super().__init__(name)
    
    async def execute(self, task: str, **kwargs) -> Dict[str, Any]:
        """Base execute — override in subclasses"""
        return {
            "success": True,
            "worker": self.name,
            "message": f"Base worker executed: {task[:100]}"
        }


class BrainWorker(BaseWorker):
    """Brain/AI worker"""
    
    def __init__(self, name: str = "brain", ollama_client=None):
        super().__init__(name)
        self.ollama = ollama_client
    
    async def execute(self, task: str, **kwargs) -> Dict[str, Any]:
        if self.ollama and self.ollama.available:
            # Use Ollama for AI response
            messages = [{"role": "user", "content": task}]
            response = ""
            async for token in self.ollama.stream_chat(messages):
                response += token
            return {
                "success": True,
                "response": response,
                "worker": self.name
            }
        return {
            "success": True,
            "response": f"Brain processing: {task[:100]}",
            "worker": self.name
        }


class PaperTraderWorker(BaseWorker):
    """Paper trading worker"""
    
    def __init__(self, name: str = "paper_trader"):
        super().__init__(name)
        self.balance = 1000000
        self.positions = {}
    
    async def execute(self, task: str, **kwargs) -> Dict[str, Any]:
        # Implementation here
        pass


class CodeGenWorker(BaseWorker):
    """Code generation worker"""
    
    def __init__(self, name: str = "code_gen"):
        super().__init__(name)
    
    async def execute(self, task: str, **kwargs) -> Dict[str, Any]:
        # Implementation here
        pass


# ============================================
# WORKER LOADER — Safe Dynamic Loading
# ============================================

class SovereignWorkerLoader:
    """Safe worker loader — no abstract instantiation"""
    
    def __init__(self, workers_dir: Path):
        self.workers_dir = workers_dir
        self.factory = WorkerFactory()
        self._load_from_directory()
    
    def _load_from_directory(self):
        """Load workers from directory safely"""
        if not self.workers_dir.exists():
            return
        
        import importlib.util
        import sys
        
        for py_file in self.workers_dir.glob("*.py"):
            if py_file.name.startswith("__"):
                continue
            
            try:
                # Load module
                spec = importlib.util.spec_from_file_location(py_file.stem, py_file)
                if not spec or not spec.loader:
                    continue
                
                mod = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(mod)
                
                # Find worker classes
                for name, obj in inspect.getmembers(mod, inspect.isclass):
                    # Check if it's a concrete worker class
                    if (issubclass(obj, SovereignWorker) and 
                        not inspect.isabstract(obj) and
                        obj != SovereignWorker and
                        obj != BaseWorker):
                        
                        worker_name = getattr(obj, 'name', name.lower())
                        self.factory.register(worker_name, obj)
                        
            except Exception as e:
                logger.warning(f"Failed to load {py_file.name}: {e}")
    
    def create_all(self) -> Dict[str, SovereignWorker]:
        """Create all loaded workers"""
        return self.factory.create_all()
    
    def get_worker(self, name: str) -> Optional[SovereignWorker]:
        """Get a worker instance"""
        return self.factory.get(name)
    
    def get_all_workers(self) -> Dict[str, SovereignWorker]:
        """Get all worker instances"""
        return self.factory._instances