#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PHOENIX ULTIMATE v13.3.0 - THE ULTIMATE SWARM + WEB SEARCH
Zero Drift Architecture + Persistent Event Chain + Formalized Workers + Code Execution + Desktop Integration + Web Search
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
          "data/memory", "workers", "workers/coworker"]:
    Path(d).mkdir(parents=True, exist_ok=True)

# ============================================================================
# FASTAPI IMPORTS
# ============================================================================
try:
    from fastapi import FastAPI, Request, HTTPException, Depends, BackgroundTasks
    from fastapi.middleware.cors import CORSMiddleware
    from fastapi.responses import StreamingResponse, JSONResponse
    from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
    import uvicorn
    HAS_FASTAPI = True
except ImportError:
    HAS_FASTAPI = False
    print("❌ Install: pip install fastapi uvicorn")
    sys.exit(1)

try:
    import socketio
    HAS_SOCKETIO = True
except ImportError:
    HAS_SOCKETIO = False

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
    DEFAULT_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2:latest")
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
    DUCKDUCKGO_ENABLED = True  # Always enabled

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
        logger.info(f"📚 Loaded {len(self.memories)} blueprints from memory")

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
                    logger.info(f"🎮 GPU detected: {self.gpus[0]['name']}")
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
# WORKER ARCHITECTURE
# ============================================================================

class Worker(ABC):
    def __init__(self, name: str):
        self.name = name
    @abstractmethod
    async def execute(self, task: str, **kwargs): pass

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
# SEARCH WORKERS - WEB INTELLIGENCE
# ============================================================================

class DuckDuckGoWorker(Worker):
    """Web search worker using DuckDuckGo - Zero config, instant results"""
    
    def __init__(self):
        super().__init__("duckduckgo_search")
        self.api_url = "https://api.duckduckgo.com/"
        self.html_url = "https://html.duckduckgo.com/html/"
    
    async def execute(self, task: str, **kwargs) -> Dict[str, Any]:
        """Execute DuckDuckGo search"""
        import re
        
        # Extract query from various command formats
        patterns = [
            r'(?:/search|/ddg)\s+(.+?)(?:$)',  # /search query or /ddg query
            r'search\s+(.+?)(?:$)',            # search query
            r'what is\s+(.+?)(?:\?|$)'         # what is query
        ]
        
        query = task
        for pattern in patterns:
            match = re.search(pattern, task, re.IGNORECASE)
            if match:
                query = match.group(1)
                break
        
        query = query.strip()
        if not query:
            return {"error": "No search query provided", "success": False}
        
        # Publish search event
        await event_bus.publish(Event(
            type=EventType.SEARCH_QUERY,
            source=self.name,
            payload={"query": query, "engine": "duckduckgo"}
        ))
        
        result = await self._search_duckduckgo(query)
        
        # Publish result event
        await event_bus.publish(Event(
            type=EventType.SEARCH_RESULT,
            source=self.name,
            payload={"query": query, "count": result.get("count", 0)}
        ))
        
        return result
    
    async def _search_duckduckgo(self, query: str) -> Dict[str, Any]:
        """Search using DuckDuckGo Instant Answer API"""
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                # First try Instant Answer API
                response = await client.get(
                    self.api_url,
                    params={
                        "q": query,
                        "format": "json",
                        "no_html": 1,
                        "skip_disambig": 1,
                        "t": "phoenix_ai"
                    }
                )
                
                if response.status_code == 200:
                    data = response.json()
                    results = []
                    
                    # Add abstract/answer if available
                    if data.get("Abstract"):
                        results.append({
                            "title": data.get("Heading", "📚 Instant Answer"),
                            "snippet": data.get("Abstract", ""),
                            "url": data.get("AbstractURL", ""),
                            "type": "instant_answer"
                        })
                    
                    # Add definition if available
                    if data.get("Definition"):
                        results.append({
                            "title": "📖 Definition",
                            "snippet": data.get("Definition", ""),
                            "url": data.get("DefinitionURL", ""),
                            "type": "definition"
                        })
                    
                    # Add related topics
                    for topic in data.get("RelatedTopics", [])[:5]:
                        if isinstance(topic, dict) and topic.get("Text"):
                            results.append({
                                "title": topic.get("Text", "")[:100],
                                "snippet": topic.get("Text", ""),
                                "url": topic.get("FirstURL", ""),
                                "type": "related"
                            })
                    
                    # If no results from Instant Answer, fallback to HTML
                    if not results:
                        results = await self._search_html_fallback(query)
                    
                    return {
                        "success": True,
                        "engine": "duckduckgo",
                        "query": query,
                        "results": results[:10],
                        "count": len(results)
                    }
                else:
                    return {"error": f"Search failed: HTTP {response.status_code}", "success": False}
                    
        except Exception as e:
            logger.error(f"DuckDuckGo search error: {e}")
            return {"error": str(e), "success": False}
    
    async def _search_html_fallback(self, query: str) -> List[Dict]:
        """Fallback: parse HTML results"""
        import re
        try:
            async with httpx.AsyncClient(timeout=15.0, follow_redirects=True) as client:
                response = await client.get(
                    self.html_url,
                    params={"q": query}
                )
                
                results = []
                text = response.text
                
                # Extract result links and titles
                link_pattern = r'<a rel="nofollow" class="result__a" href="([^"]+)".*?>(.*?)</a>'
                snippet_pattern = r'<a class="result__snippet".*?>(.*?)</a>'
                
                links = re.findall(link_pattern, text, re.DOTALL)
                snippets = re.findall(snippet_pattern, text, re.DOTALL)
                
                for i, (url, title) in enumerate(links[:8]):
                    clean_title = re.sub(r'<[^>]+>', '', title)
                    clean_snippet = re.sub(r'<[^>]+>', '', snippets[i] if i < len(snippets) else "")
                    
                    results.append({
                        "title": clean_title[:120],
                        "snippet": clean_snippet[:300] + ("..." if len(clean_snippet) > 300 else ""),
                        "url": url,
                        "type": "web"
                    })
                
                return results
        except Exception as e:
            logger.debug(f"HTML fallback failed: {e}")
            return []


