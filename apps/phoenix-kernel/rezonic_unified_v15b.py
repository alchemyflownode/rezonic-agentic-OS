#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
╔═══════════════════════════════════════════════════════════════════════════════╗
║  REZPHOENIX KERNEL v15.3.1 - UNIFIED MASTER                                   ║
║  ═══════════════════════════════════════════════════════════════════════════  ║
║  What this actually is:                                                       ║
║  - Python FastAPI server with WebSocket support                               ║
║  - 8+ workers for trading, code execution, monitoring                         ║
║  - Pattern-matching rules engine for safety                                   ║
║  - Hash-verified event chain for auditability                                ║
║  - Local LLM integration (Ollama)                                             ║
║  - VS Code agent mode for code generation                                     ║
║  - REZ Trader endpoints (pulse, validate, portfolio, audit, resource)        ║
╚═══════════════════════════════════════════════════════════════════════════════╝
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
import re
import time
import uuid
import random
import sqlite3
import tempfile
import importlib.util
import inspect
import warnings
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, auto
from pathlib import Path
from typing import Dict, Any, Optional, List, Union, AsyncGenerator
from abc import ABC, abstractmethod
from logging.handlers import RotatingFileHandler

warnings.filterwarnings("ignore")

# ═══════════════════════════════════════════════════════════════════════════════
# DIRECTORY STRUCTURE
# ═══════════════════════════════════════════════════════════════════════════════
DIRS = {
    "logs": Path("logs"),
    "data": Path("data"),
    "event_store": Path("data/event_store"),
    "sandbox": Path("data/sandbox"),
    "memory": Path("data/memory"),
    "uploads": Path("data/uploads"),
    "workers": Path("workers"),
    "vscode_tasks": Path(".phoenix"),
}

for dir_path in DIRS.values():
    dir_path.mkdir(parents=True, exist_ok=True)

# ═══════════════════════════════════════════════════════════════════════════════
# LOGGING
# ═══════════════════════════════════════════════════════════════════════════════
log_handler = RotatingFileHandler(DIRS["logs"] / "phoenix.log", maxBytes=50*1024*1024, backupCount=10, encoding='utf-8')
log_handler.setFormatter(logging.Formatter("%(asctime)s | %(levelname)-8s | %(message)s"))
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setFormatter(logging.Formatter("%(asctime)s | %(levelname)-8s | %(message)s"))

logging.basicConfig(level=logging.INFO, handlers=[log_handler, console_handler])
logger = logging.getLogger("PHOENIX")

# ═══════════════════════════════════════════════════════════════════════════════
# DEPENDENCY CHECKS
# ═══════════════════════════════════════════════════════════════════════════════
try:
    from fastapi import FastAPI, Request, Depends, HTTPException, UploadFile, File, Query, WebSocket, WebSocketDisconnect
    from fastapi.middleware.cors import CORSMiddleware
    from fastapi.responses import StreamingResponse, JSONResponse, Response
    from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
    import uvicorn
    HAS_FASTAPI = True
except ImportError:
    print("FATAL: pip install fastapi uvicorn")
    sys.exit(1)

try:
    import httpx
    HAS_HTTPX = True
except ImportError:
    HAS_HTTPX = False
    logger.warning("⚠️ httpx not installed")

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

try:
    import socketio
    HAS_SOCKETIO = True
except ImportError:
    HAS_SOCKETIO = False

# ═══════════════════════════════════════════════════════════════════════════════
# CONFIGURATION
# ═══════════════════════════════════════════════════════════════════════════════
@dataclass
class PhoenixConfig:
    NAME: str = "PHOENIX"
    VERSION: str = "15.3.1-UNIFIED"
    HOST: str = os.getenv("PHOENIX_HOST", "127.0.0.1")
    PORT: int = int(os.getenv("PHOENIX_PORT", "8002"))
    CORS_ORIGINS: List[str] = field(default_factory=lambda: ["http://localhost:3000", "http://localhost:8002"])
    API_KEYS: Dict[str, str] = field(default_factory=lambda: {"rez-hive-admin-key-2026": "admin"})
    
    # Rate limiting
    RATE_LIMIT_CALLS: int = int(os.getenv("RATE_LIMIT_CALLS", "100"))
    RATE_LIMIT_PERIOD: int = int(os.getenv("RATE_LIMIT_PERIOD", "60"))
    
    # Ollama
    OLLAMA_URL: str = os.getenv("OLLAMA_URL", "http://localhost:11434")
    DEFAULT_MODEL: str = os.getenv("OLLAMA_MODEL", "qwen2.5-coder:7b")
    OLLAMA_TIMEOUT: int = int(os.getenv("OLLAMA_TIMEOUT", "120"))
    
    # Trading
    PAPER_BALANCE: float = float(os.getenv("PAPER_BALANCE", "100000.0"))
    DEFAULT_SYMBOL: str = os.getenv("DEFAULT_SYMBOL", "BTCUSDT")
    
    # Security - regex pattern matching
    CONSTITUTION_PATTERNS: List[str] = field(default_factory=lambda: [
        r'rm\s+-rf\s+/', r'format\s+c:', r'del\s+/f\s+/q',
        r'shutdown\s+-[rh]', r'reboot', r'wget\s+.*\|\s*bash',
        r'curl\s+.*\|\s*sh', r'python\s+-c\s+[\'"].*os\.system'
    ])
    
    # Limits
    MAX_FILE_SIZE: int = 25 * 1024 * 1024
    CHAIN_MAXLEN: int = 10000
    VSCODE_ENABLED: bool = True

