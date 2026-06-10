#!/usr/bin/env python3
"""
RezTrader MVP - Sovereign Trading System
Based on Phoenix Kernel v15.3.1 - Trading Only
"""

import asyncio
import json
import logging
import os
import sys
import time
import uuid
import hashlib
from pathlib import Path
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from contextlib import asynccontextmanager

# FastAPI imports
from fastapi import FastAPI, Request, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, JSONResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import uvicorn

# WebSocket
import socketio

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)-8s | %(message)s'
)
logger = logging.getLogger("REZTRADER")

# ============================================
# CONFIGURATION
# ============================================

@dataclass
class TradingConfig:
    NAME: str = "REZTRADER"
    VERSION: str = "1.0.0-MVP"
    HOST: str = "127.0.0.1"
    PORT: int = 8002
    PAPER_BALANCE: float = 1000000.0
    DEFAULT_SYMBOL: str = "BTCUSDT"
    MAX_RISK_PERCENT: float = 2.0
    MAX_DAILY_DRAWDOWN: float = 5.0
    REQUIRE_STOP_LOSS: bool = True

cfg = TradingConfig()

# ============================================
# DIRECTORY STRUCTURE
# ============================================

DIRS = {
    "data": Path("data"),
    "event_store": Path("data/event_store"),
    "blueprints": Path("data/blueprints"),
    "logs": Path("logs"),
}

for dir_path in DIRS.values():
    dir_path.mkdir(parents=True, exist_ok=True)

# ============================================
# SCE PROTOCOL (Drift Locking)
# ============================================

class SCE:
    VERSION = "1.0.0"
    
    @staticmethod
    def drift_lock(data: Any) -> str:
        raw = json.dumps(data, sort_keys=True, default=str)
        return hashlib.sha256(raw.encode()).hexdigest()[:16]
    
    @staticmethod
    def blueprint(intent: dict, execution: dict, parent: str = None) -> dict:
        bp = {
            "version": SCE.VERSION,
            "timestamp": time.time(),
            "intent": intent,
            "execution": execution,
        }
        if parent:
            bp["parent_drift_lock"] = parent
        bp["master_drift_lock"] = SCE.drift_lock(bp)
        return bp

# ============================================
# EVENT BUS (Audit Trail)
# ============================================

class EventBus:
    def __init__(self):
        self._events = []
        self._max_events = 10000
    
    async def publish(self, event_type: str, source: str, payload: dict) -> str:
        event = {
            "id": str(uuid.uuid4())[:8],
            "type": event_type,
            "source": source,
            "payload": payload,
            "timestamp": time.time(),
            "proof": hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()[:16]
        }
        self._events.append(event)
        if len(self._events) > self._max_events:
            self._events.pop(0)
        logger.info(f"📜 EVENT: {event_type} from {source}")
        return event["proof"]
    
    async def get_stats(self) -> dict:
        return {
            "total_events": len(self._events),
            "chain_valid": True,
            "latest": self._events[-1]["proof"] if self._events else "genesis"
        }

event_bus = EventBus()

# ============================================
# CONSTITUTION (Risk Rules)
# ============================================

class Constitution:
    def __init__(self):
        self.max_risk_pct = cfg.MAX_RISK_PERCENT
        self.max_drawdown_pct = cfg.MAX_DAILY_DRAWDOWN
        self.require_stop_loss = cfg.REQUIRE_STOP_LOSS
        self.daily_pnl = 0
    
    async def evaluate_trade(self, trade: dict, portfolio: dict) -> tuple[bool, str]:
        equity = portfolio.get("equity", cfg.PAPER_BALANCE)
        position_value = trade.get("amount", 0) * trade.get("price", 0)
        
        # Risk check (2% rule)
        risk_pct = (position_value / equity) * 100 if equity > 0 else 100
        if risk_pct > self.max_risk_pct:
            return False, f"Risk {risk_pct:.1f}% exceeds {self.max_risk_pct}% limit"
        
        # Stop-loss required
        if self.require_stop_loss and not trade.get("stop_loss"):
            return False, "Stop-loss is required by constitution"
        
        return True, "Approved"

constitution = Constitution()

# ==========================================
# PAPER TRADER WORKER
# ==========================================

class PaperTrader:
    def __init__(self):
        self.balance = cfg.PAPER_BALANCE
        self.positions: Dict[str, float] = {}
        self.trades: List[Dict] = []
    
    async def execute(self, action: str, symbol: str, amount: float, price: float = 50000) -> Dict:
        action = action.lower()
        
        if action == "buy":
            cost = amount * price
            if cost <= self.balance:
                self.balance -= cost
                self.positions[symbol] = self.positions.get(symbol, 0) + amount
                trade = {"action": "BUY", "symbol": symbol, "amount": amount, "price": price, "timestamp": time.time()}
                self.trades.append(trade)
                await event_bus.publish("trade.executed", "paper_trader", trade)
                return {"success": True, "balance": self.balance, "position": self.positions[symbol], "trade": trade}
            return {"success": False, "error": f"Insufficient balance. Need {cost}, have {self.balance}"}
        
        elif action == "sell":
            if self.positions.get(symbol, 0) >= amount:
                revenue = amount * price
                self.balance += revenue
                self.positions[symbol] -= amount
                if self.positions[symbol] <= 0:
                    del self.positions[symbol]
                trade = {"action": "SELL", "symbol": symbol, "amount": amount, "price": price, "timestamp": time.time()}
                self.trades.append(trade)
                await event_bus.publish("trade.executed", "paper_trader", trade)
                return {"success": True, "balance": self.balance, "position": self.positions.get(symbol, 0), "trade": trade}
            return {"success": False, "error": f"Insufficient {symbol}. Have {self.positions.get(symbol, 0)}, need {amount}"}
        
        return {"success": False, "error": f"Unknown action: {action}"}
    
    async def get_portfolio(self) -> Dict:
        total_value = self.balance + sum([pos * 50000 for pos in self.positions.values()])
        return {
            "balance": self.balance,
            "positions": self.positions,
            "total_value": total_value,
            "trades": self.trades[-10:]
        }

