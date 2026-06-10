# kernel/governance.py
"""
Sovereign Governance Layer - Controls execution, limits, and recovery.
"""

import asyncio
import time
import traceback
from typing import Dict, Any, Optional, Callable
from dataclasses import dataclass
from enum import Enum
import logging

logger = logging.getLogger("PHOENIX.GOVERNANCE")

class ExecutionStatus(Enum):
    SUCCESS = "success"
    TIMEOUT = "timeout"
    ERROR = "error"
    KILLED = "killed"

@dataclass
class ExecutionResult:
    status: ExecutionStatus
    result: Any = None
    error: str = None
    duration: float = 0

class TaskSandbox:
    """Isolated execution container with timeout protection"""
    
    def __init__(self, default_timeout: float = 15.0):
        self.default_timeout = default_timeout
        self.active_tasks: Dict[str, asyncio.Task] = {}
    
    async def execute(self, coro, task_id: str = None, timeout: float = None) -> ExecutionResult:
        task_id = task_id or str(time.time())
        start = time.time()
        timeout = timeout or self.default_timeout
        
        try:
            task = asyncio.create_task(coro)
            self.active_tasks[task_id] = task
            result = await asyncio.wait_for(task, timeout=timeout)
            
            return ExecutionResult(
                status=ExecutionStatus.SUCCESS,
                result=result,
                duration=time.time() - start
            )
        except asyncio.TimeoutError:
            task.cancel()
            logger.warning(f"Task {task_id} timed out after {timeout}s")
            return ExecutionResult(
                status=ExecutionStatus.TIMEOUT,
                error=f"Timeout after {timeout}s",
                duration=time.time() - start
            )
        except Exception as e:
            logger.error(f"Task {task_id} failed: {e}")
            return ExecutionResult(
                status=ExecutionStatus.ERROR,
                error=str(e),
                duration=time.time() - start
            )
        finally:
            self.active_tasks.pop(task_id, None)
    
    def kill_task(self, task_id: str) -> bool:
        """Force kill a running task"""
        if task_id in self.active_tasks:
            self.active_tasks[task_id].cancel()
            return True
        return False
    
    def kill_all(self):
        """Emergency kill - terminate all running tasks"""
        for task_id, task in self.active_tasks.items():
            task.cancel()
        self.active_tasks.clear()
        logger.critical("🔴 All tasks killed by governor")

class RateLimiter:
    """Multi-user rate limiting"""
    
    def __init__(self, default_limit: int = 60, window: int = 60):
        self.default_limit = default_limit
        self.window = window
        self._requests: Dict[str, list] = {}
        self._lock = asyncio.Lock()
    
    async def allow(self, user_id: str) -> bool:
        """Check if user is allowed to make a request"""
        async with self._lock:
            now = time.time()
            
            if user_id not in self._requests:
                self._requests[user_id] = []
            
            # Clean old entries
            self._requests[user_id] = [
                t for t in self._requests[user_id] if now - t < self.window
            ]
            
            if len(self._requests[user_id]) >= self.default_limit:
                logger.warning(f"Rate limit exceeded for {user_id}")
                return False
            
            self._requests[user_id].append(now)
            return True
    
    def get_stats(self, user_id: str) -> Dict:
        """Get rate limit stats for a user"""
        now = time.time()
        recent = [t for t in self._requests.get(user_id, []) if now - t < self.window]
        return {
            "current": len(recent),
            "limit": self.default_limit,
            "reset_in": self.window - (now - recent[0]) if recent else 0
        }