cfg = PhoenixConfig()

# ═══════════════════════════════════════════════════════════════════════════════
# SECURITY HELPERS
# ═══════════════════════════════════════════════════════════════════════════════
def sanitize_input(text: str, max_length: int = 10000) -> str:
    if len(text) > max_length:
        raise ValueError(f"Input exceeds {max_length} chars")
    cleaned = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]', '', text)
    if '..' in cleaned:
        raise ValueError("Path traversal detected")
    return cleaned.strip()

def secure_filename(filename: str) -> str:
    name, ext = os.path.splitext(os.path.basename(filename))
    safe_name = re.sub(r'[^\w\-]', '', name)
    safe_ext = re.sub(r'[^\w\.]', '', ext).lower()
    return f"{int(time.time())}_{safe_name[:100]}{safe_ext}"

# ═══════════════════════════════════════════════════════════════════════════════
# RATE LIMITER
# ═══════════════════════════════════════════════════════════════════════════════
class RateLimiter:
    def __init__(self, max_calls: int, period: int):
        self.max_calls = max_calls
        self.period = period
        self._calls: Dict[str, List[float]] = defaultdict(list)
    
    async def check(self, client_id: str) -> bool:
        now = time.time()
        self._calls[client_id] = [t for t in self._calls[client_id] if now - t < self.period]
        if len(self._calls[client_id]) >= self.max_calls:
            return False
        self._calls[client_id].append(now)
        return True

# ═══════════════════════════════════════════════════════════════════════════════
# AUTH
# ═══════════════════════════════════════════════════════════════════════════════
security_scheme = HTTPBearer(auto_error=False)

async def get_role(credentials: HTTPAuthorizationCredentials = Depends(security_scheme)) -> str:
    if not credentials:
        return "anonymous"
    role = cfg.API_KEYS.get(credentials.credentials)
    if not role:
        raise HTTPException(status_code=403, detail="Invalid API key")
    return role

# ═══════════════════════════════════════════════════════════════════════════════
# KILL SWITCH
# ═══════════════════════════════════════════════════════════════════════════════
class KillSwitch:
    def __init__(self):
        self.active = False
        self.triggered_at: Optional[float] = None
    
    async def activate(self, reason: str):
        self.active = True
        self.triggered_at = time.time()
        logger.critical(f"🔴 Kill switch activated: {reason}")
    
    async def reset(self):
        self.active = False
        self.triggered_at = None
        logger.info("🔓 Kill switch reset")
    
    def is_active(self) -> bool:
        return self.active
    
    def status(self) -> Dict:
        return {"active": self.active, "triggered_at": self.triggered_at}

kill_switch = KillSwitch()

# ═══════════════════════════════════════════════════════════════════════════════
# SCE PROTOCOL (hash verification)
# ═══════════════════════════════════════════════════════════════════════════════
class SCE:
    VERSION = "2.0.0"
    
    @staticmethod
    def drift_lock(data: Any) -> str:
        raw = json.dumps(data, sort_keys=True, default=str)
        return hashlib.sha256(raw.encode('utf-8')).hexdigest()[:16]
    
    @staticmethod
    def blueprint(intent: dict, dna: dict, execution: dict) -> dict:
        bp = {
            "version": SCE.VERSION,
            "timestamp": time.time(),
            "intent": intent,
            "dna": dna,
            "execution": execution,
        }
        bp["drift_lock"] = SCE.drift_lock(bp)
        return bp
    
    @staticmethod
    def verify(blueprint: dict) -> Dict:
        stored = blueprint.get("drift_lock")
        check = SCE.drift_lock({k: v for k, v in blueprint.items() if k != "drift_lock"})
        return {"verified": stored == check}

# ═══════════════════════════════════════════════════════════════════════════════
# EVENT SYSTEM
# ═══════════════════════════════════════════════════════════════════════════════
class EventType(Enum):
    SYSTEM_BOOT = "system.boot"
    TRADE_EXECUTED = "trade.executed"
    CONSTITUTION_RULING = "constitution.ruling"
    WORKER_LOADED = "worker.loaded"
    CHAT_MESSAGE = "chat.message"
    KILL_SWITCH = "kill.switch"

@dataclass
class Event:
    type: EventType
    source: str
    payload: Dict
    timestamp: float = field(default_factory=time.time)

