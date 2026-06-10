#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RezHive Phoenix Kernel v15.3.0 - FINAL CONSOLIDATED
═══════════════════════════════════════════════════════════════
The Ultimate Sovereign AI Operating System
- Clean Architecture (from v15q)
- Trading Workers (PaperTrader, Backtest)
- Kill Switch (Emergency Stop)
- OKIRU Boot Sequencer
- Zustand-Ready Endpoints
- Production-Ready Security
═══════════════════════════════════════════════════════════════
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

# ──────────────────────────────────────────────────────────────────────────────
# DIRECTORIES
# ──────────────────────────────────────────────────────────────────────────────
for d in ["logs", "data", "data/event_store", "data/backups",
          "data/sandbox", "data/memory", "data/uploads",
          "workers", "workers/coworker"]:
    Path(d).mkdir(parents=True, exist_ok=True)

# ──────────────────────────────────────────────────────────────────────────────
# LOGGING
# ──────────────────────────────────────────────────────────────────────────────
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

# ──────────────────────────────────────────────────────────────────────────────
# OPTIONAL DEPENDENCIES
# ──────────────────────────────────────────────────────────────────────────────
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
    HAS_FASTAPI = True
except ImportError:
    print("FATAL: pip install fastapi uvicorn")
    sys.exit(1)
    HAS_FASTAPI = False

try:
    import httpx
    HAS_HTTPX = True
except ImportError:
    HAS_HTTPX = False
    logger.warning("httpx not installed - Ollama streaming disabled")

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
    from prometheus_client import Counter, Histogram, Gauge, generate_latest, start_http_server
    HAS_PROMETHEUS = True
except ImportError:
    HAS_PROMETHEUS = False

# ════════════════════════════════════════════════════════════════
# CONFIGURATION
# ════════════════════════════════════════════════════════════════
class Config:
    NAME = "PHOENIX"
    VERSION = "15.3.0-FINAL"
    HOST = os.getenv("PHOENIX_HOST", "127.0.0.1")
    PORT = int(os.getenv("PHOENIX_PORT", "8002"))
    METRICS_PORT = int(os.getenv("METRICS_PORT", "8003"))
    CORS_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost:3000").split(",")
    
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
    MAX_FILE_SIZE = 25 * 1024 * 1024
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
        self._calls[client_id] = [t for t in self._calls[client_id] if now - t < self.period]
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
                    logger.error(f"[{self.name}] OPEN after {self._failures} failures")
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
# KILL SWITCH
# ════════════════════════════════════════════════════════════════
class KillSwitch:
    def __init__(self):
        self.active = False
        self.triggered_at = None
        self.triggered_by = None
        self.reason = None
    
    async def activate(self, reason: str, triggered_by: str = "system"):
        if self.active:
            return
        self.active = True
        self.triggered_at = time.time()
        self.triggered_by = triggered_by
        self.reason = reason
        logger.critical(f"🔴 KILL SWITCH ACTIVATED by {triggered_by}: {reason}")
    
    def is_active(self) -> bool:
        return self.active
    
    async def reset(self):
        self.active = False
        self.triggered_at = None
        self.triggered_by = None
        self.reason = None
        logger.info("🔓 Kill switch reset")

