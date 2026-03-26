from typing import Optional, List, Dict, Any
import asyncio
from datetime import datetime
from enum import Enum

class EventType(Enum):
    """System-wide event types"""
    STRATEGY_PROPOSED = "strategy_proposed"
    STRATEGY_BACKTESTED = "strategy_backtested"
    WIN_RATE_UPDATED = "win_rate_updated"
    MUTATION_OCCURRED = "mutation_occurred"
    MARKET_UPDATE = "market_update"
    TRADE_EXECUTED = "trade_executed"
    FILE_SCANNED = "file_scanned"

class Event:
    """Base event class"""
    def __init__(self, type: EventType, source: str, payload: Dict[str, Any]):
        self.type = type
        self.source = source
        self.payload = payload
        self.timestamp = datetime.now()
        self.id = f"{type.value}_{datetime.now().timestamp()}"

class EventBus:
    """Central event bus for worker communication"""
    
    def __init__(self):
        self.subscribers = {}
        self.event_history = []
        self.max_history = 1000
        
    def subscribe(self, event_type: EventType, callback):
        """Subscribe to an event type"""
        if event_type not in self.subscribers:
            self.subscribers[event_type] = []
        self.subscribers[event_type].append(callback)
        
    def unsubscribe(self, event_type: EventType, callback):
        """Unsubscribe from an event type"""
        if event_type in self.subscribers:
            if callback in self.subscribers[event_type]:
                self.subscribers[event_type].remove(callback)
                
    async def publish(self, event: Event):
        """Publish an event to all subscribers"""
        # Add to history
        self.event_history.append(event)
        if len(self.event_history) > self.max_history:
            self.event_history = self.event_history[-self.max_history:]
            
        # Notify subscribers
        if event.type in self.subscribers:
            for callback in self.subscribers[event.type]:
                try:
                    if asyncio.iscoroutinefunction(callback):
                        await callback(event)
                    else:
                        callback(event)
                except Exception as e:
                    print(f"Error in event subscriber: {e}")
                    
    async def get_history(self, event_type: Optional[EventType] = None, limit: int = 100) -> List[Event]:
        """Get event history"""
        if event_type:
            filtered = [e for e in self.event_history if e.type == event_type]
            return filtered[-limit:]
        return self.event_history[-limit:]
        
    def clear_history(self):
        """Clear event history"""
        self.event_history = []

# Global event bus instance
event_bus = EventBus()