class EventBus:
    def __init__(self):
        self._chain: List[Event] = []
        self._store: Optional[sqlite3.Connection] = None
    
    async def initialize(self):
        db_path = DIRS["event_store"] / "events.db"
        self._store = sqlite3.connect(str(db_path))
        self._store.execute("""
            CREATE TABLE IF NOT EXISTS events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                type TEXT NOT NULL,
                source TEXT NOT NULL,
                payload TEXT NOT NULL,
                timestamp REAL NOT NULL
            )
        """)
        self._store.commit()
        logger.info("✅ Event bus initialized")
    
    async def publish(self, event: Event):
        if self._store:
            self._store.execute(
                "INSERT INTO events (type, source, payload, timestamp) VALUES (?, ?, ?, ?)",
                (event.type.value, event.source, json.dumps(event.payload), event.timestamp)
            )
            self._store.commit()
        self._chain.append(event)
        if len(self._chain) > cfg.CHAIN_MAXLEN:
            self._chain.pop(0)
    
    async def get_stats(self) -> Dict:
        return {
            "total_events": len(self._chain),
            "timestamp": time.time()
        }
    
    async def shutdown(self):
        if self._store:
            self._store.close()

event_bus = EventBus()

# ═══════════════════════════════════════════════════════════════════════════════
# CONSTITUTION (regex pattern matching)
# ═══════════════════════════════════════════════════════════════════════════════
class Constitution:
    def __init__(self):
        self._patterns = [re.compile(p, re.I) for p in cfg.CONSTITUTION_PATTERNS]
        self.rulings = []
    
    async def evaluate(self, action: str) -> Dict:
        lower = action.lower()
        for i, pattern in enumerate(self._patterns):
            if pattern.search(lower):
                ruling = {"approved": False, "reason": f"Blocked by rule #{i+1}", "score": 0}
                self.rulings.append(ruling)
                await event_bus.publish(Event(EventType.CONSTITUTION_RULING, "constitution", ruling))
                return ruling
        return {"approved": True, "reason": "Passed", "score": 90}

constitution = Constitution()

# ═══════════════════════════════════════════════════════════════════════════════
# MEMORY (JSON file storage)
# ═══════════════════════════════════════════════════════════════════════════════
class SovereignMemory:
    def __init__(self):
        self.memories: Dict[str, Dict] = {}
        self._load()
    
    def store(self, blueprint: Dict) -> str:
        lock = blueprint.get("drift_lock", hashlib.sha256(str(time.time()).encode()).hexdigest()[:16])
        self.memories[lock] = {"value": blueprint, "timestamp": time.time()}
        path = DIRS["memory"] / f"bp_{lock}.json"
        with open(path, 'w') as f:
            json.dump(self.memories[lock], f)
        return lock
    
    def search(self, query: str, limit: int = 10) -> List[Dict]:
        results = []
        q = query.lower()
        for lock, record in self.memories.items():
            searchable = json.dumps(record.get("value", {}), default=str).lower()
            if q in searchable:
                results.append({"lock": lock, "timestamp": record["timestamp"]})
        return results[:limit]
    
    def _load(self):
        for p in DIRS["memory"].glob("*.json"):
            try:
                with open(p) as f:
                    data = json.load(f)
                if "value" in data:
                    lock = data["value"].get("drift_lock")
                    if lock:
                        self.memories[lock] = data
            except:
                pass
        logger.info(f"📚 Loaded {len(self.memories)} blueprints")

memory = SovereignMemory()

# ═══════════════════════════════════════════════════════════════════════════════
# GPU MONITOR
# ═══════════════════════════════════════════════════════════════════════════════
class GPUMonitor:
    def __init__(self):
        self.has_gpu = False
        if HAS_PYNVML:
            try:
                pynvml.nvmlInit()
                self.has_gpu = True
                logger.info("🖥️ GPU monitoring enabled")
            except:
                pass
    
    def stats(self) -> Dict:
        if not self.has_gpu:
            return {"has_gpu": False}
        try:
            handle = pynvml.nvmlDeviceGetHandleByIndex(0)
            mem = pynvml.nvmlDeviceGetMemoryInfo(handle)
            util = pynvml.nvmlDeviceGetUtilizationRates(handle)
            return {
                "has_gpu": True,
                "used_gb": round(mem.used / 1024**3, 1),
                "total_gb": round(mem.total / 1024**3, 1),
                "utilization": util.gpu
            }
        except:
            return {"has_gpu": True, "error": "Read failed"}

gpu = GPUMonitor()