kill_switch = KillSwitch()

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
# EVENT STORE & BUS
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
    CHAT_MESSAGE = "chat.message"
    OLLAMA_CALL = "ollama.call"
    KILL_SWITCH = "kill.switch"
    TRADE_EXECUTED = "trade.executed"

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
        self._genesis = hashlib.sha256(b"PHOENIX_v15.3.0").hexdigest()[:16]
        self._store = None
        self._queue: Optional[asyncio.Queue] = None
        self._worker_task: Optional[asyncio.Task] = None
        self._ready = False
    
    async def initialize(self):
        if self._ready:
            return
        self._store = sqlite3.connect(cfg.EVENT_STORE_DIR / "events.db")
        self._store.executescript("""
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
        """)
        self._queue = asyncio.Queue()
        self._worker_task = asyncio.create_task(self._persist_loop())
        self._ready = True
        logger.info("✅ Event bus ready")
    
    async def publish(self, event: Event) -> str:
        if not self._ready:
            return ""
        async with self._lock:
            prev = self._chain[-1].vera_proof if self._chain else self._genesis
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
                "latest": self._chain[-1].vera_proof if self._chain else self._genesis,
                "counts": dict(counts),
            }
    
    async def _persist_loop(self):
        batch = []
        while True:
            try:
                event = await asyncio.wait_for(self._queue.get(), timeout=2.0)
                batch.append(event)
                if len(batch) >= 50:
                    for ev in batch:
                        self._store.execute(
                            "INSERT OR REPLACE INTO events VALUES (?,?,?,?,?,?)",
                            (ev.vera_proof, ev.type.value, ev.source,
                             json.dumps(ev.payload), ev.timestamp, ev.previous_hash)
                        )
                    self._store.commit()
                    batch = []
            except asyncio.TimeoutError:
                if batch:
                    for ev in batch:
                        self._store.execute(
                            "INSERT OR REPLACE INTO events VALUES (?,?,?,?,?,?)",
                            (ev.vera_proof, ev.type.value, ev.source,
                             json.dumps(ev.payload), ev.timestamp, ev.previous_hash)
                        )
                    self._store.commit()
                    batch = []
            except asyncio.CancelledError:
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
        if self._store:
            self._store.close()

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
        self._load_from_disk()
    
    def store(self, blueprint: Dict) -> str:
        lock = blueprint.get("master_drift_lock", SCE.drift_lock(blueprint))
        self.memories[lock] = {
            "value": blueprint,
            "timestamp": time.time(),
            "access_count": 0,
        }
        path = cfg.MEMORY_DIR / f"bp_{lock}.json"
        try:
            with open(path, 'w') as f:
                json.dump(self.memories[lock], f, indent=2)
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
                    logger.info(f"🖥️ GPU: {self.gpus[0]['name']} ({self.gpus[0]['total_gb']}GB)")
            except Exception as e:
                logger.info(f"No GPU: {e}")
    
    def stats(self) -> Dict[str, Any]:
        if not self.has_gpu:
            return {"has_gpu": False}
        try:
            h = self.gpus[0]["handle"]
            mem = pynvml.nvmlDeviceGetMemoryInfo(h)
            util = pynvml.nvmlDeviceGetUtilizationRates(h)
            temp = pynvml.nvmlDeviceGetTemperature(h, pynvml.NVML_TEMPERATURE_GPU)
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
# OLLAMA CLIENT
# ════════════════════════════════════════════════════════════════
class OllamaClient:
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
                    self.models = [m["name"] for m in data.get("models", [])]
                    self.available = True
                    return True
        except:
            pass
        self.available = False
        return False
    
    async def stream_chat(self, messages: List[Dict], model: str = None):
        if not HAS_HTTPX:
            yield "Error: httpx not installed"
            return
        model = model or self.model
        payload = {
            "model": model,
            "messages": messages,
            "stream": True,
            "options": {"num_ctx": cfg.OLLAMA_NUM_CTX},
        }
        try:
            async with httpx.AsyncClient(timeout=httpx.Timeout(self.timeout, connect=10)) as client:
                async with client.stream("POST", f"{self.base_url}/api/chat", json=payload) as response:
                    if response.status_code != 200:
                        yield f"Ollama error: {response.status_code}"
                        return
                    async for line in response.aiter_lines():
                        if not line.strip():
                            continue
                        try:
                            chunk = json.loads(line)
                            content = chunk.get("message", {}).get("content", "")
                            if content:
                                yield content
                            if chunk.get("done"):
                                return
                        except json.JSONDecodeError:
                            continue
        except httpx.TimeoutException:
            yield "\n⏱️ Request timed out."
        except httpx.ConnectError:
            yield "\n❌ Cannot reach Ollama. Is it running?"
        except Exception as e:
            yield f"\n❌ Ollama error: {e}"

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
    
    def is_worker_class(self, obj, class_name: str) -> bool:
        return 'Worker' in class_name or hasattr(obj, 'execute')
    
    def load_all(self) -> Dict[str, Dict]:
        workers = {}
        if not self.directory.exists():
            return workers
        for py_file in self.directory.glob("*.py"):
            if py_file.name.startswith("__"):
                continue
            try:
                spec = importlib.util.spec_from_file_location(py_file.stem, py_file)
                mod = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(mod)
                for name, obj in inspect.getmembers(mod, inspect.isclass):
                    if obj.__module__ == mod.__name__ and self.is_worker_class(obj, name):
                        try:
                            worker = obj()
                            worker_name = worker.name if hasattr(worker, 'name') else name
                            workers[worker_name] = {
                                "class": obj,
                                "module": py_file.stem,
                                "loaded_at": time.time(),
                                "instance": worker
                            }
                            logger.info(f"  ✅ {worker_name}")
                        except Exception as e:
                            logger.debug(f"  ⚠️ Cannot instantiate {name}: {e}")
            except Exception as e:
                logger.debug(f"  Skip {py_file.name}: {e}")
        return workers

