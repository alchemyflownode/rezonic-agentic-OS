# backend/core/sovereign_event_bus.py
"""
SOVEREIGN EVENT BUS
Pure asyncio, local-only event propagation
No cloud, no external dependencies
"""

import asyncio
import json
import time
import hashlib
import logging
from typing import Dict, Any, Callable, List, Optional
from enum import Enum
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)

class EventType(Enum):
    """All system events"""
    # System
    SYSTEM_BOOT = "system.boot"
    SYSTEM_SHUTDOWN = "system.shutdown"
    KERNEL_HEARTBEAT = "kernel.heartbeat"
    
    # Identity
    USER_LOGIN = "user.login"
    USER_LOGOUT = "user.logout"
    
    # Tech Debt Scanning
    SCAN_STARTED = "techdebt.scan.started"
    SCAN_COMPLETED = "techdebt.scan.completed"
    SCAN_ERROR = "techdebt.scan.error"
    VULNERABILITY_FOUND = "techdebt.vulnerability.found"
    LICENSE_ISSUE = "techdebt.license.issue"
    
    # Jurisdiction
    JURISDICTION_SCAN_STARTED = "jurisdiction.scan.started"
    JURISDICTION_SCAN_COMPLETED = "jurisdiction.scan.completed"
    HIGH_RISK_COMPONENT = "jurisdiction.high_risk"
    
    # Trading
    MARKET_UPDATE = "trading.market.update"
    SIGNAL_GENERATED = "trading.signal.generated"
    STRATEGY_PROPOSED = "trading.strategy.proposed"
    STRATEGY_BACKTESTED = "trading.strategy.backtested"
    MUTATION_OCCURRED = "trading.mutation.occurred"
    
    # Workers
    WORKER_START = "worker.start"
    WORKER_COMPLETE = "worker.complete"
    WORKER_ERROR = "worker.error"
    
    # Audit
    VERA_PROOF = "audit.vera.proof"
    AUDIT_LOG = "audit.log"


@dataclass
class Event:
    """Immutable event with VERA proof"""
    type: EventType
    source: str
    payload: Dict[str, Any]
    timestamp: float = field(default_factory=time.time)
    vera_proof: str = field(default="", init=False)
    
    def __post_init__(self):
        """Generate VERA proof automatically"""
        content = f"{self.type.value}:{self.source}:{json.dumps(self.payload, sort_keys=True)}:{self.timestamp}"
        self.vera_proof = hashlib.sha256(content.encode()).hexdigest()[:16]


class SovereignEventBus:
    """Singleton event bus for the entire system"""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.subscribers = {}
            cls._instance.event_history = []
            cls._instance.history_limit = 10000
            cls._instance.lock = asyncio.Lock()
        return cls._instance
    
    def subscribe(self, event_type: EventType, callback: Callable):
        """Subscribe to an event type"""
        if event_type not in self.subscribers:
            self.subscribers[event_type] = []
        self.subscribers[event_type].append(callback)
        logger.debug(f"Subscribed to {event_type.value}")
    
    def subscribe_all(self, callbacks: Dict[EventType, Callable]):
        """Subscribe to multiple events"""
        for event_type, callback in callbacks.items():
            self.subscribe(event_type, callback)
    
    async def publish(self, event: Event):
        """Publish an event to all subscribers"""
        async with self.lock:
            self.event_history.append(event)
            if len(self.event_history) > self.history_limit:
                self.event_history = self.event_history[-self.history_limit:]
        
        if event.type in self.subscribers:
            for callback in self.subscribers[event.type]:
                try:
                    asyncio.create_task(callback(event))
                except Exception as e:
                    logger.error(f"Event callback error: {e}")
        
        logger.debug(f"Published: {event.type.value} [{event.vera_proof}]")
    
    async def get_history(self, event_type: Optional[EventType] = None, limit: int = 100) -> List[Event]:
        """Get event history for audit"""
        if event_type:
            return [e for e in self.event_history if e.type == event_type][-limit:]
        return self.event_history[-limit:]
    
    async def get_stats(self) -> Dict[str, Any]:
        """Get event bus statistics"""
        counts = {}
        for event in self.event_history:
            counts[event.type.value] = counts.get(event.type.value, 0) + 1
        
        return {
            "total_events": len(self.event_history),
            "event_counts": counts,
            "subscribers": {k.value: len(v) for k, v in self.subscribers.items()}
        }


# Singleton instance
event_bus = SovereignEventBus()