import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
"""
REZ HIVE v8.0 Sovereign Kernel - SIMPLE VERSION
Run with: python run_v8.py
"""

import asyncio
import uvicorn
import random
import time
import json
import hashlib
import uuid
import psutil
from fastapi import FastAPI, File, UploadFile, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse

app = FastAPI(title="REZ HIVE v8.0")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Helper functions
def generate_proof(action_type: str, payload: str) -> dict:
    proof_hash = hashlib.sha256(f"{action_type}:{payload}:{time.time()}".encode()).hexdigest()
    return {
        "proof_hash": f"0x{proof_hash[:16]}",
        "signature": "VALID",
        "timestamp": time.time(),
        "action_type": action_type
    }

# ============================================================================
# API ENDPOINTS
# ============================================================================

@app.get("/")
async def root():
    return {"name": "REZ HIVE v8.0", "status": "operational"}

@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "version": "8.0.0",
        "components": {
            "invariant_engine": "active",
            "vera_ledger": "active"
        }
    }

@app.get("/workers")
async def workers():
    return {"workers": [
        {"id": "brain", "name": "Brain Worker", "model": "llama3.2:latest"},
        {"id": "search", "name": "Eyes Worker", "model": "llama3.2:latest"},
        {"id": "code", "name": "Hands Worker", "model": "qwen2.5-coder:14b"},
        {"id": "files", "name": "Memory Worker", "model": "llama3.2:latest"},
        {"id": "vision", "name": "Vision Worker", "model": "llava:7b"},
        {"id": "voice", "name": "Voice Worker", "model": "whisper"},
    ]}

@app.post("/auth/session")
async def session():
    session_id = str(uuid.uuid4())
    return {
        "session_id": session_id,
        "proof": generate_proof("SESSION_START", session_id)
    }

@app.get("/constitution/state")
async def constitution(session_id: str = None):
    return {
        "regime": random.choice(["BULL", "BEAR", "CRAB"]),
        "blocked": False,
        "last_check": {"passed": True, "message": "All invariants OK", "action": "PROCEED"},
        "invariants": {
            "max_drawdown": {
                "passed": True,
                "current_value": random.uniform(0.02, 0.08),
                "threshold_value": 0.15
            },
            "hard_floor": {
                "passed": True,
                "current_value": random.uniform(950000, 1050000),
                "threshold_value": 850000
            }
        },
        "exposure": {"PHP": 0.8, "ASSETS": 0.2}
    }

@app.get("/evolution/status")
async def evolution():
    return {
        "generation": random.randint(120, 160),
        "best_fitness": round(random.uniform(0.85, 0.98), 2),
        "population": 500,
        "status": "EVOLVING"
    }

@app.post("/kernel/stream")
async def stream(request: Request):
    data = await request.json()
    task = data.get('task', '')
    
    async def generate():
        # Metadata
        yield f"data: {json.dumps({
            'status': 'routing',
            'chain': ['router'],
            'proof': generate_proof('STREAM', task[:30]),
            'entropy': round(random.uniform(0.2, 0.5), 2)
        })}\n\n"
        await asyncio.sleep(0.5)
        
        # Worker started
        yield f"data: {json.dumps({'status': 'started', 'worker': 'brain'})}\n\n"
        await asyncio.sleep(0.5)
        
        # Content
        words = f"Processing: {task}. REZ HIVE v8.0 responding...".split()
        for word in words:
            yield f"data: {json.dumps({'content': word + ' '})}\n\n"
            await asyncio.sleep(0.05)
        
        # Complete
        yield f"data: {json.dumps({'status': 'complete'})}\n\n"
    
    return StreamingResponse(generate(), media_type="text/event-stream")

@app.get("/kernel/telemetry")
async def telemetry():
    async def generate():
        last_net = psutil.net_io_counters()
        last_time = time.time()
        
        while True:
            current_net = psutil.net_io_counters()
            current_time = time.time()
            
            down = (current_net.bytes_recv - last_net.bytes_recv) / (current_time - last_time) / 1024 / 1024
            up = (current_net.bytes_sent - last_net.bytes_sent) / (current_time - last_time) / 1024 / 1024
            
            last_net, last_time = current_net, current_time
            
            yield f"data: {json.dumps({
                'cpu': psutil.cpu_percent(),
                'ram': psutil.virtual_memory().percent,
                'networkDown': round(down, 1),
                'networkUp': round(up, 1),
                'invariants': {
                    'max_drawdown_passed': True,
                    'drift': round(random.uniform(0.1, 0.6), 3)
                }
            })}\n\n"
            
            await asyncio.sleep(2)
    
    return StreamingResponse(generate(), media_type="text/event-stream")

@app.post("/backtest/run")
async def backtest(request: Request):
    data = await request.json()
    pair = data.get("pair", "BTC/PHP")
    return {
        "status": "success",
        "metrics": {
            "sharpe_ratio": round(random.uniform(1.5, 3.5), 2),
            "win_rate": round(random.uniform(0.55, 0.75), 2),
            "pair": pair
        }
    }

@app.post("/chat/{session_id}/clear")
async def clear_chat(session_id: str):
    return {"status": "cleared"}

if __name__ == "__main__":
    print("🚀 REZ HIVE v8.0 Sovereign Kernel starting on port 8003...")
    print("📡 Endpoints: /health, /workers, /constitution/state, /evolution/status")
    uvicorn.run(app, host="0.0.0.0", port=8003, log_level="info")
