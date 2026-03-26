# mock_trader.py - FIXED
from typing import Dict, Any, List, Optional
import asyncio
import random
import logging

logger = logging.getLogger("PHOENIX_ULTIMATE")

class MockTraderWorker:
    """Mock trading worker for testing and simulation"""
    
    def __init__(self):
        self.name = "MockTraderWorker"
        self.trades = []
        self.balance = 10000.0
        self.positions = {}
        logger.info(f"✅ {self.name} initialized")
    
    async def execute(self, action: str, params: Dict = None) -> Dict[str, Any]:
        """Execute mock trading actions"""
        
        params = params or {}
        result = {
            "timestamp": asyncio.get_event_loop().time(),
            "action": action,
            "status": "success"
        }
        
        if action == "buy":
            symbol = params.get('symbol', 'BTC')
            amount = params.get('amount', 0.1)
            price = random.uniform(40000, 50000)
            
            if symbol not in self.positions:
                self.positions[symbol] = 0
            self.positions[symbol] += amount
            self.balance -= amount * price
            
            result.update({
                "symbol": symbol,
                "amount": amount,
                "price": price,
                "total": amount * price,
                "new_balance": self.balance
            })
            
        elif action == "sell":
            symbol = params.get('symbol', 'BTC')
            amount = min(params.get('amount', 0.1), self.positions.get(symbol, 0))
            price = random.uniform(40000, 50000)
            
            self.positions[symbol] -= amount
            self.balance += amount * price
            
            result.update({
                "symbol": symbol,
                "amount": amount,
                "price": price,
                "total": amount * price,
                "new_balance": self.balance
            })
        
        self.trades.append(result)
        
        return {
            "worker": self.name,
            "result": result,
            "balance": self.balance,
            "positions": self.positions,
            "trade_count": len(self.trades)
        }
    
    async def get_portfolio(self) -> Dict:
        return {
            "balance": self.balance,
            "positions": self.positions,
            "total_trades": len(self.trades),
            "estimated_value": self.balance + sum(
                self.positions.get(sym, 0) * random.uniform(40000, 50000) 
                for sym in self.positions
            )
        }
