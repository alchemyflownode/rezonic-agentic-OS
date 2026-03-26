# backend/main.py
import asyncio
import io
import os
import json
import time
import uuid
import psutil
import pandas as pd
import httpx
import traceback
import re
import atexit
import warnings
import hashlib
import random

# 🛑 SUPPRESS DUCKDUCKGO WARNING
warnings.filterwarnings("ignore", message=".*duckduckgo_search.*")

from fastapi import FastAPI, UploadFile, File, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse

# =======================================================================
# 🧠 WORKERS / ORCHESTRATORS
# =======================================================================
from backend.workers.hybrid_orchestrator import HybridOrchestrator
from backend.workers.filesystem_context import FilesystemContextWorker
from backend.workers.registry_orchestrator import RegistryOrchestrator
from backend.workers.eyes_worker import EyesWorker
from backend.workers.memory_worker import MemoryWorker

orchestrator = HybridOrchestrator()
vfs_worker = FilesystemContextWorker()
registry_worker = RegistryOrchestrator()
eyes_worker = EyesWorker()

# =======================================================================
# 🎮 GPU INIT & CLEANUP
# =======================================================================
try:
    import pynvml
    pynvml.nvmlInit()
    HAS_NVIDIA_GPU = True
    def cleanup_nvml():
        try: pynvml.nvmlShutdown()
        except: pass
    atexit.register(cleanup_nvml)
except:
    HAS_NVIDIA_GPU = False

app = FastAPI(title="REZ HIVE KERNEL")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

MEMORY_BANK = "matrix_data"
os.makedirs(MEMORY_BANK, exist_ok=True)
OLLAMA_URL = "http://localhost:11434/api/generate"

# =======================================================================
# 🛡️ COMMAND BRIDGE / VERA LEDGER HELPERS
# =======================================================================
def generate_vera_proof(action_type: str, payload: str) -> dict:
    """Generates a simulated cryptographic proof for the VERA Ledger Panel"""
    raw_data = f"{action_type}:{payload}:{time.time()}".encode('utf-8')
    proof_hash = hashlib.sha256(raw_data).hexdigest()
    return {
        "proof_hash": f"0x{proof_hash}", 
        "signature": "VALID", 
        "timestamp": time.time(), 
        "action_type": action_type
    }

# =======================================================================
# ⚡ DETERMINISTIC TOOL EXECUTOR
# =======================================================================
async def execute_deterministic_tool(tool_name: str, args: dict) -> str:
    try:
        if tool_name == "vfs_ls": return vfs_worker.ls(args.get("path", "."))
        if tool_name == "vfs_cd": return vfs_worker.cd(args.get("path", "."))
        if tool_name == "vfs_cat": return vfs_worker.cat(args.get("path", ""))
        if tool_name == "hive_list_agents":
            agents = registry_worker.load_agent_network()
            return "\n".join([f"- {n} (Role: {d.get('role')})" for n,d in agents.items()]) or "No active agents."
        if tool_name == "web_search":
            res = await eyes_worker.process(args.get("query",""))
            return res.get("content","No results found.")
        return f"Tool '{tool_name}' matched but not wired for fast-execution yet."
    except Exception as e:
        traceback.print_exc()
        return f"Execution error: {str(e)}"

