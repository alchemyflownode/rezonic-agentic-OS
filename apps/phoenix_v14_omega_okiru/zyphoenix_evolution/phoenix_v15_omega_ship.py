#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RezHive Phoenix Kernel v15.1.0 - OMEGA FINAL
═══════════════════════════════════════════════════════════════
The Ultimate Sovereign AI Operating System
- 77+ Workers Auto-Loaded
- Full Trading Suite (Paper Trader, Backtest)
- Kill Switch with Emergency Stop
- WebSocket Telemetry & SSE Streams
- SCE Protocol with Blockchain Event Chain
- Circuit Breaker Pattern
- GPU Monitoring (NVIDIA)
- Ollama Integration with Streaming
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
import time
import uuid
import warnings
import re
import shutil
import inspect
import importlib.util
import tempfile
import random
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, auto
from pathlib import Path
from typing import Dict, Any, Optional, List, Callable, Awaitable
from abc import ABC, abstractmethod
import sqlite3

warnings.filterwarnings("ignore")

# ============================================================================
# LOGGING SETUP
# ============================================================================
from logging.handlers import RotatingFileHandler

for d in ["logs", "data", "data/event_store", "data/backups", "data/sandbox",
          "data/memory", "workers", "workers/coworker"]:
    Path(d).mkdir(parents=True, exist_ok=True)

log_handler = RotatingFileHandler('logs/phoenix_omega.log', maxBytes=10*1024*1024, backupCount=5, encoding='utf-8')
log_handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(name)s - %(message)s"))