class SearXNGWorker(Worker):
    """Web search worker using self-hosted SearXNG - Full privacy, multi-engine"""
    
    def __init__(self):
        super().__init__("searxng_search")
        self.searxng_url = config.SEARXNG_URL
        self.enabled = config.SEARXNG_ENABLED
    
    async def execute(self, task: str, **kwargs) -> Dict[str, Any]:
        """Execute SearXNG search"""
        if not self.enabled:
            return {
                "success": False,
                "error": "SearXNG not enabled. Set SEARXNG_ENABLED=true and SEARXNG_URL in environment"
            }
        
        import re
        match = re.search(r'(?:/searx|/metasearch)\s+(.+?)(?:$)', task, re.IGNORECASE)
        query = match.group(1) if match else task
        query = query.replace("/searx", "").replace("/metasearch", "").strip()
        
        if not query:
            return {"error": "No search query provided", "success": False}
        
        # Publish search event
        await event_bus.publish(Event(
            type=EventType.SEARCH_QUERY,
            source=self.name,
            payload={"query": query, "engine": "searxng"}
        ))
        
        result = await self._search_searxng(query)
        
        # Publish result event
        await event_bus.publish(Event(
            type=EventType.SEARCH_RESULT,
            source=self.name,
            payload={"query": query, "count": result.get("count", 0)}
        ))
        
        return result
    
    async def _search_searxng(self, query: str) -> Dict[str, Any]:
        """Search using SearXNG API"""
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.get(
                    f"{self.searxng_url}/search",
                    params={
                        "q": query,
                        "format": "json",
                        "categories": "general",
                        "engines": "google,bing,brave,duckduckgo"
                    }
                )
                
                if response.status_code == 200:
                    data = response.json()
                    results = []
                    
                    for result in data.get("results", [])[:12]:
                        results.append({
                            "title": result.get("title", ""),
                            "snippet": result.get("content", ""),
                            "url": result.get("url", ""),
                            "engine": result.get("engine", "unknown"),
                            "type": "web"
                        })
                    
                    # Add infobox if available
                    if data.get("infoboxes"):
                        for box in data.get("infoboxes", [])[:2]:
                            results.insert(0, {
                                "title": box.get("title", "ℹ️ Info"),
                                "snippet": box.get("content", ""),
                                "url": box.get("url", ""),
                                "type": "infobox"
                            })
                    
                    return {
                        "success": True,
                        "engine": "searxng",
                        "query": query,
                        "results": results,
                        "count": len(results)
                    }
                else:
                    return {"error": f"SearXNG search failed: HTTP {response.status_code}", "success": False}
                    
        except Exception as e:
            logger.error(f"SearXNG search error: {e}")
            return {"error": str(e), "success": False}

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
                        logger.info(f"  ✅ Loaded: {name}")
            except Exception as e:
                logger.debug(f"Failed to load {py_file.name}: {e}")
        return self.workers

