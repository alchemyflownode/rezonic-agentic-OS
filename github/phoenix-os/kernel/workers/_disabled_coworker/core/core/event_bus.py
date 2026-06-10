"""
Event Bus for Phoenix Coworker

Central event system for decoupled communication between components.
"""

import asyncio
from typing import Dict, List, Callable, Any, Optional
from dataclasses import dataclass
from datetime import datetime
from enum import Enum, auto


class EventType(Enum):
    """Standard event types"""
    # System events
    SYSTEM_START = "system:start"
    SYSTEM_STOP = "system:stop"
    SYSTEM_ERROR = "system:error"
    
    # Memory events
    MEMORY_STORED = "memory:stored"
    MEMORY_ACCESSED = "memory:accessed"
    MEMORY_RELATED = "memory:related"
    MEMORY_FORGOTTEN = "memory:forgotten"
    
    # Task events
    TASK_CREATED = "task:created"
    TASK_STARTED = "task:started"
    TASK_COMPLETED = "task:completed"
    TASK_FAILED = "task:failed"
    
    # File events
    FILE_CREATED = "file:created"
    FILE_MODIFIED = "file:modified"
    FILE_DELETED = "file:deleted"
    
    # User events
    USER_COMMAND = "user:command"
    USER_INPUT = "user:input"
    USER_PRESENCE = "user:presence"
    
    # Worker events
    WORKER_STARTED = "worker:started"
    WORKER_STOPPED = "worker:stopped"
    WORKER_ERROR = "worker:error"
    
    # Safety events
    SAFETY_BLOCKED = "safety:blocked"
    SAFETY_CONFIRMED = "safety:confirmed"
    
    # Custom
    CUSTOM = "custom"


@dataclass
class Event:
    """An event in the system"""
    type: EventType
    data: Dict[str, Any]
    timestamp: datetime
    source: Optional[str] = None
    id: Optional[str] = None
    
    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "type": self.type.value,
            "data": self.data,
            "timestamp": self.timestamp.isoformat(),
            "source": self.source
        }


class EventBus:
    """
    Central event bus for Phoenix Coworker.
    
    Provides publish/subscribe pattern for decoupled communication.
    """
    
    def __init__(self):
        self._subscribers: Dict[EventType, List[Callable]] = {}
        self._wildcard_subscribers: List[Callable] = []
        self._event_history: List[Event] = []
        self._max_history = 1000
        self._lock = asyncio.Lock()
        
        print("✓ EventBus initialized")
    
    def subscribe(
        self, 
        event_type: EventType, 
        callback: Callable[[Event], None]
    ):
        """
        Subscribe to events of a specific type.
        
        Args:
            event_type: The event type to subscribe to
            callback: Function to call when event occurs
        """
        if event_type not in self._subscribers:
            self._subscribers[event_type] = []
        self._subscribers[event_type].append(callback)
    
    def subscribe_all(self, callback: Callable[[Event], None]):
        """
        Subscribe to all events.
        
        Args:
            callback: Function to call for all events
        """
        self._wildcard_subscribers.append(callback)
    
    def unsubscribe(
        self, 
        event_type: EventType, 
        callback: Callable[[Event], None]
    ):
        """Unsubscribe from events"""
        if event_type in self._subscribers:
            if callback in self._subscribers[event_type]:
                self._subscribers[event_type].remove(callback)
    
    async def publish(self, event_type: EventType, data: Dict, source: str = None):
        """
        Publish an event.
        
        Args:
            event_type: Type of event
            data: Event data
            source: Source component
        """
        event = Event(
            type=event_type,
            data=data,
            timestamp=datetime.now(),
            source=source,
            id=f"evt_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"
        )
        
        # Add to history
        self._event_history.append(event)
        if len(self._event_history) > self._max_history:
            self._event_history = self._event_history[-self._max_history:]
        
        # Notify specific subscribers
        if event_type in self._subscribers:
            for callback in self._subscribers[event_type]:
                try:
                    if asyncio.iscoroutinefunction(callback):
                        await callback(event)
                    else:
                        callback(event)
                except Exception as e:
                    print(f"Error in event handler: {e}")
        
        # Notify wildcard subscribers
        for callback in self._wildcard_subscribers:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(event)
                else:
                    callback(event)
            except Exception as e:
                print(f"Error in wildcard handler: {e}")
    
    def get_recent_events(
        self, 
        event_type: EventType = None, 
        limit: int = 50
    ) -> List[Event]:
        """Get recent events"""
        events = self._event_history
        
        if event_type:
            events = [e for e in events if e.type == event_type]
        
        return events[-limit:]
    
    def clear_history(self):
        """Clear event history"""
        self._event_history.clear()


# Singleton instance
_bus_instance: Optional[EventBus] = None


def get_event_bus() -> EventBus:
    """Get or create the singleton event bus"""
    global _bus_instance
    if _bus_instance is None:
        _bus_instance = EventBus()
    return _bus_instance
