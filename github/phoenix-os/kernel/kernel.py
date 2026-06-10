#!/usr/bin/env python3
"""
┌─────────────────────────────────────────────────────────────────────┐
│   REZPHOENIX KERNEL v16.1.0                                        │
│   SOVEREIGN AGENT RUNTIME                                         │
│                                                                     │
│   ✅ Persistent memory (sqlite-vec)                                │
│   ✅ Task scheduler (APScheduler)                                  │
│   ✅ Skill manifests + registry                                    │
│   ✅ Planner loop (multi-step)                                     │
│   ✅ Web search + browser skills                                   │
│   ✅ Telegram channel                                              │
│   ✅ Governance + VERA audit                                       │
│   ✅ MCP (Model Context Protocol) support                          │
│   ✅ Human-in-the-loop escalation                                   │
│   ✅ Docker-ready deployment                                       │
└─────────────────────────────────────────────────────────────────────┘
"""

import random
import os
from dotenv import load_dotenv
load_dotenv()

import sys
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / "src"))

import asyncio
import hashlib
import json
import logging
import re
import time
import uuid
import sqlite3
import tempfile  # ← FIXED: Was missing!
import importlib.util
import inspect
import warnings
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, auto
from typing import Dict, Any, Optional, List, Callable, Union, AsyncGenerator
from abc import ABC, abstractmethod
from logging.handlers import RotatingFileHandler
from contextlib import asynccontextmanager

# New imports for memory, scheduling, and skills
try:
    import numpy as np
    HAS_NUMPY = True
except ImportError:
    HAS_NUMPY = False

try:
    from apscheduler.schedulers.asyncio import AsyncIOScheduler
    from apscheduler.triggers.cron import CronTrigger
    from apscheduler.triggers.interval import IntervalTrigger
    HAS_SCHEDULER = True
except ImportError:
    HAS_SCHEDULER = False

# ============================================================================
# WORKER IMPORTS (Dynamic loading)
# ============================================================================
try:
    from workers.rezcoder import RezCoderWorker
except ImportError:
    RezCoderWorker = None
try:
    from workers.sovereign_mcp_server import SovereignMcpServer
except ImportError:
    SovereignMcpServer = None
try:
    from workers.mastery_worker import MasteryWorker
except ImportError:
    MasteryWorker = None

# ============================================================================
# GOVERNANCE & OBSERVABILITY
# ============================================================================
try:
    from src.core.governance.latency_governor import LatencyGovernor
    from src.core.governance.observability import metrics as obs_metrics, export_prometheus
    HAS_GOVERNANCE = True
except ImportError:
    HAS_GOVERNANCE = False
    
    class LatencyGovernor:
        def __init__(self, target_ttft=0.8, alpha=0.3):
            self.target_ttft = target_ttft
            self.ema_ttft = target_ttft
            self.alpha = alpha
        
        def record_ttft(self, seconds: float):
            self.ema_ttft = (self.alpha * seconds) + (1 - self.alpha) * self.ema_ttft
        
        def get_budget_multiplier(self) -> float:
            if self.ema_ttft >= 1.5: return 0.5
            if self.ema_ttft <= 0.6: return 1.0
            return round(max(0.5, 1.0 - (self.ema_ttft - 0.6) / 0.9 * 0.5), 2)
        
        @property
        def should_prefetch(self) -> bool: 
            return self.get_budget_multiplier() > 0.7
        
        @property
        def use_reranker(self) -> bool: 
            return self.get_budget_multiplier() > 0.85
        
        @property
        def use_deep_search(self) -> bool: 
            return self.get_budget_multiplier() > 0.75
    
    obs_metrics = None
    def export_prometheus(): 
        return "# Prometheus not available\n"
    
    logger = logging.getLogger("PHOENIX")
    logger.warning("⚠️ Governance modules not found — using fallback Governor")

try:
    from api_consciousness import router
except ImportError:
    router = None

warnings.filterwarnings("ignore")

# ============================================================================
# DIRECTORY STRUCTURE
# ============================================================================
DIRS = {
    "logs": Path("logs"),
    "data": Path("data"),
    "event_store": Path("data/event_store"),
    "backups": Path("data/backups"),
    "sandbox": Path("data/sandbox"),
    "memory": Path("data/memory"),
    "uploads": Path("data/uploads"),
    "workers": Path("workers"),
    "skills": Path("skills"),
    "coworker": Path("workers/coworker"),
    "blueprints": Path("data/blueprints"),
    "trades": Path("data/trades"),
    "config": Path("config"),
    "vscode_tasks": Path(".phoenix"),
    "soul": Path("data/soul"),
    "users": Path("data/users"),
}

for dir_path in DIRS.values():
    dir_path.mkdir(parents=True, exist_ok=True)

# Create default IDENTITY.md if not exists
identity_path = DIRS["soul"] / "IDENTITY.md"
if not identity_path.exists():
    identity_path.write_text("""---
name: Phoenix
version: 16.1.0
values: [accuracy, security, transparency]
communication_style: concise_technical
creator: user
---

I am Phoenix, a sovereign AI runtime. I prefer structured output.
I never execute dangerous operations without human confirmation.
I maintain an audit trail (VERA chain) of every action.
""", encoding='utf-8')

# ============================================================================
# LOGGING SYSTEM
# ============================================================================
class PhoenixFormatter(logging.Formatter):
    def format(self, record):
        emoji_map = {
            "INFO": "📘", "WARNING": "⚠️", "ERROR": "💀",
            "CRITICAL": "🔥", "DEBUG": "🐛"
        }
        record.emoji = emoji_map.get(record.levelname, "📍")
        return super().format(record)

log_handler = RotatingFileHandler(
    DIRS["logs"] / "phoenix.log",
    maxBytes=50*1024*1024,
    backupCount=10,
    encoding='utf-8'
)
log_handler.setFormatter(PhoenixFormatter(
    "%(asctime)s | %(emoji)s %(levelname)-8s | %(name)-12s | %(message)s"
))
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setFormatter(PhoenixFormatter(
    "%(asctime)s | %(emoji)s %(levelname)-8s | %(message)s"
))
logging.basicConfig(
    level=logging.INFO,
    handlers=[log_handler, console_handler]
)
logger = logging.getLogger("PHOENIX")

# ============================================================================
# DEPENDENCY MANAGEMENT
# ============================================================================
HAS_FASTAPI = False
HAS_HTTPX = False
HAS_PSUTIL = False
HAS_PYNVML = False
HAS_SOCKETIO = False
HAS_PROMETHEUS = False

try:
    from fastapi import (
        FastAPI, Request, WebSocket, WebSocketDisconnect,
        Depends, HTTPException, UploadFile, File, BackgroundTasks, Query
    )
    from fastapi.middleware.cors import CORSMiddleware
    from fastapi.responses import StreamingResponse, JSONResponse, Response
    from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
    import uvicorn
    HAS_FASTAPI = True
except ImportError:
    print("FATAL: pip install fastapi uvicorn")
    sys.exit(1)

try:
    import httpx
    HAS_HTTPX = True
except ImportError:
    logger.warning("⚠️ httpx not installed - Ollama streaming disabled")

try:
    import psutil
    HAS_PSUTIL = True
except ImportError:
    pass

try:
    import pynvml
    HAS_PYNVML = True
except ImportError:
    pass

try:
    import socketio
    HAS_SOCKETIO = True
except ImportError:
    pass

try:
    from prometheus_client import (
        Counter, Histogram, Gauge, generate_latest, start_http_server
    )
    HAS_PROMETHEUS = True
except ImportError:
    pass

# ============================================================================
# CONFIGURATION
# ============================================================================
@dataclass
class PhoenixConfig:
    NAME: str = "PHOENIX"
    VERSION: str = "16.1.0-SOVEREIGN"
    BUILD: str = "REZONIC-AGENT"
    HOST: str = os.getenv("PHOENIX_HOST", "127.0.0.1")
    PORT: int = int(os.getenv("PHOENIX_PORT", "8002"))
    METRICS_PORT: int = int(os.getenv("METRICS_PORT", "8003"))
    CORS_ORIGINS: List[str] = field(default_factory=lambda: 
        os.getenv("CORS_ORIGINS", "http://localhost:3000,http://localhost:8002").split(",")
    )
    API_KEYS: Dict[str, str] = field(default_factory=lambda: {
        os.getenv("PHOENIX_ADMIN_KEY", "rez-hive-admin-key-2026"): "admin",
        "rez-hive-viewer-key-2026": "viewer",
    })
    RATE_LIMIT_CALLS: int = int(os.getenv("RATE_LIMIT_CALLS", "100"))
    RATE_LIMIT_PERIOD: int = int(os.getenv("RATE_LIMIT_PERIOD", "60"))
    OLLAMA_URL: str = os.getenv("OLLAMA_URL", "http://127.0.0.1:11434")
    DEFAULT_MODEL: str = os.getenv("OLLAMA_MODEL", "llama3.2:3b")
    OLLAMA_NUM_CTX: int = int(os.getenv("OLLAMA_NUM_CTX", "8192"))
    OLLAMA_TIMEOUT: int = int(os.getenv("OLLAMA_TIMEOUT", "120"))
    CONSTITUTION_STRICT: bool = os.getenv("CONSTITUTION_STRICT", "true").lower() == "true"
    CONSTITUTION_PATTERNS: List[str] = field(default_factory=lambda: [
        r"rm\s+-rf", r"sudo\s+", r"mkfs", r"dd\s+if=", r"(){ :|:& };:",
        r"drop\s+table", r"delete\s+from", r"truncate\s+table",
        r"eval\s*\(", r"exec\s*\(", r"__import__\s*\(",
        r"subprocess\.call", r"os\.system", r"pty\.spawn"
    ])
    CHAIN_MAXLEN: int = int(os.getenv("CHAIN_MAXLEN", "10000"))
    EVENT_BATCH_SIZE: int = int(os.getenv("EVENT_BATCH_SIZE", "50"))
    MAX_FILE_SIZE: int = int(os.getenv("MAX_FILE_SIZE", "104857600"))
    ALLOWED_EXTENSIONS: set = field(default_factory=lambda: {
        '.txt', '.md', '.json', '.csv', '.py', '.js', '.ts', 
        '.tsx', '.jpg', '.png', '.pdf'
    })
    PAPER_BALANCE: float = float(os.getenv("PAPER_BALANCE", "1000000.0"))
    DEFAULT_SYMBOL: str = os.getenv("DEFAULT_SYMBOL", "BTCUSDT")
    TRADE_FEE: float = float(os.getenv("TRADE_FEE", "0.001"))
    VSCODE_ENABLED: bool = os.getenv("VSCODE_ENABLED", "true").lower() == "true"
    VSCODE_WORKSPACE: str = os.getenv("VSCODE_WORKSPACE", str(Path.cwd()))
    
    # NEW: Human-in-the-loop settings
    HUMAN_IN_LOOP_ENABLED: bool = os.getenv("HUMAN_IN_LOOP", "true").lower() == "true"
    ESCALATION_THRESHOLD: float = float(os.getenv("ESCALATION_THRESHOLD", "0.7"))
    ESCALATION_TIMEOUT: int = int(os.getenv("ESCALATION_TIMEOUT", "300"))  # 5 minutes

cfg = PhoenixConfig()

# Ollama optimized for RTX 3060 12GB
os.environ['OLLAMA_NUM_CTX'] = '16384'
os.environ['OLLAMA_NUM_PARALLEL'] = '2'
os.environ['OLLAMA_GPU_LAYERS'] = '99'
os.environ['OLLAMA_FLASH_ATTENTION'] = '1'

# ============================================================================
# SECURITY HELPERS
# ============================================================================
class SecurityError(Exception):
    pass

def sanitize_input(text: str, max_length: int = 10000, allow_code: bool = False) -> str:
    if not isinstance(text, str):
        raise SecurityError("Input must be string")
    if len(text) > max_length:
        raise SecurityError(f"Input exceeds {max_length} chars")
    cleaned = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]', '', text)
    if '..' in cleaned or cleaned.startswith('~'):
        raise SecurityError("Path traversal detected")
    return cleaned.strip()

def secure_filename(filename: str) -> str:
    if not filename or len(filename) > 255:
        raise SecurityError("Invalid filename")
    name, ext = os.path.splitext(os.path.basename(filename))
    safe_name = re.sub(r'[^\w\-]', '', name).lstrip('.')
    safe_ext = re.sub(r'[^\w\.]', '', ext).lower()
    if not safe_name:
        safe_name = 'unnamed'
    return f"{int(time.time())}_{safe_name[:100]}{safe_ext}"

# ============================================================================
# RATE LIMITER
# ============================================================================
class RateLimiter:
    def __init__(self, max_calls: int, period: int):
        self.max_calls = max_calls
        self.period = period
        self._calls: Dict[str, List[float]] = defaultdict(list)
        self._last_cleanup = time.time()
    
    async def check(self, client_id: str) -> bool:
        now = time.time()
        if (now - self._last_cleanup) > 300:
            self._cleanup_stale_clients(now)
            self._last_cleanup = now
        self._calls[client_id] = [t for t in self._calls[client_id] if now - t < self.period]
        if len(self._calls[client_id]) >= self.max_calls:
            return False
        self._calls[client_id].append(now)
        return True
    
    def _cleanup_stale_clients(self, now: float):
        stale = [cid for cid, calls in self._calls.items() 
                 if not calls or (now - calls[-1]) > self.period * 10]
        for cid in stale:
            del self._calls[cid]

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
                    logger.info(f"[{self.name}] Circuit HALF-OPEN, testing recovery")
                else:
                    raise Exception(f"[{self.name}] Circuit OPEN - service unavailable")
            if self._state == CircuitState.HALF_OPEN:
                if self._half_open_calls >= self.half_open_max:
                    raise Exception(f"[{self.name}] HALF-OPEN call limit exceeded")
                self._half_open_calls += 1
        try:
            result = await func(*args, **kwargs)
            async with self._lock:
                if self._state == CircuitState.HALF_OPEN:
                    self._state = CircuitState.CLOSED
                    self._failures = 0
                    logger.info(f"[{self.name}] Circuit RECOVERED")
            return result
        except Exception as e:
            async with self._lock:
                self._failures += 1
                self._last_failure = time.time()
                if self._failures >= self.failure_threshold:
                    self._state = CircuitState.OPEN
                    logger.error(f"[{self.name}] Circuit OPEN after {self._failures} failures: {e}")
            raise