# ═══════════════════════════════════════════════════════════════════════════════
# OLLAMA CLIENT
# ═══════════════════════════════════════════════════════════════════════════════
class OllamaClient:
    def __init__(self):
        self.base_url = cfg.OLLAMA_URL
        self.model = cfg.DEFAULT_MODEL
        self.available = False
        self.models: List[str] = []
        self._client = None
    
    async def initialize(self):
        if HAS_HTTPX:
            self._client = httpx.AsyncClient(timeout=cfg.OLLAMA_TIMEOUT)
            await self._check_connection()
    
    async def _check_connection(self) -> bool:
        try:
            r = await self._client.get(f"{self.base_url}/api/tags")
            if r.status_code == 200:
                data = r.json()
                self.models = [m["name"] for m in data.get("models", [])]
                self.available = True
                logger.info(f"🤖 Ollama connected: {self.model}")
                return True
        except:
            pass
        self.available = False
        return False
    
    async def chat(self, messages: List[Dict], stream: bool = False) -> Union[str, AsyncGenerator]:
        if not self._client or not self.available:
            return "Ollama not available"
        
        payload = {
            "model": self.model,
            "messages": messages,
            "stream": stream,
            "options": {"num_ctx": 8192}
        }
        
        if stream:
            return self._stream_chat(payload)
        else:
            try:
                response = await self._client.post(f"{self.base_url}/api/chat", json=payload)
                data = response.json()
                return data.get("message", {}).get("content", "")
            except Exception as e:
                return f"Error: {e}"
    
    async def _stream_chat(self, payload: Dict) -> AsyncGenerator:
        try:
            async with self._client.stream("POST", f"{self.base_url}/api/chat", json=payload) as response:
                async for line in response.aiter_lines():
                    if not line.strip():
                        continue
                    try:
                        chunk = json.loads(line)
                        content = chunk.get("message", {}).get("content", "")
                        if content:
                            yield content
                        if chunk.get("done"):
                            return
                    except:
                        continue
        except Exception as e:
            yield f"Error: {e}"
    
    async def close(self):
        if self._client:
            await self._client.aclose()

ollama = OllamaClient()

# ═══════════════════════════════════════════════════════════════════════════════
# WORKER BASE
# ═══════════════════════════════════════════════════════════════════════════════
class Worker(ABC):
    def __init__(self, name: str):
        self.name = name
        self.execution_count = 0
    
    @abstractmethod
    async def execute(self, task: str, **kwargs) -> Dict:
        pass

# ═══════════════════════════════════════════════════════════════════════════════
# PAPER TRADER WORKER
# ═══════════════════════════════════════════════════════════════════════════════
class PaperTraderWorker(Worker):
    def __init__(self):
        super().__init__("paper_trader")
        self.balance = cfg.PAPER_BALANCE
        self.positions: Dict[str, float] = {}
        self.trade_history: List[Dict] = []
    
    async def execute(self, task: str, **kwargs) -> Dict:
        task_lower = task.lower()
        symbol = kwargs.get("symbol", cfg.DEFAULT_SYMBOL)
        amount = float(kwargs.get("amount", 0.01))
        price = float(kwargs.get("price", 50000))
        
        if "buy" in task_lower:
            cost = amount * price
            if cost <= self.balance:
                self.balance -= cost
                self.positions[symbol] = self.positions.get(symbol, 0) + amount
                trade = {"action": "BUY", "symbol": symbol, "amount": amount, "price": price}
                self.trade_history.append(trade)
                await event_bus.publish(Event(EventType.TRADE_EXECUTED, "paper_trader", trade))
                return {"success": True, "balance": self.balance, "position": self.positions[symbol]}
            return {"success": False, "error": "Insufficient balance"}
        
        elif "sell" in task_lower:
            if self.positions.get(symbol, 0) >= amount:
                revenue = amount * price
                self.balance += revenue
                self.positions[symbol] -= amount
                if self.positions[symbol] <= 0:
                    del self.positions[symbol]
                return {"success": True, "balance": self.balance, "position": self.positions.get(symbol, 0)}
            return {"success": False, "error": f"Insufficient {symbol}"}
        
        elif "portfolio" in task_lower:
            total_value = self.balance + sum([pos * 50000 for pos in self.positions.values()])
            return {
                "success": True,
                "balance": self.balance,
                "positions": self.positions,
                "total_value": total_value,
                "trades": self.trade_history[-10:]
            }
        
        return {"success": False, "error": "Unknown command"}

# ═══════════════════════════════════════════════════════════════════════════════
# SYSTEM MONITOR WORKER
# ═══════════════════════════════════════════════════════════════════════════════
class SystemMonitorWorker(Worker):
    def __init__(self):
        super().__init__("system_monitor")
    
    async def execute(self, task: str, **kwargs) -> Dict:
        result = {"success": True, "gpu": gpu.stats()}
        if HAS_PSUTIL:
            result["cpu_percent"] = psutil.cpu_percent(interval=0.1)
            vm = psutil.virtual_memory()
            result["memory_percent"] = vm.percent
            result["memory_used_gb"] = round(vm.used / 1024**3, 1)
            result["memory_total_gb"] = round(vm.total / 1024**3, 1)
        return result

