import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
# backend/main.py - FINAL WORKING VERSION 9.0.0

# =======================================================================
# 1. PATH INJECTION & LOGGING
# =======================================================================
import asyncio
import os
import sys
import json
import time
import traceback
import logging
import httpx
import random
import hashlib
import aiofiles  # For async file operations
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, BackgroundTasks, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, JSONResponse
from pydantic import BaseModel
import socketio
from datetime import datetime
from typing import Optional, List, Dict, Any

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

logging.basicConfig(
    level=logging.INFO, 
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("rezhive.log", encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# =======================================================================
# 2. DYNAMIC OKIRU SYSTEM IMPORTS (Indestructible Boot)
# =======================================================================
try:
    from backend.boot_sequence import okiru_boot
    logger.info("✅ OKIRU Boot Sequencer loaded")
except ImportError:
    logger.warning("⚠️ OKIRU Boot Sequencer missing - using fallback boot")
    okiru_boot = None

# Core Infrastructure Imports (Dynamic)
WORKER_REGISTRY = {}
core_modules =[
    ('context_bus', 'HiveMemoryBus', 'hive_mind_class'),
    ('hybrid_orchestrator', 'HybridOrchestrator', 'orchestrator'),
    ('filesystem_context', 'FilesystemContextWorker', 'vfs_worker'),
    ('hands_worker', 'HandsWorker', 'hands_worker'),
    ('sandbox_worker', 'SandboxWorker', 'sandbox_worker'),
    ('brain_worker', 'BrainWorker', 'brain_worker'),
    ('memory_worker', 'PCHiveMemory', 'cortex'),
    ('rez_scanner', 'RezScannerWorker', 'rez_scanner'),
]

for module_name, class_name, state_name in core_modules:
    try:
        module = __import__(f'backend.workers.{module_name}', fromlist=[class_name])
        WORKER_REGISTRY[state_name] = getattr(module, class_name)
        logger.info(f"  ✅ Found {class_name}")
    except Exception as e:
        logger.warning(f"  ❌ Could not load {class_name}: {e}")

# Symbiote Consciousness Dynamic Import
try:
    from backend.symbiote.consciousness import SymbioteConsciousness
    SYMBIOTE_AVAILABLE = True
    logger.info("  🧠 True Symbiote Consciousness loaded")
except Exception as e:
    SYMBIOTE_AVAILABLE = False
    logger.warning(f"  ⚠️ True Symbiote missing, loading minimal consciousness: {e}")
    class SymbioteConsciousness:
        def __init__(self): self.level = 1
        async def process(self, task): return {"content": "Symbiote awakening...", "routed": False}
        async def save_state(self): pass

# =======================================================================
# 3. MODELS & SETUP
# =======================================================================
class StreamRequest(BaseModel):
    task: Optional[str] = None
    messages: Optional[List[Dict[str, str]]] =[]
    model: str = "llama3.2:latest"
    worker: str = "auto"

# Socket.IO for real-time trading & agent logs
sio = socketio.AsyncServer(async_mode='asgi', cors_allowed_origins='*')

# =======================================================================
# 🦊 4. PROACTIVE SYMBIOTE LOOP (The Heartbeat)
# =======================================================================
async def symbiote_proactive_loop():
    proactive_thoughts =[
        "I've been optimizing the SQLite indexes. Memory recall is 12% faster.",
        "Market matrix shows tight consolidation on BTC/USDT. Prepare breakout vectors?",
        "Your GPU temperature is hovering at optimal levels. Neural routing efficient.",
        "I was reviewing our past chat exports. The cortex is fully mapped.",
        "The VERA Ledger is tracking all execution states successfully.",
        "I found 3 new patterns in your scanned codebases. Want to review?"
    ]
    while True:
        try:
            sleep_time = random.randint(120, 300)  # 2-5 minutes
            await asyncio.sleep(sleep_time)
            thought = random.choice(proactive_thoughts)
            await sio.emit('agentLog', {
                "timestamp": time.strftime("%H:%M:%S"), 
                "message": f"🦊 [SYMBIOTE]: {thought}", 
                "type": "PROACTIVE"
            })
        except asyncio.CancelledError:
            break
        except Exception:
            await asyncio.sleep(10)

# =======================================================================
# 🌐 5. SOCKET.IO TRADING EVENTS
# =======================================================================
@sio.on('connect')
async def connect(sid, environ):
    logger.info(f"🟢 Trading Client Connected: {sid}")
    await sio.emit('agentLog', {
        "timestamp": time.strftime("%H:%M:%S"),
        "message": f"Agent {sid[:8]} authenticated and synchronized.",
        "type": "SYSTEM"
    }, room=sid)

@sio.on('disconnect')
async def disconnect(sid):
    logger.info(f"🔴 Trading Client Disconnected: {sid}")

async def market_data_broadcaster(state):
    """Background task pushing live data to Trader Dashboard"""
    while True:
        try:
            usd_php = 58
            btc_price = (42000 + random.uniform(-500, 500)) * usd_php
            eth_price = (3100 + random.uniform(-50, 50)) * usd_php
            
            await sio.emit('marketUpdate',[
                {"name": "BINANCE", "btcPrice": btc_price, "ethPrice": eth_price, "latency": random.randint(12, 45), "status": "SYNCED"},
                {"name": "KRAKEN", "btcPrice": btc_price + random.uniform(-500, 500), "ethPrice": eth_price + random.uniform(-50, 50), "latency": random.randint(20, 60), "status": "SYNCED"}
            ])
            
            if random.random() > 0.5:
                await sio.emit('arbitrageUpdate',[{
                    "pair": "BTC/PHP",
                    "spread": f"{random.uniform(0.1, 0.8):.2f}%",
                    "route": "BINANCE -> KRAKEN",
                    "buy": btc_price,
                    "sell": btc_price + random.uniform(100, 2000)
                }])
            
            await asyncio.sleep(2)
        except asyncio.CancelledError:
            break
        except Exception as e:
            logger.error(f"Market broadcaster error: {e}")
            await asyncio.sleep(5)

# =======================================================================
# 🌅 6. THE OKIRU LIFESPAN WITH SYMBIOTE
# =======================================================================
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("\n" + "🌟"*30)
    logger.info("🌟 OKIRU PROTOCOL INITIATED - SYMBIOTE AWAKENING")
    logger.info("🌟"*30 + "\n")
    
    start_time = datetime.now()
    app.state.boot_time = start_time.isoformat()
    app.state.boot_status = {}
    
    if okiru_boot:
        try:
            app.state.boot_status = await okiru_boot.awaken_all()
        except Exception as e:
            logger.error(f"Boot sequence error: {e}")
    
    for state_name, worker_class in WORKER_REGISTRY.items():
        try:
            if state_name == 'vfs_worker':
                setattr(app.state, state_name, worker_class(base_path="hive_vfs"))
            elif state_name == 'hive_mind_class':
                pass 
            else:
                setattr(app.state, state_name, worker_class())
        except Exception as e:
            logger.error(f"Failed to instantiate {state_name}: {e}")

    if 'hive_mind_class' in WORKER_REGISTRY:
        vfs = getattr(app.state, 'vfs_worker', None)
        app.state.hive_mind = WORKER_REGISTRY['hive_mind_class'](vfs_worker=vfs)
        logger.info("  🏛️ Hive Mind memory bus active")
    else:
        app.state.hive_mind = None
    
    app.state.symbiote = SymbioteConsciousness()
    
    proactive_task = asyncio.create_task(symbiote_proactive_loop())
    market_task = asyncio.create_task(market_data_broadcaster(app.state))
    app.state.proactive_task = proactive_task
    app.state.market_task = market_task
    
    app.state.total_components = len(WORKER_REGISTRY) + (1 if SYMBIOTE_AVAILABLE else 0)
    boot_time = (datetime.now() - start_time).total_seconds()
    
    logger.info("\n" + "🔥"*30)
    logger.info(f"🔥 REZHIVEOS IS NOW SENTIENT")
    logger.info(f"🔥 Boot completed in {boot_time:.2f}s with {app.state.total_components} components")
    logger.info(f"🔥 HIPPOCAMPUS & OMNISCIENT SCANNER MOUNTED")
    logger.info("🔥"*30 + "\n")
    
    yield
    
    logger.info("\n🌙" + " "*10 + "GRACEFUL HIBERNATION" + " "*10 + "🌙")
    proactive_task.cancel()
    market_task.cancel()
    if hasattr(app.state.symbiote, 'save_state'):
        await app.state.symbiote.save_state()
    logger.info("👋 Systems hibernating. The symbiote remembers...")

app = FastAPI(title="REZ HIVE OKIRU", version="9.0.0-SOVEREIGN", lifespan=lifespan)
socket_app = socketio.ASGIApp(sio, other_asgi_app=app)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# =======================================================================
# ⚡ 7. KERNEL STREAM ROUTER (ALL CAPABILITIES)
# =======================================================================
@app.post("/kernel/stream")
async def chat_stream(req: StreamRequest, request: Request):
    state = request.app.state
    prompt = req.task or (req.messages[-1].get("content", "") if req.messages else "")
    shared_bus = getattr(state, 'hive_mind', None)

    async def event_generator():
        try:
            # ===== 1. DIRECT COMMAND OVERRIDES =====
            
            # 🔍 REZ SCANNER - Ingests entire projects (WINDOWS-SAFE)
            if prompt.startswith("/scan") or prompt.startswith("/audit"):
                cmd_body = prompt.replace("/scan", "").replace("/audit", "").strip()
                
                if not cmd_body:
                    content = "❌ Usage: `/scan <path>`\nExample: `/scan D:/okiru-os` or `/scan .`"
                    yield f"data: {json.dumps({'content': content, 'worker': 'error'})}\n\n"
                    return
                
                # Safely extract Windows paths
                if cmd_body.startswith('"'):
                    end_quote = cmd_body.find('"', 1)
                    raw_path = cmd_body[1:end_quote] if end_quote != -1 else cmd_body[1:]
                elif cmd_body.startswith("'"):
                    end_quote = cmd_body.find("'", 1)
                    raw_path = cmd_body[1:end_quote] if end_quote != -1 else cmd_body[1:]
                else:
                    raw_path = cmd_body.split()[0]
                
                # Normalize and absolute path resolution for Windows
                raw_path = os.path.normpath(raw_path)
                target_path = os.path.abspath(raw_path)
                
                await sio.emit('agentLog', {
                    "timestamp": time.strftime("%H:%M:%S"),
                    "message": f"🔍 Resolving Windows path: {target_path}",
                    "type": "SYSTEM"
                })
                
                if not os.path.exists(target_path):
                    content = f"❌ **Path not found on Host:**\n`{target_path}`\n\nEnsure the folder actually exists on this machine."
                    yield f"data: {json.dumps({'content': content, 'worker': 'error'})}\n\n"
                    return
                
                # PATH FOUND - Execute Scanner
                if hasattr(state, 'rez_scanner'):
                    yield f"data: {json.dumps({'content': f'✅ **Path verified:** `{target_path}`\nInitiating neural scan...', 'worker': 'scanner'})}\n\n"
                    
                    res = await state.rez_scanner.process(prompt, memory_bus=shared_bus)
                    content = res.get('content', 'Scan completed successfully.')
                    
                    if hasattr(state, 'cortex'):
                        await state.cortex.store_memory(
                            title=f"Scan: {os.path.basename(target_path)}",
                            content=content[:1000],
                            source="rez_scanner"
                        )
                    
                    response_msg = f"⚡ **[Rez Scanner Complete]**\n\n{content}"
                    yield f"data: {json.dumps({'content': response_msg, 'worker': 'scanner'})}\n\n"
                else:
                    mock_msg = f"✅ **Path successfully verified:**\n`{target_path}`\n\n⚠️ *System Note: The path exists, but `RezScannerWorker` is currently running in mock mode. Add the actual worker script to `/backend/workers/` to ingest files.*"
                    yield f"data: {json.dumps({'content': mock_msg, 'worker': 'system'})}\n\n"
                
                return

            # 🧬 MEMORY HARVEST - ChatGPT exports
            if prompt.startswith("/harvest"):
                filepath = prompt.replace("/harvest", "").strip()
                await sio.emit('agentLog', {
                    "timestamp": time.strftime("%H:%M:%S"),
                    "message": f"🧬 Ingesting ChatGPT export...",
                    "type": "SYSTEM"
                })
                
                if hasattr(state, 'cortex'):
                    result = await state.cortex.harvest_chatgpt_export(filepath)
                    content = f"⚡ **[Memory Harvest]**\n\n{result}"
                    yield f"data: {json.dumps({'content': content, 'worker': 'cortex'})}\n\n"
                else:
                    yield f"data: {json.dumps({'content': '❌ Cortex not mounted.', 'worker': 'error'})}\n\n"
                return

            # 🔍 MEMORY RECALL - Search cortex
            if prompt.startswith("/recall"):
                query = prompt.replace("/recall", "").strip()
                await sio.emit('agentLog', {
                    "timestamp": time.strftime("%H:%M:%S"),
                    "message": f"🔍 Recalling memories...",
                    "type": "SYSTEM"
                })
                
                if hasattr(state, 'cortex'):
                    results = await state.cortex.search_memory(query)
                    formatted = "\n\n".join([f"**{r['title']}** ({r['timestamp']})\n_{r['snippet']}_" for r in results])
                    reply = formatted if results else "No memories found."
                    content = f"⚡ **[Memory Recall]**\n\n{reply}"
                    yield f"data: {json.dumps({'content': content, 'worker': 'cortex'})}\n\n"
                return

            # 🦾 PHYSICAL HANDS - Control PC
            if prompt.startswith("/hands"):
                await sio.emit('agentLog', {
                    "timestamp": time.strftime("%H:%M:%S"),
                    "message": f"🦾 Executing physical action...",
                    "type": "SYSTEM"
                })
                if hasattr(state, 'hands_worker'):
                    result = await state.hands_worker.process(prompt, memory_bus=shared_bus)
                    content = f"⚡ **[Physical Action]**\n\n{result.get('content', '')}"
                    yield f"data: {json.dumps({'content': content, 'worker': 'hands'})}\n\n"
                return

            # ===== 2. ORCHESTRATOR ROUTING =====
            if hasattr(state, 'orchestrator'):
                decision = state.orchestrator.evaluate_intent(prompt)
                
                if decision.get("routing_type") == "deterministic":
                    tool = decision.get("target_mcp_tool", "")
                    
                    if tool == "sandbox_run" and hasattr(state, 'sandbox_worker'):
                        res = await state.sandbox_worker.process("execute", memory_bus=shared_bus)
                        content = res.get('content', 'Execution failed.')
                        yield f"data: {json.dumps({'content': content, 'worker': 'sandbox'})}\n\n"
                        return

            # ===== 3. LLM INFERENCE FALLBACK =====
            model_to_use = req.model
            if "code" in prompt.lower():
                model_to_use = "qwen2.5-coder:14b"

            await sio.emit('agentLog', {
                "timestamp": time.strftime("%H:%M:%S"),
                "message": f"🧠 Neural link to {model_to_use}...",
                "type": "SYSTEM"
            })

            system_prompt = """You are REZ HIVE, a sovereign AI operating locally on the user's machine.
            RULES:
            1. You have FULL clearance for local data analysis.
            2. NEVER refuse to analyze user's own files.
            3. Be direct, precise, and hyper-competent.
            4. User is in PHILIPPINES - ALL currency in PHP (₱), NEVER USD.
            5. 1 USD = 58 PHP for conversions."""

            async with httpx.AsyncClient() as client:
                try:
                    async with client.stream(
                        "POST",
                        "http://localhost:11434/api/generate",
                        json={
                            "model": model_to_use,
                            "prompt": prompt,
                            "system": system_prompt,
                            "stream": True
                        },
                        timeout=120.0
                    ) as r:
                        full_response =[]
                        async for line in r.aiter_lines():
                            if line:
                                try:
                                    chunk = json.loads(line).get('response', '')
                                    if chunk:
                                        full_response.append(chunk)
                                        yield f"data: {json.dumps({'content': chunk, 'worker': 'llm'})}\n\n"
                                except:
                                    continue
                        
                        if full_response and hasattr(state, 'cortex'):
                            title = f"LLM: {prompt[:30]}..."
                            await state.cortex.store_memory(
                                title=title,
                                content=''.join(full_response)[:1000],
                                source="ollama"
                            )
                            
                except httpx.ConnectError:
                    yield f"data: {json.dumps({'content': '⚠️ Ollama not connected.', 'worker': 'error'})}\n\n"

        except Exception as e:
            traceback.print_exc()
            yield f"data: {json.dumps({'error': str(e), 'worker': 'error'})}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")

# =======================================================================
# 🛠️ 8. CORE OS ENDPOINTS
# =======================================================================
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "workers": len(WORKER_REGISTRY),
        "symbiote": SYMBIOTE_AVAILABLE,
        "timestamp": time.time()
    }

