"""Base worker for Phoenix Kernel - Production Ready"""
import asyncio
import logging
import time
import traceback
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, Union
from datetime import datetime

class WorkerConfig:
    """Worker configuration"""
    def __init__(self, name: str, **kwargs):
        self.name = name
        self.enabled = kwargs.get('enabled', True)
        self.max_concurrent = kwargs.get('max_concurrent', 5)
        self.timeout = kwargs.get('timeout', 30)
        self.requires_gpu = kwargs.get('requires_gpu', False)
        self.retry_count = kwargs.get('retry_count', 3)
        self.retry_delay = kwargs.get('retry_delay', 1)

class Worker(ABC):
    """Base worker class with production-ready error handling"""
    
    def __init__(self, config: Optional[WorkerConfig] = None):
        self.name = getattr(self, 'name', config.name if config else "unknown")
        self.config = config or WorkerConfig(self.__class__.__name__)
        self.metrics = {
            'calls': 0,
            'errors': 0,
            'total_duration': 0,
            'last_call': None,
            'last_error': None,
            'last_error_time': None
        }
        self._lock = asyncio.Lock()
        self.is_ready = True
        
        # Setup proper logging
        self.logger = logging.getLogger(f"worker.{self.name}")
    
    @abstractmethod
    async def execute(self, task: str, **kwargs) -> Dict[str, Any]:
        """
        Execute worker task - must be implemented by subclasses.
        Override this to implement worker logic.
        """
        raise NotImplementedError(f"{self.name}.execute() not implemented")
    
    async def _execute_with_metrics(self, task: str, **kwargs) -> Dict[str, Any]:
        """Execute with metrics tracking"""
        start_time = time.time()
        self.metrics['calls'] += 1
        self.metrics['last_call'] = datetime.now().isoformat()
        
        try:
            result = await self.execute(task, **kwargs)
            
            # Ensure result has expected structure
            if not isinstance(result, dict):
                result = {"result": result, "success": True}
            if "success" not in result:
                result["success"] = True
                
            return result
            
        except Exception as e:
            self.metrics['errors'] += 1
            self.metrics['last_error'] = str(e)
            self.metrics['last_error_time'] = datetime.now().isoformat()
            
            self.logger.error(f"Worker {self.name} execution failed: {e}")
            self.logger.debug(traceback.format_exc())
            
            return {
                "success": False,
                "error": str(e),
                "worker": self.name,
                "traceback": traceback.format_exc() if self.logger.isEnabledFor(logging.DEBUG) else None
            }
        finally:
            duration = time.time() - start_time
            self.metrics['total_duration'] += duration
    
    async def _execute_with_retry(self, task: str, **kwargs) -> Dict[str, Any]:
        """Execute with retry logic"""
        last_error = None
        
        for attempt in range(self.config.retry_count):
            try:
                return await self._execute_with_metrics(task, **kwargs)
            except Exception as e:
                last_error = e
                self.logger.warning(f"Attempt {attempt + 1}/{self.config.retry_count} failed: {e}")
                
                if attempt < self.config.retry_count - 1:
                    await asyncio.sleep(self.config.retry_delay * (attempt + 1))
        
        return {
            "success": False,
            "error": f"Failed after {self.config.retry_count} attempts: {last_error}",
            "worker": self.name
        }
    
    async def _execute_with_timeout(self, task: str, **kwargs) -> Dict[str, Any]:
        """Execute with timeout"""
        try:
            return await asyncio.wait_for(
                self._execute_with_retry(task, **kwargs),
                timeout=self.config.timeout
            )
        except asyncio.TimeoutError:
            self.metrics['errors'] += 1
            self.logger.error(f"Worker {self.name} timed out after {self.config.timeout}s")
            return {
                "success": False,
                "error": f"Timeout after {self.config.timeout}s",
                "worker": self.name
            }
    
    async def process(self, task: str, **kwargs) -> Dict[str, Any]:
        """
        Main entry point for worker processing.
        Handles all production concerns: metrics, errors, timeouts, retries.
        """
        if not self.config.enabled:
            return {"success": False, "error": f"Worker {self.name} is disabled"}
        
        async with self._lock:
            return await self._execute_with_timeout(task, **kwargs)
    
    async def validate(self, task: str) -> bool:
        """Validate task before execution"""
        return True
    
    async def get_metrics(self) -> Dict[str, Any]:
        """Get worker metrics"""
        async with self._lock:
            metrics_copy = self.metrics.copy()
            metrics_copy['avg_duration'] = (
                metrics_copy['total_duration'] / metrics_copy['calls'] 
                if metrics_copy['calls'] > 0 else 0
            )
            metrics_copy['config'] = {
                'enabled': self.config.enabled,
                'max_concurrent': self.config.max_concurrent,
                'timeout': self.config.timeout,
                'retry_count': self.config.retry_count
            }
            return metrics_copy
    
    async def health_check(self) -> Dict[str, Any]:
        """Return worker health status"""
        async with self._lock:
            return {
                "worker": self.name,
                "status": "healthy" if self.is_ready else "unhealthy",
                "enabled": self.config.enabled,
                "calls": self.metrics['calls'],
                "errors": self.metrics['errors'],
                "error_rate": (
                    self.metrics['errors'] / self.metrics['calls'] 
                    if self.metrics['calls'] > 0 else 0
                ),
                "last_call": self.metrics['last_call'],
                "last_error": self.metrics['last_error']
            }
    
    async def reset_metrics(self) -> None:
        """Reset worker metrics"""
        async with self._lock:
            self.metrics = {
                'calls': 0,
                'errors': 0,
                'total_duration': 0,
                'last_call': None,
                'last_error': None,
                'last_error_time': None
            }
    
    def log(self, level: str, message: str):
        """Legacy log method - use logger instead"""
        getattr(self.logger, level.lower(), self.logger.info)(message)


# Alias for backward compatibility
BaseWorker = Worker

__all__ = ['Worker', 'BaseWorker', 'WorkerConfig']