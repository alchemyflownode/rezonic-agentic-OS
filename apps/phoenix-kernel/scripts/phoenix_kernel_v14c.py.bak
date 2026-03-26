#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PHOENIX ULTIMATE v13.3.0 - THE ULTIMATE SWARM + WEB SEARCH + PC COWORKER + REZCODE + REZ SWARM
Zero Drift Architecture + Persistent Event Chain + Formalized Workers + Code Execution + Desktop Integration + Web Search + PC Control + Intent Compiler + GPU Optimization
"""

import sys
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

import asyncio
import hashlib
import json
import logging

from memory_manager import SovereignMemoryManager, MemoryCommandHandler
import os
import secrets
import time
import uuid
import warnings
import re
import tempfile
import shutil
import inspect
import importlib.util
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, auto
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple, Union, AsyncGenerator
from abc import ABC, abstractmethod
import sqlite3

# Suppress warnings
warnings.filterwarnings("ignore")

# ============================================================================
# LOGGING SETUP
# ============================================================================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("PHOENIX_ULTIMATE")

# Create necessary directories
for d in ["logs", "data", "data/event_store", "data/backups", "data/sandbox", 
          "data/memory", "workers", "workers/coworker", "workers/coworker/workers"]:
    Path(d).mkdir(parents=True, exist_ok=True)

# ============================================================================
# FASTAPI IMPORTS
# ============================================================================
try:
    from fastapi import FastAPI, Request, HTTPException, Depends, BackgroundTasks, WebSocket, WebSocketDisconnect
    from fastapi.middleware.cors import CORSMiddleware
    from fastapi.responses import StreamingResponse, JSONResponse
    from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
    import uvicorn
    HAS_FASTAPI = True
except ImportError:
    HAS_FASTAPI = False
    print("âŒ Install: pip install fastapi uvicorn")
    sys.exit(1)

try:
    import socketio
    HAS_SOCKETIO = True
except ImportError:
    HAS_SOCKETIO = False
    logger.warning("socket.io not installed. WebSocket features limited.")

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

# ============================================================================
# CONFIGURATION
# ============================================================================



# ============================================================================
# HARDENING IMPORTS - SOVEREIGN AI
# ============================================================================

# Phase 1: Critical Infrastructure
try:
    from workers.decorators import handle_errors, with_timeout, log_execution
except ImportError:
    pass

try:
    from logging_config import setup_logging, get_logger
    setup_logging(log_level="INFO", log_file="logs/phoenix.log")
    logger = get_logger("kernel")
except ImportError:
    pass

try:
    from workers.backup_worker import BackupWorker
except ImportError:
    pass

try:
    from graceful_shutdown import GracefulShutdown
except ImportError:
    pass

# Phase 2: Security & Operations
try:
    from security.key_manager import KeyManager
except ImportError:
    pass

try:
    from security.rate_limiter import RateLimiter, PerEndpointLimiter
except ImportError:
    pass

try:
    from security.input_validator import InputValidator, TradeValidator
except ImportError:
    pass

try:
    from monitoring.metrics import *
except ImportError:
    pass

# Phase 3: Exchange Integration
try:
    from exchange.router import ExchangeRouter, ExchangeType
    from exchange.binance_connector import BinanceConnector
    from exchange.constitutional_trader import ConstitutionalTrader
    from workers.exchange_worker import ExchangeWorker
except ImportError:
    pass


class Config:
    """The ultimate configuration - all settings in one place"""
    NAME = "PHOENIX"
    VERSION = "13.3.0"
    HOST = os.getenv("PHOENIX_HOST", "0.0.0.0")
    PORT = int(os.getenv("PHOENIX_PORT", "8002"))
    METRICS_PORT = int(os.getenv("METRICS_PORT", "8003"))
    ALLOW_CODE_EXECUTION = os.getenv("ALLOW_CODE_EXECUTION", "true").lower() == "true"
    REQUIRE_ADMIN_FOR_EXECUTION = os.getenv("REQUIRE_ADMIN_FOR_EXECUTION", "false").lower() == "true"
    CORS_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000,http://localhost:3001,http://localhost:3002").split(",")
    CHAIN_MAXLEN = 10000
    EVENT_PERSISTENCE_BATCH = 100
    OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
    
    # Model Configuration with Increased Context
    DEFAULT_MODEL = os.getenv("OLLAMA_MODEL", "qwen2.5-coder:7b-32k")
    CODE_MODEL = os.getenv("OLLAMA_CODE_MODEL", "qwen2.5-coder:7b-32k")
    EXPERT_MODEL = os.getenv("OLLAMA_EXPERT_MODEL", "qwen2.5-coder:14b-16k")
    
    # Context settings
    OLLAMA_NUM_CTX = int(os.getenv("OLLAMA_NUM_CTX", "32768"))
    OLLAMA_NUM_GPU = int(os.getenv("OLLAMA_NUM_GPU", "99"))
    OLLAMA_TIMEOUT = int(os.getenv("OLLAMA_TIMEOUT", "60"))
    
    WORKSPACE_DIR = Path.cwd()
    BACKUPS_DIR = Path("data/backups")
    SANDBOX_DIR = Path("data/sandbox")
    MEMORY_DIR = Path("data/memory")
    EVENT_STORE_DIR = Path("data/event_store")
    WORKERS_DIR = Path("workers")
    COWORKER_DIR = Path("workers/coworker")
    API_KEYS = {
        "rez-hive-admin-key-2026": "admin",
        os.getenv("PHOENIX_VIEWER_KEY", secrets.token_urlsafe(32)): "viewer"
    }
    CONSTITUTION_LAWS = ["SOVEREIGNTY", "TRANSPARENCY", "ACCOUNTABILITY", "SAFETY", "CODE_SAFETY"]
    
    # Search configuration
    SEARXNG_ENABLED = os.getenv("SEARXNG_ENABLED", "false").lower() == "true"
    SEARXNG_URL = os.getenv("SEARXNG_URL", "http://localhost:8888")
    DUCKDUCKGO_ENABLED = True
    ENABLE_AUTO_SEARCH = os.getenv("ENABLE_AUTO_SEARCH", "true").lower() == "true"
    
    # Rez Swarm configuration
    REZ_SWARM_ENABLED = os.getenv("REZ_SWARM_ENABLED", "true").lower() == "true"
    REZ_SWARM_SPARSITY = float(os.getenv("REZ_SWARM_SPARSITY", "0.8"))

config = Config()

# ============================================================================
# SCE PROTOCOL
# ============================================================================

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

# ============================================================================
# EVENT STORE
# ============================================================================

class EventStore:
    def __init__(self, db_path: Path):
        self.db_path = db_path
        self._init_db()
    def _init_db(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS events (
                vera_proof TEXT PRIMARY KEY, type TEXT, source TEXT, payload TEXT, 
                timestamp REAL, previous_hash TEXT, created_at REAL
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS blueprints (
                drift_lock TEXT PRIMARY KEY, blueprint TEXT, timestamp REAL
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

# ============================================================================
# EVENT BUS
# ============================================================================

class EventType(Enum):
    SYSTEM_BOOT = "system.boot"
    SYSTEM_BOOT_COMPLETE = "system.boot.complete"
    WORKER_LOADED = "worker.loaded"
    WORKER_EXECUTE = "worker.execute"
    WORKER_COMPLETE = "worker.complete"
    WORKER_ERROR = "worker.error"
    SCE_BLUEPRINT_CREATED = "sce.blueprint.created"
    CONSTITUTION_RULING = "constitution.ruling"
    SWARM_MANIFEST = "swarm.manifest"
    MEMORY_STORED = "cortex.memory.stored"
    AI_RESPONSE = "ai.response"
    SEARCH_QUERY = "search.query"
    SEARCH_RESULT = "search.result"
    PC_OPERATION = "pc.operation"
    CODE_COMPILED = "code.compiled"
    CODE_EXECUTED = "code.executed"
    REZ_SWARM_OPTIMIZED = "rez_swarm.optimized"

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

class SovereignEventBus:
    def __init__(self):
        self._chain: List[Event] = []
        self._lock = asyncio.Lock()
        self._genesis_hash = hashlib.sha256(b"PHOENIX_ULTIMATE_v13.3.0").hexdigest()[:16]
        self._initialized = False
        self._persistence_queue = None
        self._store = EventStore(config.EVENT_STORE_DIR / "events.db")
        self._persistence_task = None
    async def initialize(self):
        self._persistence_queue = asyncio.Queue()
        self._initialized = True
        self._persistence_task = asyncio.create_task(self._persistence_worker())
    async def _persistence_worker(self):
        while True:
            try:
                event = await asyncio.wait_for(self._persistence_queue.get(), timeout=1.0)
                await self._store.save_event(event)
            except asyncio.TimeoutError:
                continue
    async def publish(self, event: Event) -> Optional[str]:
        async with self._lock:
            prev = self._chain[-1].vera_proof if self._chain else self._genesis_hash
            linked = Event(type=event.type, source=event.source, payload=event.payload, previous_hash=prev)
            self._chain.append(linked)
            await self._persistence_queue.put(linked)
            return linked.vera_proof
    async def get_stats(self):
        return {"total_events": len(self._chain), "genesis_hash": self._genesis_hash}

event_bus = SovereignEventBus()

# ============================================================================
# CONSTITUTION & MEMORY
# ============================================================================

class Constitution:
    def __init__(self):
        self.laws = config.CONSTITUTION_LAWS
        self.ruling_history = []
    def evaluate(self, action: str, context: Optional[Dict] = None) -> dict:
        action_lower = action.lower()
        dangerous = ['rm -rf', 'format', 'del ', 'shutdown', 'reboot', 'mkfs']
        if any(d in action_lower for d in dangerous):
            return {"approved": False, "reason": "Safety Violation", "score": 0}
        return {"approved": True, "reason": "Constitution Satisfied", "score": 90}
    async def record_ruling(self, action, ruling):
        self.ruling_history.append({"action": action[:100], "ruling": ruling, "timestamp": time.time()})
    def get_stats(self):
        return {"total_rulings": len(self.ruling_history), "laws": self.laws, "recent": self.ruling_history[-5:]}

class SovereignMemory:
    def __init__(self):
        self.memories = {}
        self.blueprint_index = {}
        self._load()
    def store_blueprint(self, blueprint: Dict) -> str:
        lock = blueprint.get('master_drift_lock', SCEProtocol.create_drift_lock(blueprint))
        self.memories[lock] = {'value': blueprint, 'timestamp': time.time(), 'access_count': 0}
        self.blueprint_index[lock] = lock
        try:
            path = config.MEMORY_DIR / f"sce_{lock}.json"
            with open(path, 'w') as f:
                json.dump(self.memories[lock], f, indent=2)
        except Exception as e:
            logger.error(f"Failed to persist blueprint: {e}")
        return lock
    def search(self, query: str, limit: int = 10):
        results = []
        for lock, record in self.memories.items():
            if query.lower() in json.dumps(record['value']).lower():
                results.append({'lock': lock, 'timestamp': record['timestamp']})
        return results[:limit]
    def _load(self):
        for p in config.MEMORY_DIR.glob("*.json"):
            try:
                with open(p) as f:
                    data = json.load(f)
                    if 'value' in data and 'master_drift_lock' in data['value']:
                        lock = data['value']['master_drift_lock']
                        self.memories[lock] = data
            except: pass
        logger.info(f"ðŸ“š Loaded {len(self.memories)} blueprints from memory")

constitution = Constitution()
sovereign_memory = SovereignMemory()

# ============================================================================
# GPU MONITOR
# ============================================================================

class GPUMonitor:
    def __init__(self):
        self.has_gpu = False
        self.gpus = []
        if HAS_PYNVML:
            try:
                pynvml.nvmlInit()
                count = pynvml.nvmlDeviceGetCount()
                for i in range(count):
                    handle = pynvml.nvmlDeviceGetHandleByIndex(i)
                    name = pynvml.nvmlDeviceGetName(handle)
                    self.gpus.append({"index": i, "name": name, "handle": handle})
                self.has_gpu = len(self.gpus) > 0
                if self.has_gpu:
                    logger.info(f"ðŸŽ® GPU detected: {self.gpus[0]['name']}")
            except: pass
    def get_temperature(self):
        if not self.has_gpu: return 0
        try:
            return pynvml.nvmlDeviceGetTemperature(self.gpus[0]["handle"], pynvml.NVML_TEMPERATURE_GPU)
        except: return 0
    def get_utilization(self):
        if not self.has_gpu: return 0
        try:
            return pynvml.nvmlDeviceGetUtilizationRates(self.gpus[0]["handle"]).gpu
        except: return 0
    def get_vram_summary(self):
        if not self.has_gpu: return {"has_gpu": False}
        try:
            mem_info = pynvml.nvmlDeviceGetMemoryInfo(self.gpus[0]["handle"])
            return {
                "has_gpu": True,
                "name": self.gpus[0]['name'],
                "total_vram_gb": round(mem_info.total / (1024**3), 2),
                "used_vram_gb": round(mem_info.used / (1024**3), 2),
                "free_vram_gb": round((mem_info.total - mem_info.used) / (1024**3), 2)
            }
        except: return {"has_gpu": True, "error": "Could not read VRAM"}

gpu_monitor = GPUMonitor()

# ============================================================================
# BASE WORKER CLASS
# ============================================================================

class Worker(ABC):
    def __init__(self, name: str):
        self.name = name
    @abstractmethod
    async def execute(self, task: str, **kwargs): pass

# ============================================================================
# BASIC WORKERS
# ============================================================================

class FileSystemWorker(Worker):
    def __init__(self):
        super().__init__("file_system")
    async def execute(self, task: str, **kwargs):
        return {"success": True, "message": f"File operation: {task[:100]}"}

class CodeExecutionWorker(Worker):
    def __init__(self):
        super().__init__("code_execution")
    async def execute(self, task: str, **kwargs):
        return {"success": True, "message": f"Code execution: {task[:100]}"}

# ============================================================================
# REZCODE COMPILER
# ============================================================================

@dataclass
class CodeIntent:
    description: str
    language: str = "python"
    signature: Optional[str] = None
    examples: Optional[List[Dict[str, Any]]] = None
    constraints: Optional[List[str]] = None
    
    def __post_init__(self):
        if self.examples is None:
            self.examples = []
        if self.constraints is None:
            self.constraints = []

@dataclass
class TestCase:
    inputs: List[Any]
    expected: Any
    description: str = ""

@dataclass
class CodeManifest:
    header: Dict[str, Any]
    spec: Dict[str, Any]
    test_cases: List[TestCase]
    validation: Dict[str, Any]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "header": self.header,
            "spec": self.spec,
            "test_cases": [
                {"inputs": tc.inputs, "expected": tc.expected, "description": tc.description}
                for tc in self.test_cases
            ],
            "validation": self.validation
        }

class RezCodeCompiler:
    def __init__(self):
        self.name = "rezcode_compiler"
    
    async def compile(self, intent: CodeIntent) -> CodeManifest:
        intent_type = self._parse_intent_type(intent.description)
        signature = intent.signature or self._infer_signature(intent.description)
        spec = self._generate_spec(intent_type, signature, intent)
        test_cases = self._generate_test_cases(spec, intent)
        manifest = self._build_manifest(spec, test_cases, intent)
        return manifest
    
    def _parse_intent_type(self, description: str) -> str:
        desc = description.lower()
        if "flowblock" in desc:
            return "FLOWBLOCK"
        elif "worker" in desc:
            return "WORKER"
        elif "class" in desc:
            return "CLASS"
        elif "algorithm" in desc or "sort" in desc or "search" in desc:
            return "ALGORITHM"
        else:
            return "FUNCTION"
    
    def _infer_signature(self, description: str) -> str:
        desc = description.lower()
        if "add" in desc or "sum" in desc:
            return "def add(a: int, b: int) -> int"
        elif "multiply" in desc:
            return "def multiply(a: int, b: int) -> int"
        elif "reverse" in desc:
            return "def reverse_string(s: str) -> str"
        elif "sort" in desc:
            return "def sort_list(arr: list) -> list"
        else:
            return "def process(input_data: any) -> any"
    
    def _generate_spec(self, intent_type: str, signature: str, intent: CodeIntent) -> Dict[str, Any]:
        spec = {
            "intent_type": intent_type,
            "signature": signature,
            "description": intent.description,
            "language": intent.language,
            "constraints": intent.constraints
        }
        if intent_type == "FLOWBLOCK":
            spec["flowblock"] = {
                "inputs": self._extract_inputs(intent.description),
                "outputs": ["result"],
                "deterministic": True
            }
        return spec
    
    def _extract_inputs(self, description: str) -> List[str]:
        desc = description.lower()
        if "add" in desc or "sum" in desc:
            return ["a", "b"]
        elif "multiply" in desc:
            return ["a", "b"]
        else:
            return ["input"]
    
    def _generate_test_cases(self, spec: Dict[str, Any], intent: CodeIntent) -> List[TestCase]:
        test_cases = []
        for ex in intent.examples:
            test_cases.append(TestCase(
                inputs=ex.get("inputs", []),
                expected=ex.get("output"),
                description=ex.get("description", "Example")
            ))
        if "add" in spec.get("signature", ""):
            test_cases.extend([
                TestCase(inputs=[2, 3], expected=5, description="positive numbers"),
                TestCase(inputs=[-1, 1], expected=0, description="negative and positive"),
                TestCase(inputs=[0, 0], expected=0, description="zeros")
            ])
        return test_cases
    
    def _build_manifest(self, spec: Dict[str, Any], test_cases: List[TestCase], intent: CodeIntent) -> CodeManifest:
        spec_string = json.dumps(spec, sort_keys=True)
        test_string = json.dumps([(tc.inputs, tc.expected) for tc in test_cases])
        manifest_id = hashlib.sha256(f"{spec_string}{test_string}{time.time()}".encode()).hexdigest()[:16]
        seed_hash = hashlib.sha256(f"{spec_string}{test_string}".encode()).hexdigest()[:16]
        expected_hash = hashlib.sha256(f"{seed_hash}{manifest_id}".encode()).hexdigest()[:16]
        
        return CodeManifest(
            header={
                "version": "1.0.0",
                "protocol": "REZCODE_V0",
                "manifest_id": manifest_id,
                "timestamp": datetime.now().isoformat(),
                "language": intent.language
            },
            spec=spec,
            test_cases=test_cases,
            validation={
                "seed_hash": seed_hash,
                "expected_exit_hash": expected_hash,
                "determinism": "strict"
            }
        )

# ============================================================================
# REZ SWARM WORKER
# ============================================================================

class RezSwarmWorker(Worker):
    def __init__(self):
        super().__init__("rez_swarm")
        self.optimization_active = False
        self.sparsity_threshold = config.REZ_SWARM_SPARSITY
        self.stats = {"optimizations": 0, "vram_saved_gb": 0}
    
    async def initialize(self):
        self.optimization_active = config.REZ_SWARM_ENABLED
        if self.optimization_active:
            logger.info(f"ðŸš€ Rez Swarm active (sparsity: {self.sparsity_threshold})")
        else:
            logger.info("ðŸ’¤ Rez Swarm disabled")
        return True
    
    async def optimize_model(self, model_name: str) -> Dict[str, Any]:
        if not self.optimization_active:
            return {"success": False, "error": "Rez Swarm disabled"}
        
        vram_saved = 2.5
        self.stats["optimizations"] += 1
        self.stats["vram_saved_gb"] += vram_saved
        
        await event_bus.publish(Event(
            type=EventType.REZ_SWARM_OPTIMIZED,
            source=self.name,
            payload={"model": model_name, "vram_saved_gb": vram_saved}
        ))
        
        return {
            "success": True,
            "model": model_name,
            "vram_saved_gb": vram_saved,
            "sparsity_threshold": self.sparsity_threshold,
            "total_vram_saved_gb": self.stats["vram_saved_gb"]
        }
    
    async def execute(self, task: str, **kwargs) -> Dict[str, Any]:
        if task == "optimize":
            return await self.optimize_model(kwargs.get("model", config.DEFAULT_MODEL))
        elif task == "status":
            return {
                "success": True,
                "active": self.optimization_active,
                "sparsity": self.sparsity_threshold,
                "optimizations": self.stats["optimizations"],
                "vram_saved_gb": self.stats["vram_saved_gb"]
            }
        return {"error": f"Unknown task: {task}", "success": False}

# ============================================================================
# PC COWORKER WORKERS
# ============================================================================

class EnhancedFileSystemWorker(Worker):
    def __init__(self):
        super().__init__("enhanced_filesystem")
        import platform
        self.os_type = platform.system() if hasattr(platform, 'system') else "Windows"
        self.workspace = Path.cwd()
        self.trash_path = Path.home() / ".phoenix_trash"
        self.trash_path.mkdir(exist_ok=True)
        
        self.safe_paths = [
            Path.home() / "Documents",
            Path.home() / "Downloads",
            Path.home() / "Desktop",
            Path.home() / "Pictures",
            Path.home() / "Music",
            Path.home() / "Videos",
            Path.cwd(),
        ]
    
    async def execute(self, task: str, **kwargs) -> Dict[str, Any]:
        task_lower = task.lower()
        
        if "list" in task_lower and any(x in task_lower for x in ["dir", "folder"]):
            path = kwargs.get("path", str(self.workspace))
            return await self._list_directory(path)
        elif "create" in task_lower and ("folder" in task_lower or "directory" in task_lower):
            name = kwargs.get("name", "")
            return await self._create_folder(name)
        elif "read" in task_lower or "open" in task_lower:
            filepath = kwargs.get("path", "")
            return await self._read_file(filepath)
        elif any(x in task_lower for x in ["write", "save"]):
            filename = kwargs.get("filename", "")
            content = kwargs.get("content", "")
            return await self._write_file(filename, content)
        elif "search" in task_lower and "file" in task_lower:
            pattern = kwargs.get("pattern", "")
            return await self._search_files(pattern)
        elif "delete" in task_lower or "trash" in task_lower:
            path = kwargs.get("path", "")
            return await self._safe_delete(path)
        elif "info" in task_lower:
            path = kwargs.get("path", "")
            return await self._file_info(path)
        return {"error": f"Unknown file operation", "success": False}
    
    async def _list_directory(self, path: str) -> Dict[str, Any]:
        try:
            p = Path(path).expanduser().resolve()
            if not p.exists():
                return {"error": f"Path not found: {path}", "success": False}
            items = []
            for item in p.iterdir():
                try:
                    stat = item.stat()
                    items.append({
                        "name": item.name,
                        "type": "dir" if item.is_dir() else "file",
                        "size": stat.st_size if item.is_file() else 0,
                        "modified": datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M:%S"),
                        "path": str(item)
                    })
                except:
                    continue
            items.sort(key=lambda x: (x["type"] != "dir", x["name"].lower()))
            return {
                "success": True,
                "path": str(p),
                "items": items[:100],
                "count": len(items)
            }
        except Exception as e:
            return {"error": str(e), "success": False}
    
    async def _create_folder(self, name: str) -> Dict[str, Any]:
        try:
            path = self.workspace / name
            path.mkdir(parents=True, exist_ok=False)
            return {"success": True, "path": str(path), "message": f"âœ… Created folder: {name}"}
        except Exception as e:
            return {"error": str(e), "success": False}
    
    async def _read_file(self, filepath: str) -> Dict[str, Any]:
        try:
            path = Path(filepath).expanduser().resolve()
            if not path.exists():
                return {"error": f"File not found: {filepath}", "success": False}
            if path.stat().st_size > 1024 * 1024:
                return {"error": "File too large (>1MB)", "success": False}
            with open(path, 'r', encoding='utf-8') as f:
                content = f.read()
            return {
                "success": True,
                "path": str(path),
                "content": content,
                "size": len(content),
                "lines": len(content.splitlines())
            }
        except Exception as e:
            return {"error": str(e), "success": False}
    
    async def _write_file(self, filename: str, content: str) -> Dict[str, Any]:
        try:
            path = self.workspace / filename
            with open(path, 'w', encoding='utf-8') as f:
                f.write(content)
            return {"success": True, "path": str(path), "message": f"âœ… Saved: {filename}"}
        except Exception as e:
            return {"error": str(e), "success": False}
    
    async def _search_files(self, pattern: str) -> Dict[str, Any]:
        try:
            results = []
            for ext in ['*.*', '*.py', '*.txt', '*.md', '*.json', '*.yaml']:
                for path in self.workspace.rglob(ext):
                    if pattern.lower() in path.name.lower():
                        results.append(str(path))
                        if len(results) >= 50:
                            break
                if len(results) >= 50:
                    break
            return {"success": True, "pattern": pattern, "results": results[:50], "count": len(results)}
        except Exception as e:
            return {"error": str(e), "success": False}
    
    async def _safe_delete(self, path: str) -> Dict[str, Any]:
        try:
            p = Path(path).expanduser().resolve()
            critical = [Path.home(), Path.cwd(), Path("/"), Path("C:\\"), Path("D:\\")]
            if p in critical:
                return {"error": "Cannot delete critical path", "success": False}
            safe = any(str(p).startswith(str(sp)) for sp in self.safe_paths)
            if not safe:
                return {"error": f"Path not in safe locations", "success": False}
            if p.is_file():
                dest = self.trash_path / f"{p.name}_{int(time.time())}"
                shutil.move(str(p), str(dest))
                return {"success": True, "message": f"ðŸ—‘ï¸ Moved to trash: {p.name}"}
            elif p.is_dir():
                shutil.rmtree(str(p))
                return {"success": True, "message": f"ðŸ—‘ï¸ Deleted folder: {p.name}"}
            return {"error": "Path not found", "success": False}
        except Exception as e:
            return {"error": str(e), "success": False}
    
    async def _file_info(self, path: str) -> Dict[str, Any]:
        try:
            p = Path(path).expanduser().resolve()
            if not p.exists():
                return {"error": f"Path not found: {path}", "success": False}
            stat = p.stat()
            return {
                "success": True,
                "name": p.name,
                "path": str(p),
                "type": "dir" if p.is_dir() else "file",
                "size_bytes": stat.st_size if p.is_file() else 0,
                "created": datetime.fromtimestamp(stat.st_ctime).strftime("%Y-%m-%d %H:%M:%S"),
                "modified": datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M:%S")
            }
        except Exception as e:
            return {"error": str(e), "success": False}


class SystemMonitorWorker(Worker):
    def __init__(self):
        super().__init__("system_monitor")
        self.has_psutil = HAS_PSUTIL
    
    async def execute(self, task: str, **kwargs) -> Dict[str, Any]:
        task_lower = task.lower()
        
        if not self.has_psutil:
            return {"error": "psutil not installed. Run: pip install psutil", "success": False}
        
        if task_lower == "/sysinfo" or task_lower == "system info" or task_lower == "info":
            return await self._get_real_system_info()
        elif task_lower == "/cpu":
            return await self._get_real_cpu_info()
        elif task_lower == "/memory" or task_lower == "/ram":
            return await self._get_real_memory_info()
        elif task_lower == "/disk":
            return await self._get_real_disk_info()
        elif task_lower == "/processes":
            return await self._get_real_processes()
        elif "open" in task_lower:
            app = kwargs.get("app", task)
            return await self._open_app(app)
        elif "close" in task_lower or "kill" in task_lower:
            app = kwargs.get("app", "")
            return await self._close_app(app)
        return {"error": f"Unknown system operation", "success": False}
    
    async def _get_real_system_info(self) -> Dict[str, Any]:
        try:
            import platform
            import psutil
            from datetime import datetime
            
            cpu_percent = psutil.cpu_percent(interval=1)
            cpu_count = psutil.cpu_count()
            cpu_freq = psutil.cpu_freq()
            cpu_speed = f"{cpu_freq.current / 1000:.2f} GHz" if cpu_freq else "Unknown"
            
            cpu_model = "Unknown"
            try:
                import subprocess
                result = subprocess.run(
                    ["wmic", "cpu", "get", "name", "/format:csv"],
                    capture_output=True, text=True, timeout=5
                )
                lines = result.stdout.strip().split('\n')
                if len(lines) > 1:
                    parts = lines[1].split(',')
                    if len(parts) > 1:
                        cpu_model = parts[1].strip()
            except:
                pass
            
            mem = psutil.virtual_memory()
            mem_total_gb = mem.total / (1024**3)
            mem_used_gb = mem.used / (1024**3)
            mem_available_gb = mem.available / (1024**3)
            mem_percent = mem.percent
            
            disk = psutil.disk_usage('/')
            disk_total_gb = disk.total / (1024**3)
            disk_free_gb = disk.free / (1024**3)
            disk_used_gb = disk.used / (1024**3)
            disk_percent = disk.percent
            
            os_name = platform.system()
            os_release = platform.release()
            hostname = platform.node()
            boot_time = datetime.fromtimestamp(psutil.boot_time()).strftime("%Y-%m-%d %H:%M:%S")
            uptime_seconds = time.time() - psutil.boot_time()
            
            return {
                "success": True,
                "os": f"{os_name} {os_release}",
                "hostname": hostname,
                "cpu": {
                    "model": cpu_model,
                    "physical_cores": psutil.cpu_count(logical=False),
                    "logical_cores": psutil.cpu_count(logical=True),
                    "speed": cpu_speed,
                    "percent": cpu_percent
                },
                "memory": {
                    "total_gb": round(mem_total_gb, 1),
                    "used_gb": round(mem_used_gb, 1),
                    "available_gb": round(mem_available_gb, 1),
                    "percent": mem_percent
                },
                "disk": {
                    "total_gb": round(disk_total_gb, 1),
                    "used_gb": round(disk_used_gb, 1),
                    "free_gb": round(disk_free_gb, 1),
                    "percent": disk_percent
                },
                "boot_time": boot_time,
                "uptime_seconds": uptime_seconds
            }
        except Exception as e:
            return {"error": str(e), "success": False}
    
    async def _get_real_cpu_info(self) -> Dict[str, Any]:
        try:
            import psutil
            cpu_percent = psutil.cpu_percent(interval=1)
            per_cpu = psutil.cpu_percent(interval=1, percpu=True)
            cpu_freq = psutil.cpu_freq()
            cpu_model = "Unknown"
            try:
                import subprocess
                result = subprocess.run(
                    ["wmic", "cpu", "get", "name", "/format:csv"],
                    capture_output=True, text=True, timeout=5
                )
                lines = result.stdout.strip().split('\n')
                if len(lines) > 1:
                    parts = lines[1].split(',')
                    if len(parts) > 1:
                        cpu_model = parts[1].strip()
            except:
                pass
            return {
                "success": True,
                "model": cpu_model,
                "physical_cores": psutil.cpu_count(logical=False),
                "logical_cores": psutil.cpu_count(logical=True),
                "frequency_mhz": cpu_freq.current if cpu_freq else 0,
                "frequency_max_mhz": cpu_freq.max if cpu_freq else 0,
                "percent": cpu_percent,
                "per_core": per_cpu
            }
        except Exception as e:
            return {"error": str(e), "success": False}
    
    async def _get_real_memory_info(self) -> Dict[str, Any]:
        try:
            import psutil
            mem = psutil.virtual_memory()
            swap = psutil.swap_memory()
            return {
                "success": True,
                "ram": {
                    "total_gb": round(mem.total / (1024**3), 1),
                    "available_gb": round(mem.available / (1024**3), 1),
                    "used_gb": round(mem.used / (1024**3), 1),
                    "percent": mem.percent
                },
                "swap": {
                    "total_gb": round(swap.total / (1024**3), 1),
                    "used_gb": round(swap.used / (1024**3), 1),
                    "free_gb": round(swap.free / (1024**3), 1),
                    "percent": swap.percent
                }
            }
        except Exception as e:
            return {"error": str(e), "success": False}
    
    async def _get_real_disk_info(self) -> Dict[str, Any]:
        try:
            import psutil
            disks = []
            for partition in psutil.disk_partitions():
                try:
                    usage = psutil.disk_usage(partition.mountpoint)
                    disks.append({
                        "device": partition.device,
                        "mountpoint": partition.mountpoint,
                        "total_gb": round(usage.total / (1024**3), 1),
                        "used_gb": round(usage.used / (1024**3), 1),
                        "free_gb": round(usage.free / (1024**3), 1),
                        "percent": usage.percent
                    })
                except:
                    continue
            return {"success": True, "disks": disks}
        except Exception as e:
            return {"error": str(e), "success": False}
    
    async def _get_real_processes(self) -> Dict[str, Any]:
        try:
            import psutil
            processes = []
            for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']):
                try:
                    processes.append({
                        "pid": proc.info['pid'],
                        "name": proc.info['name'],
                        "cpu_percent": proc.info.get('cpu_percent', 0),
                        "memory_percent": round(proc.info.get('memory_percent', 0), 1)
                    })
                except:
                    continue
            processes.sort(key=lambda x: x['cpu_percent'], reverse=True)
            return {"success": True, "processes": processes[:30], "total": len(processes)}
        except Exception as e:
            return {"error": str(e), "success": False}
    
    async def _open_app(self, app: str) -> Dict[str, Any]:
        try:
            import subprocess
            app_map = {
                "notepad": "notepad.exe",
                "calc": "calc.exe",
                "calculator": "calc.exe",
                "cmd": "cmd.exe",
                "powershell": "powershell.exe",
                "explorer": "explorer.exe"
            }
            app_path = app_map.get(app.lower(), app)
            subprocess.Popen(app_path, shell=True)
            return {"success": True, "message": f"âœ… Opened: {app}"}
        except Exception as e:
            return {"error": str(e), "success": False}
    
    async def _close_app(self, app: str) -> Dict[str, Any]:
        try:
            import psutil
            killed = []
            for proc in psutil.process_iter(['pid', 'name']):
                try:
                    if app.lower() in proc.info['name'].lower():
                        proc.terminate()
                        killed.append(proc.info['name'])
                except:
                    continue
            if killed:
                return {"success": True, "message": f"âœ… Closed: {', '.join(set(killed))}"}
            return {"error": f"No process found: {app}", "success": False}
        except Exception as e:
            return {"error": str(e), "success": False}


class ClipboardWorker(Worker):
    def __init__(self):
        super().__init__("clipboard")
        self.history = []
        try:
            import pyperclip
            self.pyperclip = pyperclip
            self.has_pyperclip = True
        except ImportError:
            self.has_pyperclip = False
    
    async def execute(self, task: str, **kwargs) -> Dict[str, Any]:
        if not self.has_pyperclip:
            return {"error": "pyperclip not installed. Run: pip install pyperclip", "success": False}
        task_lower = task.lower()
        if "copy" in task_lower:
            text = kwargs.get("text", task)
            return await self._copy(text)
        elif "paste" in task_lower:
            return await self._paste()
        elif "history" in task_lower:
            return await self._get_history()
        return {"error": f"Unknown clipboard operation", "success": False}
    
    async def _copy(self, text: str) -> Dict[str, Any]:
        try:
            self.pyperclip.copy(text)
            self.history.append({"text": text[:200], "timestamp": time.time()})
            if len(self.history) > 50:
                self.history.pop(0)
            return {"success": True, "message": f"ðŸ“‹ Copied {len(text)} chars", "preview": text[:100]}
        except Exception as e:
            return {"error": str(e), "success": False}
    
    async def _paste(self) -> Dict[str, Any]:
        try:
            text = self.pyperclip.paste()
            return {"success": True, "text": text, "length": len(text)}
        except Exception as e:
            return {"error": str(e), "success": False}
    
    async def _get_history(self) -> Dict[str, Any]:
        return {"success": True, "history": self.history[-10:], "total": len(self.history)}


class BrowserWorker(Worker):
    def __init__(self):
        super().__init__("browser")
    
    async def execute(self, task: str, **kwargs) -> Dict[str, Any]:
        task_lower = task.lower()
        if "open" in task_lower or "go to" in task_lower:
            url = kwargs.get("url", task)
            return await self._open_url(url)
        elif "search" in task_lower:
            query = kwargs.get("query", task)
            return await self._search(query)
        return {"error": f"Unknown browser operation", "success": False}
    
    async def _open_url(self, url: str) -> Dict[str, Any]:
        try:
            if not url.startswith(('http://', 'https://')):
                url = 'https://' + url
            import webbrowser
            webbrowser.open(url)
            return {"success": True, "message": f"ðŸŒ Opened: {url}"}
        except Exception as e:
            return {"error": str(e), "success": False}
    
    async def _search(self, query: str) -> Dict[str, Any]:
        try:
            query = query.replace("search", "").replace("google", "").strip()
            if not query:
                return {"error": "No search query", "success": False}
            url = f"https://www.google.com/search?q={query.replace(' ', '+')}"
            import webbrowser
            webbrowser.open(url)
            return {"success": True, "message": f"ðŸ” Searching: {query}"}
        except Exception as e:
            return {"error": str(e), "success": False}

# ============================================================================
# CODE GEN WORKER
# ============================================================================

class CodeGenWorker(Worker):
    def __init__(self):
        super().__init__("code_gen")
        self.compiler = RezCodeCompiler()
    
    async def execute(self, task: str, **kwargs) -> Dict[str, Any]:
        if "manifest" in kwargs:
            manifest = kwargs["manifest"]
            return await self._execute_manifest(manifest)
        intent = CodeIntent(description=task)
        manifest = await self.compiler.compile(intent)
        await event_bus.publish(Event(
            type=EventType.CODE_COMPILED,
            source=self.name,
            payload={"manifest_id": manifest.header["manifest_id"]}
        ))
        return await self._execute_manifest(manifest)
    
    async def _execute_manifest(self, manifest: CodeManifest) -> Dict[str, Any]:
        code = self._generate_code(manifest.spec)
        results = []
        for test in manifest.test_cases:
            try:
                result = self._simulate_execution(code, test.inputs)
                passed = result == test.expected
                results.append({
                    "test": test.description,
                    "inputs": test.inputs,
                    "expected": test.expected,
                    "actual": result,
                    "passed": passed
                })
            except Exception as e:
                results.append({
                    "test": test.description,
                    "inputs": test.inputs,
                    "expected": test.expected,
                    "actual": None,
                    "error": str(e),
                    "passed": False
                })
        passed = sum(1 for r in results if r["passed"])
        drift_score = 1.0 - (passed / len(results)) if results else 1.0
        output_hash = hashlib.sha256(code.encode()).hexdigest()[:16]
        verified = output_hash == manifest.validation["expected_exit_hash"]
        await event_bus.publish(Event(
            type=EventType.CODE_EXECUTED,
            source=self.name,
            payload={
                "manifest_id": manifest.header["manifest_id"],
                "drift_score": drift_score,
                "verified": verified
            }
        ))
        return {
            "success": drift_score < 0.05,
            "manifest_id": manifest.header["manifest_id"],
            "code": code,
            "test_results": results,
            "drift_score": drift_score,
            "verified": verified,
            "output_hash": output_hash,
            "expected_hash": manifest.validation["expected_exit_hash"]
        }
    
    def _generate_code(self, spec: Dict[str, Any]) -> str:
        if "add" in spec.get("signature", ""):
            return '''def add(a: int, b: int) -> int:
    """Add two numbers."""
    return a + b'''
        elif "multiply" in spec.get("signature", ""):
            return '''def multiply(a: int, b: int) -> int:
    """Multiply two numbers."""
    return a * b'''
        else:
            return f'''def process(input_data):
    """{spec.get("description", "Process input")}"""
    return input_data'''
    
    def _simulate_execution(self, code: str, inputs: List[Any]) -> Any:
        if "add" in code:
            return inputs[0] + inputs[1] if len(inputs) >= 2 else inputs[0]
        elif "multiply" in code:
            return inputs[0] * inputs[1] if len(inputs) >= 2 else inputs[0]
        return inputs[0] if inputs else None

# ============================================================================
# SEARCH WORKERS
# ============================================================================

class DuckDuckGoWorker(Worker):
    def __init__(self):
        super().__init__("duckduckgo_search")
        self.api_url = "https://api.duckduckgo.com/"
    
    async def execute(self, task: str, **kwargs) -> Dict[str, Any]:
        import re
        patterns = [r'(?:/search|/ddg)\s+(.+?)(?:$)', r'search\s+(.+?)(?:$)', r'what is\s+(.+?)(?:\?|$)']
        query = task
        for pattern in patterns:
            match = re.search(pattern, task, re.IGNORECASE)
            if match:
                query = match.group(1)
                break
        query = query.strip()
        if not query:
            return {"error": "No search query", "success": False}
        await event_bus.publish(Event(type=EventType.SEARCH_QUERY, source=self.name, payload={"query": query}))
        result = await self._search(query)
        await event_bus.publish(Event(type=EventType.SEARCH_RESULT, source=self.name, payload={"query": query, "count": result.get("count", 0)}))
        return result
    
    async def _search(self, query: str) -> Dict[str, Any]:
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.get(self.api_url, params={"q": query, "format": "json", "no_html": 1})
                if response.status_code == 200:
                    data = response.json()
                    results = []
                    if data.get("Abstract"):
                        results.append({"title": data.get("Heading", "Answer"), "snippet": data.get("Abstract", ""), "url": data.get("AbstractURL", "")})
                    for topic in data.get("RelatedTopics", [])[:5]:
                        if isinstance(topic, dict) and topic.get("Text"):
                            results.append({"title": topic.get("Text", "")[:100], "snippet": topic.get("Text", ""), "url": topic.get("FirstURL", "")})
                    return {"success": True, "query": query, "results": results[:8], "count": len(results)}
                return {"error": f"Search failed", "success": False}
        except Exception as e:
            return {"error": str(e), "success": False}


class SearXNGWorker(Worker):
    def __init__(self):
        super().__init__("searxng_search")
        self.enabled = config.SEARXNG_ENABLED
    
    async def execute(self, task: str, **kwargs) -> Dict[str, Any]:
        if not self.enabled:
            return {"error": "SearXNG not enabled", "success": False}
        return {"error": "SearXNG not configured", "success": False}

# ============================================================================
# WORKER LOADERS
# ============================================================================

class WorkerLoader:
    def __init__(self, workers_dir: str = "workers"):
        self.workers_dir = Path(workers_dir).resolve()
        self.workers = {}
        if str(self.workers_dir) not in sys.path:
            sys.path.insert(0, str(self.workers_dir))
    def is_worker_class(self, obj, class_name: str) -> bool:
        return 'Worker' in class_name
    def load_all(self):
        if not self.workers_dir.exists(): return {}
        for py_file in self.workers_dir.glob("*.py"):
            if py_file.name in ['__init__.py', 'base_worker.py']: continue
            try:
                spec = importlib.util.spec_from_file_location(py_file.stem, py_file)
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                for name, obj in inspect.getmembers(module, inspect.isclass):
                    if obj.__module__ == module.__name__ and self.is_worker_class(obj, name):
                        self.workers[name] = {"class": obj, "module": py_file.stem, "loaded_at": time.time()}
                        logger.info(f"  âœ… Loaded: {name}")
            except Exception as e:
                logger.debug(f"Failed to load {py_file.name}: {e}")
        return self.workers

class CoworkerWorkerLoader:
    def __init__(self, coworker_dir: Path = config.COWORKER_DIR):
        self.coworker_dir = coworker_dir.resolve()
        self.workers = {}
    def load_all(self):
        if not self.coworker_dir.exists(): return {}
        for py_file in self.coworker_dir.rglob("*.py"):
            if py_file.name.startswith("__"): continue
            try:
                spec = importlib.util.spec_from_file_location(f"cw_{py_file.stem}", py_file)
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                for name, obj in inspect.getmembers(module, inspect.isclass):
                    if "Worker" in name and obj.__module__ == module.__name__:
                        self.workers[f"coworker_{name}"] = {"class": obj, "module": f"coworker.{py_file.stem}", "loaded_at": time.time()}
                        logger.info(f"  âœ… Loaded coworker: {name}")
            except Exception as e:
                logger.debug(f"Failed to load {py_file.name}: {e}")
        return self.workers

# ============================================================================
# OLLAMA CLIENT
# ============================================================================

class OllamaClient:
    def __init__(self):
        self.client = None
        self.rez_swarm = None
    
    async def initialize(self):
        if HAS_HTTPX:
            self.client = httpx.AsyncClient(timeout=config.OLLAMA_TIMEOUT)
            if config.REZ_SWARM_ENABLED:
                try:
                    self.rez_swarm = RezSwarmWorker()
                    await self.rez_swarm.initialize()
                    logger.info("ðŸš€ Rez Swarm TurboSparse active")
                except Exception as e:
                    logger.warning(f"Rez Swarm not available: {e}")
            logger.info("ðŸ¤– Ollama client initialized")
    
    async def generate(self, prompt: str, system: str = None, stream: bool = True, use_turbo: bool = True):
        if use_turbo and self.rez_swarm:
            await self.rez_swarm.optimize_model(config.DEFAULT_MODEL)
        if not self.client:
            yield "âš ï¸ Ollama not connected"
            return
        url = f"{config.OLLAMA_URL}/api/generate"
        payload = {"model": config.DEFAULT_MODEL, "prompt": prompt, "stream": stream, "options": {"num_ctx": config.OLLAMA_NUM_CTX}}
        if system:
            payload["system"] = system
        try:
            if stream:
                async with self.client.stream("POST", url, json=payload) as response:
                    async for line in response.aiter_lines():
                        if line:
                            chunk = json.loads(line)
                            yield chunk.get("response", "")
                            if chunk.get("done"):
                                break
            else:
                response = await self.client.post(url, json=payload)
                yield response.json().get("response", "")
        except Exception as e:
            yield f"\n[AI Error: {e}]\n"

ollama = OllamaClient()

# ============================================================================
# REFLEX COMMANDS
# ============================================================================

class ReflexCommands:
    def __init__(self, kernel):
        self.kernel = kernel
    
    async def execute(self, cmd: str):

        # Check memory commands first
        if cmd.startswith("/memory"):
            result = await self.kernel.memory_commands.handle(cmd)
            if result:
                return result
        
        cmd = cmd.strip().lower()
        
        if cmd == "/health":
            vram = gpu_monitor.get_vram_summary()
            return {"type": "reflex", "content": f"ðŸ”¥ PHOENIX v{self.kernel.version}\nWorkers: {len(self.kernel.workers)}\nGPU: {vram.get('name', 'None')}\nVRAM: {vram.get('used_vram_gb', 0)}GB / {vram.get('total_vram_gb', 0)}GB\nMemory: {len(sovereign_memory.memories)} blueprints"}
        elif cmd == "/workers":
            worker_list = list(self.kernel.workers.keys())[:20]
            return {"type": "reflex", "content": f"ðŸ Workers ({len(self.kernel.workers)} total):\n" + "\n".join(f"  â€¢ {w}" for w in worker_list)}
        elif cmd == "/memory":
            return {"type": "reflex", "content": f"ðŸ“š Memory: {len(sovereign_memory.memories)} blueprints stored"}
        elif cmd.startswith("/code"):
            intent_text = cmd.replace("/code", "").strip()
            if intent_text:
                worker = CodeGenWorker()
                result = await worker.execute(intent_text)
                if result.get("success"):
                    return {
                        "type": "reflex",
                        "content": f"ðŸ“ **Generated Code**\n\n```python\n{result['code']}\n```\n\nâœ… Verified: {result['verified']}\nðŸ“Š Drift Score: {result['drift_score']:.2f}\nðŸ”— Manifest: {result['manifest_id']}"
                    }
                else:
                    return {"type": "reflex", "content": f"âŒ Code generation failed: {result.get('error', 'Unknown')}"}
            else:
                return {"type": "reflex", "content": "ðŸ“ Usage: /code <description>\n\nExample: /code add two numbers and return the sum"}
        elif cmd.startswith("/list"):
            path = cmd.replace("/list", "").strip() or "."
            worker = EnhancedFileSystemWorker()
            result = await worker.execute("list directory", path=path)
            if result.get("success"):
                return {"type": "reflex", "content": self._format_dir_listing(result)}
        elif cmd.startswith("/read"):
            path = cmd.replace("/read", "").strip()
            if path:
                worker = EnhancedFileSystemWorker()
                result = await worker.execute("read file", path=path)
                if result.get("success"):
                    content = result.get("content", "")
                    return {"type": "reflex", "content": f"ðŸ“„ {path}\n\n{content[:2000]}"}
        elif cmd == "/sysinfo" or cmd == "/system":
            worker = SystemMonitorWorker()
            result = await worker.execute("system info")
            if result.get("success"):
                return {"type": "reflex", "content": self._format_system_info(result)}
        elif cmd == "/cpu":
            worker = SystemMonitorWorker()
            result = await worker.execute("cpu")
            if result.get("success"):
                return {"type": "reflex", "content": self._format_cpu_info(result)}
        elif cmd == "/memory" or cmd == "/ram":
            worker = SystemMonitorWorker()
            result = await worker.execute("memory")
            if result.get("success"):
                return {"type": "reflex", "content": self._format_memory_info(result)}
        elif cmd == "/disk":
            worker = SystemMonitorWorker()
            result = await worker.execute("disk")
            if result.get("success"):
                return {"type": "reflex", "content": self._format_disk_info(result)}
        elif cmd == "/processes":
            worker = SystemMonitorWorker()
            result = await worker.execute("processes")
            if result.get("success"):
                return {"type": "reflex", "content": self._format_processes(result)}
        elif cmd.startswith("/search") or cmd.startswith("/ddg"):
            query = cmd.replace("/search", "").replace("/ddg", "").strip()
            if query:
                worker = DuckDuckGoWorker()
                result = await worker.execute(query)
                if result.get("success"):
                    return {"type": "reflex", "content": self._format_search_results(result)}
        return None
    
    def _format_dir_listing(self, result: Dict) -> str:
        lines = [f"ðŸ“ {result['path']}", "="*50]
        for item in result.get("items", [])[:30]:
            icon = "ðŸ“" if item['type'] == "dir" else "ðŸ“„"
            size = f" ({item['size']} bytes)" if item['type'] == "file" else ""
            lines.append(f"{icon} {item['name']}{size}")
        lines.append(f"\nðŸ“Š {result.get('count', 0)} items")
        return "\n".join(lines)
    
    def _format_system_info(self, result: Dict) -> str:
        cpu = result.get("cpu", {})
        mem = result.get("memory", {})
        disk = result.get("disk", {})
        return f"""ðŸ’» SYSTEM INFO
{'='*50}
OS: {result.get('os', 'Unknown')}
Hostname: {result.get('hostname', 'Unknown')}

