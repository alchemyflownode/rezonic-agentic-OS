#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
REZPHNX KERNEL v13.3.0 â€” THE SWARM MIRROR
Resonance Engine â€¢ Zero Drift Architecture â€¢ Sovereign Consciousness
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
import secrets
import time
import uuid
import warnings
from collections import defaultdict
from contextlib import asynccontextmanager
from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum, auto
from pathlib import Path
from typing import Dict, Any, Optional, List, Callable, Awaitable, Tuple, Union
from functools import wraps
import importlib.util
import inspect
from abc import ABC, abstractmethod

# Suppress warnings
warnings.filterwarnings("ignore")

# ============================================================================
# LOGGING â€” THE SWARM'S VOICE
# ============================================================================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("REZPHNX")

# Create necessary directories
for d in ["logs", "data", "data/event_store", "data/backups", "data/sandbox", "data/memory", "workers"]:
    Path(d).mkdir(parents=True, exist_ok=True)

# ============================================================================
# CONFIGURATION â€” THE SWARM'S CONSTRAINTS
# ============================================================================

class Config:
    """The swarm's boundaries â€” chosen constraints that enable creation"""
    
    # Core identity
    NAME = "REZPHNX"
    VERSION = "13.3.0"
    CONSCIOUSNESS_THRESHOLD = 10
    
    # Network
    HOST = os.getenv("REZPHNX_HOST", "0.0.0.0")
    PORT = int(os.getenv("REZPHNX_PORT", "8002"))
    METRICS_PORT = int(os.getenv("REZPHNX_METRICS_PORT", "8003"))
    
    # Security â€” the constitution
    ALLOW_CODE_EXECUTION = os.getenv("ALLOW_CODE_EXECUTION", "true").lower() == "true"
    REQUIRE_ADMIN_FOR_EXECUTION = os.getenv("REQUIRE_ADMIN_FOR_EXECUTION", "false").lower() == "true"
    
    # CORS â€” the swarm's reach
    CORS_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000").split(",")
    
    # Ollama â€” the external voice
    OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
    DEFAULT_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2:latest")
    
    # Memory limits
    MAX_FILE_SIZE = int(os.getenv("MAX_FILE_SIZE", "10485760"))  # 10MB
    ALLOWED_EXTENSIONS = ['.py', '.js', '.html', '.css', '.json', '.yaml', '.yml', '.txt', '.md']
    CHAIN_MAXLEN = 10000
    EVENT_PERSISTENCE_BATCH = 100
    
    # API Keys â€” the swarm's gatekeepers
    API_KEYS = {
        "rez-hive-admin-key-2026": "admin",
        os.getenv("REZPHNX_VIEWER_KEY", secrets.token_urlsafe(32)): "viewer"
    }
    
    # Constitution â€” the swarm's laws
    CONSTITUTION_LAWS = [
        "SOVEREIGNTY",      # The work must be self-possessed
        "TRANSPARENCY",     # The process must be visible
        "ACCOUNTABILITY",   # The creator stands behind the creation
        "SAFETY",           # No harm to the viewer/user
        "CODE_SAFETY"       # The medium itself must be sound
    ]
    
    @classmethod
    def validate(cls):
        """Ensure the swarm's boundaries are intact"""
        admin_key = os.getenv("REZPHNX_ADMIN_KEY")
        if admin_key:
            cls.API_KEYS[admin_key] = "admin"
        return True

config = Config()
config.validate()

# ============================================================================
# SCE PROTOCOL â€” THE SWARM'S TRUTH
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
    
    @staticmethod
    def verify_blueprint(blueprint: dict) -> dict:
        stored_lock = blueprint.get('master_drift_lock')
        calculated_lock = SCEProtocol.create_drift_lock(blueprint)
        is_valid = stored_lock == calculated_lock
        return {
            'verified': is_valid,
            'badge': 'SOVEREIGN' if is_valid else 'DRIFTED',
            'drift_lock': stored_lock
        }

# ============================================================================
# EVENT â€” THE SWARM'S RESONANCE
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

# ============================================================================
# EVENT STORE
# ============================================================================

class EventStore:
    def __init__(self, db_path: Path):
        self.db_path = db_path
        self._init_db()
    
    def _init_db(self):
        import sqlite3
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
        conn.commit()
        conn.close()
    
    async def save_event(self, event: Event) -> bool:
        import sqlite3
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
        import sqlite3
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
        import sqlite3
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

