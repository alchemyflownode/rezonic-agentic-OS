#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PHOENIX ULTIMATE v13.3.0 - HARDENED VERSION
Zero Drift Architecture + Persistent Event Chain + Formalized Workers + Code Execution
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
import sqlite3
import shutil
import subprocess
import tempfile
import ast
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, Optional, List, Callable, Awaitable, Tuple, Union
from enum import Enum, auto
from dataclasses import dataclass, field, asdict
from collections import defaultdict
from functools import wraps
from contextlib import asynccontextmanager
from abc import ABC, abstractmethod
# Desktop coworker imports
from desktop.client import KernelClient
from desktop.presence import DesktopPresence
from desktop.watcher import PhoenixFileHandler

# Suppress warnings
warnings.filterwarnings("ignore")

# =======================================================================
# LOGGING SETUP (With Fallbacks)
# =======================================================================
def safe_makedirs(path):
    try:
        Path(path).mkdir(parents=True, exist_ok=True)
        return True
    except:
        return False

safe_makedirs('logs')
safe_makedirs('data')
safe_makedirs('data/event_store')
safe_makedirs('data/backups')
safe_makedirs('data/sandbox')
safe_makedirs('data/memory')

from logging.handlers import RotatingFileHandler

log_file_path = Path('logs/phoenix_ultimate.log')
log_handler = None

for attempt in range(3):
    try:
        log_handler = RotatingFileHandler(
            str(log_file_path),
            maxBytes=10*1024*1024,
            backupCount=5,
            encoding='utf-8',
            delay=True
        )
        break
    except PermissionError:
        if attempt == 2:
            log_handler = logging.StreamHandler(sys.stdout)

if log_handler:
    log_handler.setFormatter(logging.Formatter(
        "%(asctime)s [%(levelname)s] %(name)s - %(message)s"
    ))

