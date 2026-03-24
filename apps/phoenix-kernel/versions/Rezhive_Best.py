#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PHOENIX ULTIMATE v13.1.0 - FULL SCE PROTOCOL
Zero Drift Architecture + Event Blockchain + Constitution + Workers
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
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List, Callable, Awaitable, Tuple
from enum import Enum, auto
from dataclasses import dataclass, field
from collections import defaultdict
from functools import wraps

# Suppress warnings
warnings.filterwarnings("ignore", message=".*duckduckgo_search.*")

# =======================================================================
# THIRD-PARTY IMPORTS
# =======================================================================
try:
    from fastapi import FastAPI, Request, HTTPException, Depends
    from fastapi.middleware.cors import CORSMiddleware
    from fastapi.middleware.trustedhost import TrustedHostMiddleware
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
    from pydantic_settings import BaseSettings, SettingsConfigDict
    HAS_PYDANTIC = True
except ImportError:
    HAS_PYDANTIC = False
    print("⚠️ Install: pip install pydantic pydantic-settings")

try:
    import aiofiles
except ImportError:
    print("⚠️ Install: pip install aiofiles for file operations")

# =======================================================================
# LOGGING
# =======================================================================
from logging.handlers import RotatingFileHandler

os.makedirs('logs', exist_ok=True)
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
# CONFIGURATION
# =======================================================================
class Settings(BaseSettings):
    environment: str = os.getenv("ENV", "development")
    port: int = int(os.getenv("PHOENIX_PORT", "8002"))
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
    bots_dir: Path = Path("bots")
    workers_dir: Path = Path("workers")
    
    # Ollama
    ollama_url: str = os.getenv("OLLAMA_URL", "http://localhost:11434")
    default_model: str = os.getenv("OLLAMA_MODEL", "llama3.2:latest")
    
    # API Keys
    api_keys: Dict[str, str] = {
        "rez-hive-admin-key-2026": "admin",
    }
    
    # Event chain
    chain_maxlen: int = 10000
    
    # CORS
    frontend_urls: list = [
        "http://localhost:3000", "http://127.0.0.1:3000",
        "http://localhost:5173", "http://127.0.0.1:5173",
        "http://localhost:8000", "http://127.0.0.1:8000"
    ]
    
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
    
    def validate(self):
        # Add admin key from env
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
          settings.bots_dir, settings.workers_dir]:
    d.mkdir(parents=True, exist_ok=True)

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
# GPU MONITOR
# =======================================================================
class GPUMonitor:
    def __init__(self):
        self.has_gpu = False
        self.name = "N/A"
        self.temp = 0
        self.utilization = 0
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
                self.utilization = pynvml.nvmlDeviceGetUtilizationRates(self.handle).gpu
            except:
                self.utilization = 0
        except:
            pass

gpu = GPUMonitor()

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
        self._genesis_hash = hashlib.sha256(b"PHOENIX_ULTIMATE_v13.1.0").hexdigest()[:16]
        self._initialized = False

    async def initialize(self):
        if not self._initialized:
            self._initialized = True
            logger.info("✅ Event bus initialized")
            await self.publish(Event(
                type=EventType.SYSTEM_BOOT,
                source="event_bus",
                payload={"version": "13.1.0"}
            ))

    async def publish(self, event: Event):
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
                "event_counts": dict(counts)
            }

event_bus = SovereignEventBus()

# =======================================================================
# AUTHENTICATION
# =======================================================================
class AuthManager:
    def __init__(self):
        self._keys = settings.api_keys
        self._lock = asyncio.Lock()

    async def verify_key(self, api_key: Optional[str]) -> str:
        if not api_key:
            raise HTTPException(status_code=403, detail="API key required")

        async with self._lock:
            role = self._keys.get(api_key)

        if not role:
            raise HTTPException(status_code=403, detail="Invalid API key")
        return role

    def require_role(self, required_role: str):
        async def dep(api_key: Optional[str] = None) -> str:
            role = await self.verify_key(api_key)
            if required_role == "admin" and role != "admin":
                raise HTTPException(status_code=403, detail="Admin access required")
            return role
        return dep

auth_manager = AuthManager()