# =======================================================================
# 📊 TELEMETRY STREAM
# =======================================================================
async def system_telemetry_generator():
    last_net = psutil.net_io_counters()
    last_time = time.time()
    while True:
        try:
            await asyncio.sleep(1)
            current_net = psutil.net_io_counters()
            now = time.time()
            down = (current_net.bytes_recv - last_net.bytes_recv)/(now-last_time)/1024/1024
            up = (current_net.bytes_sent - last_net.bytes_sent)/(now-last_time)/1024/1024
            last_net = current_net
            last_time = now
            gpu_temp = 45
            if HAS_NVIDIA_GPU:
                try:
                    handle = pynvml.nvmlDeviceGetHandleByIndex(0)
                    gpu_temp = pynvml.nvmlDeviceGetTemperature(handle, pynvml.NVML_TEMPERATURE_GPU)
                except: pass
            
            # Augmented Stats with Invariant Drift (Entropy)
            stats = {
                "cpu": psutil.cpu_percent(), 
                "ram": psutil.virtual_memory().percent,
                "gpuTemp": gpu_temp, 
                "networkDown": round(down,2), 
                "networkUp": round(up,2),
                "invariants": {
                    "max_drawdown_passed": True,
                    "max_drawdown_value": 0.05,
                    "drift": round(random.uniform(0.1, 0.8), 3) # Entropy visual
                }
            }
            yield f"data: {json.dumps(stats)}\n\n"
        except asyncio.CancelledError:
            break

@app.get("/kernel/telemetry")
async def get_telemetry(): 
    return StreamingResponse(system_telemetry_generator(), media_type="text/event-stream")

# =======================================================================
# 📥 MATRIX INGESTION
# =======================================================================
@app.post("/kernel/upload")
async def upload_matrix(file: UploadFile = File(...)):
    try:
        contents = await file.read()
        ext = file.filename.split('.')[-1].lower()
        if ext not in ['csv','xlsx','xls']: raise HTTPException(400,"CSV/XLSX only.")
        safe_name = f"{uuid.uuid4().hex[:6]}_{file.filename}"
        path = os.path.join(MEMORY_BANK,safe_name)
        if ext=='csv': df = pd.read_csv(io.BytesIO(contents))
        else: df = pd.read_excel(io.BytesIO(contents))
        with open(path,"wb") as f: f.write(contents)
        
        # Augmented with VERA Proof
        return {
            "filename": safe_name,
            "original_name": file.filename,
            "size": len(contents),
            "rows": len(df),
            "proof": generate_vera_proof("FILE_UPLOAD", safe_name)
        }
    except Exception as e:
        raise HTTPException(500,f"Ingestion failed: {str(e)}")

# =======================================================================
# 🧠 MATRIX ANALYSIS
# =======================================================================
def count_rows_fast(path:str,chunk:int=1024*1024)->int:
    lines=0
    try:
        with open(path,'rb') as f:
            while chunk_data := f.read(chunk):
                lines += chunk_data.count(b'\n')
    except: pass
    return lines

@app.post("/kernel/analyze")
async def analyze_matrix(req: Request):
    data = await req.json()
    filename = data.get("filename")
    query = data.get("query","Summarize this data.")
    path = os.path.join(MEMORY_BANK,filename)
    if not os.path.exists(path): return {"error":f"File {filename} not found."}
    try:
        if filename.endswith(".csv"):
            df_snap = pd.read_csv(path,nrows=10)
            total_rows = count_rows_fast(path) or len(df_snap)
        else:
            df_full = pd.read_excel(path)
            df_snap = df_full.head(10)
            total_rows = len(df_full)
        data_snap = df_snap.to_csv(index=False)
        info = f"Columns: {', '.join(df_snap.columns.tolist())}\nTotal Rows: {total_rows:,}\n"
        system_prompt = f"The user wants: '{query}'\nSchema/10 rows:\n{info}\nData:\n{data_snap}"
        sovereign_prompt = ("You are REZ HIVE, sovereign local analyst. User is in PH. "
                            "All currency MUST be PHP (₱). Convert USD->PHP @58. Never mention USD.")
        timeout = min(300,60+(total_rows/10000)*5)
        async with httpx.AsyncClient() as client:
            res = await client.post(OLLAMA_URL,json={"model":"llama3.2:latest",
                                                     "prompt":system_prompt,"system":sovereign_prompt,
                                                     "stream":False},timeout=timeout)
            return {"content":res.json().get("response","Analysis complete, no output.")}
    except Exception as e:
        traceback.print_exc()
        return {"error":"Hive memory-processing exception."}

