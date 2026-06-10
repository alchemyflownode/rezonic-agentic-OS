# workers/trade_visualizer.py
"""Enhanced trading worker with real-time visualization"""

import asyncio
import json
import time
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from enum import Enum
import aiohttp
from websockets import serve, connect
import pandas as pd
import numpy as np

class TradeType(Enum):
    BUY = "buy"
    SELL = "sell"
    HOLD = "hold"

class TradeStatus(Enum):
    PENDING = "pending"
    CONSTITUTION_CHECK = "constitution_check"
    APPROVED = "approved"
    EXECUTED = "executed"
    BLOCKED = "blocked"
    FAILED = "failed"

@dataclass
class TradeDecision:
    """Complete AI trade decision with reasoning"""
    timestamp: datetime
    worker: str
    trade_type: TradeType
    symbol: str
    price: float
    quantity: float
    reasoning: str
    confidence: float
    risk_metrics: Dict[str, float]
    constitution_checks: List[Dict]
    status: TradeStatus
    tx_hash: Optional[str] = None
    error: Optional[str] = None

@dataclass
class WorkerActivity:
    """Real-time worker activity tracking"""
    worker_name: str
    last_action: datetime
    action_type: str
    reasoning: str
    trades_today: int
    win_rate: float
    current_pnl: float

