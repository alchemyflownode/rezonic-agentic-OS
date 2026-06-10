from .base import BaseWorker
from typing import Dict, Any

class PaperTrader(BaseWorker):
    def __init__(self, user_id: str, initial_balance: float = 1_000_000.0):
        super().__init__(name="paper_trader", user_id=user_id)
        self.balance = initial_balance
        self.positions: Dict[str, float] = {}
    
    async def execute(self, task: str, **kwargs) -> Dict[str, Any]:
        symbol = kwargs.get("symbol", "BTCUSDT")
        amount = float(kwargs.get("amount", 0.01))
        price = float(kwargs.get("price", 50000))
        
        if "buy" in task.lower():
            cost = amount * price
            if cost <= self.balance:
                self.balance -= cost
                self.positions[symbol] = self.positions.get(symbol, 0) + amount
                return {"success": True, "balance": self.balance, "action": "buy"}
            return {"success": False, "error": "Insufficient balance"}
        
        elif "sell" in task.lower():
            if self.positions.get(symbol, 0) >= amount:
                revenue = amount * price
                self.balance += revenue
                self.positions[symbol] -= amount
                return {"success": True, "balance": self.balance, "action": "sell"}
            return {"success": False, "error": f"Insufficient {symbol}"}
        
        return {"success": False, "error": "Unknown command"}