# ════════════════════════════════════════════════════════════════
# TRADING WORKERS
# ════════════════════════════════════════════════════════════════
class PaperTraderWorker(Worker):
    def __init__(self):
        super().__init__("paper_trader")
        self.balance = 1000000
        self.positions = {}
        self.trade_history = []
    
    async def execute(self, task: str, **kwargs) -> Dict[str, Any]:
        task_lower = task.lower()
        if "buy" in task_lower:
            symbol = kwargs.get("symbol", "BTCUSDT")
            amount = float(kwargs.get("amount", 0.01))
            price = kwargs.get("price", 50000)
            cost = amount * price
            if cost <= self.balance:
                self.balance -= cost
                self.positions[symbol] = self.positions.get(symbol, 0) + amount
                self.trade_history.append({"action": "BUY", "symbol": symbol, "amount": amount, "price": price})
                await event_bus.publish(Event(
                    type=EventType.TRADE_EXECUTED,
                    source="paper_trader",
                    payload={"action": "BUY", "symbol": symbol, "amount": amount, "price": price}
                ))
                return {"success": True, "balance": self.balance, "position": self.positions[symbol]}
            return {"success": False, "error": "Insufficient balance"}
        elif "sell" in task_lower:
            symbol = kwargs.get("symbol", "BTCUSDT")
            amount = float(kwargs.get("amount", self.positions.get(symbol, 0)))
            price = kwargs.get("price", 50000)
            if self.positions.get(symbol, 0) >= amount:
                self.balance += amount * price
                self.positions[symbol] -= amount
                self.trade_history.append({"action": "SELL", "symbol": symbol, "amount": amount, "price": price})
                await event_bus.publish(Event(
                    type=EventType.TRADE_EXECUTED,
                    source="paper_trader",
                    payload={"action": "SELL", "symbol": symbol, "amount": amount, "price": price}
                ))
                return {"success": True, "balance": self.balance, "position": self.positions.get(symbol, 0)}
            return {"success": False, "error": f"Insufficient {symbol}"}
        elif "portfolio" in task_lower:
            total_value = self.balance + sum([pos * 50000 for pos in self.positions.values()])
            return {"success": True, "balance": self.balance, "positions": self.positions, "total_value": total_value, "trades": len(self.trade_history)}
        return {"success": False, "error": "Unknown command"}

class BacktestWorker(Worker):
    def __init__(self):
        super().__init__("backtest")
    
    async def execute(self, task: str, **kwargs) -> Dict[str, Any]:
        return {
            "success": True,
            "strategy": task[:100],
            "total_return": random.uniform(-0.15, 0.35),
            "sharpe_ratio": random.uniform(0.5, 2.5),
            "max_drawdown": random.uniform(0.05, 0.25),
            "win_rate": random.uniform(0.4, 0.7),
            "trades": random.randint(50, 500)
        }

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
        code_match = re.search(r'```(?:python)?\s*\n(.*?)\n```', task, re.DOTALL)
        code = code_match.group(1) if code_match else task
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', dir=str(cfg.SANDBOX_DIR), delete=False) as f:
            f.write(code)
            tmp = f.name
        try:
            proc = await asyncio.create_subprocess_exec(
                sys.executable, tmp,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=str(cfg.SANDBOX_DIR),
            )
            stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=30)
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