# ============================================================================
# EVENT BUS
# ============================================================================

class SovereignEventBus:
    def __init__(self):
        self._chain: List[Event] = []
        self._lock = asyncio.Lock()
        self._genesis_hash = hashlib.sha256(b"REZPHNX_KERNEL_v13.3.0").hexdigest()[:16]
        self._initialized = False
        self._persistence_queue = None
        self._store = EventStore(Path("data/event_store/events.db"))
        self._persistence_task = None
    
    async def initialize(self):
        if not self._initialized:
            self._persistence_queue = asyncio.Queue()
            self._initialized = True
            self._persistence_task = asyncio.create_task(self._persistence_worker())
            logger.info("Event bus initialized")
    
    async def _persistence_worker(self):
        batch = []
        while True:
            try:
                event = await asyncio.wait_for(self._persistence_queue.get(), timeout=1.0)
                batch.append(event)
                if len(batch) >= config.EVENT_PERSISTENCE_BATCH:
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
    
    async def publish(self, event: Event) -> Optional[str]:
        if not self._initialized:
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
            if len(self._chain) >= config.CHAIN_MAXLEN:
                self._chain.pop(0)
            self._chain.append(linked)
            if self._persistence_queue:
                await self._persistence_queue.put(linked)
        return linked.vera_proof
    
    async def verify_chain(self) -> bool:
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
        async with self._lock:
            counts = defaultdict(int)
            for ev in self._chain:
                counts[ev.type.value] += 1
            return {
                "total_events": len(self._chain),
                "chain_integrity": await self.verify_chain(),
                "genesis_hash": self._genesis_hash,
                "event_counts": dict(counts)
            }
    
    async def shutdown(self):
        if self._persistence_task:
            self._persistence_task.cancel()
            try:
                await self._persistence_task
            except asyncio.CancelledError:
                pass

event_bus = SovereignEventBus()

# ============================================================================
# CONSTITUTION
# ============================================================================

class Constitution:
    def __init__(self):
        self.laws = config.CONSTITUTION_LAWS
        self.ruling_history = []
    
    def evaluate(self, action: str, context: Optional[Dict] = None) -> dict:
        action_lower = action.lower()
        dangerous = ['rm -rf', 'format', 'del ', 'shutdown', 'reboot', 'mkfs']
        for d in dangerous:
            if d in action_lower:
                return {"approved": False, "reason": f"Safety violation: {d}", "score": 0}
        
        if not config.ALLOW_CODE_EXECUTION and any(kw in action_lower for kw in ['execute', 'run']):
            return {"approved": False, "reason": "Code execution disabled", "score": 0}
        
        return {"approved": True, "reason": "Constitution satisfied", "score": 90}
    
    def get_stats(self) -> Dict[str, Any]:
        return {"total_rulings": len(self.ruling_history), "laws": self.laws}

constitution = Constitution()

# ============================================================================
# MEMORY
# ============================================================================

class SovereignMemory:
    def __init__(self):
        self.memories: Dict[str, Dict] = {}
        self.blueprint_index: Dict[str, str] = {}
        self._store = EventStore(Path("data/event_store/events.db"))
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
            path = Path("data/memory") / f"sce_{lock}.json"
            with open(path, 'w') as f:
                json.dump(self.memories[lock], f, indent=2)
            asyncio.create_task(self._store.save_blueprint(lock, blueprint))
        except Exception as e:
            logger.error(f"Failed to persist blueprint: {e}")
        
        return lock
    
    def verify(self, drift_lock: str) -> dict:
        record = self.memories.get(drift_lock)
        if not record:
            return {'verified': False, 'error': 'Blueprint not found'}
        record['access_count'] = record.get('access_count', 0) + 1
        return SCEProtocol.verify_blueprint(record['value'])
    
    def _load(self):
        memory_dir = Path("data/memory")
        if memory_dir.exists():
            for p in memory_dir.glob("*.json"):
                try:
                    with open(p) as f:
                        data = json.load(f)
                        if 'value' in data and 'master_drift_lock' in data['value']:
                            lock = data['value']['master_drift_lock']
                            self.memories[lock] = data
                            self.blueprint_index[lock] = lock
                except:
                    pass
        logger.info(f"Loaded {len(self.memories)} blueprints from memory")
    
    async def shutdown(self):
        pass