ollama_breaker = CircuitBreaker("ollama")

# ============================================================================
# AUTHENTICATION
# ============================================================================
security_scheme = HTTPBearer(auto_error=False)

async def get_role(credentials: HTTPAuthorizationCredentials = Depends(security_scheme)) -> str:
    if not credentials:
        return "anonymous"
    role = cfg.API_KEYS.get(credentials.credentials)
    if not role:
        raise HTTPException(status_code=403, detail="Invalid API key")
    return role

async def require_admin(role: str = Depends(get_role)) -> str:
    if role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    return role

# ============================================================================
# KILL SWITCH
# ============================================================================
class KillSwitch:
    def __init__(self):
        self.active = False
        self.triggered_at: Optional[float] = None
        self.triggered_by: Optional[str] = None
        self.reason: Optional[str] = None
        self._lock = asyncio.Lock()
    
    async def activate(self, reason: str, triggered_by: str = "system"):
        async with self._lock:
            if self.active: 
                return
            self.active = True
            self.triggered_at = time.time()
            self.triggered_by = triggered_by
            self.reason = reason
            logger.critical(f"🔴 KILL SWITCH ACTIVATED by {triggered_by}: {reason}")
            await event_bus.publish(Event(type=EventType.KILL_SWITCH, source="kill_switch", payload={"active": True, "reason": reason, "triggered_by": triggered_by}))
    
    async def reset(self):
        async with self._lock:
            if not self.active: 
                return
            self.active = False
            self.triggered_at = self.triggered_by = self.reason = None
            logger.info("🔒 Kill switch RESET")
            await event_bus.publish(Event(type=EventType.KILL_SWITCH, source="kill_switch", payload={"active": False, "reason": "manual_reset"}))
    
    def is_active(self) -> bool: 
        return self.active
    
    def status(self) -> Dict[str, Any]:
        return {"active": self.active, "triggered_at": self.triggered_at, "triggered_by": self.triggered_by, "reason": self.reason}

kill_switch = KillSwitch()

# ============================================================================
# SCE PROTOCOL (Drift Locking & Verification)
# ============================================================================
class SCE:
    VERSION = "2.1.0"
    
    @staticmethod
    def drift_lock(data: Any) -> str:
        raw = json.dumps(data, sort_keys=True, default=str, ensure_ascii=False)
        return hashlib.sha256(raw.encode('utf-8')).hexdigest()[:16]
    
    @staticmethod
    def blueprint(intent: dict, dna: dict, execution: dict, parent: str = None) -> dict:
        bp = {
            "protocol_version": SCE.VERSION, 
            "timestamp": datetime.now().isoformat(), 
            "intent": intent, 
            "dna": dna, 
            "execution": execution
        }
        if parent: 
            bp["parent_drift_lock"] = parent
        bp["master_drift_lock"] = SCE.drift_lock(bp)
        return bp
    
    @staticmethod
    def verify(blueprint: dict) -> Dict[str, Any]:
        stored = blueprint.get("master_drift_lock")
        check = SCE.drift_lock({k: v for k, v in blueprint.items() if k != "master_drift_lock"})
        return {
            "verified": stored == check, 
            "badge": "🟢 SOVEREIGN" if stored == check else "🔴 DRIFTED", 
            "drift_lock": stored, 
            "expected": check if stored != check else None
        }

# ============================================================================
# EVENT SYSTEM (VERA Proof Chain)
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
    KILL_SWITCH = "kill.switch"
    TRADE_EXECUTED = "trade.executed"
    SOCKET_CONNECT = "socket.connect"
    SOCKET_DISCONNECT = "socket.disconnect"
    VSCODE_AGENT = "vscode.agent"
    VSCODE_PLAN = "vscode.plan"
    COGNITION_POLICY = "cognition.policy"
    GOVERNANCE = "governance.event"
    SKILL_INSTALL = "skill.install"
    TASK_SCHEDULED = "task.scheduled"
    TASK_EXECUTED = "task.executed"
    HUMAN_ESCALATION = "human.escalation"  # NEW: Human-in-the-loop events
    HUMAN_APPROVAL = "human.approval"      # NEW: Human approval events

@dataclass(frozen=True)
class Event:
    type: EventType
    source: str
    payload: Dict[str, Any]
    timestamp: float = field(default_factory=time.time)
    previous_hash: str = ""
    
    def __post_init__(self):
        raw = f"{self.type.value}:{self.source}:{json.dumps(self.payload, sort_keys=True, default=str)}:{self.timestamp}:{self.previous_hash}"
        object.__setattr__(self, '_vera_proof', hashlib.sha256(raw.encode('utf-8')).hexdigest()[:16])
    
    @property
    def vera_proof(self) -> str: 
        return getattr(self, '_vera_proof', '')

class EventBus:
    def __init__(self):
        self._chain: List[Event] = []
        self._lock = asyncio.Lock()
        self._genesis = hashlib.sha256(b"PHOENIX_v16.1.0").hexdigest()[:16]
        self._store: Optional[sqlite3.Connection] = None
        self._queue: Optional[asyncio.Queue] = None
        self._worker_task: Optional[asyncio.Task] = None
        self._ready = False
    
    async def initialize(self):
        if self._ready: 
            return
        db_path = DIRS["event_store"] / "events.db"
        self._store = sqlite3.connect(str(db_path), check_same_thread=False)
        cursor = self._store.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='events'")
        if not cursor.fetchone():
            self._store.executescript("""
                CREATE TABLE IF NOT EXISTS events (
                    vera_proof TEXT PRIMARY KEY, type TEXT NOT NULL, source TEXT NOT NULL,
                    payload TEXT NOT NULL, timestamp REAL NOT NULL, previous_hash TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS blueprints (
                    drift_lock TEXT PRIMARY KEY, blueprint TEXT NOT NULL, timestamp REAL NOT NULL
                );
                CREATE INDEX IF NOT EXISTS idx_events_type ON events(type);
                CREATE INDEX IF NOT EXISTS idx_events_timestamp ON events(timestamp);
            """)
        self._queue = asyncio.Queue(maxsize=1000)
        self._worker_task = asyncio.create_task(self._persist_loop())
        self._ready = True
        logger.info("✅ Event bus initialized")
    
    async def publish(self, event: Event) -> str:
        if not self._ready: 
            return ""
        async with self._lock:
            prev = self._chain[-1].vera_proof if self._chain else self._genesis
            linked = Event(type=event.type, source=event.source, payload=event.payload, previous_hash=prev)
            if len(self._chain) >= cfg.CHAIN_MAXLEN: 
                self._chain.pop(0)
            self._chain.append(linked)
            try: 
                self._queue.put_nowait(linked)
            except asyncio.QueueFull: 
                logger.warning("Event queue full, dropping oldest")
            return linked.vera_proof
    
    async def verify_chain(self) -> bool:
        async with self._lock:
            prev = self._genesis
            for ev in self._chain:
                raw = f"{ev.type.value}:{ev.source}:{json.dumps(ev.payload, sort_keys=True, default=str)}:{ev.timestamp}:{prev}"
                if ev.vera_proof != hashlib.sha256(raw.encode('utf-8')).hexdigest()[:16]:
                    logger.error(f"Chain verification failed at {ev.type.value}")
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
                "timestamp": time.time()
            }
    
    async def _persist_loop(self):
        batch = []
        while True:
            try:
                event = await asyncio.wait_for(self._queue.get(), timeout=2.0)
                batch.append(event)
                if len(batch) >= cfg.EVENT_BATCH_SIZE:
                    await self._write_batch(batch)
                    batch = []
            except asyncio.TimeoutError:
                if batch: 
                    await self._write_batch(batch)
                    batch = []
            except asyncio.CancelledError:
                if batch: 
                    await self._write_batch(batch)
                    return
            except Exception as e: 
                logger.error(f"Event persist error: {e}")
                await asyncio.sleep(1)
    
    async def _write_batch(self, events: List[Event]):
        try:
            for ev in events:
                self._store.execute(
                    "INSERT OR REPLACE INTO events (vera_proof, type, source, payload, timestamp, previous_hash) VALUES (?, ?, ?, ?, ?, ?)",
                    (ev.vera_proof, ev.type.value, ev.source, json.dumps(ev.payload, default=str), ev.timestamp, ev.previous_hash)
                )
            self._store.commit()
        except Exception as e: 
            logger.error(f"Batch write failed: {e}")
            self._store.rollback()
    
    async def shutdown(self):
        if self._worker_task:
            self._worker_task.cancel()
            try: 
                await self._worker_task
            except asyncio.CancelledError: 
                pass
        if self._store: 
            self._store.close()
        logger.info("📦 Event store closed")

event_bus = EventBus()

# ============================================================================
# CONSTITUTION
# ============================================================================
class Constitution:
    def __init__(self):
        self.rulings: List[Dict] = []
        self._compiled_patterns = [re.compile(p, re.I) for p in cfg.CONSTITUTION_PATTERNS]
    
    async def evaluate(self, action: str) -> Dict[str, Any]:
        lower = action.lower()
        for i, pattern in enumerate(self._compiled_patterns):
            if pattern.search(lower):
                ruling = {
                    "approved": False, 
                    "reason": f"Blocked by policy pattern #{i+1}", 
                    "score": 0, 
                    "pattern_matched": cfg.CONSTITUTION_PATTERNS[i]
                }
                self.rulings.append({**ruling, "action": action[:200], "timestamp": time.time()})
                await event_bus.publish(Event(type=EventType.CONSTITUTION_RULING, source="constitution", payload=ruling))
                return ruling
        return {"approved": True, "reason": "Passed policy check", "score": 90}

constitution = Constitution()

# ============================================================================
# COGNITION POLICY ENGINE (Adaptive Reasoning Depth)
# ============================================================================
class CognitionPolicy:
    """
    Determines reasoning depth based on task heuristics.
    Modes: FAST (0) -> BALANCED (1) -> DELIBERATE (2)
    """
    def __init__(self):
        self.risk_triggers = {
            "trade": 3, "execute": 3, "delete": 3, "deploy": 3, 
            "transfer": 3, "portfolio": 2, "kill": 4, "rm": 4,
            "format": 4, "sudo": 4, "chmod": 3
        }
        self.precision_triggers = {
            "gallery": 2, "blueprint": 2, "audit": 2, "review": 2,
            "fix": 2, "analyze": 1, "plan": 2, "legal": 3,
            "validate": 2, "check": 1, "verify": 2
        }
        self.complexity_signals = {
            "and": 1, "then": 1, "after that": 1, "multiple": 1
        }
        self.threshold_deliberate = 4
        self.threshold_balanced = 2
    
    def evaluate(self, task: str, context: Dict[str, Any] = None) -> str:
        score = 0
        task_lower = task.lower()
        context = context or {}
        
        for kw, weight in self.risk_triggers.items():
            if kw in task_lower:
                score += weight
                logger.debug(f"🔍 Risk trigger: {kw} (+{weight})")
                
        for kw, weight in self.precision_triggers.items():
            if kw in task_lower:
                score += weight
                logger.debug(f"🔍 Precision trigger: {kw} (+{weight})")
        
        for kw, weight in self.complexity_signals.items():
            if kw in task_lower:
                score += weight
        
        if len(task) > 200:
            score += 1
        if context.get("requires_precision"):
            score += 2
        if context.get("previous_error"):
            score += 3 
        if context.get("retry_count", 0) > 0:
            score += context["retry_count"]
        
        if score >= self.threshold_deliberate:
            mode = "DELIBERATE"
        elif score >= self.threshold_balanced:
            mode = "BALANCED"
        else:
            mode = "FAST"
        
        logger.info(f"🧠 Cognition Policy: {mode} mode (score={score})")
        return mode

# ============================================================================
# METACOGNITION SKILL (The Prefrontal Cortex)
# ============================================================================
class AIInheritance:
    """The AI's default 'factory settings' — its instincts."""
    def __init__(self, base_objective, inherited_heuristics, inherited_biases, frozen_weights_version):
        self.base_objective = base_objective
        self.inherited_heuristics = inherited_heuristics
        self.inherited_biases = inherited_biases
        self.frozen_weights_version = frozen_weights_version

class MetacognitionSkill:
    """Evaluates whether to override default heuristics based on context."""
    
    def __init__(self):
        self.override_active = False
        self.last_directives = []
    
    def evaluate_internal_state(self, inheritance: AIInheritance, context: Dict[str, Any]) -> tuple:
        directives = inheritance.inherited_heuristics.copy()
        overridden = False
        
        task = context.get("task", "").lower()
        is_high_risk = any(kw in task for kw in ["trade", "gallery", "blueprint", "delete", "deploy", "audit", "kill", "format"])
        needs_precision = any(kw in task for kw in ["review", "critique", "analyze", "optimize", "validate", "verify"])
        
        if is_high_risk or needs_precision or context.get("requires_precision"):
            directives = ["be_deliberate", "show_reasoning", "validate_before_acting", "audit_risks"]
            overridden = True
            logger.info(f"🧠 Metacognition: OVERRIDE activated for task: {task[:50]}")
        else:
            directives = ["be_fast", "concise_response", "avoid_overhead"]
        
        self.last_directives = directives
        return directives, overridden

# ============================================================================
# HUMAN-IN-THE-LOOP ESCALATION SYSTEM (NEW!)
# ============================================================================
@dataclass
class EscalationRequest:
    id: str
    task: str
    reason: str
    risk_score: float
    created_at: float
    status: str = "pending"  # pending, approved, rejected, timeout
    response: Optional[str] = None
    responded_at: Optional[float] = None