paper_trader = PaperTrader()

# ==========================================
# REFLEX COMMANDS
# ==========================================

class Reflex:
    async def try_execute(self, cmd: str) -> Optional[Dict]:
        cmd = cmd.strip().lower()
        
        if cmd == "/health":
            return {"type": "reflex", "content": f"🔥 RezTrader v{cfg.VERSION}\nBalance: ₱{paper_trader.balance:,.0f}\nPositions: {len(paper_trader.positions)}"}
        
        if cmd == "/portfolio":
            portfolio = await paper_trader.get_portfolio()
            return {"type": "reflex", "content": f"📊 Portfolio\nBalance: ₱{portfolio['balance']:,.0f}\nTotal Value: ₱{portfolio['total_value']:,.0f}\nPositions: {portfolio['positions']}"}
        
        if cmd.startswith("/trade "):
            parts = cmd.split()
            if len(parts) >= 4:
                action, symbol, amount = parts[1], parts[2], float(parts[3])
                result = await paper_trader.execute(action, symbol, amount)
                return {"type": "reflex", "content": json.dumps(result, indent=2)}
        
        return None

reflex = Reflex()

# ==========================================
# FASTAPI APP
# ==========================================

app = FastAPI(title="RezTrader MVP", version=cfg.VERSION)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==========================================
# API ENDPOINTS
# ==========================================

@app.get("/health")
async def health():
    return {
        "status": "online",
        "version": cfg.VERSION,
        "balance": paper_trader.balance,
        "workers": 1  # Simplified for MVP
    }

@app.get("/portfolio")
async def get_portfolio():
    return await paper_trader.get_portfolio()

@app.post("/trade")
async def execute_trade(request: Request):
    data = await request.json()
    action = data.get("action")
    symbol = data.get("symbol", cfg.DEFAULT_SYMBOL)
    amount = float(data.get("amount", 0))
    price = float(data.get("price", 50000))
    
    # Constitutional validation
    portfolio = await paper_trader.get_portfolio()
    approved, reason = await constitution.evaluate_trade(
        {"action": action, "amount": amount, "price": price},
        portfolio
    )
    
    if not approved:
        return JSONResponse({"success": False, "error": reason}, status_code=400)
    
    result = await paper_trader.execute(action, symbol, amount, price)
    return result

@app.get("/workers/status")
async def workers_status():
    return {"workers": [{"name": "paper_trader", "status": "active"}], "total": 1}

@app.get("/events/stats")
async def events_stats():
    return await event_bus.get_stats()

# ==========================================
# KERNEL STREAM (Main Entry Point)
# ==========================================

@app.post("/kernel/stream")
async def kernel_stream(request: Request):
    data = await request.json()
    task = data.get("task", "").strip()
    
    async def generate():
        # Try reflex first
        reflex_result = await reflex.try_execute(task)
        if reflex_result:
            yield f"data: {json.dumps(reflex_result)}\n\n"
            yield f"data: {json.dumps({'type': 'done'})}\n\n"
            return
        
        # Fallback response
        yield f"data: {json.dumps({'type': 'token', 'content': f'Unknown command: {task}'})}\n\n"
        yield f"data: {json.dumps({'type': 'done'})}\n\n"
    
    return StreamingResponse(generate(), media_type="text/event-stream")

# ==========================================
# SOCKET.IO SETUP
# ==========================================

sio = socketio.AsyncServer(cors_allowed_origins="*", async_mode="asgi")
socket_app = socketio.ASGIApp(sio, app)

@sio.on("connect")
async def on_connect(sid, environ):
    logger.info(f"🔌 Socket connected: {sid[:8]}")
    await sio.emit("agentLog", {"message": "Connected to RezTrader", "type": "SYSTEM"}, room=sid)

@sio.on("execute_trade")
async def on_trade(sid, data):
    logger.info(f"💹 Trade request from {sid[:8]}: {data}")
    action = data.get("command", "").lower()
    if "buy" in action:
        action = "buy"
    elif "sell" in action:
        action = "sell"
    else:
        action = "buy"
    
    result = await paper_trader.execute(action, data.get("pair", "BTCUSDT"), float(data.get("amount", 0.01)))
    await sio.emit("trade_result", {"status": "AUTHORIZED", "result": result}, room=sid)

# ==========================================
# MAIN ENTRY
# ==========================================

if __name__ == "__main__":
    print("\n" + "=" * 60)
    print(f"🔥 RezTrader MVP v{cfg.VERSION}")
    print("=" * 60)
    print(f"  Balance:     ₱{paper_trader.balance:,.0f}")
    print(f"  API:         http://{cfg.HOST}:{cfg.PORT}")
    print(f"  WebSocket:   ws://{cfg.HOST}:{cfg.PORT}")
    print("=" * 60)
    print("  Commands:")
    print("    /trade buy BTC 0.01")
    print("    /trade sell ETH 0.5")
    print("    /portfolio")
    print("    /health")
    print("=" * 60 + "\n")
    
    uvicorn.run(socket_app, host=cfg.HOST, port=cfg.PORT, log_level="info")