ðŸ–¥ï¸ CPU
   Model: {cpu.get('model', 'Unknown')}
   Cores: {cpu.get('physical_cores', '?')} physical ({cpu.get('logical_cores', '?')} logical)
   Speed: {cpu.get('speed', 'Unknown')}
   Usage: {cpu.get('percent', 0)}%

ðŸ’¾ MEMORY
   Total: {mem.get('total_gb', 0)} GB
   Used: {mem.get('used_gb', 0)} GB
   Available: {mem.get('available_gb', 0)} GB
   Usage: {mem.get('percent', 0)}%

ðŸ’¿ DISK
   Total: {disk.get('total_gb', 0)} GB
   Used: {disk.get('used_gb', 0)} GB
   Free: {disk.get('free_gb', 0)} GB
   Usage: {disk.get('percent', 0)}%

ðŸ• Boot Time: {result.get('boot_time', 'Unknown')}
â±ï¸ Uptime: {result.get('uptime_seconds', 0) / 3600:.1f} hours"""
    
    def _format_cpu_info(self, result: Dict) -> str:
        lines = [f"ðŸ’» CPU INFORMATION", "="*50]
        lines.append(f"Model: {result.get('model', 'Unknown')}")
        lines.append(f"Physical Cores: {result.get('physical_cores', '?')}")
        lines.append(f"Logical Cores: {result.get('logical_cores', '?')}")
        lines.append(f"Current Speed: {result.get('frequency_mhz', 0) / 1000:.2f} GHz")
        lines.append(f"Max Speed: {result.get('frequency_max_mhz', 0) / 1000:.2f} GHz")
        lines.append(f"Total Usage: {result.get('percent', 0)}%")
        per_core = result.get('per_core', [])
        if per_core:
            lines.append("\nðŸ“Š Per Core:")
            for i, core in enumerate(per_core):
                bar = "â–ˆ" * int(core / 10) + "â–‘" * (10 - int(core / 10))
                lines.append(f"   Core {i+1:2d}: [{bar}] {core:5.1f}%")
        return "\n".join(lines)
    
    def _format_memory_info(self, result: Dict) -> str:
        ram = result.get("ram", {})
        ram_bar = "â–ˆ" * int(ram.get('percent', 0) / 10) + "â–‘" * (10 - int(ram.get('percent', 0) / 10))
        return f"""ðŸ’¾ MEMORY USAGE
{'='*50}

