# workers/ai_trader_worker.py - Fixed version with absolute imports
import time
import random
import logging
from base_worker import Worker

logger = logging.getLogger(__name__)

class AiTraderWorker(Worker):
    """AI-powered trading worker"""
    
    def __init__(self):
        super().__init__("ai_trader_worker")
        self.trades = []
        self.analysis_cache = {}
    
    async def execute(self, task: str, **kwargs) -> dict:
        task_lower = task.lower()
        
        if "analyze" in task_lower:
            symbol = kwargs.get("symbol", task_lower.replace("analyze", "").strip())
            return await self._analyze(symbol)
        elif "trade" in task_lower:
            symbol = kwargs.get("symbol", "")
            action = kwargs.get("action", "buy")
            amount = kwargs.get("amount", 100)
            return await self._execute_trade(symbol, action, amount)
        elif "history" in task_lower:
            return {"trades": self.trades[-20:], "count": len(self.trades)}
        
        return {"error": f"Unknown task: {task}", "success": False}
    
    async def _analyze(self, symbol: str) -> dict:
        if not symbol:
            return {"error": "No symbol provided", "success": False}
        
        # Simulate AI analysis
        confidence = random.uniform(0.3, 0.9)
        recommendation = "buy" if confidence > 0.6 else "sell" if confidence > 0.4 else "hold"
        
        analysis = {
            "symbol": symbol,
            "confidence": confidence,
            "recommendation": recommendation,
            "timestamp": time.time(),
            "factors": {
                "momentum": random.uniform(-1, 1),
                "volatility": random.uniform(0.1, 0.5),
                "trend": random.choice(["bullish", "bearish", "neutral"])
            }
        }
        
        self.analysis_cache[symbol] = analysis
        return analysis
    
    async def _execute_trade(self, symbol: str, action: str, amount: float) -> dict:
        trade = {
            "id": len(self.trades) + 1,
            "symbol": symbol,
            "action": action,
            "amount": amount,
            "timestamp": time.time(),
            "status": "executed"
        }
        self.trades.append(trade)
        return trade