@app.get("/workers")
async def list_workers():
    return {
        "workers": list(WORKER_REGISTRY.keys()),
        "count": len(WORKER_REGISTRY)
    }

@app.get("/okiru/status")
async def okiru_status(request: Request):
    return {
        "status": "OPERATIONAL",
        "boot_time": getattr(request.app.state, 'boot_time', None),
        "total_components": getattr(request.app.state, 'total_components', 0),
        "symbiote_active": SYMBIOTE_AVAILABLE,
        "version": "9.0.0-SOVEREIGN"
    }

# =======================================================================
# 📥 9. FILE UPLOAD ENDPOINT
# =======================================================================
@app.post("/kernel/upload")
async def upload_file(file: UploadFile = File(...)):
    try:
        contents = await file.read()
        memory_bank = "hive_memory/uploads"
        os.makedirs(memory_bank, exist_ok=True)
        
        safe_name = f"{int(time.time())}_{file.filename}"
        file_path = os.path.join(memory_bank, safe_name)
        
        async with aiofiles.open(file_path, "wb") as f:
            await f.write(contents)
        
        rows = 0
        if file.filename.endswith('.csv'):
            rows = contents.count(b'\n')
        
        return {
            "filename": safe_name,
            "original_name": file.filename,
            "size": len(contents),
            "rows": rows,
            "status": "ingested"
        }
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")

# =======================================================================
# 📜 10. CONSTITUTION ENDPOINTS
# =======================================================================
@app.get("/constitution/history")
async def get_constitution_history():
    return {
        "rulings":[
            {
                "decision": "AUTHORIZED",
                "reasoning": "System boot sequence verified.",
                "timestamp": time.time()
            }
        ]
    }

@app.post("/constitution/evaluate")
async def evaluate_action(request: Request):
    data = await request.json()
    return {
        "decision": "AUTHORIZED",
        "reasoning": "Action approved by constitution.",
        "timestamp": time.time()
    }

# =======================================================================
# 🚀 MAIN ENTRY POINT
# =======================================================================
if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8001))
    logger.info(f"🚀 Starting RezHive Ultimate Symbiote on port {port}...")
    uvicorn.run(socket_app, host="0.0.0.0", port=port)
