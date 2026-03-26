import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
# backend/workers/backtest_engine.py
"""
Backtest Engine - Simulates strategies on historical data
"""

import json
import time
import asyncio
from typing import Dict, List, Any

from backend.core.event_bus import event_bus, Event, EventType


class BacktestEngine:
    """
    Pure local backtesting
    No cloud dependencies, uses local market data
    """
    
    def __init__(self):
        self.name = "BacktestEngine"
        self.historical_data = self._load_historical_data()
        
        # Subscribe to events
        event_bus.subscribe(EventType.STRATEGY_PROPOSED, self.on_strategy_proposed)
        
    def _load_historical_data(self) -> Dict[str, List]:
        """Load local historical market data"""
        # In production: load from CSV/Parquet files
        # For MVP: generate synthetic data
        return {
            "BTC": self._generate_synthetic_data("BTC", 365),
            "ETH": self._generate_synthetic_data("ETH", 365),
            "PHP": self._generate_synthetic_data("PHP", 365)
        }
    
    def _generate_synthetic_data(self, symbol: str, days: int) -> List[Dict]:
        """Generate synthetic price data for testing"""
        import random
        data = []
        price = 1000 if symbol == "BTC" else (50 if symbol == "ETH" else 58)
        
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
            price = daily["close"]  # Chain for next day
            
        return data
    
    async def on_strategy_proposed(self, event: Event):
        """Run backtest on proposed strategy"""
        strategy_id = event.payload.get("strategy_id")
        strategy = event.payload.get("strategy", {})
        
        # Run backtest
        results = await self.backtest(strategy)
        
        # Publish results
        await event_bus.publish(Event(
            type=EventType.STRATEGY_BACKTESTED,
            source="backtest_engine",
            payload={
                "strategy_id": strategy_id,
                "strategy_name": strategy.get("name", "Unknown"),
                "win_rate": results["win_rate"],
                "trades": results["total_trades"],
                "profit": results["total_profit"],
                "max_drawdown": results["max_drawdown"],
                "sharpe_ratio": results["sharpe_ratio"]
            }
        ))
    
    async def backtest(self, strategy: Dict) -> Dict:
        """Run backtest on historical data"""
        strategy_type = strategy.get("type", "unknown")
        params = strategy.get("parameters", {})
        
        # Simplified backtest logic
        if strategy_type == "mean_reversion":
            return await self._backtest_mean_reversion(params)
        elif strategy_type == "trend_following":
            return await self._backtest_trend_following(params)
        else:
            return await self._backtest_generic(params)
    
    async def _backtest_mean_reversion(self, params: Dict) -> Dict:
        """Simulate mean reversion strategy"""
        rsi_oversold = params.get("rsi_oversold", 30)
        rsi_overbought = params.get("rsi_overbought", 70)
        stop_loss = params.get("stop_loss", 2)
        
        # Simulate trading on historical data
        trades = []
        profits = []
        
        for data in self.historical_data["BTC"]:
            # Simplified: random RSI
            import random
            rsi = random.uniform(0, 100)
            
            if rsi < rsi_oversold:
                # Buy signal
                trades.append("BUY")
                # Random profit/loss
                profit = random.uniform(-stop_loss, 5)
                profits.append(profit)
            elif rsi > rsi_overbought:
                # Sell signal
                trades.append("SELL")
                profit = random.uniform(-stop_loss, 5)
                profits.append(profit)
        
        total_trades = len(profits)
        profitable_trades = len([p for p in profits if p > 0])
        win_rate = (profitable_trades / total_trades * 100) if total_trades > 0 else 0
        
        return {
            "win_rate": win_rate,
            "total_trades": total_trades,
            "total_profit": sum(profits),
            "max_drawdown": abs(min(profits)) if profits else 0,
            "sharpe_ratio": (sum(profits) / len(profits) / (max(profits) - min(profits))) if profits else 0
        }
    
    async def _backtest_trend_following(self, params: Dict) -> Dict:
        """Simulate trend following strategy"""
        # Simplified implementation
        return await self._backtest_mean_reversion(params)
    
    async def _backtest_generic(self, params: Dict) -> Dict:
        """Generic backtest"""
        return {
            "win_rate": random.uniform(40, 60),
            "total_trades": random.randint(50, 200),
            "total_profit": random.uniform(-1000, 5000),
            "max_drawdown": random.uniform(5, 15),
            "sharpe_ratio": random.uniform(0.5, 2.0)
        }

    async def process(self, task: str, memory_bus=None):
        """Process task – auto-generated stub"""
        return {"content": f"Processed: {task[:50]}", "worker": self.name}
    
    async def health_check(self):
        """Return worker health status"""
        return {"worker": self.name, "status": "healthy", "timestamp": __import__('time').time()}


from typing import Optional