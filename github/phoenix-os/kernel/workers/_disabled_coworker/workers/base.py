"""
Base Worker for Phoenix Coworker

All workers inherit from this base class.
"""

import asyncio
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from datetime import datetime


class BaseWorker(ABC):
    """
    Base class for all Phoenix workers.
    
    Workers are specialized components that handle specific types of tasks.
    """
    
    def __init__(self, kernel: Any, name: str = None):
        self.kernel = kernel
        self.name = name or self.__class__.__name__
        self._running = False
        self._task: Optional[asyncio.Task] = None
        self._start_time: Optional[datetime] = None
    
    @property
    def is_running(self) -> bool:
        """Check if worker is running"""
        return self._running
    
    async def start(self):
        """Start the worker"""
        self._running = True
        self._start_time = datetime.now()
        
        await self.kernel.event_bus.publish(
            "worker:started",
            {"worker": self.name},
            source="worker"
        )
        
        print(f"✓ Worker '{self.name}' started")
        
        # Run worker loop
        await self.run()
    
    async def stop(self):
        """Stop the worker"""
        self._running = False
        
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        
        await self.kernel.event_bus.publish(
            "worker:stopped",
            {"worker": self.name},
            source="worker"
        )
        
        print(f"✓ Worker '{self.name}' stopped")
    
    @abstractmethod
    async def run(self):
        """Main worker loop - override in subclass"""
        pass
    
    @abstractmethod
    async def process(self, command: str, context: Dict = None) -> Dict:
        """Process a command - override in subclass"""
        pass
    
    async def emit_event(self, event_type: str, data: Dict):
        """Emit an event to the event bus"""
        await self.kernel.event_bus.publish(
            event_type,
            data,
            source=self.name
        )
