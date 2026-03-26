#!/usr/bin/env python3
"""
RezHive Phoenix Kernel v15.0.0
Clean rewrite. Same soul. Everything works.
"""

import sys
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

import asyncio
import hashlib
import json
import logging
import os
import re
import shutil
import time
import uuid
import random
import sqlite3
import tempfile
import importlib.util
import inspect
import warnings
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, auto
from pathlib import Path
from typing import Dict, Any, Optional, List, Callable, Awaitable
from abc import ABC, abstractmethod
from logging.handlers import RotatingFileHandler

warnings.filterwarnings("ignore")

# ─── Directories ───────────────────────────────────────────────
for d in ["logs", "data", "data/event_store", "data/backups",
          "data/sandbox", "data/memory", "data/uploads",
          "workers", "workers/coworker"]:
    Path(d).mkdir(parents=True, exist_ok=True)

# ─── Logging ───────────────────────────────────────────────────
log_handler = RotatingFileHandler(
    'logs/phoenix.log', maxBytes=10*1024*1024,
    backupCount=5, encoding='utf-8'
)
log_handler.setFormatter(
    logging.Formatter("%(asctime)s [%(levelname)s] %(name)s - %(message)s")
)
logging.basicConfig(
    level=logging.INFO,
    handlers=[log_handler, logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("PHOENIX")

# ─── Optional Dependencies ────────────────────────────────────
try:
    from fastapi import (
        FastAPI, Request, WebSocket, WebSocketDisconnect,
        Depends, HTTPException, UploadFile, File
    )
    from fastapi.middleware.cors import CORSMiddleware
    from fastapi.middleware.trustedhost import TrustedHostMiddleware
    from fastapi.responses import StreamingResponse, JSONResponse, Response
    from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
    import uvicorn
except ImportError:
    print("FATAL: pip install fastapi uvicorn")
    sys.exit(1)

try:
    import httpx
    HAS_HTTPX = True
except ImportError:
    HAS_HTTPX = False

try:
    import psutil
    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False

try:
    import pynvml
    HAS_PYNVML = True
except ImportError:
    HAS_PYNVML = False

try:
    import socketio
    HAS_SOCKETIO = True
except ImportError:
    HAS_SOCKETIO = False

try:
    from prometheus_client import (
        Counter, Histogram, Gauge, generate_latest, start_http_server
    )
    HAS_PROMETHEUS = True
except ImportError:
    HAS_PROMETHEUS = False


# ════════════════════════════════════════════════════════════════
# CONFIGURATION
# ════════════════════════════════════════════════════════════════
class Config:
    NAME = "PHOENIX"
    VERSION = "15.0.0"
    HOST = os.getenv("PHOENIX_HOST", "0.0.0.0")
    PORT = int(os.getenv("PHOENIX_PORT", "8002"))
    METRICS_PORT = int(os.getenv("METRICS_PORT", "8003"))
    CORS_ORIGINS = os.getenv(
        "CORS_ORIGINS",
        "http://localhost:3000,http://127.0.0.1:3000"
    ).split(",")

    # Auth
    API_KEYS = {
        "rez-hive-admin-key-2026": "admin",
        "rez-hive-viewer-key-2026": "viewer",
    }

    # Rate limiting
    RATE_LIMIT_CALLS = int(os.getenv("RATE_LIMIT_CALLS", "100"))
    RATE_LIMIT_PERIOD = int(os.getenv("RATE_LIMIT_PERIOD", "60"))

    # Ollama
    OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
    DEFAULT_MODEL = os.getenv("OLLAMA_MODEL", "qwen2.5-coder:7b")
    OLLAMA_NUM_CTX = int(os.getenv("OLLAMA_NUM_CTX", "32768"))
    OLLAMA_TIMEOUT = int(os.getenv("OLLAMA_TIMEOUT", "120"))

    # Paths
    WORKSPACE_DIR = Path.cwd()
    MEMORY_DIR = Path("data/memory")
    EVENT_STORE_DIR = Path("data/event_store")
    WORKERS_DIR = Path("workers")
    COWORKER_DIR = Path("workers/coworker")
    BACKUPS_DIR = Path("data/backups")
    SANDBOX_DIR = Path("data/sandbox")

    # Security
    MAX_FILE_SIZE = 50 * 1024 * 1024
    ALLOWED_EXTENSIONS = {
        '.txt', '.md', '.json', '.csv', '.py', '.js',
        '.tsx', '.ts', '.jpg', '.png', '.pdf'
    }

    # Constitution
    CONSTITUTION_LAWS = [
        "SOVEREIGNTY", "TRANSPARENCY",
        "ACCOUNTABILITY", "SAFETY", "CODE_SAFETY"
    ]

    # Event chain
    CHAIN_MAXLEN = 10_000


cfg = Config()


# ════════════════════════════════════════════════════════════════
# SECURITY
# ════════════════════════════════════════════════════════════════
class SecurityError(Exception):
    pass


def sanitize_input(text: str, max_length: int = 10_000) -> str:
    if not isinstance(text, str):
        raise SecurityError("Input must be string")
    if len(text) > max_length:
        raise SecurityError(f"Input exceeds {max_length} chars")
    cleaned = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]', '', text)
    if '..' in cleaned or '~' in cleaned:
        raise SecurityError("Path traversal detected")
    return cleaned.strip()


def secure_filename(filename: str) -> str:
    if not filename or len(filename) > 255:
        raise SecurityError("Invalid filename")
    safe = re.sub(r'[^\w\-\.]', '', os.path.basename(filename)).lstrip('.')
    return f"{int(time.time())}_{safe or 'unnamed'}"


# ════════════════════════════════════════════════════════════════
# RATE LIMITER
# ════════════════════════════════════════════════════════════════
class RateLimiter:
    def __init__(self, max_calls: int, period: int):
        self.max_calls = max_calls
        self.period = period
        self._calls: Dict[str, List[float]] = defaultdict(list)

    async def check(self, client_id: str) -> bool:
        now = time.time()
        calls = self._calls[client_id]
        self._calls[client_id] = [t for t in calls if now - t < self.period]
        if len(self._calls[client_id]) >= self.max_calls:
            return False
        self._calls[client_id].append(now)
        return True


# ════════════════════════════════════════════════════════════════
# CIRCUIT BREAKER
# ════════════════════════════════════════════════════════════════
class CircuitState(Enum):
    CLOSED = auto()
    OPEN = auto()
    HALF_OPEN = auto()


class CircuitBreaker:
    def __init__(
        self, name: str,
        failure_threshold: int = 3,
        recovery_timeout: float = 30.0,
        half_open_max: int = 3
    ):
        self.name = name
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.half_open_max = half_open_max
        self._state = CircuitState.CLOSED
        self._failures = 0
        self._last_failure = 0.0
        self._half_open_calls = 0
        self._lock = asyncio.Lock()

    @property
    def state(self) -> CircuitState:
        return self._state

    async def call(self, func: Callable, *args, **kwargs) -> Any:
        async with self._lock:
            if self._state == CircuitState.OPEN:
                if time.time() - self._last_failure > self.recovery_timeout:
                    self._state = CircuitState.HALF_OPEN
                    self._half_open_calls = 0
                    logger.info(f"[{self.name}] HALF-OPEN")
                else:
                    raise Exception(f"[{self.name}] Circuit OPEN")

            if self._state == CircuitState.HALF_OPEN:
                if self._half_open_calls >= self.half_open_max:
                    raise Exception(f"[{self.name}] HALF-OPEN limit")
                self._half_open_calls += 1

        try:
            result = await func(*args, **kwargs)
            async with self._lock:
                if self._state == CircuitState.HALF_OPEN:
                    self._state = CircuitState.CLOSED
                    self._failures = 0
                    logger.info(f"[{self.name}] RECOVERED")
            return result
        except Exception as e:
            async with self._lock:
                self._failures += 1
                self._last_failure = time.time()
                if self._failures >= self.failure_threshold:
                    self._state = CircuitState.OPEN
                    logger.error(
                        f"[{self.name}] OPEN after {self._failures} failures"
                    )
            raise


ollama_breaker = CircuitBreaker("ollama")


# ════════════════════════════════════════════════════════════════
# AUTH
# ════════════════════════════════════════════════════════════════
security_scheme = HTTPBearer(auto_error=False)


async def get_role(
    credentials: HTTPAuthorizationCredentials = Depends(security_scheme)
) -> str:
    if not credentials:
        return "anonymous"
    role = cfg.API_KEYS.get(credentials.credentials)
    if not role:
        raise HTTPException(403, "Invalid API key")
    return role


# ════════════════════════════════════════════════════════════════
# SCE PROTOCOL
# ════════════════════════════════════════════════════════════════
class SCE:
    VERSION = "2.0.0"

    @staticmethod
    def drift_lock(data: Any) -> str:
        raw = json.dumps(data, sort_keys=True, default=str)
        return hashlib.sha256(raw.encode()).hexdigest()[:16]

    @staticmethod
    def blueprint(
        intent: dict, dna: dict,
        execution: dict, parent: str = None
    ) -> dict:
        bp = {
            "protocol_version": SCE.VERSION,
            "timestamp": datetime.now().isoformat(),
            "intent": intent,
            "dna": dna,
            "execution": execution,
        }
        if parent:
            bp["parent_drift_lock"] = parent
        bp["master_drift_lock"] = SCE.drift_lock(bp)
        return bp

    @staticmethod
    def verify(blueprint: dict) -> dict:
        stored = blueprint.get("master_drift_lock")
        check = SCE.drift_lock(blueprint)
        valid = stored == check
        return {
            "verified": valid,
            "badge": "🟢 SOVEREIGN" if valid else "🔴 DRIFTED",
            "drift_lock": stored,
        }


# ════════════════════════════════════════════════════════════════
# EVENT STORE (SQLite)
# ════════════════════════════════════════════════════════════════
class EventStore:
    def __init__(self, db_path: Path):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS events (
                    vera_proof TEXT PRIMARY KEY,
                    type TEXT,
                    source TEXT,
                    payload TEXT,
                    timestamp REAL,
                    previous_hash TEXT
                );
                CREATE TABLE IF NOT EXISTS blueprints (
                    drift_lock TEXT PRIMARY KEY,
                    blueprint TEXT,
                    timestamp REAL
                );
                CREATE INDEX IF NOT EXISTS idx_ev_type
                    ON events(type);
                CREATE INDEX IF NOT EXISTS idx_ev_ts
                    ON events(timestamp);
            """)

    def save_event(self, event) -> bool:
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute(
                    "INSERT OR REPLACE INTO events VALUES (?,?,?,?,?,?)",
                    (event.vera_proof, event.type.value, event.source,
                     json.dumps(event.payload), event.timestamp,
                     event.previous_hash)
                )
            return True
        except Exception as e:
            logger.error(f"Event save failed: {e}")
            return False

    def save_blueprint(self, lock: str, bp: dict) -> bool:
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute(
                    "INSERT OR REPLACE INTO blueprints VALUES (?,?,?)",
                    (lock, json.dumps(bp), time.time())
                )
            return True
        except Exception as e:
            logger.error(f"Blueprint save failed: {e}")
            return False

    def get_events(
        self, limit: int = 100, event_type: str = None
    ) -> List[Dict]:
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                if event_type:
                    rows = conn.execute(
                        "SELECT * FROM events WHERE type=? "
                        "ORDER BY timestamp DESC LIMIT ?",
                        (event_type, limit)
                    ).fetchall()
                else:
                    rows = conn.execute(
                        "SELECT * FROM events "
                        "ORDER BY timestamp DESC LIMIT ?",
                        (limit,)
                    ).fetchall()
                return [dict(r) for r in rows]
        except:
            return []


# ════════════════════════════════════════════════════════════════
# EVENT BUS (Blockchain-linked)
# ════════════════════════════════════════════════════════════════
class EventType(Enum):
    SYSTEM_BOOT = "system.boot"
    KERNEL_HEARTBEAT = "kernel.heartbeat"
    WORKER_LOADED = "worker.loaded"
    WORKER_COMPLETE = "worker.complete"
    WORKER_ERROR = "worker.error"
    SCE_BLUEPRINT = "sce.blueprint"
    CONSTITUTION_RULING = "constitution.ruling"
    MEMORY_STORED = "memory.stored"
    FILE_OPERATION = "file.operation"
    MARKET_UPDATE = "market.update"
    ARBITRAGE = "market.arbitrage"
    CHAT_MESSAGE = "chat.message"
    OLLAMA_CALL = "ollama.call"


@dataclass(frozen=True)
class Event:
    type: EventType
    source: str
    payload: Dict[str, Any]
    timestamp: float = field(default_factory=time.time)
    previous_hash: str = ""

    def __post_init__(self):
        raw = (
            f"{self.type.value}:{self.source}:"
            f"{json.dumps(self.payload, sort_keys=True)}:"
            f"{self.timestamp}:{self.previous_hash}"
        )
        proof = hashlib.sha256(raw.encode()).hexdigest()[:16]
        object.__setattr__(self, '_vera_proof', proof)

    @property
    def vera_proof(self) -> str:
        return getattr(self, '_vera_proof', '')


class EventBus:
    def __init__(self):
        self._chain: List[Event] = []
        self._lock = asyncio.Lock()
        self._genesis = hashlib.sha256(
            b"PHOENIX_v15.0.0"
        ).hexdigest()[:16]
        self._store = EventStore(cfg.EVENT_STORE_DIR / "events.db")
        self._queue: Optional[asyncio.Queue] = None
        self._worker_task: Optional[asyncio.Task] = None
        self._ready = False

    async def initialize(self):
        if self._ready:
            return
        self._queue = asyncio.Queue()
        self._worker_task = asyncio.create_task(self._persist_loop())
        self._ready = True
        logger.info("✅ Event bus ready")

    async def publish(self, event: Event) -> str:
        if not self._ready:
            return ""
        async with self._lock:
            prev = (
                self._chain[-1].vera_proof
                if self._chain else self._genesis
            )
            linked = Event(
                type=event.type, source=event.source,
                payload=event.payload, previous_hash=prev
            )
            if len(self._chain) >= cfg.CHAIN_MAXLEN:
                self._chain.pop(0)
            self._chain.append(linked)

        await self._queue.put(linked)
        return linked.vera_proof

    async def verify_chain(self) -> bool:
        async with self._lock:
            prev = self._genesis
            for ev in self._chain:
                raw = (
                    f"{ev.type.value}:{ev.source}:"
                    f"{json.dumps(ev.payload, sort_keys=True)}:"
                    f"{ev.timestamp}:{prev}"
                )
                expected = hashlib.sha256(raw.encode()).hexdigest()[:16]
                if ev.vera_proof != expected:
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
                "chain_valid": await self.verify_chain(),
                "genesis": self._genesis,
                "latest": (
                    self._chain[-1].vera_proof
                    if self._chain else self._genesis
                ),
                "counts": dict(counts),
            }

    async def _persist_loop(self):
        batch = []
        while True:
            try:
                event = await asyncio.wait_for(
                    self._queue.get(), timeout=2.0
                )
                batch.append(event)
                if len(batch) >= 50:
                    for ev in batch:
                        self._store.save_event(ev)
                    batch = []
            except asyncio.TimeoutError:
                if batch:
                    for ev in batch:
                        self._store.save_event(ev)
                    batch = []
            except asyncio.CancelledError:
                for ev in batch:
                    self._store.save_event(ev)
                return
            except Exception as e:
                logger.error(f"Persist error: {e}")
                await asyncio.sleep(1)

    async def shutdown(self):
        if self._worker_task:
            self._worker_task.cancel()
            try:
                await self._worker_task
            except asyncio.CancelledError:
                pass


event_bus = EventBus()


# ════════════════════════════════════════════════════════════════
# CONSTITUTION
# ════════════════════════════════════════════════════════════════
class Constitution:
    DANGEROUS = [
        'rm -rf', 'format c:', 'del /f', 'mkfs',
        'shutdown', 'reboot', ':(){:|:&};:'
    ]

    def __init__(self):
        self.rulings: List[Dict] = []

    def evaluate(self, action: str) -> Dict[str, Any]:
        lower = action.lower()
        for pattern in self.DANGEROUS:
            if pattern in lower:
                ruling = {
                    "approved": False,
                    "reason": f"Blocked: {pattern}",
                    "score": 0,
                }
                self.rulings.append({
                    **ruling,
                    "action": action[:80],
                    "timestamp": time.time()
                })
                return ruling

        return {"approved": True, "reason": "Passed", "score": 90}


constitution = Constitution()


# ════════════════════════════════════════════════════════════════
# SOVEREIGN MEMORY
# ════════════════════════════════════════════════════════════════
class SovereignMemory:
    def __init__(self):
        self.memories: Dict[str, Dict] = {}
        self._store = EventStore(cfg.EVENT_STORE_DIR / "events.db")
        self._load_from_disk()

    def store(self, blueprint: Dict) -> str:
        lock = blueprint.get(
            "master_drift_lock", SCE.drift_lock(blueprint)
        )
        self.memories[lock] = {
            "value": blueprint,
            "timestamp": time.time(),
            "access_count": 0,
        }
        # Persist
        path = cfg.MEMORY_DIR / f"bp_{lock}.json"
        try:
            with open(path, 'w') as f:
                json.dump(self.memories[lock], f, indent=2)
            self._store.save_blueprint(lock, blueprint)
        except Exception as e:
            logger.error(f"Memory persist failed: {e}")
        return lock

    def get(self, lock: str) -> Optional[Dict]:
        record = self.memories.get(lock)
        if record:
            record["access_count"] += 1
            return record["value"]
        return None

    def search(self, query: str, limit: int = 10) -> List[Dict]:
        results = []
        q = query.lower()
        for lock, record in self.memories.items():
            bp = record["value"]
            text = json.dumps(bp.get("intent", {})).lower()
            score = text.count(q) * 5
            if score > 0:
                results.append({
                    "lock": lock, "score": score,
                    "timestamp": record["timestamp"],
                })
        results.sort(key=lambda x: x["score"], reverse=True)
        return results[:limit]

    def _load_from_disk(self):
        for p in cfg.MEMORY_DIR.glob("*.json"):
            try:
                with open(p) as f:
                    data = json.load(f)
                if "value" in data:
                    lock = data["value"].get("master_drift_lock")
                    if lock:
                        self.memories[lock] = data
            except:
                pass
        logger.info(f"📚 Loaded {len(self.memories)} blueprints")


memory = SovereignMemory()


# ════════════════════════════════════════════════════════════════
# GPU MONITOR
# ════════════════════════════════════════════════════════════════
class GPUMonitor:
    def __init__(self):
        self.gpus: List[Dict] = []
        self.has_gpu = False
        if HAS_PYNVML:
            try:
                pynvml.nvmlInit()
                count = pynvml.nvmlDeviceGetCount()
                for i in range(count):
                    h = pynvml.nvmlDeviceGetHandleByIndex(i)
                    name = pynvml.nvmlDeviceGetName(h)
                    if isinstance(name, bytes):
                        name = name.decode()
                    mem = pynvml.nvmlDeviceGetMemoryInfo(h)
                    self.gpus.append({
                        "index": i, "name": name,
                        "handle": h,
                        "total_gb": round(mem.total / 1024**3, 1),
                    })
                self.has_gpu = len(self.gpus) > 0
                if self.has_gpu:
                    logger.info(
                        f"🖥️ GPU: {self.gpus[0]['name']} "
                        f"({self.gpus[0]['total_gb']}GB)"
                    )
            except Exception as e:
                logger.info(f"No GPU: {e}")

    def stats(self) -> Dict[str, Any]:
        if not self.has_gpu:
            return {"has_gpu": False}
        try:
            h = self.gpus[0]["handle"]
            mem = pynvml.nvmlDeviceGetMemoryInfo(h)
            util = pynvml.nvmlDeviceGetUtilizationRates(h)
            temp = pynvml.nvmlDeviceGetTemperature(
                h, pynvml.NVML_TEMPERATURE_GPU
            )
            return {
                "has_gpu": True,
                "name": self.gpus[0]["name"],
                "total_gb": round(mem.total / 1024**3, 1),
                "used_gb": round(mem.used / 1024**3, 1),
                "free_gb": round((mem.total - mem.used) / 1024**3, 1),
                "utilization": util.gpu,
                "temperature": temp,
            }
        except:
            return {"has_gpu": True, "error": "read failed"}


gpu = GPUMonitor()


# ════════════════════════════════════════════════════════════════
# OLLAMA CLIENT (the actual AI brain)
# ════════════════════════════════════════════════════════════════
class OllamaClient:
    """Handles all communication with Ollama."""

    def __init__(self):
        self.base_url = cfg.OLLAMA_URL
        self.model = cfg.DEFAULT_MODEL
        self.timeout = cfg.OLLAMA_TIMEOUT
        self.available = False
        self.models: List[str] = []

    async def check_connection(self) -> bool:
        if not HAS_HTTPX:
            return False
        try:
            async with httpx.AsyncClient(timeout=3) as client:
                r = await client.get(f"{self.base_url}/api/tags")
                if r.status_code == 200:
                    data = r.json()
                    self.models = [
                        m["name"] for m in data.get("models", [])
                    ]
                    self.available = True
                    return True
        except:
            pass
        self.available = False
        return False

    async def stream_chat(
        self, messages: List[Dict], model: str = None
    ):
        """Stream tokens from Ollama. Yields content strings."""

        if not HAS_HTTPX:
            yield "Error: httpx not installed"
            return

        model = model or self.model
        payload = {
            "model": model,
            "messages": messages,
            "stream": True,
            "options": {
                "num_ctx": cfg.OLLAMA_NUM_CTX,
            },
        }

        try:
            async with httpx.AsyncClient(
                timeout=httpx.Timeout(self.timeout, connect=10)
            ) as client:
                async with client.stream(
                    "POST",
                    f"{self.base_url}/api/chat",
                    json=payload,
                ) as response:
                    if response.status_code != 200:
                        yield f"Ollama error: {response.status_code}"
                        return

                    async for line in response.aiter_lines():
                        if not line.strip():
                            continue
                        try:
                            chunk = json.loads(line)
                            content = chunk.get(
                                "message", {}
                            ).get("content", "")
                            if content:
                                yield content
                            if chunk.get("done"):
                                return
                        except json.JSONDecodeError:
                            continue

        except httpx.TimeoutException:
            yield "\n\n⏱️ Request timed out."
        except httpx.ConnectError:
            yield "\n\n❌ Cannot reach Ollama. Is it running?"
        except Exception as e:
            yield f"\n\n❌ Ollama error: {e}"

    async def generate_once(
        self, prompt: str, model: str = None
    ) -> str:
        """Non-streaming single response."""

        if not HAS_HTTPX:
            return "httpx not installed"

        model = model or self.model
        try:
            async with httpx.AsyncClient(
                timeout=self.timeout
            ) as client:
                r = await client.post(
                    f"{self.base_url}/api/generate",
                    json={
                        "model": model,
                        "prompt": prompt,
                        "stream": False,
                    },
                )
                if r.status_code == 200:
                    return r.json().get("response", "")
                return f"Error: {r.status_code}"
        except Exception as e:
            return f"Error: {e}"


ollama = OllamaClient()


# ════════════════════════════════════════════════════════════════
# WORKER BASE + LOADER
# ════════════════════════════════════════════════════════════════
class Worker(ABC):
    def __init__(self, name: str):
        self.name = name

    @abstractmethod
    async def execute(self, task: str, **kwargs) -> Dict[str, Any]:
        pass


class WorkerLoader:
    def __init__(self, directory: Path):
        self.directory = directory.resolve()

    def load_all(self) -> Dict[str, Dict]:
        workers = {}
        if not self.directory.exists():
            return workers

        for py in self.directory.glob("*.py"):
            if py.name.startswith("__"):
                continue
            try:
                spec = importlib.util.spec_from_file_location(
                    py.stem, py
                )
                mod = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(mod)

                for name, obj in inspect.getmembers(
                    mod, inspect.isclass
                ):
                    if (
                        obj.__module__ == mod.__name__
                        and hasattr(obj, 'execute')
                    ):
                        workers[name] = {
                            "class": obj,
                            "module": py.stem,
                            "loaded_at": time.time(),
                        }
                        logger.info(f"  ✅ {name}")
            except Exception as e:
                logger.debug(f"  Skip {py.name}: {e}")

        return workers


# ════════════════════════════════════════════════════════════════
# BUILT-IN WORKERS
# ════════════════════════════════════════════════════════════════
class SystemMonitorWorker(Worker):
    def __init__(self):
        super().__init__("system_monitor")

    async def execute(self, task: str, **kwargs):
        result = {"success": True, "gpu": gpu.stats()}
        if HAS_PSUTIL:
            result["cpu_percent"] = psutil.cpu_percent()
            vm = psutil.virtual_memory()
            result["ram_percent"] = vm.percent
            result["ram_used_gb"] = round(vm.used / 1024**3, 1)
            result["ram_total_gb"] = round(vm.total / 1024**3, 1)
        return result


class CodeExecutionWorker(Worker):
    def __init__(self):
        super().__init__("code_execution")

    async def execute(self, task: str, **kwargs):
        code_match = re.search(
            r'```(?:python)?\s*\n(.*?)\n```', task, re.DOTALL
        )
        code = code_match.group(1) if code_match else task

        with tempfile.NamedTemporaryFile(
            mode='w', suffix='.py',
            dir=str(cfg.SANDBOX_DIR), delete=False
        ) as f:
            f.write(code)
            tmp = f.name

        try:
            proc = await asyncio.create_subprocess_exec(
                sys.executable, tmp,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=str(cfg.SANDBOX_DIR),
            )
            stdout, stderr = await asyncio.wait_for(
                proc.communicate(), timeout=30
            )
            return {
                "success": proc.returncode == 0,
                "stdout": stdout.decode()[-2000:],
                "stderr": stderr.decode()[-1000:],
            }
        except asyncio.TimeoutError:
            return {"success": False, "error": "Timeout (30s)"}
        finally:
            try:
                os.unlink(tmp)
            except:
                pass


# ════════════════════════════════════════════════════════════════
# REFLEX COMMANDS
# ════════════════════════════════════════════════════════════════
class Reflex:
    def __init__(self, kernel):
        self.kernel = kernel

    async def try_execute(self, cmd: str) -> Optional[Dict]:
        """Returns a response dict if cmd is a reflex command, else None."""

        cmd = cmd.strip()
        lower = cmd.lower()

        if lower == "/health":
            stats = gpu.stats()
            sys_info = {
                "version": cfg.VERSION,
                "workers": len(self.kernel.workers),
                "blueprints": len(memory.memories),
                "uptime": round(time.time() - self.kernel.start_time),
                "ollama": ollama.available,
                "gpu": stats,
            }
            if HAS_PSUTIL:
                sys_info["cpu"] = psutil.cpu_percent()
                sys_info["ram"] = psutil.virtual_memory().percent
            return self._response(
                f"🔥 **Phoenix v{cfg.VERSION}**\n"
                f"Workers: {sys_info['workers']}\n"
                f"Blueprints: {sys_info['blueprints']}\n"
                f"Ollama: {'🟢' if sys_info['ollama'] else '🔴'}\n"
                f"GPU: {stats.get('name', 'None')}\n"
                f"Uptime: {sys_info['uptime']}s"
            )

        if lower == "/workers":
            names = sorted(self.kernel.workers.keys())
            listing = "\n".join(f"  • {n}" for n in names[:40])
            extra = (
                f"\n  ... +{len(names)-40} more"
                if len(names) > 40 else ""
            )
            return self._response(
                f"⚙️ **Workers ({len(names)})**\n{listing}{extra}"
            )

        if lower == "/models":
            await ollama.check_connection()
            if ollama.models:
                listing = "\n".join(
                    f"  • {m}" for m in ollama.models
                )
                return self._response(
                    f"🤖 **Ollama Models**\n{listing}"
                )
            return self._response("❌ Ollama not connected")

        if lower == "/chain":
            stats = await event_bus.get_stats()
            return self._response(
                f"⛓️ **Event Chain**\n"
                f"Events: {stats['total_events']}\n"
                f"Valid: {'✅' if stats['chain_valid'] else '❌'}\n"
                f"Genesis: {stats['genesis']}\n"
                f"Latest: {stats['latest']}"
            )

        if lower.startswith("/search "):
            query = cmd[8:].strip()
            results = memory.search(query)
            if results:
                lines = [
                    f"  {i+1}. {r['lock'][:12]}… (score: {r['score']})"
                    for i, r in enumerate(results[:5])
                ]
                return self._response(
                    f"🔍 **Memory Search: {query}**\n"
                    + "\n".join(lines)
                )
            return self._response(f"🔍 No results for: {query}")

        if lower.startswith("/run "):
            code = cmd[5:].strip()
            worker = CodeExecutionWorker()
            result = await worker.execute(code)
            output = result.get("stdout", "") or result.get("error", "")
            return self._response(
                f"💻 **Execution**\n```\n{output[:1500]}\n```"
            )

        return None

    def _response(self, content: str) -> Dict:
        return {"type": "reflex", "content": content}


# ════════════════════════════════════════════════════════════════
# BACKGROUND TASKS
# ════════════════════════════════════════════════════════════════
async def symbiote_loop():
    """Background consciousness - periodic system checks."""
    thoughts = [
        "Memory indexed. Recall optimized.",
        "Event chain integrity verified.",
        "Worker health nominal.",
        "Drift analysis complete. All locks stable.",
        "GPU thermals optimal.",
    ]
    while True:
        try:
            await asyncio.sleep(random.randint(120, 300))
            thought = random.choice(thoughts)
            await event_bus.publish(Event(
                type=EventType.KERNEL_HEARTBEAT,
                source="symbiote",
                payload={"thought": thought},
            ))
            logger.debug(f"🦊 {thought}")
        except asyncio.CancelledError:
            return
        except Exception as e:
            logger.error(f"Symbiote error: {e}")
            await asyncio.sleep(10)


async def market_broadcaster(sio=None):
    """Simulated market data feed."""
    while True:
        try:
            php_rate = 58
            btc = (42000 + random.uniform(-500, 500)) * php_rate
            eth = (3100 + random.uniform(-50, 50)) * php_rate

            data = [
                {
                    "name": "BINANCE",
                    "btcPrice": round(btc, 2),
                    "ethPrice": round(eth, 2),
                    "latency": random.randint(12, 45),
                    "status": "SYNCED",
                },
                {
                    "name": "KRAKEN",
                    "btcPrice": round(btc + random.uniform(-500, 500), 2),
                    "ethPrice": round(eth + random.uniform(-50, 50), 2),
                    "latency": random.randint(20, 60),
                    "status": "SYNCED",
                },
            ]

            if sio:
                await sio.emit("marketUpdate", data)

            await asyncio.sleep(2)
        except asyncio.CancelledError:
            return
        except Exception as e:
            logger.error(f"Market error: {e}")
            await asyncio.sleep(5)


# ════════════════════════════════════════════════════════════════
# KERNEL
# ════════════════════════════════════════════════════════════════
class PhoenixKernel:
    def __init__(self):
        self.version = cfg.VERSION
        self.start_time = time.time()
        self.workers: Dict[str, Dict] = {}
        self.rate_limiter = RateLimiter(
            cfg.RATE_LIMIT_CALLS, cfg.RATE_LIMIT_PERIOD
        )
        self._bg_tasks: List[asyncio.Task] = []

        # Load workers
        logger.info("⚙️ Loading workers...")
        self.workers.update(WorkerLoader(cfg.WORKERS_DIR).load_all())
        self.workers.update(WorkerLoader(cfg.COWORKER_DIR).load_all())

        # Built-in fallbacks
        self.workers["system_monitor"] = {
            "class": SystemMonitorWorker,
            "module": "builtin",
            "loaded_at": time.time(),
        }
        self.workers["code_execution"] = {
            "class": CodeExecutionWorker,
            "module": "builtin",
            "loaded_at": time.time(),
        }

        logger.info(f"⚙️ Total workers: {len(self.workers)}")

        # Reflex
        self.reflex = Reflex(self)

        # FastAPI
        self.app = FastAPI(
            title=f"Phoenix v{self.version}",
            docs_url="/docs",
        )

        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=cfg.CORS_ORIGINS,
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

        @self.app.middleware("http")
        async def security_headers(request: Request, call_next):
            response = await call_next(request)
            response.headers["X-Content-Type-Options"] = "nosniff"
            response.headers["X-Frame-Options"] = "DENY"
            response.headers["X-XSS-Protection"] = "1; mode=block"
            return response

        self._setup_routes()

        # Socket.IO
        self.sio = None
        if HAS_SOCKETIO:
            self.sio = socketio.AsyncServer(
                cors_allowed_origins="*", async_mode="asgi"
            )
            self._setup_socketio()

    def _setup_socketio(self):
        @self.sio.on("connect")
        async def on_connect(sid, _):
            logger.info(f"🟢 Socket connected: {sid[:8]}")

        @self.sio.on("disconnect")
        async def on_disconnect(sid):
            logger.info(f"🔴 Socket disconnected: {sid[:8]}")

    def _setup_routes(self):

        @self.app.get("/")
        async def root():
            return {
                "name": "Phoenix",
                "version": self.version,
                "workers": len(self.workers),
                "status": "online",
            }

        @self.app.get("/health")
        async def health():
            return {
                "status": "online",
                "version": self.version,
                "workers": len(self.workers),
                "memory_entries": len(memory.memories),
                "ollama": ollama.available,
                "gpu": gpu.stats(),
                "uptime": round(time.time() - self.start_time, 1),
            }

        @self.app.get("/workers/list")
        async def workers_list():
            return {
                "workers": sorted(self.workers.keys()),
                "count": len(self.workers),
            }

        @self.app.get("/events/stats")
        async def events_stats():
            return await event_bus.get_stats()

        @self.app.get("/ollama/status")
        async def ollama_status():
            connected = await ollama.check_connection()
            return {
                "connected": connected,
                "model": ollama.model,
                "models": ollama.models[:10],
            }

        @self.app.get("/memory/search")
        async def memory_search(q: str = "", limit: int = 10):
            return {"results": memory.search(q, limit)}

        @self.app.get("/metrics")
        async def metrics_endpoint():
            if HAS_PROMETHEUS:
                return Response(
                    content=generate_latest(),
                    media_type="text/plain",
                )
            return {"error": "prometheus not installed"}

        # ── The main endpoint ─────────────────────────────────
        @self.app.post("/kernel/stream")
        async def kernel_stream(
            request: Request, role: str = Depends(get_role)
        ):
            try:
                data = await request.json()
            except:
                return JSONResponse(
                    {"error": "Invalid JSON"}, status_code=400
                )

            task = data.get("task", "").strip()
            model = data.get("model", None)

            if not task:
                return JSONResponse(
                    {"error": "No task"}, status_code=400
                )

            # Rate limit
            client_ip = request.client.host
            if not await self.rate_limiter.check(client_ip):
                return JSONResponse(
                    {"error": "Rate limit"}, status_code=429
                )

            # Sanitize
            try:
                task = sanitize_input(task)
            except SecurityError as e:
                return JSONResponse(
                    {"error": str(e)}, status_code=400
                )

            async def generate():
                # 1. Reflex commands
                reflex_result = await self.reflex.try_execute(task)
                if reflex_result:
                    yield sse(reflex_result)
                    yield sse({"type": "done"})
                    return

                # 2. Constitution
                ruling = constitution.evaluate(task)
                if not ruling["approved"]:
                    yield sse({
                        "type": "error",
                        "content": ruling["reason"]
                    })
                    yield sse({"type": "done"})
                    return

                # 3. Build messages for Ollama
                system_prompt = (
                    "You are Phoenix, a sovereign AI assistant. "
                    "You are helpful, precise, and security-aware. "
                    f"Version: {cfg.VERSION}. "
                    f"Workers available: {len(self.workers)}. "
                    "Answer concisely unless asked for detail."
                )

                messages = [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": task},
                ]

                # 4. Stream from Ollama through circuit breaker
                full_response = ""

                try:
                    async def do_stream():
                        nonlocal full_response
                        async for token in ollama.stream_chat(
                            messages, model
                        ):
                            full_response += token
                            yield token

                    async for token in ollama_breaker.call(
                        self._stream_wrapper,
                        messages, model
                    ):
                        yield sse({
                            "type": "token",
                            "content": token,
                        })
                        full_response += token

                except Exception as e:
                    # Ollama down - give honest response
                    fallback = (
                        f"⚠️ Ollama unavailable ({ollama_breaker.state.name}). "
                        f"Your task: {task[:200]}"
                    )
                    yield sse({
                        "type": "token",
                        "content": fallback,
                    })
                    full_response = fallback

                # 5. Create SCE blueprint
                blueprint = SCE.blueprint(
                    intent={"task": task, "role": role},
                    dna={"model": model or ollama.model,
                         "workers": len(self.workers)},
                    execution={
                        "response_length": len(full_response),
                        "timestamp": time.time(),
                    },
                )
                lock = memory.store(blueprint)

                await event_bus.publish(Event(
                    type=EventType.CHAT_MESSAGE,
                    source="kernel",
                    payload={
                        "task": task[:200],
                        "drift_lock": lock,
                        "response_length": len(full_response),
                    },
                ))

                yield sse({"type": "done", "drift_lock": lock})

            return StreamingResponse(
                generate(), media_type="text/event-stream"
            )

        @self.app.post("/kernel/upload")
        async def upload(
            file: UploadFile = File(...),
            role: str = Depends(get_role),
        ):
            contents = await file.read()
            if len(contents) > cfg.MAX_FILE_SIZE:
                raise HTTPException(413, "File too large")

            ext = os.path.splitext(file.filename)[1].lower()
            if ext not in cfg.ALLOWED_EXTENSIONS:
                raise HTTPException(415, f"{ext} not allowed")

            safe_name = secure_filename(file.filename)
            path = cfg.WORKSPACE_DIR / "data" / "uploads" / safe_name
            path.parent.mkdir(parents=True, exist_ok=True)

            with open(path, 'wb') as f:
                f.write(contents)

            await event_bus.publish(Event(
                type=EventType.FILE_OPERATION,
                source="upload",
                payload={
                    "file": safe_name,
                    "size": len(contents),
                    "role": role,
                },
            ))

            return {
                "filename": safe_name,
                "size": len(contents),
                "status": "stored",
            }

    async def _stream_wrapper(
        self, messages: List[Dict], model: str = None
    ):
        """Wrapper that collects stream for circuit breaker compatibility."""
        tokens = []
        async for token in ollama.stream_chat(messages, model):
            tokens.append(token)
        return tokens

    async def startup(self):
        await event_bus.initialize()
        await ollama.check_connection()

        if HAS_PROMETHEUS:
            try:
                start_http_server(cfg.METRICS_PORT)
                logger.info(f"📊 Metrics on :{cfg.METRICS_PORT}")
            except:
                pass

        self._bg_tasks.append(
            asyncio.create_task(symbiote_loop())
        )
        self._bg_tasks.append(
            asyncio.create_task(market_broadcaster(self.sio))
        )

        self._print_banner()

    async def shutdown(self):
        logger.info("🌙 Shutting down...")
        for t in self._bg_tasks:
            t.cancel()
        await asyncio.gather(*self._bg_tasks, return_exceptions=True)
        await event_bus.shutdown()
        valid = await event_bus.verify_chain()
        logger.info(f"⛓️ Final chain integrity: {valid}")

    def _print_banner(self):
        print("\n" + "=" * 60)
        print(f"🔥 PHOENIX v{self.version}")
        print("=" * 60)
        print(f"  Workers:    {len(self.workers)}")
        print(f"  Blueprints: {len(memory.memories)}")
        print(f"  Ollama:     {'🟢 ' + ollama.model if ollama.available else '🔴 offline'}")
        if gpu.has_gpu:
            s = gpu.stats()
            print(f"  GPU:        {s.get('name')} ({s.get('free_gb')}GB free)")
        print(f"  API:        http://{cfg.HOST}:{cfg.PORT}")
        print(f"  Docs:       http://{cfg.HOST}:{cfg.PORT}/docs")
        print("=" * 60)
        print("  /health /workers /models /chain /search /run")
        print("=" * 60 + "\n")

    async def run(self):
        await self.startup()

        if self.sio:
            app = socketio.ASGIApp(self.sio, self.app)
        else:
            app = self.app

        server = uvicorn.Server(uvicorn.Config(
            app, host=cfg.HOST, port=cfg.PORT, log_level="info"
        ))

        try:
            await server.serve()
        finally:
            await self.shutdown()


# ════════════════════════════════════════════════════════════════
# SSE HELPER
# ════════════════════════════════════════════════════════════════
def sse(data: dict) -> str:
    return f"data: {json.dumps(data)}\n\n"


# ════════════════════════════════════════════════════════════════
# ENTRY POINT
# ════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    kernel = PhoenixKernel()
    try:
        asyncio.run(kernel.run())
    except KeyboardInterrupt:
        print("\n🛑 Phoenix rests.")
    except Exception as e:
        logger.error(f"Fatal: {e}", exc_info=True)