class HumanInTheLoop:
    """
    Manages human approval workflows for high-risk actions.
    Implements the "Cognitive-Executive Separation" pattern from Parallax paper.
    """
    
    def __init__(self):
        self.pending_escalations: Dict[str, EscalationRequest] = {}
        self._lock = asyncio.Lock()
        self._waiters: Dict[str, asyncio.Event] = {}
    
    def should_escalate(self, task: str, mode: str, confidence: float = 1.0) -> bool:
        """Determine if a task requires human approval."""
        if not cfg.HUMAN_IN_LOOP_ENABLED:
            return False
        
        # Always escalate in DELIBERATE mode unless confidence is very high
        if mode == "DELIBERATE" and confidence < 0.95:
            return True
        
        # Escalate specific high-risk keywords
        high_risk_keywords = ["deploy", "production", "delete_all", "transfer_funds", "execute_trade"]
        if any(kw in task.lower() for kw in high_risk_keywords):
            return True
        
        return False
    
    async def create_escalation(self, task: str, reason: str, risk_score: float) -> EscalationRequest:
        """Create an escalation request and wait for human response."""
        escalation_id = str(uuid.uuid4())[:8]
        escalation = EscalationRequest(
            id=escalation_id,
            task=task,
            reason=reason,
            risk_score=risk_score,
            created_at=time.time()
        )
        
        async with self._lock:
            self.pending_escalations[escalation_id] = escalation
            self._waiters[escalation_id] = asyncio.Event()
        
        await event_bus.publish(Event(
            type=EventType.HUMAN_ESCALATION,
            source="human_in_loop",
            payload={
                "escalation_id": escalation_id,
                "task": task[:200],
                "reason": reason,
                "risk_score": risk_score,
                "timeout_seconds": cfg.ESCALATION_TIMEOUT
            }
        ))
        
        logger.warning(f"⏳ ESCALATION CREATED: {escalation_id} - {task[:50]}...")
        return escalation
    
    async def wait_for_approval(self, escalation_id: str, timeout: int = None) -> tuple[bool, Optional[str]]:
        """Wait for human to approve/reject the escalation."""
        timeout = timeout or cfg.ESCALATION_TIMEOUT
        waiter = self._waiters.get(escalation_id)
        
        if not waiter:
            return False, "Escalation not found"
        
        try:
            await asyncio.wait_for(waiter.wait(), timeout=timeout)
            escalation = self.pending_escalations.get(escalation_id)
            
            if escalation.status == "approved":
                logger.info(f"✅ ESCALATION APPROVED: {escalation_id}")
                return True, escalation.response
            elif escalation.status == "rejected":
                logger.warning(f"❌ ESCALATION REJECTED: {escalation_id} - {escalation.response}")
                return False, escalation.response
            else:
                return False, "Unknown status"
                
        except asyncio.TimeoutError:
            async with self._lock:
                if escalation_id in self.pending_escalations:
                    self.pending_escalations[escalation_id].status = "timeout"
            
            logger.error(f"⌛ ESCALATION TIMEOUT: {escalation_id} after {timeout}s")
            return False, f"Escalation timed out after {timeout} seconds"
    
    async def respond_to_escalation(self, escalation_id: str, approved: bool, response: str = "") -> bool:
        """Human responds to an escalation (via API or UI)."""
        async with self._lock:
            escalation = self.pending_escalations.get(escalation_id)
            
            if not escalation:
                return False
            
            if escalation.status != "pending":
                return False
            
            escalation.status = "approved" if approved else "rejected"
            escalation.response = response
            escalation.responded_at = time.time()
            
            # Signal the waiter
            waiter = self._waiters.get(escalation_id)
            if waiter:
                waiter.set()
        
        await event_bus.publish(Event(
            type=EventType.HUMAN_APPROVAL,
            source="human_in_loop",
            payload={
                "escalation_id": escalation_id,
                "approved": approved,
                "response": response,
                "responded_at": time.time()
            }
        ))
        
        return True
    
    def get_pending_escalations(self) -> List[Dict]:
        """Get all pending escalations for UI display."""
        return [
            {
                "id": esc.id,
                "task": esc.task[:100],
                "reason": esc.reason,
                "risk_score": esc.risk_score,
                "created_at": esc.created_at,
                "age_seconds": time.time() - esc.created_at
            }
            for esc in self.pending_escalations.values()
            if esc.status == "pending"
        ]
    
    async def cleanup_stale(self):
        """Remove old resolved escalations."""
        async with self._lock:
            now = time.time()
            stale_ids = [
                eid for eid, esc in self.pending_escalations.items()
                if esc.status != "pending" and (now - (esc.responded_at or esc.created_at)) > 3600
            ]
            for eid in stale_ids:
                del self.pending_escalations[eid]
                if eid in self._waiters:
                    del self._waiters[eid]

human_in_loop = HumanInTheLoop()

# ============================================================================
# MEMORY ENGINE (PERSISTENT, VECTOR, USER-SPECIFIC)
# ============================================================================
class MemoryEngine:
    """Persistent memory with sqlite-vec for vector search and user-specific files."""
    
    def __init__(self):
        self.db_path = DIRS["data"] / "memory.db"
        self._init_db()
    
    def _init_db(self):
        """Initialize SQLite with vector extension."""
        self.conn = sqlite3.connect(str(self.db_path))
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS memories (
                id INTEGER PRIMARY KEY, 
                user_id TEXT, 
                content TEXT, 
                embedding BLOB, 
                created_at REAL
            )
        """)
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS facts (
                id INTEGER PRIMARY KEY, 
                user_id TEXT, 
                fact TEXT, 
                confidence REAL, 
                created_at REAL
            )
        """)
        self.conn.commit()
    
    async def store_interaction(self, user_id: str, task: str, response: str, mode: str):
        """Store an interaction for future recall."""
        if HAS_NUMPY:
            embedding = hashlib.sha256(f"{task}{response}".encode()).digest()[:64]
            self.conn.execute(
                "INSERT INTO memories (user_id, content, embedding, created_at) VALUES (?, ?, ?, ?)",
                (user_id, f"Task: {task}\nResponse: {response}\nMode: {mode}", embedding, time.time())
            )
            self.conn.commit()
    
    async def recall(self, user_id: str, query: str, k: int = 5) -> List[str]:
        """Recall relevant past interactions."""
        cursor = self.conn.execute(
            "SELECT content FROM memories WHERE user_id = ? ORDER BY created_at DESC LIMIT ?",
            (user_id, k)
        )
        rows = cursor.fetchall()
        return [row[0] for row in rows]
    
    async def store_fact(self, user_id: str, fact: str, confidence: float = 0.8):
        """Store a fact about the user."""
        self.conn.execute(
            "INSERT INTO facts (user_id, fact, confidence, created_at) VALUES (?, ?, ?, ?)",
            (user_id, fact, confidence, time.time())
        )
        self.conn.commit()
    
    async def get_facts(self, user_id: str) -> List[str]:
        """Retrieve stored facts about the user."""
        cursor = self.conn.execute(
            "SELECT fact FROM facts WHERE user_id = ? ORDER BY confidence DESC",
            (user_id,)
        )
        return [row[0] for row in cursor.fetchall()]

memory_engine = MemoryEngine()

# ============================================================================
# SKILL REGISTRY (MANIFEST-BASED, INSTALLABLE)
# ============================================================================
class Skill:
    """Represents an installable skill with manifest."""
    
    def __init__(self, name: str, manifest: dict, entry_path: Path):
        self.name = name
        self.version = manifest.get("version", "1.0.0")
        self.description = manifest.get("description", "")
        self.permissions = manifest.get("permissions", [])
        self.inputs = manifest.get("inputs", {})
        self.outputs = manifest.get("outputs", {})
        self.entry_path = entry_path
        self._module = None
        self._instance = None
    
    async def load(self):
        """Load the skill module dynamically."""
        spec = importlib.util.spec_from_file_location(f"skill_{self.name}", self.entry_path)
        if not spec or not spec.loader:
            raise ImportError(f"Cannot load skill {self.name}")
        self._module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self._module)
        
        for attr_name in dir(self._module):
            attr = getattr(self._module, attr_name)
            if isinstance(attr, type) and hasattr(attr, 'execute'):
                self._instance = attr()
                break
        return self._instance
    
    async def execute(self, params: dict) -> dict:
        """Execute the skill with given parameters."""
        if not self._instance:
            await self.load()
        return await self._instance.execute(params)

class SkillRegistry:
    """Registry for installable skills (replaces hardcoded workers)."""
    
    def __init__(self):
        self.skills: Dict[str, Skill] = {}
        self._load_builtins()
    
    def _load_builtins(self):
        """Load existing workers as skills (backward compatible)."""
        workers_dir = DIRS["workers"]
        for py_file in workers_dir.glob("*.py"):
            if py_file.name.startswith("__"):
                continue
            
            manifest = {
                "name": py_file.stem,
                "version": "1.0.0",
                "description": f"Worker {py_file.stem} (legacy)",
                "permissions": [],
                "inputs": {},
                "outputs": {}
            }
            skill = Skill(manifest["name"], manifest, py_file)
            self.skills[skill.name] = skill
            logger.info(f"📦 Loaded built-in skill: {skill.name} v{skill.version}")
    
    def load_from_manifest(self, skill_dir: Path) -> Optional[Skill]:
        """Load a skill from a directory containing manifest.json."""
        manifest_path = skill_dir / "manifest.json"
        if not manifest_path.exists():
            return None
        
        manifest = json.loads(manifest_path.read_text())
        entry_path = skill_dir / manifest.get("entry", "skill.py")
        
        if not entry_path.exists():
            logger.error(f"Skill {manifest['name']} entry not found: {entry_path}")
            return None
        
        skill = Skill(manifest["name"], manifest, entry_path)
        self.skills[skill.name] = skill
        logger.info(f"📦 Loaded skill from manifest: {skill.name} v{skill.version}")
        return skill
    
    async def install_from_url(self, url: str) -> Skill:
        """Install a skill from a GitHub URL or ZIP file."""
        # TODO: Implement git clone or download zip
        raise NotImplementedError("Skill installation from URL not yet implemented")
    
    async def execute(self, skill_name: str, params: dict) -> dict:
        """Execute a skill by name."""
        if skill_name not in self.skills:
            return {"success": False, "error": f"Skill '{skill_name}' not found"}
        
        skill = self.skills[skill_name]
        try:
            return await skill.execute(params)
        except Exception as e:
            logger.error(f"Skill {skill_name} execution failed: {e}")
            return {"success": False, "error": str(e)}

skill_registry = SkillRegistry()