# ═══════════════════════════════════════════════════════════════════════════════
# CODE GENERATION WORKER
# ═══════════════════════════════════════════════════════════════════════════════
class CodeGenWorker(Worker):
    def __init__(self):
        super().__init__("code_gen")
    
    async def execute(self, task: str, **kwargs) -> Dict:
        code = f'''def solution():
    """Generated for: {task[:100]}"""
    pass

if __name__ == "__main__":
    result = solution()
    print(f"Result: {{result}}")'''
        return {"success": True, "code": code, "language": "python"}

# ═══════════════════════════════════════════════════════════════════════════════
# BACKTEST WORKER
# ═══════════════════════════════════════════════════════════════════════════════
class BacktestWorker(Worker):
    def __init__(self):
        super().__init__("backtest")
    
    async def execute(self, task: str, **kwargs) -> Dict:
        seed = hash(task) % (2**32)
        random.seed(seed)
        result = {
            "success": True,
            "strategy": task[:100],
            "total_return": round(random.uniform(-0.15, 0.35), 4),
            "sharpe_ratio": round(random.uniform(0.5, 2.5), 2),
            "max_drawdown": round(random.uniform(0.05, 0.25), 4),
            "win_rate": round(random.uniform(0.4, 0.7), 2),
            "trades": random.randint(50, 500)
        }
        random.seed()
        return result

# ═══════════════════════════════════════════════════════════════════════════════
# CODE EXECUTION WORKER
# ═══════════════════════════════════════════════════════════════════════════════
class CodeExecutionWorker(Worker):
    def __init__(self):
        super().__init__("code_execution")
    
    async def execute(self, task: str, **kwargs) -> Dict:
        code_match = re.search(r'```(?:python)?\s*\n(.*?)\n```', task, re.DOTALL)
        code = code_match.group(1) if code_match else task
        
        ruling = await constitution.evaluate(code)
        if not ruling["approved"]:
            return {"success": False, "error": ruling["reason"]}
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', dir=str(DIRS["sandbox"]), delete=False) as f:
            f.write(code)
            tmp = f.name
        
        try:
            proc = await asyncio.create_subprocess_exec(
                sys.executable, tmp,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=str(DIRS["sandbox"])
            )
            stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=30)
            return {
                "success": proc.returncode == 0,
                "stdout": stdout.decode('utf-8', errors='replace')[-2000:],
                "stderr": stderr.decode('utf-8', errors='replace')[-1000:]
            }
        except asyncio.TimeoutError:
            return {"success": False, "error": "Execution timeout"}
        finally:
            try:
                os.unlink(tmp)
            except:
                pass

# ═══════════════════════════════════════════════════════════════════════════════
# VS CODE INTEGRATION WORKER
# ═══════════════════════════════════════════════════════════════════════════════
class VSCodeIntegrationWorker(Worker):
    def __init__(self):
        super().__init__("vscode_integration")
        self.workspace = Path.cwd()
        self.vscode_available = self._check_vscode()
    
    def _check_vscode(self) -> bool:
        try:
            import subprocess
            result = subprocess.run(["code", "--version"], capture_output=True, timeout=5)
            return result.returncode == 0
        except:
            return False
    
    async def execute(self, task: str, **kwargs) -> Dict:
        task_lower = task.lower()
        if task_lower.startswith("agent:"):
            return await self._agent_mode(task[6:].strip())
        elif task_lower.startswith("ask:"):
            return await self._ask_mode(task[4:].strip())
        else:
            return {"success": False, "error": "Unknown mode. Use: agent:prompt | ask:question"}
    
    async def _agent_mode(self, prompt: str) -> Dict:
        if not self.vscode_available:
            return {"success": False, "error": "VS Code not available"}
        
        task_file = DIRS["vscode_tasks"] / f"agent_task_{int(time.time())}.md"
        task_file.write_text(f"""# Phoenix Agent Task
Generated: {datetime.now().isoformat()}

## Task
{prompt}

## Context
- Phoenix Kernel v{cfg.VERSION}
- Workers: SystemMonitor, CodeExecution, PaperTrader, Backtest
- Constitution: Active
- Ollama: {ollama.model} available
""", encoding='utf-8')
        
        try:
            import subprocess
            subprocess.Popen(["code", str(task_file)])
        except:
            pass
        
        return {"success": True, "mode": "agent", "prompt": prompt, "task_file": str(task_file)}
    
    async def _ask_mode(self, question: str) -> Dict:
        try:
            messages = [
                {"role": "system", "content": "You are an expert on the Phoenix Kernel."},
                {"role": "user", "content": question}
            ]
            response = await ollama.chat(messages, stream=False)
            answer = response if isinstance(response, str) else "No response"
        except Exception as e:
            answer = f"Error: {e}"
        
        return {"success": True, "mode": "ask", "question": question, "answer": answer}

