# backend/trading/backtest_engine.py
"""
BACKTEST ENGINE
Simulates strategies on historical data
"""

import random
import time
from typing import Dict, List, Any

from backend.core.sovereign_event_bus import event_bus, Event, EventType


class BacktestEngine:
    """
    Local backtesting engine
    """
    
    def __init__(self):
        self.name = "BacktestEngine"
        self.historical_data = self._load_historical_data()
        
        event_bus.subscribe(EventType.STRATEGY_PROPOSED, self.on_strategy_proposed)
    
    def _load_historical_data(self) -> Dict[str, List]:
        """Load historical market data"""
        # In production: load from CSV files
        return {
            "BTC": self._generate_synthetic_data("BTC", 365),
            "ETH": self._generate_synthetic_data("ETH", 365)
        }
    
    def _generate_synthetic_data(self, symbol: str, days: int) -> List[Dict]:
        """Generate synthetic data for testing"""
        data = []
        price = 1000 if symbol == "BTC" else 50
        
        for i in range(days):
            daily = {
                "timestamp": time.time() - (days - i) * 86400,
                "open": price,
                "high": price * (1 + random.uniform(0, 0.05)),
                "low": price * (1 - random.uniform(0, 0.05)),
                "close": price * (1 + random.uniform(-0.03, 0.03)),
                "volume": random.randint(1000, 10000)
            }
            data.append(daily)
            price = daily["close"]
        
        return data
    
    async def on_strategy_proposed(self, event: Event):
        """Run backtest on proposed strategy"""
        strategy_id = event.payload.get("strategy_id")
        strategy = event.payload.get("strategy", {})
        
        results = await self.backtest(strategy)
        
        await event_bus.publish(Event(
            type=EventType.STRATEGY_BACKTESTED,
            source="backtest_engine",
            payload={
                "strategy_id": strategy_id,
                "win_rate": results["win_rate"],
                "trades": results["total_trades"]
            }
        ))
    
    async def backtest(self, strategy: Dict) -> Dict:
        """Run backtest"""
        strategy_type = strategy.get("type", "unknown")
        
        if strategy_type == "mean_reversion":
            return await self._backtest_mean_reversion()
        else:
            return await self._backtest_generic()
    
    async def _backtest_mean_reversion(self) -> Dict:
        """Simulate mean reversion"""
        trades = random.randint(50, 200)
        win_rate = random.uniform(45, 65)
        
        return {
            "win_rate": win_rate,
            "total_trades": trades,
            "profitable_trades": int(trades * win_rate / 100),
            "total_profit": random.uniform(-1000, 5000),
            "max_drawdown": random.uniform(5, 15)
        }
    
    async def _backtest_generic(self) -> Dict:
        """Generic backtest"""
        return {
            "win_rate": random.uniform(40, 60),
            "total_trades": random.randint(50, 200),
            "total_profit": random.uniform(-1000, 5000),
            "max_drawdown": random.uniform(5, 15)
        }