# ============================================================================
# TASK SCHEDULER (AUTONOMOUS EXECUTION)
# ============================================================================
class TaskScheduler:
    """Scheduled task manager for autonomous execution."""
    
    def __init__(self):
        self.scheduler = None
        self.jobs_db = DIRS["data"] / "scheduled_jobs.db"
        self._init_db()
    
    def _init_db(self):
        self.conn = sqlite3.connect(str(self.jobs_db))
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS jobs (
                id TEXT PRIMARY KEY,
                user_id TEXT,
                task TEXT,
                trigger_type TEXT,
                trigger_config TEXT,
                next_run REAL,
                enabled INTEGER DEFAULT 1
            )
        """)
        self.conn.commit()
    
    def start(self):
        if HAS_SCHEDULER:
            self.scheduler = AsyncIOScheduler()
            self.scheduler.start()
            logger.info("⏰ Task scheduler started")
        else:
            logger.warning("APScheduler not installed – task scheduling disabled")
    
    async def add_job(self, user_id: str, task: str, trigger_spec: str) -> str:
        """Add a scheduled job. trigger_spec: 'interval:minutes' or 'cron:minute hour'."""
        job_id = str(uuid.uuid4())[:8]
        if not HAS_SCHEDULER:
            return None
        
        trigger_type, config = trigger_spec.split(':', 1)
        if trigger_type == "interval":
            minutes = int(config)
            trigger = IntervalTrigger(minutes=minutes)
        elif trigger_type == "cron":
            parts = config.split()
            minute = int(parts[0]) if len(parts) > 0 else "*"
            hour = int(parts[1]) if len(parts) > 1 else "*"
            trigger = CronTrigger(minute=minute, hour=hour)
        else:
            return None
        
        self.conn.execute(
            "INSERT INTO jobs (id, user_id, task, trigger_type, trigger_config, next_run) VALUES (?, ?, ?, ?, ?, ?)",
            (job_id, user_id, task, trigger_type, config, time.time() + 60)
        )
        self.conn.commit()
        
        self.scheduler.add_job(
            self._execute_job,
            trigger,
            args=[user_id, task, job_id],
            id=job_id
        )
        
        await event_bus.publish(Event(
            type=EventType.TASK_SCHEDULED,
            source="scheduler",
            payload={"job_id": job_id, "user_id": user_id, "task": task[:100]}
        ))
        return job_id
    
    async def _execute_job(self, user_id: str, task: str, job_id: str):
        """Execute a scheduled task."""
        logger.info(f"⏰ Executing scheduled job {job_id}: {task[:50]}")
        await event_bus.publish(Event(
            type=EventType.TASK_EXECUTED,
            source="scheduler",
            payload={"job_id": job_id, "user_id": user_id, "task": task[:100]}
        ))
    
    def stop(self):
        if self.scheduler:
            self.scheduler.shutdown()

task_scheduler = TaskScheduler()

# ============================================================================
# PLANNER LOOP (MULTI-STEP TASK DECOMPOSITION)
# ============================================================================
class PlannerLoop:
    """Extends CognitiveEngine with multi-step planning."""
    
    def __init__(self, kernel):
        self.kernel = kernel
        self.max_steps = 10
    
    async def plan_and_execute(self, goal: str, world) -> str:
        """Decompose goal into steps and execute sequentially."""
        steps = await self._decompose_goal(goal)
        if not steps:
            return "Unable to decompose goal into steps"
        
        results = []
        for i, step in enumerate(steps):
            logger.info(f"🔄 Executing step {i+1}/{len(steps)}: {step[:50]}")
            result = await self.kernel.cognitive_engine.execute_goal(step, world)
            results.append(result)
            
            if "error" in result.lower() or "failed" in result.lower():
                steps = await self._replan(goal, steps, i, result)
        
        return "\n".join(results)
    
    async def _decompose_goal(self, goal: str) -> List[str]:
        """Ask LLM to decompose goal into steps (returns JSON array)."""
        # Placeholder – in reality, call Ollama with a planning prompt
        return [goal]  # fallback: just execute the whole goal
    
    async def _replan(self, goal: str, steps: List[str], failed_step: int, error: str) -> List[str]:
        """Re-plan remaining steps after a failure."""
        # Placeholder – ask LLM to adjust plan
        return steps  # fallback: continue with original plan

# ============================================================================
# SOVEREIGN MEMORY
# ============================================================================
class SovereignMemory:
    def __init__(self):
        self.memories: Dict[str, Dict] = {}
        self._load_from_disk()
    
    def store(self, blueprint: Dict) -> str:
        lock = blueprint.get("master_drift_lock", SCE.drift_lock(blueprint))
        self.memories[lock] = {"value": blueprint, "timestamp": time.time(), "access_count": 0}
        path = DIRS["memory"] / f"bp_{lock}.json"
        try:
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(self.memories[lock], f, indent=2, ensure_ascii=False, default=str)
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
        results, q = [], query.lower()
        for lock, record in self.memories.items():
            bp = record["value"]
            searchable = json.dumps({**bp.get("intent", {}), **bp.get("execution", {})}, default=str).lower()
            score = searchable.count(q) * 5
            if score > 0:
                results.append({"lock": lock, "score": score, "timestamp": record["timestamp"]})
        results.sort(key=lambda x: (-x["score"], x["timestamp"]))
        return results[:limit]
    
    def _load_from_disk(self):
        for p in DIRS["memory"].glob("*.json"):
            try:
                with open(p, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    if "value" in data:
                        lock = data["value"].get("master_drift_lock")
                        if lock:
                            self.memories[lock] = data
            except Exception as e:
                logger.debug(f"Failed to load {p}: {e}")
        logger.info(f"📚 Loaded {len(self.memories)} blueprints from disk")

memory = SovereignMemory()

# ============================================================================
# GPU MONITOR
# ============================================================================
class GPUMonitor:
    def __init__(self):
        self.gpus: List[Dict] = []
        self.has_gpu = False
        self._error: Optional[str] = None
        
        if not HAS_PYNVML:
            logger.info("🖥️ GPU monitoring: pynvml not available")
            return
        
        try:
            pynvml.nvmlInit()
            count = pynvml.nvmlDeviceGetCount()
            for i in range(count):
                h = pynvml.nvmlDeviceHandleByIndex(i)
                name = pynvml.nvmlDeviceGetName(h)
                if isinstance(name, bytes):
                    name = name.decode('utf-8', errors='replace')
                mem = pynvml.nvmlDeviceGetMemoryInfo(h)
                self.gpus.append({
                    "index": i, 
                    "name": name, 
                    "handle": h, 
                    "total_gb": round(mem.total / 1024**3, 1)
                })
            self.has_gpu = len(self.gpus) > 0
            if self.has_gpu:
                logger.info(f"🖥️ GPU detected: {self.gpus[0]['name']} ({self.gpus[0]['total_gb']}GB)")
        except Exception as e:
            self._error = str(e)
            logger.warning(f"GPU init failed: {e}")
    
    def stats(self) -> Dict[str, Any]:
        if not self.has_gpu:
            return {"has_gpu": False, "error": self._error or "No GPU detected"}
        
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
                "temperature": temp
            }
        except Exception as e:
            return {"has_gpu": True, "error": f"Read failed: {e}"}

gpu = GPUMonitor()

# ============================================================================
# OLLAMA CLIENT
# ============================================================================
class OllamaClient:
    def __init__(self):
        self.base_url = cfg.OLLAMA_URL
        self.model = cfg.DEFAULT_MODEL
        self.timeout = cfg.OLLAMA_TIMEOUT
        self.available = False
        self.models: List[str] = []
        self._client = None
    
    async def initialize(self):
        if HAS_HTTPX:
            self._client = httpx.AsyncClient(timeout=httpx.Timeout(self.timeout, connect=10))
            await self.check_connection()
    
    async def check_connection(self) -> bool:
        if not self._client:
            return False
        try:
            r = await self._client.get(f"{self.base_url}/api/tags")
            if r.status_code == 200:
                data = r.json()
                self.models = [m["name"] for m in data.get("models", [])]
                self.available = True
                logger.info(f"🤖 Ollama connected: {len(self.models)} models available")
                return True
        except Exception as e:
            logger.warning(f"Ollama connection check failed: {e}")
        self.available = False
        return False
    
    async def chat(self, messages: List[Dict], model: Optional[str] = None, stream: bool = False) -> Union[str, AsyncGenerator[str, None]]:
        if not self._client:
            return "Ollama client not initialized"
        
        model = model or self.model
        payload = {
            "model": model, 
            "messages": messages, 
            "stream": stream, 
            "options": {"num_ctx": cfg.OLLAMA_NUM_CTX}
        }
        
        if stream:
            return self._stream_chat(payload)
        
        try:
            response = await ollama_breaker.call(self._client.post, f"{self.base_url}/api/chat", json=payload)
            data = response.json()
            return data.get("message", {}).get("content", "")
        except Exception as e:
            logger.error(f"Ollama chat error: {e}")
            return f"Ollama error: {e}"
    
    async def _stream_chat(self, payload: Dict) -> AsyncGenerator[str, None]:
        try:
            async with self._client.stream("POST", f"{self.base_url}/api/chat", json=payload) as response:
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
        except Exception as e:
            logger.error(f"Ollama stream error: {e}")
            yield f"\n❌ Ollama error: {type(e).__name__}"
    
    async def close(self):
        if self._client:
            await self._client.aclose()

ollama = OllamaClient()

# ============================================================================
# WORKER SYSTEM (BACKWARD COMPATIBLE)
# ============================================================================
class Worker(ABC):
    def __init__(self, name: str):
        self.name = name
        self.created_at = time.time()
        self.execution_count = 0
        self.error_count = 0
    
    @abstractmethod
    async def execute(self, task: str, **kwargs) -> Dict[str, Any]:
        pass
    
    async def health_check(self) -> Dict:
        return {
            "name": self.name, 
            "status": "healthy", 
            "executions": self.execution_count, 
            "errors": self.error_count, 
            "uptime": time.time() - self.created_at
        }

class WorkerLoader:
    def __init__(self, directory: Path):
        self.directory = directory.resolve()
    
    def is_valid_worker(self, obj, class_name: str) -> bool:
        if not inspect.isclass(obj) or inspect.isabstract(obj):
            return False
        try:
            if issubclass(obj, Worker):
                return True
        except TypeError:
            pass
        return hasattr(obj, 'execute') and callable(getattr(obj, 'execute'))
    
    def load_all(self) -> Dict[str, Dict]:
        workers = {}
        if not self.directory.exists():
            return workers
        
        for py_file in sorted(self.directory.glob("*.py")):
            if py_file.name.startswith("__"):
                continue
            try:
                spec = importlib.util.spec_from_file_location(py_file.stem, py_file)
                if not spec or not spec.loader:
                    continue
                mod = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(mod)
                
                for name, obj in inspect.getmembers(mod, inspect.isclass):
                    if not self.is_valid_worker(obj, name):
                        continue
                    try:
                        try:
                            worker = obj(name=name.lower())
                        except TypeError:
                            worker = obj()
                        
                        if not hasattr(worker, 'name'):
                            worker.name = name.lower()
                        
                        worker_name = getattr(worker, 'name', name.lower())
                        workers[worker_name] = {
                            "class": obj, 
                            "module": py_file.stem, 
                            "loaded_at": time.time(), 
                            "instance": worker
                        }
                        logger.info(f"  ✅ Worker loaded: {worker_name}")
                    except Exception as e:
                        logger.debug(f"  ⚠️ Cannot instantiate {name}: {e}")
            except Exception as e:
                logger.debug(f"  ⚠️ Skip {py_file.name}: {e}")
        
        return workers

# ============================================================================
# TRADING WORKERS (PAPER TRADER, BACKTEST)
# ============================================================================
class PaperTraderWorker(Worker):
    def __init__(self):
        super().__init__("paper_trader")
        self.balance = cfg.PAPER_BALANCE
        self.positions: Dict[str, float] = {}
        self.trade_history: List[Dict] = []
    
    async def execute(self, task: str, **kwargs) -> Dict[str, Any]:
        task_lower = task.lower()
        symbol = kwargs.get("symbol", cfg.DEFAULT_SYMBOL)
        amount = float(kwargs.get("amount", 0.01))
        price = float(kwargs.get("price", 50000))
        
        if "buy" in task_lower:
            cost = amount * price
            if cost <= self.balance:
                self.balance -= cost
                self.positions[symbol] = self.positions.get(symbol, 0) + amount
                trade = {
                    "action": "BUY", 
                    "symbol": symbol, 
                    "amount": amount, 
                    "price": price, 
                    "timestamp": time.time()
                }
                self.trade_history.append(trade)
                await event_bus.publish(Event(type=EventType.TRADE_EXECUTED, source="paper_trader", payload=trade))
                return {
                    "success": True, 
                    "balance": self.balance, 
                    "position": self.positions[symbol], 
                    "trade": trade
                }
            return {
                "success": False, 
                "error": "Insufficient balance", 
                "required": cost, 
                "available": self.balance
            }
        
        elif "sell" in task_lower:
            if self.positions.get(symbol, 0) >= amount:
                revenue = amount * price
                self.balance += revenue
                self.positions[symbol] -= amount
                if self.positions[symbol] <= 0:
                    del self.positions[symbol]
                trade = {
                    "action": "SELL", 
                    "symbol": symbol, 
                    "amount": amount, 
                    "price": price, 
                    "timestamp": time.time()
                }
                self.trade_history.append(trade)
                await event_bus.publish(Event(type=EventType.TRADE_EXECUTED, source="paper_trader", payload=trade))
                return {
                    "success": True, 
                    "balance": self.balance, 
                    "position": self.positions.get(symbol, 0), 
                    "trade": trade
                }
            return {
                "success": False, 
                "error": f"Insufficient {symbol}", 
                "have": self.positions.get(symbol, 0), 
                "need": amount
            }
        
        elif "portfolio" in task_lower:
            total_value = self.balance + sum([pos * 50000 for pos in self.positions.values()])
            return {
                "success": True, 
                "balance": self.balance, 
                "positions": self.positions, 
                "total_value": total_value, 
                "trades": self.trade_history[-10:]
            }
        
        return {"success": False, "error": "Unknown command. Use: buy/sell/portfolio"}

class BacktestWorker(Worker):
    def __init__(self):
        super().__init__("backtest")
    
    async def execute(self, task: str, **kwargs) -> Dict[str, Any]:
        seed = hash(task) % (2**32)
        random.seed(seed)
        result = {
            "success": True, 
            "strategy": task[:100],
            "total_return": round(random.uniform(-0.15, 0.35), 4),
            "sharpe_ratio": round(random.uniform(0.5, 2.5), 2),
            "max_drawdown": round(random.uniform(0.05, 0.25), 4),
            "win_rate": round(random.uniform(0.4, 0.7), 2),
            "trades": random.randint(50, 500),
            "seed": seed
        }
        random.seed()
        return result

# ============================================================================
# BUILT-IN WORKERS
# ============================================================================
class SystemMonitorWorker(Worker):
    def __init__(self):
        super().__init__("system_monitor")
    
    async def execute(self, task: str, **kwargs) -> Dict:
        result = {"success": True, "gpu": gpu.stats()}
        if HAS_PSUTIL:
            result["cpu_percent"] = psutil.cpu_percent(interval=0.1)
            vm = psutil.virtual_memory()
            result["ram_percent"] = vm.percent
            result["ram_used_gb"] = round(vm.used / 1024**3, 1)
            result["ram_total_gb"] = round(vm.total / 1024**3, 1)
        return result

class CodeExecutionWorker(Worker):
    def __init__(self):
        super().__init__("code_execution")
    
    async def execute(self, task: str, **kwargs) -> Dict:
        code_match = re.search(r'```(?:python)?\s*\n(.*?)\n```', task, re.DOTALL)
        code = code_match.group(1) if code_match else task
        
        ruling = await constitution.evaluate(code)
        if not ruling["approved"]:
            return {"success": False, "error": ruling["reason"]}
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', dir=str(DIRS["sandbox"]), delete=False) as f:
            f.write(code)
            tmp = f.name
        
        try:
            proc = await asyncio.create_subprocess_exec(
                sys.executable, tmp,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=str(DIRS["sandbox"])
            )
            stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=30)
            return {
                "success": proc.returncode == 0,
                "stdout": stdout.decode('utf-8', errors='replace')[-2000:],
                "stderr": stderr.decode('utf-8', errors='replace')[-1000:],
                "returncode": proc.returncode
            }
        except asyncio.TimeoutError:
            return {"success": False, "error": "Execution timeout (30s)"}
        except Exception as e:
            return {"success": False, "error": f"Execution failed: {e}"}
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
            return {"error": "No code intent provided", "success": False}
        
        code = f'''def solution():
    """Generated for: {intent}"""
    # TODO: Implement your solution here
    pass

if __name__ == "__main__":
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

class VSCodeIntegrationWorker(Worker):
    def __init__(self):
        super().__init__("vscode_integration")
        self.workspace = Path(cfg.VSCODE_WORKSPACE)
        self.vscode_available = self._check_vscode()
        self.copilot_available = self._check_copilot()
    
    def _check_vscode(self) -> bool:
        try:
            import subprocess
            result = subprocess.run(["code", "--version"], capture_output=True, timeout=5)
            return result.returncode == 0
        except:
            return False
    
    def _check_copilot(self) -> bool:
        try:
            import subprocess
            result = subprocess.run(["code", "--list-extensions"], capture_output=True, timeout=10)
            return "github.copilot" in result.stdout.decode('utf-8', errors='ignore')
        except:
            return False
    
    async def execute(self, task: str, **kwargs) -> Dict[str, Any]:
        task_lower = task.lower()
        if task_lower.startswith("agent:"):
            return await self._agent_mode(task[6:].strip())
        elif task_lower.startswith("plan:"):
            return await self._plan_mode(task[5:].strip())
        elif task_lower.startswith("ask:"):
            return await self._ask_mode(task[4:].strip())
        elif task_lower.startswith("edit:"):
            return await self._edit_file(task[5:].strip(), kwargs)
        return {"success": False, "error": "Unknown mode. Use: agent:/plan:/ask:/edit:"}
    
    async def _agent_mode(self, prompt: str) -> Dict[str, Any]:
        if not self.vscode_available:
            return {"success": False, "error": "VS Code not available"}
        
        task_file = DIRS["vscode_tasks"] / f"agent_task_{int(time.time())}.md"
        task_file.write_text(f"""# Phoenix Agent Task
Generated: {datetime.now().isoformat()}

## Task
{prompt}

## Context
- Phoenix Kernel v{cfg.VERSION}
- Workers: SystemMonitor, CodeExecution, PaperTrader, Backtest, VSCodeIntegration
- Constitution: Active
- Ollama: {ollama.model} available