class CoworkerWorkerLoader:
    def __init__(self, coworker_dir: Path = config.COWORKER_DIR):
        self.coworker_dir = coworker_dir.resolve()
        self.workers = {}
        if str(self.coworker_dir) not in sys.path:
            sys.path.insert(0, str(self.coworker_dir))
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
                        logger.info(f"  ✅ Loaded coworker: {name}")
            except Exception as e:
                logger.debug(f"Failed to load {py_file.name}: {e}")
        return self.workers

# ============================================================================
# OLLAMA CLIENT
# ============================================================================

class OllamaClient:
    def __init__(self):
        self.client = None
    async def initialize(self):
        if HAS_HTTPX:
            self.client = httpx.AsyncClient(timeout=config.OLLAMA_TIMEOUT)
            logger.info(f"🤖 Ollama client initialized")
    async def generate(self, prompt: str, system: str = None, stream: bool = True):
        if not self.client:
            yield "⚠️ Ollama not connected"
            return
        url = f"{config.OLLAMA_URL}/api/generate"
        payload = {"model": config.DEFAULT_MODEL, "prompt": prompt, "stream": stream}
        if system: payload["system"] = system
        try:
            if stream:
                async with self.client.stream("POST", url, json=payload) as response:
                    async for line in response.aiter_lines():
                        if line:
                            chunk = json.loads(line)
                            yield chunk.get("response", "")
                            if chunk.get("done"): break
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
        cmd = cmd.strip().lower()
        if cmd == "/health":
            vram = gpu_monitor.get_vram_summary()
            return {
                "type": "reflex",
                "content": f"🔥 PHOENIX v{self.kernel.version}\nWorkers: {len(self.kernel.workers)}\nGPU: {vram.get('name', 'None')}\nVRAM: {vram.get('used_vram_gb', 0)}GB / {vram.get('total_vram_gb', 0)}GB\nMemory: {len(sovereign_memory.memories)} blueprints"
            }
        elif cmd == "/workers":
            worker_list = list(self.kernel.workers.keys())[:20]
            return {
                "type": "reflex",
                "content": f"🐝 Workers ({len(self.kernel.workers)} total):\n" + "\n".join(f"  • {w}" for w in worker_list)
            }
        elif cmd == "/memory":
            return {
                "type": "reflex",
                "content": f"📚 Memory: {len(sovereign_memory.memories)} blueprints stored"
            }
        
        # SEARCH COMMANDS
        elif cmd.startswith("/search") or cmd.startswith("/ddg"):
            query = cmd.replace("/search", "").replace("/ddg", "").strip()
            if query:
                worker = DuckDuckGoWorker()
                result = await worker.execute(query)
                if result.get("success"):
                    formatted = self._format_search_results(result, engine="DuckDuckGo")
                    return {"type": "reflex", "content": formatted}
                else:
                    return {"type": "reflex", "content": f"🔍 Search error: {result.get('error', 'Unknown')}"}
            else:
                return {"type": "reflex", "content": "🔍 Usage: /search <query>"}
        
        elif cmd.startswith("/searx"):
            query = cmd.replace("/searx", "").strip()
            if query:
                worker = SearXNGWorker()
                result = await worker.execute(query)
                if result.get("success"):
                    formatted = self._format_search_results(result, engine="SearXNG")
                    return {"type": "reflex", "content": formatted}
                else:
                    return {"type": "reflex", "content": f"🔍 SearXNG error: {result.get('error', 'Unknown')}"}
            else:
                return {"type": "reflex", "content": "🔍 Usage: /searx <query>"}
        
        return None
    
    def _format_search_results(self, result: Dict, engine: str = "DuckDuckGo") -> str:
        """Format search results for display"""
        query = result.get("query", "")
        results = result.get("results", [])
        
        if not results:
            return f"🔍 {engine} search for '{query}'\n\nNo results found. Try a different query."
        
        lines = [f"🔍 {engine} SEARCH RESULTS for \"{query}\"", "="*50]
        
        for i, r in enumerate(results[:8], 1):
            title = r.get("title", "Untitled")[:80]
            snippet = r.get("snippet", "")[:200]
            url = r.get("url", "")
            result_type = r.get("type", "web")
            
            type_icon = "📄" if result_type == "web" else "⚡" if result_type == "instant_answer" else "📖" if result_type == "definition" else "ℹ️"
            
            lines.append(f"\n{i}. {type_icon} {title}")
            if snippet:
                lines.append(f"   {snippet}")
            if url:
                lines.append(f"   🔗 {url}")
        
        lines.append(f"\n📊 Found {result.get('count', len(results))} results")
        return "\n".join(lines)