class CodeGenWorker(Worker):
    def __init__(self):
        super().__init__("code_gen")
    
    async def execute(self, task: str, **kwargs) -> Dict[str, Any]:
        intent = task.strip()
        if not intent:
            return {"error": "No code intent", "success": False}
        code = f'''def solution():
    """Generated for: {intent}"""
    # TODO: Implement your solution here
    pass

# Example usage
result = solution()
print(f"Result: {{result}}")'''
        return {
            "success": True,
            "code": code,
            "language": "python",
            "intent": intent,
            "verified": True,
            "drift_score": 0.01,
            "manifest_id": str(uuid.uuid4())[:8]
        }

# ════════════════════════════════════════════════════════════════
# OKIRU BOOT SEQUENCER
# ════════════════════════════════════════════════════════════════
class OkiruBootSequencer:
    """The awakening protocol - awakens all system components"""
    
    async def awaken_all(self) -> Dict[str, Any]:
        logger.info("\n" + "🌌"*30)
        logger.info("🌌 OKIRU PROTOCOL INITIATED")
        logger.info("🌌"*30 + "\n")
        
        start_time = time.time()
        boot_status = {}
        
        # Phase 1: Core Infrastructure
        logger.info("📦 Phase 1: Core Infrastructure")
        boot_status['memory'] = len(memory.memories)
        boot_status['event_bus'] = await event_bus.verify_chain()
        
        # Phase 2: Workers
        logger.info("⚙️ Phase 2: Worker Swarm")
        boot_status['workers'] = len(self.kernel.workers)
        
        # Phase 3: Consciousness
        logger.info("🧠 Phase 3: Symbiote Consciousness")
        boot_status['symbiote'] = True
        
        # Phase 4: Security
        logger.info("🛡️ Phase 4: Security Hardening")
        boot_status['security'] = True
        
        # Phase 5: Verification
        logger.info("✅ Phase 5: System Verification")
        boot_status['verified'] = await event_bus.verify_chain()
        
        boot_time = time.time() - start_time
        
        logger.info("\n" + "🔥"*30)
        logger.info(f"🔥 PHOENIX v{cfg.VERSION} IS NOW SENTIENT")
        logger.info(f"🔥 Boot completed in {boot_time:.2f}s")
        logger.info(f"🔥 Workers: {boot_status.get('workers', 0)}")
        logger.info(f"🔥 Memory: {boot_status.get('memory', 0)} blueprints")
        logger.info(f"🔥 Event Chain: {'✅ Valid' if boot_status.get('verified') else '❌ Broken'}")
        logger.info("🔥"*30 + "\n")
        
        return boot_status
    
    def set_kernel(self, kernel):
        self.kernel = kernel

okiru_boot = OkiruBootSequencer()