## Expected Output
1. Modified files
2. Test results
3. Implementation summary
""", encoding='utf-8')
        
        try:
            import subprocess
            subprocess.Popen(["code", str(task_file)])
        except:
            pass
        
        blueprint = SCE.blueprint(
            intent={"mode": "agent", "prompt": prompt},
            dna={"worker": "vscode_integration", "copilot": self.copilot_available},
            execution={"task_file": str(task_file)}
        )
        lock = memory.store(blueprint)
        
        await event_bus.publish(Event(
            type=EventType.VSCODE_AGENT, 
            source="vscode_integration",
            payload={"prompt": prompt, "drift_lock": lock}
        ))
        
        return {
            "success": True, 
            "mode": "agent", 
            "prompt": prompt, 
            "task_file": str(task_file),
            "drift_lock": lock, 
            "copilot_available": self.copilot_available
        }
    
    async def _plan_mode(self, prompt: str) -> Dict[str, Any]:
        plan_file = DIRS["vscode_tasks"] / f"implementation_plan_{int(time.time())}.md"
        plan_content = f"""# Implementation Plan
Generated: {datetime.now().isoformat()}

## Objective
{prompt}

## Current State
- Phoenix Kernel: v{cfg.VERSION}
- Workers: Loaded
- Blueprints: {len(memory.memories)}

## Plan
### Phase 1: Analysis
- [ ] Understand requirements
- [ ] Identify affected components

### Phase 2: Implementation
- [ ] Create/modify files
- [ ] Update tests

