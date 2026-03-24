#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PHOENIX ULTIMATE v13.2.2 - REFINED
Zero Drift Architecture + Persistent Event Chain + Formalized Workers + Observability
"""

from __future__ import annotations

import asyncio
import hashlib
import importlib.machinery
import importlib.util
import inspect
import json
import logging
import os
import platform
import psutil
import random
import re
import secrets
import sqlite3
import subprocess
import sys
import time
import traceback
import uuid
import warnings
from abc import ABC, abstractmethod
from collections import defaultdict
from contextlib import contextmanager
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum, auto
from functools import wraps
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import (
    Any,
    AsyncGenerator,
    Awaitable,
    Callable,
    Dict,
    List,
    Optional,
    Tuple,
    Union,
)

# ---------------------------------------------------------------------------
# Platform-specific stdout encoding
# ---------------------------------------------------------------------------
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

# ---------------------------------------------------------------------------
# Suppress noisy third-party warnings
# ---------------------------------------------------------------------------
warnings.filterwarnings("ignore", message=".*duckduckgo_search.*")

# =======================================================================
# THIRD-PARTY IMPORTS (hard requirements first, soft after)
# =======================================================================
try:
    from fastapi import BackgroundTasks, Depends, FastAPI, HTTPException, Request
    from fastapi.middleware.cors import CORSMiddleware
    from fastapi.responses import JSONResponse, StreamingResponse
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
    print("⚠️  Install: pip install python-socketio for real-time features")

try:
    from pydantic import BaseModel, ConfigDict, Field
    from pydantic_settings import BaseSettings, SettingsConfigDict
    HAS_PYDANTIC = True
except ImportError:
    HAS_PYDANTIC = False
    print("⚠️  Install: pip install pydantic pydantic-settings")

try:
    import aiofiles
    import aiofiles.os
    HAS_AIOFILES = True
except ImportError:
    HAS_AIOFILES = False
    print("⚠️  Install: pip install aiofiles for file operations")

try:
    from prometheus_client import (
        Counter,
        Gauge,
        Histogram,
        generate_latest,
        start_http_server,
    )
    HAS_PROMETHEUS = True
except ImportError:
    HAS_PROMETHEUS = False
    print("⚠️  Install: pip install prometheus-client for metrics")

try:
    import httpx
except ImportError:
    print("❌ Install: pip install httpx")
    sys.exit(1)

try:
    import pynvml
    HAS_PYNVML = True
except ImportError:
    HAS_PYNVML = False

# =======================================================================
# CONSTANTS
# =======================================================================
DEFAULT_PORT = 8002
DEFAULT_METRICS_PORT = 8003
CHAIN_MAXLEN = 10_000
EVENT_PERSISTENCE_BATCH = 100
DEFAULT_OLLAMA_TIMEOUT = 60
DEFAULT_OLLAMA_RETRIES = 3
CIRCUIT_BREAKER_THRESHOLD = 5
CIRCUIT_BREAKER_TIMEOUT = 60
GPU_UPDATE_INTERVAL = 5          # seconds
HEALTH_CHECK_INTERVAL = 30       # seconds
MEMORY_METRICS_INTERVAL = 30     # seconds
MAX_INPUT_LENGTH = 10_000
MAX_HISTORY_RULINGS = 1_000
RATE_LIMIT_WINDOW = 60           # seconds
RATE_LIMIT_MAX = 100

# =======================================================================
# DIRECTORIES
# =======================================================================
DIRS: Dict[str, Path] = {
    "logs": Path("logs"),
    "data": Path("data"),
    "uploads": Path("data/uploads"),
    "quarantine": Path("quarantine"),
    "memory": Path("data/memory"),
    "event_store": Path("data/event_store"),
    "bots": Path("bots"),
    "workers": Path("workers"),
}

for d in DIRS.values():
    d.mkdir(parents=True, exist_ok=True)

# =======================================================================
# LOGGING
# =======================================================================
_log_handler = RotatingFileHandler(
    DIRS["logs"] / "phoenix_ultimate.log",
    maxBytes=10 * 1024 * 1024,
    backupCount=5,
    encoding="utf-8",
)
_log_handler.setFormatter(
    logging.Formatter("%(asctime)s [%(levelname)s] %(name)s - %(message)s")
)
logging.basicConfig(
    level=logging.INFO,
    handlers=[_log_handler, logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("PHOENIX_ULTIMATE")


# =======================================================================
# PROMETHEUS METRICS (lazy, safe to check before init)
# =======================================================================
class _Metrics:
    """Thin wrapper – all gauges/counters start as *None* until ``init()``."""

    def __init__(self) -> None:
        self._ready = False
        self.event_counter: Optional[Counter] = None
        self.worker_duration: Optional[Histogram] = None
        self.active_connections: Optional[Gauge] = None
        self.blueprint_counter: Optional[Counter] = None
        self.memory_usage: Optional[Gauge] = None
        self.drift_chain_length: Optional[Gauge] = None
        self.gpu_temp: Optional[Gauge] = None
        self.api_requests: Optional[Counter] = None
        self.api_duration: Optional[Histogram] = None

    # -- public API -------------------------------------------------------

    def init(self) -> None:
        if self._ready or not HAS_PROMETHEUS:
            return
        self.event_counter = Counter(
            "phoenix_events_total", "Total events published", ["event_type"]
        )
        self.worker_duration = Histogram(
            "phoenix_worker_duration_seconds",
            "Worker execution time",
            ["worker_name"],
        )
        self.active_connections = Gauge(
            "phoenix_active_connections", "Active WebSocket connections"
        )
        self.blueprint_counter = Counter(
            "phoenix_blueprints_total", "Total blueprints created"
        )
        self.memory_usage = Gauge("phoenix_memory_entries", "Memory store entries")
        self.drift_chain_length = Gauge(
            "phoenix_drift_chain_length", "Drift chain length"
        )
        self.gpu_temp = Gauge("phoenix_gpu_temperature", "GPU temperature")
        self.api_requests = Counter(
            "phoenix_api_requests_total", "API requests", ["endpoint", "method"]
        )
        self.api_duration = Histogram(
            "phoenix_api_request_duration_seconds",
            "API request duration",
            ["endpoint"],
        )
        self._ready = True
        logger.info("✅ Prometheus metrics initialised")

    @property
    def is_ready(self) -> bool:
        return self._ready and HAS_PROMETHEUS

    def inc(self, counter: Optional[Counter], amount: int = 1, **labels) -> None:
        if self.is_ready and counter is not None:
            counter.labels(**labels).inc(amount) if labels else counter.inc(amount)

    def observe(self, hist: Optional[Histogram], value: float, **labels) -> None:
        if self.is_ready and hist is not None:
            hist.labels(**labels).observe(value) if labels else hist.observe(value)

    def set_gauge(self, gauge: Optional[Gauge], value: float) -> None:
        if self.is_ready and gauge is not None:
            gauge.set(value)


metrics = _Metrics()

# =======================================================================
# CONFIGURATION
# =======================================================================


class Settings(BaseSettings):
    environment: str = os.getenv("ENV", "development")
    port: int = int(os.getenv("PHOENIX_PORT", str(DEFAULT_PORT)))
    metrics_port: int = int(os.getenv("METRICS_PORT", str(DEFAULT_METRICS_PORT)))
    host: str = os.getenv("PHOENIX_HOST", "0.0.0.0")
    log_level: str = os.getenv("LOG_LEVEL", "INFO")

    # Security
    api_key_admin: str = os.getenv("PHOENIX_ADMIN_KEY", secrets.token_urlsafe(32))
    api_key_viewer: str = os.getenv("PHOENIX_VIEWER_KEY", secrets.token_urlsafe(32))
    allowed_hosts: str = os.getenv("ALLOWED_HOSTS", "*")

    # Ollama
    ollama_url: str = os.getenv("OLLAMA_URL", "http://localhost:11434")
    default_model: str = os.getenv("OLLAMA_MODEL", "llama3.2:latest")
    ollama_timeout: int = int(os.getenv("OLLAMA_TIMEOUT", str(DEFAULT_OLLAMA_TIMEOUT)))

    # CORS
    frontend_urls: list = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:8002",
        "http://127.0.0.1:8002",
    ]

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @property
    def api_keys(self) -> Dict[str, str]:
        keys: Dict[str, str] = {"rez-hive-admin-key-2026": "admin"}
        admin = os.getenv("PHOENIX_ADMIN_KEY")
        viewer = os.getenv("PHOENIX_VIEWER_KEY")
        if admin:
            keys[admin] = "admin"
        if viewer:
            keys[viewer] = "viewer"
        return keys


settings = Settings()


# =======================================================================
# PYDANTIC MODELS (only if pydantic is available)
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
        model_config = ConfigDict(extra="forbid")

    class EventModel(BaseModel):
        type: str
        source: str
        payload: Dict[str, Any]
        timestamp: float
        previous_hash: str
        vera_proof: str
        model_config = ConfigDict(extra="forbid")

    class WorkerConfigModel(BaseModel):
        name: str
        enabled: bool = True
        max_concurrent: int = 5
        timeout: int = 30
        requires_gpu: bool = False
        environment: Dict[str, str] = Field(default_factory=dict)
        model_config = ConfigDict(extra="allow")


# =======================================================================
# SECURITY
# =======================================================================
class SecurityError(Exception):
    pass


def sanitize_input(text: str, max_length: int = MAX_INPUT_LENGTH) -> str:
    if not isinstance(text, str):
        raise SecurityError("Input must be a string")
    if len(text) > max_length:
        raise SecurityError(f"Input exceeds {max_length} characters")
    cleaned = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", "", text)
    if ".." in cleaned or "~" in cleaned:
        raise SecurityError("Path traversal attempt detected")
    return cleaned.strip()


def validate_safe_path(base_dir: Path, user_path: str) -> Path:
    base = base_dir.resolve()
    if os.path.isabs(user_path):
        raise SecurityError("Absolute paths are not allowed")
    target = (base / user_path).resolve()
    try:
        target.relative_to(base)
    except ValueError:
        raise SecurityError("Path escapes base directory")
    return target


# =======================================================================
# CONTEXT-MANAGED SQLITE
# =======================================================================


@contextmanager
def _db(db_path: Path):
    """Yield a cursor; commit on clean exit, rollback on exception."""
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = None
    try:
        cursor = conn.cursor()
        yield cursor
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


@contextmanager
def _db_rows(db_path: Path):
    """Same as _db but returns rows as dicts."""
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    try:
        cursor = conn.cursor()
        yield cursor
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


# =======================================================================
# CIRCUIT BREAKER
# =======================================================================
class CircuitBreaker:
    """Simple async-aware circuit breaker."""

    def __init__(
        self,
        name: str,
        threshold: int = CIRCUIT_BREAKER_THRESHOLD,
        timeout: int = CIRCUIT_BREAKER_TIMEOUT,
    ) -> None:
        self.name = name
        self.threshold = threshold
        self.timeout = timeout
        self.failure_count = 0
        self.last_failure_time: float = 0.0
        self.state = "CLOSED"  # CLOSED → OPEN → HALF_OPEN → CLOSED
        self._lock = asyncio.Lock()

    async def call(self, func: Callable, *args, **kwargs):
        # --- gate check ---
        async with self._lock:
            if self.state == "OPEN":
                if time.time() - self.last_failure_time > self.timeout:
                    self.state = "HALF_OPEN"
                    logger.info("Circuit %s → HALF_OPEN", self.name)
                else:
                    raise RuntimeError(f"Circuit {self.name} is OPEN")

        # --- execute ---
        try:
            if asyncio.iscoroutinefunction(func):
                result = await func(*args, **kwargs)
            else:
                result = func(*args, **kwargs)
            async with self._lock:
                if self.state == "HALF_OPEN":
                    self.state = "CLOSED"
                    self.failure_count = 0
                    logger.info("Circuit %s → CLOSED (recovered)", self.name)
            return result
        except Exception:
            async with self._lock:
                self.failure_count += 1
                self.last_failure_time = time.time()
                if self.state in ("CLOSED", "HALF_OPEN") and self.failure_count >= self.threshold:
                    self.state = "OPEN"
                    logger.warning(
                        "Circuit %s → OPEN (failures: %d)",
                        self.name,
                        self.failure_count,
                    )
            raise


# =======================================================================
# GPU MONITOR
# =======================================================================
class GPUMonitor:
    def __init__(self) -> None:
        self.has_gpu = False
        self.name = "N/A"
        self.temp = 0
        self.utilization = 0
        self.memory_used = 0
        self.memory_total = 0
        self._handle = None
        self._task: Optional[asyncio.Task] = None
        self._init_gpu()

    # -- init -------------------------------------------------------------
    def _init_gpu(self) -> None:
        if not HAS_PYNVML:
            logger.info("ℹ️  pynvml not installed – GPU stats disabled")
            return
        try:
            pynvml.nvmlInit()
            if pynvml.nvmlDeviceGetCount() > 0:
                self._handle = pynvml.nvmlDeviceGetHandleByIndex(0)
                raw = pynvml.nvmlDeviceGetName(self._handle)
                self.name = raw.decode() if isinstance(raw, bytes) else raw
                self.has_gpu = True
                self.update_stats()
                logger.info("✅ GPU detected: %s", self.name)
        except Exception as exc:
            logger.info("ℹ️  GPU monitoring unavailable: %s", exc)

    # -- stats ------------------------------------------------------------
    def update_stats(self) -> None:
        if not self.has_gpu or self._handle is None:
            return
        try:
            self.temp = pynvml.nvmlDeviceGetTemperature(
                self._handle, pynvml.NVML_TEMPERATURE_GPU
            )
        except Exception:
            self.temp = 0
        try:
            util = pynvml.nvmlDeviceGetUtilizationRates(self._handle)
            self.utilization = util.gpu
        except Exception:
            self.utilization = 0
        try:
            mem = pynvml.nvmlDeviceGetMemoryInfo(self._handle)
            self.memory_used = mem.used // (1024 * 1024)
            self.memory_total = mem.total // (1024 * 1024)
        except Exception:
            pass

    # -- background loop --------------------------------------------------
    async def start_background_updates(self) -> None:
        if self.has_gpu and self._task is None:
            self._task = asyncio.create_task(self._loop())
            logger.info("✅ GPU background monitoring started")

    async def _loop(self) -> None:
        while True:
            try:
                self.update_stats()
                metrics.set_gauge(metrics.gpu_temp, self.temp)
                await asyncio.sleep(GPU_UPDATE_INTERVAL)
            except asyncio.CancelledError:
                break
            except Exception as exc:
                logger.error("GPU update error: %s", exc)
                await asyncio.sleep(GPU_UPDATE_INTERVAL * 2)

    async def shutdown(self) -> None:
        if self._task:
            self._task.cancel()
            with contextmanager(lambda: (yield))():
                pass  # noqa – keep syntax consistent
            try:
                await self._task
            except asyncio.CancelledError:
                pass


gpu = GPUMonitor()

# =======================================================================
# EVENT TYPES & DATA
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

    def __post_init__(self) -> None:
        # Serialize payload safely – fall back to repr if JSON fails
        try:
            payload_str = json.dumps(self.payload, sort_keys=True, default=str)
        except (TypeError, ValueError):
            payload_str = repr(self.payload)
        content = (
            f"{self.type.value}:{self.source}:"
            f"{payload_str}:"
            f"{self.timestamp}:{self.previous_hash}"
        )
        object.__setattr__(self, "_vera_proof", hashlib.sha256(content.encode()).hexdigest()[:16])

    @property
    def vera_proof(self) -> str:
        return getattr(self, "_vera_proof", "")

    def to_dict(self) -> Dict[str, Any]:
        """JSON-safe dict (payload uses default=str)."""
        return {
            "vera_proof": self.vera_proof,
            "type": self.type.value,
            "source": self.source,
            "payload": json.dumps(self.payload, default=str),
            "timestamp": self.timestamp,
            "previous_hash": self.previous_hash,
        }


# =======================================================================
# PERSISTENT EVENT STORE (SQLite)
# =======================================================================
class EventStore:
    def __init__(self, db_path: Path) -> None:
        self.db_path = db_path
        self._init_db()

    def _init_db(self) -> None:
        with _db(self.db_path) as cur:
            cur.execute(
                """CREATE TABLE IF NOT EXISTS events (
                       vera_proof   TEXT PRIMARY KEY,
                       type         TEXT,
                       source       TEXT,
                       payload      TEXT,
                       timestamp    REAL,
                       previous_hash TEXT,
                       created_at   REAL
                   )"""
            )
            cur.execute(
                """CREATE TABLE IF NOT EXISTS blueprints (
                       drift_lock TEXT PRIMARY KEY,
                       blueprint  TEXT,
                       timestamp  REAL
                   )"""
            )
            cur.execute(
                "CREATE INDEX IF NOT EXISTS idx_events_type ON events(type)"
            )
            cur.execute(
                "CREATE INDEX IF NOT EXISTS idx_events_ts ON events(timestamp)"
            )

    # -- writes -----------------------------------------------------------
    async def save_event(self, event: Event) -> bool:
        try:
            with _db(self.db_path) as cur:
                d = event.to_dict()
                cur.execute(
                    """INSERT OR REPLACE INTO events
                       (vera_proof, type, source, payload, timestamp, previous_hash, created_at)
                       VALUES (?,?,?,?,?,?,?)""",
                    (
                        d["vera_proof"],
                        d["type"],
                        d["source"],
                        d["payload"],
                        d["timestamp"],
                        d["previous_hash"],
                        time.time(),
                    ),
                )
            return True
        except Exception as exc:
            logger.error("Failed to save event: %s", exc)
            return False

    async def save_blueprint(self, drift_lock: str, blueprint: dict) -> bool:
        try:
            with _db(self.db_path) as cur:
                cur.execute(
                    "INSERT OR REPLACE INTO blueprints (drift_lock, blueprint, timestamp) VALUES (?,?,?)",
                    (drift_lock, json.dumps(blueprint, default=str), time.time()),
                )
            return True
        except Exception as exc:
            logger.error("Failed to save blueprint: %s", exc)
            return False

    # -- reads ------------------------------------------------------------
    async def get_events(
        self, limit: int = 100, event_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        try:
            with _db_rows(self.db_path) as cur:
                if event_type:
                    cur.execute(
                        "SELECT * FROM events WHERE type=? ORDER BY timestamp DESC LIMIT ?",
                        (event_type, limit),
                    )
                else:
                    cur.execute(
                        "SELECT * FROM events ORDER BY timestamp DESC LIMIT ?",
                        (limit,),
                    )
                return [dict(row) for row in cur.fetchall()]
        except Exception as exc:
            logger.error("Failed to fetch events: %s", exc)
            return []

    async def get_blueprint(self, drift_lock: str) -> Optional[Dict[str, Any]]:
        try:
            with _db(self.db_path) as cur:
                cur.execute(
                    "SELECT blueprint FROM blueprints WHERE drift_lock=?", (drift_lock,)
                )
                row = cur.fetchone()
            return json.loads(row[0]) if row else None
        except Exception as exc:
            logger.error("Failed to fetch blueprint: %s", exc)
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
    def create_blueprint(
        intent: dict,
        dna: dict,
        execution: dict,
        parent_lock: Optional[str] = None,
    ) -> dict:
        bp: Dict[str, Any] = {
            "protocol_version": SCEProtocol.VERSION,
            "timestamp": datetime.now().isoformat(),
            "intent": intent,
            "dna": dna,
            "execution": execution,
        }
        if parent_lock:
            bp["parent_drift_lock"] = parent_lock
        bp["master_drift_lock"] = SCEProtocol.create_drift_lock(bp)
        return bp

    @staticmethod
    def verify_blueprint(blueprint: dict) -> dict:
        stored = blueprint.get("master_drift_lock")
        calculated = SCEProtocol.create_drift_lock(blueprint)
        return {
            "verified": stored == calculated,
            "badge": "🟢 SOVEREIGN" if stored == calculated else "🔴 DRIFTED",
            "drift_lock": stored,
        }


# =======================================================================
# EVENT BUS (chain + SQLite persistence)
# =======================================================================
class SovereignEventBus:
    def __init__(self) -> None:
        self._chain: List[Event] = []
        self._lock = asyncio.Lock()
        self._genesis = hashlib.sha256(b"PHOENIX_ULTIMATE_v13.2.2").hexdigest()[:16]
        self._store = EventStore(DIRS["event_store"] / "events.db")
        self._persist_queue: Optional[asyncio.Queue] = None
        self._persist_task: Optional[asyncio.Task] = None
        self._ready = False

    # -- lifecycle --------------------------------------------------------
    async def initialize(self) -> None:
        if self._ready:
            return
        await self._load_recent()
        self._persist_queue = asyncio.Queue()
        self._persist_task = asyncio.create_task(self._persist_loop())
        self._ready = True
        logger.info("✅ Event bus initialised (%d events loaded)", len(self._chain))
        await self.publish(
            Event(type=EventType.SYSTEM_BOOT, source="event_bus", payload={"version": "13.2.2"})
        )

    async def shutdown(self) -> None:
        if self._persist_task:
            self._persist_task.cancel()
            try:
                await self._persist_task
            except asyncio.CancelError:
                pass

    # -- persistence loop -------------------------------------------------
    async def _load_recent(self) -> None:
        try:
            rows = await self._store.get_events(limit=CHAIN_MAXLEN)
            loaded = 0
            for row in reversed(rows):
                try:
                    ev = Event(
                        type=EventType(row["type"]),
                        source=row["source"],
                        payload=json.loads(row["payload"]),
                        timestamp=row["timestamp"],
                        previous_hash=row["previous_hash"],
                    )
                    self._chain.append(ev)
                    loaded += 1
                except Exception:
                    pass
            logger.info("Restored %d events from store", loaded)
        except Exception as exc:
            logger.error("Failed loading events: %s", exc)

    async def _persist_loop(self) -> None:
        batch: List[Event] = []
        while True:
            try:
                ev = await asyncio.wait_for(self._persist_queue.get(), timeout=1.0)
                batch.append(ev)
                if len(batch) >= EVENT_PERSISTENCE_BATCH:
                    await self._flush(batch)
                    batch = []
            except asyncio.TimeoutError:
                if batch:
                    await self._flush(batch)
                    batch = []
            except asyncio.CancelledError:
                if batch:
                    await self._flush(batch)
                break
            except Exception as exc:
                logger.error("Persistence loop error: %s", exc)
                await asyncio.sleep(1)

    async def _flush(self, batch: List[Event]) -> None:
        for ev in batch:
            await self._store.save_event(ev)
        metrics.inc(metrics.event_counter, len(batch), event_type="batch")

    # -- publish / verify -------------------------------------------------
    async def publish(self, event: Event) -> Optional[str]:
        if not self._ready:
            logger.warning("Bus not ready – event dropped")
            return None
        async with self._lock:
            prev = self._chain[-1].vera_proof if self._chain else self._genesis
            linked = Event(
                type=event.type,
                source=event.source,
                payload=event.payload,
                timestamp=event.timestamp,
                previous_hash=prev,
            )
            if len(self._chain) >= CHAIN_MAXLEN:
                self._chain.pop(0)
            self._chain.append(linked)
        if self._persist_queue:
            await self._persist_queue.put(linked)
        metrics.inc(metrics.event_counter, event_type=linked.type.value)
        logger.debug("Published %s [%s]", linked.type.value, linked.vera_proof)
        return linked.vera_proof

    async def verify_chain(self) -> bool:
        async with self._lock:
            prev = self._genesis
            for ev in self._chain:
                expected = Event(
                    type=ev.type,
                    source=ev.source,
                    payload=ev.payload,
                    timestamp=ev.timestamp,
                    previous_hash=prev,
                ).vera_proof
                if ev.vera_proof != expected:
                    logger.error("Chain broken at %s", ev.vera_proof)
                    return False
                prev = ev.vera_proof
            return True

    # -- queries ----------------------------------------------------------
    async def get_stats(self) -> Dict[str, Any]:
        async with self._lock:
            counts: Dict[str, int] = defaultdict(int)
            for ev in self._chain:
                counts[ev.type.value] += 1
            return {
                "total_events": len(self._chain),
                "chain_integrity": await self.verify_chain(),
                "genesis_hash": self._genesis,
                "latest_hash": self._chain[-1].vera_proof if self._chain else self._genesis,
                "event_counts": dict(counts),
                "persist_queue_size": self._persist_queue.qsize() if self._persist_queue else 0,
            }

    async def get_events_by_type(
        self, event_type: Optional[str] = None, limit: int = 100
    ) -> List[Dict[str, Any]]:
        return await self._store.get_events(limit=limit, event_type=event_type)


event_bus = SovereignEventBus()

# =======================================================================
# AUTHENTICATION
# =======================================================================


class AuthManager:
    def __init__(self) -> None:
        self._rate: Dict[str, List[float]] = defaultdict(list)

    async def verify_key(self, api_key: Optional[str], client_ip: Optional[str] = None) -> str:
        if not api_key:
            raise HTTPException(status_code=403, detail="API key required")
        # rate limit
        if client_ip:
            now = time.time()
            self._rate[client_ip] = [t for t in self._rate[client_ip] if t > now - RATE_LIMIT_WINDOW]
            if len(self._rate[client_ip]) >= RATE_LIMIT_MAX:
                raise HTTPException(status_code=429, detail="Rate limit exceeded")
            self._rate[client_ip].append(now)
        role = settings.api_keys.get(api_key)
        if not role:
            await event_bus.publish(
                Event(type=EventType.AUTH_FAILURE, source="auth", payload={"ip": client_ip})
            )
            raise HTTPException(status_code=403, detail="Invalid API key")
        return role

    def require_role(self, required: str):
        """FastAPI dependency factory."""

        async def _dep(
            request: Request,
            creds: Optional[HTTPAuthorizationCredentials] = Depends(HTTPBearer(auto_error=False)),
        ) -> str:
            ip = request.client.host if request.client else None
            key = creds.credentials if creds else request.headers.get("X-Hive-API-Key")
            role = await self.verify_key(key, ip)
            if required == "admin" and role != "admin":
                raise HTTPException(status_code=403, detail="Admin access required")
            return role

        return _dep


auth = AuthManager()

# =======================================================================
# WORKER BASE CLASS
# =======================================================================


class Worker(ABC):
    """Base class all workers must extend."""

    def __init__(self, name: Optional[str] = None) -> None:
        self.name = name or self.__class__.__name__
        self.metrics: Dict[str, Any] = {"calls": 0, "errors": 0, "total_duration": 0.0, "last_call": None}
        self._lock = asyncio.Lock()

    @abstractmethod
    async def execute(self, task: str, **kwargs) -> Dict[str, Any]:
        ...

    async def validate(self, task: str) -> bool:
        return True

    async def get_metrics(self) -> Dict[str, Any]:
        async with self._lock:
            m = dict(self.metrics)
        m["avg_duration"] = m["total_duration"] / m["calls"] if m["calls"] else 0.0
        return m

    async def _record(self, duration: float, success: bool) -> None:
        async with self._lock:
            self.metrics["calls"] += 1
            self.metrics["total_duration"] += duration
            self.metrics["last_call"] = time.time()
            if not success:
                self.metrics["errors"] += 1


# =======================================================================
# SCE DECORATOR (wraps any function with blueprint emission)
# =======================================================================


def sce_compliant(worker_name: str = "unknown"):
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            intent = {
                "worker": worker_name,
                "function": func.__name__,
                "timestamp": time.time(),
            }
            start = time.time()
            try:
                await event_bus.publish(
                    Event(type=EventType.WORKER_START, source=worker_name, payload={"function": func.__name__})
                )
                if asyncio.iscoroutinefunction(func):
                    result = await func(*args, **kwargs)
                else:
                    result = func(*args, **kwargs)
                dur = time.time() - start
                bp = SCEProtocol.create_blueprint(
                    intent,
                    {"narrative": [f"{worker_name} executed {func.__name__}"]},
                    {"result": str(result)[:200], "success": True, "duration": dur},
                )
                await event_bus.publish(
                    Event(type=EventType.SCE_BLUEPRINT_CREATED, source=worker_name, payload={"blueprint": bp})
                )
                await event_bus.publish(
                    Event(type=EventType.WORKER_COMPLETE, source=worker_name, payload={"duration": dur, "success": True})
                )
                metrics.observe(metrics.worker_duration, dur, worker_name=worker_name)
                return {"sce_compliant": True, "blueprint": bp, "result": result, "drift_lock": bp["master_drift_lock"]}
            except Exception as exc:
                dur = time.time() - start
                bp = SCEProtocol.create_blueprint(
                    intent,
                    {"narrative": [f"{worker_name} failed: {exc}"]},
                    {"error": str(exc), "success": False, "duration": dur},
                )
                await event_bus.publish(
                    Event(type=EventType.WORKER_ERROR, source=worker_name, payload={"blueprint": bp, "error": str(exc)})
                )
                metrics.observe(metrics.worker_duration, dur, worker_name=worker_name)
                return {"sce_compliant": True, "blueprint": bp, "error": str(exc), "drift_lock": bp["master_drift_lock"]}

        return wrapper

    return decorator


# =======================================================================
# WORKER CACHE (singleton instances per class)
# =======================================================================


class WorkerCache:
    def __init__(self) -> None:
        self._instances: Dict[str, Worker] = {}
        self._locks: Dict[str, asyncio.Lock] = defaultdict(asyncio.Lock)
        self._stats = {"loads": 0, "reloads": 0, "clears": 0}

    async def get(self, cls: type, name: Optional[str] = None) -> Worker:
        key = name or cls.__name__
        async with self._locks[key]:
            if key not in self._instances:
                self._instances[key] = cls(name=key)
                self._stats["loads"] += 1
                logger.info("Worker cache: loaded %s", key)
            return self._instances[key]

    async def reload(self, key: str) -> bool:
        async with self._locks[key]:
            if key in self._instances:
                del self._instances[key]
                self._stats["reloads"] += 1
                return True
        return False

    def clear(self) -> None:
        self._instances.clear()
        self._stats["clears"] += 1

    async def get_metrics(self) -> Dict[str, Any]:
        wm: Dict[str, Any] = {}
        for k, w in self._instances.items():
            wm[k] = await w.get_metrics()
        return {"cache": dict(self._stats), "workers": wm, "active_workers": len(self._instances)}


worker_cache = WorkerCache()

# =======================================================================
# WORKER LOADER (auto-discovers .py files in workers/)
# =======================================================================

# Methods that indicate a "worker-like" class
_WORKER_SIGNAL_METHODS = {"execute", "process", "run", "handle", "work"}
_WORKER_KEYWORDS = {"Worker", "Plugin", "Skill", "Agent"}


def _looks_like_worker(cls: type) -> bool:
    name = cls.__name__
    if any(kw in name for kw in _WORKER_KEYWORDS):
        return True
    # Walk bases up to 3 levels
    stack = list(cls.__bases__)
    depth = 0
    while stack and depth < 3:
        base = stack.pop()
        if any(kw in base.__name__ for kw in _WORKER_KEYWORDS):
            return True
        stack.extend(base.__bases__)
        depth += 1
    # Check for characteristic methods
    methods = {m for m in dir(cls) if not m.startswith("_") and callable(getattr(cls, m, None))}
    if methods & _WORKER_SIGNAL_METHODS:
        return True
    return False


class WorkerLoader:
    def __init__(self, workers_dir: Path = DIRS["workers"]) -> None:
        self.workers_dir = workers_dir.resolve()
        self.loaded: Dict[str, Dict[str, Any]] = {}
        self.failed: List[str] = []
        # Ensure import path
        for p in (str(self.workers_dir), str(self.workers_dir.parent)):
            if p not in sys.path:
                sys.path.insert(0, p)

    def load_all(self) -> Dict[str, Dict[str, Any]]:
        if not self.workers_dir.exists():
            logger.error("Workers directory not found: %s", self.workers_dir)
            return {}

        skip = {"__init__.py", "base_worker.py"}
        files = [f for f in self.workers_dir.glob("*.py") if f.name not in skip]
        logger.info("Scanning %d files in %s", len(files), self.workers_dir)

        for path in files:
            try:
                spec = importlib.util.spec_from_file_location(path.stem, path)
                if not spec or not spec.loader:
                    raise ImportError(f"Cannot create spec for {path.name}")
                mod = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(mod)

                found = 0
                for cname, obj in inspect.getmembers(mod, inspect.isclass):
                    if obj.__module__ != mod.__name__:
                        continue
                    if _looks_like_worker(obj):
                        self.loaded[cname] = {
                            "class": obj,
                            "module": path.stem,
                            "path": str(path),
                            "loaded_at": time.time(),
                            "methods": [
                                m
                                for m in dir(obj)
                                if not m.startswith("_") and callable(getattr(obj, m, None))
                            ],
                        }
                        found += 1
                        logger.info("  ✅ %s ← %s", cname, path.name)

                if found == 0:
                    logger.warning("  ⚠️  No worker classes in %s", path.name)

            except Exception as exc:
                logger.error("  ❌ %s: %s", path.name, exc)
                self.failed.append(path.name)

        logger.info("Loaded %d workers (%d failed)", len(self.loaded), len(self.failed))
        return self.loaded


# =======================================================================
# CONSTITUTION (rule evaluator)
# =======================================================================


class Constitution:
    LAWS = ["SOVEREIGNTY", "TRANSPARENCY", "ACCOUNTABILITY", "SAFETY"]
    WHITELIST = ["/health", "/workers", "/sys", "/ollama", "/metrics"]
    DANGEROUS = ["rm -rf", "format", "del ", "shutdown", "reboot", "mkfs"]
    SYSTEM_PATHS = ["/etc", "/bin", "/boot", "/dev", "/proc", "/sys"]

    def __init__(self) -> None:
        self.history: List[Dict[str, Any]] = []

    def evaluate(self, action: str, context: Optional[Dict] = None) -> dict:
        low = action.lower()

        # Whitelist pass
        if any(w in low for w in self.WHITELIST):
            ruling = {"approved": True, "reason": "Whitelist", "score": 100}
        # Dangerous command block
        elif any(d in low for d in self.DANGEROUS):
            hit = next(d for d in self.DANGEROUS if d in low)
            ruling = {"approved": False, "reason": f"SAFETY violation: {hit}", "score": 0}
        # System path guard
        elif any(p in low for p in self.SYSTEM_PATHS) and (not context or context.get("role") != "admin"):
            ruling = {"approved": False, "reason": "System path access requires admin", "score": 30}
        else:
            ruling = {
                "approved": True,
                "score": 90,
                "reason": "SCE applied",
                "laws_applied": ["TRANSPARENCY", "ACCOUNTABILITY"],
            }

        self._record(action, ruling)
        return ruling

    def _record(self, action: str, ruling: dict) -> None:
        entry = {"timestamp": time.time(), "action": action[:100], "ruling": ruling}
        self.history.append(entry)
        if len(self.history) > MAX_HISTORY_RULINGS:
            self.history.pop(0)
        # Fire-and-forget event (safe even without running loop in some edge cases)
        try:
            loop = asyncio.get_running_loop()
            loop.create_task(
                event_bus.publish(
                    Event(type=EventType.CONSTITUTION_RULING, source="constitution", payload=entry)
                )
            )
        except RuntimeError:
            pass  # no running loop – skip

    def get_stats(self) -> Dict[str, Any]:
        approved = sum(1 for r in self.history if r["ruling"]["approved"])
        total = len(self.history)
        return {
            "total_rulings": total,
            "approved": approved,
            "denied": total - approved,
            "approval_rate": approved / total if total else 0.0,
            "laws": self.LAWS,
            "recent": self.history[-10:],
        }


# =======================================================================
# INTENT ROUTER
# =======================================================================


class IntentRouter:
    MAP = {
        "brain": ["explain", "analyze", "think", "what", "how", "tell", "why", "describe"],
        "code": ["write", "code", "script", "program", "function", "implement", "debug"],
        "cortex": ["memory", "recall", "remember", "forget", "store"],
        "file": ["read", "write", "save", "load", "file", "directory"],
        "web": ["search", "browse", "fetch", "download", "scrape"],
        "data": ["analyze", "process", "transform", "convert", "parse"],
    }

    def __init__(self) -> None:
        self.stats: Dict[str, Dict[str, int]] = defaultdict(lambda: {"hits": 0, "success": 0})

    def route(self, task: str) -> str:
        low = task.lower()
        scores = {
            w: sum(1 for kw in kws if kw in low)
            for w, kws in self.MAP.items()
            if any(kw in low for kw in kws)
        }
        best = max(scores, key=scores.get) if scores else "brain"
        self.stats[best]["hits"] += 1
        return best

    def report(self, worker: str, success: bool) -> None:
        if success:
            self.stats[worker]["success"] += 1

    def get_stats(self) -> Dict[str, Any]:
        out: Dict[str, Any] = {}
        for w, d in self.stats.items():
            out[w] = {**d, "success_rate": d["success"] / d["hits"] if d["hits"] else 0.0}
        return out


# =======================================================================
# SOVEREIGN MEMORY
# =======================================================================


class SovereignMemory:
    def __init__(self) -> None:
        self.memories: Dict[str, Dict[str, Any]] = {}
        self.blueprint_index: Dict[str, str] = {}
        self._store = EventStore(DIRS["event_store"] / "events.db")
        self._task: Optional[asyncio.Task] = None
        self._load_from_disk()

    def store_blueprint(self, blueprint: Dict) -> str:
        lock = blueprint.get("master_drift_lock", SCEProtocol.create_drift_lock(blueprint))
        record = {"value": blueprint, "timestamp": time.time(), "access_count": 0}
        self.memories[lock] = record
        self.blueprint_index[lock] = lock
        # persist to disk + db
        try:
            (DIRS["memory"] / f"sce_{lock}.json").write_text(json.dumps(record, indent=2, default=str))
        except Exception as exc:
            logger.error("Disk persist failed: %s", exc)
        try:
            loop = asyncio.get_running_loop()
            loop.create_task(self._store.save_blueprint(lock, blueprint))
        except RuntimeError:
            pass
        metrics.inc(metrics.blueprint_counter)
        metrics.set_gauge(metrics.memory_usage, len(self.memories))
        return lock

    def verify(self, drift_lock: str) -> dict:
        rec = self.memories.get(drift_lock)
        if not rec:
            return {"verified": False, "error": "Blueprint not found"}
        rec["access_count"] = rec.get("access_count", 0) + 1
        return SCEProtocol.verify_blueprint(rec["value"])

    def search(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        ql = query.lower()
        results: List[Dict[str, Any]] = []
        for lock, rec in self.memories.items():
            bp = rec["value"]
            score = 0
            intent_s = json.dumps(bp.get("intent", {}), default=str).lower()
            dna_s = json.dumps(bp.get("dna", {}), default=str).lower()
            if ql in intent_s:
                score += 5
            if ql in dna_s:
                score += 3
            if score:
                results.append(
                    {
                        "lock": lock,
                        "score": score,
                        "timestamp": rec["timestamp"],
                        "intent": bp.get("intent"),
                        "access_count": rec.get("access_count", 0),
                    }
                )
        results.sort(key=lambda r: (r["score"], r["timestamp"]), reverse=True)
        return results[:limit]

    def _load_from_disk(self) -> None:
        for p in DIRS["memory"].glob("*.json"):
            try:
                data = json.loads(p.read_text())
                if "value" in data and "master_drift_lock" in data["value"]:
                    lock = data["value"]["master_drift_lock"]
                    self.memories[lock] = data
                    self.blueprint_index[lock] = lock
            except Exception:
                pass

    async def start_background_updates(self) -> None:
        if self._task is None:
            self._task = asyncio.create_task(self._metrics_loop())
            logger.info("✅ Memory metrics loop started")

    async def _metrics_loop(self) -> None:
        while True:
            try:
                metrics.set_gauge(metrics.memory_usage, len(self.memories))
                await asyncio.sleep(MEMORY_METRICS_INTERVAL)
            except asyncio.CancelledError:
                break
            except Exception as exc:
                logger.error("Memory metrics error: %s", exc)
                await asyncio.sleep(MEMORY_METRICS_INTERVAL * 2)

    async def shutdown(self) -> None:
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass


# =======================================================================
# OLLAMA CLIENT
# =======================================================================


class OllamaClient:
    def __init__(self) -> None:
        self._client: Optional[httpx.AsyncClient] = None
        self.circuit = CircuitBreaker("ollama")
        self.stats: Dict[str, Any] = {
            "calls": 0,
            "failures": 0,
            "total_tokens": 0,
            "last_call": None,
        }

    async def _ensure_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(timeout=settings.ollama_timeout)
        return self._client

    # -- generate ---------------------------------------------------------
    async def generate(
        self,
        prompt: str,
        *,
        stream: bool = True,
        system: Optional[str] = None,
    ) -> AsyncGenerator[str, None]:
        client = await self._ensure_client()
        url = f"{settings.ollama_url}/api/generate"
        payload: Dict[str, Any] = {"model": settings.default_model, "prompt": prompt, "stream": stream}
        if system:
            payload["system"] = system

        self.stats["calls"] += 1
        self.stats["last_call"] = time.time()
        metrics.inc(metrics.api_requests, endpoint="ollama", method="POST")

        async def _call():
            async with client.stream("POST", url, json=payload) as resp:
                if stream:
                    async for line in resp.aiter_lines():
                        if not line:
                            continue
                        try:
                            chunk = json.loads(line)
                        except json.JSONDecodeError:
                            continue
                        if "response" in chunk:
                            self.stats["total_tokens"] += 1
                            yield chunk["response"]
                        if chunk.get("done"):
                            return
                else:
                    data = await resp.json()
                    yield data.get("response", "")

        try:
            async for piece in self.circuit.call(_call):
                yield piece
        except Exception as exc:
            self.stats["failures"] += 1
            yield f"\n[AI_ERROR: {exc}]"

    # -- models / stats ---------------------------------------------------
    async def get_models(self) -> list:
        try:
            client = await self._ensure_client()
            resp = await client.get(f"{settings.ollama_url}/api/tags", timeout=5.0)
            return resp.json().get("models", []) if resp.status_code == 200 else []
        except Exception:
            return []

    async def get_stats(self) -> Dict[str, Any]:
        return {
            **self.stats,
            "circuit_state": self.circuit.state,
            "circuit_failures": self.circuit.failure_count,
        }

    async def close(self) -> None:
        if self._client and not self._client.is_closed:
            await self._client.aclose()


# =======================================================================
# REFLEX COMMANDS
# =======================================================================


class Reflex:
    def __init__(self) -> None:
        self.commands: Dict[str, Callable] = {
            "/health": self._health,
            "/sys": self._sys,
            "/gpu": self._gpu,
            "/memory": self._memory,
            "/events": self._events,
            "/workers": self._workers,
            "/help": self._help,
        }

    async def execute(self, cmd: str, *, kernel: "PhoenixKernel" = None) -> Optional[Dict]:
        cmd = cmd.strip().lower()
        for prefix, handler in self.commands.items():
            if cmd == prefix or cmd.startswith(prefix + " "):
                arg = cmd[len(prefix) :].strip()
                content = await handler(kernel, arg) if arg else await handler(kernel)
                return {"content": content, "type": "reflex", "command": prefix}
        return None

    @staticmethod
    async def _health(kernel=None, _="") -> str:
        return json.dumps(await kernel.get_stats(), indent=2) if kernel else "Kernel unavailable"

    @staticmethod
    async def _sys(kernel=None, _="") -> str:
        gpu.update_stats()
        cpu = psutil.cpu_percent(interval=0.5)
        mem = psutil.virtual_memory()
        disk = psutil.disk_usage("/")
        up = time.time() - kernel.start_time if kernel else 0
        return (
            f"CPU: {cpu}% ({psutil.cpu_count()} cores)\n"
            f"RAM: {mem.percent}% ({mem.used // (1024*1024)}MB / {mem.total // (1024*1024)}MB)\n"
            f"DISK: {disk.percent}% ({disk.used // (1024**3)}GB / {disk.total // (1024**3)}GB)\n"
            f"GPU: {gpu.name if gpu.has_gpu else 'None'} {gpu.temp}°C {gpu.utilization}%\n"
            f"Uptime: {up:.1f}s"
        )

    @staticmethod
    async def _gpu(kernel=None, _="") -> str:
        gpu.update_stats()
        if not gpu.has_gpu:
            return "No GPU detected"
        return f"{gpu.name}\nTemp: {gpu.temp}°C  Util: {gpu.utilization}%  Mem: {gpu.memory_used}/{gpu.memory_total}MB"

    @staticmethod
    async def _memory(kernel=None, arg="") -> str:
        if not kernel:
            return "Kernel unavailable"
        if arg.startswith("search "):
            q = arg[7:]
            hits = kernel.memory.search(q)
            if not hits:
                return f"No memories for: {q}"
            lines = [f"[{h['lock']}] score={h['score']} accesses={h['access_count']}" for h in hits[:5]]
            return f"Results for '{q}':\n" + "\n".join(lines)
        return f"Memory: {len(kernel.memory.memories)} blueprints"

    @staticmethod
    async def _events(kernel=None, _="") -> str:
        return json.dumps(await event_bus.get_stats(), indent=2)

    @staticmethod
    async def _workers(kernel=None, arg="") -> str:
        if not kernel:
            return "Kernel unavailable"
        if arg == "stats":
            return json.dumps(await worker_cache.get_metrics(), indent=2)
        names = list(kernel.workers.keys())
        return f"Workers ({len(names)}): {', '.join(names)}"

    @staticmethod
    async def _help(kernel=None, _="") -> str:
        return (
            "/health  /sys  /gpu  /memory [search <q>]\n"
            "/events  /workers [stats]  /help"
        )


# =======================================================================
# PHOENIX KERNEL (FastAPI app + orchestration)
# =======================================================================


class PhoenixKernel:
    VERSION = "13.2.2"

    def __init__(self) -> None:
        self.start_time = time.time()
        self.drift_chain: List[str] = []

        # Core subsystems
        self.constitution = Constitution()
        self.router = IntentRouter()
        self.memory = SovereignMemory()
        self.reflex = Reflex()
        self.ollama = OllamaClient()

        # Workers
        self._loader = WorkerLoader()
        self.workers = self._loader.load_all()

        # FastAPI
        self.app = FastAPI(
            title=f"Phoenix v{self.VERSION}",
            description="Zero Drift SCE Protocol",
            version=self.VERSION,
            docs_url="/docs" if settings.environment == "development" else None,
            redoc_url=None,
        )
        origins = ["*"] if settings.environment == "development" else settings.frontend_urls
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=origins,
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        if metrics.is_ready:
            self.app.middleware("http")(self._metrics_middleware)

        self._register_routes()

        # Socket.IO
        self.sio: Optional[socketio.AsyncServer] = None
        if HAS_SOCKETIO:
            self.sio = socketio.AsyncServer(
                cors_allowed_origins="*" if settings.environment == "development" else origins,
                async_mode="asgi",
            )
            self._register_socketio()

        self._bg: List[asyncio.Task] = []
        logger.info("🚀 Phoenix v%s ready", self.VERSION)

    # -- metrics middleware -----------------------------------------------
    async def _metrics_middleware(self, request: Request, call_next):
        t0 = time.time()
        metrics.inc(metrics.api_requests, endpoint=request.url.path, method=request.method)
        response = await call_next(request)
        metrics.observe(metrics.api_duration, time.time() - t0, endpoint=request.url.path)
        return response

    # =====================================================================
    # ROUTES
    # =====================================================================
    def _register_routes(self) -> None:
        app = self.app  # shorthand

        # ---- public -----------------------------------------------------
        @app.get("/")
        async def _root():
            return {
                "name": "Phoenix AI",
                "version": self.VERSION,
                "status": "online",
                "standard": "Rezonic Agentic Standard v1.0",
            }

        @app.get("/health")
        async def _health():
            return await self.get_stats()

        @app.get("/metrics")
        async def _metrics_ep():
            if HAS_PROMETHEUS:
                from fastapi.responses import Response
                return Response(content=generate_latest(), media_type="text/plain")
            return {"error": "Prometheus not enabled"}

        @app.get("/ollama/status")
        async def _ollama_status():
            models = await self.ollama.get_models()
            return {"connected": bool(models), "models": models, "stats": await self.ollama.get_stats()}

        # ---- workers ----------------------------------------------------
        @app.get("/workers/list")
        async def _wlist(_role=Depends(auth.require_role("viewer"))):
            details = {}
            for name, info in self.workers.items():
                details[name] = {
                    "module": info.get("module"),
                    "path": info.get("path"),
                    "loaded_at": info.get("loaded_at"),
                }
            return {"loaded": list(self.workers), "count": len(self.workers), "details": details}

        @app.get("/workers/metrics")
        async def _wmetrics(_role=Depends(auth.require_role("admin"))):
            return await worker_cache.get_metrics()

        @app.post("/workers/reload/{name}")
        async def _wreload(name: str, _role=Depends(auth.require_role("admin"))):
            return {"success": await worker_cache.reload(name), "worker": name}

        # ---- events -----------------------------------------------------
        @app.get("/events/stats")
        async def _estats():
            return await event_bus.get_stats()

        @app.get("/events/recent")
        async def _erecent(limit: int = 100, event_type: Optional[str] = None):
            events = await event_bus.get_events_by_type(event_type, limit)
            return {"events": events, "count": len(events)}

        # ---- sce / memory -----------------------------------------------
        @app.get("/sce/status")
        async def _sce():
            return {
                "version": SCEProtocol.VERSION,
                "blueprints": len(self.memory.memories),
                "drift_chain": self.drift_chain[-10:],
                "length": len(self.drift_chain),
            }

        @app.get("/memory/blueprints")
        async def _bp():
            return {"count": len(self.memory.memories), "recent": list(self.memory.blueprint_index)[-50:]}

        @app.get("/memory/search")
        async def _bsearch(query: str, limit: int = 10):
            return {"results": self.memory.search(query, limit)}

        @app.get("/memory/verify/{lock}")
        async def _bverify(lock: str):
            return self.memory.verify(lock)

        # ---- constitution -----------------------------------------------
        @app.get("/constitution/stats")
        async def _cstats():
            return self.constitution.get_stats()

        @app.post("/constitution/evaluate")
        async def _ceval(request: Request, _role=Depends(auth.require_role("viewer"))):
            data = await request.json()
            return self.constitution.evaluate(data.get("action", ""), data.get("context"))

        # ---- router -----------------------------------------------------
        @app.get("/router/stats")
        async def _rstats():
            return self.router.get_stats()

        # ---- main stream endpoint ---------------------------------------
        @app.post("/kernel/stream")
        async def _stream(
            request: Request,
            bg: BackgroundTasks,
            role=Depends(auth.require_role("viewer")),
        ):
            try:
                data = await request.json()
            except Exception:
                return JSONResponse({"error": "Invalid JSON"}, 400)

            task: str = data.get("task", "").strip()
            if not task:
                return JSONResponse({"error": "No task provided"}, 400)

            user_ip = request.client.host if request.client else "unknown"
            bg.add_task(self._track, user_ip, task)

            kernel_ref = self  # capture for closure

            async def _generate():
                # 1) Reflex
                reflex = await kernel_ref.reflex.execute(task, kernel=kernel_ref)
                if reflex:
                    yield f"data: {json.dumps(reflex)}\n\n"
                    return

                # 2) Constitution
                ruling = kernel_ref.constitution.evaluate(task, {"role": role, "user": user_ip})
                if not ruling.get("approved"):
                    yield f"data: {json.dumps({'type': 'error', 'content': ruling.get('reason')})}\n\n"
                    return

                # 3) Route
                worker_name = kernel_ref.router.route(task)
                yield f"data: {json.dumps({'type': 'thinking', 'worker': worker_name})}\n\n"

                full_response = ""
                worker_used = False

                # 4) Try worker
                if worker_name in kernel_ref.workers:
                    try:
                        info = kernel_ref.workers[worker_name]
                        wcls = info["class"]
                        w = await worker_cache.get(wcls, worker_name)
                        if await w.validate(task):
                            t0 = time.time()
                            result = await w.execute(task)
                            dur = time.time() - t0
                            kernel_ref.router.report(worker_name, True)
                            yield f"data: {json.dumps({'type': 'worker_result', 'worker': worker_name, 'content': result, 'duration': dur})}\n\n"
                            worker_used = True
                    except Exception as exc:
                        logger.error("Worker %s error: %s", worker_name, exc)
                        kernel_ref.router.report(worker_name, False)

                # 5) Fallback → Ollama
                if not worker_used:
                    system = f"You are Phoenix v{self.VERSION}. Be concise."
                    async for chunk in kernel_ref.ollama.generate(task, system=system):
                        full_response += chunk
                        yield f"data: {json.dumps({'type': 'result', 'content': chunk})}\n\n"

                # 6) Blueprint
                bp = SCEProtocol.create_blueprint(
                    {"task": task, "worker": worker_name, "user": user_ip, "role": role},
                    {"narrative": ["Streaming complete"], "worker_used": worker_used},
                    {"response_length": len(full_response), "success": True},
                    kernel_ref.drift_chain[-1] if kernel_ref.drift_chain else None,
                )
                lock = kernel_ref.memory.store_blueprint(bp)
                kernel_ref.drift_chain.append(lock)
                metrics.set_gauge(metrics.drift_chain_length, len(kernel_ref.drift_chain))
                yield f"data: {json.dumps({'type': 'done', 'drift_lock': lock})}\n\n"

            return StreamingResponse(_generate(), media_type="text/event-stream")

        # ---- feedback ---------------------------------------------------
        @app.post("/feedback")
        async def _feedback(request: Request, _role=Depends(auth.require_role("viewer"))):
            d = await request.json()
            await event_bus.publish(
                Event(
                    type=EventType.USER_FEEDBACK,
                    source="feedback",
                    payload={
                        "drift_lock": d.get("drift_lock"),
                        "rating": d.get("rating"),
                        "comment": str(d.get("comment", ""))[:500],
                    },
                )
            )
            return {"success": True}

        # ---- CORS preflight catch-all -----------------------------------
        @app.options("/{path:path}")
        async def _options(request: Request, path: str):
            origin = request.headers.get("origin", "*")
            return JSONResponse(
                {},
                headers={
                    "Access-Control-Allow-Origin": origin,
                    "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS, PATCH",
                    "Access-Control-Allow-Headers": "Content-Type, Authorization, X-Hive-API-Key, X-Requested-With, Accept",
                    "Access-Control-Allow-Credentials": "true",
                    "Access-Control-Max-Age": "3600",
                    "Access-Control-Expose-Headers": "*",
                },
            )

    # ---- Socket.IO -----------------------------------------------------
    def _register_socketio(self) -> None:
        sio = self.sio
        kernel_ref = self

        @sio.event
        async def connect(sid, environ, auth):
            logger.info("🟢 WS connect: %s", sid)
            metrics.inc(metrics.active_connections)
            await sio.emit("connection_verified", {"status": "ok", "version": self.VERSION}, room=sid)

        @sio.event
        async def disconnect(sid):
            logger.info("🔴 WS disconnect: %s", sid)
            metrics.inc(metrics.active_connections, amount=-1)

        @sio.event
        async def message(sid, data):
            task = data.get("task", "")
            await sio.emit("thinking", {"worker": kernel_ref.router.route(task)}, room=sid)
            async for chunk in kernel_ref.ollama.generate(task):
                await sio.emit("chunk", {"content": chunk}, room=sid)
            await sio.emit("done", room=sid)

    # ---- helpers --------------------------------------------------------
    async def _track(self, user_id: str, task: str) -> None:
        logger.info("User %s: %s…", user_id, task[:60])

    async def get_stats(self) -> Dict[str, Any]:
        gpu.update_stats()
        ev = await event_bus.get_stats()
        wm = await worker_cache.get_metrics()
        models = await self.ollama.get_models()
        return {
            "status": "ONLINE",
            "version": self.VERSION,
            "uptime": round(time.time() - self.start_time, 2),
            "workers": len(self.workers),
            "active_workers": wm.get("active_workers", 0),
            "memory_entries": len(self.memory.memories),
            "drift_chain": len(self.drift_chain),
            "events": ev.get("total_events", 0),
            "gpu": gpu.name if gpu.has_gpu else None,
            "gpu_temp": gpu.temp,
            "gpu_util": gpu.utilization,
            "consciousness": 5 + len(self.workers),
            "sce_enforcement": "FULL",
            "environment": settings.environment,
            "ollama_connected": bool(models),
        }

    # ---- health-check background loop ----------------------------------
    async def _health_loop(self) -> None:
        while True:
            try:
                metrics.set_gauge(metrics.drift_chain_length, len(self.drift_chain))
                models = await self.ollama.get_models()
                if not models:
                    logger.warning("Ollama not responding")
                await asyncio.sleep(HEALTH_CHECK_INTERVAL)
            except asyncio.CancelledError:
                break
            except Exception as exc:
                logger.error("Health loop error: %s", exc)
                await asyncio.sleep(HEALTH_CHECK_INTERVAL * 2)

    # =====================================================================
    # LIFECYCLE
    # =====================================================================
    async def startup(self) -> None:
        metrics.init()
        await gpu.start_background_updates()
        await event_bus.initialize()
        await self.memory.start_background_updates()
        await self.ollama._ensure_client()

        for name in self.workers:
            await event_bus.publish(
                Event(type=EventType.WORKER_LOADED, source="loader", payload={"worker": name})
            )

        self._bg.append(asyncio.create_task(self._health_loop()))

        if HAS_PROMETHEUS:
            try:
                start_http_server(settings.metrics_port)
                logger.info("📊 Metrics on :%d", settings.metrics_port)
            except Exception as exc:
                logger.error("Metrics server failed: %s", exc)

        models = await self.ollama.get_models()
        print(
            f"\n{'='*60}\n"
            f"🔥 PHOENIX v{self.VERSION} – ENHANCED SCE PROTOCOL\n"
            f"{'='*60}\n"
            f"Workers:  {len(self.workers)}\n"
            f"GPU:      {gpu.name if gpu.has_gpu else 'None'}\n"
            f"Memory:   {len(self.memory.memories)} entries\n"
            f"SCE:      ✅ FULL ENFORCEMENT\n"
            f"Prom:     {'✅ :'+str(settings.metrics_port) if HAS_PROMETHEUS else '⚠️ Disabled'}\n"
            f"Ollama:   {'✅ '+str(len(models))+' models' if models else '⚠️ Offline'}\n"
            f"{'='*60}\n"
        )

    async def shutdown(self) -> None:
        logger.info("Shutting down…")
        for t in self._bg:
            t.cancel()
        if self._bg:
            await asyncio.gather(*self._bg, return_exceptions=True)
        await gpu.shutdown()
        await self.memory.shutdown()
        await self.ollama.close()
        await event_bus.shutdown()
        logger.info("Shutdown complete ✓")

    async def run(self) -> None:
        await self.startup()
        asgi = socketio.ASGIApp(self.sio, self.app) if self.sio else self.app
        server = uvicorn.Server(
            uvicorn.Config(asgi, host=settings.host, port=settings.port, log_level="info")
        )
        try:
            await server.serve()
        finally:
            await self.shutdown()


# =======================================================================
# ENTRY POINT
# =======================================================================
if __name__ == "__main__":
    # Kill anything already on our port (best-effort, Windows-aware)
    if platform.system() == "Windows":
        try:
            out = subprocess.run(
                f"netstat -ano | findstr :{DEFAULT_PORT}",
                shell=True, capture_output=True, text=True,
            ).stdout
            for line in out.splitlines():
                if "LISTENING" in line:
                    pid = line.strip().split()[-1]
                    subprocess.run(f"taskkill /F /PID {pid}", shell=True)
                    logger.info("Freed port %d (killed PID %s)", DEFAULT_PORT, pid)
        except Exception:
            pass

    asyncio.run(PhoenixKernel().run())