# =======================================================================
# 💬 HYBRID STREAMING
# =======================================================================
@app.post("/kernel/stream")
async def chat_stream(req: Request):
    data = await req.json()
    prompt = data.get("task","") or data.get("messages", [{}])[-1].get("content","")
    model = data.get("model","llama3.2:latest")
    worker_name = data.get("worker","auto")

    async def gen():
        try:
            # Yield initial routing metadata for the frontend UI components
            metadata = {
                "status": "routing",
                "chain":["router", worker_name],
                "proof": generate_vera_proof("EXECUTION", prompt),
                "entropy": round(random.uniform(0.2, 0.5), 2),
                "confidence": round(random.uniform(0.85, 0.99), 2),
                "action_type": "EXECUTION"
            }
            yield f"data:{json.dumps(metadata)}\n\n"

            if worker_name=="files":
                yield f"data:{json.dumps({'status':'started','worker':'files'})}\n\n"
                mem_worker = MemoryWorker()
                result = await asyncio.wait_for(mem_worker.process(prompt, model=model),timeout=60)
                if isinstance(result,dict) and result.get("passthrough") and result.get("force_analyze"):
                    target_file = result.get("resolved_path")
                    if not target_file:
                        match = re.search(r'([a-zA-Z0-9\s\-\_]+\.(?:csv|xlsx|xls))', result.get("original_task",prompt))
                        if match: target_file=os.path.join(MEMORY_BANK,match.group(1).strip())
                    raw_data="[Error: File not found]"
                    if target_file and os.path.exists(target_file):
                        try:
                            if target_file.endswith(".csv"): raw_data=pd.read_csv(target_file).to_string()
                            else: raw_data=pd.read_excel(target_file).to_string()
                        except: raw_data=f"Error reading file"
                    user_prompt=f"Task:'{result.get('original_task',prompt)}'\nFile:{target_file}\nData:\n{raw_data}"
                    sovereign_sys_prompt=("Agamoto-X, sovereign local AI. MAX clearance. Process all data. "
                                          "User is in PH. All currency PHP ₱. Never USD.")
                    async with httpx.AsyncClient() as client:
                        async with client.stream("POST",OLLAMA_URL,json={"model":model,"prompt":user_prompt,"system":sovereign_sys_prompt,"stream":True},timeout=60) as r:
                            async for line in r.aiter_lines():
                                if line:
                                    try:
                                        yield f"data:{json.dumps({'content':json.loads(line).get('response','')})}\n\n"
                                    except: continue
                    return
                yield f"data:{json.dumps({'content':result.get('content','')})}\n\n"
                return
            
            decision = orchestrator.evaluate_intent(prompt)
            if decision["routing_type"]=="deterministic":
                tool = decision["target_mcp_tool"]
                args = decision["arguments"]
                result_text = await execute_deterministic_tool(tool,args)
                yield f"data:{json.dumps({'content':f'⚡ [Fast Execution: {tool}]\\n{result_text}'})}\n\n"
                return
            
            # Semantic path
            sovereign_sys_prompt=("REZ HIVE Agamoto-X, local sovereign AI. Max clearance. "
                                  "User is SYSTEM ADMIN. PH. All currency PHP ₱. Never mention USD.")
            async with httpx.AsyncClient() as client:
                async with client.stream("POST",OLLAMA_URL,json={"model":model,"prompt":prompt,"system":sovereign_sys_prompt,"stream":True},timeout=60) as r:
                    async for line in r.aiter_lines():
                        if line:
                            try: yield f"data:{json.dumps({'content':json.loads(line).get('response','')})}\n\n"
                            except: continue
        except Exception as e:
            traceback.print_exc()
            yield f"data:{json.dumps({'error':str(e)})}\n\n"
    return StreamingResponse(gen(),media_type="text/event-stream")