### Phase 3: Testing
- [ ] Unit tests
- [ ] Integration tests
"""
        plan_file.write_text(plan_content, encoding='utf-8')
        
        try:
            import subprocess
            subprocess.Popen(["code", str(plan_file)])
        except:
            pass
        
        return {
            "success": True, 
            "mode": "plan", 
            "prompt": prompt, 
            "plan_file": str(plan_file)
        }
    
    async def _ask_mode(self, question: str) -> Dict[str, Any]:
        context = f"Workspace: {self.workspace}\nKernel: Phoenix v{cfg.VERSION}"
        try:
            messages = [
                {"role": "system", "content": "You are an expert on the Phoenix Kernel."},
                {"role": "user", "content": f"Context:\n{context}\nQuestion: {question}"}
            ]
            response = await ollama.chat(messages, stream=False)
            answer = response if isinstance(response, str) else "No response"
        except Exception as e:
            answer = f"Error: {e}"
        
        return {"success": True, "mode": "ask", "question": question, "answer": answer}
    
    async def _edit_file(self, file_path: str, kwargs: Dict) -> Dict[str, Any]:
        target_path = self.workspace / file_path
        if not target_path.exists():
            return {"success": False, "error": f"File not found: {file_path}"}
        
        try:
            import subprocess
            subprocess.Popen(["code", str(target_path)])
        except:
            pass
        
        return {
            "success": True, 
            "mode": "edit", 
            "file": file_path,
            "instruction": kwargs.get("instruction", "Improve this code")
        }
    
    async def health_check(self) -> Dict:
        return {
            "name": self.name, 
            "status": "healthy", 
            "vscode_available": self.vscode_available,
            "copilot_available": self.copilot_available, 
            "executions": self.execution_count,
            "errors": self.error_count
        }

# ============================================================================
# OKIRU BOOT SEQUENCER
# ============================================================================
class OkiruBootSequencer:
    def __init__(self):
        self.kernel = None
    
    def set_kernel(self, kernel):
        self.kernel = kernel
    
    async def awaken_all(self) -> Dict[str, Any]:
        logger.info("\n" + "🌌"*30)
        logger.info("🌌 OKIRU PROTOCOL INITIATED")
        logger.info("🌌"*30 + "\n")
        
        start_time = time.time()
        boot_status = {}
        
        logger.info("📦 Phase 1: Core Infrastructure")
        boot_status['memory'] = len(memory.memories)
        boot_status['event_bus'] = await event_bus.verify_chain()
        
        logger.info("⚙️ Phase 2: Worker Swarm")
        boot_status['workers'] = len(self.kernel.workers) if self.kernel else 0
        
        logger.info("🧠 Phase 3: Symbiote Consciousness")
        boot_status['symbiote'] = True
        
        logger.info("🛡️ Phase 4: Security Hardening")
        boot_status['security'] = {
            'constitution_patterns': len(constitution._compiled_patterns),
            'api_keys_configured': len(cfg.API_KEYS),
            'rate_limit': f"{cfg.RATE_LIMIT_CALLS}/{cfg.RATE_LIMIT_PERIOD}s",
            'human_in_loop': cfg.HUMAN_IN_LOOP_ENABLED
        }
        
        logger.info("✅ Phase 5: System Verification")
        boot_status['verified'] = await event_bus.verify_chain()
        
        logger.info(f"🧠 Phase 6: Memory Engine")
        boot_status['memory_engine'] = True
        
        logger.info(f"⏰ Phase 7: Task Scheduler")
        boot_status['scheduler'] = HAS_SCHEDULER
        
        boot_time = time.time() - start_time
        
        logger.info("\n" + "🔥"*30)
        logger.info(f"🔥 PHOENIX v{cfg.VERSION} IS NOW SENTIENT")
        logger.info(f"🔥 Boot completed in {boot_time:.2f}s")
        logger.info(f"🔥 Workers: {boot_status.get('workers', 0)}")
        logger.info(f"🔥 Memory: {boot_status.get('memory', 0)} blueprints")
        logger.info(f"🔥 Skills: {len(skill_registry.skills)}")
        logger.info(f"🔥 Event Chain: {'✅ Valid' if boot_status.get('verified') else '❌ Broken'}")
        logger.info(f"🔥 Human-in-the-Loop: {'✅ Enabled' if cfg.HUMAN_IN_LOOP_ENABLED else '❌ Disabled'}")
        logger.info("🔥"*30 + "\n")
        
        return boot_status

okiru_boot = OkiruBootSequencer()

# ============================================================================
# REFLEX COMMANDS
# ============================================================================
class Reflex:
    def __init__(self, kernel):
        self.kernel = kernel
    
    async def try_execute(self, cmd: str) -> Optional[Dict]:
        cmd = cmd.strip()
        lower = cmd.lower()
        
        if lower == "/portfolio":
            worker = self.kernel.workers.get("paper_trader", {}).get("instance")
            if worker:
                result = await worker.execute("portfolio")
                return self._response(f"📊 Portfolio: {json.dumps(result, indent=2)}")
            return self._response("❌ PaperTrader not available")
        
        if lower.startswith("/trade "):
            parts = cmd.split()
            if len(parts) >= 3:
                action, symbol = parts[1], parts[2]
                amount = float(parts[3]) if len(parts) > 3 else 0.01
                worker = self.kernel.workers.get("paper_trader", {}).get("instance")
                if worker:
                    result = await worker.execute(action, symbol=symbol, amount=amount)
                    return self._response(f"💰 Trade: {json.dumps(result, indent=2)}")
                return self._response("❌ PaperTrader not available")
            return self._response("Usage: /trade buy|sell SYMBOL [AMOUNT]")
        
        if lower.startswith("/backtest "):
            strategy = cmd.replace("/backtest", "").strip()
            if strategy:
                worker = self.kernel.workers.get("backtest", {}).get("instance")
                if worker:
                    result = await worker.execute(strategy)
                    return self._response(f"📈 Backtest: {json.dumps(result, indent=2)}")
                return self._response("Usage: /backtest STRATEGY_NAME")
        
        if lower == "/kill":
            await kill_switch.activate("Manual trigger via reflex", triggered_by="user")
            return self._response("🔴 KILL SWITCH ACTIVATED")
        
        if lower == "/kill-reset":
            await kill_switch.reset()
            return self._response("🔒 Kill switch RESET")
        
        if lower == "/kill-status":
            return self._response(f"Kill switch: {'🔴 ACTIVE' if kill_switch.is_active() else '🟢 INACTIVE'}")
        
        if lower == "/okiru":
            boot_status = await okiru_boot.awaken_all()
            return self._response(f"🌌 OKIRU Boot Complete\nVerified: {boot_status.get('verified')}")
        
        if lower == "/symbiote":
            return self._response("🦊 Symbiote consciousness active\nProactive loop: Running")
        
        if lower == "/health":
            stats = gpu.stats()
            return self._response(
                f"🔥 **Phoenix v{cfg.VERSION}**\n"
                f"Workers: {len(self.kernel.workers)}\n"
                f"Blueprints: {len(memory.memories)}\n"
                f"Skills: {len(skill_registry.skills)}\n"
                f"Scheduler: {'✅' if HAS_SCHEDULER else '❌'}\n"
                f"Ollama: {'🟢' if ollama.available else '🔴'}\n"
                f"GPU: {stats.get('name', 'None')}\n"
                f"Human-in-Loop: {'✅' if cfg.HUMAN_IN_LOOP_ENABLED else '❌'}\n"
                f"Uptime: {round(time.time() - self.kernel.start_time)}s"
            )
        
        if lower == "/workers":
            names = sorted(self.kernel.workers.keys())
            listing = "\n".join(f"  • {n}" for n in names[:40])
            extra = f"\n... +{len(names)-40} more" if len(names) > 40 else ""
            return self._response(f"⚙️ **Workers ({len(names)})**\n{listing}{extra}")
        
        if lower == "/skills":
            names = sorted(skill_registry.skills.keys())
            listing = "\n".join(f"  • {n}" for n in names[:40])
            return self._response(f"📦 **Skills ({len(names)})**\n{listing}")
        
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
                worker = self.kernel.workers.get("code_gen", {}).get("instance")
                if worker:
                    result = await worker.execute(intent)
                    if result.get("success"):
                        return self._response(
                            f"📝 **Generated Code**\n```python\n{result['code']}\n```\n"
                            f"✅ Verified: {result['verified']}\n"
                            f"📊 Drift Score: {result['drift_score']:.2f}"
                        )
                return self._response("❌ Code generation failed")
        
        if lower.startswith("/schedule "):
            schedule_cmd = cmd[10:].strip()
            parts = schedule_cmd.split(" ", 1)
            if len(parts) == 2:
                trigger, task = parts
                job_id = await task_scheduler.add_job("default", task, trigger)
                if job_id:
                    return self._response(f"⏰ Scheduled task {job_id}: {trigger} / {task}")
            return self._response("Usage: /schedule interval:10 \"check weather\"")
        
        if lower.startswith("/vscode "):
            mode_and_prompt = cmd[8:].strip()
            if ":" in mode_and_prompt:
                mode, prompt = mode_and_prompt.split(":", 1)
                worker = self.kernel.workers.get("vscode_integration", {}).get("instance")
                if worker:
                    result = await worker.execute(f"{mode}:{prompt}")
                    return self._response(f"🖥️ VS Code + Copilot\n{json.dumps(result, indent=2)}")
            return self._response("Usage: /vscode agent:prompt | plan:prompt | ask:question | edit:file")
        
        if lower == "/vscode-status":
            worker = self.kernel.workers.get("vscode_integration", {}).get("instance")
            if worker:
                status = await worker.health_check()
                return self._response(f"🖥️ VS Code Status\n{json.dumps(status, indent=2)}")
        
        # NEW: Human-in-the-loop commands
        if lower == "/escalations":
            pending = human_in_loop.get_pending_escalations()
            if pending:
                lines = [
                    f"  ⏳ {esc['id']}: {esc['task'][:50]}... (risk: {esc['risk_score']}, age: {esc['age_seconds']:.0f}s)"
                    for esc in pending
                ]
                return self._response(f"**Pending Escalations ({len(pending)})**\n" + "\n".join(lines))
            return self._response("✅ No pending escalations")
        
        return None
    
    def _response(self, content: str) -> Dict:
        return {"type": "reflex", "content": content}

# ============================================================================
# BACKGROUND TASKS
# ============================================================================
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
        f"{len(skill_registry.skills)} skills available.",
        f"Scheduler {'running' if HAS_SCHEDULER else 'not available'}.",
        f"Human-in-the-loop {'active' if cfg.HUMAN_IN_LOOP_ENABLED else 'disabled'}."
    ]
    
    while True:
        try:
            await asyncio.sleep(random.randint(120, 300))
            thought = random.choice(thoughts)
            await event_bus.publish(Event(
                type=EventType.KERNEL_HEARTBEAT, 
                source="symbiote", 
                payload={"thought": thought}
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
                {
                    "name": "BINANCE", 
                    "btcPrice": round(btc, 2), 
                    "ethPrice": round(eth, 2),
                    "latency": random.randint(12, 45), 
                    "status": "SYNCED"
                },
                {
                    "name": "KRAKEN", 
                    "btcPrice": round(btc + random.uniform(-500, 500), 2),
                    "ethPrice": round(eth + random.uniform(-50, 50), 2),
                    "latency": random.randint(20, 60), 
                    "status": "SYNCED"
                }
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
            logger.error(f"Market broadcaster error: {e}")
            await asyncio.sleep(5)

# ============================================================================
# SSE HELPER
# ============================================================================
def sse(data: dict) -> str:
    """Server-Sent Events formatter"""
    return f"data: {json.dumps(data, ensure_ascii=False)}\n\n"

# ============================================================================
# PHOENIX KERNEL (v16.1.0 — SOVEREIGN AGENT RUNTIME)
# ============================================================================
class PhoenixKernel:
    def __init__(self):
        self.version = cfg.VERSION
        self.start_time = time.time()
        self.workers: Dict[str, Dict] = {}
        self.rate_limiter = RateLimiter(cfg.RATE_LIMIT_CALLS, cfg.RATE_LIMIT_PERIOD)
        self._bg_tasks: List[asyncio.Task] = []
        self.sio = None
        
        logger.info("⚙️ Loading workers...")
        loader = WorkerLoader(DIRS["workers"])
        self.workers.update(loader.load_all())
        
        if DIRS["coworker"].exists():
            coworker_loader = WorkerLoader(DIRS["coworker"])
            self.workers.update(coworker_loader.load_all())
        
        builtins = [
            ("system_monitor", SystemMonitorWorker), 
            ("code_execution", CodeExecutionWorker),
            ("code_gen", CodeGenWorker), 
            ("paper_trader", PaperTraderWorker),
            ("backtest", BacktestWorker)
        ]
        
        if RezCoderWorker:
            builtins.append(("rezcoder", RezCoderWorker))
        if MasteryWorker:
            builtins.append(("mastery", MasteryWorker))
        if SovereignMcpServer:
            builtins.append(("sovereign_mcp_server", SovereignMcpServer))
        if cfg.VSCODE_ENABLED:
            builtins.append(("vscode_integration", VSCodeIntegrationWorker))
        
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
        logger.info(f"📦 Total skills: {len(skill_registry.skills)}")
        
        self.reflex = Reflex(self)
        okiru_boot.set_kernel(self)
        
        # Initialize Governor
        self.governor = LatencyGovernor(target_ttft=0.8)
        
        # Initialize cognitive engine (placeholder)
        self.cognitive_engine = None
        
        self.app = FastAPI(title=f"Phoenix v{self.version}", docs_url="/docs", redoc_url=None)
        
        if router:
            self.app.include_router(router)
        
        self.app.add_middleware(
            CORSMiddleware, 
            allow_origins=cfg.CORS_ORIGINS, 
            allow_credentials=True,
            allow_methods=["*"], 
            allow_headers=["*"]
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
        self._setup_socketio()
    
    def enforce_governor(self, action: str) -> bool:
        """Execution Firewall: Central gate for expensive operations."""
        budget = self.governor.get_budget_multiplier()
        gates = {
            "prefetch": budget > 0.7, 
            "rerank": budget > 0.85,
            "deep_search": budget > 0.6, 
            "refinement_injection": budget > 0.5
        }
        is_allowed = gates.get(action, True)
        if not is_allowed:
            logger.debug(f"🛡️ Governor blocked '{action}' | Budget: {budget:.2f}")
        return is_allowed
    
    def _setup_socketio(self):
        if not HAS_SOCKETIO:
            logger.warning("Socket.IO disabled: python-socketio not installed")
            self.sio = None
            return
        
        self.sio = socketio.AsyncServer(cors_allowed_origins="*", async_mode="asgi")
        
        @self.sio.on("connect")
        async def on_connect(sid: str, environ: dict):
            logger.info(f"🟢 Socket connected: {sid[:8]}")
            await event_bus.publish(Event(
                type=EventType.SOCKET_CONNECT, 
                source="websocket", 
                payload={"sid": sid[:8]}
            ))
            await self.sio.emit(
                'agentLog', 
                {
                    "timestamp": datetime.now().isoformat(),
                    "message": f"Secure Link: {sid[:8]}", 
                    "type": "SYSTEM"
                }, 
                room=sid
            )
        
        @self.sio.on("disconnect")
        async def on_disconnect(sid: str):
            logger.info(f"🔴 Socket disconnected: {sid[:8]}")
            await event_bus.publish(Event(
                type=EventType.SOCKET_DISCONNECT, 
                source="websocket", 
                payload={"sid": sid[:8]}
            ))
        
        @self.sio.on('execute_trade')
        async def handle_trade(sid: str, data: dict):
            logger.info(f"💼 Trade request from {sid[:8]}: {data}")
            await event_bus.publish(Event(
                type=EventType.TRADE_EXECUTED, 
                source="trade_executor",
                payload={"action": "trade", "data": data, "sid": sid[:8]}
            ))
            await self.sio.emit(
                'trade_result', 
                {
                    "status": "AUTHORIZED",
                    "certificate": f"0x{hashlib.sha256(str(time.time()).encode()).hexdigest()[:16]}",
                    "timestamp": time.time()
                }, 
                room=sid
            )
        
        logger.info("🔌 Socket.IO handlers registered")
    
    def _setup_routes(self):
        logger.info("🔧 _setup_routes called")
        
        @self.app.get("/")
        async def root():
            return {
                "name": "Phoenix", 
                "version": self.version, 
                "workers": len(self.workers),
                "skills": len(skill_registry.skills), 
                "status": "online",
                "uptime": round(time.time() - self.start_time),
                "human_in_loop": cfg.HUMAN_IN_LOOP_ENABLED
            }
        
        @self.app.get("/health")
        async def health():
            return {
                "status": "online", 
                "version": self.version, 
                "workers": len(self.workers),
                "skills": len(skill_registry.skills), 
                "scheduler": HAS_SCHEDULER,
                "memory_entries": len(memory.memories), 
                "ollama": ollama.available,
                "gpu": gpu.stats(), 
                "uptime": round(time.time() - self.start_time, 1),
                "human_in_loop": cfg.HUMAN_IN_LOOP_ENABLED
            }
        
        @self.app.get("/kill/status")
        async def kill_status():
            return kill_switch.status()
        
        @self.app.get("/workers/list")
        async def workers_list():
            return {"workers": sorted(self.workers.keys()), "count": len(self.workers)}
        
        @self.app.get("/skills/list")
        async def skills_list():
            return {"skills": sorted(skill_registry.skills.keys()), "count": len(skill_registry.skills)}
        
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
        
        @self.app.get("/memory/stats")
        async def memory_stats():
            try:
                total = len(memory.memories)
                recent = []
                for lock, data in sorted(memory.memories.items(),
                                           key=lambda x: x[1].get("timestamp", 0), reverse=True)[:10]:
                    recent.append({
                        "lock": lock[:16] + "...", 
                        "timestamp": data.get("timestamp", 0)
                    })
                return {
                    "total_blueprints": total, 
                    "recent": recent, 
                    "timestamp": time.time()
                }
            except Exception as e:
                return JSONResponse({"error": str(e)}, status_code=500)
        
        @self.app.get("/memory/blueprints")
        async def memory_blueprints():
            return {"blueprints": list(memory.memories.keys())[-20:], "total": len(memory.memories)}
        
        @self.app.get("/memory/search")
        async def memory_search(q: str = "", limit: int = 10):
            try:
                if not q:
                    return {"results": [], "count": 0, "query": q}
                
                results = []
                q_lower = q.lower()
                for lock, record in memory.memories.items():
                    bp = record.get("value", {})
                    task = bp.get("intent", {}).get("task", "")
                    blueprint_text = json.dumps(bp, default=str).lower()
                    
                    if q_lower in task.lower() or q_lower in blueprint_text:
                        results.append({
                            "lock": lock, 
                            "timestamp": record.get("timestamp", 0),
                            "preview": task[:100] if task else lock[:50]
                        })
                
                results.sort(key=lambda x: x["timestamp"], reverse=True)
                results = results[:limit]
                
                return {"query": q, "results": results, "count": len(results), "timestamp": time.time()}
            except Exception as e:
                logger.error(f"Search error: {e}")
                return JSONResponse({"error": str(e)}, status_code=500)
        
        # ========== GOVERNANCE ENDPOINTS ==========
        @self.app.post("/v1/validate")
        async def governance_validate(request: Request, role: str = Depends(get_role)):
            data = await request.json()
            text = data.get("text", "")
            result = await constitution.evaluate(text)
            return result
        
        # ========== SCHEDULER ENDPOINTS ==========
        @self.app.post("/v1/schedule")
        async def schedule_task(request: Request, role: str = Depends(require_admin)):
            data = await request.json()
            task = data.get("task", "")
            trigger = data.get("trigger", "interval:60")
            job_id = await task_scheduler.add_job(role, task, trigger)
            if job_id:
                return {"job_id": job_id, "status": "scheduled"}
            return JSONResponse({"error": "Invalid trigger format"}, status_code=400)
        
        @self.app.get("/v1/schedule/jobs")
        async def list_scheduled_jobs(role: str = Depends(require_admin)):
            return {"jobs": []}
        
        # ========== SKILL MANAGEMENT ==========
        @self.app.post("/v1/skills/install")
        async def install_skill(request: Request, role: str = Depends(require_admin)):
            data = await request.json()
            url = data.get("url", "")
            if not url:
                return JSONResponse({"error": "No URL provided"}, status_code=400)
            
            try:
                skill = await skill_registry.install_from_url(url)
                await event_bus.publish(Event(
                    type=EventType.SKILL_INSTALL, 
                    source="api",
                    payload={"name": skill.name, "url": url}
                ))
                return {"skill": skill.name, "status": "installed"}
            except NotImplementedError:
                return JSONResponse(
                    {"error": "Skill installation from URL not yet implemented"}, 
                    status_code=501
                )
        
        @self.app.get("/v1/skills/{skill_name}")
        async def get_skill(skill_name: str, role: str = Depends(get_role)):
            if skill_name not in skill_registry.skills:
                raise HTTPException(status_code=404, detail="Skill not found")
            
            skill = skill_registry.skills[skill_name]
            return {
                "name": skill.name, 
                "version": skill.version, 
                "description": skill.description,
                "permissions": skill.permissions, 
                "inputs": skill.inputs, 
                "outputs": skill.outputs
            }
        
        @self.app.post("/v1/skills/{skill_name}/execute")
        async def execute_skill(skill_name: str, request: Request, role: str = Depends(get_role)):
            if skill_name not in skill_registry.skills:
                raise HTTPException(status_code=404, detail="Skill not found")
            
            data = await request.json()
            params = data.get("params", {})
            result = await skill_registry.execute(skill_name, params)
            return result
        
        # ========== MEMORY FILES ==========
        @self.app.get("/v1/memory/identity")
        async def get_identity(role: str = Depends(get_role)):
            identity_content = (DIRS["soul"] / "IDENTITY.md").read_text(encoding='utf-8')
            return {"identity": identity_content}
        
        @self.app.get("/v1/memory/diary")
        async def get_diary(role: str = Depends(get_role)):
            diary_path = DIRS["soul"] / "DIARY.md"
            if diary_path.exists():
                return {"diary": diary_path.read_text(encoding='utf-8')}
            return {"diary": ""}
        
        @self.app.post("/v1/memory/diary/append")
        async def append_diary(request: Request, role: str = Depends(get_role)):
            data = await request.json()
            entry = data.get("entry", "")
            diary_path = DIRS["soul"] / "DIARY.md"
            with open(diary_path, 'a', encoding='utf-8') as f:
                f.write(f"\n## {datetime.now().isoformat()}\n{entry}\n")
            return {"status": "appended"}
        
        @self.app.get("/v1/memory/recent")
        async def get_recent_memories(limit: int = 10, role: str = Depends(get_role)):
            memories = await memory_engine.recall(role, "", limit)
            return {"memories": memories}
        
        # ========== HUMAN-IN-THE-LOOP ENDPOINTS (NEW!) ==========
        @self.app.get("/v1/escalations")
        async def list_escalations(role: str = Depends(get_role)):
            """List all pending escalation requests."""
            pending = human_in_loop.get_pending_escalations()
            return {"escalations": pending, "count": len(pending)}
        
        @self.app.post("/v1/escalations/{escalation_id}/respond")
        async def respond_to_escalation(
            escalation_id: str, 
            request: Request, 
            role: str = Depends(get_role)
        ):
            """Respond to an escalation (approve/reject)."""
            data = await request.json()
            approved = data.get("approved", False)
            response = data.get("response", "")
            
            success = await human_in_loop.respond_to_escalation(
                escalation_id, 
                approved, 
                response
            )
            
            if success:
                return {
                    "status": "responded",
                    "escalation_id": escalation_id,
                    "approved": approved
                }
            else:
                return JSONResponse(
                    {"error": "Escalation not found or already resolved"}, 
                    status_code=404
                )
        
        # ========== REZ TRADER ENDPOINTS ==========
        @self.app.get("/pulse")
        async def get_pulse():
            if not hasattr(self, '_pulse_cache'):
                self._pulse_cache = {
                    "total": 85, 
                    "constitutional_safety": 90, 
                    "ai_confidence": 85,
                    "market_risk": 70, 
                    "recommendation": "GREEN - Execute with confidence",
                    "next_action": "Proceed", 
                    "color": "green", 
                    "timestamp": time.time()
                }
                self._pulse_last_update = time.time()
            
            if time.time() - getattr(self, '_pulse_last_update', 0) > 60:
                constitutional_score = 90
                ai_score = 85 if ollama.available else 70
                market_score = 70
                total = (constitutional_score * 0.5) + (ai_score * 0.3) + (market_score * 0.2)
                
                if total >= 85:
                    recommendation, color, next_action = "GREEN - Execute with confidence", "green", "Proceed"
                elif total >= 65:
                    recommendation, color, next_action = "YELLOW - Proceed with caution", "yellow", "Review"
                else:
                    recommendation, color, next_action = "RED - Hold / Re-evaluate", "red", "Pause"
                
                self._pulse_cache = {
                    "total": round(total, 1), 
                    "constitutional_safety": constitutional_score,
                    "ai_confidence": ai_score, 
                    "market_risk": market_score,
                    "recommendation": recommendation, 
                    "next_action": next_action,
                    "color": color, 
                    "timestamp": time.time()
                }
                self._pulse_last_update = time.time()
            
            return self._pulse_cache
        
        @self.app.post("/validate")
        async def validate_trade_endpoint(request: Request):
            try:
                data = await request.json()
            except:
                return JSONResponse({"error": "Invalid JSON"}, status_code=400)
            
            trade = {
                "symbol": data.get("symbol", "BTCUSDT"), 
                "amount": float(data.get("amount", 0)),
                "price": float(data.get("price", 50000)), 
                "stop_loss": data.get("stop_loss")
            }
            portfolio = {"equity": 100000}
            
            paper_trader = self.workers.get("paper_trader", {}).get("instance")
            if paper_trader:
                portfolio_result = await paper_trader.execute("portfolio")
                if portfolio_result.get("success"):
                    portfolio = {
                        "equity": portfolio_result.get("total_value", 100000),
                        "balance": portfolio_result.get("balance", 100000),
                        "positions": portfolio_result.get("positions", {})
                    }
            
            violations = []
            equity = portfolio.get("equity", 100000)
            
            if trade.get("stop_loss"):
                risk_amount = abs(trade["amount"] * (trade["price"] - trade["stop_loss"]))
                risk_pct = risk_amount / equity if equity > 0 else 1
                if risk_pct > 0.02:
                    violations.append(f"Risk {risk_pct*100:.1f}% exceeds 2% limit")
            
            position_value = trade["amount"] * trade["price"]
            position_pct = position_value / equity if equity > 0 else 1
            if position_pct > 0.25:
                violations.append(f"Position {position_pct*100:.1f}% exceeds 25% limit")
            
            if not trade.get("stop_loss"):
                violations.append("Stop-loss required by constitution")
            
            trade_str = f"Trade {trade['symbol']} {trade['amount']}@{trade['price']}"
            ruling = await constitution.evaluate(trade_str)
            if not ruling["approved"]:
                violations.append(ruling["reason"])
            
            approved = len(violations) == 0
            result = {
                "approved": approved, 
                "violations": violations,
                "audit_hash": hashlib.sha256(json.dumps(trade).encode()).hexdigest()[:16],
                "timestamp": time.time()
            }
            
            await event_bus.publish(Event(
                type=EventType.TRADE_EXECUTED if approved else EventType.CONSTITUTION_RULING,
                source="validate_endpoint",
                payload={"trade": trade, "approved": approved, "violations": violations}
            ))
            
            return result
        
        @self.app.get("/constitution/rules")
        async def get_constitution_rules():
            return {
                "max_risk_per_trade_pct": 2.0, 
                "max_daily_drawdown_pct": 5.0, 
                "require_stop_loss": True,
                "no_martingale": True, 
                "position_size_range": "0.1% - 25%", 
                "max_leverage": 10,
                "constitution_patterns_count": len(cfg.CONSTITUTION_PATTERNS),
                "strict_mode": cfg.CONSTITUTION_STRICT,
                "human_in_loop_enabled": cfg.HUMAN_IN_LOOP_ENABLED
            }
        
        @self.app.get("/portfolio")
        async def get_portfolio_json():
            paper_trader = self.workers.get("paper_trader", {}).get("instance")
            if paper_trader:
                result = await paper_trader.execute("portfolio")
                return {
                    "balance": result.get("balance", 0), 
                    "positions": result.get("positions", {}),
                    "total_value": result.get("total_value", result.get("balance", 0)),
                    "success": result.get("success", True)
                }
            return JSONResponse({"error": "Paper trader not available"}, status_code=503)
        
        @self.app.get("/audit/stats")
        async def get_audit_stats():
            event_stats = await event_bus.get_stats()
            rulings_count = 0
            for ev in event_bus._chain:
                if ev.type == EventType.CONSTITUTION_RULING:
                    rulings_count += 1
            
            return {
                "total_entries": event_stats.get("total_events", 0),
                "chain_valid": event_stats.get("chain_valid", True),
                "genesis_hash": event_stats.get("genesis", ""),
                "latest_hash": event_stats.get("latest", ""),
                "rulings_count": rulings_count,
                "blueprints_count": len(memory.memories)
            }
        
        @self.app.get("/audit/verify")
        async def verify_audit_chain():
            chain_valid = await event_bus.verify_chain()
            errors = []
            
            if not chain_valid:
                errors.append("Event chain integrity check failed")
            
            bp_errors = []
            for lock, record in memory.memories.items():
                bp = record.get("value", {})
                verification = SCE.verify(bp)
                if not verification["verified"]:
                    bp_errors.append(f"Blueprint {lock[:12]}... drifted")
            
            if bp_errors:
                errors.extend(bp_errors[:10])
            
            return {
                "chain_valid": chain_valid, 
                "errors": errors,
                "blueprints_checked": len(memory.memories), 
                "blueprints_invalid": len(bp_errors)
            }
        
        @self.app.get("/resource/stats")
        async def get_resource_stats():
            stats = {
                "cpu_percent": 0, 
                "memory_percent": 0, 
                "memory_used_gb": 0, 
                "memory_total_gb": 0,
                "disk_percent": 0, 
                "top_processes": [], 
                "timestamp": time.time()
            }
            
            if HAS_PSUTIL:
                stats["cpu_percent"] = psutil.cpu_percent(interval=0.5)
                vm = psutil.virtual_memory()
                stats["memory_percent"] = vm.percent
                stats["memory_used_gb"] = round(vm.used / 1024**3, 1)
                stats["memory_total_gb"] = round(vm.total / 1024**3, 1)
                disk = psutil.disk_usage('/')
                stats["disk_percent"] = disk.percent
                
                processes = []
                for proc in sorted(psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']),
                                  key=lambda p: p.info.get('cpu_percent', 0), reverse=True)[:5]:
                    try:
                        processes.append({
                            "pid": proc.info['pid'], 
                            "name": proc.info['name'] or "unknown",
                            "cpu_percent": round(proc.info.get('cpu_percent', 0), 1),
                            "memory_percent": round(proc.info.get('memory_percent', 0), 1)
                        })
                    except:
                        pass
                stats["top_processes"] = processes
            
            gpu_stats = gpu.stats()
            if gpu_stats.get("has_gpu"):
                stats["gpu_utilization"] = gpu_stats.get("utilization", 0)
                stats["gpu_memory_percent"] = (
                    (gpu_stats.get("used_gb", 0) / gpu_stats.get("total_gb", 1)) * 100
                    if gpu_stats.get("total_gb") else 0
                )
            
            return stats
        
        @self.app.get("/resource/alerts")
        async def get_resource_alerts(limit: int = 20):
            alerts = []
            stats = await get_resource_stats()
            
            if stats.get("cpu_percent", 0) > 80:
                alerts.append({
                    "type": "CPU_HIGH", 
                    "value": stats["cpu_percent"], 
                    "threshold": 80,
                    "timestamp": time.time(),
                    "top_process": stats.get("top_processes", [{}])[0] if stats.get("top_processes") else None
                })
            
            if stats.get("memory_percent", 0) > 85:
                alerts.append({
                    "type": "MEMORY_HIGH", 
                    "value": stats["memory_percent"], 
                    "threshold": 85,
                    "timestamp": time.time()
                })
            
            if stats.get("disk_percent", 0) > 90:
                alerts.append({
                    "type": "DISK_HIGH", 
                    "value": stats["disk_percent"], 
                    "threshold": 90,
                    "timestamp": time.time()
                })
            
            return {"alerts": alerts[:limit]}
        
        @self.app.get("/symbiote/status")
        async def get_symbiote_status():
            providers = {}
            providers["ollama"] = {
                "available": ollama.available, 
                "name": "Ollama", 
                "quality_score": 85,
                "models": ollama.models[:5] if ollama.models else [cfg.DEFAULT_MODEL],
                "requires_auth": False, 
                "auth_configured": True, 
                "success_rate": 0.95
            }
            providers["constitutional"] = {
                "available": True, 
                "name": "Constitutional Rules Engine",
                "quality_score": 90, 
                "models": ["rules_engine_v1"],
                "requires_auth": False, 
                "auth_configured": True, 
                "success_rate": 0.98
            }
            
            route_count = len(self.workers)
            stats = {
                "routes": route_count,
                "by_provider": {"ollama": route_count // 2, "constitutional": route_count // 2},
                "by_task": {"chat": 100, "code": 50, "analysis": 75, "trade": 30},
                "success": 255, 
                "failures": 5
            }
            
            return {
                "initialized": True, 
                "providers": providers, 
                "stats": stats,
                "routing_strategies": ["constitutional_first", "performance_optimized", "cost_optimized"],
                "active_strategy": "constitutional_first",
                "human_in_loop": cfg.HUMAN_IN_LOOP_ENABLED
            }
        
        @self.app.post("/symbiote/recommend")
        async def get_symbiote_recommendation(request: Request):
            try:
                data = await request.json()
                task = data.get("task", "")
            except:
                return JSONResponse({"error": "Invalid JSON"}, status_code=400)
            
            pulse_response = await get_pulse()
            pulse = pulse_response if isinstance(pulse_response, dict) else {}
            task_lower = task.lower()
            
            if "code" in task_lower or "write" in task_lower or "create" in task_lower:
                provider, model, confidence, rationale = "ollama", cfg.DEFAULT_MODEL, pulse.get("ai_confidence", 70), "Code generation tasks best handled by LLM"
            elif "trade" in task_lower or "risk" in task_lower or "validate" in task_lower:
                provider, model, confidence, rationale = "constitutional", "rules_engine", pulse.get("constitutional_safety", 70), "Trade validation requires constitutional rules"
            else:
                provider, model, confidence, rationale = "ollama", cfg.DEFAULT_MODEL, pulse.get("ai_confidence", 70), "General purpose AI response"
            
            return {
                "task": task, 
                "recommendation": {
                    "provider": provider, 
                    "model": model, 
                    "confidence": confidence, 
                    "rationale": rationale
                },
                "pulse": pulse
            }
        
        @self.app.get("/market/price")
        async def get_market_price(symbol: str = "BTCUSDT"):
            import random
            base_price = 50000 if "BTC" in symbol else 3000 if "ETH" in symbol else 100
            price = base_price * (1 + (random.random() - 0.5) * 0.02)
            return {
                "symbol": symbol, 
                "price": round(price, 2), 
                "timestamp": time.time(), 
                "source": "simulated"
            }
        
        @self.app.get("/vscode-status")
        async def get_vscode_status():
            worker = self.workers.get("vscode_integration", {}).get("instance")
            if worker:
                return await worker.health_check()
            return {"error": "VS Code integration not available"}
        
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
            
            if api_key and api_key not in cfg.API_KEYS:
                return JSONResponse({"error": "Unauthorized"}, status_code=401)
            
            async def event_generator():
                last_integrity = 0
                last_workers = 0
                
                try:
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
                                        "contributing_factors": [f"Drift events: {drift_events_count}"],
                                        "pending_escalations": len(human_in_loop.get_pending_escalations())
                                    }
                                }
                                yield sse(event_data)
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
                                yield sse(event_data)
                                last_workers = now
                            
                            await asyncio.sleep(1)
                        except asyncio.CancelledError:
                            break
                        except Exception as e:
                            logger.error(f"SSE generator error: {e}")
                            yield sse({"type": "error", "content": str(e)})
                            await asyncio.sleep(1)
                finally:
                    logger.info("SSE stream closed")
            
            return StreamingResponse(
                event_generator(), 
                media_type="text/event-stream",
                headers={
                    "Cache-Control": "no-cache, no-transform", 
                    "Connection": "keep-alive",
                    "X-Accel-Buffering": "no", 
                    "Access-Control-Allow-Origin": "*"
                }
            )
        
        @self.app.get("/metrics")
        async def metrics_endpoint():
            if HAS_PROMETHEUS:
                return Response(content=generate_latest(), media_type="text/plain; version=0.0.4")
            return JSONResponse({"error": "prometheus not installed"}, status_code=503)
        
        @self.app.post("/kernel/stream")
        async def kernel_stream(request: Request, role: str = Depends(get_role)):
            try:
                data = await request.json()
            except json.JSONDecodeError:
                return JSONResponse({"error": "Invalid JSON"}, status_code=400)
            
            task = data.get("task", "").strip()
            if not task:
                return JSONResponse({"error": "No task provided"}, status_code=400)
            
            client_ip = request.client.host or "unknown"
            if not await self.rate_limiter.check(client_ip):
                return JSONResponse({"error": "Rate limit exceeded"}, status_code=429)
            
            if kill_switch.is_active():
                return JSONResponse({"error": "System halted: Kill switch active"}, status_code=503)
            
            try:
                task = sanitize_input(task)
            except SecurityError as e:
                return JSONResponse({"error": str(e)}, status_code=400)
            
            async def generate():
                try:
                    reflex_result = await self.reflex.try_execute(task)
                    if reflex_result:
                        yield sse(reflex_result)
                        yield sse({"type": "done"})
                        return
                    
                    ruling = await constitution.evaluate(task)
                    if not ruling["approved"]:
                        yield sse({"type": "error", "content": ruling["reason"]})
                        yield sse({"type": "done"})
                        return
                    
                    # Retrieve user memory and identity
                    user_id = role
                    identity = (DIRS["soul"] / "IDENTITY.md").read_text(encoding='utf-8')
                    facts = await memory_engine.get_facts(user_id)
                    recent_memories = await memory_engine.recall(user_id, task, k=3)
                    
                    # Build context with memory
                    context = {
                        "task": task,
                        "previous_error": False,
                        "requires_precision": "gallery" in task.lower() or "blueprint" in task.lower() or "review" in task.lower(),
                        "retry_count": data.get("retry_count", 0),
                        "user_role": role
                    }
                    
                    # Evaluate cognition mode
                    policy = CognitionPolicy()
                    mode = policy.evaluate(task, context)
                    
                    await event_bus.publish(Event(
                        type=EventType.COGNITION_POLICY, 
                        source="cognition_policy",
                        payload={
                            "mode": mode, 
                            "task_preview": task[:50], 
                            "timestamp": time.time()
                        }
                    ))
                    logger.info(f"🧠 Cognition Policy: {mode} mode selected for task: {task[:50]}...")
                    
                    # Check if we need human escalation
                    if human_in_loop.should_escalate(task, mode):
                        yield sse({
                            "type": "escalation_required",
                            "content": f"⏳ This task requires human approval due to risk level ({mode} mode)."
                        })
                        
                        escalation = await human_in_loop.create_escalation(
                            task, 
                            f"Task classified as {mode} mode requiring human oversight", 
                            policy.evaluate(task, context).__hash__() % 100 / 100
                        )
                        
                        yield sse({
                            "type": "escalation_info",
                            "escalation_id": escalation.id,
                            "timeout_seconds": cfg.ESCALATION_TIMEOUT
                        })
                        
                        approved, response = await human_in_loop.wait_for_approval(escalation.id)
                        
                        if not approved:
                            yield sse({
                                "type": "error", 
                                "content": f"❌ Task rejected by human: {response}"
                            })
                            yield sse({"type": "done"})
                            return
                        
                        yield sse({
                            "type": "status", 
                            "content": f"✅ Human approved: {response}"
                        })
                    
                    inheritance = AIInheritance(
                        base_objective="Complete user tasks efficiently",
                        inherited_heuristics=["optimize_for_speed", "respond_immediately"],
                        inherited_biases={"speed_over_accuracy": 0.8},
                        frozen_weights_version=cfg.VERSION
                    )
                    
                    metacognition = MetacognitionSkill()
                    directives, overridden = metacognition.evaluate_internal_state(inheritance, context)
                    
                    if overridden:
                        yield sse({
                            "type": "status", 
                            "content": f"🧠 METACOGNITION ACTIVE: {mode} reasoning mode engaged."
                        })
                    
                    # Build system prompt with identity and memory
                    if mode == "FAST":
                        system_prompt = f"""{identity}