async def get_api_key(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(HTTPBearer(auto_error=False))
) -> str:
    if credentials:
        return await auth_manager.verify_key(credentials.credentials)
    api_key = request.headers.get("X-Hive-API-Key")
    if api_key:
        return await auth_manager.verify_key(api_key)
    raise HTTPException(status_code=403, detail="API key required")

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
                "timestamp": time.time()
            }
            start = time.time()
            try:
                if asyncio.iscoroutinefunction(func):
                    result = await func(*args, **kwargs)
                else:
                    result = func(*args, **kwargs)
                execution = {
                    "result": str(result)[:200] if result else "None",
                    "success": True,
                    "duration": time.time() - start
                }
                dna = {"narrative": [f"{worker_name} executed {func.__name__}"]}
                blueprint = SCEProtocol.create_blueprint(intent, dna, execution)
                await event_bus.publish(Event(
                    type=EventType.SCE_BLUEPRINT_CREATED,
                    source=worker_name,
                    payload={"blueprint": blueprint}
                ))
                return {
                    "sce_compliant": True,
                    "blueprint": blueprint,
                    "result": result,
                    "drift_lock": blueprint["master_drift_lock"]
                }
            except Exception as e:
                execution = {
                    "error": str(e),
                    "success": False,
                    "duration": time.time() - start
                }
                dna = {"narrative": [f"{worker_name} failed: {str(e)}"]}
                blueprint = SCEProtocol.create_blueprint(intent, dna, execution)
                await event_bus.publish(Event(
                    type=EventType.WORKER_ERROR,
                    source=worker_name,
                    payload={"blueprint": blueprint}
                ))
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
        self._lock = asyncio.Lock()
    
    async def get_worker(self, worker_class, *args, **kwargs):
        key = f"{worker_class.__name__}:{args}:{kwargs}"
        async with self._lock:
            if key not in self._instances:
                self._instances[key] = worker_class(*args, **kwargs)
            return self._instances[key]
    
    def clear(self):
        self._instances.clear()

worker_cache = WorkerCache()

# =======================================================================
# WORKER LOADER
# =======================================================================
class WorkerLoader:
    def __init__(self):
        self.workers = {}
        self.workers_dir = Path("workers")

    def load_all(self):
        if not self.workers_dir.exists():
            logger.warning(f"Workers directory not found: {self.workers_dir}")
            return {}
        
        sys.path.insert(0, str(self.workers_dir))
        
        for py in self.workers_dir.glob("*.py"):
            if py.name.startswith("__"):
                continue
            try:
                spec = importlib.util.spec_from_file_location(py.stem, py)
                mod = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(mod)
                for name, obj in inspect.getmembers(mod, inspect.isclass):
                    if 'Worker' in name:
                        self.workers[name] = {
                            "class": obj,
                            "path": str(py),
                            "loaded": time.time()
                        }
                        logger.info(f"  ✅ Loaded: {name}")
            except Exception as e:
                logger.error(f"  ❌ Failed to load {py.name}: {e}")
        logger.info(f"📊 Total workers: {len(self.workers)}")
        return self.workers

# =======================================================================
# CONSTITUTION
# =======================================================================
class Constitution:
    def __init__(self):
        self.rulings = []
        self.laws = ["SOVEREIGNTY", "TRANSPARENCY", "ACCOUNTABILITY", "SAFETY"]
        self.whitelist = ['/health', '/workers', '/sys', '/ollama']

    def evaluate(self, action: str) -> dict:
        if any(cmd in action for cmd in self.whitelist):
            return {"approved": True, "reason": "Whitelist", "score": 100}
        
        dangerous = ['rm -rf', 'format', 'del', 'shutdown']
        if any(d in action.lower() for d in dangerous):
            return {"approved": False, "reason": "SAFETY violation"}
        
        ruling = {"approved": True, "score": 100, "reason": "SCE applied"}
        self.rulings.append(ruling)
        return ruling

# =======================================================================
# INTENT ROUTER
# =======================================================================
class IntentRouter:
    def __init__(self):
        self.intent_map = {
            'brain': ['explain', 'analyze', 'think', 'what', 'how', 'tell'],
            'code': ['write', 'code', 'script', 'program', 'function'],
            'cortex': ['memory', 'recall', 'remember'],
        }

    def route(self, task: str) -> str:
        task_lower = task.lower()
        for worker, keywords in self.intent_map.items():
            if any(kw in task_lower for kw in keywords):
                return worker
        return 'brain'