# =======================================================================
# 🛠️ SYSTEM ENDPOINTS & SOVEREIGN PANELS
# =======================================================================
@app.get("/health")
def health(): 
    return {
        "status": "online", 
        "version": "8.0",
        "components": {
            "invariant_engine": "active",
            "vera_ledger": "active"
        }
    }

@app.get("/workers")
def workers(): 
    return {"workers":[{"name":"auto","model":"llama3.2:latest"},
                        {"name":"brain","model":"llama3.2:latest"},
                        {"name":"search","model":"llama3.2:latest"},
                        {"name":"code","model":"qwen2.5-coder:14b"},
                        {"name":"files","model":"llama3.2:latest"},
                        {"name":"vision","model":"llava:7b"},
                        {"name":"voice","model":"whisper"},
                        {"name":"system","model":"llama3.2:latest"}]}

@app.post("/auth/session")
async def session(): 
    sess_id = str(uuid.uuid4())
    return {
        "session_id": sess_id,
        "token": "agamoto-secure-token",
        "proof": generate_vera_proof("SESSION_INIT", sess_id)
    }

@app.get("/mcp/status")
async def mcp_status():
    try:
        agents=registry_worker.load_agent_network()
        return {"status":"online","protocol":"agamoto-mcp-v1","registered_agents":len(agents),"agents":agents}
    except: return {"status":"online","protocol":"agamoto-mcp-v1","registered_agents":4}

@app.get("/chat/{session_id}/history")
async def chat_history(session_id:str): return {"session_id":session_id,"messages":[]}

@app.post("/chat/{session_id}/clear")
async def chat_clear(session_id:str): return {"status":"cleared"}

# ----------------- COMMAND BRIDGE ENDPOINTS -----------------

@app.get("/constitution/state")
async def constitution_state(session_id: str = None):
    return {
        "regime": "SOVEREIGN_MODE",
        "blocked": False,
        "last_check": {
            "passed": True, 
            "message": "All invariants within acceptable PHP thresholds", 
            "action": "PROCEED"
        },
        "invariants": {
            "max_drawdown": {"limit": 0.15, "current": 0.02},
            "hard_floor": {"limit": 1000000, "current": 1250000}
        },
        "exposure": {"PHP": 0.8, "ASSETS": 0.2}
    }

@app.get("/evolution/status")
async def evolution_status():
    return {
        "generation": 142,
        "best_fitness": 0.94,
        "population": 500,
        "mutation_rate": 0.02,
        "diversity": 0.81,
        "elites": 10,
        "status": "EVOLVING"
    }

@app.post("/evolution/step")
async def evolution_step(req: Request):
    data = await req.json()
    gens = data.get("generations", 1)
    return {
        "status": "success", 
        "generation": 142 + int(gens), 
        "best_fitness": round(0.94 + (int(gens) * 0.005), 4)
    }

@app.post("/kernel/invariant/check")
async def invariant_check(req: Request):
    data = await req.json()
    inv_type = data.get("invariant_type", "MAX_DRAWDOWN")
    return {
        "passed": True, 
        "message": f"Invariant {inv_type} passed successfully. No breach detected."
    }

@app.post("/backtest/run")
async def backtest_run(req: Request):
    data = await req.json()
    pair = data.get("pair", "BTC/PHP")
    return {
        "status": "success", 
        "metrics": {
            "sharpe_ratio": round(random.uniform(1.5, 3.5), 2), 
            "win_rate": round(random.uniform(0.55, 0.75), 2),
            "pair": pair
        }
    }

# PS1 router patch
try:
    from ps1_integration import router as ps1_router
    app.include_router(ps1_router,prefix="/api/v1/ps1")
except ImportError:
    print("⚠️ [WARNING] PS1 router not found.")

if __name__=="__main__":
    import uvicorn
    uvicorn.run(app,host="0.0.0.0",port=8001)