class TradeVisualizerWorker:
    """
    Enhanced worker that streams AI trading decisions
    Like Binance trade feed + TradingView chart + AI reasoning
    """
    
    def __init__(self):
        self.name = "trade_visualizer"
        self.trade_stream: List[TradeDecision] = []
        self.active_workers: Dict[str, WorkerActivity] = {}
        self.paper_portfolio: Dict[str, Dict] = {}
        self.constitution_log: List[Dict] = []
        self.drift_chain: List[str] = []
        
        # WebSocket clients
        self.connected_clients = set()
        
        # Real-time metrics
        self.metrics = {
            "total_trades": 0,
            "approved_trades": 0,
            "blocked_trades": 0,
            "total_volume": 0,
            "total_pnl": 0,
            "winning_trades": 0,
            "losing_trades": 0
        }
    
    async def start_streaming(self, port: int = 8765):
        """Start WebSocket server for real-time trade streaming"""
        async def handler(websocket, path):
            self.connected_clients.add(websocket)
            try:
                async for message in websocket:
                    # Handle client commands
                    data = json.loads(message)
                    if data.get("command") == "subscribe":
                        await self._send_trade_history(websocket)
                    elif data.get("command") == "get_workers":
                        await self._send_worker_status(websocket)
                    elif data.get("command") == "get_constitution":
                        await self._send_constitution_status(websocket)
            finally:
                self.connected_clients.remove(websocket)
        
        async with serve(handler, "localhost", port):
            print(f"📡 Trade Visualizer streaming on ws://localhost:{port}")
            await asyncio.Future()  # run forever
    
    async def broadcast_trade(self, decision: TradeDecision):
        """Broadcast trade decision to all connected clients"""
        message = {
            "type": "trade",
            "data": {
                "timestamp": decision.timestamp.isoformat(),
                "worker": decision.worker,
                "action": decision.trade_type.value,
                "symbol": decision.symbol,
                "price": decision.price,
                "quantity": decision.quantity,
                "value": decision.price * decision.quantity,
                "reasoning": decision.reasoning,
                "confidence": decision.confidence,
                "risk_metrics": decision.risk_metrics,
                "status": decision.status.value,
                "tx_hash": decision.tx_hash
            }
        }
        
        self.trade_stream.append(decision)
        
        # Send to all connected clients
        for client in self.connected_clients:
            try:
                await client.send(json.dumps(message))
            except:
                pass
        
        # Also log to file for paper trading audit
        self._log_paper_trade(decision)
    
    async def process_ai_decision(self, worker: str, signal: Dict) -> TradeDecision:
        """
        Process AI trade decision with full reasoning
        Returns: TradeDecision with all context
        """
        # Step 1: AI Reasoning
        reasoning = self._generate_ai_reasoning(worker, signal)
        
        # Step 2: Calculate risk metrics
        risk_metrics = await self._calculate_risk_metrics(signal)
        
        # Step 3: Constitutional check (SCE enforcement)
        constitution_checks, is_allowed = await self._constitutional_check(signal, risk_metrics)
        
        # Step 4: Create decision
        decision = TradeDecision(
            timestamp=datetime.now(),
            worker=worker,
            trade_type=TradeType.BUY if signal.get("action") == "buy" else TradeType.SELL,
            symbol=signal.get("symbol", "BTC/PHP"),
            price=signal.get("price", 0),
            quantity=signal.get("quantity", 0),
            reasoning=reasoning,
            confidence=signal.get("confidence", 0.5),
            risk_metrics=risk_metrics,
            constitution_checks=constitution_checks,
            status=TradeStatus.PENDING
        )
        
        # Step 5: Broadcast reasoning immediately
        await self.broadcast_reasoning(decision)
        
        # Step 6: Check constitution
        decision.status = TradeStatus.CONSTITUTION_CHECK
        await self.broadcast_trade(decision)
        
        if not is_allowed:
            decision.status = TradeStatus.BLOCKED
            decision.error = "Constitution violation"
            await self.broadcast_trade(decision)
            return decision
        
        # Step 7: Execute trade (or paper trade)
        decision.status = TradeStatus.APPROVED
        await self.broadcast_trade(decision)
        
        execution_result = await self._execute_paper_trade(decision)
        decision.status = TradeStatus.EXECUTED if execution_result["success"] else TradeStatus.FAILED
        decision.tx_hash = execution_result.get("tx_hash")
        
        # Step 8: Final broadcast
        await self.broadcast_trade(decision)
        
        # Update metrics
        self.metrics["total_trades"] += 1
        if decision.status == TradeStatus.EXECUTED:
            self.metrics["approved_trades"] += 1
            self.metrics["total_volume"] += decision.price * decision.quantity
        
        return decision
    
    def _generate_ai_reasoning(self, worker: str, signal: Dict) -> str:
        """Generate human-readable AI reasoning"""
        reasons = []
        
        # Technical analysis
        if signal.get("rsi"):
            reasons.append(f"RSI={signal['rsi']:.1f} ({'oversold' if signal['rsi'] < 30 else 'overbought' if signal['rsi'] > 70 else 'neutral'})")
        
        if signal.get("macd"):
            reasons.append(f"MACD crossover detected (signal: {signal['macd']['signal']})")
        
        if signal.get("volume"):
            reasons.append(f"Volume {signal['volume']:.0f} ({signal.get('volume_ratio', 1):.1f}x avg)")
        
        if signal.get("trend"):
            reasons.append(f"Trend: {signal['trend']} (strength: {signal.get('trend_strength', 0):.1f})")
        
        # Worker-specific reasoning
        if worker == "MomentumWorker":
            reasons.append(f"Momentum score: {signal.get('momentum', 0):.2f}")
            reasons.append("Breakout detected above resistance")
        elif worker == "ReversionWorker":
            reasons.append(f"Z-score: {signal.get('z_score', 0):.2f}")
            reasons.append("Mean reversion opportunity")
        elif worker == "ScalpingWorker":
            reasons.append(f"Spread: {signal.get('spread', 0):.2f}%")
            reasons.append("Quick profit opportunity")
        
        return f"{worker}: " + " | ".join(reasons)
    
    async def _constitutional_check(self, signal: Dict, risk_metrics: Dict) -> tuple[List[Dict], bool]:
        """Check all constitutional invariants"""
        checks = []
        is_allowed = True
        
        # Invariant 1: Max Drawdown
        if risk_metrics.get("projected_drawdown", 0) > 0.15:
            checks.append({
                "invariant": "MAX_DRAWDOWN",
                "limit": 0.15,
                "value": risk_metrics["projected_drawdown"],
                "result": "BLOCKED"
            })
            is_allowed = False
        else:
            checks.append({
                "invariant": "MAX_DRAWDOWN",
                "limit": 0.15,
                "value": risk_metrics.get("projected_drawdown", 0),
                "result": "PASSED"
            })
        
        # Invariant 2: Position Size
        position_size = signal.get("quantity", 0) * signal.get("price", 0)
        portfolio_value = self.paper_portfolio.get("value", 1_245_678)
        if position_size / portfolio_value > 0.10:
            checks.append({
                "invariant": "MAX_POSITION",
                "limit": 0.10,
                "value": position_size / portfolio_value,
                "result": "BLOCKED"
            })
            is_allowed = False
        else:
            checks.append({
                "invariant": "MAX_POSITION",
                "limit": 0.10,
                "value": position_size / portfolio_value,
                "result": "PASSED"
            })
        
        # Log to constitution
        self.constitution_log.append({
            "timestamp": datetime.now(),
            "checks": checks,
            "allowed": is_allowed
        })
        
        return checks, is_allowed
    
    async def _calculate_risk_metrics(self, signal: Dict) -> Dict:
        """Calculate real-time risk metrics"""
        # Simulate portfolio impact
        position_value = signal.get("quantity", 0) * signal.get("price", 0)
        portfolio_value = self.paper_portfolio.get("value", 1_245_678)
        
        return {
            "position_pct": position_value / portfolio_value if portfolio_value > 0 else 0,
            "projected_drawdown": position_value / portfolio_value * signal.get("stop_loss", 0.05),
            "risk_reward_ratio": signal.get("target", 0.02) / signal.get("stop_loss", 0.01) if signal.get("stop_loss") else 0,
            "volatility_impact": signal.get("volatility", 0) * 0.1,
            "correlation_risk": signal.get("correlation", 0) * 0.2
        }
    
    async def _execute_paper_trade(self, decision: TradeDecision) -> Dict:
        """Execute paper trade for simulation"""
        # This mimics Binance order execution
        await asyncio.sleep(0.1)  # Simulate order book latency
        
        value = decision.price * decision.quantity
        
        if decision.trade_type == TradeType.BUY:
            # Update portfolio
            if decision.symbol not in self.paper_portfolio:
                self.paper_portfolio[decision.symbol] = {
                    "quantity": 0,
                    "avg_price": 0,
                    "current_value": 0
                }
            
            position = self.paper_portfolio[decision.symbol]
            old_value = position["quantity"] * position["avg_price"]
            new_value = value
            total_quantity = position["quantity"] + decision.quantity
            
            position["avg_price"] = (old_value + new_value) / total_quantity if total_quantity > 0 else 0
            position["quantity"] = total_quantity
            position["current_value"] = position["quantity"] * decision.price
            
            self.paper_portfolio["value"] = self.paper_portfolio.get("value", 1_245_678) - value
            self.paper_portfolio["cash"] = self.paper_portfolio.get("cash", 1_245_678) - value
            
        else:  # SELL
            position = self.paper_portfolio.get(decision.symbol, {"quantity": 0, "avg_price": 0})
            if position["quantity"] >= decision.quantity:
                pnl = (decision.price - position["avg_price"]) * decision.quantity
                self.metrics["total_pnl"] += pnl
                if pnl > 0:
                    self.metrics["winning_trades"] += 1
                else:
                    self.metrics["losing_trades"] += 1
                
                position["quantity"] -= decision.quantity
                position["current_value"] = position["quantity"] * decision.price
                
                self.paper_portfolio["value"] = self.paper_portfolio.get("value", 1_245_678) + value
                self.paper_portfolio["cash"] = self.paper_portfolio.get("cash", 0) + value
        
        return {
            "success": True,
            "tx_hash": f"0x{hash(str(decision.timestamp)):x}",
            "value": value
        }
    
    async def broadcast_reasoning(self, decision: TradeDecision):
        """Broadcast AI reasoning in real-time"""
        message = {
            "type": "reasoning",
            "data": {
                "worker": decision.worker,
                "reasoning": decision.reasoning,
                "confidence": decision.confidence,
                "risk_metrics": decision.risk_metrics,
                "timestamp": decision.timestamp.isoformat()
            }
        }
        
        for client in self.connected_clients:
            try:
                await client.send(json.dumps(message))
            except:
                pass
    
    async def _send_trade_history(self, websocket):
        """Send trade history to new client"""
        for trade in self.trade_stream[-100:]:  # Last 100 trades
            message = {
                "type": "trade_history",
                "data": {
                    "timestamp": trade.timestamp.isoformat(),
                    "worker": trade.worker,
                    "action": trade.trade_type.value,
                    "symbol": trade.symbol,
                    "price": trade.price,
                    "quantity": trade.quantity,
                    "reasoning": trade.reasoning,
                    "status": trade.status.value
                }
            }
            await websocket.send(json.dumps(message))
    
    async def _send_worker_status(self, websocket):
        """Send worker status"""
        message = {
            "type": "workers",
            "data": {
                "active_workers": len(self.active_workers),
                "workers": [
                    {
                        "name": name,
                        "last_action": activity.last_action.isoformat(),
                        "trades_today": activity.trades_today,
                        "win_rate": activity.win_rate,
                        "pnl": activity.current_pnl
                    }
                    for name, activity in self.active_workers.items()
                ]
            }
        }
        await websocket.send(json.dumps(message))
    
    async def _send_constitution_status(self, websocket):
        """Send constitution status"""
        message = {
            "type": "constitution",
            "data": {
                "drift_chain": self.drift_chain[-10:],
                "recent_checks": self.constitution_log[-20:],
                "metrics": self.metrics,
                "portfolio": self.paper_portfolio
            }
        }
        await websocket.send(json.dumps(message))
    
    def _log_paper_trade(self, decision: TradeDecision):
        """Log paper trade for audit"""
        log_entry = {
            "timestamp": decision.timestamp.isoformat(),
            "worker": decision.worker,
            "action": decision.trade_type.value,
            "symbol": decision.symbol,
            "price": decision.price,
            "quantity": decision.quantity,
            "value": decision.price * decision.quantity,
            "reasoning": decision.reasoning,
            "status": decision.status.value,
            "constitution_checks": decision.constitution_checks
        }
        
        # Append to paper trading log file
        with open(f"paper_trades_{datetime.now().strftime('%Y%m%d')}.json", "a") as f:
            f.write(json.dumps(log_entry) + "\n")