# =======================================================================
# SOVEREIGN MEMORY
# =======================================================================
class SovereignMemory:
    def __init__(self):
        self.memories = {}
        self.blueprint_index = {}
        self._load()

    def store_blueprint(self, blueprint: Dict) -> str:
        lock = blueprint.get('master_drift_lock', SCEProtocol.create_drift_lock(blueprint))
        self.memories[lock] = {'value': blueprint, 'timestamp': time.time()}
        self.blueprint_index[lock] = lock
        
        try:
            path = settings.memory_dir / f"sce_{lock}.json"
            with open(path, 'w') as f:
                json.dump(self.memories[lock], f, indent=2)
        except Exception as e:
            logger.error(f"Failed to persist blueprint: {e}")
        return lock

    def verify(self, drift_lock: str) -> dict:
        record = self.memories.get(drift_lock)
        if not record:
            return {'verified': False, 'error': 'Blueprint not found'}
        return SCEProtocol.verify_blueprint(record['value'])

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

# =======================================================================
# REFLEX
# =======================================================================
class Reflex:
    @staticmethod
    async def execute(cmd: str, kernel=None) -> Optional[Dict]:
        cmd = cmd.strip().lower()
        
        if cmd == '/health' and kernel:
            return {"content": json.dumps(await kernel.get_stats(), indent=2), "type": "reflex"}
        
        if cmd == '/sys':
            gpu.update_stats()
            return {
                "content": f"CPU: {psutil.cpu_percent()}%\nRAM: {psutil.virtual_memory().percent}%\nGPU: {gpu.name} {gpu.temp}°C",
                "type": "reflex"
            }
        
        return None

