"""
Event Service - Blockchain-style event bus with persistence
"""

import asyncio
import json
import hashlib
import time
import sqlite3
from enum import Enum
from typing import Dict, Any, Optional, List
from collections import defaultdict
from dataclasses import dataclass, field

class EventType(str, Enum):
    SYSTEM_BOOT = "system.boot"
    WORKER_START = "worker.start"
    WORKER_COMPLETE = "worker.complete"
    WORKER_ERROR = "worker.error"
    SCE_BLUEPRINT_CREATED = "sce.blueprint.created"
    CONSTITUTION_RULING = "constitution.ruling"
    AUTH_FAILURE = "auth.failure"
    MEMORY_STORED = "cortex.memory.stored"
    WORKER_LOADED = "worker.loaded"
    EXTERNAL_API_CALL = "external.api.call"
    USER_FEEDBACK = "user.feedback"

@dataclass
class Event:
    type: EventType
    source: str
    payload: Dict[str, Any]
    timestamp: float = field(default_factory=time.time)
    previous_hash: str = ""
    vera_proof: str = field(init=False)
    
    def __post_init__(self):
        content = (
            f"{self.type.value}:{self.source}:"
            f"{json.dumps(self.payload, sort_keys=True)}:"
            f"{self.timestamp}:{self.previous_hash}"
        )
        self.vera_proof = hashlib.sha256(content.encode()).hexdigest()[:16]

class EventStore:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self._init_db()
    
    def _init_db(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS events (
                vera_proof TEXT PRIMARY KEY,
                type TEXT,
                source TEXT,
                payload TEXT,
                timestamp REAL,
                previous_hash TEXT,
                created_at REAL
            )
        ''')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_events_type ON events(type)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_events_timestamp ON events(timestamp)')
        conn.commit()
        conn.close()
    
    def save_event(self, event: Event) -> bool:
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute(
                "INSERT OR REPLACE INTO events (vera_proof, type, source, payload, timestamp, previous_hash, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (event.vera_proof, event.type.value, event.source, json.dumps(event.payload), event.timestamp, event.previous_hash, time.time())
            )
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"Failed to save event: {e}")
            return False
    
    def get_recent(self, limit: int = 100, event_type: Optional[str] = None) -> List[Dict]:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        if event_type:
            cursor.execute(
                "SELECT * FROM events WHERE type = ? ORDER BY timestamp DESC LIMIT ?",
                (event_type, limit)
            )
        else:
            cursor.execute("SELECT * FROM events ORDER BY timestamp DESC LIMIT ?", (limit,))
        
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]

class EventBus:
    def __init__(self, store: EventStore):
        self._chain: List[Event] = []
        self._lock = asyncio.Lock()
        self._genesis_hash = hashlib.sha256(b"REZONIC_GENESIS").hexdigest()[:16]
        self._store = store
        self._subscribers: Dict[str, List[callable]] = defaultdict(list)
        self._initialized = False
        self._persistence_queue = asyncio.Queue()
        self._persistence_task = None
    
    async def initialize(self):
        """Initialize the event bus"""
        if not self._initialized:
            await self._load_recent_events()
            self._persistence_queue = asyncio.Queue()
            self._initialized = True
            self._persistence_task = asyncio.create_task(self._persistence_worker())
            print("✅ Event bus initialized")
            await self.publish(Event(
                type=EventType.SYSTEM_BOOT,
                source="event_bus",
                payload={"version": "1.0.0"}
            ))
    
    async def _load_recent_events(self):
        """Load recent events from store"""
        try:
            events = self._store.get_recent(limit=1000)
            for evt_data in reversed(events):
                try:
                    event = Event(
                        type=EventType(evt_data['type']),
                        source=evt_data['source'],
                        payload=json.loads(evt_data['payload']),
                        timestamp=evt_data['timestamp'],
                        previous_hash=evt_data['previous_hash']
                    )
                    self._chain.append(event)
                except Exception as e:
                    print(f"Failed to load event: {e}")
            print(f"Loaded {len(self._chain)} events from store")
        except Exception as e:
            print(f"Failed to load events from store: {e}")
    
    async def _persistence_worker(self):
        """Background worker to persist events"""
        batch = []
        while True:
            try:
                event = await asyncio.wait_for(self._persistence_queue.get(), timeout=1.0)
                batch.append(event)
                if len(batch) >= 100:
                    await self._persist_batch(batch)
                    batch = []
            except asyncio.TimeoutError:
                if batch:
                    await self._persist_batch(batch)
                    batch = []
            except Exception as e:
                print(f"Persistence worker error: {e}")
                await asyncio.sleep(1)
    
    async def _persist_batch(self, batch: List[Event]):
        """Persist a batch of events"""
        for event in batch:
            self._store.save_event(event)
        print(f"Persisted {len(batch)} events")
    
    async def publish(self, event: Event) -> str:
        """Publish an event to the bus"""
        if not self._initialized:
            print("Event bus not initialized")
            return None
            
        async with self._lock:
            if self._chain:
                event.previous_hash = self._chain[-1].vera_proof
            else:
                event.previous_hash = self._genesis_hash
            
            if len(self._chain) >= 10000:
                self._chain.pop(0)
            self._chain.append(event)
            
            await self._persistence_queue.put(event)
        
        # Notify subscribers
        for callback in self._subscribers[event.type.value]:
            try:
                await callback(event)
            except Exception:
                pass
        
        return event.vera_proof
    
    def subscribe(self, event_type: str, callback: callable):
        """Subscribe to an event type"""
        self._subscribers[event_type].append(callback)
    
    async def verify_chain(self) -> bool:
        """Verify the integrity of the entire chain"""
        async with self._lock:
            prev = self._genesis_hash
            for ev in self._chain:
                content = f"{ev.type.value}:{ev.source}:{json.dumps(ev.payload, sort_keys=True)}:{ev.timestamp}:{prev}"
                expected = hashlib.sha256(content.encode()).hexdigest()[:16]
                if ev.vera_proof != expected:
                    return False
                prev = ev.vera_proof
            return True
    
    async def get_stats(self) -> Dict[str, Any]:
        """Get event bus statistics"""
        async with self._lock:
            counts = defaultdict(int)
            for ev in self._chain:
                counts[ev.type.value] += 1
            return {
                "total_events": len(self._chain),
                "chain_integrity": await self.verify_chain(),
                "genesis_hash": self._genesis_hash,
                "latest_hash": self._chain[-1].vera_proof if self._chain else self._genesis_hash,
                "event_counts": dict(counts),
                "persistence_queue": self._persistence_queue.qsize()
            }
    
    async def get_events_by_type(self, event_type: str, limit: int = 100) -> List[Dict]:
        """Get events by type from store"""
        return self._store.get_recent(limit=limit, event_type=event_type)
    
    async def shutdown(self):
        """Shutdown the event bus"""
        if self._persistence_task:
            self._persistence_task.cancel()
            try:
                await self._persistence_task
            except asyncio.CancelledError:
                pass