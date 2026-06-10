# core/event_bus.py
import asyncio
import logging
from typing import Callable, Any, Dict, List
from datetime import datetime

logger = logging.getLogger(__name__)

class EventBus:
    def __init__(self):
        self.subscribers: Dict[str, List[Callable]] = {}
        self._lock = asyncio.Lock()
        self.event_count = 0

    def subscribe(self, event_type: str, handler: Callable):
        """Subscribe to an event type"""
        if event_type not in self.subscribers:
            self.subscribers[event_type] = []
        self.subscribers[event_type].append(handler)
        logger.debug(f"Subscribed handler to {event_type}")

    def unsubscribe(self, event_type: str, handler: Callable):
        """Unsubscribe to prevent memory leaks"""
        if event_type in self.subscribers:
            try:
                self.subscribers[event_type].remove(handler)
            except ValueError:
                pass

    async def emit(self, event_type: str, data: Any):
        """Emit event to all subscribers with error isolation"""
        self.event_count += 1
        handlers = self.subscribers.get(event_type, []).copy()
        
        if not handlers:
            return

        results = await asyncio.gather(
            *[self._safe_call(handler, data, event_type) for handler in handlers],
            return_exceptions=True
        )
        
        # Log any failures
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"Handler {i} failed for {event_type}: {result}")

    async def _safe_call(self, handler: Callable, data: Any, event_type: str):
        """Wrap handler to prevent one failure from breaking all"""
        try:
            if asyncio.iscoroutinefunction(handler):
                return await handler(data)
            else:
                return handler(data)
        except Exception as e:
            logger.error(f"Event handler error [{event_type}]: {e}")
            raise  # Re-raise for gather to catch

    def get_stats(self) -> dict:
        """Observability - track event flow"""
        return {
            "total_events": self.event_count,
            "subscribers": {k: len(v) for k, v in self.subscribers.items()}
        }