#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PHOENIX ULTIMATE v13.2.1 - COMPLETE WORKING VERSION
Zero Drift Architecture + Persistent Event Chain + Formalized Workers + Observability
"""

import sys
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

import uuid
import asyncio
import logging
import os
import json
import time
import hashlib
import random
import re
import secrets
import warnings
import psutil
import importlib.util
import inspect
import httpx
import pickle
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, Optional, List, Callable, Awaitable, Tuple, Union
from enum import Enum, auto
from dataclasses import dataclass, field, asdict
from collections import defaultdict
from functools import wraps
from contextlib import asynccontextmanager
from abc import ABC, abstractmethod

# Suppress warnings
warnings.filterwarnings("ignore", message=".*duckduckgo_search.*")

# =======================================================================
# THIRD-PARTY IMPORTS
# =======================================================================
try:
    from fastapi import FastAPI, Request, HTTPException, Depends, BackgroundTasks
    from fastapi.middleware.cors import CORSMiddleware
    from fastapi.responses import StreamingResponse, JSONResponse
    from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
    import uvicorn
    HAS_FASTAPI = True
except ImportError:
    print("❌ Install: pip install fastapi uvicorn")
    sys.exit(1)

try:
    import socketio
    HAS_SOCKETIO = True
except ImportError:
    HAS_SOCKETIO = False
    print("⚠️ Install: pip install python-socketio for real-time features")

try:
    from pydantic import BaseModel, Field, ConfigDict
    from pydantic_settings import BaseSettings, SettingsConfigDict
    HAS_PYDANTIC = True
except ImportError:
    HAS_PYDANTIC = False
    print("⚠️ Install: pip install pydantic pydantic-settings")

try:
    import aiofiles
    import aiofiles.os
    HAS_AIOFILES = True
except ImportError:
    HAS_AIOFILES = False
    print("⚠️ Install: pip install aiofiles for file operations")

try:
    from prometheus_client import Counter, Histogram, Gauge, generate_latest, start_http_server
    HAS_PROMETHEUS = True
except ImportError:
    HAS_PROMETHEUS = False
    print("⚠️ Install: pip install prometheus-client for metrics")

# =======================================================================
# LOGGING
# =======================================================================
from logging.handlers import RotatingFileHandler

os.makedirs('logs', exist_ok=True)
os.makedirs('data', exist_ok=True)
os.makedirs('data/event_store', exist_ok=True)

log_handler = RotatingFileHandler(
    'logs/phoenix_ultimate.log', maxBytes=10*1024*1024, backupCount=5, encoding='utf-8'
)
log_handler.setFormatter(logging.Formatter(
    "%(asctime)s [%(levelname)s] %(name)s - %(message)s"
))

logging.basicConfig(
    level=logging.INFO,
    handlers=[log_handler, logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("PHOENIX_ULTIMATE")

# =======================================================================
# PROMETHEUS METRICS (lazy initialization)
# =======================================================================
class MetricsRegistry:
    def __init__(self):
        self._initialized = False
        self.event_counter = None
        self.worker_duration = None
        self.active_connections = None
        self.blueprint_counter = None
        self.memory_usage = None
        self.drift_chain_length = None
        self.gpu_temp_gauge = None
        self.api_requests = None
        self.api_request_duration = None
    
    def initialize(self):
        if not self._initialized and HAS_PROMETHEUS:
            self.event_counter = Counter('phoenix_events_total', 'Total events published', ['event_type'])
            self.worker_duration = Histogram('phoenix_worker_duration_seconds', 'Worker execution time', ['worker_name'])
            self.active_connections = Gauge('phoenix_active_connections', 'Active WebSocket connections')
            self.blueprint_counter = Counter('phoenix_blueprints_total', 'Total blueprints created')
            self.memory_usage = Gauge('phoenix_memory_entries', 'Memory store entries')
            self.drift_chain_length = Gauge('phoenix_drift_chain_length', 'Drift chain length')
            self.gpu_temp_gauge = Gauge('phoenix_gpu_temperature', 'GPU temperature')
            self.api_requests = Counter('phoenix_api_requests_total', 'API requests', ['endpoint', 'method'])
            self.api_request_duration = Histogram('phoenix_api_request_duration_seconds', 'API request duration', ['endpoint'])
            self._initialized = True
            logger.info("✅ Prometheus metrics initialized")

metrics = MetricsRegistry()

# =======================================================================
# CONFIGURATION
# =======================================================================
class Settings(BaseSettings):
    environment: str = os.getenv("ENV", "development")
    port: int = int(os.getenv("PHOENIX_PORT", "8002"))
    metrics_port: int = int(os.getenv("METRICS_PORT", "8003"))
    host: str = os.getenv("PHOENIX_HOST", "0.0.0.0")
    log_level: str = os.getenv("LOG_LEVEL", "INFO")
    
    # Security
    api_key_admin: str = os.getenv("PHOENIX_ADMIN_KEY", secrets.token_urlsafe(32))
    api_key_viewer: str = os.getenv("PHOENIX_VIEWER_KEY", secrets.token_urlsafe(32))
    allowed_hosts: str = os.getenv("ALLOWED_HOSTS", "*")
    
    # Directories
    upload_dir: Path = Path("data/uploads")
    quarantine_dir: Path = Path("quarantine")
    memory_dir: Path = Path("data/memory")
    event_store_dir: Path = Path("data/event_store")
    bots_dir: Path = Path("bots")
    workers_dir: Path = Path("workers")
    
    # Ollama
    ollama_url: str = os.getenv("OLLAMA_URL", "http://localhost:11434")
    default_model: str = os.getenv("OLLAMA_MODEL", "llama3.2:latest")
    ollama_timeout: int = int(os.getenv("OLLAMA_TIMEOUT", "60"))
    ollama_retries: int = int(os.getenv("OLLAMA_RETRIES", "3"))
    ollama_retry_delay: float = float(os.getenv("OLLAMA_RETRY_DELAY", "1.0"))
    
    # API Keys (populated from env)
    api_keys: Dict[str, str] = {
        "rez-hive-admin-key-2026": "admin",
    }
    
    # Event chain
    chain_maxlen: int = 10000
    event_persistence_batch: int = 100
    
    # CORS
    frontend_urls: list = [
        "http://localhost:3000", "http://127.0.0.1:3000",
        "http://localhost:5173", "http://127.0.0.1:5173",
        "http://localhost:8002", "http://127.0.0.1:8002"
    ]
    
    # Circuit breaker
    circuit_breaker_threshold: int = 5
    circuit_breaker_timeout: int = 60
    
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
    
    def validate(self):
        admin_key = os.getenv("PHOENIX_ADMIN_KEY")
        if admin_key:
            self.api_keys[admin_key] = "admin"
        viewer_key = os.getenv("PHOENIX_VIEWER_KEY") 
        if viewer_key:
            self.api_keys[viewer_key] = "viewer"
        return True

settings = Settings()
settings.validate()

# Create directories
for d in [settings.upload_dir, settings.quarantine_dir, settings.memory_dir, 
          settings.bots_dir, settings.workers_dir, settings.event_store_dir]:
    d.mkdir(parents=True, exist_ok=True)

# =======================================================================
# PYDANTIC MODELS
# =======================================================================
if HAS_PYDANTIC:
    class SCEBlueprintModel(BaseModel):
        protocol_version: str
        timestamp: str
        intent: Dict[str, Any]
        dna: Dict[str, Any]
        execution: Dict[str, Any]
        parent_drift_lock: Optional[str] = None
        master_drift_lock: Optional[str] = None
        model_config = ConfigDict(extra='forbid')
    
    class EventModel(BaseModel):
        type: str
        source: str
        payload: Dict[str, Any]
        timestamp: float
        previous_hash: str
        vera_proof: str
        model_config = ConfigDict(extra='forbid')
    
    class WorkerConfig(BaseModel):
        name: str
        enabled: bool = True
        max_concurrent: int = 5
        timeout: int = 30
        requires_gpu: bool = False
        environment: Dict[str, str] = Field(default_factory=dict)
        model_config = ConfigDict(extra='allow')

# =======================================================================
# SECURITY UTILITIES
# =======================================================================
class SecurityError(Exception):
    pass

def sanitize_input(text: str, max_length: int = 10000) -> str:
    if not isinstance(text, str):
        raise SecurityError("Input must be string")
    if len(text) > max_length:
        raise SecurityError(f"Input exceeds {max_length} chars")
    sanitized = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]', '', text)
    if '..' in sanitized or '~' in sanitized:
        raise SecurityError("Path traversal attempt")
    return sanitized.strip()

def validate_safe_path(base_dir: Path, user_path: str) -> Path:
    base = base_dir.resolve()
    if os.path.isabs(user_path):
        raise SecurityError("Absolute paths not allowed")
    target = (base / user_path).resolve()
    try:
        target.relative_to(base)
    except ValueError:
        raise SecurityError("Path escapes base directory")
    return target

# =======================================================================
# CIRCUIT BREAKER
# =======================================================================
class CircuitBreaker:
    def __init__(self, name: str, threshold: int = 5, timeout: int = 60):
        self.name = name
        self.threshold = threshold
        self.timeout = timeout
        self.failure_count = 0
        self.last_failure_time = 0
        self.state = "CLOSED"
        self._lock = asyncio.Lock()
    
    async def call(self, func: Callable, *args, **kwargs):
        async with self._lock:
            if self.state == "OPEN":
                if time.time() - self.last_failure_time > self.timeout:
                    self.state = "HALF_OPEN"
                    logger.info(f"Circuit {self.name} half-open")
                else:
                    raise Exception(f"Circuit {self.name} is OPEN")
        
        try:
            result = await func(*args, **kwargs) if asyncio.iscoroutinefunction(func) else func(*args, **kwargs)
            async with self._lock:
                if self.state == "HALF_OPEN":
                    self.state = "CLOSED"
                    self.failure_count = 0
                    logger.info(f"Circuit {self.name} closed (success)")
            return result
        except Exception as e:
            async with self._lock:
                self.failure_count += 1
                self.last_failure_time = time.time()
                if self.state == "CLOSED" and self.failure_count >= self.threshold:
                    self.state = "OPEN"
                    logger.warning(f"Circuit {self.name} opened (failures: {self.failure_count})")
                elif self.state == "HALF_OPEN":
                    self.state = "OPEN"
                    logger.warning(f"Circuit {self.name} re-opened from half-open")
            raise e

# =======================================================================
# GPU MONITOR
# =======================================================================
class GPUMonitor:
    def __init__(self):
        self.has_gpu = False
        self.name = "N/A"
        self.temp = 0
        self.utilization = 0
        self.memory_used = 0
        self.memory_total = 0
        self._update_task = None
        self._init_gpu()
        
    def _init_gpu(self):
        try:
            import pynvml
            pynvml.nvmlInit()
            device_count = pynvml.nvmlDeviceGetCount()
            if device_count > 0:
                self.handle = pynvml.nvmlDeviceGetHandleByIndex(0)
                name_data = pynvml.nvmlDeviceGetName(self.handle)
                self.name = name_data.decode('utf-8') if isinstance(name_data, bytes) else name_data
                self.has_gpu = True
                self.update_stats()
                logger.info(f"✅ GPU detected: {self.name}")
        except ImportError:
            logger.info("ℹ️ pynvml not installed - GPU stats disabled")
        except Exception as e:
            logger.info(f"ℹ️ GPU monitoring disabled: {e}")
    
    async def start_background_updates(self):
        if self.has_gpu and not self._update_task:
            self._update_task = asyncio.create_task(self._background_update())
            logger.info("✅ GPU background monitoring started")
    
    async def _background_update(self):
        while True:
            try:
                self.update_stats()
                if metrics._initialized and metrics.gpu_temp_gauge:
                    metrics.gpu_temp_gauge.set(self.temp)
                await asyncio.sleep(5)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"GPU update error: {e}")
                await asyncio.sleep(10)
    
    def update_stats(self):
        if not self.has_gpu:
            return
        try:
            import pynvml
            try:
                self.temp = pynvml.nvmlDeviceGetTemperature(self.handle, pynvml.NVML_TEMPERATURE_GPU)
            except:
                self.temp = 0
            try:
                util = pynvml.nvmlDeviceGetUtilizationRates(self.handle)
                self.utilization = util.gpu
            except:
                self.utilization = 0
            try:
                mem_info = pynvml.nvmlDeviceGetMemoryInfo(self.handle)
                self.memory_used = mem_info.used // 1024 // 1024
                self.memory_total = mem_info.total // 1024 // 1024
            except:
                pass
        except:
            pass
    
    async def shutdown(self):
        if self._update_task:
            self._update_task.cancel()
            try:
                await self._update_task
            except asyncio.CancelledError:
                pass

gpu = GPUMonitor()

# =======================================================================
# PERSISTENT EVENT STORE
# =======================================================================
class EventStore:
    def __init__(self, db_path: Path):
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
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS blueprints (
                drift_lock TEXT PRIMARY KEY,
                blueprint TEXT,
                timestamp REAL
            )
        ''')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_events_type ON events(type)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_events_timestamp ON events(timestamp)')
        conn.commit()
        conn.close()
    
    async def save_event(self, event) -> bool:
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
            logger.error(f"Failed to save event: {e}")
            return False
    
    async def save_blueprint(self, drift_lock: str, blueprint: dict) -> bool:
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute(
                "INSERT OR REPLACE INTO blueprints (drift_lock, blueprint, timestamp) VALUES (?, ?, ?)",
                (drift_lock, json.dumps(blueprint), time.time())
            )
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            logger.error(f"Failed to save blueprint: {e}")
            return False
    
    async def get_events(self, limit: int = 100, event_type: Optional[str] = None) -> List[Dict]:
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
    
    async def get_blueprint(self, drift_lock: str) -> Optional[Dict]:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT blueprint FROM blueprints WHERE drift_lock = ?", (drift_lock,))
        row = cursor.fetchone()
        conn.close()
        if row:
            return json.loads(row[0])
        return None

# =======================================================================
# SCE PROTOCOL
# =======================================================================
class SCEProtocol:
    VERSION = "1.0.0"
    
    @staticmethod
    def create_drift_lock(data: Any) -> str:
        content = json.dumps(data, sort_keys=True, default=str)
        return hashlib.sha256(content.encode()).hexdigest()[:16]
    
    @staticmethod
    def create_blueprint(intent: dict, dna: dict, execution: dict, parent_lock: str = None) -> dict:
        blueprint = {
            "protocol_version": SCEProtocol.VERSION,
            "timestamp": datetime.now().isoformat(),
            "intent": intent,
            "dna": dna,
            "execution": execution
        }
        if parent_lock:
            blueprint["parent_drift_lock"] = parent_lock
        blueprint["master_drift_lock"] = SCEProtocol.create_drift_lock(blueprint)
        return blueprint
    
    @staticmethod
    def verify_blueprint(blueprint: dict) -> dict:
        stored_lock = blueprint.get('master_drift_lock')
        calculated_lock = SCEProtocol.create_drift_lock(blueprint)
        is_valid = stored_lock == calculated_lock
        return {
            'verified': is_valid,
            'badge': '🟢 SOVEREIGN' if is_valid else '🔴 DRIFTED',
            'drift_lock': stored_lock
        }

# =======================================================================
# EVENT BUS
# =======================================================================
class EventType(Enum):
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

@dataclass(frozen=True)
class Event:
    type: EventType
    source: str
    payload: Dict[str, Any]
    timestamp: float = field(default_factory=time.time)
    previous_hash: str = ""

    def __post_init__(self):
        content = (
            f"{self.type.value}:{self.source}:"
            f"{json.dumps(self.payload, sort_keys=True)}:"
            f"{self.timestamp}:{self.previous_hash}"
        )
        object.__setattr__(self, '_vera_proof', hashlib.sha256(content.encode()).hexdigest()[:16])

    @property
    def vera_proof(self) -> str:
        return getattr(self, '_vera_proof', '')

class SovereignEventBus:
    def __init__(self):
        self._chain: List[Event] = []
        self._lock = asyncio.Lock()
        self._genesis_hash = hashlib.sha256(b"PHOENIX_ULTIMATE_v13.2.1").hexdigest()[:16]
        self._initialized = False
        self._persistence_queue = None
        self._store = EventStore(settings.event_store_dir / "events.db")
        self._persistence_task = None

    async def initialize(self):
        if not self._initialized:
            await self._load_recent_events()
            self._persistence_queue = asyncio.Queue()
            self._initialized = True
            self._persistence_task = asyncio.create_task(self._persistence_worker())
            logger.info("✅ Event bus initialized")
            await self.publish(Event(
                type=EventType.SYSTEM_BOOT,
                source="event_bus",
                payload={"version": "13.2.1"}
            ))
    
    async def _load_recent_events(self):
        try:
            events = await self._store.get_events(limit=settings.chain_maxlen)
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
                    logger.error(f"Failed to load event: {e}")
            logger.info(f"Loaded {len(self._chain)} events from store")
        except Exception as e:
            logger.error(f"Failed to load events from store: {e}")
    
    async def _persistence_worker(self):
        batch = []
        while True:
            try:
                event = await asyncio.wait_for(self._persistence_queue.get(), timeout=1.0)
                batch.append(event)
                if len(batch) >= settings.event_persistence_batch:
                    await self._persist_batch(batch)
                    batch = []
            except asyncio.TimeoutError:
                if batch:
                    await self._persist_batch(batch)
                    batch = []
            except Exception as e:
                logger.error(f"Persistence worker error: {e}")
                await asyncio.sleep(1)
    
    async def _persist_batch(self, batch: List[Event]):
        for event in batch:
            await self._store.save_event(event)
        if metrics._initialized and metrics.event_counter:
            metrics.event_counter.labels(event_type='batch').inc(len(batch))
        logger.debug(f"Persisted {len(batch)} events")

    async def publish(self, event: Event):
        if not self._initialized:
            logger.warning("Event bus not initialized, event not published")
            return None
        async with self._lock:
            if self._chain:
                linked = Event(
                    type=event.type,
                    source=event.source,
                    payload=event.payload,
                    timestamp=event.timestamp,
                    previous_hash=self._chain[-1].vera_proof
                )
            else:
                linked = Event(
                    type=event.type,
                    source=event.source,
                    payload=event.payload,
                    timestamp=event.timestamp,
                    previous_hash=self._genesis_hash
                )
            if len(self._chain) >= settings.chain_maxlen:
                self._chain.pop(0)
            self._chain.append(linked)
            if self._persistence_queue:
                await self._persistence_queue.put(linked)
        if metrics._initialized and metrics.event_counter:
            metrics.event_counter.labels(event_type=linked.type.value).inc()
        logger.debug(f"Published {linked.type.value} [{linked.vera_proof}]")
        return linked.vera_proof

    async def verify_chain(self) -> bool:
        async with self._lock:
            prev = self._genesis_hash
            for ev in self._chain:
                content = f"{ev.type.value}:{ev.source}:{json.dumps(ev.payload, sort_keys=True)}:{ev.timestamp}:{prev}"
                expected = hashlib.sha256(content.encode()).hexdigest()[:16]
                if ev.vera_proof != expected:
                    logger.error(f"Chain broken at {ev.vera_proof}")
                    return False
                prev = ev.vera_proof
            return True

    async def get_stats(self) -> Dict[str, Any]:
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
                "persistence_queue": self._persistence_queue.qsize() if self._persistence_queue else 0
            }
    
    async def get_events_by_type(self, event_type: str, limit: int = 100) -> List[Dict]:
        return await self._store.get_events(limit=limit, event_type=event_type)
    
    async def shutdown(self):
        if self._persistence_task:
            self._persistence_task.cancel()
            try:
                await self._persistence_task
            except asyncio.CancelledError:
                pass

event_bus = SovereignEventBus()

# =======================================================================
# AUTHENTICATION
# =======================================================================
class AuthManager:
    def __init__(self):
        self._keys = settings.api_keys
        self._lock = asyncio.Lock()
        self._rate_limits = defaultdict(list)

    async def verify_key(self, api_key: Optional[str], client_ip: str = None) -> str:
        if not api_key:
            raise HTTPException(status_code=403, detail="API key required")
        if client_ip:
            now = time.time()
            self._rate_limits[client_ip] = [t for t in self._rate_limits[client_ip] if t > now - 60]
            if len(self._rate_limits[client_ip]) > 100:
                raise HTTPException(status_code=429, detail="Rate limit exceeded")
            self._rate_limits[client_ip].append(now)
        async with self._lock:
            role = self._keys.get(api_key)
        if not role:
            await event_bus.publish(Event(
                type=EventType.AUTH_FAILURE,
                source="auth_manager",
                payload={"client_ip": client_ip}
            ))
            raise HTTPException(status_code=403, detail="Invalid API key")
        return role

    def require_role(self, required_role: str):
        async def dep(
            request: Request,
            api_key: Optional[str] = Depends(HTTPBearer(auto_error=False))
        ) -> str:
            client_ip = request.client.host if request.client else None
            key = api_key.credentials if api_key else request.headers.get("X-Hive-API-Key")
            role = await self.verify_key(key, client_ip)
            if required_role == "admin" and role != "admin":
                raise HTTPException(status_code=403, detail="Admin access required")
            return role
        return dep

auth_manager = AuthManager()

# =======================================================================
# WORKER INTERFACE
# =======================================================================
class Worker(ABC):
    def __init__(self, config: Optional['WorkerConfig'] = None):
        self.config = config or WorkerConfig(name=self.__class__.__name__)
        self.metrics = {
            'calls': 0,
            'errors': 0,
            'total_duration': 0,
            'last_call': None
        }
        self._lock = asyncio.Lock()
    
    @abstractmethod
    async def execute(self, task: str, **kwargs) -> Dict[str, Any]:
        pass
    
    async def validate(self, task: str) -> bool:
        return True
    
    async def get_metrics(self) -> Dict[str, Any]:
        async with self._lock:
            return {
                **self.metrics,
                'avg_duration': self.metrics['total_duration'] / self.metrics['calls'] if self.metrics['calls'] > 0 else 0
            }
    
    def _record_call(self, duration: float, success: bool):
        async def _record():
            async with self._lock:
                self.metrics['calls'] += 1
                self.metrics['total_duration'] += duration
                self.metrics['last_call'] = time.time()
                if not success:
                    self.metrics['errors'] += 1
        asyncio.create_task(_record())

# =======================================================================
# SCE DECORATOR
# =======================================================================
def sce_compliant(worker_name: str = "unknown"):
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            intent = {
                "worker": worker_name,
                "function": func.__name__,
                "timestamp": time.time(),
                "args": str(args)[:100],
                "kwargs": str(kwargs)[:100]
            }
            start = time.time()
            try:
                await event_bus.publish(Event(
                    type=EventType.WORKER_START,
                    source=worker_name,
                    payload={"function": func.__name__}
                ))
                if asyncio.iscoroutinefunction(func):
                    result = await func(*args, **kwargs)
                else:
                    result = func(*args, **kwargs)
                duration = time.time() - start
                execution = {
                    "result": str(result)[:200] if result else "None",
                    "success": True,
                    "duration": duration
                }
                dna = {"narrative": [f"{worker_name} executed {func.__name__}"]}
                blueprint = SCEProtocol.create_blueprint(intent, dna, execution)
                await event_bus.publish(Event(
                    type=EventType.SCE_BLUEPRINT_CREATED,
                    source=worker_name,
                    payload={"blueprint": blueprint}
                ))
                await event_bus.publish(Event(
                    type=EventType.WORKER_COMPLETE,
                    source=worker_name,
                    payload={"duration": duration, "success": True}
                ))
                if metrics._initialized and metrics.worker_duration:
                    metrics.worker_duration.labels(worker_name=worker_name).observe(duration)
                return {
                    "sce_compliant": True,
                    "blueprint": blueprint,
                    "result": result,
                    "drift_lock": blueprint["master_drift_lock"]
                }
            except Exception as e:
                duration = time.time() - start
                execution = {
                    "error": str(e),
                    "success": False,
                    "duration": duration
                }
                dna = {"narrative": [f"{worker_name} failed: {str(e)}"]}
                blueprint = SCEProtocol.create_blueprint(intent, dna, execution)
                await event_bus.publish(Event(
                    type=EventType.WORKER_ERROR,
                    source=worker_name,
                    payload={"blueprint": blueprint, "error": str(e)}
                ))
                if metrics._initialized and metrics.worker_duration:
                    metrics.worker_duration.labels(worker_name=worker_name).observe(duration)
                return {
                    "sce_compliant": True,
                    "blueprint": blueprint,
                    "error": str(e),
                    "drift_lock": blueprint["master_drift_lock"]
                }
        return wrapper
    return decorator

# =======================================================================
# WORKER CACHE
# =======================================================================
class WorkerCache:
    def __init__(self):
        self._instances = {}
        self._locks = defaultdict(asyncio.Lock)
        self._metrics = defaultdict(int)
    
    async def get_worker(self, worker_class, config: Optional['WorkerConfig'] = None) -> Worker:
        key = f"{worker_class.__name__}"
        async with self._locks[key]:
            if key not in self._instances:
                self._instances[key] = worker_class(config)
                self._metrics['loads'] += 1
                logger.info(f"Loaded worker: {key}")
            return self._instances[key]
    
    async def reload_worker(self, worker_name: str) -> bool:
        async with self._locks[worker_name]:
            if worker_name in self._instances:
                self._instances.pop(worker_name)
                self._metrics['reloads'] += 1
                return True
        return False
    
    def clear(self):
        self._instances.clear()
        self._metrics['clears'] += 1
    
    async def get_metrics(self) -> Dict[str, Any]:
        worker_metrics = {}
        for name, worker in self._instances.items():
            worker_metrics[name] = await worker.get_metrics()
        return {
            "cache": dict(self._metrics),
            "workers": worker_metrics,
            "active_workers": len(self._instances)
        }

worker_cache = WorkerCache()

# =======================================================================
# WORKER LOADER
# =======================================================================
class WorkerLoader:
    def __init__(self, workers_dir: str = "workers"):
        self.workers_dir = Path(workers_dir).resolve()
        self.workers = {}
        self.failed_imports = []
        if str(self.workers_dir) not in sys.path:
            sys.path.insert(0, str(self.workers_dir))
        if str(self.workers_dir.parent) not in sys.path:
            sys.path.insert(0, str(self.workers_dir.parent))
        logger.info(f"📁 Worker directory: {self.workers_dir}")
        logger.info(f"📂 Directory exists: {self.workers_dir.exists()}")
    
    def is_worker_class(self, obj, class_name: str, module_name: str) -> bool:
        if 'Worker' in class_name:
            return True
        try:
            for base in obj.__bases__:
                base_name = base.__name__
                if 'Worker' in base_name:
                    return True
                for deeper in base.__bases__:
                    if 'Worker' in deeper.__name__:
                        return True
        except:
            pass
        worker_methods = ['execute', 'process', 'run', 'handle', 'work']
        methods = [m for m in dir(obj) if not m.startswith('_')]
        if any(method in methods for method in worker_methods):
            return True
        if 'worker' in module_name.lower():
            return True
        return False
    
    def safe_import_module(self, file_path: Path):
        module_name = file_path.stem
        try:
            spec = importlib.util.spec_from_file_location(module_name, file_path)
            if spec and spec.loader:
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                return module
        except Exception as e:
            logger.debug(f"  ⚠️ Strategy 1 failed for {module_name}: {e}")
        try:
            import importlib.machinery
            loader = importlib.machinery.SourceFileLoader(module_name, str(file_path))
            module = loader.load_module()
            return module
        except Exception as e:
            logger.debug(f"  ⚠️ Strategy 2 failed for {module_name}: {e}")
        try:
            import importlib
            module = importlib.import_module(module_name)
            return module
        except Exception as e:
            logger.debug(f"  ⚠️ Strategy 3 failed for {module_name}: {e}")
        return None
    
    def load_all(self):
        if not self.workers_dir.exists():
            logger.error(f"❌ Workers directory NOT FOUND: {self.workers_dir}")
            return {}
        all_files = list(self.workers_dir.glob("*.py"))
        logger.info(f"📦 Found {len(all_files)} Python files")
        exclude_patterns = ['__init__.py', 'base_worker.py']
        worker_files = [f for f in all_files if f.name not in exclude_patterns]
        logger.info(f"🔍 Attempting to load {len(worker_files)} potential worker files...")
        for py_file in worker_files:
            try:
                module = self.safe_import_module(py_file)
                if not module:
                    logger.error(f"  ❌ Could not import {py_file.name}")
                    self.failed_imports.append(py_file.name)
                    continue
                classes_found = 0
                worker_classes_found = 0
                for name, obj in inspect.getmembers(module, inspect.isclass):
                    classes_found += 1
                    if obj.__module__ != module.__name__:
                        continue
                    if self.is_worker_class(obj, name, py_file.stem):
                        worker_classes_found += 1
                        sce_compliant = False
                        try:
                            for base in obj.__bases__:
                                if 'SCEWorker' in str(base):
                                    sce_compliant = True
                                    break
                        except:
                            pass
                        self.workers[name] = {
                            "module": py_file.stem,
                            "class": obj,
                            "path": str(py_file),
                            "sce_compliant": sce_compliant,
                            "loaded_at": time.time(),
                            "methods": [m for m in dir(obj) if not m.startswith('_') and callable(getattr(obj, m, None))]
                        }
                        logger.info(f"  ✅ Loaded worker: {name} from {py_file.name}")
                if worker_classes_found == 0 and classes_found > 0:
                    logger.warning(f"  ⚠️ No worker classes in {py_file.name} (found {classes_found} other classes)")
                elif classes_found == 0:
                    logger.warning(f"  ⚠️ No classes at all in {py_file.name}")
            except Exception as e:
                logger.error(f"  ❌ Failed to load {py_file.name}: {e}")
                import traceback
                logger.error(traceback.format_exc())
                self.failed_imports.append(py_file.name)
        logger.info(f"📊 Total workers loaded: {len(self.workers)}")
        if self.failed_imports:
            logger.warning(f"⚠️ Failed imports: {len(self.failed_imports)} files")
            for f in self.failed_imports[:5]:
                logger.warning(f"   - {f}")
        return self.workers

# =======================================================================
# CONSTITUTION
# =======================================================================
class Constitution:
    def __init__(self):
        self.rulings = []
        self.laws = ["SOVEREIGNTY", "TRANSPARENCY", "ACCOUNTABILITY", "SAFETY"]
        self.whitelist = ['/health', '/workers', '/sys', '/ollama', '/metrics']
        self.ruling_history = []

    def evaluate(self, action: str, context: Optional[Dict] = None) -> dict:
        action_lower = action.lower()
        if any(cmd in action_lower for cmd in self.whitelist):
            ruling = {"approved": True, "reason": "Whitelist", "score": 100}
            self._record_ruling(action, ruling)
            return ruling
        dangerous = ['rm -rf', 'format', 'del ', 'shutdown', 'reboot', 'mkfs']
        for d in dangerous:
            if d in action_lower:
                ruling = {"approved": False, "reason": f"SAFETY violation: {d}", "score": 0}
                self._record_ruling(action, ruling)
                return ruling
        system_paths = ['/etc', '/bin', '/boot', '/dev', '/proc', '/sys']
        if any(path in action_lower for path in system_paths):
            if context and context.get('role') != 'admin':
                ruling = {"approved": False, "reason": "System path access requires admin", "score": 30}
                self._record_ruling(action, ruling)
                return ruling
        ruling = {
            "approved": True, 
            "score": 90, 
            "reason": "SCE applied",
            "laws_applied": ["TRANSPARENCY", "ACCOUNTABILITY"]
        }
        self._record_ruling(action, ruling)
        return ruling
    
    def _record_ruling(self, action: str, ruling: dict):
        record = {
            "timestamp": time.time(),
            "action": action[:100],
            "ruling": ruling
        }
        self.ruling_history.append(record)
        if len(self.ruling_history) > 1000:
            self.ruling_history.pop(0)
        asyncio.create_task(self._publish_ruling(record))
    
    async def _publish_ruling(self, record: dict):
        try:
            await event_bus.publish(Event(
                type=EventType.CONSTITUTION_RULING,
                source="constitution",
                payload=record
            ))
        except:
            pass
    
    def get_stats(self) -> Dict[str, Any]:
        approved = sum(1 for r in self.ruling_history if r['ruling']['approved'])
        total = len(self.ruling_history)
        return {
            "total_rulings": total,
            "approved": approved,
            "denied": total - approved,
            "approval_rate": approved / total if total > 0 else 0,
            "laws": self.laws,
            "recent": self.ruling_history[-10:]
        }

# =======================================================================
# INTENT ROUTER
# =======================================================================
class IntentRouter:
    def __init__(self):
        self.intent_map = {
            'brain': ['explain', 'analyze', 'think', 'what', 'how', 'tell', 'why', 'describe'],
            'code': ['write', 'code', 'script', 'program', 'function', 'implement', 'debug'],
            'cortex': ['memory', 'recall', 'remember', 'forget', 'store'],
            'file': ['read', 'write', 'save', 'load', 'file', 'directory'],
            'web': ['search', 'browse', 'fetch', 'download', 'scrape'],
            'data': ['analyze', 'process', 'transform', 'convert', 'parse']
        }
        self.routing_stats = defaultdict(lambda: {'hits': 0, 'success': 0})

    def route(self, task: str) -> str:
        task_lower = task.lower()
        scores = {}
        for worker, keywords in self.intent_map.items():
            score = sum(1 for kw in keywords if kw in task_lower)
            if score > 0:
                scores[worker] = score
        if not scores:
            return 'brain'
        best_worker = max(scores.items(), key=lambda x: x[1])[0]
        self.routing_stats[best_worker]['hits'] += 1
        return best_worker
    
    def report_success(self, worker: str, success: bool):
        if success:
            self.routing_stats[worker]['success'] += 1
    
    def get_stats(self) -> Dict[str, Any]:
        stats = {}
        for worker, data in self.routing_stats.items():
            stats[worker] = {
                **data,
                'success_rate': data['success'] / data['hits'] if data['hits'] > 0 else 0
            }
        return stats

# =======================================================================
# SOVEREIGN MEMORY
# =======================================================================
class SovereignMemory:
    def __init__(self):
        self.memories = {}
        self.blueprint_index = {}
        self._store = EventStore(settings.event_store_dir / "events.db")
        self._update_task = None
        self._load()

    def store_blueprint(self, blueprint: Dict) -> str:
        lock = blueprint.get('master_drift_lock', SCEProtocol.create_drift_lock(blueprint))
        self.memories[lock] = {
            'value': blueprint, 
            'timestamp': time.time(),
            'access_count': 0
        }
        self.blueprint_index[lock] = lock
        try:
            path = settings.memory_dir / f"sce_{lock}.json"
            with open(path, 'w') as f:
                json.dump(self.memories[lock], f, indent=2)
            asyncio.create_task(self._store.save_blueprint(lock, blueprint))
        except Exception as e:
            logger.error(f"Failed to persist blueprint: {e}")
        if metrics._initialized and metrics.blueprint_counter:
            metrics.blueprint_counter.inc()
            metrics.memory_usage.set(len(self.memories))
        return lock

    def verify(self, drift_lock: str) -> dict:
        record = self.memories.get(drift_lock)
        if not record:
            return {'verified': False, 'error': 'Blueprint not found'}
        record['access_count'] = record.get('access_count', 0) + 1
        return SCEProtocol.verify_blueprint(record['value'])

    def search(self, query: str, limit: int = 10) -> List[Dict]:
        results = []
        query_lower = query.lower()
        for lock, record in self.memories.items():
            blueprint = record['value']
            score = 0
            intent_str = json.dumps(blueprint.get('intent', {})).lower()
            dna_str = json.dumps(blueprint.get('dna', {})).lower()
            if query_lower in intent_str:
                score += 5
            if query_lower in dna_str:
                score += 3
            if score > 0:
                results.append({
                    'lock': lock,
                    'score': score,
                    'timestamp': record['timestamp'],
                    'intent': blueprint.get('intent'),
                    'access_count': record.get('access_count', 0)
                })
        results.sort(key=lambda x: (x['score'], x['timestamp']), reverse=True)
        return results[:limit]

    def _load(self):
        for p in settings.memory_dir.glob("*.json"):
            try:
                with open(p) as f:
                    data = json.load(f)
                    if 'value' in data and 'master_drift_lock' in data['value']:
                        lock = data['value']['master_drift_lock']
                        self.memories[lock] = data
                        self.blueprint_index[lock] = lock
            except:
                pass
    
    async def start_background_updates(self):
        if not self._update_task:
            self._update_task = asyncio.create_task(self._update_metrics())
            logger.info("✅ Memory background updates started")
    
    async def _update_metrics(self):
        while True:
            try:
                if metrics._initialized and metrics.memory_usage:
                    metrics.memory_usage.set(len(self.memories))
                await asyncio.sleep(30)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Memory metrics error: {e}")
                await asyncio.sleep(60)
    
    async def shutdown(self):
        if self._update_task:
            self._update_task.cancel()
            try:
                await self._update_task
            except asyncio.CancelledError:
                pass

# =======================================================================
# OLLAMA CLIENT
# =======================================================================
class OllamaClient:
    def __init__(self):
        self.circuit_breaker = CircuitBreaker(
            "ollama", 
            threshold=settings.circuit_breaker_threshold,
            timeout=settings.circuit_breaker_timeout
        )
        self.client = None
        self.stats = {
            'calls': 0,
            'failures': 0,
            'total_tokens': 0,
            'last_call': None
        }
    
    async def initialize(self):
        self.client = httpx.AsyncClient(timeout=settings.ollama_timeout)
        logger.info("✅ Ollama client initialized")
    
    async def generate(self, prompt: str, stream: bool = True, system: str = None):
        if not self.client:
            await self.initialize()
        url = f"{settings.ollama_url}/api/generate"
        payload = {
            "model": settings.default_model,
            "prompt": prompt,
            "stream": stream
        }
        if system:
            payload["system"] = system
        self.stats['calls'] += 1
        self.stats['last_call'] = time.time()
        if metrics._initialized and metrics.api_requests:
            metrics.api_requests.labels(endpoint='ollama', method='POST').inc()
        async def _call():
            async with self.client.stream("POST", url, json=payload) as response:
                if stream:
                    async for line in response.aiter_lines():
                        if line:
                            chunk = json.loads(line)
                            if 'response' in chunk:
                                self.stats['total_tokens'] += 1
                                yield chunk.get("response", "")
                            if chunk.get("done"):
                                break
                else:
                    data = await response.json()
                    yield data.get("response", "")
        if not stream:
            try:
                async for chunk in await self.circuit_breaker.call(_call):
                    yield chunk
            except Exception as e:
                self.stats['failures'] += 1
                yield f"\n[AI_UNAVAILABLE: {e}]"
        else:
            try:
                async for chunk in _call():
                    yield chunk
            except Exception as e:
                self.stats['failures'] += 1
                yield f"\n[AI_ERROR: {e}]"
    
    async def get_models(self):
        if not self.client:
            await self.initialize()
        try:
            url = f"{settings.ollama_url}/api/tags"
            response = await self.client.get(url, timeout=5.0)
            if response.status_code == 200:
                return response.json().get("models", [])
            return []
        except:
            return []
    
    async def get_stats(self):
        return {
            **self.stats,
            'circuit_breaker_state': self.circuit_breaker.state,
            'circuit_breaker_failures': self.circuit_breaker.failure_count
        }
    
    async def close(self):
        if self.client:
            await self.client.aclose()

# =======================================================================
# REFLEX COMMANDS
# =======================================================================
class Reflex:
    def __init__(self):
        self.commands = {
            '/health': self._health,
            '/sys': self._system,
            '/gpu': self._gpu,
            '/memory': self._memory,
            '/events': self._events,
            '/workers': self._workers,
            '/help': self._help
        }
    
    async def execute(self, cmd: str, kernel=None) -> Optional[Dict]:
        cmd = cmd.strip().lower()
        if cmd in self.commands:
            result = await self.commands[cmd](kernel)
            return {"content": result, "type": "reflex", "command": cmd}
        for prefix in self.commands:
            if cmd.startswith(prefix + ' '):
                result = await self.commands[prefix](kernel, cmd[len(prefix)+1:])
                return {"content": result, "type": "reflex", "command": prefix}
        return None
    
    async def _health(self, kernel=None) -> str:
        if kernel:
            stats = await kernel.get_stats()
            return json.dumps(stats, indent=2)
        return "Kernel not available"
    
    async def _system(self, kernel=None, args=None) -> str:
        gpu.update_stats()
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        return f"""SYSTEM STATUS:
CPU: {cpu_percent}% ({psutil.cpu_count()} cores)
RAM: {memory.percent}% ({memory.used//1024//1024}MB / {memory.total//1024//1024}MB)
DISK: {disk.percent}% ({disk.used//1024//1024//1024}GB / {disk.total//1024//1024//1024}GB)
GPU: {gpu.name if gpu.has_gpu else 'None'} {gpu.temp}°C {gpu.utilization}% used
Uptime: {time.time() - kernel.start_time if kernel else 0:.1f}s"""
    
    async def _gpu(self, kernel=None, args=None) -> str:
        gpu.update_stats()
        if not gpu.has_gpu:
            return "No GPU detected"
        return f"""GPU: {gpu.name}
Temperature: {gpu.temp}°C
Utilization: {gpu.utilization}%
Memory: {gpu.memory_used}MB / {gpu.memory_total}MB"""
    
    async def _memory(self, kernel=None, args=None) -> str:
        if not kernel:
            return "Kernel not available"
        if args and args.startswith('search '):
            query = args[7:]
            results = kernel.memory.search(query)
            if not results:
                return f"No memories found for: {query}"
            output = f"Memory search results for '{query}':\n"
            for r in results[:5]:
                output += f"\n[{r['lock']}] Score: {r['score']} | Accesses: {r['access_count']}"
            return output
        return f"Memory store: {len(kernel.memory.memories)} blueprints"
    
    async def _events(self, kernel=None, args=None) -> str:
        if not kernel:
            return "Kernel not available"
        stats = await kernel.event_bus.get_stats()
        return json.dumps(stats, indent=2)
    
    async def _workers(self, kernel=None, args=None) -> str:
        if not kernel:
            return "Kernel not available"
        if args == 'stats':
            metrics = await kernel.worker_cache.get_metrics()
            return json.dumps(metrics, indent=2)
        return f"Loaded workers: {len(kernel.workers)}\n{', '.join(kernel.workers.keys())}"
    
    async def _help(self, kernel=None, args=None) -> str:
        return """Available reflex commands:
/health - System health
/sys - System stats
/gpu - GPU info
/memory - Memory stats
/memory search <query> - Search memories
/events - Event bus stats
/workers - List workers
/workers stats - Worker metrics
/help - This help"""

# =======================================================================
# PHOENIX KERNEL
# =======================================================================
class PhoenixKernel:
    def __init__(self):
        self.version = "13.2.1"
        self.start_time = time.time()
        self.drift_chain = []
        self.constitution = Constitution()
        self.router = IntentRouter()
        self.memory = SovereignMemory()
        self.reflex = Reflex()
        self.ollama = OllamaClient()
        
        # Load workers
        self.workers_loader = WorkerLoader()
        self.workers = self.workers_loader.load_all() or {}
        
        # FastAPI App
        self.app = FastAPI(
            title=f"Phoenix v{self.version}",
            description="Zero Drift SCE Protocol with Enhanced Observability",
            version=self.version,
            docs_url="/docs" if settings.environment == "development" else None,
            redoc_url="/redoc" if settings.environment == "development" else None
        )
        
        # CORS - Configure based on environment
        origins = ["*"] if settings.environment == "development" else settings.frontend_urls
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=origins,
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        
        # Add metrics middleware
        if HAS_PROMETHEUS:
            self.app.middleware("http")(self.metrics_middleware)
        
        self.setup_routes()
        
        # Socket.IO
        self.sio = None
        if HAS_SOCKETIO:
            self.sio = socketio.AsyncServer(
                cors_allowed_origins='*' if settings.environment == "development" else settings.frontend_urls,
                async_mode='asgi'
            )
            self.setup_socketio()
        
        # Background tasks
        self.background_tasks = []
        
        logger.info(f"🚀 Phoenix v{self.version} initialized (sync)")

    async def metrics_middleware(self, request: Request, call_next):
        start_time = time.time()
        if metrics._initialized and metrics.api_requests:
            metrics.api_requests.labels(endpoint=request.url.path, method=request.method).inc()
        response = await call_next(request)
        if metrics._initialized and metrics.api_request_duration:
            duration = time.time() - start_time
            metrics.api_request_duration.labels(endpoint=request.url.path).observe(duration)
        return response

    def setup_routes(self):
        # ===== PUBLIC ENDPOINTS =====
        @self.app.get("/")
        async def root():
            return {
                "name": "Phoenix AI",
                "version": self.version,
                "status": "online",
                "standard": "Rezonic Agentic Standard v1.0",
                "docs": "/docs" if settings.environment == "development" else None
            }

        @self.app.get("/health")
        async def health():
            return await self.get_stats()

        @self.app.get("/metrics")
        async def metrics_endpoint():
            if HAS_PROMETHEUS:
                from prometheus_client import generate_latest
                from fastapi.responses import Response
                return Response(
                    content=generate_latest(),
                    media_type="text/plain"
                )
            return {"error": "Prometheus not enabled"}

        @self.app.get("/ollama/status")
        async def ollama_status():
            models = await self.ollama.get_models()
            stats = await self.ollama.get_stats()
            return {
                "connected": len(models) > 0,
                "models": models,
                "stats": stats
            }

        @self.app.get("/workers/list")
        async def workers_list(role: str = Depends(auth_manager.require_role("viewer"))):
            workers_info = {}
            for name, info in self.workers.items():
                workers_info[name] = {
                    "path": info.get("path", "unknown"),
                    "loaded": info.get("loaded_at", time.time()),
                    "module": info.get("module", "unknown"),
                    "metrics": {
                        "calls": 0,
                        "errors": 0,
                        "avg_duration": 0
                    }
                }
            return {
                "loaded": list(self.workers.keys()),
                "count": len(self.workers),
                "details": workers_info
            }

        @self.app.get("/workers/metrics")
        async def workers_metrics(role: str = Depends(auth_manager.require_role("admin"))):
            return await worker_cache.get_metrics()

        @self.app.post("/workers/reload/{worker_name}")
        async def workers_reload(worker_name: str, role: str = Depends(auth_manager.require_role("admin"))):
            success = await worker_cache.reload_worker(worker_name)
            return {"success": success, "worker": worker_name}

        @self.app.get("/events/stats")
        async def events_stats():
            return await event_bus.get_stats()

        @self.app.get("/events/recent")
        async def events_recent(limit: int = 100, event_type: Optional[str] = None):
            events = await event_bus.get_events_by_type(event_type, limit)
            return {"events": events, "count": len(events)}

        @self.app.get("/sce/status")
        async def sce_status():
            return {
                "version": SCEProtocol.VERSION,
                "blueprints": len(self.memory.memories),
                "drift_chain": self.drift_chain[-10:],
                "drift_chain_length": len(self.drift_chain)
            }

        @self.app.get("/memory/blueprints")
        async def memory_blueprints():
            return {
                "count": len(self.memory.memories),
                "blueprints": list(self.memory.blueprint_index.keys())[-50:]
            }

        @self.app.get("/memory/search")
        async def memory_search(query: str, limit: int = 10):
            return {"results": self.memory.search(query, limit)}

        @self.app.get("/memory/verify/{drift_lock}")
        async def memory_verify(drift_lock: str):
            return self.memory.verify(drift_lock)

        @self.app.get("/constitution/stats")
        async def constitution_stats():
            return self.constitution.get_stats()

        @self.app.post("/constitution/evaluate")
        async def constitution_evaluate(request: Request, role: str = Depends(auth_manager.require_role("viewer"))):
            data = await request.json()
            action = data.get('action', '')
            context = data.get('context', {})
            return self.constitution.evaluate(action, context)

        @self.app.get("/router/stats")
        async def router_stats():
            return self.router.get_stats()

        @self.app.post("/kernel/stream")
        async def kernel_stream(
            request: Request,
            background_tasks: BackgroundTasks,
            role: str = Depends(auth_manager.require_role("viewer"))
        ):
            try:
                data = await request.json()
            except:
                return JSONResponse({"error": "Invalid JSON"}, status_code=400)

            task = data.get("task", "").strip()
            if not task:
                return JSONResponse({"error": "No task provided"}, status_code=400)

            user_id = request.client.host if request.client else "unknown"
            background_tasks.add_task(self.track_user_interaction, user_id, task)

            async def generate():
                reflex_result = await self.reflex.execute(task, kernel=self)
                if reflex_result:
                    yield f"data: {json.dumps({'type': 'reflex', 'content': reflex_result['content'], 'command': reflex_result.get('command')})}\n"
                    return

                ruling = self.constitution.evaluate(task, {"role": role, "user": user_id})
                if not ruling.get("approved"):
                    yield f"data: {json.dumps({'type': 'error', 'content': ruling.get('reason', 'Blocked by constitution')})}\n"
                    return

                worker_name = self.router.route(task)
                yield f"data: {json.dumps({'type': 'thinking', 'worker': worker_name})}\n"

                worker_used = False
                if worker_name in self.workers:
                    try:
                        worker_class = self.workers[worker_name]["class"]
                        worker_config = self.workers[worker_name].get("config")
                        worker = await worker_cache.get_worker(worker_class, worker_config)
                        if await worker.validate(task):
                            start_time = time.time()
                            worker_result = await worker.execute(task)
                            duration = time.time() - start_time
                            self.router.report_success(worker_name, True)
                            yield f"data: {json.dumps({'type': 'worker_result', 'worker': worker_name, 'content': worker_result, 'duration': duration})}\n"
                            worker_used = True
                    except Exception as e:
                        logger.error(f"Worker {worker_name} failed: {e}")
                        self.router.report_success(worker_name, False)

                if not worker_used:
                    system_prompt = f"You are Phoenix AI v{self.version} (Rezonic Standard). Be concise and helpful."
                    full_response = ""
                    async for chunk in self.ollama.generate(task, system=system_prompt):
                        full_response += chunk
                        yield f"data: {json.dumps({'type': 'result', 'content': chunk})}\n"

                blueprint = SCEProtocol.create_blueprint(
                    {"task": task, "worker": worker_name, "user": user_id, "role": role},
                    {"narrative": ["Streaming complete"], "routing": worker_used, "timestamp": time.time()},
                    {"response_length": len(full_response) if not worker_used else 0,
                     "worker_used": worker_used,
                     "success": True},
                    self.drift_chain[-1] if self.drift_chain else None
                )
                lock = self.memory.store_blueprint(blueprint)
                self.drift_chain.append(lock)
                if metrics._initialized and metrics.drift_chain_length:
                    metrics.drift_chain_length.set(len(self.drift_chain))

                yield f"data: {json.dumps({'type': 'done', 'drift_lock': lock})}\n"

            return StreamingResponse(generate(), media_type="text/event-stream")

        @self.app.post("/feedback")
        async def user_feedback(request: Request, role: str = Depends(auth_manager.require_role("viewer"))):
            data = await request.json()
            drift_lock = data.get("drift_lock")
            rating = data.get("rating")
            comment = data.get("comment", "")
            await event_bus.publish(Event(
                type=EventType.USER_FEEDBACK,
                source="feedback_api",
                payload={
                    "drift_lock": drift_lock,
                    "rating": rating,
                    "comment": comment[:500]
                }
            ))
            return {"success": True, "message": "Feedback recorded"}

        @self.app.options("/{path:path}")
        async def options_handler(request: Request, path: str):
            origin = request.headers.get("origin", "*")
            return JSONResponse(
                content={},
                headers={
                    "Access-Control-Allow-Origin": origin,
                    "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS, PATCH",
                    "Access-Control-Allow-Headers": "Content-Type, Authorization, X-Hive-API-Key, X-Requested-With, Accept",
                    "Access-Control-Allow-Credentials": "true",
                    "Access-Control-Max-Age": "3600",
                    "Access-Control-Expose-Headers": "*",
                }
            )

    async def track_user_interaction(self, user_id: str, task: str):
        logger.info(f"User {user_id} interaction: {task[:50]}...")

    async def get_stats(self):
        gpu.update_stats()
        event_stats = await event_bus.get_stats()
        worker_metrics = await worker_cache.get_metrics()
        
        return {
            "status": "ONLINE",
            "version": self.version,
            "uptime": round(time.time() - self.start_time, 2),
            "workers": len(self.workers),
            "active_workers": worker_metrics.get('active_workers', 0),
            "memory_entries": len(self.memory.memories),
            "drift_chain": len(self.drift_chain),
            "events": event_stats.get('total_events', 0),
            "gpu": gpu.name if gpu.has_gpu else None,
            "gpu_temp": gpu.temp,
            "gpu_util": gpu.utilization,
            "consciousness": 5 + len(self.workers),
            "sce_enforcement": "FULL",
            "environment": settings.environment,
            "ollama_connected": len(await self.ollama.get_models()) > 0
        }

    def setup_socketio(self):
        if not self.sio:
            return
        @self.sio.event
        async def connect(sid, environ, auth):
            logger.info(f"🟢 Client: {sid}")
            if metrics._initialized and metrics.active_connections:
                metrics.active_connections.inc()
            await self.sio.emit('connection_verified', {'status': 'ok', 'version': self.version}, room=sid)
        @self.sio.event
        async def disconnect(sid):
            logger.info(f"🔴 Disconnected: {sid}")
            if metrics._initialized and metrics.active_connections:
                metrics.active_connections.dec()
        @self.sio.event
        async def message(sid, data):
            task = data.get('task', '')
            await self.sio.emit('thinking', {'worker': self.router.route(task)}, room=sid)
            async for chunk in self.ollama.generate(task):
                await self.sio.emit('chunk', {'content': chunk}, room=sid)
            await self.sio.emit('done', room=sid)

    async def _health_check(self):
        while True:
            try:
                if metrics._initialized and metrics.drift_chain_length:
                    metrics.drift_chain_length.set(len(self.drift_chain))
                    models = await self.ollama.get_models()
                    if not models:
                        logger.warning("Ollama not responding")
                await asyncio.sleep(30)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Health check error: {e}")
                await asyncio.sleep(60)

    async def startup(self):
        metrics.initialize()
        await gpu.start_background_updates()
        await event_bus.initialize()
        await self.memory.start_background_updates()
        await self.ollama.initialize()
        
        for worker_name in self.workers.keys():
            await event_bus.publish(Event(
                type=EventType.WORKER_LOADED,
                source="worker_loader",
                payload={"worker": worker_name}
            ))
        
        self.background_tasks.append(asyncio.create_task(self._health_check()))
        
        if HAS_PROMETHEUS:
            try:
                start_http_server(settings.metrics_port)
                logger.info(f"📊 Metrics server started on port {settings.metrics_port}")
            except Exception as e:
                logger.error(f"Failed to start metrics server: {e}")
        
        print("\n" + "="*60)
        print(f"🔥 PHOENIX v{self.version} - ENHANCED SCE PROTOCOL")
        print("="*60)
        print(f"Workers: {len(self.workers)}")
        print(f"GPU: {gpu.name if gpu.has_gpu else 'None'}")
        print(f"Memory: {len(self.memory.memories)} entries")
        print(f"SCE: ✅ FULL ENFORCEMENT")
        print(f"Prometheus: ✅ on :{settings.metrics_port}" if HAS_PROMETHEUS else "Prometheus: ⚠️ Disabled")
        
        try:
            models = await self.ollama.get_models()
            print(f"Ollama: ✅ {len(models)} models")
        except:
            print("Ollama: ⚠️ Offline")
        
        print("="*60 + "\n")

    async def shutdown(self):
        logger.info("Shutting down Phoenix...")
        for task in self.background_tasks:
            task.cancel()
        if self.background_tasks:
            await asyncio.gather(*self.background_tasks, return_exceptions=True)
        await gpu.shutdown()
        await self.memory.shutdown()
        await self.ollama.close()
        await event_bus.shutdown()
        logger.info("Shutdown complete")

    async def run(self):
        await self.startup()
        if self.sio:
            app = socketio.ASGIApp(self.sio, self.app)
        else:
            app = self.app
        config = uvicorn.Config(
            app, 
            host=settings.host, 
            port=settings.port, 
            log_level="info",
            loop="asyncio"
        )
        server = uvicorn.Server(config)
        try:
            await server.serve()
        finally:
            await self.shutdown()

if __name__ == "__main__":
    # Kill any existing process on port 8002 before starting
    import subprocess
    import platform
    
    if platform.system() == "Windows":
        try:
            result = subprocess.run('netstat -ano | findstr :8002', shell=True, capture_output=True, text=True)
            for line in result.stdout.split('\n'):
                if 'LISTENING' in line:
                    pid = line.strip().split()[-1]
                    subprocess.run(f'taskkill /F /PID {pid}', shell=True)
                    logger.info(f"Killed process {pid} using port 8002")
        except:
            pass
    
    kernel = PhoenixKernel()
    asyncio.run(kernel.run())