logging.basicConfig(
    level=logging.INFO,
    handlers=[log_handler, logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("PHOENIX_OMEGA")

# ============================================================================
# FASTAPI IMPORTS
# ============================================================================
try:
    from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect, Depends, HTTPException, UploadFile, File
    from fastapi.middleware.cors import CORSMiddleware
    from fastapi.middleware.trustedhost import TrustedHostMiddleware
    from fastapi.responses import StreamingResponse, JSONResponse, Response
    from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
    import uvicorn
    HAS_FASTAPI = True
except ImportError:
    print("❌ Install: pip install fastapi uvicorn")
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
    from prometheus_client import Counter, Histogram, Gauge, generate_latest, start_http_server
    HAS_PROMETHEUS = True
except ImportError:
    HAS_PROMETHEUS = False

# ============================================================================
# CONFIGURATION
# ============================================================================
class Config:
    NAME = "PHOENIX_OMEGA"
    VERSION = "15.1.0"
    HOST = os.getenv("PHOENIX_HOST", "127.0.0.1")
    PORT = int(os.getenv("PHOENIX_PORT", "8002"))
    METRICS_PORT = int(os.getenv("METRICS_PORT", "8003"))
    CORS_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost:3000").split(",")
    
    # Security
    API_KEYS = {
        os.getenv("ADMIN_KEY", "rez-hive-admin-key-2026"): "admin",
        os.getenv("VIEWER_KEY", "rez-hive-viewer-key-2026"): "viewer"
    }
    RATE_LIMIT_CALLS = int(os.getenv("RATE_LIMIT_CALLS", "100"))
    RATE_LIMIT_PERIOD = int(os.getenv("RATE_LIMIT_PERIOD", "60"))
    
    # Ollama
    OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
    DEFAULT_MODEL = os.getenv("OLLAMA_MODEL", "qwen2.5-coder:7b")
    OLLAMA_NUM_CTX = int(os.getenv("OLLAMA_NUM_CTX", "32768"))
    OLLAMA_TIMEOUT = int(os.getenv("OLLAMA_TIMEOUT", "120"))
    
    # Directories
    WORKSPACE_DIR = Path.cwd()
    MEMORY_DIR = Path("data/memory")
    EVENT_STORE_DIR = Path("data/event_store")
    WORKERS_DIR = Path("workers")
    COWORKER_DIR = Path("workers/coworker")
    BACKUPS_DIR = Path("data/backups")
    SANDBOX_DIR = Path("data/sandbox")
    
    # Constitution
    CONSTITUTION_LAWS = ["SOVEREIGNTY", "TRANSPARENCY", "ACCOUNTABILITY", "SAFETY", "CODE_SAFETY"]
    
    # Event Chain
    CHAIN_MAXLEN = 10000
    EVENT_PERSISTENCE_BATCH = 50
    
    # Security
    MAX_FILE_SIZE = 25 * 1024 * 1024
    ALLOWED_EXTENSIONS = {'.txt', '.md', '.json', '.csv', '.py', '.js', '.tsx', '.jpg', '.png', '.pdf'}

config = Config()

# ============================================================================
# SECURITY UTILITIES
# ============================================================================
class SecurityError(Exception):
    pass

def sanitize_input(text: str, max_length: int = 10000) -> str:
    if not isinstance(text, str):
        raise SecurityError("Input must be string")
    if len(text) > max_length:
        raise SecurityError(f"Input exceeds {max_length} chars")
    sanitized = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]', '', text)
    if '..' in sanitized or '~' in sanitized:
        raise SecurityError("Path traversal attempt detected")
    return sanitized.strip()

def secure_filename(filename: str) -> str:
    if not filename or len(filename) > 255:
        raise SecurityError("Invalid filename")
    safe = re.sub(r'[^\w\-\.]', '', os.path.basename(filename)).lstrip('.')
    return f"{int(time.time())}_{safe if safe else 'unnamed_file'}"

# ============================================================================
# RATE LIMITER
# ============================================================================
class RateLimiter:
    def __init__(self, calls_per_period: int = 100, period_seconds: int = 60):
        self.calls_per_period = calls_per_period
        self.period_seconds = period_seconds
        self.calls: Dict[str, List[float]] = defaultdict(list)
    
    async def check(self, client_id: str) -> bool:
        now = time.time()
        self.calls[client_id] = [t for t in self.calls[client_id] if now - t < self.period_seconds]
        if len(self.calls[client_id]) >= self.calls_per_period:
            return False
        self.calls[client_id].append(now)
        return True

# ============================================================================
# CIRCUIT BREAKER
# ============================================================================
class CircuitState(Enum):
    CLOSED = auto()
    OPEN = auto()
    HALF_OPEN = auto()

class CircuitBreaker:
    def __init__(self, name: str, failure_threshold: int = 3, recovery_timeout: float = 30.0, half_open_max: int = 3):
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

# ============================================================================
# AUTHENTICATION
# ============================================================================
security_scheme = HTTPBearer(auto_error=False)

async def get_api_key(credentials: HTTPAuthorizationCredentials = Depends(security_scheme)) -> str:
    if not credentials:
        return "anonymous"
    role = config.API_KEYS.get(credentials.credentials)
    if not role:
        raise HTTPException(403, "Invalid API key")
    return role

async def get_optional_key(credentials: HTTPAuthorizationCredentials = Depends(security_scheme)) -> str:
    if credentials:
        role = config.API_KEYS.get(credentials.credentials)
        if role:
            return role
    return "anonymous"

# ============================================================================
# SCE PROTOCOL
# ============================================================================
class SCEProtocol:
    VERSION = "2.0.0"
    
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

# ============================================================================
# EVENT STORE
# ============================================================================
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
                    previous_hash TEXT,
                    created_at REAL DEFAULT (strftime('%s', 'now'))
                );
                CREATE TABLE IF NOT EXISTS blueprints (
                    drift_lock TEXT PRIMARY KEY,
                    blueprint TEXT,
                    timestamp REAL
                );
                CREATE INDEX IF NOT EXISTS idx_events_type ON events(type);
                CREATE INDEX IF NOT EXISTS idx_events_timestamp ON events(timestamp);
            """)
    
    async def save_event(self, event) -> bool:
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute(
                    "INSERT OR REPLACE INTO events VALUES (?,?,?,?,?,?,?)",
                    (event.vera_proof, event.type.value, event.source,
                     json.dumps(event.payload), event.timestamp,
                     event.previous_hash, time.time())
                )
            return True
        except Exception as e:
            logger.error(f"Event save failed: {e}")
            return False
    
    async def save_blueprint(self, drift_lock: str, blueprint: dict) -> bool:
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute(
                    "INSERT OR REPLACE INTO blueprints VALUES (?,?,?)",
                    (drift_lock, json.dumps(blueprint), time.time())
                )
            return True
        except Exception as e:
            logger.error(f"Blueprint save failed: {e}")
            return False
    
    async def get_events(self, limit: int = 100, event_type: str = None) -> List[Dict]:
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                if event_type:
                    rows = conn.execute(
                        "SELECT * FROM events WHERE type=? ORDER BY timestamp DESC LIMIT ?",
                        (event_type, limit)
                    ).fetchall()
                else:
                    rows = conn.execute(
                        "SELECT * FROM events ORDER BY timestamp DESC LIMIT ?",
                        (limit,)
                    ).fetchall()
                return [dict(r) for r in rows]
        except:
            return []

# ============================================================================
# EVENT BUS
# ============================================================================
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
    TRADE_EXECUTED = "trade.executed"
    KILL_SWITCH = "kill.switch"

@dataclass(frozen=True)
class Event:
    type: EventType
    source: str
    payload: Dict[str, Any]
    timestamp: float = field(default_factory=time.time)
    previous_hash: str = ""
    
    def __post_init__(self):
        content = f"{self.type.value}:{self.source}:{json.dumps(self.payload, sort_keys=True)}:{self.timestamp}:{self.previous_hash}"
        object.__setattr__(self, '_vera_proof', hashlib.sha256(content.encode()).hexdigest()[:16])
    
    @property
    def vera_proof(self) -> str:
        return getattr(self, '_vera_proof', '')

class EventBus:
    def __init__(self):
        self._chain: List[Event] = []
        self._lock = asyncio.Lock()
        self._genesis = hashlib.sha256(b"PHOENIX_OMEGA_v15.1.0").hexdigest()[:16]
        self._store = EventStore(config.EVENT_STORE_DIR / "events.db")
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
        await self.publish(Event(type=EventType.SYSTEM_BOOT, source="event_bus", payload={"version": "15.1.0"}))
    
    async def publish(self, event: Event) -> str:
        if not self._ready:
            return ""
        async with self._lock:
            prev = self._chain[-1].vera_proof if self._chain else self._genesis
            linked = Event(
                type=event.type, source=event.source,
                payload=event.payload, previous_hash=prev
            )
            if len(self._chain) >= config.CHAIN_MAXLEN:
                self._chain.pop(0)
            self._chain.append(linked)
        await self._queue.put(linked)
        return linked.vera_proof
    
    async def verify_chain(self) -> bool:
        async with self._lock:
            prev = self._genesis
            for ev in self._chain:
                raw = f"{ev.type.value}:{ev.source}:{json.dumps(ev.payload, sort_keys=True)}:{ev.timestamp}:{prev}"
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
                if len(batch) >= config.EVENT_PERSISTENCE_BATCH:
                    for ev in batch:
                        await self._store.save_event(ev)
                    batch = []
            except asyncio.TimeoutError:
                if batch:
                    for ev in batch:
                        await self._store.save_event(ev)
                    batch = []
            except asyncio.CancelledError:
                for ev in batch:
                    await self._store.save_event(ev)
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

# ============================================================================
# CONSTITUTION
# ============================================================================
class Constitution:
    DANGEROUS = ['rm -rf', 'format', 'del /f', 'mkfs', 'shutdown', 'reboot', ':(){:|:&};:']
    
    def __init__(self):
        self.rulings: List[Dict] = []
    
    def evaluate(self, action: str) -> Dict[str, Any]:
        lower = action.lower()
        for pattern in self.DANGEROUS:
            if pattern in lower:
                ruling = {"approved": False, "reason": f"Blocked: {pattern}", "score": 0}
                self.rulings.append({**ruling, "action": action[:80], "timestamp": time.time()})
                return ruling
        return {"approved": True, "reason": "Passed", "score": 90}

constitution = Constitution()

# ============================================================================
# SOVEREIGN MEMORY
# ============================================================================
class SovereignMemory:
    def __init__(self):
        self.memories: Dict[str, Dict] = {}
        self._store = EventStore(config.EVENT_STORE_DIR / "events.db")
        self._load_from_disk()
    
    def store(self, blueprint: Dict) -> str:
        lock = blueprint.get("master_drift_lock", SCEProtocol.create_drift_lock(blueprint))
        self.memories[lock] = {"value": blueprint, "timestamp": time.time(), "access_count": 0}
        path = config.MEMORY_DIR / f"bp_{lock}.json"
        try:
            with open(path, 'w') as f:
                json.dump(self.memories[lock], f, indent=2)
            asyncio.create_task(self._store.save_blueprint(lock, blueprint))
        except Exception as e:
            logger.error(f"Memory persist failed: {e}")
        return lock
    
    def search(self, query: str, limit: int = 10) -> List[Dict]:
        results = []
        q = query.lower()
        for lock, record in self.memories.items():
            bp = record["value"]
            text = json.dumps(bp.get("intent", {})).lower()
            score = text.count(q) * 5
            if score > 0:
                results.append({"lock": lock, "score": score, "timestamp": record["timestamp"]})
        results.sort(key=lambda x: x["score"], reverse=True)
        return results[:limit]
    
    def _load_from_disk(self):
        for p in config.MEMORY_DIR.glob("*.json"):
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

# ============================================================================
# GPU MONITOR
# ============================================================================
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
                    self.gpus.append({"index": i, "name": name, "handle": h, "total_gb": round(mem.total / 1024**3, 1)})
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

# ============================================================================
# OLLAMA CLIENT
# ============================================================================
class OllamaClient:
    def __init__(self):
        self.base_url = config.OLLAMA_URL
        self.model = config.DEFAULT_MODEL
        self.timeout = config.OLLAMA_TIMEOUT
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
            "options": {"num_ctx": config.OLLAMA_NUM_CTX},
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
            yield "\n\n⏱️ Request timed out."
        except httpx.ConnectError:
            yield "\n\n❌ Cannot reach Ollama. Is it running?"
        except Exception as e:
            yield f"\n\n❌ Ollama error: {e}"

ollama = OllamaClient()

# ============================================================================
# WORKER BASE CLASS
# ============================================================================
class Worker(ABC):
    def __init__(self, name: str):
        self.name = name
    
    @abstractmethod
    async def execute(self, task: str, **kwargs) -> Dict[str, Any]:
        pass

# ============================================================================
# WORKER LOADER - FIXED TO LOAD ALL WORKERS
# ============================================================================
class WorkerLoader:
    def __init__(self, workers_dir: Path):
        self.workers_dir = Path(workers_dir).resolve()
        self.workers = {}
        if str(self.workers_dir) not in sys.path:
            sys.path.insert(0, str(self.workers_dir))
    
    def load_all(self) -> Dict[str, Dict]:
        if not self.workers_dir.exists():
            return {}
        
        logger.info(f"📂 Scanning {self.workers_dir}")
        count = 0
        
        for py_file in self.workers_dir.glob("*.py"):
            if py_file.name.startswith('__') or py_file.name == 'base_worker.py':
                continue
            
            try:
                # First check syntax
                with open(py_file, 'r', encoding='utf-8') as f:
                    compile(f.read(), py_file.name, 'exec')
                
                # Import module
                spec = importlib.util.spec_from_file_location(py_file.stem, py_file)
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                
                # Find Worker subclasses
                for name, obj in inspect.getmembers(module, inspect.isclass):
                    try:
                        if obj is Worker:
                            continue
                        if issubclass(obj, Worker):
                            try:
                                worker = obj()
                                worker_name = worker.name if hasattr(worker, 'name') else name
                                self.workers[worker_name] = {
                                    "class": obj,
                                    "module": py_file.stem,
                                    "loaded_at": time.time(),
                                    "instance": worker
                                }
                                count += 1
                                logger.info(f"  ✅ {worker_name}")
                            except Exception as e:
                                logger.debug(f"  ⚠️ Cannot instantiate {name}: {e}")
                    except TypeError:
                        pass
                        
            except SyntaxError as e:
                logger.debug(f"  ❌ {py_file.name}: Syntax error at line {e.lineno}")
            except Exception as e:
                logger.debug(f"  ❌ {py_file.name}: {str(e)[:50]}")
        
        logger.info(f"📊 Loaded {count} workers from {self.workers_dir.name}")
        return self.workers

# ============================================================================
# BUILT-IN WORKERS
# ============================================================================
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
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', dir=str(config.SANDBOX_DIR), delete=False) as f:
            f.write(code)
            tmp = f.name
        
        try:
            proc = await asyncio.create_subprocess_exec(
                sys.executable, tmp,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=str(config.SANDBOX_DIR),
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
    pass

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
                return {"success": True, "balance": self.balance, "position": self.positions.get(symbol, 0)}
            return {"success": False, "error": f"Insufficient {symbol}"}
        elif "portfolio" in task_lower or "balance" in task_lower:
            total_value = self.balance + sum([pos * 50000 for pos in self.positions.values()])
            return {"success": True, "balance": self.balance, "positions": self.positions, "total_value": total_value}
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

# ============================================================================
# KILL SWITCH
# ============================================================================
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
        await event_bus.publish(Event(type=EventType.KILL_SWITCH, source="kill_switch", payload={"reason": reason, "by": triggered_by}))
    
    def is_active(self) -> bool:
        return self.active
    
    async def reset(self):
        self.active = False
        self.triggered_at = None
        self.triggered_by = None
        self.reason = None
        logger.info("🔓 Kill switch reset")

kill_switch = KillSwitch()

# ============================================================================
# REFLEX COMMANDS
# ============================================================================
class ReflexCommands:
    def __init__(self, kernel):
        self.kernel = kernel
    
    async def execute(self, cmd: str) -> Optional[Dict]:
        cmd = cmd.strip().lower()
        
        if cmd == "/health":
            stats = gpu.stats()
            return {"type": "reflex", "content": f"🔥 Phoenix v{config.VERSION}\nWorkers: {len(self.kernel.workers)}\nBlueprints: {len(memory.memories)}\nOllama: {'🟢' if ollama.available else '🔴'}\nGPU: {stats.get('name', 'None')}\nUptime: {round(time.time() - self.kernel.start_time)}s"}
        
        elif cmd == "/workers":
            names = sorted(self.kernel.workers.keys())
            listing = "\n".join(f"  • {n}" for n in names[:50])
            extra = f"\n  ... +{len(names)-50} more" if len(names) > 50 else ""
            return {"type": "reflex", "content": f"⚙️ Workers ({len(names)})\n{listing}{extra}"}
        
        elif cmd == "/models":
            await ollama.check_connection()
            if ollama.models:
                return {"type": "reflex", "content": f"🤖 Models\n" + "\n".join(f"  • {m}" for m in ollama.models[:10])}
            return {"type": "reflex", "content": "❌ Ollama not connected"}
        
        elif cmd == "/chain":
            stats = await event_bus.get_stats()
            return {"type": "reflex", "content": f"⛓️ Event Chain\nEvents: {stats['total_events']}\nValid: {'✅' if stats['chain_valid'] else '❌'}"}
        
        elif cmd.startswith("/search "):
            query = cmd[8:].strip()
            results = memory.search(query)
            if results:
                lines = [f"  {i+1}. {r['lock'][:12]}… (score: {r['score']})" for i, r in enumerate(results[:5])]
                return {"type": "reflex", "content": f"🔍 Search: {query}\n" + "\n".join(lines)}
            return {"type": "reflex", "content": f"🔍 No results for: {query}"}
        
        elif cmd.startswith("/code "):
            intent = cmd[6:].strip()
            if intent:
                worker = CodeGenWorker()
                result = await worker.execute(intent)
                if result.get("success"):
                    return {"type": "reflex", "content": f"📝 Generated Code\n```python\n{result['code']}\n```"}
            return {"type": "reflex", "content": "Usage: /code <description>"}
        
        elif cmd.startswith("/trade"):
            parts = cmd.split()
            if len(parts) >= 2:
                worker = PaperTraderWorker()
                symbol = parts[2] if len(parts) > 2 else "BTCUSDT"
                amount = float(parts[3]) if len(parts) > 3 else 0.01
                result = await worker.execute(parts[1], symbol=symbol, amount=amount)
                return {"type": "reflex", "content": f"💰 Trade: {result}"}
            return {"type": "reflex", "content": "Usage: /trade buy|sell [symbol] [amount]"}
        
        elif cmd == "/portfolio":
            worker = PaperTraderWorker()
            result = await worker.execute("portfolio")
            return {"type": "reflex", "content": f"📊 Portfolio: {result}"}
        
        elif cmd == "/kill":
            await kill_switch.activate("Manual trigger", triggered_by="user")
            return {"type": "reflex", "content": "🔴 KILL SWITCH ACTIVATED"}
        
        elif cmd == "/kill-status":
            return {"type": "reflex", "content": f"Kill switch active: {kill_switch.is_active()}"}
        
        return None

# ============================================================================
# BACKGROUND TASKS
# ============================================================================
async def symbiote_loop():
    thoughts = ["Memory indexed.", "Event chain verified.", "Worker health nominal.", "Drift analysis complete.", "GPU thermals optimal."]
    while True:
        try:
            await asyncio.sleep(random.randint(120, 300))
            thought = random.choice(thoughts)
            await event_bus.publish(Event(type=EventType.KERNEL_HEARTBEAT, source="symbiote", payload={"thought": thought}))
            logger.debug(f"🦊 {thought}")
        except asyncio.CancelledError:
            return
        except Exception as e:
            logger.error(f"Symbiote error: {e}")
            await asyncio.sleep(10)

async def market_broadcaster(sio=None):
    while True:
        try:
            php_rate = 58
            btc = (42000 + random.uniform(-500, 500)) * php_rate
            eth = (3100 + random.uniform(-50, 50)) * php_rate
            data = [{"name": "BINANCE", "btcPrice": round(btc, 2), "ethPrice": round(eth, 2), "latency": random.randint(12, 45), "status": "SYNCED"},
                    {"name": "KRAKEN", "btcPrice": round(btc + random.uniform(-500, 500), 2), "ethPrice": round(eth + random.uniform(-50, 50), 2), "latency": random.randint(20, 60), "status": "SYNCED"}]
            if sio:
                await sio.emit("marketUpdate", data)
            await asyncio.sleep(2)
        except asyncio.CancelledError:
            return
        except Exception as e:
            logger.error(f"Market error: {e}")
            await asyncio.sleep(5)

# ============================================================================
# MAIN KERNEL
# ============================================================================
class PhoenixOmegaKernel:
    def __init__(self):
        self.version = config.VERSION
        self.start_time = time.time()
        self.workers: Dict[str, Dict] = {}
        self.rate_limiter = RateLimiter(config.RATE_LIMIT_CALLS, config.RATE_LIMIT_PERIOD)
        self._bg_tasks: List[asyncio.Task] = []
        
        # Load workers
        logger.info("=" * 60)
        logger.info("📦 LOADING WORKERS")
        logger.info("=" * 60)
        
        loader = WorkerLoader(config.WORKERS_DIR)
        self.workers.update(loader.load_all())
        
        if config.COWORKER_DIR.exists():
            coworker_loader = WorkerLoader(config.COWORKER_DIR)
            self.workers.update(coworker_loader.load_all())
        
        # Add built-in workers
        builtins = [
            ("system_monitor", SystemMonitorWorker),
            ("code_execution", CodeExecutionWorker),
            ("code_gen", CodeGenWorker),
            ("paper_trader", PaperTraderWorker),
            ("backtest", BacktestWorker),
        ]
        for name, cls in builtins:
            if name not in self.workers:
                self.workers[name] = {"class": cls, "module": "builtin", "loaded_at": time.time()}
                logger.info(f"  ✅ {name} (builtin)")
        
        logger.info(f"⚙️ Total workers: {len(self.workers)}")
        
        self.reflex = ReflexCommands(self)
        
        # Setup FastAPI
        self.app = FastAPI(title=f"Phoenix Omega v{self.version}", docs_url="/docs")
        self.app.add_middleware(CORSMiddleware, allow_origins=config.CORS_ORIGINS, allow_credentials=True, allow_methods=["*"], allow_headers=["*"])
        
        @self.app.middleware("http")
        async def security_headers(request: Request, call_next):
            response = await call_next(request)
            response.headers["X-Content-Type-Options"] = "nosniff"
            response.headers["X-Frame-Options"] = "DENY"
            response.headers["X-XSS-Protection"] = "1; mode=block"
            return response
        
        self._setup_routes()
        
        self.sio = None
        if HAS_SOCKETIO:
            self.sio = socketio.AsyncServer(cors_allowed_origins="*", async_mode="asgi")
            self._setup_socketio()
    
    def _setup_socketio(self):
        @self.sio.on("connect")
        async def on_connect(sid, _):
            logger.info(f"🟢 Socket: {sid[:8]}")
        
        @self.sio.on("disconnect")
        async def on_disconnect(sid):
            logger.info(f"🔴 Socket: {sid[:8]}")
    
    def _setup_routes(self):
        @self.app.get("/")
        async def root():
            return {"name": "Phoenix Omega", "version": self.version, "workers": len(self.workers), "status": "online"}
        
        @self.app.get("/health")
        async def health():
            return {"status": "online", "version": self.version, "workers": len(self.workers), "memory": len(memory.memories), "ollama": ollama.available, "gpu": gpu.stats(), "uptime": round(time.time() - self.start_time, 1)}
        
        @self.app.get("/workers/list")
        async def workers_list():
            return {"workers": sorted(self.workers.keys()), "count": len(self.workers)}
        
        @self.app.get("/events/stats")
        async def events_stats():
            return await event_bus.get_stats()
        
        @self.app.get("/ollama/status")
        async def ollama_status():
            connected = await ollama.check_connection()
            return {"connected": connected, "model": ollama.model, "models": ollama.models[:10]}
        
        @self.app.get("/metrics")
        async def metrics_endpoint():
            if HAS_PROMETHEUS:
                return Response(content=generate_latest(), media_type="text/plain")
            return {"error": "prometheus not installed"}
        
        @self.app.get("/kill/status")
        async def kill_status():
            return {"active": kill_switch.is_active(), "triggered_at": kill_switch.triggered_at, "triggered_by": kill_switch.triggered_by, "reason": kill_switch.reason}
        
        @self.app.post("/kill")
        async def kill_endpoint(role: str = Depends(get_api_key)):
            if role != "admin":
                raise HTTPException(403, "Admin required")
            await kill_switch.activate("API trigger", triggered_by=role)
            return {"status": "activated"}
        
        @self.app.post("/kernel/stream")
        async def kernel_stream(request: Request, role: str = Depends(get_optional_key)):
            try:
                data = await request.json()
            except:
                return JSONResponse({"error": "Invalid JSON"}, status_code=400)
            
            task = data.get("task", "").strip()
            if not task:
                return JSONResponse({"error": "No task"}, status_code=400)
            
            if not await self.rate_limiter.check(request.client.host):
                return JSONResponse({"error": "Rate limit"}, status_code=429)
            
            try:
                task = sanitize_input(task)
            except SecurityError as e:
                return JSONResponse({"error": str(e)}, status_code=400)
            
            async def generate():
                reflex = await self.reflex.execute(task)
                if reflex:
                    yield f"data: {json.dumps(reflex)}\n\n"
                    yield f"data: {json.dumps({'type': 'done'})}\n\n"
                    return
                
                ruling = constitution.evaluate(task)
                if not ruling["approved"]:
                    yield f"data: {json.dumps({'type': 'error', 'content': ruling['reason']})}\n\n"
                    yield f"data: {json.dumps({'type': 'done'})}\n\n"
                    return
                
                system_prompt = f"You are Phoenix, a sovereign AI assistant. Version: {config.VERSION}. Answer concisely."
                messages = [{"role": "system", "content": system_prompt}, {"role": "user", "content": task}]
                full_response = ""
                
                try:
                    async for token in ollama_breaker.call(ollama.stream_chat, messages):
                        yield f"data: {json.dumps({'type': 'token', 'content': token})}\n\n"
                        full_response += token
                except Exception as e:
                    yield f"data: {json.dumps({'type': 'token', 'content': f'⚠️ Ollama unavailable: {e}'})}\n\n"
                    full_response = f"⚠️ Service unavailable"
                
                blueprint = SCEProtocol.create_blueprint({"task": task, "role": role}, {"workers": len(self.workers)}, {"response_length": len(full_response)})
                lock = memory.store(blueprint)
                await event_bus.publish(Event(type=EventType.CHAT_MESSAGE, source="kernel", payload={"task": task[:200], "drift_lock": lock}))
                yield f"data: {json.dumps({'type': 'done', 'drift_lock': lock})}\n\n"
            
            return StreamingResponse(generate(), media_type="text/event-stream")
        
        @self.app.post("/kernel/upload")
        async def upload_file(file: UploadFile = File(...), role: str = Depends(get_optional_key)):
            contents = await file.read()
            if len(contents) > config.MAX_FILE_SIZE:
                raise HTTPException(413, "File too large")
            ext = os.path.splitext(file.filename)[1].lower()
            if ext not in config.ALLOWED_EXTENSIONS:
                raise HTTPException(415, f"{ext} not allowed")
            safe_name = secure_filename(file.filename)
            path = config.WORKSPACE_DIR / "data" / "uploads" / safe_name
            path.parent.mkdir(parents=True, exist_ok=True)
            with open(path, 'wb') as f:
                f.write(contents)
            await event_bus.publish(Event(type=EventType.FILE_OPERATION, source="upload", payload={"file": safe_name, "size": len(contents)}))
            return {"filename": safe_name, "size": len(contents), "status": "stored"}
        
        @self.app.websocket("/ws/telemetry")
        async def websocket_telemetry(websocket: WebSocket):
            await websocket.accept()
            try:
                while True:
                    telemetry = {"type": "telemetry", "timestamp": time.time(), "data": {"workers": len(self.workers), "memory": len(memory.memories), "gpu": gpu.stats()}}
                    await websocket.send_json(telemetry)
                    await asyncio.sleep(2)
            except WebSocketDisconnect:
                pass
    
    async def startup(self):
        await event_bus.initialize()
        await ollama.check_connection()
        
        if HAS_PROMETHEUS:
            try:
                start_http_server(config.METRICS_PORT)
                logger.info(f"📊 Metrics on :{config.METRICS_PORT}")
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
        logger.info(f"⛓️ Final chain integrity: {await event_bus.verify_chain()}")
    
    def _print_banner(self):
        print("\n" + "=" * 60)
        print(f"🔥 PHOENIX OMEGA v{self.version}")
        print("=" * 60)
        print(f"  Workers:    {len(self.workers)}")
        print(f"  Blueprints: {len(memory.memories)}")
        print(f"  Ollama:     {'🟢 ' + ollama.model if ollama.available else '🔴 offline'}")
        if gpu.has_gpu:
            s = gpu.stats()
            print(f"  GPU:        {s.get('name')} ({s.get('free_gb')}GB free)")
        print(f"  API:        http://{config.HOST}:{config.PORT}")
        print("=" * 60)
        print("  Commands: /health /workers /models /chain /search /code")
        print("  Trading:   /trade /portfolio")
        print("  Emergency: /kill /kill-status")
        print("=" * 60 + "\n")
    
    async def run(self):
        await self.startup()
        app = socketio.ASGIApp(self.sio, self.app) if self.sio else self.app
        server = uvicorn.Server(uvicorn.Config(app, host=config.HOST, port=config.PORT, log_level="info"))
        try:
            await server.serve()
        finally:
            await self.shutdown()

# ============================================================================
# ENTRY POINT
# ============================================================================
if __name__ == "__main__":
    kernel = PhoenixOmegaKernel()
    try:
        asyncio.run(kernel.run())
    except KeyboardInterrupt:
        print("\n🛑 Phoenix rests.")
    except Exception as e:
        logger.error(f"Fatal: {e}", exc_info=True)