# ============================================================================
# TradingView-Style Chart Integration
# ============================================================================

class TradingViewIntegration:
    """Generate TradingView-compatible chart data"""
    
    def __init__(self, trade_visualizer: TradeVisualizerWorker):
        self.visualizer = trade_visualizer
        self.candles = []
        self.trade_markers = []
    
    def add_candle(self, timestamp: datetime, open: float, high: float, low: float, close: float, volume: float):
        """Add candlestick data"""
        self.candles.append({
            "time": int(timestamp.timestamp()),
            "open": open,
            "high": high,
            "low": low,
            "close": close,
            "volume": volume
        })
    
    def add_trade_marker(self, trade: TradeDecision):
        """Add trade marker to chart"""
        marker = {
            "time": int(trade.timestamp.timestamp()),
            "price": trade.price,
            "type": trade.trade_type.value,
            "text": f"{trade.worker}: {trade.reasoning[:50]}...",
            "worker": trade.worker,
            "status": trade.status.value
        }
        self.trade_markers.append(marker)
    
    def get_chart_data(self) -> Dict:
        """Get chart data in TradingView format"""
        return {
            "candles": self.candles,
            "markers": self.trade_markers,
            "workers": self.visualizer.active_workers,
            "metrics": self.visualizer.metrics
        }