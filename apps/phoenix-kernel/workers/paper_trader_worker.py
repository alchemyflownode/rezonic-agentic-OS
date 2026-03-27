# workers/paper_trader_worker.py
"""Paper Trading Worker - Simulated trading with portfolio tracking"""

import time
import random
import hashlib
from typing import Dict, Any
from base_worker import Worker


class PaperTraderWorker(Worker):
    """Paper trading simulation with portfolio management"""
    
    def __init__(self):
        super().__init__("paper_trader")
        self.balance = 1000000.0
        self.positions: Dict[str, float] = {}
        self.trade_history = []
        self.daily_pnl = 0.0
        self.total_trades = 0
    
    async def execute(self, task: str, **kwargs) -> Dict[str, Any]:
        """Execute trade command"""
        task_lower = task.lower()
        
        if "buy" in task_lower or kwargs.get("action") == "buy":
            return await self._buy(kwargs)
        elif "sell" in task_lower or kwargs.get("action") == "sell":
            return await self._sell(kwargs)
        elif "portfolio" in task_lower or task_lower == "/portfolio":
            return await self._portfolio()
        elif "reset" in task_lower:
            return await self._reset()
        else:
            return {"success": False, "error": "Unknown command", "worker": self.name}
    
    async def _buy(self, kwargs: Dict) -> Dict:
        """Execute buy order"""
        symbol = kwargs.get("symbol", "BTCUSDT")
        amount = float(kwargs.get("amount", 0))
        price = kwargs.get("price", 50000)
        
        if amount <= 0:
            return {"success": False, "error": "Amount must be positive", "worker": self.name}
        
        cost = amount * price
        if cost > self.balance:
            return {"success": False, "error": f"Insufficient balance: {self.balance:.2f}", "worker": self.name}
        
        self.balance -= cost
        self.positions[symbol] = self.positions.get(symbol, 0) + amount
        self.trade_history.append({
            "action": "BUY",
            "symbol": symbol,
            "amount": amount,
            "price": price,
            "timestamp": time.time()
        })
        self.total_trades += 1
        
        drift_lock = hashlib.sha256(f"{symbol}{amount}{price}{time.time()}".encode()).hexdigest()[:16]
        
        return {
            "success": True,
            "balance": self.balance,
            "position": self.positions[symbol],
            "cost": cost,
            "drift_lock": drift_lock,
            "worker": self.name
        }
    
    async def _sell(self, kwargs: Dict) -> Dict:
        """Execute sell order"""
        symbol = kwargs.get("symbol", "BTCUSDT")
        amount = float(kwargs.get("amount", 0))
        price = kwargs.get("price", 50000)
        
        if amount <= 0:
            return {"success": False, "error": "Amount must be positive", "worker": self.name}
        
        current_position = self.positions.get(symbol, 0)
        if amount > current_position:
            return {"success": False, "error": f"Insufficient {symbol}: {current_position}", "worker": self.name}
        
        revenue = amount * price
        self.balance += revenue
        self.positions[symbol] = current_position - amount
        
        # Calculate PnL if we had entry price tracking
        self.trade_history.append({
            "action": "SELL",
            "symbol": symbol,
            "amount": amount,
            "price": price,
            "timestamp": time.time()
        })
        self.total_trades += 1
        
        drift_lock = hashlib.sha256(f"{symbol}{amount}{price}{time.time()}".encode()).hexdigest()[:16]
        
        return {
            "success": True,
            "balance": self.balance,
            "position": self.positions.get(symbol, 0),
            "revenue": revenue,
            "drift_lock": drift_lock,
            "worker": self.name
        }
    
    async def _portfolio(self) -> Dict:
        """Get portfolio summary"""
        # Estimate current value (simplified)
        estimated_value = self.balance + sum([pos * 50000 for pos in self.positions.values()])
        
        # Calculate win rate
        wins = len([t for t in self.trade_history if t["action"] == "SELL"])
        win_rate = (wins / self.total_trades * 100) if self.total_trades > 0 else 0
        
        return {
            "success": True,
            "balance": self.balance,
            "positions": self.positions,
            "total_value": estimated_value,
            "trades": len(self.trade_history),
            "total_trades": self.total_trades,
            "win_rate": round(win_rate, 1),
            "daily_pnl": self.daily_pnl,
            "worker": self.name
        }
    
    async def _reset(self) -> Dict:
        """Reset portfolio"""
        self.balance = 1000000.0
        self.positions = {}
        self.trade_history = []
        self.daily_pnl = 0.0
        self.total_trades = 0
        
        return {
            "success": True,
            "message": "Portfolio reset to initial state",
            "balance": self.balance,
            "worker": self.name
        }