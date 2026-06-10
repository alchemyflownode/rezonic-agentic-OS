# workers/decorators.py
"""Error handling decorators for all workers"""

import asyncio
import logging
import traceback
from functools import wraps
from typing import Any, Callable, Dict
import time

logger = logging.getLogger("phoenix.workers")

def handle_errors(worker_name: str, retry_count: int = 3, retry_delay: float = 1.0):
    """
    Decorator for error handling with retry logic.
    
    Usage:
        @handle_errors("momentum_worker")
        async def execute(self, task):
            ...
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> Dict[str, Any]:
            last_error = None
            
            for attempt in range(retry_count):
                try:
                    return await func(*args, **kwargs)
                    
                except asyncio.TimeoutError as e:
                    last_error = e
                    logger.warning(f"[{worker_name}] Timeout (attempt {attempt+1}/{retry_count}): {e}")
                    
                except ConnectionError as e:
                    last_error = e
                    logger.warning(f"[{worker_name}] Connection error (attempt {attempt+1}/{retry_count}): {e}")
                    
                except Exception as e:
                    last_error = e
                    logger.error(f"[{worker_name}] Error: {e}")
                    logger.debug(traceback.format_exc())
                    
                    # Don't retry on fatal errors
                    if "fatal" in str(e).lower():
                        return {
                            "success": False,
                            "error": str(e),
                            "worker": worker_name,
                            "fatal": True
                        }
                
                # Wait before retry (exponential backoff)
                if attempt < retry_count - 1:
                    await asyncio.sleep(retry_delay * (2 ** attempt))
            
            # All retries exhausted
            return {
                "success": False,
                "error": str(last_error),
                "worker": worker_name,
                "retries": retry_count
            }
        
        return wrapper
    return decorator


def with_timeout(timeout_seconds: float = 30.0):
    """
    Decorator for timeout handling.
    
    Usage:
        @with_timeout(10.0)
        async def execute(self, task):
            ...
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                return await asyncio.wait_for(
                    func(*args, **kwargs),
                    timeout=timeout_seconds
                )
            except asyncio.TimeoutError:
                return {
                    "success": False,
                    "error": f"Timeout after {timeout_seconds}s",
                    "worker": args[0].name if args else "unknown"
                }
        return wrapper
    return decorator


def log_execution(worker_name: str = None):
    """
    Decorator for logging execution time.
    
    Usage:
        @log_execution("momentum_worker")
        async def execute(self, task):
            ...
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            start = time.time()
            wname = worker_name or (args[0].name if args else "unknown")
            
            try:
                result = await func(*args, **kwargs)
                duration = (time.time() - start) * 1000
                
                logger.debug(f"[{wname}] Executed in {duration:.2f}ms")
                
                # Add execution time to result
                if isinstance(result, dict):
                    result["execution_time_ms"] = duration
                
                return result
                
            except Exception as e:
                duration = (time.time() - start) * 1000
                logger.error(f"[{wname}] Failed after {duration:.2f}ms: {e}")
                raise
                
        return wrapper
    return decorator


__all__ = ['handle_errors', 'with_timeout', 'log_execution']