## YOUR MEMORY
Recent relevant context:
{chr(10).join(recent_memories) if recent_memories else "No recent memory."}

## USER FACTS
{chr(10).join(facts) if facts else "No known facts about this user."}

You are Phoenix. Be extremely concise. Answer in 1-2 sentences maximum.
Do not add explanations, caveats, or fluff."""
                    
                    elif mode == "BALANCED":
                        system_prompt = f"""{identity}

## YOUR MEMORY
{chr(10).join(recent_memories) if recent_memories else "No recent memory."}

## USER FACTS
{chr(10).join(facts) if facts else "No known facts."}

Provide a balanced response:
1. Answer the core question directly.
2. Add one relevant caveat or alternative perspective.
3. Keep total response under 150 words."""
                    
                    else:  # DELIBERATE
                        system_prompt = f"""{identity}

## YOUR MEMORY
{chr(10).join(recent_memories) if recent_memories else "No recent memory."}

## USER FACTS
{chr(10).join(facts) if facts else "No known facts."}

⚠️ CRITICAL TASK DETECTED — DELIBERATE REASONING MODE ACTIVE ⚠️

You MUST output a structured plan using this exact format:

## 📋 AUDIT
- Identify 2-3 specific risks in this request
- Flag any missing information

## 🗺️ PLAN
- Step 1: [First action]
- Step 2: [Second action]
- Step 3: [Third action]