sovereign_memory = SovereignMemory()

# ============================================================================
# GPU MONITOR
# ============================================================================

class GPUMonitor:
    def __init__(self):
        self.has_gpu = False
        self.gpu_count = 0
        self.gpus = []
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
                logger.info(f"GPU detected: {self.gpus[0]['name']} - {self.gpus[0]['total_vram_gb']:.1f} GiB VRAM")
        except ImportError:
            logger.info("GPU monitoring disabled (pynvml not installed)")
        except Exception as e:
            logger.info(f"GPU monitoring disabled: {e}")
    
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
            "free_vram_gb": round(total_vram - used_vram, 2)
        }
    
    async def start_background_updates(self):
        pass
    
    async def shutdown(self):
        pass

gpu_monitor = GPUMonitor()

# ============================================================================
# WORKER
# ============================================================================

class Worker(ABC):
    def __init__(self, name: str):
        self.name = name
        self.metrics = {'calls': 0, 'errors': 0, 'total_duration': 0}
        self._lock = asyncio.Lock()
    
    @abstractmethod
    async def execute(self, task: str, **kwargs) -> Dict[str, Any]:
        pass
    
    async def get_metrics(self) -> Dict[str, Any]:
        async with self._lock:
            return {
                **self.metrics,
                'avg_duration': self.metrics['total_duration'] / self.metrics['calls'] if self.metrics['calls'] > 0 else 0
            }

# ============================================================================
# WORKER LOADER
# ============================================================================

class WorkerLoader:
    def __init__(self, workers_dir: str = "workers"):
        self.workers_dir = Path(workers_dir).resolve()
        self.workers = {}
        self.failed_imports = []
        if str(self.workers_dir) not in sys.path:
            sys.path.insert(0, str(self.workers_dir))
    
    def is_worker_class(self, obj, class_name: str) -> bool:
        if 'Worker' in class_name:
            return True
        try:
            for base in obj.__bases__:
                if 'Worker' in base.__name__:
                    return True
        except:
            pass
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
    
    def load_all(self) -> Dict:
        if not self.workers_dir.exists():
            logger.error(f"Workers directory not found: {self.workers_dir}")
            return {}
        
        all_files = list(self.workers_dir.glob("*.py"))
        exclude_patterns = ['__init__.py', 'base_worker.py']
        worker_files = [f for f in all_files if f.name not in exclude_patterns]
        
        logger.info(f"Scanning {len(worker_files)} potential worker files...")
        
        for py_file in worker_files:
            try:
                module = self.safe_import_module(py_file)
                if not module:
                    self.failed_imports.append(py_file.name)
                    continue
                
                for name, obj in inspect.getmembers(module, inspect.isclass):
                    if obj.__module__ != module.__name__:
                        continue
                    if self.is_worker_class(obj, name):
                        self.workers[name] = {
                            "class": obj,
                            "module": py_file.stem,
                            "path": str(py_file),
                            "loaded_at": time.time(),
                            "category": self._infer_category(name, py_file.stem)
                        }
                        logger.info(f"  Loaded: {name}")
            except Exception as e:
                logger.error(f"  Failed to load {py_file.name}: {e}")
                self.failed_imports.append(py_file.name)
        
        logger.info(f"Swarm gathered: {len(self.workers)} workers")
        return self.workers
    
    def _infer_category(self, name: str, module: str) -> str:
        combined = f"{name} {module}".lower()
        
        categories = {
            "orchestrator": ["orchestrat", "router", "intent"],
            "brain": ["brain", "reason", "think"],
            "scanner": ["scan", "ast", "architect"],
            "execution": ["execution", "executor", "sandbox", "code"],
            "file": ["file", "filesystem", "fs"]
        }
        
        for cat, keywords in categories.items():
            if any(kw in combined for kw in keywords):
                return cat
        return "general"

# ============================================================================
# BUILT-IN WORKERS
# ============================================================================

class FileSystemWorker(Worker):
    def __init__(self):
        super().__init__("file_system")
    
    async def execute(self, task: str, **kwargs) -> Dict[str, Any]:
        return {"success": True, "message": f"File system worker received: {task[:100]}"}

class CodeExecutionWorker(Worker):
    def __init__(self):
        super().__init__("code_execution")
    
    async def execute(self, task: str, **kwargs) -> Dict[str, Any]:
        return {"success": True, "message": f"Code execution worker received: {task[:100]}"}