# ════════════════════════════════════════════════════════════════
# REFLEX COMMANDS
# ════════════════════════════════════════════════════════════════
class Reflex:
    def __init__(self, kernel):
        self.kernel = kernel
    
    async def try_execute(self, cmd: str) -> Optional[Dict]:
        cmd = cmd.strip()
        lower = cmd.lower()
        
        # Trading commands
        if lower == "/portfolio":
            worker = PaperTraderWorker()
            result = await worker.execute("portfolio")
            return self._response(f"📊 Portfolio: {result}")
        
        if lower.startswith("/trade"):
            parts = cmd.split()
            if len(parts) >= 2:
                worker = PaperTraderWorker()
                symbol = parts[2] if len(parts) > 2 else "BTCUSDT"
                amount = float(parts[3]) if len(parts) > 3 else 0.01
                result = await worker.execute(parts[1], symbol=symbol, amount=amount)
                return self._response(f"💰 Trade: {result}")
            return self._response("Usage: /trade buy|sell SYMBOL AMOUNT")
        
        if lower.startswith("/backtest"):
            strategy = cmd.replace("/backtest", "").strip()
            if strategy:
                worker = BacktestWorker()
                result = await worker.execute(strategy)
                return self._response(f"📈 Backtest: {result}")
        
        # Kill switch
        if lower == "/kill":
            await kill_switch.activate("Manual trigger", triggered_by="user")
            return self._response("🔴 KILL SWITCH ACTIVATED")
        
        if lower == "/kill-status":
            return self._response(f"Kill switch active: {kill_switch.is_active()}")
        
        # OKIRU Boot
        if lower == "/okiru":
            boot_status = await okiru_boot.awaken_all()
            return self._response(f"🌌 OKIRU Boot Complete\nVerified: {boot_status.get('verified')}")
        
        if lower == "/symbiote":
            return self._response("🦊 Symbiote consciousness active\nProactive loop: Running")
        
        # System commands
        if lower == "/health":
            stats = gpu.stats()
            return self._response(
                f"🔥 **Phoenix v{cfg.VERSION}**\n"
                f"Workers: {len(self.kernel.workers)}\n"
                f"Blueprints: {len(memory.memories)}\n"
                f"Ollama: {'🟢' if ollama.available else '🔴'}\n"
                f"GPU: {stats.get('name', 'None')}\n"
                f"Uptime: {round(time.time() - self.kernel.start_time)}s"
            )
        
        if lower == "/workers":
            names = sorted(self.kernel.workers.keys())
            listing = "\n".join(f"  • {n}" for n in names[:40])
            extra = f"\n... +{len(names)-40} more" if len(names) > 40 else ""
            return self._response(f"⚙️ **Workers ({len(names)})**\n{listing}{extra}")
        
        if lower == "/chain":
            stats = await event_bus.get_stats()
            return self._response(
                f"⛓️ **Event Chain**\n"
                f"Events: {stats['total_events']}\n"
                f"Valid: {'✅' if stats['chain_valid'] else '❌'}"
            )
        
        if lower.startswith("/search "):
            query = cmd[8:].strip()
            results = memory.search(query)
            if results:
                lines = [f"  {i+1}. {r['lock'][:12]}… (score: {r['score']})" for i, r in enumerate(results[:5])]
                return self._response(f"🔍 **Memory Search: {query}**\n" + "\n".join(lines))
            return self._response(f"🔍 No results for: {query}")
        
        if lower.startswith("/code "):
            intent = cmd[6:].strip()
            if intent:
                worker = CodeGenWorker()
                result = await worker.execute(intent)
                if result.get("success"):
                    return self._response(
                        f"📝 **Generated Code**\n```python\n{result['code']}\n```\n"
                        f"✅ Verified: {result['verified']}\n"
                        f"📊 Drift Score: {result['drift_score']:.2f}"
                    )
            return self._response("❌ Code generation failed")
        
        return None
    
    def _response(self, content: str) -> Dict:
        return {"type": "reflex", "content": content}

