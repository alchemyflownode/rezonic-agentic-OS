#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PHOENIX ULTIMATE v14.0.0-COMPLETE - AUTO-LOADS ALL 65+ WORKERS
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
import importlib.util
import inspect
from pathlib import Path
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, auto
from abc import ABC, abstractmethod

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
logger = logging.getLogger("PHOENIX_COMPLETE")

# Create necessary directories
for d in ["logs", "data", "data/event_store", "data/backups", "data/sandbox", 
          "data/memory", "workers", "workers/coworker"]:
    Path(d).mkdir(parents=True, exist_ok=True)

# ============================================================================
# FASTAPI IMPORTS
# ============================================================================
try:
    from fastapi import FastAPI, Request
    from fastapi.middleware.cors import CORSMiddleware
    from fastapi.responses import StreamingResponse, JSONResponse
    import uvicorn
    HAS_FASTAPI = True
except ImportError:
    HAS_FASTAPI = False
    print("❌ Install: pip install fastapi uvicorn")
    sys.exit(1)

try:
    import httpx
    HAS_HTTPX = True
except ImportError:
    HAS_HTTPX = False

# ============================================================================
# CONFIGURATION
# ============================================================================

class Config:
    NAME = "PHOENIX"
    VERSION = "14.0.0-COMPLETE"
    HOST = os.getenv("PHOENIX_HOST", "0.0.0.0")
    PORT = int(os.getenv("PHOENIX_PORT", "8002"))
    CORS_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000").split(",")
    OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
    DEFAULT_MODEL = os.getenv("OLLAMA_MODEL", "qwen2.5-coder:7b-instruct-q4_K_M")
    ALLOW_CODE_EXECUTION = os.getenv("ALLOW_CODE_EXECUTION", "true").lower() == "true"
    ENABLE_AUTO_SEARCH = os.getenv("ENABLE_AUTO_SEARCH", "true").lower() == "true"
    REZ_SWARM_ENABLED = os.getenv("REZ_SWARM_ENABLED", "true").lower() == "true"
    WORKSPACE_DIR = Path.cwd()
    MEMORY_DIR = Path("data/memory")
    EVENT_STORE_DIR = Path("data/event_store")

config = Config()

# ============================================================================
# BASE WORKER CLASS (for compatibility)
# ============================================================================

class Worker(ABC):
    def __init__(self, name: str):
        self.name = name
    @abstractmethod
    async def execute(self, task: str, **kwargs): pass

# ============================================================================
# BUILT-IN WORKERS (MINIMAL CORE)
# ============================================================================

class HealthWorker(Worker):
    def __init__(self):
        super().__init__("health")
    async def execute(self, task: str, **kwargs):
        return {"status": "online", "workers": len(kwargs.get("workers", {}))}

class WorkersWorker(Worker):
    def __init__(self):
        super().__init__("workers")
    async def execute(self, task: str, **kwargs):
        return {"workers": list(kwargs.get("workers", {}).keys()), "count": len(kwargs.get("workers", {}))}

class FileSystemWorker(Worker):
    def __init__(self):
        super().__init__("file_system")
        self.workspace = Path.cwd()
    async def execute(self, task: str, **kwargs):
        if "list" in task.lower():
            path = kwargs.get("path", str(self.workspace))
            return await self._list_directory(path)
        return {"error": "Unknown operation", "success": False}
    async def _list_directory(self, path: str):
        try:
            p = Path(path).expanduser().resolve()
            if not p.exists():
                return {"error": f"Path not found: {path}", "success": False}
            items = [{"name": item.name, "type": "dir" if item.is_dir() else "file"} 
                     for item in p.iterdir()[:50]]
            return {"success": True, "path": str(p), "items": items, "count": len(items)}
        except Exception as e:
            return {"error": str(e), "success": False}