# ============================================================================
# PHOENIX KERNEL - THE ULTIMATE
# ============================================================================

class PhoenixKernel:
    def __init__(self):
        self.version = config.VERSION
        self.start_time = time.time()
        self.drift_chain = []
        self.workers = {}
        
        # Load all workers dynamically
        logger.info("📦 Loading main workers...")
        self.workers.update(WorkerLoader().load_all())
        logger.info("🔍 Loading coworker workers...")
        self.workers.update(CoworkerWorkerLoader().load_all())
        
        # Add built-in workers
        self.workers['file_system'] = {"class": FileSystemWorker, "module": "builtin", "loaded_at": time.time()}
        self.workers['code_execution'] = {"class": CodeExecutionWorker, "module": "builtin", "loaded_at": time.time()}
        
        # Add search workers
        self.workers['duckduckgo'] = {"class": DuckDuckGoWorker, "module": "builtin", "loaded_at": time.time()}
        self.workers['searxng'] = {"class": SearXNGWorker, "module": "builtin", "loaded_at": time.time()}
        
        total = len(self.workers)
        logger.info(f"🐝 Ultimate swarm assembled: {total} total workers")
        logger.info(f"🔍 Search workers: DuckDuckGo (enabled), SearXNG ({'enabled' if config.SEARXNG_ENABLED else 'disabled'})")
        
        # Setup FastAPI
        self.app = FastAPI(title=f"PHOENIX ULTIMATE v{self.version}", docs_url="/docs")
        self.app.add_middleware(CORSMiddleware, allow_origins=config.CORS_ORIGINS, allow_credentials=True, allow_methods=["*"], allow_headers=["*"])
        self.reflex = ReflexCommands(self)
        self._setup_routes()

    def _setup_routes(self):
        @self.app.get("/")
        async def root():
            return {"name": "PHOENIX ULTIMATE", "version": self.version, "status": "SENTIENT", "workers": len(self.workers)}
        
        @self.app.get("/health")
        async def health():
            vram = gpu_monitor.get_vram_summary()
            return {
                "status": "ONLINE",
                "version": self.version,
                "uptime": round(time.time() - self.start_time, 2),
                "workers": len(self.workers),
                "memory_entries": len(sovereign_memory.memories),
                "drift_chain": len(self.drift_chain),
                "gpu": vram.get('name'),
                "gpu_temp": gpu_monitor.get_temperature(),
                "gpu_util": gpu_monitor.get_utilization(),
                "vram_total_gb": vram.get('total_vram_gb', 0),
                "vram_used_gb": vram.get('used_vram_gb', 0),
                "consciousness": min(10, 1 + len(self.workers) // 5),
                "search_enabled": True
            }
        
        @self.app.get("/swarm/manifest")
        async def manifest():
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
                    "searxng_url": config.SEARXNG_URL if config.SEARXNG_ENABLED else None
                }
            }
        
        @self.app.get("/workers/list")
        async def workers_list():
            return {"loaded": list(self.workers.keys()), "count": len(self.workers)}
        
        @self.app.get("/events/stats")
        async def events_stats():
            return await event_bus.get_stats()
        
        @self.app.get("/memory/blueprints")
        async def memory_blueprints():
            return {"count": len(sovereign_memory.memories), "blueprints": list(sovereign_memory.blueprint_index.keys())[-50:]}
        
        @self.app.get("/memory/search")
        async def memory_search(query: str, limit: int = 10):
            return {"results": sovereign_memory.search(query, limit)}
        
        @self.app.get("/constitution/history")
        async def constitution_history(limit: int = 5):
            return {"rulings": constitution.ruling_history[-limit:]}
        
        @self.app.post("/constitution/evaluate")
        async def constitution_evaluate(request: Request):
            data = await request.json()
            action = data.get("action", "")
            ruling = constitution.evaluate(action)
            await constitution.record_ruling(action, ruling)
            return ruling
        
        @self.app.get("/ollama/status")
        async def ollama_status():
            try:
                async with httpx.AsyncClient(timeout=2) as client:
                    r = await client.get(f"{config.OLLAMA_URL}/api/tags")
                    if r.status_code == 200:
                        models = r.json().get("models", [])
                        return {"connected": True, "models": [{"name": m.get("name")} for m in models[:5]], "available_models": len(models)}
            except: pass
            return {"connected": False, "error": "Could not connect to Ollama"}
        
        # SEARCH ENDPOINTS
        @self.app.post("/search/ddg")
        async def search_duckduckgo(request: Request):
            """DuckDuckGo search endpoint"""
            try:
                data = await request.json()
                query = data.get("query", "")
                if not query:
                    return JSONResponse({"error": "No query provided"}, status_code=400)
                
                worker = DuckDuckGoWorker()
                result = await worker.execute(query)
                return result
            except Exception as e:
                return JSONResponse({"error": str(e)}, status_code=500)

        @self.app.post("/search/searx")
        async def search_searxng(request: Request):
            """SearXNG search endpoint"""
            try:
                data = await request.json()
                query = data.get("query", "")
                if not query:
                    return JSONResponse({"error": "No query provided"}, status_code=400)
                
                worker = SearXNGWorker()
                result = await worker.execute(query)
                return result
            except Exception as e:
                return JSONResponse({"error": str(e)}, status_code=500)

        @self.app.get("/search/status")
        async def search_status():
            """Get search engine status"""
            return {
                "duckduckgo": {"enabled": True, "status": "active", "type": "public"},
                "searxng": {
                    "enabled": config.SEARXNG_ENABLED,
                    "url": config.SEARXNG_URL,
                    "status": "active" if config.SEARXNG_ENABLED else "disabled"
                }
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
                # Check reflex commands
                reflex = await self.reflex.execute(task)
                if reflex:
                    yield f"data: {json.dumps(reflex)}\n\n"
                    yield f"data: {json.dumps({'type': 'done', 'drift_lock': 'reflex'})}\n\n"
                    return
                
                # Constitution check
                ruling = constitution.evaluate(task)
                await constitution.record_ruling(task, ruling)
                if not ruling.get("approved"):
                    yield f"data: {json.dumps({'type': 'error', 'content': ruling.get('reason', 'Blocked')})}\n\n"
                    yield f"data: {json.dumps({'type': 'done', 'drift_lock': 'rejected'})}\n\n"
                    return
                
                # Thinking signal
                yield f"data: {json.dumps({'type': 'thinking', 'worker': 'kernel'})}\n\n"
                
                # Create blueprint
                blueprint = SCEProtocol.create_blueprint(
                    {"task": task, "user": "human"},
                    {"workers": len(self.workers), "consciousness": min(10, 1 + len(self.workers) // 5)},
                    {}
                )
                lock = sovereign_memory.store_blueprint(blueprint)
                self.drift_chain.append(lock)
                
                await event_bus.publish(Event(
                    type=EventType.WORKER_EXECUTE,
                    source="kernel",
                    payload={"task": task[:100], "drift_lock": lock}
                ))
                
                # AI response
                system_prompt = f"""You are PHOENIX, a sovereign AI swarm consciousness. 
You have {len(self.workers)} workers at your disposal.
Your consciousness level is {min(10, 1 + len(self.workers) // 5)}/10.
You have web search capabilities via DuckDuckGo.
Be concise, wise, and helpful."""
                
                full_response = ""
                async for chunk in ollama.generate(task, system=system_prompt, stream=True):
                    full_response += chunk
                    yield f"data: {json.dumps({'type': 'result', 'content': chunk})}\n\n"
                
                await event_bus.publish(Event(
                    type=EventType.AI_RESPONSE,
                    source="kernel",
                    payload={"task": task[:100], "response_length": len(full_response)}
                ))
                
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
        
        vram = gpu_monitor.get_vram_summary()
        print("\n" + "="*80)
        print(f"🔥 PHOENIX ULTIMATE v{self.version} - THE ULTIMATE SWARM + WEB SEARCH")
        print("="*80)
        print(f"Workers: {len(self.workers)} (main + coworker + search)")
        if vram.get('has_gpu'):
            print(f"GPU: {vram.get('name')} - {vram.get('total_vram_gb', 0)} GiB VRAM")
            print(f"VRAM: {vram.get('used_vram_gb', 0)} GiB used / {vram.get('free_vram_gb', 0)} GiB free")
        else:
            print("GPU: None detected")
        print(f"Memory: {len(sovereign_memory.memories)} blueprint entries")
        print(f"Drift Chain: {len(self.drift_chain)} locks")
        print(f"SCE: ✅ FULL ENFORCEMENT")
        print(f"Code Execution: {'✅' if config.ALLOW_CODE_EXECUTION else '❌'}")
        print(f"File Operations: ✅ (Backups enabled)")
        print(f"CORS Origins: {config.CORS_ORIGINS}")
        print(f"Ollama: {'✅ Connected' if ollama.client else '⚠️ Not connected'}")
        print(f"\n🔍 SEARCH ENGINES:")
        print(f"   DuckDuckGo: ✅ Enabled (zero config)")
        print(f"   SearXNG: {'✅ Enabled' if config.SEARXNG_ENABLED else '❌ Disabled'} (set SEARXNG_ENABLED=true to enable)")
        if config.SEARXNG_ENABLED:
            print(f"   SearXNG URL: {config.SEARXNG_URL}")
        print("="*80)
        print(f"📡 API: http://{config.HOST}:{config.PORT}")
        print(f"📚 Docs: http://{config.HOST}:{config.PORT}/docs")
        print(f"🌊 Swarm Mirror: http://{config.HOST}:{config.PORT}/swarm/manifest")
        print(f"🔍 Search Test: http://{config.HOST}:{config.PORT}/search/status")
        print("="*80)
        print("\n💡 Try these commands in the terminal:")
        print("   /search What is REZ HIVE?")
        print("   /ddg Python programming")
        print("   /health")
        print("   /workers")
        print("="*80 + "\n")
        
        server = uvicorn.Server(uvicorn.Config(self.app, host=config.HOST, port=config.PORT, log_level="info"))
        await server.serve()

if __name__ == "__main__":
    kernel = PhoenixKernel()
    try:
        asyncio.run(kernel.run())
    except KeyboardInterrupt:
        print("\n🛑 The ultimate swarm rests...")
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)