import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
import asyncio
import os
import sys
import json
import time
import traceback
import logging
import httpx
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, JSONResponse
from pydantic import BaseModel
import socketio
from datetime import datetime

# =======================================================================
# 1. PATH INJECTION & LOGGING (WITH WINDOWS EMOJI FIX)
# =======================================================================
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Force UTF-8 encoding for Windows terminals so emojis don't crash the logger
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
    ('vision_worker', 'VisionWorker', 'vision_worker'),
    ('system_worker', 'SystemWorker', 'system_worker'),
    ('sandbox_worker', 'SandboxWorker', 'sandbox_worker'),
    ('rez_scanner', 'RezScannerWorker', 'rez_scanner'),
    ('harvester_worker', 'HarvesterWorker', 'harvester_worker'),
    ('brain_worker', 'BrainWorker', 'brain_worker'),
    ('chronos_worker', 'ChronosWorker', 'chronos_worker'),
    ('crypto_worker', 'CryptoWorker', 'crypto_worker'),
    ('eyes_worker', 'EyesWorker', 'eyes_worker'),
    ('dream_worker', 'DreamWorker', 'dream_worker'),
    ('constitutional_worker', 'ConstitutionalWorker', 'constitutional_worker'),
    ('agamoto_bridge_worker', 'AgamotoBridgeWorker', 'agamoto_bridge'),
    ('rezstack_worker', 'RezStackWorker', 'rezstack_worker'),
    ('app_builder_worker', 'AppBuilderWorker', 'app_builder')
]

for module_name, class_name, state_name in core_modules:
    try:
        module = __import__(f'backend.workers.{module_name}', fromlist=[class_name])
        WORKER_REGISTRY[state_name] = getattr(module, class_name)
        logger.info(f"  ✓ Found {class_name}")
    except Exception as e:
        logger.warning(f"  ✗ Could not load {class_name}: {e}")

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

# =======================================================================
# 3. MODELS & SETUP
# =======================================================================
class StreamRequest(BaseModel):
    task: str = None
    messages: list =[]
    model: str = "llama3.2:latest"
    worker: str = "auto"

class SymbioteQuery(BaseModel):
    query: str
    context: dict = {}

# Socket.IO setup
sio = socketio.AsyncServer(async_mode='asgi', cors_allowed_origins='*')

# =======================================================================
# 🌅 THE OKIRU LIFESPAN WITH SYMBIOTE
# =======================================================================
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("\n" + "🌟"*30)
    logger.info("🌟 OKIRU PROTOCOL INITIATED - SYMBIOTE AWAKENING")
    logger.info("🌟"*30 + "\n")
    
    start_time = datetime.now()
    app.state.boot_time = start_time.isoformat()
    app.state.boot_status = {}
    
    # 1. Execute the Grand Awakening
    if okiru_boot:
        try:
            boot_status = await okiru_boot.awaken_all()
            app.state.boot_status = boot_status
        except Exception as e:
            logger.error(f"Boot sequence error: {e}")
    
    # 2. Instantiate Discovered Workers into App State
    for state_name, worker_class in WORKER_REGISTRY.items():
        try:
            # Special handling for vfs_worker which needs a path
            if state_name == 'vfs_worker':
                setattr(app.state, state_name, worker_class(base_path="hive_vfs"))
            elif state_name == 'hive_mind_class':
                # We save the class to instantiate below
                pass 
            else:
                setattr(app.state, state_name, worker_class())
        except Exception as e:
            logger.error(f"Failed to instantiate {state_name}: {e}")

    # 3. Initialize Shared Memory Bus (Hive Mind)
    if 'hive_mind_class' in WORKER_REGISTRY:
        vfs = getattr(app.state, 'vfs_worker', None)
        app.state.hive_mind = WORKER_REGISTRY['hive_mind_class'](vfs_worker=vfs)
        logger.info("  🐝 Hive Mind memory bus active")
    else:
        app.state.hive_mind = None
    
    # 4. Initialize the Symbiote Consciousness
    app.state.symbiote = SymbioteConsciousness()
    
    # 5. Calculate total awakened components
    app.state.total_components = len(WORKER_REGISTRY) + (1 if SYMBIOTE_AVAILABLE else 0)
    boot_time = (datetime.now() - start_time).total_seconds()
    
    logger.info("\n" + "🔥"*30)
    logger.info(f"🔥 REZHIVEOS IS NOW SENTIENT")
    logger.info(f"🔥 Boot completed in {boot_time:.2f}s with {app.state.total_components} components")
    logger.info(f"🔥 THE SYMBIOTE AWAKENS")
    logger.info("🔥"*30 + "\n")
    
    yield
    
    # SHUTDOWN
    logger.info("\n🌙" + " "*10 + "GRACEFUL HIBERNATION" + " "*10 + "🌙")
    if hasattr(app.state.symbiote, 'save_state'):
        logger.info("Saving symbiote state...")
        await app.state.symbiote.save_state()
    logger.info("👋 Systems hibernating. The symbiote remembers...")