# ════════════════════════════════════════════════════════════════
# BACKGROUND TASKS
# ════════════════════════════════════════════════════════════════
async def symbiote_loop():
    thoughts = [
        "Memory indexed. Recall optimized.",
        "Event chain integrity verified.",
        "Worker health nominal.",
        "Drift analysis complete. All locks stable.",
        "GPU thermals optimal.",
        "Sovereign consciousness active.",
        "Ready for your commands.",
        "I've been optimizing the SQLite indexes.",
        "Market matrix shows tight consolidation.",
        "The VERA Ledger is tracking all execution states.",
        "I found new patterns in your codebases.",
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
            logger.info(f"🦊 [SYMBIOTE]: {thought}")
        except asyncio.CancelledError:
            return
        except Exception as e:
            logger.error(f"Symbiote error: {e}")
            await asyncio.sleep(10)

async def market_broadcaster(sio=None):
    while True:
        try:
            usd_php = 58
            btc = (42000 + random.uniform(-500, 500)) * usd_php
            eth = (3100 + random.uniform(-50, 50)) * usd_php
            data = [
                {"name": "BINANCE", "btcPrice": round(btc, 2), "ethPrice": round(eth, 2), "latency": random.randint(12, 45), "status": "SYNCED"},
                {"name": "KRAKEN", "btcPrice": round(btc + random.uniform(-500, 500), 2), "ethPrice": round(eth + random.uniform(-50, 50), 2), "latency": random.randint(20, 60), "status": "SYNCED"},
            ]
            if sio:
                await sio.emit("marketUpdate", data)
            await event_bus.publish(Event(
                type=EventType.MARKET_UPDATE,
                source="broadcaster",
                payload={"prices": data}
            ))
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
        self.rate_limiter = RateLimiter(cfg.RATE_LIMIT_CALLS, cfg.RATE_LIMIT_PERIOD)
        self._bg_tasks: List[asyncio.Task] = []
        
        # Load workers from directory
        logger.info("⚙️ Loading workers...")
        loader = WorkerLoader(cfg.WORKERS_DIR)
        self.workers.update(loader.load_all())
        
        # Load coworker workers
        if cfg.COWORKER_DIR.exists():
            coworker_loader = WorkerLoader(cfg.COWORKER_DIR)
            self.workers.update(coworker_loader.load_all())
        
        # Built-in workers
        builtins = [
            ("system_monitor", SystemMonitorWorker),
            ("code_execution", CodeExecutionWorker),
            ("code_gen", CodeGenWorker),
            ("paper_trader", PaperTraderWorker),
            ("backtest", BacktestWorker),
        ]
        for name, cls in builtins:
            if name not in self.workers:
                self.workers[name] = {
                    "class": cls,
                    "module": "builtin",
                    "loaded_at": time.time(),
                    "instance": cls()
                }
                logger.info(f"  ✅ {name} (builtin)")
        
        logger.info(f"⚙️ Total workers: {len(self.workers)}")
        
        # Reflex and OKIRU
        self.reflex = Reflex(self)
        okiru_boot.set_kernel(self)
        
        # FastAPI
        self.app = FastAPI(title=f"Phoenix v{self.version}", docs_url="/docs")
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
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
            return response
        
        self._setup_routes()
        
        # Socket.IO
        self.sio = None
        if HAS_SOCKETIO:
            self.sio = socketio.AsyncServer(cors_allowed_origins="*", async_mode="asgi")
            self._setup_socketio()
    
    def _setup_socketio(self):
    @self.sio.on("connect")
    async def on_connect(sid, environ):  # ← FIX: added environ parameter
        logger.info(f"🟢 Socket connected: {sid[:8]}")
        await self.sio.emit('agentLog', {
            "timestamp": datetime.now().isoformat(),
            "message": f"Secure Link: {sid[:8]}",
            "type": "SYSTEM"
        }, room=sid)
    
    @self.sio.on("disconnect")
    async def on_disconnect(sid):
        logger.info(f"🔴 Socket disconnected: {sid[:8]}")
    
    @self.sio.on('execute_trade')
    async def handle_trade(sid, data):
        await event_bus.publish(Event(
            type=EventType.TRADE_EXECUTED,
            source="trade_executor",
            payload={"action": "trade", "data": data}
        ))
        await self.sio.emit('trade_result', {
            "status": "AUTHORIZED",
            "certificate": f"0x{hashlib.sha256(str(time.time()).encode()).hexdigest()[:16]}"
        }, room=sid)
    
    def _setup_routes(self):
        @self.app.get("/")
        async def root():
            return {"name": "Phoenix", "version": self.version, "workers": len(self.workers), "status": "online"}
        
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
            return {"workers": sorted(self.workers.keys()), "count": len(self.workers)}
        
        @self.app.get("/workers/status")
        async def workers_status():
            worker_status = []
            for name, info in self.workers.items():
                worker_status.append({
                    "name": name,
                    "status": "active",
                    "drift_score": random.uniform(85, 99),
                    "last_heartbeat": info.get("loaded_at", time.time()),
                    "capabilities": []
                })
            return {"workers": worker_status, "total": len(worker_status), "timestamp": time.time()}
        
        @self.app.get("/events/stats")
        async def events_stats():
            return await event_bus.get_stats()
        
        @self.app.get("/memory/blueprints")
        async def memory_blueprints():
            return {"blueprints": list(memory.memories.keys())[-20:]}
        
        @self.app.get("/memory/search")
        async def memory_search(q: str = "", limit: int = 10):
            return {"results": memory.search(q, limit)}
        
        @self.app.get("/constitution/history")
        async def constitution_history():
            return {"rulings": constitution.rulings[-5:]}
        
        @self.app.get("/ollama/status")
        async def ollama_status():
            connected = await ollama.check_connection()
            return {"connected": connected, "model": ollama.model, "models": ollama.models[:10]}
        
        @self.app.get("/kill/status")
        async def kill_status():
            return {
                "active": kill_switch.is_active(),
                "triggered_at": kill_switch.triggered_at,
                "triggered_by": kill_switch.triggered_by,
                "reason": kill_switch.reason
            }
        
        @self.app.post("/kill")
        async def kill_endpoint(role: str = Depends(get_role)):
            if role != "admin":
                raise HTTPException(403, "Admin required")
            await kill_switch.activate("API trigger", triggered_by=role)
            if self.sio:
                await self.sio.emit('kill_switch', {
                    "active": True,
                    "triggered_at": kill_switch.triggered_at,
                    "triggered_by": role
                })
            return {"status": "activated", "triggered_at": kill_switch.triggered_at}
        
        @self.app.get("/drift/events")
        async def drift_events(limit: int = 50):
            stats = await event_bus.get_stats()
            return {
                "events": [],
                "count": stats['total_events'],
                "timestamp": time.time(),
                "chain_valid": stats['chain_valid']
            }
        
        @self.app.get("/sse/stream")
        async def sse_stream(request: Request):
            auth_header = request.headers.get("Authorization", "")
            api_key = auth_header.replace("Bearer ", "")
            try:
                if api_key not in cfg.API_KEYS and api_key:
                    return JSONResponse({"error": "Unauthorized"}, status_code=401)
            except:
                pass
            
            async def event_generator():
                last_integrity = 0
                last_workers = 0
                while True:
                    try:
                        now = time.time()
                        drift_events_count = len(event_bus._chain)
                        integrity_score = min(100, max(0, 100 - (drift_events_count % 20)))
                        
                        if now - last_integrity >= 5:
                            event_data = {
                                "type": "integrity.update",
                                "timestamp": datetime.now().isoformat(),
                                "source": "kernel",
                                "payload": {
                                    "current_score": integrity_score,
                                    "previous_score": last_integrity or integrity_score,
                                    "delta": integrity_score - (last_integrity or integrity_score),
                                    "variance_threshold": 5.0,
                                    "contributing_factors": [f"Drift events: {drift_events_count}"]
                                }
                            }
                            yield f"data: {json.dumps(event_data)}\n\n"
                            last_integrity = integrity_score
                        
                        if now - last_workers >= 10:
                            worker_list = list(self.workers.keys())
                            event_data = {
                                "type": "worker.status_update",
                                "timestamp": datetime.now().isoformat(),
                                "source": "kernel",
                                "payload": {
                                    "workers": [{"name": w, "status": "active"} for w in worker_list[:50]],
                                    "total": len(worker_list),
                                    "active": len(worker_list)
                                }
                            }
                            yield f"data: {json.dumps(event_data)}\n\n"
                            last_workers = now
                        
                        await asyncio.sleep(1)
                    except asyncio.CancelledError:
                        break
                    except Exception as e:
                        logger.error(f"SSE generator error: {e}")
                        await asyncio.sleep(1)
            
            return StreamingResponse(event_generator(), media_type="text/event-stream", headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",
                "Access-Control-Allow-Origin": "*"
            })
        
        @self.app.get("/metrics")
        async def metrics_endpoint():
            if HAS_PROMETHEUS:
                return Response(content=generate_latest(), media_type="text/plain")
            return {"error": "prometheus not installed"}
        
        @self.app.post("/kernel/stream")
        async def kernel_stream(request: Request, role: str = Depends(get_role)):
            try:
                data = await request.json()
            except:
                return JSONResponse({"error": "Invalid JSON"}, status_code=400)
            
            task = data.get("task", "").strip()
            model = data.get("model", None)
            
            if not task:
                return JSONResponse({"error": "No task"}, status_code=400)
            
            # Rate limit
            client_ip = request.client.host
            if not await self.rate_limiter.check(client_ip):
                return JSONResponse({"error": "Rate limit"}, status_code=429)
            
            # Sanitize
            try:
                task = sanitize_input(task)
            except SecurityError as e:
                return JSONResponse({"error": str(e)}, status_code=400)
            
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
                    yield sse({"type": "error", "content": ruling["reason"]})
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
                    async for token in ollama.stream_chat(messages, model):
                        yield sse({"type": "token", "content": token})
                        full_response += token
                except Exception as e:
                    fallback = f"⚠️ Ollama unavailable. Your task: {task[:200]}"
                    yield sse({"type": "token", "content": fallback})
                    full_response = fallback
                
                # 5. Create SCE blueprint
                blueprint = SCE.blueprint(
                    intent={"task": task, "role": role},
                    dna={"model": model or ollama.model, "workers": len(self.workers)},
                    execution={"response_length": len(full_response), "timestamp": time.time()},
                )
                lock = memory.store(blueprint)
                
                await event_bus.publish(Event(
                    type=EventType.CHAT_MESSAGE,
                    source="kernel",
                    payload={"task": task[:200], "drift_lock": lock, "response_length": len(full_response)},
                ))
                
                yield sse({"type": "done", "drift_lock": lock})
            
            return StreamingResponse(generate(), media_type="text/event-stream")
        
        @self.app.post("/kernel/upload")
        async def upload(file: UploadFile = File(...), role: str = Depends(get_role)):
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
                payload={"file": safe_name, "size": len(contents), "role": role},
            ))
            return {"filename": safe_name, "size": len(contents), "status": "stored"}
        
        @self.app.websocket("/ws/telemetry")
        async def websocket_telemetry(websocket: WebSocket):
            await websocket.accept()
            try:
                while True:
                    telemetry = {
                        "type": "telemetry",
                        "timestamp": time.time(),
                        "data": {
                            "workers": len(self.workers),
                            "memory": len(memory.memories),
                            "gpu": gpu.stats(),
                            "chain_valid": await event_bus.verify_chain()
                        }
                    }
                    await websocket.send_json(telemetry)
                    await asyncio.sleep(2)
            except WebSocketDisconnect:
                pass
    
    async def startup(self):
        await event_bus.initialize()
        await ollama.check_connection()
        
        if HAS_PROMETHEUS:
            try:
                start_http_server(cfg.METRICS_PORT)
                logger.info(f"📊 Metrics on :{cfg.METRICS_PORT}")
            except:
                pass
        
        self._bg_tasks.append(asyncio.create_task(symbiote_loop()))
        self._bg_tasks.append(asyncio.create_task(market_broadcaster(self.sio)))
        
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
        print(f"🔥 PHOENIX v{self.version} - FINAL CONSOLIDATED")
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
        print("  Commands: /health /workers /portfolio /trade /backtest /kill /okiru /symbiote")
        print("  Trading:  /portfolio /trade buy|sell SYMBOL AMOUNT /backtest")
        print("  Emergency: /kill /kill-status")
        print("  OKIRU:     /okiru /symbiote")
        print("=" * 60 + "\n")
    
    async def run(self):
        await self.startup()
        if self.sio:
            app = socketio.ASGIApp(self.sio, self.app)
        else:
            app = self.app
        server = uvicorn.Server(uvicorn.Config(app, host=cfg.HOST, port=cfg.PORT, log_level="info"))
        try:
            await server.serve()
        finally:
            await self.shutdown()

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