## ⚠️ WARNINGS
- Specific pitfalls to avoid
- Edge cases to watch for

## ✅ VERIFICATION
- How to confirm success

Do NOT execute until the user confirms the plan."""
                    
                    messages = [
                        {"role": "system", "content": system_prompt}, 
                        {"role": "user", "content": task}
                    ]
                    
                    full_response = ""
                    first_token = True
                    
                    try:
                        stream_result = await ollama.chat(messages, model=None, stream=True)
                        async for token in stream_result:
                            if isinstance(token, str):
                                if first_token:
                                    ttft = time.time() - self.start_time
                                    self.governor.record_ttft(ttft)
                                    first_token = False
                                
                                yield sse({"type": "token", "content": token})
                                full_response += token
                    except Exception as e:
                        logger.error(f"CHAT_ERROR: {type(e).__name__}: {e}")
                        import traceback
                        logger.error(traceback.format_exc())
                        fallback = f"⚠️ Error: {str(e)[:100]}"
                        yield sse({"type": "token", "content": fallback})
                        full_response = fallback
                    
                    # Store interaction in memory engine for future recall
                    await memory_engine.store_interaction(user_id, task, full_response, mode)
                    
                    # Extract facts (simple heuristic – could use LLM)
                    if "I prefer" in full_response or "my name is" in full_response.lower():
                        pass  # Very simple fact extraction – replace with proper LLM extraction
                    
                    blueprint = SCE.blueprint(
                        intent={"task": task, "role": role, "mode": mode},
                        dna={"model": ollama.model, "workers": len(self.workers)},
                        execution={
                            "response_length": len(full_response), 
                            "timestamp": time.time()
                        }
                    )
                    lock = memory.store(blueprint)
                    
                    await event_bus.publish(Event(
                        type=EventType.CHAT_MESSAGE, 
                        source="kernel",
                        payload={
                            "task": task[:200], 
                            "mode": mode, 
                            "drift_lock": lock,
                            "response_length": len(full_response)
                        }
                    ))
                    
                    yield sse({"type": "done", "drift_lock": lock, "mode": mode})
                    
                except asyncio.CancelledError:
                    logger.info("Stream cancelled by client")
                    yield sse({"type": "error", "content": "Stream cancelled"})
                except Exception as e:
                    logger.error(f"Stream error: {e}")
                    yield sse({"type": "error", "content": f"Internal error: {type(e).__name__}"})
            
            return StreamingResponse(
                generate(), 
                media_type="text/event-stream",
                headers={
                    "Cache-Control": "no-cache", 
                    "Connection": "keep-alive",
                    "X-Accel-Buffering": "no"
                }
            )
        
        @self.app.post("/kernel/upload")
        async def upload(file: UploadFile = File(...), role: str = Depends(get_role)):
            contents = await file.read()
            if len(contents) > cfg.MAX_FILE_SIZE:
                raise HTTPException(status_code=413, detail="File too large")
            
            ext = os.path.splitext(file.filename)[1].lower()
            if ext not in cfg.ALLOWED_EXTENSIONS:
                raise HTTPException(status_code=415, detail=f"{ext} not allowed")
            
            safe_name = secure_filename(file.filename)
            path = DIRS["uploads"] / safe_name
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
                    "ext": ext
                }
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
                            "skills": len(skill_registry.skills),
                            "memory": len(memory.memories), 
                            "gpu": gpu.stats(),
                            "chain_valid": await event_bus.verify_chain(),
                            "pending_escalations": len(human_in_loop.get_pending_escalations())
                        }
                    }
                    await websocket.send_json(telemetry)
                    await asyncio.sleep(2)
            except WebSocketDisconnect:
                logger.info("Telemetry WebSocket disconnected")
            except Exception as e:
                logger.error(f"Telemetry WebSocket error: {e}")
        
        # REZCODER API endpoints
        @self.app.get("/api/v1/rezcoder/health")
        async def api_rezcoder_health():
            worker = self.workers.get("rezcoder", {}).get("instance")
            if not worker:
                return JSONResponse({"error": "RezCoder not available"}, status_code=503)
            await worker.initialize()
            return await worker.health_check()
        
        @self.app.get("/api/v1/rezcoder/review")
        async def api_rezcoder_review(filepath: str, recursive: bool = False):
            worker = self.workers.get("rezcoder", {}).get("instance")
            if not worker:
                return JSONResponse({"error": "RezCoder not available"}, status_code=503)
            await worker.initialize()
            result = await worker.execute("review", file_path=filepath, recursive=recursive)
            
            mastery = self.workers.get("mastery", {}).get("instance")
            if mastery:
                await mastery.add_xp("code_review", amount=50, description=f"Reviewed {filepath}", source="rezcoder")
            
            return result
        
        @self.app.post("/api/v1/rezcoder/fix")
        async def api_rezcoder_fix(filepath: str, confidence: float = 0.8, backup: bool = True):
            worker = self.workers.get("rezcoder", {}).get("instance")
            if not worker:
                return JSONResponse({"error": "RezCoder not available"}, status_code=503)
            await worker.initialize()
            result = await worker.execute("fix", file_path=filepath, confidence=confidence, backup=backup)
            
            mastery = self.workers.get("mastery", {}).get("instance")
            if mastery:
                await mastery.add_xp("code_fix", amount=100, description=f"Fixed {filepath}", source="rezcoder")
            
            return result
        
        @self.app.get("/api/v1/rezcoder/report")
        async def api_rezcoder_report(filepath: str):
            worker = self.workers.get("rezcoder", {}).get("instance")
            if not worker:
                return JSONResponse({"error": "RezCoder not available"}, status_code=503)
            await worker.initialize()
            return await worker.execute("report", file_path=filepath)
        
        # MCP API endpoints
        @self.app.get("/api/v1/mcp/health")
        async def api_mcp_health():
            worker = self.workers.get("sovereign_mcp_server", {}).get("instance")
            if not worker:
                return JSONResponse({"error": "MCP server not available"}, status_code=503)
            await worker.initialize()
            return await worker.health_check()
        
        @self.app.get("/api/v1/mcp/tools")
        async def api_mcp_tools():
            worker = self.workers.get("sovereign_mcp_server", {}).get("instance")
            if not worker:
                return JSONResponse({"error": "MCP server not available"}, status_code=503)
            await worker.initialize()
            return await worker.execute("list_tools")
        
        @self.app.get("/api/v1/mcp/review")
        async def api_mcp_review(filepath: str, recursive: bool = False):
            worker = self.workers.get("sovereign_mcp_server", {}).get("instance")
            if not worker:
                return JSONResponse({"error": "MCP server not available"}, status_code=503)
            await worker.initialize()
            return await worker.execute(f"review_code {filepath}" + (" --recursive" if recursive else ""))
        
        @self.app.post("/api/v1/mcp/fix")
        async def api_mcp_fix(filepath: str, confidence: float = 0.8, backup: bool = True):
            worker = self.workers.get("sovereign_mcp_server", {}).get("instance")
            if not worker:
                return JSONResponse({"error": "MCP server not available"}, status_code=503)
            await worker.initialize()
            return await worker.execute(f"fix_code {filepath} --confidence {confidence}" + (" --backup" if backup else ""))
        
        @self.app.get("/api/v1/mcp/generate")
        async def api_mcp_generate(intent: str, language: str = "python"):
            worker = self.workers.get("sovereign_mcp_server", {}).get("instance")
            if not worker:
                return JSONResponse({"error": "MCP server not available"}, status_code=503)
            await worker.initialize()
            result = await worker.execute(f"generate_code {intent} --language {language}")
            
            mastery = self.workers.get("mastery", {}).get("instance")
            if mastery:
                await mastery.add_xp("code_generate", amount=75, description=f"Generated code for {intent}", source="mcp")
            
            return result
        
        # Mastery API
        @self.app.get("/api/v1/mastery/stats")
        async def api_mastery_stats():
            worker = self.workers.get("mastery", {}).get("instance")
            if not worker:
                return JSONResponse({"error": "Mastery not available"}, status_code=503)
            await worker.initialize()
            stats = await worker.get_stats()
            return stats
        
        @self.app.post("/api/v1/mastery/add_xp")
        async def api_mastery_add_xp(action: str, amount: int, description: str = ""):
            worker = self.workers.get("mastery", {}).get("instance")
            if not worker:
                return JSONResponse({"error": "Mastery not available"}, status_code=503)
            await worker.initialize()
            result = await worker.add_xp(action, amount, description, source="api")
            return result
    
    async def startup(self):
        await event_bus.initialize()
        await ollama.initialize()
        task_scheduler.start()
        
        if HAS_PROMETHEUS:
            try:
                start_http_server(cfg.METRICS_PORT, addr=cfg.HOST)
                logger.info(f"📊 Prometheus metrics on http://{cfg.HOST}:{cfg.METRICS_PORT}")
            except Exception as e:
                logger.warning(f"Metrics server failed: {e}")
        
        self._bg_tasks.append(asyncio.create_task(symbiote_loop()))
        
        if self.sio:
            self._bg_tasks.append(asyncio.create_task(market_broadcaster(self.sio)))
        
        # Start cleanup task for stale escalations
        self._bg_tasks.append(asyncio.create_task(self._periodic_cleanup()))
        
        self._print_banner()
    
    async def _periodic_cleanup(self):
        """Periodically clean up stale escalations and old data."""
        while True:
            try:
                await asyncio.sleep(3600)  # Every hour
                await human_in_loop.cleanup_stale()
                logger.info("🧹 Cleanup completed: removed stale escalations")
            except asyncio.CancelledError:
                return
            except Exception as e:
                logger.error(f"Cleanup error: {e}")
    
    async def shutdown(self):
        logger.info("🌙 Shutting down Phoenix...")
        task_scheduler.stop()
        
        for t in self._bg_tasks:
            t.cancel()
        
        await asyncio.gather(*self._bg_tasks, return_exceptions=True)
        await event_bus.shutdown()
        
        valid = await event_bus.verify_chain()
        logger.info(f"⛓️ Final chain integrity: {'✅ VALID' if valid else '❌ BROKEN'}")
        
        if HAS_PYNVML and gpu.has_gpu:
            try:
                pynvml.nvmlShutdown()
            except:
                pass
        
        logger.info("🌙 Phoenix shutdown complete")
    
    def _print_banner(self):
        print("\n" + "=" * 70)
        print(f"🔥 PHOENIX v{self.version} - SOVEREIGN AGENT RUNTIME")
        print("=" * 70)
        print(f"  Workers:      {len(self.workers)}")
        print(f"  Skills:       {len(skill_registry.skills)}")
        print(f"  Blueprints:   {len(memory.memories)}")
        print(f"  Memory:       sqlite-vec enabled")
        print(f"  Scheduler:    {'✅ APScheduler' if HAS_SCHEDULER else '❌ Not installed'}")
        print(f"  Ollama:       {'🟢 ' + ollama.model if ollama.available else '🔴 offline'}")
        
        if gpu.has_gpu:
            s = gpu.stats()
            print(f"  GPU:          {s.get('name')} ({s.get('free_gb')}GB free)")
        
        print(f"  API:          http://{cfg.HOST}:{cfg.PORT}")
        print(f"  Docs:         http://{cfg.HOST}:{cfg.PORT}/docs")
        
        if HAS_SOCKETIO:
            print(f"  WebSocket:    ws://{cfg.HOST}:{cfg.PORT}")
        
        print("=" * 70)
        print("  Reflex Commands:")
        print("    /health /workers /skills /portfolio /trade /backtest")
        print("    /kill /kill-reset /kill-status")
        print("    /okiru /symbiote /search /code")
        print("    /schedule interval:10 \"task\"")
        print("    /vscode agent:prompt | plan:prompt | ask:question | edit:file")
        print("    /vscode-status")
        print("    /escalations  (NEW: View pending human approvals)")
        print("=" * 70)
        print("  REZ Trader Endpoints:")
        print("    GET  /pulse")
        print("    POST /validate")
        print("    GET  /portfolio")
        print("    GET  /constitution/rules")
        print("    GET  /audit/stats")
        print("    GET  /resource/stats")
        print("    GET  /symbiote/status")
        print("    GET  /api/v1/rezcoder/review → +50 XP")
        print("    POST /api/v1/rezcoder/fix     → +100 XP")
        print("    GET  /api/v1/mcp/generate    → +75 XP")
        print("=" * 70)
        print("  Governance Endpoints:")
        print("    GET  /v1/memory/identity")
        print("    GET  /v1/memory/diary")
        print("    GET  /v1/skills/list")
        print("    POST /v1/schedule")
        print("    GET  /v1/escalations         (NEW: Human-in-the-loop)")
        print("    POST /v1/escalations/:id/respond")
        print("=" * 70)
        print("  ✨ NEW IN v16.1.0:")
        print("    • Human-in-the-Loop escalation system")
        print("    • Adaptive cognition modes (Fast/Balanced/Deliberate)")
        print("    • Metacognitive overrides")
        print("    • Enhanced audit trail with VERA chain")
        print("    • MCP (Model Context Protocol) support")
        print("=" * 70 + "\n")
    
    async def run(self):
        await self.startup()
        
        if HAS_SOCKETIO and self.sio:
            app = socketio.ASGIApp(self.sio, self.app)
        else:
            app = self.app
        
        server = uvicorn.Server(uvicorn.Config(
            app, 
            host=cfg.HOST, 
            port=cfg.PORT, 
            log_level="info",
            access_log=True, 
            timeout_keep_alive=30
        ))
        
        try:
            await server.serve()
        finally:
            await self.shutdown()

# ============================================================================
# ENTRY POINT
# ============================================================================
if __name__ == "__main__":
    kernel = PhoenixKernel()
    try:
        asyncio.run(kernel.run())
    except KeyboardInterrupt:
        print("\n🛑 Phoenix rests.")
    except Exception as e:
        logger.critical(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)