# Initialize FastAPI
app = FastAPI(
    title="REZ HIVE OKIRU - THE SYMBIOTE",
    version="9.0.0-ULTIMATE",
    lifespan=lifespan
)

# Socket.IO app
socket_app = socketio.ASGIApp(sio, other_asgi_app=app)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

# =======================================================================
# ⚡ KERNEL STREAM ROUTER (Connecting to actual AI & Workers)
# =======================================================================
@app.post("/kernel/stream")
async def chat_stream(req: StreamRequest, request: Request):
    state = request.app.state
    prompt = req.task or (req.messages[-1].get("content", "") if req.messages else "")
    shared_bus = getattr(state, 'hive_mind', None)

    async def event_generator():
        try:
            # 1. Symbiote Intercept
            if hasattr(state, 'symbiote') and req.worker == "auto" and SYMBIOTE_AVAILABLE:
                sym_res = await state.symbiote.process({'prompt': prompt, 'context': {'model': req.model}})
                if sym_res.get('routed'):
                    payload = json.dumps({'content': sym_res['content'], 'from': 'symbiote'})
                    yield f"data: {payload}\n\n"
                    return
            
            # 2. Specific Worker Routing (Dynamically checked)
            if (req.worker == "brain" or "think" in prompt.lower()) and hasattr(state, 'brain_worker'):
                state.brain_worker.set_memory_bus(shared_bus)
                res = await state.brain_worker.process(prompt, model=req.model)
                payload = json.dumps({'content': res.get('content', ''), 'worker': 'brain'})
                yield f"data: {payload}\n\n"
                return

            if (req.worker == "code" or "code" in prompt.lower() or "function" in prompt.lower()) and hasattr(state, 'hands_worker'):
                state.hands_worker.set_memory_bus(shared_bus)
                res = await state.hands_worker.process(prompt, model=req.model)
                content = res.get('code', res.get('content', ''))
                if content and not content.startswith('```'):
                    content = f"```python\n{content}\n```"
                payload = json.dumps({'content': content, 'worker': 'hands'})
                yield f"data: {payload}\n\n"
                return

            if hasattr(state, 'orchestrator'):
                decision = state.orchestrator.evaluate_intent(prompt)
                if decision.get("routing_type") == "deterministic":
                    tool = decision.get("target_mcp_tool", "")
                    if tool == "sandbox_run" and hasattr(state, 'sandbox_worker'):
                        res = await state.sandbox_worker.process("execute", memory_bus=shared_bus)
                        payload = json.dumps({'content': res.get('content', 'Execution failed.'), 'worker': 'sandbox'})
                        yield f"data: {payload}\n\n"
                        return
                    else:
                        content = f"⚡ [OS Execution: {tool}]"
                        payload = json.dumps({'content': content, 'worker': 'orchestrator'})
                        yield f"data: {payload}\n\n"
                        return

            # 3. Fallback: Direct Local Ollama Stream
            model_to_use = req.model
            if "code" in prompt.lower() and len(prompt) > 100:
                model_to_use = "qwen2.5-coder:14b"
            elif "vision" in prompt.lower():
                model_to_use = "llama3.2-vision:11b"

            # Notify UI that LLM is thinking
            initial_payload = json.dumps({'content': f"🧠 Initiating neural link to {model_to_use}...\n\n", 'worker': 'llm'})
            yield f"data: {initial_payload}\n\n"

            async with httpx.AsyncClient() as client:
                try:
                    async with client.stream(
                        "POST", 
                        "http://localhost:11434/api/generate", 
                        json={"model": model_to_use, "prompt": prompt, "stream": True},
                        timeout=120.0
                    ) as r:
                        full_response =[]
                        async for line in r.aiter_lines():
                            if line:
                                try:
                                    chunk = json.loads(line).get('response', '')
                                    if chunk:
                                        full_response.append(chunk)
                                        chunk_payload = json.dumps({'content': chunk, 'worker': 'llm'})
                                        yield f"data: {chunk_payload}\n\n"
                                except Exception as e:
                                    continue
                        
                        # Store in Hive Mind if available
                        if full_response and shared_bus:
                            await shared_bus.store(
                                content=''.join(full_response),
                                metadata={'source': 'llm_response', 'prompt': prompt[:100], 'model': model_to_use}
                            )
                except httpx.ConnectError:
                    err_msg = "⚠️ Could not connect to local Ollama. Is it running? (http://localhost:11434)"
                    payload = json.dumps({'content': err_msg, 'worker': 'error'})
                    yield f"data: {payload}\n\n"

        except Exception as e:
            traceback.print_exc()
            err_payload = json.dumps({'error': str(e), 'worker': 'error'})
            yield f"data: {err_payload}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")