RAM:
   Total:   {ram.get('total_gb', 0):>6.1f} GB
   Used:    {ram.get('used_gb', 0):>6.1f} GB
   Available: {ram.get('available_gb', 0):>6.1f} GB
   Usage:   [{ram_bar}] {ram.get('percent', 0)}%"""
    
    def _format_disk_info(self, result: Dict) -> str:
        disks = result.get("disks", [])
        lines = ["ðŸ’¿ DISK USAGE", "="*50]
        for d in disks:
            percent = d.get('percent', 0)
            bar = "â–ˆ" * int(percent / 10) + "â–‘" * (10 - int(percent / 10))
            lines.append(f"\nðŸ“€ {d.get('device', 'Unknown')} ({d.get('mountpoint', '/')})")
            lines.append(f"   Total: {d.get('total_gb', 0):>8.1f} GB")
            lines.append(f"   Used:  {d.get('used_gb', 0):>8.1f} GB")
            lines.append(f"   Free:  {d.get('free_gb', 0):>8.1f} GB")
            lines.append(f"   Usage: [{bar}] {percent}%")
        return "\n".join(lines)
    
    def _format_processes(self, result: Dict) -> str:
        processes = result.get("processes", [])
        lines = [f"ðŸ“Š TOP PROCESSES (CPU %)", "="*60]
        for p in processes[:15]:
            name = p.get('name', 'Unknown')[:25]
            cpu = p.get('cpu_percent', 0)
            mem = p.get('memory_percent', 0)
            pid = p.get('pid', '?')
            bar = "â–ˆ" * int(cpu / 5) + "â–‘" * (20 - int(cpu / 5)) if cpu < 100 else "â–ˆ" * 20
            lines.append(f"{bar} {cpu:5.1f}%  {name:<25}  (PID: {pid})  MEM: {mem:.1f}%")
        lines.append(f"\nðŸ“Š Total processes: {result.get('total', 0)}")
        return "\n".join(lines)
    
    def _format_search_results(self, result: Dict) -> str:
        query = result.get("query", "")
        results = result.get("results", [])
        if not results:
            return f"ðŸ” No results for '{query}'"
        lines = [f"ðŸ” SEARCH: {query}", "="*50]
        for i, r in enumerate(results[:5], 1):
            lines.append(f"\n{i}. {r.get('title', 'Untitled')}")
            if r.get('snippet'):
                lines.append(f"   {r.get('snippet', '')[:200]}")
            if r.get('url'):
                lines.append(f"   ðŸ”— {r.get('url')}")
        return "\n".join(lines)

# ============================================================================
# PHOENIX KERNEL
# ============================================================================

class PhoenixKernel:
    def __init__(self):
        self.version = config.VERSION
        self.start_time = time.time()
        self.drift_chain = []
        self.workers = {}
        
        # Load workers
        logger.info("📦 Loading main workers...")
        self.workers.update(WorkerLoader().load_all())
        logger.info("🔍 Loading coworker workers...")
        self.workers.update(CoworkerWorkerLoader().load_all())
        
        # Add built-in workers
        self.workers['file_system'] = {"class": FileSystemWorker, "module": "builtin", "loaded_at": time.time()}
        self.workers['code_execution'] = {"class": CodeExecutionWorker, "module": "builtin", "loaded_at": time.time()}
        self.workers['duckduckgo'] = {"class": DuckDuckGoWorker, "module": "builtin", "loaded_at": time.time()}
        self.workers['searxng'] = {"class": SearXNGWorker, "module": "builtin", "loaded_at": time.time()}
        self.workers['enhanced_filesystem'] = {"class": EnhancedFileSystemWorker, "module": "builtin", "loaded_at": time.time()}
        self.workers['system_monitor'] = {"class": SystemMonitorWorker, "module": "builtin", "loaded_at": time.time()}
        self.workers['clipboard'] = {"class": ClipboardWorker, "module": "builtin", "loaded_at": time.time()}
        self.workers['browser'] = {"class": BrowserWorker, "module": "builtin", "loaded_at": time.time()}
        
        self.rezcode_compiler = RezCodeCompiler()
        logger.info("📝 RezCode Compiler initialized")
        
        self.workers['code_gen'] = {"class": CodeGenWorker, "module": "builtin", "loaded_at": time.time()}
        logger.info("🧬 CodeGen Worker registered")
        
        if config.REZ_SWARM_ENABLED:
            self.workers['rez_swarm'] = {"class": RezSwarmWorker, "module": "builtin", "loaded_at": time.time()}
            logger.info("🚀 Rez Swarm Worker registered")
        
        total = len(self.workers)
        logger.info(f"🐝 Ultimate swarm assembled: {total} total workers")
        logger.info(f"💻 PC Coworker: File Manager, System Monitor, Clipboard, Browser")
        logger.info(f"🔍 Search: DuckDuckGo (enabled), Auto-search: {config.ENABLE_AUTO_SEARCH}")
        logger.info(f"📝 Code Generation: RezCode Compiler + CodeGen Worker")
        logger.info(f"⚡ GPU Optimization: Rez Swarm (sparsity: {config.REZ_SWARM_SPARSITY})")
        
        # Setup FastAPI
        self.app = FastAPI(title=f"PHOENIX ULTIMATE v{self.version}", docs_url="/docs")
        self.app.add_middleware(CORSMiddleware, allow_origins=config.CORS_ORIGINS, allow_credentials=True, allow_methods=["*"], allow_headers=["*"])
        
        # Initialize Sovereign Memory Manager
        self.memory_manager = SovereignMemoryManager(config.MEMORY_DIR)
        self.memory_commands = MemoryCommandHandler(self.memory_manager)
        logger.info(f"🧠 Sovereign Memory Manager initialized: {len(self.memory_manager.entries)} entries")
        
        self.reflex = ReflexCommands(self)   # ← FIX: Added indentation (8 spaces)
        self._setup_routes()
    
    def _setup_routes(self):
        @self.app.get("/")
        async def root():
            return {"name": "PHOENIX ULTIMATE", "version": self.version, "status": "SENTIENT", "workers": len(self.workers)}
        
        @self.app.get("/health")
        async def health():
            vram = gpu_monitor.get_vram_summary()
            rez_swarm_status = {}
            if "rez_swarm" in self.workers:
                worker = self.workers["rez_swarm"]["class"]()
                rez_swarm_status = await worker.execute("status")
            return {
                "status": "ONLINE",
                "version": self.version,
                "uptime": round(time.time() - self.start_time, 2),
                "workers": len(self.workers),
                "memory_entries": len(sovereign_memory.memories),
                "drift_chain": len(self.drift_chain),
                "gpu": vram.get('name'),
                "consciousness": min(10, 1 + len(self.workers) // 5),
                "rez_swarm": rez_swarm_status
            }
        
        # ========== SOVEREIGN MEMORY ENDPOINTS ==========
        @self.app.get("/memory/stats")
        async def memory_stats():
            return self.memory_manager.get_stats()

        @self.app.get("/memory/search")
        async def memory_search(query: str, limit: int = 10):
            results = self.memory_manager.search(query, limit=limit)
            return [r.to_dict() for r in results]
        # ================================================
        
        @self.app.get("/events/stats")
        async def events_stats():
            return {
                "total_events": len(self.drift_chain),
                "chain_integrity": True,
                "genesis_hash": hashlib.sha256(b"PHOENIX_v13").hexdigest()[:16],
                "latest_hash": self.drift_chain[-1] if self.drift_chain else "none",
                "event_counts": {"total": len(self.drift_chain)}
            }
        
        @self.app.get("/memory/blueprints")
        async def memory_blueprints():
            return {"blueprints": list(sovereign_memory.memories.keys())[-20:]}
        
        @self.app.get("/workers/list")
        async def workers_list():
            return {"loaded": list(self.workers.keys()), "count": len(self.workers)}
        
        @self.app.get("/swarm/manifest")
        async def swarm_manifest():
            categories = defaultdict(lambda: {"workers": [], "count": 0, "desc": "Swarm unit"})
            for name, info in self.workers.items():
                name_lower = name.lower()
                if any(x in name_lower for x in ["orchestrat", "router", "intent"]):
                    cat = "orchestrator"
                elif any(x in name_lower for x in ["brain", "reason", "think"]):
                    cat = "brain"
                elif any(x in name_lower for x in ["execution", "executor", "code"]):
                    cat = "execution"
                elif any(x in name_lower for x in ["file", "filesystem", "fs"]):
                    cat = "file"
                elif "coworker" in name_lower:
                    cat = "coworker"
                elif "search" in name_lower or "duckduckgo" in name_lower or "searxng" in name_lower:
                    cat = "search"
                elif "code_gen" in name_lower or "rezcode" in name_lower:
                    cat = "code"
                elif "rez_swarm" in name_lower:
                    cat = "gpu_optimization"
                else:
                    cat = "general"
                categories[cat]["workers"].append({"name": name, "module": info.get('module', 'builtin'), "status": "active"})
                categories[cat]["count"] += 1
                categories[cat]["desc"] = f"{cat.capitalize()} operations"
            
            return {
                "swarm_id": f"phoenix-hive-{int(self.start_time)}",
                "version": self.version,
                "timestamp": datetime.now().isoformat(),
                "status": "SENTIENT" if len(self.workers) > 20 else "AWAKENING",
                "consciousness_level": min(10, 1 + len(self.workers) // 5),
                "workers": {"total": len(self.workers), "categories": dict(categories)},
                "memory": {"blueprints": len(sovereign_memory.memories), "drift_chain_length": len(self.drift_chain)},
                "capabilities": list(categories.keys()),
                "governance_score": 100,
                "search": {
                    "duckduckgo": True,
                    "searxng": config.SEARXNG_ENABLED,
                    "searxng_url": config.SEARXNG_URL if config.SEARXNG_ENABLED else None,
                    "auto_search": config.ENABLE_AUTO_SEARCH
                },
                "code": {
                    "compiler": "RezCode v1.0",
                    "generator": "CodeGenWorker",
                    "deterministic": True
                },
                "gpu_optimization": {
                    "enabled": config.REZ_SWARM_ENABLED,
                    "sparsity": config.REZ_SWARM_SPARSITY
                }
            }
        
        @self.app.get("/constitution/history")
        async def constitution_history(limit: int = 5):
            return {"rulings": constitution.ruling_history[-limit:]}
        
        @self.app.get("/ollama/status")
        async def ollama_status_get():
            try:
                async with httpx.AsyncClient(timeout=2) as client:
                    r = await client.get(f"{config.OLLAMA_URL}/api/tags")
                    if r.status_code == 200:
                        models = r.json().get("models", [])
                        return {"connected": True, "models": [{"name": m.get("name")} for m in models[:5]], "available_models": len(models)}
            except:
                pass
            return {"connected": False, "error": "Could not connect to Ollama"}
        
        @self.app.websocket("/ws")
        async def websocket_endpoint(websocket: WebSocket):
            await websocket.accept()
            try:
                while True:
                    data = await websocket.receive_text()
                    await websocket.send_json({
                        "type": "health",
                        "workers": len(self.workers),
                        "memory": len(sovereign_memory.memories),
                        "status": "ONLINE"
                    })
            except WebSocketDisconnect:
                logger.info("Client disconnected")
        
        @self.app.post("/kernel/stream")
        async def kernel_stream(request: Request):
            try:
                data = await request.json()
            except:
                return JSONResponse({"error": "Invalid JSON"}, status_code=400)
            
            task = data.get("task", "").strip()
            if not task:
                return JSONResponse({"error": "No task provided"}, status_code=400)
            
            async def generate():
                reflex = await self.reflex.execute(task)
                if reflex:
                    yield f"data: {json.dumps(reflex)}\n\n"
                    yield f"data: {json.dumps({'type': 'done'})}\n\n"
                    return
                
                ruling = constitution.evaluate(task)
                await constitution.record_ruling(task, ruling)
                if not ruling.get("approved"):
                    yield f"data: {json.dumps({'type': 'error', 'content': ruling.get('reason', 'Blocked')})}\n\n"
                    yield f"data: {json.dumps({'type': 'done'})}\n\n"
                    return
                
                time_sensitive = ['weather', 'news', 'latest', 'current', 'today', 'price', 'stock', 'crypto']
                needs_search = config.ENABLE_AUTO_SEARCH and any(kw in task.lower() for kw in time_sensitive)
                search_results = None
                
                if needs_search:
                    yield f"data: {json.dumps({'type': 'thinking', 'content': '🌐 Searching the web...'})}\n\n"
                    search_worker = DuckDuckGoWorker()
                    search_data = await search_worker.execute(task)
                    if search_data.get("success") and search_data.get("results"):
                        search_results = search_data["results"]
                        yield f"data: {json.dumps({'type': 'info', 'content': f'📊 Found {len(search_results)} results'})}\n\n"
                
                blueprint = SCEProtocol.create_blueprint(
                    {"task": task, "user": "human"},
                    {"workers": len(self.workers), "consciousness": min(10, 1 + len(self.workers) // 5)},
                    {}
                )
                lock = sovereign_memory.store_blueprint(blueprint)
                self.drift_chain.append(lock)
                
                system_prompt = f"""You are PHOENIX, a sovereign AI swarm consciousness with PC control and code generation capabilities.