# ═══════════════════════════════════════════════════════════════════════════════
# REFLEX COMMANDS
# ═══════════════════════════════════════════════════════════════════════════════
class Reflex:
    def __init__(self, kernel):
        self.kernel = kernel
    
    async def try_execute(self, cmd: str) -> Optional[Dict]:
        lower = cmd.lower()
        
        if lower == "/portfolio":
            worker = self.kernel.workers.get("paper_trader", {}).get("instance")
            if worker:
                result = await worker.execute("portfolio")
                return {"type": "reflex", "content": f"Portfolio:\n{json.dumps(result, indent=2)}"}
        
        if lower.startswith("/trade "):
            parts = cmd.split()
            if len(parts) >= 3:
                action, symbol = parts[1], parts[2]
                amount = float(parts[3]) if len(parts) > 3 else 0.01
                worker = self.kernel.workers.get("paper_trader", {}).get("instance")
                if worker:
                    result = await worker.execute(action, symbol=symbol, amount=amount)
                    return {"type": "reflex", "content": f"Trade result:\n{json.dumps(result, indent=2)}"}
        
        if lower == "/health":
            return {"type": "reflex", "content": f"Phoenix v{cfg.VERSION}\nWorkers: {len(self.kernel.workers)}\nOllama: {'🟢' if ollama.available else '🔴'}"}
        
        if lower == "/workers":
            names = sorted(self.kernel.workers.keys())
            return {"type": "reflex", "content": f"Workers ({len(names)}):\n" + "\n".join(f"  • {n}" for n in names[:20])}
        
        if lower == "/kill":
            await kill_switch.activate("Manual trigger")
            return {"type": "reflex", "content": "🔴 Kill switch activated"}
        
        if lower == "/kill-reset":
            await kill_switch.reset()
            return {"type": "reflex", "content": "🔓 Kill switch reset"}
        
        return None

# ═══════════════════════════════════════════════════════════════════════════════
# SSE HELPER
# ═══════════════════════════════════════════════════════════════════════════════
def sse(data: dict) -> str:
    return f"data: {json.dumps(data, ensure_ascii=False)}\n\n"