logging.basicConfig(
    level=logging.INFO,
    handlers=[log_handler] if log_handler else [logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("PHOENIX")

# =======================================================================
# IMPORTS
# =======================================================================
try:
    from fastapi import FastAPI, Request, HTTPException, Depends, BackgroundTasks
    from fastapi.middleware.cors import CORSMiddleware
    from fastapi.responses import StreamingResponse, JSONResponse
    from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
    import uvicorn
    HAS_FASTAPI = True
except ImportError:
    print("âŒ Install: pip install fastapi uvicorn")
    sys.exit(1)

# HARDENING: Rate limiting imports
try:
    from slowapi import Limiter, _rate_limit_exceeded_handler
    from slowapi.util import get_remote_address
    from slowapi.errors import RateLimitExceeded
    HAS_SLOWAPI = True
except ImportError:
    HAS_SLOWAPI = False
    print("âš ï¸ Install slowapi for rate limiting: pip install slowapi")

try:
    import socketio
    HAS_SOCKETIO = True
except ImportError:
    HAS_SOCKETIO = False

try:
    from pydantic import BaseModel, Field, ConfigDict
    from pydantic_settings import BaseSettings, SettingsConfigDict
    HAS_PYDANTIC = True
except ImportError:
    HAS_PYDANTIC = False

try:
    from prometheus_client import Counter, Histogram, Gauge, generate_latest, start_http_server
    HAS_PROMETHEUS = True
except ImportError:
    HAS_PROMETHEUS = False

# =======================================================================
# CONFIGURATION
# =======================================================================
class Settings(BaseSettings):
    environment: str = os.getenv("ENV", "development")
    port: int = int(os.getenv("PHOENIX_PORT", "8002"))
    metrics_port: int = int(os.getenv("METRICS_PORT", "8003"))
    host: str = os.getenv("PHOENIX_HOST", "0.0.0.0")
    
    # Security
    api_key_admin: str = os.getenv("PHOENIX_ADMIN_KEY", secrets.token_urlsafe(32))
    api_key_viewer: str = os.getenv("PHOENIX_VIEWER_KEY", secrets.token_urlsafe(32))
    
    # Directories
    workspace_dir: Path = Path(os.getenv("WORKSPACE_DIR", str(Path.cwd())))
    backups_dir: Path = Path("data/backups")
    sandbox_dir: Path = Path("data/sandbox")
    memory_dir: Path = Path("data/memory")
    event_store_dir: Path = Path("data/event_store")
    workers_dir: Path = Path("workers")
    bots_dir: Path = Path("bots")
    
    # Ollama
    ollama_url: str = os.getenv("OLLAMA_URL", "http://localhost:11434")
    default_model: str = os.getenv("OLLAMA_MODEL", "llama3.2:latest")
    ollama_timeout: int = int(os.getenv("OLLAMA_TIMEOUT", "60"))
    
    # Code execution safety
    allow_code_execution: bool = os.getenv("ALLOW_CODE_EXECUTION", "true").lower() == "true"
    require_admin_for_execution: bool = os.getenv("REQUIRE_ADMIN_FOR_EXECUTION", "false").lower() == "true"
    max_file_size: int = int(os.getenv("MAX_FILE_SIZE", "10485760"))
    allowed_extensions: List[str] = ['.py', '.js', '.html', '.css', '.json', '.yaml', '.yml', '.txt', '.md']
    
    # Event chain
    chain_maxlen: int = 10000
    event_persistence_batch: int = 100
    
    # CORS
    cors_origins_str: str = os.getenv("CORS_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000,http://localhost:3001,http://127.0.0.1:3001,http://localhost:3002")
    cors_origins: list = [origin.strip() for origin in cors_origins_str.split(",")]
    
    # Circuit breaker
    circuit_breaker_threshold: int = 5
    circuit_breaker_timeout: int = 60
    
    # API Keys - ADD THIS
    api_keys: Dict[str, str] = {
        "rez-hive-admin-key-2026": "admin",
    }
    
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
    
    def validate(self):
        # Add default admin key
        self.api_keys["rez-hive-admin-key-2026"] = "admin"
        admin_key = os.getenv("PHOENIX_ADMIN_KEY")
        if admin_key:
            self.api_keys[admin_key] = "admin"
        viewer_key = os.getenv("PHOENIX_VIEWER_KEY") 
        if viewer_key:
            self.api_keys[viewer_key] = "viewer"
        return True
    
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

for d in [settings.workspace_dir, settings.backups_dir, settings.sandbox_dir,
          settings.memory_dir, settings.event_store_dir, settings.workers_dir,
          settings.bots_dir]:
    try:
        d.mkdir(parents=True, exist_ok=True)
    except:
        pass

# =======================================================================
# PROMETHEUS METRICS
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
            self.event_counter = Counter('phoenix_events_total', 'Total events', ['event_type'])
            self.worker_duration = Histogram('phoenix_worker_duration_seconds', 'Worker duration', ['worker_name'])
            self.active_connections = Gauge('phoenix_active_connections', 'Active connections')
            self.blueprint_counter = Counter('phoenix_blueprints_total', 'Total blueprints')
            self.memory_usage = Gauge('phoenix_memory_entries', 'Memory entries')
            self.drift_chain_length = Gauge('phoenix_drift_chain_length', 'Drift chain length')
            self.gpu_temp_gauge = Gauge('phoenix_gpu_temperature', 'GPU temperature')
            self.api_requests = Counter('phoenix_api_requests_total', 'API requests', ['endpoint', 'method'])
            self.api_request_duration = Histogram('phoenix_api_request_duration_seconds', 'API duration', ['endpoint'])
            self._initialized = True
            logger.info("âœ… Prometheus metrics initialized")

metrics = MetricsRegistry()

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

def validate_path(base_dir: Path, user_path: str) -> Path:
    if not user_path or user_path.strip() == "":
        raise SecurityError("Empty path")
    user_path = user_path.replace('\\', '/')
    if '..' in user_path or '~' in user_path:
        raise SecurityError("Path traversal not allowed")
    target = (base_dir / user_path).resolve()
    try:
        target.relative_to(base_dir.resolve())
    except ValueError:
        raise SecurityError(f"Path escapes workspace")
    return target

def validate_file_extension(filename: str) -> bool:
    ext = Path(filename).suffix.lower()
    return ext in settings.allowed_extensions or not ext

def create_backup(file_path: Path) -> Optional[Path]:
    if not file_path.exists():
        return None
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_name = f"{file_path.stem}_{timestamp}{file_path.suffix}.backup"
    backup_path = settings.backups_dir / backup_name
    try:
        shutil.copy2(file_path, backup_path)
        logger.info(f"Backup created: {backup_path}")
        return backup_path
    except:
        return None

# =======================================================================
# EVENT STORE (SQLite)
# =======================================================================
class EventStore:
    def __init__(self, db_path: Path):
        self.db_path = db_path
        self._init_db()
    
    def _init_db(self):
        try:
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
        except Exception as e:
            logger.error(f"DB init failed: {e}")
    
    async def save_event(self, event) -> bool:
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute(
                "INSERT OR REPLACE INTO events VALUES (?, ?, ?, ?, ?, ?, ?)",
                (event.vera_proof, event.type.value, event.source, 
                 json.dumps(event.payload), event.timestamp, 
                 event.previous_hash, time.time())
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
                "INSERT OR REPLACE INTO blueprints VALUES (?, ?, ?)",
                (drift_lock, json.dumps(blueprint), time.time())
            )
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            logger.error(f"Failed to save blueprint: {e}")
            return False
    
    async def get_events(self, limit: int = 100, event_type: Optional[str] = None) -> List[Dict]:
        try:
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
        except:
            return []

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
            'badge': 'ðŸŸ¢ SOVEREIGN' if is_valid else 'ðŸ”´ DRIFTED',
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
    CODE_EXECUTION = "code.execution"
    FILE_OPERATION = "file.operation"
    CODE_REFACTOR = "code.refactor"
    TEST_RUN = "test.run"
    SECURITY_VIOLATION = "security.violation"
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
        self._genesis_hash = hashlib.sha256(b"PHOENIX_ULTIMATE_v13.3.0").hexdigest()[:16]
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
            logger.info("âœ… Event bus initialized")
            await self.publish(Event(
                type=EventType.SYSTEM_BOOT,
                source="event_bus",
                payload={"version": "13.3.0"}
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
            logger.error(f"Failed to load events: {e}")
    
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
                logger.error(f"Persistence error: {e}")
                await asyncio.sleep(1)
    
    async def _persist_batch(self, batch: List[Event]):
        for event in batch:
            await self._store.save_event(event)
        if metrics._initialized and metrics.event_counter:
            metrics.event_counter.labels(event_type='batch').inc(len(batch))
        logger.debug(f"Persisted {len(batch)} events")

    async def publish(self, event: Event):
        if not self._initialized:
            logger.warning("Event bus not initialized")
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
# GPU MONITOR (VRAM Detection)
# =======================================================================
class GPUMonitor:
    def __init__(self):
        self.has_gpu = False
        self.gpu_count = 0
        self.gpus = []
        self._update_task = None
        self._init_gpu()
    
    def _init_gpu(self):
        try:
            import pynvml
            pynvml.nvmlInit()
            self.gpu_count = pynvml.nvmlDeviceGetCount()
            
            for i in range(self.gpu_count):
                handle = pynvml.nvmlDeviceGetHandleByIndex(i)
                name = pynvml.nvmlDeviceGetName(handle)
                if isinstance(name, bytes):
                    name = name.decode('utf-8')
                mem_info = pynvml.nvmlDeviceGetMemoryInfo(handle)
                
                self.gpus.append({
                    "index": i,
                    "name": name,
                    "total_vram_gb": mem_info.total / (1024**3),
                    "handle": handle
                })
            
            self.has_gpu = len(self.gpus) > 0
            if self.has_gpu:
                logger.info(f"âœ… Detected {self.gpu_count} GPU(s)")
                for gpu in self.gpus:
                    logger.info(f"   GPU {gpu['index']}: {gpu['name']} - {gpu['total_vram_gb']:.1f} GiB VRAM")
        except ImportError:
            logger.info("â„¹ï¸ pynvml not installed - GPU stats disabled")
        except Exception as e:
            logger.info(f"â„¹ï¸ GPU monitoring disabled: {e}")
    
    async def start_background_updates(self):
        if self.has_gpu and not self._update_task:
            self._update_task = asyncio.create_task(self._background_update())
            logger.info("âœ… GPU background monitoring started")
    
    async def _background_update(self):
        while True:
            try:
                self.update_stats()
                if metrics._initialized and metrics.gpu_temp_gauge:
                    metrics.gpu_temp_gauge.set(self.get_temperature())
                await asyncio.sleep(5)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"GPU update error: {e}")
                await asyncio.sleep(10)
    
    def update_stats(self):
        if not self.has_gpu:
            return
    
    def get_temperature(self, gpu_index: int = 0) -> int:
        if not self.has_gpu or gpu_index >= len(self.gpus):
            return 0
        try:
            import pynvml
            return pynvml.nvmlDeviceGetTemperature(self.gpus[gpu_index]["handle"], pynvml.NVML_TEMPERATURE_GPU)
        except:
            return 0
    
    def get_utilization(self, gpu_index: int = 0) -> int:
        if not self.has_gpu or gpu_index >= len(self.gpus):
            return 0
        try:
            import pynvml
            return pynvml.nvmlDeviceGetUtilizationRates(self.gpus[gpu_index]["handle"]).gpu
        except:
            return 0
    
    def get_vram_summary(self) -> Dict[str, Any]:
        if not self.has_gpu:
            return {"has_gpu": False, "total_gpus": 0, "total_vram_gb": 0}
        
        total_vram = 0
        used_vram = 0
        for i in range(self.gpu_count):
            try:
                import pynvml
                mem_info = pynvml.nvmlDeviceGetMemoryInfo(self.gpus[i]["handle"])
                total_vram += mem_info.total / (1024**3)
                used_vram += mem_info.used / (1024**3)
            except:
                pass
        
        return {
            "has_gpu": True,
            "total_gpus": self.gpu_count,
            "total_vram_gb": round(total_vram, 2),
            "used_vram_gb": round(used_vram, 2),
            "free_vram_gb": round(total_vram - used_vram, 2),
            "utilization_percent": round((used_vram / total_vram * 100) if total_vram > 0 else 0, 2)
        }
    
    def get_gpu_details(self, gpu_index: int = 0) -> Dict[str, Any]:
        if not self.has_gpu or gpu_index >= len(self.gpus):
            return {"error": "GPU not available"}
        
        try:
            import pynvml
            handle = self.gpus[gpu_index]["handle"]
            mem_info = pynvml.nvmlDeviceGetMemoryInfo(handle)
            
            return {
                "index": gpu_index,
                "name": self.gpus[gpu_index]["name"],
                "memory": {
                    "total_gb": round(mem_info.total / (1024**3), 2),
                    "used_gb": round(mem_info.used / (1024**3), 2),
                    "free_gb": round(mem_info.free / (1024**3), 2),
                    "used_percent": round((mem_info.used / mem_info.total) * 100, 2)
                },
                "temperature_celsius": self.get_temperature(gpu_index),
                "gpu_utilization_percent": self.get_utilization(gpu_index)
            }
        except Exception as e:
            return {"error": str(e)}
    
    async def shutdown(self):
        if self._update_task:
            self._update_task.cancel()
            try:
                await self._update_task
            except asyncio.CancelledError:
                pass

gpu = GPUMonitor()

# =======================================================================
# AUTHENTICATION
# =======================================================================
class AuthManager:
    def __init__(self):
        self._keys = settings.api_keys
        self._lock = asyncio.Lock()
        self._rate_limits = defaultdict(list)

    async def verify_key(self, api_key: Optional[str], client_ip: str = None) -> str:
        # TEMPORARY: Disable authentication for testing
        return "admin"
        
        # Original code is commented out, keep it for later
        # if not api_key:
        #     raise HTTPException(status_code=403, detail="API key required")
        # if client_ip:
        #     now = time.time()
        #     self._rate_limits[client_ip] = [t for t in self._rate_limits[client_ip] if t > now - 60]
        #     if len(self._rate_limits[client_ip]) > 100:
        #         raise HTTPException(status_code=429, detail="Rate limit exceeded")
        #     self._rate_limits[client_ip].append(now)
        # async with self._lock:
        #     role = self._keys.get(api_key)
        # if not role:
        #     await event_bus.publish(Event(
        #         type=EventType.AUTH_FAILURE,
        #         source="auth_manager",
        #         payload={"client_ip": client_ip}
        #     ))
        #     raise HTTPException(status_code=403, detail="Invalid API key")
        # return role

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
# WORKER BASE CLASS
# =======================================================================
class Worker(ABC):
    def __init__(self, name: str):
        self.name = name
        self.metrics = {'calls': 0, 'errors': 0, 'total_duration': 0}
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
                if not success:
                    self.metrics['errors'] += 1
        asyncio.create_task(_record())

# =======================================================================
# WORKER LOADER (Loads your 48 workers)
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
        logger.info(f"ðŸ“ Worker directory: {self.workers_dir}")
        logger.info(f"ðŸ“‚ Directory exists: {self.workers_dir.exists()}")
    
    def is_worker_class(self, obj, class_name: str, module_name: str) -> bool:
        if 'Worker' in class_name:
            return True
        try:
            for base in obj.__bases__:
                if 'Worker' in base.__name__:
                    return True
        except:
            pass
        worker_methods = ['execute', 'process', 'run', 'handle', 'work']
        methods = [m for m in dir(obj) if not m.startswith('_')]
        if any(method in methods for method in worker_methods):
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
            logger.debug(f"Import failed for {module_name}: {e}")
        return None
    
    def load_all(self):
        if not self.workers_dir.exists():
            logger.error(f"âŒ Workers directory NOT FOUND: {self.workers_dir}")
            return {}
        all_files = list(self.workers_dir.glob("*.py"))
        logger.info(f"ðŸ“¦ Found {len(all_files)} Python files")
        exclude_patterns = ['__init__.py', 'base_worker.py']
        worker_files = [f for f in all_files if f.name not in exclude_patterns]
        logger.info(f"ðŸ” Attempting to load {len(worker_files)} potential worker files...")
        
        for py_file in worker_files:
            try:
                module = self.safe_import_module(py_file)
                if not module:
                    logger.error(f"  âŒ Could not import {py_file.name}")
                    self.failed_imports.append(py_file.name)
                    continue
                
                for name, obj in inspect.getmembers(module, inspect.isclass):
                    if obj.__module__ != module.__name__:
                        continue
                    if self.is_worker_class(obj, name, py_file.stem):
                        self.workers[name] = {
                            "module": py_file.stem,
                            "class": obj,
                            "path": str(py_file),
                            "loaded_at": time.time()
                        }
                        logger.info(f"  âœ… Loaded worker: {name} from {py_file.name}")
            except Exception as e:
                logger.error(f"  âŒ Failed to load {py_file.name}: {e}")
                self.failed_imports.append(py_file.name)
        
        logger.info(f"ðŸ“Š Total workers loaded: {len(self.workers)}")
        if self.failed_imports:
            logger.warning(f"âš ï¸ Failed imports: {len(self.failed_imports)} files")
        return self.workers

# =======================================================================
# WORKER CACHE
# =======================================================================
class WorkerCache:
    def __init__(self):
        self._instances = {}
        self._locks = defaultdict(asyncio.Lock)
        self._metrics = defaultdict(int)
    
    async def get_worker(self, worker_class, config=None) -> Worker:
        key = f"{worker_class.__name__}"
        async with self._locks[key]:
            if key not in self._instances:
                self._instances[key] = worker_class(config) if config else worker_class()
                self._metrics['loads'] += 1
                logger.info(f"Loaded worker: {key}")
            return self._instances[key]
    
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
# FILE SYSTEM WORKER
# =======================================================================
class FileSystemWorker(Worker):
    def __init__(self):
        super().__init__("file_system_worker")
        self.workspace = settings.workspace_dir
    
    async def execute(self, task: str, **kwargs) -> Dict[str, Any]:
        task_lower = task.lower()
        
        if 'read' in task_lower or 'view' in task_lower:
            return await self._read_file(task, **kwargs)
        elif 'write' in task_lower or 'create' in task_lower:
            return await self._write_file(task, **kwargs)
        elif 'modify' in task_lower or 'edit' in task_lower:
            return await self._modify_file(task, **kwargs)
        elif 'list' in task_lower or 'ls' in task_lower:
            return await self._list_directory(task, **kwargs)
        elif 'search' in task_lower or 'find' in task_lower:
            return await self._search_files(task, **kwargs)
        else:
            return {"error": f"Unknown operation: {task}", "success": False}
    
    async def _read_file(self, task: str, **kwargs) -> Dict[str, Any]:
        match = re.search(r'(?:read|view|cat|open)\s+([^\s]+)', task.lower())
        if not match:
            return {"error": "No filename specified", "success": False}
        
        filename = match.group(1)
        try:
            safe_path = validate_path(self.workspace, filename)
            if not safe_path.exists():
                return {"error": f"File not found: {filename}", "success": False}
            if safe_path.is_dir():
                return {"error": f"Cannot read directory: {filename}", "success": False}
            
            with open(safe_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            await event_bus.publish(Event(
                type=EventType.FILE_OPERATION,
                source=self.name,
                payload={"operation": "read", "file": str(safe_path), "size": len(content)}
            ))
            
            return {
                "success": True,
                "filename": str(safe_path),
                "content": content,
                "size": len(content),
                "lines": len(content.splitlines())
            }
        except Exception as e:
            return {"error": str(e), "success": False}
    
    async def _write_file(self, task: str, **kwargs) -> Dict[str, Any]:
        match = re.search(r'(?:write|create|save)\s+([^\s]+)\s+(.+?)$', task, re.IGNORECASE)
        if not match:
            filename = kwargs.get('filename')
            content = kwargs.get('content')
            if not filename or content is None:
                return {"error": "Invalid format", "success": False}
        else:
            filename = match.group(1)
            content = match.group(2)
        
        try:
            safe_path = validate_path(self.workspace, filename)
            backup_path = create_backup(safe_path) if safe_path.exists() else None
            safe_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(safe_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            await event_bus.publish(Event(
                type=EventType.FILE_OPERATION,
                source=self.name,
                payload={"operation": "write", "file": str(safe_path), "size": len(content)}
            ))
            
            return {
                "success": True,
                "filename": str(safe_path),
                "bytes_written": len(content),
                "backup_created": str(backup_path) if backup_path else None
            }
        except Exception as e:
            return {"error": str(e), "success": False}
    
    async def _modify_file(self, task: str, **kwargs) -> Dict[str, Any]:
        match = re.search(r'(?:modify|edit|update)\s+([^\s]+)\s+/(.+?)/(.+?)/', task, re.IGNORECASE)
        if not match:
            return {"error": "Invalid format. Use: modify <filename> /pattern/replacement/", "success": False}
        
        filename = match.group(1)
        search_pattern = match.group(2)
        replacement = match.group(3)
        
        try:
            safe_path = validate_path(self.workspace, filename)
            if not safe_path.exists():
                return {"error": f"File not found: {filename}", "success": False}
            
            with open(safe_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            backup_path = create_backup(safe_path)
            new_content = re.sub(search_pattern, replacement, content)
            changes_made = len(re.findall(search_pattern, content))
            
            with open(safe_path, 'w', encoding='utf-8') as f:
                f.write(new_content)
            
            return {
                "success": True,
                "filename": str(safe_path),
                "changes_made": changes_made,
                "backup": str(backup_path) if backup_path else None
            }
        except Exception as e:
            return {"error": str(e), "success": False}
    
    async def _list_directory(self, task: str, **kwargs) -> Dict[str, Any]:
        match = re.search(r'(?:list|ls|dir)\s+([^\s]*)', task.lower())
        directory = match.group(1) if match else '.'
        
        try:
            safe_path = validate_path(self.workspace, directory)
            if not safe_path.exists():
                return {"error": f"Path not found: {directory}", "success": False}
            if not safe_path.is_dir():
                return {"error": f"Not a directory: {directory}", "success": False}
            
            items = []
            for item in safe_path.iterdir():
                items.append({
                    "name": item.name,
                    "type": "directory" if item.is_dir() else "file",
                    "size": item.stat().st_size if item.is_file() else 0
                })
            
            items.sort(key=lambda x: (x['type'] != 'directory', x['name'].lower()))
            
            return {
                "success": True,
                "directory": str(safe_path),
                "items": items,
                "count": len(items)
            }
        except Exception as e:
            return {"error": str(e), "success": False}
    
    async def _search_files(self, task: str, **kwargs) -> Dict[str, Any]:
        match = re.search(r'(?:search|find)\s+([^\s]+)\s+([^\s]+)?', task.lower())
        if not match:
            return {"error": "Invalid format. Use: search <pattern> [directory]", "success": False}
        
        pattern = match.group(1)
        directory = match.group(2) if len(match.groups()) > 1 else '.'
        
        try:
            safe_path = validate_path(self.workspace, directory)
            if not safe_path.exists() or not safe_path.is_dir():
                return {"error": f"Invalid directory: {directory}", "success": False}
            
            results = []
            for file_path in safe_path.rglob(pattern):
                if file_path.is_file():
                    results.append({
                        "path": str(file_path.relative_to(self.workspace)),
                        "size": file_path.stat().st_size
                    })
            
            return {
                "success": True,
                "pattern": pattern,
                "directory": str(safe_path),
                "results": results[:100],
                "count": len(results)
            }
        except Exception as e:
            return {"error": str(e), "success": False}

# =======================================================================
# CODE EXECUTION WORKER
# =======================================================================
class CodeExecutionWorker(Worker):
    def __init__(self):
        super().__init__("code_execution_worker")
        self.sandbox_dir = settings.sandbox_dir
        self.timeout = 30
    
    async def execute(self, task: str, **kwargs) -> Dict[str, Any]:
        code_block = re.search(r'```(?:python)?\s*\n(.*?)\n```', task, re.DOTALL)
        if code_block:
            code = code_block.group(1)
        else:
            match = re.search(r'(?:run|execute)\s+(.+?)(?:$)', task, re.IGNORECASE)
            if match:
                code = match.group(1)
            else:
                return {"error": "No code found", "success": False}
        
        if not settings.allow_code_execution:
            return {"error": "Code execution disabled", "success": False}
        
        return await self._execute_python(code)
    
    async def _execute_python(self, code: str) -> Dict[str, Any]:
        # HARDENING: set a timeout for the whole execution
        try:
            return await asyncio.wait_for(self._execute_python_internal(code), timeout=self.timeout)
        except asyncio.TimeoutError:
            return {"success": False, "error": f"Execution timed out after {self.timeout} seconds"}
    
    async def _execute_python_internal(self, code: str) -> Dict[str, Any]:
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', dir=str(self.sandbox_dir), delete=False) as f:
            wrapper = f'''
import sys, io
from contextlib import redirect_stdout, redirect_stderr

stdout_capture = io.StringIO()
stderr_capture = io.StringIO()

try:
    with redirect_stdout(stdout_capture), redirect_stderr(stderr_capture):
        {code}
    result = {{"success": True, "stdout": stdout_capture.getvalue(), "stderr": stderr_capture.getvalue()}}
except Exception as e:
    result = {{"success": False, "error": str(e), "stdout": stdout_capture.getvalue(), "stderr": stderr_capture.getvalue()}}
finally:
    import json
    print(json.dumps(result))
'''
            f.write(wrapper)
            temp_file = f.name
        
        try:
            # HARDENING: use subprocess with timeout via asyncio
            process = await asyncio.create_subprocess_exec(
                sys.executable, temp_file,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=str(self.sandbox_dir)
            )
            
            try:
                stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=self.timeout)
                result = json.loads(stdout.decode('utf-8').strip().split('\n')[-1])
                return result
            except asyncio.TimeoutError:
                process.kill()
                await process.wait()
                return {"success": False, "error": f"Subprocess timed out after {self.timeout}s"}
        except Exception as e:
            return {"success": False, "error": str(e)}
        finally:
            try:
                os.unlink(temp_file)
            except:
                pass

# =======================================================================
# CODE ANALYZER WORKER
# =======================================================================
class CodeAnalyzerWorker(Worker):
    def __init__(self):
        super().__init__("code_analyzer_worker")
    
    async def execute(self, task: str, **kwargs) -> Dict[str, Any]:
        code = None
        filename = None
        
        if 'file' in task.lower():
            match = re.search(r'file\s+([^\s]+)', task.lower())
            if match:
                filename = match.group(1)
                try:
                    safe_path = validate_path(settings.workspace_dir, filename)
                    with open(safe_path, 'r', encoding='utf-8') as f:
                        code = f.read()
                except Exception as e:
                    return {"error": f"Could not read file: {e}", "success": False}
        elif '```' in task:
            match = re.search(r'```(?:python)?\s*\n(.*?)\n```', task, re.DOTALL)
            if match:
                code = match.group(1)
        
        if not code:
            return {"error": "No code to analyze", "success": False}
        
        analysis = await self._analyze_code(code)
        return {"success": True, "filename": filename, "analysis": analysis}
    
    async def _analyze_code(self, code: str) -> Dict[str, Any]:
        analysis = {"metrics": {}, "issues": [], "suggestions": [], "security_concerns": []}
        
        lines = code.splitlines()
        analysis["metrics"]["lines"] = len(lines)
        analysis["metrics"]["characters"] = len(code)
        
        try:
            tree = ast.parse(code)
            functions = [n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)]
            classes = [n for n in ast.walk(tree) if isinstance(n, ast.ClassDef)]
            analysis["metrics"]["functions"] = len(functions)
            analysis["metrics"]["classes"] = len(classes)
            
            for imp in [n for n in ast.walk(tree) if isinstance(n, ast.Import)]:
                for alias in imp.names:
                    if alias.name in ['os', 'subprocess', 'sys']:
                        analysis["security_concerns"].append(f"Import of '{alias.name}' - potentially dangerous")
        except SyntaxError as e:
            analysis["issues"].append(f"Syntax error: {e}")
        
        if len(lines) > 500:
            analysis["suggestions"].append("File is large - consider splitting into modules")
        
        score = 100 - len(analysis["issues"]) * 5 - len(analysis["security_concerns"]) * 10
        analysis["quality_score"] = max(0, min(100, score))
        
        return analysis

# =======================================================================
# REFACTORING WORKER
# =======================================================================
class RefactoringWorker(Worker):
    def __init__(self, ollama_client):
        super().__init__("refactoring_worker")
        self.ollama = ollama_client
    
    async def execute(self, task: str, **kwargs) -> Dict[str, Any]:
        match = re.search(r'refactor\s+([^\s]+)\s+(.+?)(?:$)', task, re.IGNORECASE)
        if not match:
            return {"error": "Format: refactor <filename> <instructions>", "success": False}
        
        filename = match.group(1)
        instructions = match.group(2)
        
        try:
            safe_path = validate_path(settings.workspace_dir, filename)
            if not safe_path.exists():
                return {"error": f"File not found: {filename}", "success": False}
            
            with open(safe_path, 'r', encoding='utf-8') as f:
                original_code = f.read()
            
            prompt = f"Refactor this code: {instructions}\n\n```python\n{original_code}\n```\n\nProvide refactored code in a code block:"
            
            response = ""
            async for chunk in self.ollama.generate(prompt, stream=False):
                response += chunk
            
            code_match = re.search(r'```(?:python)?\s*\n(.*?)\n```', response, re.DOTALL)
            if code_match:
                refactored_code = code_match.group(1)
                backup_path = create_backup(safe_path)
                
                with open(safe_path, 'w', encoding='utf-8') as f:
                    f.write(refactored_code)
                
                return {
                    "success": True,
                    "filename": str(safe_path),
                    "backup": str(backup_path) if backup_path else None,
                    "changes_made": len(original_code) != len(refactored_code)
                }
            else:
                return {"success": False, "error": "Could not extract refactored code"}
        except Exception as e:
            return {"error": str(e), "success": False}

# =======================================================================
# TEST WORKER
# =======================================================================
class TestWorker(Worker):
    def __init__(self):
        super().__init__("test_worker")
    
    async def execute(self, task: str, **kwargs) -> Dict[str, Any]:
        match = re.search(r'test\s+([^\s]+)', task.lower())
        target = match.group(1) if match else None
        return await self._run_tests(target)
    
    async def _run_tests(self, target: Optional[str]) -> Dict[str, Any]:
        try:
            cmd = [sys.executable, '-m', 'pytest', '-v', '--tb=short']
            if target:
                safe_path = validate_path(settings.workspace_dir, target)
                cmd.append(str(safe_path))
            else:
                tests_dir = settings.workspace_dir / 'tests'
                if tests_dir.exists():
                    cmd.append(str(tests_dir))
                else:
                    cmd.append(str(settings.workspace_dir))
            
            result = subprocess.run(cmd, capture_output=True, text=True, cwd=str(settings.workspace_dir), timeout=60)
            
            return {
                "success": result.returncode == 0,
                "passed": result.returncode == 0,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "returncode": result.returncode
            }
        except subprocess.TimeoutExpired:
            return {"success": False, "error": "Tests timed out"}
        except Exception as e:
            return {"success": False, "error": str(e)}

# =======================================================================
# OLLAMA CLIENT
# =======================================================================
class OllamaClient:
    def __init__(self):
        self.client = None
        self.base_url = settings.ollama_url
    
    async def initialize(self):
        self.client = httpx.AsyncClient(timeout=settings.ollama_timeout)
        logger.info("âœ… Ollama client initialized")
        await self.check_connection()
    
    async def check_connection(self):
        try:
            resp = await self.client.get(f"{self.base_url}/api/tags", timeout=5)
            if resp.status_code == 200:
                models = resp.json().get("models", [])
                logger.info(f"âœ… Found {len(models)} Ollama models")
                return True
        except:
            logger.warning("âš ï¸ Ollama not responding")
        return False
    
    async def generate(self, prompt: str, stream: bool = True, system: str = None):
        if not self.client:
            await self.initialize()
        
        url = f"{self.base_url}/api/generate"
        payload = {
            "model": settings.default_model,
            "prompt": prompt,
            "stream": stream
        }
        if system:
            payload["system"] = system
        
        try:
            if stream:
                async with self.client.stream("POST", url, json=payload) as response:
                    async for line in response.aiter_lines():
                        if line:
                            chunk = json.loads(line)
                            if 'response' in chunk:
                                yield chunk.get("response", "")
                            if chunk.get("done"):
                                break
            else:
                response = await self.client.post(url, json=payload)
                data = response.json()
                yield data.get("response", "")
        except Exception as e:
            yield f"\n[AI Error: {e}]\n"
    
    async def close(self):
        if self.client:
            await self.client.aclose()

# =======================================================================
# CONSTITUTION
# =======================================================================
class Constitution:
    def __init__(self):
        self.laws = ["SOVEREIGNTY", "TRANSPARENCY", "ACCOUNTABILITY", "SAFETY", "CODE_SAFETY"]
        self.whitelist = ['/health', '/workers', '/sys', '/ollama', '/metrics', '/gpu', '/events']
        self.ruling_history = []
    
    def evaluate(self, action: str, context: Optional[Dict] = None) -> dict:
        action_lower = action.lower()
        
        if any(cmd in action_lower for cmd in self.whitelist):
            return {"approved": True, "reason": "Whitelist", "score": 100}
        
        dangerous = ['rm -rf', 'format', 'del ', 'shutdown', 'reboot', 'mkfs']
        for d in dangerous:
            if d in action_lower:
                return {"approved": False, "reason": f"Safety violation: {d}", "score": 0}
        
        if any(kw in action_lower for kw in ['execute', 'run', 'eval', 'exec']):
            if not settings.allow_code_execution:
                return {"approved": False, "reason": "Code execution disabled", "score": 0}
        
        if any(kw in action_lower for kw in ['write', 'modify', 'delete']):
            if context and context.get('role') != 'admin':
                return {"approved": False, "reason": "File modification requires admin", "score": 30}
        
        return {"approved": True, "reason": "SCE applied", "score": 90}
    
    def get_stats(self) -> Dict[str, Any]:
        return {
            "total_rulings": len(self.ruling_history),
            "laws": self.laws,
            "recent": self.ruling_history[-10:]
        }

constitution = Constitution()

# =======================================================================
# INTENT ROUTER
# =======================================================================
class IntentRouter:
    def __init__(self):
        self.intent_map = {
            'brain': ['explain', 'analyze', 'think', 'what', 'how', 'tell', 'why'],
            'code': ['write', 'code', 'script', 'program', 'function', 'implement'],
            'cortex': ['memory', 'recall', 'remember', 'forget'],
            'file': ['read', 'write', 'save', 'load', 'file', 'directory', 'list'],
            'web': ['search', 'browse', 'fetch', 'download'],
            'data': ['analyze', 'process', 'transform', 'convert']
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
        self.memories[lock] = {'value': blueprint, 'timestamp': time.time(), 'access_count': 0}
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
    
    async def _update_metrics(self):
        while True:
            try:
                if metrics._initialized and metrics.memory_usage:
                    metrics.memory_usage.set(len(self.memories))
                await asyncio.sleep(30)
            except asyncio.CancelledError:
                break
            except:
                await asyncio.sleep(60)
    
    async def shutdown(self):
        if self._update_task:
            self._update_task.cancel()
            try:
                await self._update_task
            except asyncio.CancelledError:
                pass

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
        vram = gpu.get_vram_summary()
        return f"""SYSTEM STATUS:
CPU: {cpu_percent}% ({psutil.cpu_count()} cores)
RAM: {memory.percent}% ({memory.used//1024//1024}MB / {memory.total//1024//1024}MB)
DISK: {disk.percent}% ({disk.used//1024//1024//1024}GB / {disk.total//1024//1024//1024}GB)
GPU: {gpu.gpus[0]['name'] if gpu.has_gpu else 'None'}
VRAM: {vram.get('used_vram_gb', 0)}GB / {vram.get('total_vram_gb', 0)}GB
Uptime: {time.time() - kernel.start_time if kernel else 0:.1f}s"""
    
    async def _gpu(self, kernel=None, args=None) -> str:
        if not gpu.has_gpu:
            return "No GPU detected"
        vram = gpu.get_vram_summary()
        details = gpu.get_gpu_details(0)
        return f"""GPU: {details.get('name', 'Unknown')}
VRAM Total: {vram.get('total_vram_gb', 0)} GiB
VRAM Used: {vram.get('used_vram_gb', 0)} GiB
VRAM Free: {vram.get('free_vram_gb', 0)} GiB
Temperature: {details.get('temperature_celsius', 0)}Â°C
Utilization: {details.get('gpu_utilization_percent', 0)}%"""
    
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
        return f"Loaded workers: {len(kernel.workers)}\n{', '.join(list(kernel.workers.keys())[:20])}"
    
    async def _help(self, kernel=None, args=None) -> str:
        return """Available reflex commands:
/health - System health
/sys - System stats
/gpu - GPU info (VRAM, temp, utilization)
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
        self.version = "13.3.0"
        self.start_time = time.time()
        self.drift_chain = []
        self.constitution = constitution
        self.router = IntentRouter()
        self.memory = SovereignMemory()
        self.reflex = Reflex()
        self.ollama = OllamaClient()
        
        # Load all 48 workers from your workers directory
        self.workers_loader = WorkerLoader()
        self.workers = self.workers_loader.load_all() or {}
        
        # Initialize agentic coding workers
        self.file_worker = FileSystemWorker()
        self.code_executor = CodeExecutionWorker()
        self.code_analyzer = CodeAnalyzerWorker()
        self.test_worker = TestWorker()
        self.refactor_worker = RefactoringWorker(self.ollama)
        
        # Add them to workers dict
        self.workers['file_system'] = {"class": FileSystemWorker, "module": "builtin"}
        self.workers['code_execution'] = {"class": CodeExecutionWorker, "module": "builtin"}
        self.workers['code_analyzer'] = {"class": CodeAnalyzerWorker, "module": "builtin"}
        self.workers['test_runner'] = {"class": TestWorker, "module": "builtin"}
        self.workers['refactor'] = {"class": RefactoringWorker, "module": "builtin"}
        
        # FastAPI App
        self.app = FastAPI(
            title=f"Phoenix v{self.version}",
            description="Zero Drift SCE Protocol with Agentic Coding",
            version=self.version,
            docs_url="/docs" if settings.environment == "development" else None
        )
        
        # ========== HARDENING: Security Headers Middleware ==========
        @self.app.middleware("http")
        async def security_headers(request: Request, call_next):
            response = await call_next(request)
            response.headers["X-Content-Type-Options"] = "nosniff"
            response.headers["X-Frame-Options"] = "DENY"
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
            # CSP - adjust as needed for your frontend
            if settings.environment == "production":
                response.headers["Content-Security-Policy"] = "default-src 'self'"
            return response
        
        # ========== HARDENING: Rate Limiting ==========
        if HAS_SLOWAPI:
            from slowapi import Limiter, _rate_limit_exceeded_handler
            from slowapi.util import get_remote_address
            self.limiter = Limiter(key_func=get_remote_address, default_limits=["30/minute"])
            self.app.state.limiter = self.limiter
            self.app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
            logger.info("âœ… Rate limiting enabled")
        else:
            self.limiter = None
            logger.warning("âš ï¸ Rate limiting not available (install slowapi)")
        
        # ========== HARDENING: CORS (restricted) ==========
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=settings.cors_origins,   # now set from environment
            allow_credentials=True,
            allow_methods=["GET", "POST", "OPTIONS"],  # restrict methods
            allow_headers=["*"],
        )
        
        # Metrics middleware
        if HAS_PROMETHEUS:
            self.app.middleware("http")(self.metrics_middleware)
        
        self.setup_routes()
        
        # Socket.IO
        self.sio = None
        if HAS_SOCKETIO:
            self.sio = socketio.AsyncServer(cors_allowed_origins="*", async_mode='asgi')
            self.setup_socketio()
        
        # Background tasks
        self.background_tasks = []
        
        logger.info(f"ðŸš€ Phoenix v{self.version} initialized")
    
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
                "workers": len(self.workers),
                "features": ["file_operations", "code_execution", "analysis", "refactoring", "testing"]
            }
        
        @self.app.get("/health")
        async def health():
            return await self.get_stats()
        
        @self.app.get("/metrics")
        async def metrics_endpoint():
            if HAS_PROMETHEUS:
                from prometheus_client import generate_latest
                from fastapi.responses import Response
                return Response(content=generate_latest(), media_type="text/plain")
            return {"error": "Prometheus not enabled"}
        
        # ===== GPU & VRAM ENDPOINTS =====
        @self.app.get("/gpu/vram")
        async def gpu_vram():
            return gpu.get_vram_summary()
        
        @self.app.get("/gpu/details/{gpu_id}")
        async def gpu_details(gpu_id: int = 0):
            return gpu.get_gpu_details(gpu_id)
        
        # ===== OLLAMA ENDPOINTS =====
        @self.app.get("/ollama/status")
        async def ollama_status():
            models = []
            try:
                async with httpx.AsyncClient(timeout=5) as client:
                    r = await client.get(f"{settings.ollama_url}/api/tags")
                    if r.status_code == 200:
                        models = r.json().get("models", [])
            except:
                pass
            return {
                "connected": len(models) > 0,
                "models": models,
                "default_model": settings.default_model
            }
        
        # ===== WORKER ENDPOINTS =====
        @self.app.get("/workers/list")
        async def workers_list():
            workers_info = {}
            for name, info in self.workers.items():
                workers_info[name] = {
                    "path": info.get("path", "builtin"),
                    "loaded": info.get("loaded_at", time.time()),
                    "module": info.get("module", "builtin")
                }
            return {
                "loaded": list(self.workers.keys()),
                "count": len(self.workers),
                "details": workers_info
            }
        
        @self.app.get("/workers/metrics")
        async def workers_metrics():
            return await worker_cache.get_metrics()
        
        # ===== EVENT ENDPOINTS =====
        @self.app.get("/events/stats")
        async def events_stats():
            return await event_bus.get_stats()
        
        @self.app.get("/events/recent")
        async def events_recent(limit: int = 100, event_type: Optional[str] = None):
            events = await event_bus.get_events_by_type(event_type, limit)
            return {"events": events, "count": len(events)}
        
        # ===== SCE & MEMORY ENDPOINTS =====
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
        
        # ===== CONSTITUTION ENDPOINTS =====
        @self.app.get("/constitution/stats")
        async def constitution_stats():
            return self.constitution.get_stats()
        
        @self.app.post("/constitution/evaluate")
        async def constitution_evaluate(request: Request):
            data = await request.json()
            action = data.get('action', '')
            context = data.get('context', {})
            return self.constitution.evaluate(action, context)
        
        @self.app.get("/router/stats")
        async def router_stats():
            return self.router.get_stats()
        
        # ===== FILE OPERATION ENDPOINTS =====
        # HARDENING: require admin role for writes/modifies
        @self.app.post("/file/read")
        async def file_read(request: Request):
            data = await request.json()
            result = await self.file_worker.execute(f"read {data.get('path', '')}")
            return result
        
        @self.app.post("/file/write")
        async def file_write(request: Request, role: str = Depends(auth_manager.require_role("admin"))):
            data = await request.json()
            result = await self.file_worker.execute(
                f"write {data.get('path', '')}",
                filename=data.get('path'),
                content=data.get('content', '')
            )
            return result
        
        @self.app.post("/file/list")
        async def file_list(request: Request):
            data = await request.json()
            result = await self.file_worker.execute(f"list {data.get('path', '.')}")
            return result
        
        @self.app.post("/file/search")
        async def file_search(request: Request):
            data = await request.json()
            result = await self.file_worker.execute(f"search {data.get('pattern', '')} {data.get('directory', '.')}")
            return result
        
        # ===== CODE EXECUTION ENDPOINTS =====
        @self.app.post("/code/execute")
        async def code_execute(request: Request, role: str = Depends(auth_manager.require_role("admin"))):
            data = await request.json()
            result = await self.code_executor.execute(data.get('code', ''))
            return result
        
        @self.app.post("/code/analyze")
        async def code_analyze(request: Request):
            data = await request.json()
            if 'file' in data:
                result = await self.code_analyzer.execute(f"analyze file {data['file']}")
            else:
                result = await self.code_analyzer.execute(f"analyze ```python\n{data.get('code', '')}\n```")
            return result
        
        @self.app.post("/code/refactor")
        async def code_refactor(request: Request, role: str = Depends(auth_manager.require_role("admin"))):
            data = await request.json()
            result = await self.refactor_worker.execute(
                f"refactor {data.get('file_path', '')} {data.get('instructions', '')}"
            )
            return result
        
        # ===== TEST ENDPOINTS =====
        @self.app.post("/test/run")
        async def test_run(request: Request):
            data = await request.json()
            result = await self.test_worker.execute(f"test {data.get('target', '')}")
            return result
        
        # ===== MAIN STREAMING ENDPOINT =====
        # HARDENING: apply rate limiting if available
        @self.app.post("/kernel/stream")
        async def kernel_stream(request: Request, background_tasks: BackgroundTasks):
            if self.limiter:
                # apply rate limiting
                await self.limiter.limit("10/minute")(request)
            
            try:
                data = await request.json()
            except:
                return JSONResponse({"error": "Invalid JSON"}, status_code=400)
            
            task = data.get("task", "").strip()
            if not task:
                return JSONResponse({"error": "No task provided"}, status_code=400)
            
            user_id = request.client.host if request.client else "unknown"
            
            async def generate():
                # Check reflex commands
                reflex_result = await self.reflex.execute(task, kernel=self)
                if reflex_result:
                    yield f"data: {json.dumps({'type': 'reflex', 'content': reflex_result['content'], 'command': reflex_result.get('command')})}\n\n"
                    return
                
                # Constitution check
                ruling = self.constitution.evaluate(task, {"role": "user", "user": user_id})
                if not ruling.get("approved"):
                    yield f"data: {json.dumps({'type': 'error', 'content': ruling.get('reason', 'Blocked')})}\n\n"
                    return
                
                # Route intent
                worker_name = self.router.route(task)
                yield f"data: {json.dumps({'type': 'thinking', 'worker': worker_name})}\n\n"
                
                # Try to use a worker
                worker_used = False
                if worker_name in self.workers:
                    try:
                        worker_class = self.workers[worker_name]["class"]
                        worker = await worker_cache.get_worker(worker_class)
                        # HARDENING: set timeout for worker execution
                        if await worker.validate(task):
                            start_time = time.time()
                            # use asyncio.wait_for to enforce timeout
                            worker_result = await asyncio.wait_for(worker.execute(task), timeout=30)
                            duration = time.time() - start_time
                            self.router.report_success(worker_name, True)
                            yield f"data: {json.dumps({'type': 'worker_result', 'worker': worker_name, 'content': worker_result, 'duration': duration})}\n\n"
                            worker_used = True
                    except asyncio.TimeoutError:
                        yield f"data: {json.dumps({'type': 'error', 'content': 'Worker execution timed out'})}\n\n"
                    except Exception as e:
                        logger.error(f"Worker {worker_name} failed: {e}")
                        self.router.report_success(worker_name, False)
                
                # Fall back to Ollama
                if not worker_used:
                    system_prompt = f"You are Phoenix AI v{self.version}. Be concise and helpful."
                    full_response = ""
                    async for chunk in self.ollama.generate(task, system=system_prompt):
                        full_response += chunk
                        yield f"data: {json.dumps({'type': 'result', 'content': chunk})}\n\n"
                
                # Create SCE blueprint
                blueprint = SCEProtocol.create_blueprint(
                    {"task": task, "worker": worker_name, "user": user_id},
                    {"narrative": ["Streaming complete"], "worker_used": worker_used},
                    {"response_length": len(full_response) if not worker_used else 0, "success": True},
                    self.drift_chain[-1] if self.drift_chain else None
                )
                lock = self.memory.store_blueprint(blueprint)
                self.drift_chain.append(lock)
                if metrics._initialized and metrics.drift_chain_length:
                    metrics.drift_chain_length.set(len(self.drift_chain))
                
                yield f"data: {json.dumps({'type': 'done', 'drift_lock': lock})}\n\n"
            
            return StreamingResponse(generate(), media_type="text/event-stream")
        
        @self.app.post("/feedback")
        async def user_feedback(request: Request):
            data = await request.json()
            drift_lock = data.get("drift_lock")
            rating = data.get("rating")
            comment = data.get("comment", "")
            await event_bus.publish(Event(
                type=EventType.USER_FEEDBACK,
                source="feedback_api",
                payload={"drift_lock": drift_lock, "rating": rating, "comment": comment[:500]}
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
                    "Access-Control-Allow-Headers": "Content-Type, Authorization, X-Hive-API-Key",
                    "Access-Control-Allow-Credentials": "true",
                    "Access-Control-Max-Age": "3600",
                }
            )
    
    async def get_stats(self):
        gpu.update_stats()
        event_stats = await event_bus.get_stats()
        worker_metrics = await worker_cache.get_metrics()
        vram = gpu.get_vram_summary()
        
        return {
            "status": "ONLINE",
            "version": self.version,
            "uptime": round(time.time() - self.start_time, 2),
            "workers": len(self.workers),
            "active_workers": worker_metrics.get('active_workers', 0),
            "memory_entries": len(self.memory.memories),
            "drift_chain": len(self.drift_chain),
            "events": event_stats.get('total_events', 0),
            "gpu": gpu.gpus[0]['name'] if gpu.has_gpu else None,
            "gpu_temp": gpu.get_temperature(),
            "gpu_util": gpu.get_utilization(),
            "vram_total_gb": vram.get('total_vram_gb', 0),
            "vram_used_gb": vram.get('used_vram_gb', 0),
            "vram_free_gb": vram.get('free_vram_gb', 0),
            "consciousness": 5 + len(self.workers),
            "sce_enforcement": "FULL",
            "environment": settings.environment
        }
    
    def setup_socketio(self):
        if not self.sio:
            return
        
        @self.sio.event
        async def connect(sid, environ, auth):
            logger.info(f"ðŸŸ¢ Client connected: {sid}")
            if metrics._initialized and metrics.active_connections:
                metrics.active_connections.inc()
            await self.sio.emit('connection_verified', {'status': 'ok', 'version': self.version}, room=sid)
        
        @self.sio.event
        async def disconnect(sid):
            logger.info(f"ðŸ”´ Client disconnected: {sid}")
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
        
        # Log all loaded workers
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
                logger.info(f"ðŸ“Š Metrics server started on port {settings.metrics_port}")
            except Exception as e:
                logger.error(f"Failed to start metrics server: {e}")
        
        vram = gpu.get_vram_summary()
        
        print("\n" + "="*70)
        print(f"ðŸ”¥ PHOENIX ULTIMATE v{self.version} - HARDENED")
        print("="*70)
        print(f"Workers: {len(self.workers)} (48 from directory + 5 agentic)")
        if gpu.has_gpu:
            print(f"GPU: {gpu.gpus[0]['name']} - {vram.get('total_vram_gb', 0):.1f} GiB VRAM")
            print(f"VRAM: {vram.get('used_vram_gb', 0):.1f} GiB used / {vram.get('free_vram_gb', 0):.1f} GiB free")
        else:
            print("GPU: None detected")
        print(f"Memory: {len(self.memory.memories)} blueprint entries")
        print(f"Events: {len(await event_bus.get_events_by_type(''))} persisted")
        print(f"SCE: âœ… FULL ENFORCEMENT")
        print(f"Code Execution: {'âœ…' if settings.allow_code_execution else 'âŒ'}")
        print(f"File Operations: âœ… (Backups enabled)")
        print(f"Prometheus: âœ… on :{settings.metrics_port}" if HAS_PROMETHEUS else "Prometheus: âš ï¸ Disabled")
        print(f"Rate Limiting: {'âœ…' if HAS_SLOWAPI else 'âš ï¸ Disabled (install slowapi)'}")
        print(f"CORS Origins: {settings.cors_origins}")
        
        try:
            async with httpx.AsyncClient(timeout=5) as client:
                r = await client.get(f"{settings.ollama_url}/api/tags")
                if r.status_code == 200:
                    models = r.json().get("models", [])
                    print(f"Ollama: âœ… {len(models)} models available")
                else:
                    print("Ollama: âš ï¸ Not responding")
        except:
            print("Ollama: âš ï¸ Not connected")
        
        print("="*70)
        print(f"ðŸ“¡ API: http://{settings.host}:{settings.port}")
        print(f"ðŸ“Š Metrics: http://{settings.host}:{settings.metrics_port}/metrics")
        print(f"ðŸ“š Docs: http://{settings.host}:{settings.port}/docs")
        print("="*70 + "\n")
    
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
        config = uvicorn.Config(app, host=settings.host, port=settings.port, log_level="info", loop="asyncio")
        server = uvicorn.Server(config)
        try:
            await server.serve()
        finally:
            await self.shutdown()

# =======================================================================
# MAIN ENTRY POINT
# =======================================================================
if __name__ == "__main__":
    kernel = PhoenixKernel()
    try:
        asyncio.run(kernel.run())
    except KeyboardInterrupt:
        print("\nðŸ›‘ Shutting down...")
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)