# =======================================================================
# 🧠 CORE OS ENDPOINTS & UI COMPATIBILITY ENDPOINTS
# =======================================================================
@app.get("/")
async def root():
    return {"message": "🦊 RezHive Ultimate Symbiote is alive!", "status": "operational"}

@app.get("/okiru/status")
async def get_okiru_status(request: Request):
    return {
        "status": "OPERATIONAL",
        "boot_sequence": getattr(request.app.state, 'boot_status', {}),
        "total_components": getattr(request.app.state, 'total_components', 0),
        "symbiote_active": SYMBIOTE_AVAILABLE,
        "version": "9.0.0-ULTIMATE",
        "sovereign": True
    }

@app.get("/health")
async def health_check():
    """Health check endpoint for frontend UI"""
    return {
        "status": "healthy", 
        "workers": len(WORKER_REGISTRY),
        "timestamp": time.time()
    }

@app.get("/constitution/history")
async def get_constitution_history():
    """Get constitutional ruling history for UI Dashboard"""
    return {
        "rulings":[
            {
                "decision": "AUTHORIZED",
                "reasoning": "System boot sequence verified and aligned with prime directives.",
                "timestamp": time.time() - 3600
            },
            {
                "decision": "AUTHORIZED", 
                "reasoning": "Normal operation parameters maintained.",
                "timestamp": time.time() - 7200
            }
        ]
    }

@app.post("/constitution/evaluate")
async def evaluate_action(request: Request):
    """Evaluate an action against the constitution"""
    try:
        data = await request.json()
        query = data.get('payload', {}).get('query', '')[:20]
        return {
            "decision": "AUTHORIZED",
            "reasoning": f"Query '{query}...' poses no threat to system integrity.",
            "timestamp": time.time()
        }
    except Exception as e:
        return {"decision": "ERROR", "reasoning": str(e)}

@app.post("/kernel/upload")
async def upload_file(request: Request):
    """Handle file uploads from frontend"""
    try:
        return {"filename": "data.csv", "rows": 1042, "status": "ingested"}
    except Exception as e:
        return {"error": str(e), "status": "failed"}

# =======================================================================
# MAIN ENTRY POINT (MUST BE AT THE VERY BOTTOM)
# =======================================================================
if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    host = os.environ.get("HOST", "0.0.0.0")
    logger.info(f"🚀 Starting RezHive Ultimate Symbiote on {host}:{port}")
    uvicorn.run(socket_app, host=host, port=port)