class SystemMonitorWorker(Worker):
    def __init__(self):
        super().__init__("system_monitor")
    async def execute(self, task: str, **kwargs):
        try:
            import psutil
            return {"success": True, "cpu_percent": psutil.cpu_percent(interval=1), 
                    "memory_percent": psutil.virtual_memory().percent}
        except:
            return {"error": "psutil not installed", "success": False}

class DuckDuckGoWorker(Worker):
    def __init__(self):
        super().__init__("duckduckgo")
    async def execute(self, task: str, **kwargs):
        query = task.replace("/search", "").strip()
        if not query:
            return {"error": "No search query", "success": False}
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.get("https://api.duckduckgo.com/", 
                                          params={"q": query, "format": "json", "no_html": 1})
                if response.status_code == 200:
                    data = response.json()
                    results = []
                    if data.get("Abstract"):
                        results.append({"title": data.get("Heading", "Answer"), 
                                      "snippet": data.get("Abstract", "")})
                    return {"success": True, "query": query, "results": results[:3]}
        except Exception as e:
            return {"error": str(e), "success": False}

class CodeGenWorker(Worker):
    def __init__(self):
        super().__init__("code_gen")
    async def execute(self, task: str, **kwargs):
        intent = task.replace("/code", "").strip()
        if not intent:
            return {"error": "No code intent", "success": False}
        code = f'def solution():\n    """Generated for: {intent}"""\n    return "Implement your solution here"'
        return {"success": True, "code": code, "intent": intent}

class MemoryWorker(Worker):
    def __init__(self):
        super().__init__("memory")
        self.memories = {}
    async def execute(self, task: str, **kwargs):
        return {"success": True, "memory": len(self.memories)}

class RezSwarmWorker(Worker):
    def __init__(self):
        super().__init__("rez_swarm")
        self.optimizations = 0
    async def execute(self, task: str, **kwargs):
        return {"success": True, "active": config.REZ_SWARM_ENABLED, "optimizations": self.optimizations}

# ============================================================================
# WORKER AUTO-LOADER
# ============================================================================

class WorkerAutoLoader:
    """Auto-discovers and loads all workers from workers/ directory"""
    
    def __init__(self):
        self.workers_dir = Path(__file__).parent / "workers"
        self.loaded_workers = {}
    
    def load_all(self) -> Dict[str, Worker]:
        """Load all workers from directory"""
        
        logger.info(f"📦 Scanning for workers in {self.workers_dir}")
        
        if not self.workers_dir.exists():
            logger.warning(f"Workers directory not found: {self.workers_dir}")
            return self._load_builtins()
        
        # First, load built-in core workers
        self.loaded_workers.update(self._load_builtins())
        
        # Then load all Python files in workers/
        for py_file in self.workers_dir.glob("*.py"):
            if py_file.name.startswith("__"):
                continue
            # Skip base classes and utilities
            if py_file.name in ["base_worker.py", "decorators.py", "registry.py", "__init__.py"]:
                continue
                
            try:
                self._load_worker_from_file(py_file)
            except Exception as e:
                logger.debug(f"Failed to load {py_file.name}: {e}")
        
        # Load from coworker subdirectory
        coworker_dir = self.workers_dir / "coworker"
        if coworker_dir.exists():
            logger.info(f"🤝 Loading coworker workers from {coworker_dir}")
            for py_file in coworker_dir.glob("*.py"):
                if py_file.name.startswith("__"):
                    continue
                try:
                    self._load_worker_from_file(py_file, prefix="coworker_")
                except Exception as e:
                    logger.debug(f"Failed to load coworker {py_file.name}: {e}")
        
        logger.info(f"🐝 Total workers loaded: {len(self.loaded_workers)}")
        return self.loaded_workers
    
    def _load_worker_from_file(self, py_file: Path, prefix: str = ""):
        """Load a single worker file"""
        try:
            # Import module dynamically
            spec = importlib.util.spec_from_file_location(
                f"worker_{py_file.stem}", 
                py_file
            )
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            # Find all classes in module
            for name, obj in inspect.getmembers(module, inspect.isclass):
                # Check if it's a Worker subclass or has execute method
                is_worker = False
                
                # Check inheritance
                if hasattr(obj, '__bases__'):
                    for base in obj.__bases__:
                        if base.__name__ == 'Worker' or 'Worker' in base.__name__:
                            is_worker = True
                            break
                
                # Check for execute method (duck typing)
                if not is_worker and hasattr(obj, 'execute') and callable(obj.execute):
                    is_worker = True
                
                if is_worker:
                    # Try to instantiate
                    try:
                        worker_instance = obj()
                        worker_key = f"{prefix}{py_file.stem}_{name.lower()}"
                        self.loaded_workers[worker_key] = worker_instance
                        logger.debug(f"  ✅ Loaded: {name} from {py_file.name}")
                    except Exception as e:
                        logger.debug(f"  ⚠️ Failed to instantiate {name}: {e}")
                        
        except Exception as e:
            logger.debug(f"  ❌ Failed to load {py_file.name}: {e}")
    
    def _load_builtins(self) -> Dict[str, Worker]:
        """Load core built-in workers"""
        builtins = {
            'health': HealthWorker(),
            'workers': WorkersWorker(),
            'file_system': FileSystemWorker(),
            'system_monitor': SystemMonitorWorker(),
            'duckduckgo': DuckDuckGoWorker(),
            'code_gen': CodeGenWorker(),
            'memory': MemoryWorker(),
        }
        
        if config.REZ_SWARM_ENABLED:
            builtins['rez_swarm'] = RezSwarmWorker()
        
        return builtins