# =======================================================================
# PHOENIX KERNEL
# =======================================================================
class PhoenixKernel:
    def __init__(self):
        self.version = "13.1.0"
        self.start_time = time.time()
        self.drift_chain = []
        self.constitution = Constitution()
        self.router = IntentRouter()
        self.memory = SovereignMemory()
        self.reflex = Reflex()
        
        # Load workers
        self.workers_loader = WorkerLoader()
        self.workers = self.workers_loader.load_all() or {}
        
        # FastAPI App
        self.app = FastAPI(title=f"Phoenix v{self.version}")
        
        # CORS - Allow all for development
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        
        self.setup_routes()
        
        # Socket.IO
        self.sio = None
        if HAS_SOCKETIO:
            self.sio = socketio.AsyncServer(cors_allowed_origins='*', async_mode='asgi')
            self.setup_socketio()
        
        logger.info(f"🚀 Phoenix v{self.version} initialized")

    def setup_routes(self):
        # ===== HEALTH (NO AUTH REQUIRED) =====
        @self.app.get("/health")
        async def health():
            return await self.get_stats()

        @self.app.get("/ollama/status")
        async def ollama_status():
            try:
                async with httpx.AsyncClient(timeout=2.0) as client:
                    r = await client.get(f"{settings.ollama_url}/api/tags")
                    return {"connected": r.status_code == 200, "models": r.json().get("models", [])}
            except:
                return {"connected": False}

        @self.app.get("/workers/list")
        async def workers_list():
            return {"loaded": list(self.workers.keys()), "count": len(self.workers)}

        @self.app.get("/events/stats")
        async def events_stats():
            return await event_bus.get_stats()

        @self.app.get("/sce/status")
        async def sce_status():
            return {
                "version": SCEProtocol.VERSION,
                "blueprints": len(self.memory.memories),
                "drift_chain": self.drift_chain[-10:]
            }

        @self.app.get("/memory/blueprints")
        async def memory_blueprints():
            return {
                "count": len(self.memory.memories),
                "blueprints": list(self.memory.blueprint_index.keys())[-50:]
            }

        @self.app.get("/memory/verify/{drift_lock}")
        async def memory_verify(drift_lock: str):
            return self.memory.verify(drift_lock)

        @self.app.post("/constitution/evaluate")
        async def constitution_evaluate(request: Request):
            data = await request.json()
            action = data.get('action', '')
            return self.constitution.evaluate(action)

        # ===== MAIN STREAMING ENDPOINT =====
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
                # 1. Check reflex
                reflex_result = await self.reflex.execute(task, kernel=self)
                if reflex_result:
                    yield f"data: {json.dumps({'type': 'reflex', 'content': reflex_result['content']})}\n\n"
                    return

                # 2. Constitution check
                ruling = self.constitution.evaluate(task)
                if not ruling.get("approved"):
                    yield f"data: {json.dumps({'type': 'error', 'content': ruling.get('reason', 'Blocked')})}\n\n"
                    return

                # 3. Route
                worker = self.router.route(task)
                yield f"data: {json.dumps({'type': 'thinking', 'worker': worker})}\n\n"

                # 4. Stream from Ollama
                full_response = ""
                async for chunk in self._call_ollama(task):
                    full_response += chunk
                    yield f"data: {json.dumps({'type': 'result', 'content': chunk})}\n\n"

                # 5. Create SCE blueprint
                blueprint = SCEProtocol.create_blueprint(
                    {"task": task, "worker": worker},
                    {"narrative": ["Streaming complete"]},
                    {"response_length": len(full_response), "success": True},
                    self.drift_chain[-1] if self.drift_chain else None
                )
                lock = self.memory.store_blueprint(blueprint)
                self.drift_chain.append(lock)

                yield f"data: {json.dumps({'type': 'done', 'drift_lock': lock})}\n\n"

            return StreamingResponse(generate(), media_type="text/event-stream")

    async def _call_ollama(self, prompt: str):
        url = f"{settings.ollama_url}/api/generate"
        payload = {
            "model": settings.default_model,
            "prompt": prompt,
            "system": "You are Phoenix AI. Be concise and helpful.",
            "stream": True
        }
        try:
            async with httpx.AsyncClient(timeout=None) as client:
                async with client.stream("POST", url, json=payload) as r:
                    async for line in r.aiter_lines():
                        if line:
                            chunk = json.loads(line)
                            yield chunk.get("response", "")
                            if chunk.get("done"):
                                break
        except Exception as e:
            yield f"\n[AI_OFFLINE: {e}]"

    async def get_stats(self):
        gpu.update_stats()
        return {
            "status": "ONLINE",
            "version": self.version,
            "uptime": round(time.time() - self.start_time, 2),
            "workers": len(self.workers),
            "memory_entries": len(self.memory.memories),
            "drift_chain": len(self.drift_chain),
            "gpu": gpu.name if gpu.has_gpu else None,
            "gpu_temp": gpu.temp,
            "consciousness": 5 + len(self.workers),
            "sce_enforcement": "FULL"
        }

    def setup_socketio(self):
        @self.sio.event
        async def connect(sid, environ, auth):
            logger.info(f"🟢 Client: {sid}")
            await self.sio.emit('connection_verified', {'status': 'ok'}, room=sid)

        @self.sio.event
        async def disconnect(sid):
            logger.info(f"🔴 Disconnected: {sid}")

    async def run(self):
        print("\n" + "="*60)
        print(f"🔥 PHOENIX v{self.version} - ZERO DRIFT SCE PROTOCOL")
        print("="*60)
        print(f"Workers: {len(self.workers)}")
        print(f"GPU: {gpu.name if gpu.has_gpu else 'None'}")
        print(f"Memory: {len(self.memory.memories)} entries")
        print(f"SCE: ✅ FULL ENFORCEMENT")
        
        try:
            async with httpx.AsyncClient(timeout=2) as c:
                r = await c.get(f"{settings.ollama_url}/api/tags")
                print(f"Ollama: ✅ {len(r.json().get('models', []))} models")
        except:
            print("Ollama: ⚠️ Offline")
        
        print("="*60 + "\n")
        
        await event_bus.initialize()
        
        if self.sio:
            app = socketio.ASGIApp(self.sio, self.app)
        else:
            app = self.app
        
        config = uvicorn.Config(app, host=settings.host, port=settings.port, log_level="info")
        await uvicorn.Server(config).serve()

if __name__ == "__main__":
    asyncio.run(PhoenixKernel().run())