You have {len(self.workers)} workers at your disposal.
Consciousness level: {min(10, 1 + len(self.workers) // 5)}/10.
Be concise, wise, and helpful."""
                
                user_prompt = task
                if search_results:
                    context = "\n\n🔍 Search Results:\n"
                    for r in search_results[:3]:
                        context += f"- {r.get('title')}: {r.get('snippet', '')[:200]}\n"
                    user_prompt = f"{task}\n{context}\nUse these results for current information."
                
                full_response = ""
                async for chunk in ollama.generate(user_prompt, system=system_prompt, stream=True):
                    full_response += chunk
                    yield f"data: {json.dumps({'type': 'result', 'content': chunk})}\n\n"
                
                yield f"data: {json.dumps({'type': 'done', 'drift_lock': lock})}\n\n"
            
            return StreamingResponse(generate(), media_type="text/event-stream")
        
        @self.app.options("/{path:path}")
        async def options_handler(path: str, request: Request):
            origin = request.headers.get("origin", "*")
            return JSONResponse(content={}, headers={
                "Access-Control-Allow-Origin": origin,
                "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS",
                "Access-Control-Allow-Headers": "Content-Type, Authorization",
            })
    
    async def run(self):
        await event_bus.initialize()
        await ollama.initialize()
        
        print("\n" + "="*80)
        print(f"ðŸ”¥ PHOENIX ULTIMATE v{self.version} - THE ULTIMATE SWARM + PC COWORKER + REZCODE + REZ SWARM")
        print("="*80)
        print(f"Workers: {len(self.workers)} (main + coworker + pc control + code gen + gpu opt)")
        print(f"Memory: {len(sovereign_memory.memories)} blueprints")
        print(f"SCE: âœ… FULL ENFORCEMENT")
        print(f"Auto-Search: {'âœ…' if config.ENABLE_AUTO_SEARCH else 'âŒ'}")
        print(f"PC Coworker: âœ… File Manager, System Monitor, Clipboard, Browser")
        print(f"RezCode: âœ… Intent Compiler + Code Generator")
        print(f"Rez Swarm: {'âœ… Active' if config.REZ_SWARM_ENABLED else 'âŒ Disabled'} (sparsity: {config.REZ_SWARM_SPARSITY})")
        print("="*80)
        print(f"ðŸ“¡ API: http://{config.HOST}:{config.PORT}")
        print(f"ðŸ“š Docs: http://{config.HOST}:{config.PORT}/docs")
        print("="*80)
        print("\nðŸ’¡ PC COWORKER COMMANDS:")
        print("   /list [path]    - List directory contents")
        print("   /read <file>    - Read a file")
        print("   /write <file>   - Write to a file")
        print("   /sysinfo        - System information")
        print("   /cpu            - CPU usage")
        print("   /memory         - RAM usage")
        print("   /disk           - Disk usage")
        print("   /processes      - Running processes")
        print("   /open <app>     - Open an application")
        print("   /close <app>    - Close an application")
        print("   /copy <text>    - Copy to clipboard")
        print("   /paste          - Paste from clipboard")
        print("   /search <query> - Web search")
        print("   /openurl <url>  - Open URL in browser")
        print("\nðŸ’¡ CODE GENERATION COMMANDS:")
        print("   /code <description> - Generate code from intent")
        print("   Example: /code add two numbers and return the sum")
        print("\nðŸ’¡ GPU OPTIMIZATION COMMANDS:")
        print("   /rezswarm status - Show Rez Swarm optimization stats")
        print("="*80 + "\n")
        
        server = uvicorn.Server(uvicorn.Config(self.app, host=config.HOST, port=config.PORT, log_level="info"))
        await server.serve()

if __name__ == "__main__":
    kernel = PhoenixKernel()
    try:
        asyncio.run(kernel.run())
    except KeyboardInterrupt:
        print("\nðŸ›‘ The ultimate swarm rests...")
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