# ============================================================================
# PHOENIX KERNEL
# ============================================================================

class PhoenixKernel:
    def __init__(self):
        self.version = config.VERSION
        self.start_time = time.time()
        
        # AUTO-LOAD ALL WORKERS
        logger.info("🚀 Initializing Phoenix Kernel...")
        loader = WorkerAutoLoader()
        self.workers = loader.load_all()
        
        # Setup FastAPI
        self.app = FastAPI(title=f"PHOENIX v{self.version}", docs_url="/docs")
        self.app.add_middleware(CORSMiddleware, allow_origins=config.CORS_ORIGINS, 
                               allow_credentials=True, allow_methods=["*"], allow_headers=["*"])
        
        self._setup_routes()
    
    def _setup_routes(self):
        @self.app.get("/")
        async def root():
            return {"name": "PHOENIX", "version": self.version, "workers": len(self.workers)}
        
        @self.app.get("/health")
        async def health():
            return {
                "status": "ONLINE",
                "version": self.version,
                "workers": len(self.workers),
                "uptime": round(time.time() - self.start_time, 2)
            }
        
        @self.app.get("/workers/list")
        async def workers_list():
            return {
                "workers": list(self.workers.keys()), 
                "count": len(self.workers),
                "categories": self._categorize_workers()
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
                # Simple command routing
                if task.startswith("/"):
                    # Handle commands
                    cmd_parts = task.split()
                    cmd = cmd_parts[0].lower()
                    
                    # Route to appropriate worker
                    if cmd == "/workers":
                        result = {"type": "reflex", "content": f"🐝 Workers ({len(self.workers)}):\n" + "\n".join(list(self.workers.keys())[:20])}
                        yield f"data: {json.dumps(result)}\n\n"
                    elif cmd == "/health":
                        result = {"type": "reflex", "content": f"🔥 PHOENIX v{self.version}\nWorkers: {len(self.workers)}\nUptime: {round(time.time() - self.start_time, 2)}s"}
                        yield f"data: {json.dumps(result)}\n\n"
                    elif cmd == "/list" and "file_system" in self.workers:
                        path = " ".join(cmd_parts[1:]) if len(cmd_parts) > 1 else "."
                        result = await self.workers["file_system"].execute("list", path=path)
                        if result.get("success"):
                            items = "\n".join([f"  📁 {i['name']}" for i in result['items'][:20]])
                            content = f"📁 {result['path']}\n\n{items}\n\n📊 {result['count']} items"
                            yield f"data: {json.dumps({'type': 'reflex', 'content': content})}\n\n"
                    elif cmd == "/search" and "duckduckgo" in self.workers:
                        query = " ".join(cmd_parts[1:]) if len(cmd_parts) > 1 else ""
                        if query:
                            result = await self.workers["duckduckgo"].execute(f"/search {query}")
                            if result.get("success"):
                                content = f"🔍 SEARCH: {query}\n\n" + "\n".join([f"📌 {r.get('title')}" for r in result.get('results', [])])
                                yield f"data: {json.dumps({'type': 'reflex', 'content': content})}\n\n"
                    else:
                        yield f"data: {json.dumps({'type': 'result', 'content': f'Command: {task}'})}\n\n"
                else:
                    yield f"data: {json.dumps({'type': 'result', 'content': f'Task: {task}'})}\n\n"
                
                yield f"data: {json.dumps({'type': 'done'})}\n\n"
            
            return StreamingResponse(generate(), media_type="text/event-stream")
    
    def _categorize_workers(self) -> Dict[str, List[str]]:
        """Categorize workers by type"""
        categories = {
            "core": [],
            "file": [],
            "system": [],
            "search": [],
            "code": [],
            "memory": [],
            "coworker": [],
            "other": []
        }
        
        for name in self.workers.keys():
            name_lower = name.lower()
            if "file" in name_lower or "fs" in name_lower:
                categories["file"].append(name)
            elif "system" in name_lower or "monitor" in name_lower:
                categories["system"].append(name)
            elif "search" in name_lower or "duck" in name_lower:
                categories["search"].append(name)
            elif "code" in name_lower or "gen" in name_lower:
                categories["code"].append(name)
            elif "memory" in name_lower or "recall" in name_lower:
                categories["memory"].append(name)
            elif "coworker" in name_lower:
                categories["coworker"].append(name)
            elif name in ["health", "workers"]:
                categories["core"].append(name)
            else:
                categories["other"].append(name)
        
        return categories
    
    async def run(self):
        print("\n" + "="*80)
        print(f"🔥 PHOENIX v{self.version} - COMPLETE EDITION")
        print("="*80)
        print(f"✅ Workers Loaded: {len(self.workers)} (Auto-discovered from workers/ directory)")
        print(f"📂 Workers Directory: {Path(__file__).parent / 'workers'}")
        print("="*80)
        print(f"📡 API: http://{config.HOST}:{config.PORT}")
        print(f"📚 Docs: http://{config.HOST}:{config.PORT}/docs")
        print("="*80)
        print("\n💡 TEST COMMANDS:")
        print("   GET /workers/list - See ALL workers")
        print("   POST /kernel/stream {\"task\": \"/workers\"}")
        print("   POST /kernel/stream {\"task\": \"/list\"}")
        print("   POST /kernel/stream {\"task\": \"/search AI\"}")
        print("="*80 + "\n")
        
        # Show first 20 workers as sample
        worker_sample = list(self.workers.keys())[:20]
        print(f"📋 Sample workers (first 20 of {len(self.workers)}):")
        for i, w in enumerate(worker_sample, 1):
            print(f"   {i:2d}. {w}")
        if len(self.workers) > 20:
            print(f"   ... and {len(self.workers) - 20} more")
        print("\n" + "="*80 + "\n")
        
        server = uvicorn.Server(uvicorn.Config(self.app, host=config.HOST, port=config.PORT, log_level="info"))
        await server.serve()

if __name__ == "__main__":
    kernel = PhoenixKernel()
    try:
        asyncio.run(kernel.run())
    except KeyboardInterrupt:
        print("\n🛑 Phoenix rests...")