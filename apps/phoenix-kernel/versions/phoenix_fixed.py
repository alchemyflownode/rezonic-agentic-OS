#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PHOENIX v13.3.0 - Agentic Coding Tool with VRAM Detection
"""

import sys
import os
import time
import asyncio
import json
import hashlib
import secrets
import shutil
import subprocess
import tempfile
import re
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime
import logging

# Setup logging
os.makedirs('logs', exist_ok=True)
os.makedirs('data/backups', exist_ok=True)
os.makedirs('data/sandbox', exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/phoenix.log', encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("PHOENIX")

# FastAPI imports
try:
    from fastapi import FastAPI, Request
    from fastapi.middleware.cors import CORSMiddleware
    from fastapi.responses import StreamingResponse, JSONResponse
    import uvicorn
except ImportError:
    print("❌ Install: pip install fastapi uvicorn")
    sys.exit(1)

try:
    import httpx
except ImportError:
    print("❌ Install: pip install httpx")
    sys.exit(1)

try:
    import psutil
except ImportError:
    psutil = None
    logger.warning("⚠️ psutil not installed")

try:
    import pynvml
    HAS_GPU = True
except ImportError:
    HAS_GPU = False
    logger.warning("⚠️ nvidia-ml-py not installed (GPU monitoring disabled)")

# =======================================================================
# CONFIGURATION
# =======================================================================
class Config:
    port = int(os.getenv("PHOENIX_PORT", "8002"))
    host = os.getenv("PHOENIX_HOST", "0.0.0.0")
    workspace = Path(os.getenv("WORKSPACE_DIR", str(Path.cwd())))
    ollama_url = os.getenv("OLLAMA_URL", "http://localhost:11434")
    default_model = os.getenv("OLLAMA_MODEL", "llama3.2:latest")
    allow_code_execution = os.getenv("ALLOW_CODE_EXECUTION", "true").lower() == "true"
    
    # Create workspace
    workspace.mkdir(parents=True, exist_ok=True)

config = Config()

# =======================================================================
# GPU MONITOR (VRAM Detection)
# =======================================================================
class GPUMonitor:
    def __init__(self):
        self.has_gpu = False
        self.gpu_count = 0
        self.gpus = []
        if HAS_GPU:
            self._init_gpu()
    
    def _init_gpu(self):
        try:
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
                logger.info(f"✅ Detected {self.gpu_count} GPU(s)")
                for gpu in self.gpus:
                    logger.info(f"   GPU {gpu['index']}: {gpu['name']} - {gpu['total_vram_gb']:.1f} GiB VRAM")
        except Exception as e:
            logger.warning(f"GPU monitoring disabled: {e}")
    
    def get_vram_summary(self) -> Dict:
        if not self.has_gpu:
            return {"has_gpu": False, "total_vram_gb": 0}
        
        total = 0
        used = 0
        for i in range(self.gpu_count):
            try:
                handle = self.gpus[i]["handle"]
                mem_info = pynvml.nvmlDeviceGetMemoryInfo(handle)
                total += mem_info.total / (1024**3)
                used += mem_info.used / (1024**3)
            except:
                pass
        
        return {
            "has_gpu": True,
            "total_gpus": self.gpu_count,
            "total_vram_gb": round(total, 2),
            "used_vram_gb": round(used, 2),
            "free_vram_gb": round(total - used, 2),
            "utilization_percent": round((used / total * 100) if total > 0 else 0, 2)
        }
    
    def get_gpu_details(self, gpu_id: int = 0) -> Dict:
        if not self.has_gpu or gpu_id >= self.gpu_count:
            return {"error": "GPU not available"}
        
        try:
            handle = self.gpus[gpu_id]["handle"]
            mem_info = pynvml.nvmlDeviceGetMemoryInfo(handle)
            
            try:
                temp = pynvml.nvmlDeviceGetTemperature(handle, pynvml.NVML_TEMPERATURE_GPU)
            except:
                temp = 0
            
            try:
                util = pynvml.nvmlDeviceGetUtilizationRates(handle)
                gpu_util = util.gpu
            except:
                gpu_util = 0
            
            return {
                "index": gpu_id,
                "name": self.gpus[gpu_id]["name"],
                "memory": {
                    "total_gb": round(mem_info.total / (1024**3), 2),
                    "used_gb": round(mem_info.used / (1024**3), 2),
                    "free_gb": round(mem_info.free / (1024**3), 2),
                    "used_percent": round((mem_info.used / mem_info.total) * 100, 2)
                },
                "temperature_celsius": temp,
                "gpu_utilization_percent": gpu_util
            }
        except Exception as e:
            return {"error": str(e)}

gpu_monitor = GPUMonitor()

# =======================================================================
# OLLAMA CLIENT (Model Introspection)
# =======================================================================
class OllamaClient:
    def __init__(self):
        self.client = None
        self.model_cache = {}
    
    async def init(self):
        self.client = httpx.AsyncClient(timeout=60)
        await self.refresh_models()
    
    async def refresh_models(self):
        try:
            resp = await self.client.get(f"{config.ollama_url}/api/tags", timeout=5)
            if resp.status_code == 200:
                models = resp.json().get("models", [])
                self.model_cache = {m["name"]: m for m in models}
                logger.info(f"✅ Found {len(models)} Ollama models")
        except Exception as e:
            logger.error(f"Failed to refresh models: {e}")
    
    async def get_model_details(self, model_name: str) -> Dict:
        try:
            resp = await self.client.post(f"{config.ollama_url}/api/show", json={"name": model_name})
            if resp.status_code == 200:
                details = resp.json()
                
                # Extract context window
                context_window = 2048
                model_info = details.get("model_info", {})
                
                # Try different keys for context window
                for key in ["llama.context_length", "context_length", "num_ctx"]:
                    if key in model_info:
                        context_window = int(model_info[key])
                        break
                
                # Check modelfile
                if "modelfile" in details:
                    match = re.search(r'num_ctx\s+(\d+)', details["modelfile"])
                    if match:
                        context_window = int(match.group(1))
                
                return {
                    "name": model_name,
                    "context_window": context_window,
                    "parameter_size": details.get("parameter_size", "unknown"),
                    "quantization": details.get("quantization_level", "unknown"),
                    "size_gb": round(details.get("size", 0) / (1024**3), 2)
                }
        except Exception as e:
            return {"name": model_name, "error": str(e)}
    
    async def generate(self, prompt: str, system: str = None, context_window: int = None):
        if not self.client:
            await self.init()
        
        payload = {
            "model": config.default_model,
            "prompt": prompt,
            "stream": True
        }
        if system:
            payload["system"] = system
        if context_window:
            payload["options"] = {"num_ctx": context_window}
        
        try:
            async with self.client.stream("POST", f"{config.ollama_url}/api/generate", json=payload) as resp:
                async for line in resp.aiter_lines():
                    if line:
                        chunk = json.loads(line)
                        if 'response' in chunk:
                            yield chunk['response']
                        if chunk.get('done'):
                            break
        except Exception as e:
            yield f"\n[Error: {e}]\n"
    
    async def close(self):
        if self.client:
            await self.client.aclose()

ollama = OllamaClient()

# =======================================================================
# FILE WORKER
# =======================================================================
class FileWorker:
    def __init__(self):
        self.workspace = config.workspace
    
    async def read(self, path: str) -> Dict:
        try:
            safe_path = (self.workspace / path).resolve()
            if not str(safe_path).startswith(str(self.workspace.resolve())):
                return {"success": False, "error": "Path traversal not allowed"}
            
            if not safe_path.exists():
                return {"success": False, "error": "File not found"}
            
            with open(safe_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            return {
                "success": True,
                "path": str(safe_path),
                "content": content,
                "size": len(content),
                "lines": len(content.splitlines())
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def write(self, path: str, content: str) -> Dict:
        try:
            safe_path = (self.workspace / path).resolve()
            if not str(safe_path).startswith(str(self.workspace.resolve())):
                return {"success": False, "error": "Path traversal not allowed"}
            
            # Create backup
            if safe_path.exists():
                backup = Path("data/backups") / f"{safe_path.name}.{int(time.time())}.bak"
                shutil.copy2(safe_path, backup)
            
            safe_path.parent.mkdir(parents=True, exist_ok=True)
            with open(safe_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            return {"success": True, "path": str(safe_path), "bytes": len(content)}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def list_dir(self, path: str = ".") -> Dict:
        try:
            safe_path = (self.workspace / path).resolve()
            if not str(safe_path).startswith(str(self.workspace.resolve())):
                return {"success": False, "error": "Path traversal not allowed"}
            
            items = []
            for item in safe_path.iterdir():
                items.append({
                    "name": item.name,
                    "type": "dir" if item.is_dir() else "file",
                    "size": item.stat().st_size if item.is_file() else 0
                })
            
            return {
                "success": True,
                "path": str(safe_path),
                "items": sorted(items, key=lambda x: (x['type'] != 'dir', x['name'])),
                "count": len(items)
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

file_worker = FileWorker()

# =======================================================================
# CODE WORKER
# =======================================================================
class CodeWorker:
    async def execute(self, code: str) -> Dict:
        if not config.allow_code_execution:
            return {"success": False, "error": "Code execution disabled"}
        
        import io
        import contextlib
        
        stdout = io.StringIO()
        stderr = io.StringIO()
        
        try:
            with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
                exec_globals = {
                    '__builtins__': __builtins__,
                    'print': print,
                    'len': len,
                    'str': str,
                    'int': int,
                    'list': list,
                    'dict': dict,
                }
                exec(code, exec_globals)
            
            return {
                "success": True,
                "stdout": stdout.getvalue(),
                "stderr": stderr.getvalue()
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "stdout": stdout.getvalue(),
                "stderr": stderr.getvalue()
            }

code_worker = CodeWorker()

# =======================================================================
# FASTAPI APP
# =======================================================================
app = FastAPI(title="Phoenix Agentic Coding Tool", version="13.3.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routes
@app.get("/")
async def root():
    return {
        "name": "Phoenix",
        "version": "13.3.0",
        "status": "online",
        "workspace": str(config.workspace)
    }

@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "uptime": time.time() - start_time,
        "gpu": gpu_monitor.has_gpu
    }

@app.get("/gpu/vram")
async def vram():
    """Get VRAM information"""
    return gpu_monitor.get_vram_summary()

@app.get("/gpu/details/{gpu_id}")
async def gpu_details(gpu_id: int = 0):
    """Get detailed GPU stats"""
    return gpu_monitor.get_gpu_details(gpu_id)

@app.get("/ollama/models")
async def list_models():
    """List all Ollama models with context windows"""
    await ollama.refresh_models()
    models = []
    for name in ollama.model_cache.keys():
        details = await ollama.get_model_details(name)
        models.append(details)
    return {"models": models, "count": len(models)}

@app.get("/ollama/model/{name}")
async def model_details(name: str):
    """Get model details including context window"""
    return await ollama.get_model_details(name)

@app.post("/file/read")
async def read_file(request: Request):
    data = await request.json()
    return await file_worker.read(data.get("path", ""))

@app.post("/file/write")
async def write_file(request: Request):
    data = await request.json()
    return await file_worker.write(data.get("path", ""), data.get("content", ""))

@app.get("/file/list")
async def list_dir(path: str = "."):
    return await file_worker.list_dir(path)

@app.post("/code/execute")
async def execute_code(request: Request):
    data = await request.json()
    return await code_worker.execute(data.get("code", ""))

@app.post("/chat")
async def chat(request: Request):
    data = await request.json()
    prompt = data.get("prompt", "")
    system = data.get("system", "You are a helpful AI assistant.")
    context = data.get("context_window", None)
    
    async def generate():
        async for chunk in ollama.generate(prompt, system, context):
            yield f"data: {json.dumps({'content': chunk})}\n\n"
        yield f"data: {json.dumps({'done': True})}\n\n"
    
    return StreamingResponse(generate(), media_type="text/event-stream")

start_time = time.time()

@app.on_event("startup")
async def startup():
    await ollama.init()
    
    # Print banner
    print("\n" + "="*70)
    print("🔥 PHOENIX AGENTIC CODING TOOL v13.3.0")
    print("="*70)
    print(f"📁 Workspace: {config.workspace}")
    
    vram = gpu_monitor.get_vram_summary()
    if vram.get("has_gpu"):
        print(f"🎮 GPU: {vram['total_gpus']} GPU(s)")
        print(f"   Total VRAM: {vram['total_vram_gb']:.1f} GiB")
        print(f"   Available: {vram['free_vram_gb']:.1f} GiB")
    else:
        print("🎮 GPU: None detected")
    
    print(f"🤖 Ollama: {len(ollama.model_cache)} models available")
    print(f"🚀 API: http://{config.host}:{config.port}")
    print("="*70 + "\n")

@app.on_event("shutdown")
async def shutdown():
    await ollama.close()

# =======================================================================
# MAIN
# =======================================================================
if __name__ == "__main__":
    uvicorn.run(app, host=config.host, port=config.port, log_level="info")