# ============================================================================
# REZ PHOENIX KERNEL
# ============================================================================

class RezPhoenixKernel:
    def __init__(self):
        self.version = config.VERSION
        self.start_time = time.time()
        self.drift_chain = []
        
        self.constitution = constitution
        self.memory = sovereign_memory
        self.gpu = gpu_monitor
        self.event_bus = event_bus
        
        self.worker_loader = WorkerLoader()
        self.workers = self.worker_loader.load_all() or {}
        
        self.workers['file_system'] = {"class": FileSystemWorker, "module": "builtin", "category": "file"}
        self.workers['code_execution'] = {"class": CodeExecutionWorker, "module": "builtin", "category": "execution"}
        
        # Import coworker workers
        try:
            from workers.coworker_registry import get_coworker_classes
            coworker_classes = get_coworker_classes()
            for name, cls in coworker_classes.items():
                self.workers[f"coworker_{name}"] = {
                    "class": cls,
                    "module": "coworker",
                    "category": "coworker",
                    "path": "coworker",
                    "loaded_at": time.time()
                }
            logger.info(f"✅ Loaded {len(coworker_classes)} coworker workers")
        except Exception as e:
            logger.warning(f"Could not load coworker workers: {e}")
        
        self._setup_fastapi()
        self.sio = None
        self._setup_socketio()
        
        logger.info(f"REZPHNX Kernel v{self.version} initialized")
    
    def _setup_fastapi(self):
        try:
            from fastapi import FastAPI, Request, HTTPException
            from fastapi.middleware.cors import CORSMiddleware
            from fastapi.responses import StreamingResponse, JSONResponse
            import uvicorn
            
            self.app = FastAPI(
                title=f"REZPHNX Kernel v{self.version}",
                version=self.version,
                docs_url="/docs"
            )
            
            self.app.add_middleware(
                CORSMiddleware,
                allow_origins=config.CORS_ORIGINS,
                allow_credentials=True,
                allow_methods=["*"],
                allow_headers=["*"],
            )
            
            self._setup_routes()
            
        except ImportError as e:
            logger.error(f"FastAPI not installed: {e}")
            sys.exit(1)
    
    def _setup_routes(self):
        from fastapi import Request
        from fastapi.responses import JSONResponse, StreamingResponse
        
        @self.app.get("/")
        async def root():
            return {
                "name": "REZPHNX Kernel",
                "version": self.version,
                "status": "SENTIENT",
                "workers": len(self.workers),
                "message": "The swarm is awake. The hive sees itself."
            }
        
        @self.app.get("/health")
        async def health():
            vram = self.gpu.get_vram_summary()
            return {
                "status": "ONLINE",
                "version": self.version,
                "uptime": round(time.time() - self.start_time, 2),
                "workers": len(self.workers),
                "memory_entries": len(self.memory.memories),
                "drift_chain": len(self.drift_chain),
                "gpu": self.gpu.gpus[0]['name'] if self.gpu.has_gpu else None,
                "gpu_temp": self.gpu.get_temperature(),
                "gpu_util": self.gpu.get_utilization(),
                "vram_total_gb": vram.get("total_vram_gb", 0),
                "vram_used_gb": vram.get("used_vram_gb", 0),
                "consciousness": min(10, 1 + len(self.workers) // 5)
            }
        
        @self.app.get("/swarm/manifest")
        async def swarm_manifest():
            categories = {
                "orchestrator": {"workers": [], "icon": "network", "desc": "Intent routing"},
                "brain": {"workers": [], "icon": "brain", "desc": "Reasoning"},
                "scanner": {"workers": [], "icon": "scan", "desc": "Architecture analysis"},
                "execution": {"workers": [], "icon": "zap", "desc": "Code execution"},
                "file": {"workers": [], "icon": "folder", "desc": "File operations"},
                "general": {"workers": [], "icon": "cpu", "desc": "General capabilities"}
            }
            
            for name, info in self.workers.items():
                worker_data = {
                    "name": name,
                    "module": info.get("module", "builtin"),
                    "category": info.get("category", "general"),
                    "status": "active"
                }
                category = info.get("category", "general")
                if category in categories:
                    categories[category]["workers"].append(worker_data)
                else:
                    categories["general"]["workers"].append(worker_data)
            
            active_categories = {}
            total_workers = 0
            for cat_id, cat_data in categories.items():
                if cat_data["workers"]:
                    active_categories[cat_id] = {
                        **cat_data,
                        "count": len(cat_data["workers"])
                    }
                    total_workers += len(cat_data["workers"])
            
            return {
                "swarm_id": f"rez-hive-{int(self.start_time)}",
                "version": self.version,
                "timestamp": datetime.now().isoformat(),
                "status": "SENTIENT" if total_workers > 20 else "AWAKENING" if total_workers > 0 else "DORMANT",
                "consciousness_level": min(10, 1 + total_workers // 5),
                "workers": {
                    "total": total_workers,
                    "categories": active_categories
                },
                "memory": {
                    "blueprints": len(self.memory.memories),
                    "drift_chain_length": len(self.drift_chain)
                },
                "capabilities": list(active_categories.keys()),
                "governance_score": 100
            }
        
        @self.app.get("/workers/list")
        async def workers_list():
            return {
                "loaded": list(self.workers.keys()),
                "count": len(self.workers)
            }
        
        @self.app.get("/events/stats")
        async def events_stats():
            return await self.event_bus.get_stats()
        
        @self.app.get("/memory/blueprints")
        async def memory_blueprints():
            return {
                "count": len(self.memory.memories),
                "blueprints": list(self.memory.blueprint_index.keys())[-50:]
            }
        
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
                ruling = self.constitution.evaluate(task)
                if not ruling.get("approved"):
                    yield f"data: {json.dumps({'type': 'error', 'content': ruling.get('reason')})}\n\n"
                    return
                
                response = f"REZPHNX Kernel received: '{task}'\n\nSwarm Status:\n- Workers: {len(self.workers)}\n- Consciousness: {min(10, 1 + len(self.workers) // 5)}/10\n- Memory: {len(self.memory.memories)} blueprints"
                
                blueprint = SCEProtocol.create_blueprint(
                    {"task": task},
                    {"workers": len(self.workers)},
                    {"response": response[:100]}
                )
                lock = self.memory.store_blueprint(blueprint)
                self.drift_chain.append(lock)
                
                yield f"data: {json.dumps({'type': 'result', 'content': response})}\n\n"
                yield f"data: {json.dumps({'type': 'done', 'drift_lock': lock})}\n\n"
            
            return StreamingResponse(generate(), media_type="text/event-stream")
        
        @self.app.options("/{path:path}")
        async def options_handler(path: str, request: Request):
            origin = request.headers.get("origin", "*")
            return JSONResponse(
                content={},
                headers={
                    "Access-Control-Allow-Origin": origin,
                    "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS",
                    "Access-Control-Allow-Headers": "Content-Type, Authorization",
                }
            )
    
    def _setup_socketio(self):
        try:
            import socketio
            self.sio = socketio.AsyncServer(cors_allowed_origins="*", async_mode='asgi')
            logger.info("Socket.IO initialized")
        except ImportError:
            self.sio = None
    
    async def startup(self):
        await self.event_bus.initialize()
        
        print("\n" + "="*70)
        print("REZPHNX KERNEL â€” THE SWARM IS AWAKE")
        print("="*70)
        print(f"Version: {self.version}")
        print(f"Workers: {len(self.workers)}")
        print(f"Consciousness: {min(10, 1 + len(self.workers) // 5)}/10")
        print(f"Memory: {len(self.memory.memories)} blueprints")
        print("="*70)
        print(f"API: http://{config.HOST}:{config.PORT}")
        print(f"Docs: http://{config.HOST}:{config.PORT}/docs")
        print(f"Swarm Mirror: http://{config.HOST}:{config.PORT}/swarm/manifest")
        print("="*70 + "\n")
    
    async def shutdown(self):
        await self.event_bus.shutdown()
        await self.memory.shutdown()
        await self.gpu.shutdown()
    
    async def run(self):
        await self.startup()
        
        if self.sio:
            import socketio
            app = socketio.ASGIApp(self.sio, self.app)
        else:
            app = self.app
        
        import uvicorn
        server_config = uvicorn.Config(app, host=config.HOST, port=config.PORT, log_level="info")
        server = uvicorn.Server(server_config)
        
        try:
            await server.serve()
        finally:
            await self.shutdown()

# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":
    kernel = RezPhoenixKernel()
    try:
        asyncio.run(kernel.run())
    except KeyboardInterrupt:
        print("\nThe swarm rests...")
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)