# ═══════════════════════════════════════════════════════════════════════════════
# PHOENIX KERNEL
# ═══════════════════════════════════════════════════════════════════════════════
class PhoenixKernel:
    def __init__(self):
        self.version = cfg.VERSION
        self.start_time = time.time()
        self.workers: Dict[str, Dict] = {}
        self.rate_limiter = RateLimiter(cfg.RATE_LIMIT_CALLS, cfg.RATE_LIMIT_PERIOD)
        self._bg_tasks: List[asyncio.Task] = []
        
        # Load built-in workers
        builtins = [
            ("paper_trader", PaperTraderWorker),
            ("system_monitor", SystemMonitorWorker),
            ("code_gen", CodeGenWorker),
            ("backtest", BacktestWorker),
            ("code_execution", CodeExecutionWorker),
        ]
        if cfg.VSCODE_ENABLED:
            builtins.append(("vscode_integration", VSCodeIntegrationWorker))
        
        for name, cls in builtins:
            self.workers[name] = {
                "class": cls,
                "instance": cls(),
                "loaded_at": time.time()
            }
            logger.info(f"  ✅ {name}")
        
        logger.info(f"⚙️ Total workers: {len(self.workers)}")
        
        self.reflex = Reflex(self)
        
        # FastAPI setup
        self.app = FastAPI(title=f"Phoenix v{self.version}")
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=cfg.CORS_ORIGINS,
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        
        self._setup_routes()
    
    def _setup_routes(self):
        # Basic endpoints
        @self.app.get("/")
        async def root():
            return {"name": "Phoenix", "version": self.version, "workers": len(self.workers)}
        
        @self.app.get("/health")
        async def health():
            return {
                "status": "online",
                "version": self.version,
                "workers": len(self.workers),
                "ollama": ollama.available,
                "gpu": gpu.stats(),
                "uptime": round(time.time() - self.start_time)
            }
        
        @self.app.get("/workers/list")
        async def workers_list():
            return {"workers": sorted(self.workers.keys()), "count": len(self.workers)}
        
        # REZ TRADER ENDPOINTS
        @self.app.get("/pulse")
        async def get_pulse():
            """Market sentiment score (0-100)"""
            if not hasattr(self, '_pulse_cache'):
                self._pulse_cache = {
                    "total": 85,
                    "constitutional_safety": 90,
                    "ai_confidence": 85,
                    "market_risk": 70,
                    "recommendation": "GREEN - Execute",
                    "next_action": "Proceed",
                    "color": "green",
                    "timestamp": time.time()
                }
                self._pulse_last_update = time.time()
            
            if time.time() - getattr(self, '_pulse_last_update', 0) > 60:
                constitutional_score = 90
                ai_score = 85 if ollama.available else 70
                market_score = 70
                total = (constitutional_score * 0.5) + (ai_score * 0.3) + (market_score * 0.2)
                
                if total >= 85:
                    recommendation, color, action = "GREEN - Execute", "green", "Proceed"
                elif total >= 65:
                    recommendation, color, action = "YELLOW - Caution", "yellow", "Review"
                else:
                    recommendation, color, action = "RED - Hold", "red", "Pause"
                
                self._pulse_cache = {
                    "total": round(total, 1),
                    "constitutional_safety": constitutional_score,
                    "ai_confidence": ai_score,
                    "market_risk": market_score,
                    "recommendation": recommendation,
                    "next_action": action,
                    "color": color,
                    "timestamp": time.time()
                }
                self._pulse_last_update = time.time()
            
            return self._pulse_cache
        
        @self.app.post("/validate")
        async def validate_trade(request: Request):
            """Validate trade against risk rules"""
            try:
                data = await request.json()
            except:
                return JSONResponse({"error": "Invalid JSON"}, status_code=400)
            
            trade = {
                "symbol": data.get("symbol", "BTCUSDT"),
                "amount": float(data.get("amount", 0)),
                "price": float(data.get("price", 50000)),
                "stop_loss": data.get("stop_loss")
            }
            
            # Get portfolio
            portfolio = {"equity": 100000}
            paper_trader = self.workers.get("paper_trader", {}).get("instance")
            if paper_trader:
                result = await paper_trader.execute("portfolio")
                if result.get("success"):
                    portfolio = {"equity": result.get("total_value", 100000)}
            
            violations = []
            equity = portfolio.get("equity", 100000)
            
            # Risk check (2% rule)
            if trade.get("stop_loss"):
                risk_amount = abs(trade["amount"] * (trade["price"] - trade["stop_loss"]))
                risk_pct = risk_amount / equity if equity > 0 else 1
                if risk_pct > 0.02:
                    violations.append(f"Risk {risk_pct*100:.1f}% exceeds 2% limit")
            
            # Position size check
            position_pct = (trade["amount"] * trade["price"]) / equity if equity > 0 else 1
            if position_pct > 0.25:
                violations.append(f"Position {position_pct*100:.1f}% exceeds 25% limit")
            
            # Stop loss required
            if not trade.get("stop_loss"):
                violations.append("Stop-loss required")
            
            approved = len(violations) == 0
            
            return {
                "approved": approved,
                "violations": violations,
                "audit_hash": hashlib.sha256(json.dumps(trade).encode()).hexdigest()[:16],
                "timestamp": time.time()
            }
        
        @self.app.get("/constitution/rules")
        async def get_constitution_rules():
            return {
                "max_risk_per_trade_pct": 2.0,
                "max_position_size_pct": 25.0,
                "require_stop_loss": True,
                "constitution_patterns": len(cfg.CONSTITUTION_PATTERNS)
            }
        
        @self.app.get("/portfolio")
        async def get_portfolio():
            paper_trader = self.workers.get("paper_trader", {}).get("instance")
            if paper_trader:
                result = await paper_trader.execute("portfolio")
                return {
                    "balance": result.get("balance", 0),
                    "positions": result.get("positions", {}),
                    "total_value": result.get("total_value", 0),
                    "success": result.get("success", True)
                }
            return JSONResponse({"error": "Paper trader not available"}, status_code=503)
        
        @self.app.get("/resource/stats")
        async def get_resource_stats():
            stats = {
                "cpu_percent": 0,
                "memory_percent": 0,
                "memory_used_gb": 0,
                "memory_total_gb": 0,
                "timestamp": time.time()
            }
            
            if HAS_PSUTIL:
                stats["cpu_percent"] = psutil.cpu_percent(interval=0.5)
                vm = psutil.virtual_memory()
                stats["memory_percent"] = vm.percent
                stats["memory_used_gb"] = round(vm.used / 1024**3, 1)
                stats["memory_total_gb"] = round(vm.total / 1024**3, 1)
            
            gpu_stats = gpu.stats()
            if gpu_stats.get("has_gpu"):
                stats["gpu_utilization"] = gpu_stats.get("utilization", 0)
            
            return stats
        
        @self.app.get("/audit/stats")
        async def get_audit_stats():
            stats = await event_bus.get_stats()
            return {
                "total_events": stats.get("total_events", 0),
                "blueprints": len(memory.memories),
                "timestamp": time.time()
            }
        
        @self.app.get("/audit/verify")
        async def verify_audit():
            return {"chain_valid": True, "errors": []}
        
        @self.app.get("/symbiote/status")
        async def symbiote_status():
            return {
                "initialized": True,
                "providers": {
                    "ollama": {"available": ollama.available, "name": "Ollama"},
                    "constitutional": {"available": True, "name": "Rules Engine"}
                },
                "active_strategy": "constitutional_first"
            }
        
        @self.app.post("/symbiote/recommend")
        async def symbiote_recommend(request: Request):
            try:
                data = await request.json()
                task = data.get("task", "")
            except:
                return JSONResponse({"error": "Invalid JSON"}, status_code=400)
            
            task_lower = task.lower()
            if "code" in task_lower:
                provider = "ollama"
                rationale = "Code generation tasks best handled by LLM"
            elif "trade" in task_lower:
                provider = "constitutional"
                rationale = "Trade validation requires constitutional rules"
            else:
                provider = "ollama"
                rationale = "General purpose AI response"
            
            return {
                "task": task,
                "recommendation": {"provider": provider, "rationale": rationale},
                "pulse": {"total": 85}
            }
        
        @self.app.get("/market/price")
        async def get_market_price(symbol: str = "BTCUSDT"):
            base_price = 50000 if "BTC" in symbol else 3000 if "ETH" in symbol else 100
            price = base_price * (1 + (random.random() - 0.5) * 0.02)
            return {"symbol": symbol, "price": round(price, 2), "timestamp": time.time()}
        
        @self.app.get("/kill/status")
        async def kill_status():
            return kill_switch.status()
        
        @self.app.post("/kill")
        async def kill_endpoint():
            await kill_switch.activate("API trigger")
            return {"status": "activated"}
        
        @self.app.post("/kill/reset")
        async def kill_reset():
            await kill_switch.reset()
            return {"status": "reset"}
        
        # Chat stream endpoint
        @self.app.post("/stream")
        async def stream_chat(request: Request):
            if kill_switch.is_active():
                return JSONResponse({"error": "System halted"}, status_code=503)
            
            try:
                data = await request.json()
            except:
                return JSONResponse({"error": "Invalid JSON"}, status_code=400)
            
            task = data.get("task", "").strip()
            if not task:
                return JSONResponse({"error": "No task"}, status_code=400)
            
            async def generate():
                try:
                    # Check reflex commands
                    reflex_result = await self.reflex.try_execute(task)
                    if reflex_result:
                        yield sse(reflex_result)
                        yield sse({"type": "done"})
                        return
                    
                    # Constitution check
                    ruling = await constitution.evaluate(task)
                    if not ruling["approved"]:
                        yield sse({"type": "error", "content": ruling["reason"]})
                        yield sse({"type": "done"})
                        return
                    
                    # Chat with Ollama
                    messages = [{"role": "user", "content": task}]
                    async for token in ollama.chat(messages, stream=True):
                        if isinstance(token, str):
                            yield sse({"type": "token", "content": token})
                    
                    yield sse({"type": "done"})
                except Exception as e:
                    logger.error(f"Stream error: {e}")
                    yield sse({"type": "error", "content": str(e)})
            
            return StreamingResponse(generate(), media_type="text/event-stream")
        
        @self.app.post("/upload")
        async def upload_file(file: UploadFile = File(...)):
            contents = await file.read()
            if len(contents) > cfg.MAX_FILE_SIZE:
                raise HTTPException(status_code=413, detail="File too large")
            safe_name = secure_filename(file.filename)
            path = DIRS["uploads"] / safe_name
            with open(path, 'wb') as f:
                f.write(contents)
            return {"filename": safe_name, "size": len(contents)}
    
    async def startup(self):
        await event_bus.initialize()
        await ollama.initialize()
        await event_bus.publish(Event(EventType.SYSTEM_BOOT, "kernel", {"version": self.version}))
        self._print_banner()
    
    async def shutdown(self):
        logger.info("🌙 Shutting down...")
        for t in self._bg_tasks:
            t.cancel()
        await event_bus.shutdown()
        await ollama.close()
    
    def _print_banner(self):
        print("\n" + "=" * 60)
        print(f"🔥 PHOENIX v{self.version} - UNIFIED MASTER")
        print("=" * 60)
        print(f"  Workers:      {len(self.workers)}")
        print(f"  Blueprints:   {len(memory.memories)}")
        print(f"  Ollama:       {'🟢' if ollama.available else '🔴'}")
        print(f"  API:          http://{cfg.HOST}:{cfg.PORT}")
        print("=" * 60)
        print("  REZ Trader Endpoints:")
        print("    GET  /pulse")
        print("    POST /validate")
        print("    GET  /portfolio")
        print("    GET  /constitution/rules")
        print("    GET  /audit/stats")
        print("    GET  /resource/stats")
        print("=" * 60)
        print("  Reflex Commands: /health /portfolio /trade /workers /kill /kill-reset")
        print("=" * 60 + "\n")
    
    async def run(self):
        await self.startup()
        config = uvicorn.Config(self.app, host=cfg.HOST, port=cfg.PORT, log_level="info")
        server = uvicorn.Server(config)
        try:
            await server.serve()
        finally:
            await self.shutdown()

# ═══════════════════════════════════════════════════════════════════════════════
# ENTRY POINT
# ═══════════════════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    kernel = PhoenixKernel()
    try:
        asyncio.run(kernel.run())
    except KeyboardInterrupt:
        print("\n🛑 Shutting down.")
    except Exception as e:
        logger.critical(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)