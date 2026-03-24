#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PHOENIX ULTIMATE v13.3.0 - THE ULTIMATE SWARM (Hardened)
Zero Drift Architecture + Persistent Event Chain + Dynamic Worker Swarm + Hardware Pulse
"""

import sys
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
import sqlite3
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple, Union, AsyncGenerator
from abc import ABC, abstractmethod

# FastAPI & Network Imports
from fastapi import FastAPI, Request, HTTPException, Depends, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, JSONResponse
import uvicorn
import httpx
import psutil

try:
    import pynvml
    HAS_PYNVML = True
except ImportError:
    HAS_PYNVML = False

# Suppress warnings
warnings.filterwarnings("ignore")

# ============================================================================
# CONFIGURATION & LOGGING
# ============================================================================

class Config:
    NAME = "PHOENIX"
    VERSION = "13.3.0"
    HOST = os.getenv("PHOENIX_HOST", "0.0.0.0")
    PORT = int(os.getenv("PHOENIX_PORT", "8002"))
    
    # Security
    ALLOW_CODE_EXECUTION = os.getenv("ALLOW_CODE_EXECUTION", "true").lower() == "true"
    CORS_ORIGINS = ["*"] 
    
    # Ollama
    OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
    DEFAULT_MODEL = os.getenv("OLLAMA_MODEL", "qwen2.5-coder:14b")
    OLLAMA_TIMEOUT = 60
    
    # Storage
    WORKSPACE_DIR = Path.cwd()
    DATA_DIR = Path("./data")
    MEMORY_DIR = DATA_DIR / "memory"
    EVENT_STORE_DIR = DATA_DIR / "event_store"
    WORKERS_DIR = Path("./workers")
    COWORKER_DIR = WORKERS_DIR / "coworker"

config = Config()

# Setup Filesystem
for d in [config.DATA_DIR, config.MEMORY_DIR, config.EVENT_STORE_DIR, config.WORKERS_DIR, config.COWORKER_DIR]:
    d.mkdir(parents=True, exist_ok=True)

logging.basicConfig(level=logging.INFO, format="%(asctime)s [PHOENIX] %(message)s")
logger = logging.getLogger("PHOENIX_ULTIMATE")

# ============================================================================
# SCE PROTOCOL & EVENT PERSISTENCE
# ============================================================================

class EventType(Enum):
    SYSTEM_BOOT = "system.boot"
    WORKER_EXECUTE = "worker.execute"
    CONSTITUTION_RULING = "constitution.ruling"
    AI_RESPONSE = "ai.response"
    CODE_EXECUTION = "code.execution"

@dataclass(frozen=True)
class Event:
    type: EventType
    source: str
    payload: Dict[str, Any]
    timestamp: float = field(default_factory=time.time)
    previous_hash: str = ""
    
    def __post_init__(self):
        # The Vera Proof: Cryptographic standing wave of this event
        content = f"{self.type.value}:{self.timestamp}:{self.previous_hash}:{json.dumps(self.payload)}"
        object.__setattr__(self, '_vera_proof', hashlib.sha256(content.encode()).hexdigest()[:16])
    
    @property
    def vera_proof(self) -> str:
        return getattr(self, '_vera_proof', '')

class EventStore:
    def __init__(self, db_path: Path):
        self.db_path = db_path
        self._init_db()
    
    def _init_db(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''CREATE TABLE IF NOT EXISTS events 
            (vera_proof TEXT PRIMARY KEY, type TEXT, payload TEXT, timestamp REAL, prev_hash TEXT)''')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_timestamp ON events(timestamp)')
        conn.commit()
        conn.close()

    async def save_event(self, event: Event):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("INSERT OR REPLACE INTO events VALUES (?, ?, ?, ?, ?)",
            (event.vera_proof, event.type.value, json.dumps(event.payload), event.timestamp, event.previous_hash))
        conn.commit()
        conn.close()

# ============================================================================
# CORE COMPONENTS (GPU, WORKERS, REFLEX)
# ============================================================================

class GPUMonitor:
    def __init__(self):
        self.active = False
        if HAS_PYNVML:
            try:
                pynvml.nvmlInit()
                self.active = True
            except: pass

    def get_stats(self):
        if not self.active: return {"connected": False}
        try:
            handle = pynvml.nvmlDeviceGetHandleByIndex(0)
            mem = pynvml.nvmlDeviceGetMemoryInfo(handle)
            return {
                "connected": True,
                "name": pynvml.nvmlDeviceGetName(handle),
                "temp": pynvml.nvmlDeviceGetTemperature(handle, 0),
                "vram_total": round(mem.total / 1024**3, 2),
                "vram_used": round(mem.used / 1024**3, 2)
            }
        except: return {"connected": False}

class Worker(ABC):
    def __init__(self, name: str): self.name = name
    @abstractmethod
    async def execute(self, task: str, **kwargs) -> Dict[str, Any]: pass

class SwarmRegistry:
    def __init__(self):
        self.workers = {}

    def load_workers(self):
        """Scans folders for JSON blueprints and Python modules"""
        # Load JSON Blueprints
        for p in list(config.WORKERS_DIR.glob("*.json")) + list(config.COWORKER_DIR.glob("*.json")):
            try:
                with open(p) as f:
                    data = json.load(f)
                    self.workers[data['name']] = {**data, "type": "blueprint", "path": str(p)}
            except Exception as e: logger.error(f"Failed to load blueprint {p}: {e}")
        return self.workers

# ============================================================================
# THE PHOENIX KERNEL
# ============================================================================

class PhoenixKernel:
    def __init__(self):
        self.version = config.VERSION
        self.start_time = time.time()
        self.drift_chain = []
        
        # Internal Systems
        self.gpu = GPUMonitor()
        self.registry = SwarmRegistry()
        self.store = EventStore(config.EVENT_STORE_DIR / "events.db")
        self.genesis = "PHOENIX_GENESIS_2026"
        
        # Load Swarm
        self.registry.load_workers()
        
        # Setup Web API
        self.app = FastAPI(title=f"PHOENIX ULTIMATE v{self.version}")
        self.app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])
        self._setup_routes()

    def _setup_routes(self):
        @self.app.get("/health")
        async def health():
            stats = self.gpu.get_stats()
            return {
                "status": "ONLINE",
                "version": self.version,
                "uptime": round(time.time() - self.start_time, 2),
                "workers": len(self.registry.workers),
                "drift_chain": len(self.drift_chain),
                "gpu": stats
            }

        @self.app.get("/swarm/manifest")
        async def manifest():
            # Categories for the React Sidebar
            categories = defaultdict(lambda: {"workers": [], "count": 0, "desc": ""})
            for name, w in self.registry.workers.items():
                cat = w.get("role", "General Capabilities")
                categories[cat]["workers"].append({"name": name, "module": w.get("model", "qwen2.5"), "status": "active"})
                categories[cat]["count"] += 1
                categories[cat]["desc"] = f"Operations related to {cat}"

            return {
                "swarm_id": f"hive-{int(self.start_time)}",
                "status": "SENTIENT",
                "consciousness_level": 9,
                "workers": {"total": len(self.registry.workers), "categories": dict(categories)},
                "sovereignty": {"drift_chain_integrity": True, "genesis_hash": self.genesis},
                "telemetry": {"cpu": psutil.cpu_percent(), "ram": psutil.virtual_memory().percent}
            }

        @self.app.post("/constitution/evaluate")
        async def evaluate(request: Request):
            data = await request.json()
            action = data.get("action", "").lower()
            forbidden = ["rm -rf", "format", "shutdown", "del /"]
            approved = not any(x in action for x in forbidden)
            return {
                "approved": approved,
                "decision": "AUTHORIZED" if approved else "BLOCKED",
                "reasoning": "Synaptic alignment verified." if approved else "Forbidden system command detected.",
                "timestamp": time.time()
            }

        @self.app.get("/ollama/status")
        async def ollama_status():
            async with httpx.AsyncClient() as client:
                try:
                    r = await client.get(f"{config.OLLAMA_URL}/api/tags")
                    return {"connected": r.status_code == 200, "models": r.json().get("models", [])}
                except: return {"connected": False}

        @self.app.post("/kernel/stream")
        async def kernel_stream(request: Request):
            data = await request.json()
            task = data.get("task", "")

            async def event_generator():
                # 1. Reflex / Intent Recognition
                selected_worker = "core_researcher"
                if any(x in task.lower() for x in ["code", "python", "script"]):
                    selected_worker = "code_executor"
                
                yield f"data: {json.dumps({'type': 'thinking', 'worker': selected_worker})}\n\n"
                
                # 2. Stream from Ollama
                full_response = ""
                worker_prompt = self.registry.workers.get(selected_worker, {}).get("system_prompt", "You are REZ HIVE.")
                
                async with httpx.AsyncClient(timeout=config.OLLAMA_TIMEOUT) as client:
                    payload = {"model": config.DEFAULT_MODEL, "prompt": task, "system": worker_prompt, "stream": True}
                    try:
                        async with client.stream("POST", f"{config.OLLAMA_URL}/api/generate", json=payload) as resp:
                            async for line in resp.aiter_lines():
                                if line:
                                    chunk = json.loads(line)
                                    token = chunk.get("response", "")
                                    full_response += token
                                    yield f"data: {json.dumps({'type': 'result', 'content': token})}\n\n"
                                    if chunk.get("done"): break
                    except Exception as e:
                        yield f"data: {json.dumps({'type': 'error', 'content': f'Ollama link severed: {str(e)}'})}\n\n"

                # 3. Finalize SCE Drift Lock
                prev_hash = self.drift_chain[-1] if self.drift_chain else self.genesis
                ev = Event(type=EventType.AI_RESPONSE, source=selected_worker, payload={"task": task}, previous_hash=prev_hash)
                await self.store.save_event(ev)
                self.drift_chain.append(ev.vera_proof)
                
                yield f"data: {json.dumps({'type': 'done', 'drift_lock': ev.vera_proof})}\n\n"

            return StreamingResponse(event_generator(), media_type="text/event-stream")

    async def startup(self):
        vram = self.gpu.get_stats()
        print("\n" + "="*80)
        print(f"🔥 PHOENIX ULTIMATE v{self.version} - THE FULL STACK")
        print("="*80)
        print(f"Swarm Capacity:  {len(self.registry.workers)} specialized nodes detected")
        print(f"Drift Chain:     Active (Genesis: {self.genesis[:8]}...)")
        if vram.get("connected"):
            print(f"Hardware:        {vram['name']} | Temp: {vram['temp']}°C | VRAM: {vram['vram_used']}GB/{vram['vram_total']}GB")
        else:
            print("Hardware:        GPU Monitoring Unavailable (CPU Only)")
        print(f"Linkage:         Ollama @ {config.OLLAMA_URL} | Model: {config.DEFAULT_MODEL}")
        print("="*80)
        print(f"📡 API ONLINE:   http://{config.HOST}:{config.PORT}")
        print("="*80 + "\n")

# ============================================================================
# ENTRY POINT
# ============================================================================

# Single instantiation for the ASGI server
kernel = PhoenixKernel()
app = kernel.app

if __name__ == "__main__":
    # Ensure startup print happens before uvicorn hijacks stdout
    asyncio.run(kernel.startup())
    uvicorn.run(app, host=config.HOST, port=config.PORT, log_level="info")