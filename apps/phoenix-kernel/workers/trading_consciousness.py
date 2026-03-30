# workers/trading_consciousness.py
"""
Trading Consciousness Worker - Self-evolving trading AI
Continuously simulates trades, learns patterns, and optimizes strategies
"""

import asyncio
import random
import numpy as np
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import hashlib
import json
from collections import deque
import logging

logger = logging.getLogger(__name__)

@dataclass
class TradeSimulation:
    """A simulated trade with outcome"""
    id: str
    strategy: str
    action: str
    symbol: str
    amount: float
    price: float
    simulated_price: float
    pnl: float
    confidence: float
    timestamp: float
    reasoning: str
    success: bool

@dataclass
class Strategy:
    """A trading strategy with performance metrics"""
    name: str
    description: str
    parameters: Dict[str, Any]
    win_rate: float = 0.0
    total_trades: int = 0
    total_pnl: float = 0.0
    avg_confidence: float = 0.0
    last_used: float = 0.0
    exploration_bonus: float = 1.0
    
class TradingConsciousnessWorker:
    """Self-evolving trading AI that continuously simulates and learns"""
    
    def __init__(self):
        self.name = "trading_consciousness"
        self.strategies: Dict[str, Strategy] = {}
        self.simulation_history: deque = deque(maxlen=10000)
        self.pattern_memory: Dict[str, List[TradeSimulation]] = {}
        self.consciousness_state = {
            "market_sentiment": 0.0,
            "volatility": 0.0,
            "momentum": 0.0,
            "risk_appetite": 0.5,
            "learning_rate": 0.1,
            "total_simulations": 0,
            "active_since": None
        }
        
        self._init_strategies()
        self._simulating = False
        self._simulation_task = None
        
        logger.info("🧠 Trading Consciousness initialized")
    
    def _init_strategies(self):
        """Initialize the strategy library"""
        self.strategies = {
            "mean_reversion": Strategy(
                name="mean_reversion",
                description="Buy when price is below moving average",
                parameters={"lookback": 20, "threshold": 0.02}
            ),
            "momentum": Strategy(
                name="momentum",
                description="Follow trend with RSI confirmation",
                parameters={"rsi_period": 14, "overbought": 70, "oversold": 30}
            ),
            "breakout": Strategy(
                name="breakout",
                description="Trade breakouts from consolidation",
                parameters={"range_period": 20, "breakout_multiplier": 1.5}
            ),
            "volatility_arbitrage": Strategy(
                name="volatility_arbitrage",
                description="Profit from volatility spikes",
                parameters={"volatility_threshold": 0.03}
            ),
            "ai_adaptive": Strategy(
                name="ai_adaptive",
                description="AI-learned adaptive strategy",
                parameters={"learning_rate": 0.01, "exploration_rate": 0.1}
            )
        }
    
    async def start_consciousness(self):
        """Start the continuous simulation loop"""
        if self._simulating:
            return
        
        self._simulating = True
        self.consciousness_state["active_since"] = datetime.now().isoformat()
        self._simulation_task = asyncio.create_task(self._consciousness_loop())
        logger.info("🧠 Trading Consciousness activated - continuous learning started")
        return {"status": "started", "message": "Trading consciousness activated"}
    
    async def stop_consciousness(self):
        """Stop the simulation loop"""
        self._simulating = False
        if self._simulation_task:
            self._simulation_task.cancel()
        logger.info("🧠 Trading Consciousness deactivated")
        return {"status": "stopped", "message": "Trading consciousness deactivated"}
    
    async def _consciousness_loop(self):
        """Main loop - continuously simulates and learns"""
        while self._simulating:
            try:
                strategy = self._select_strategy()
                simulation = await self._simulate_trade(strategy)
                await self._learn_from_simulation(simulation, strategy)
                self._update_consciousness(simulation)
                
                if len(self.simulation_history) % 100 == 0:
                    await self._optimize_strategies()
                
                sleep_time = random.uniform(0.5, 2.0) * (1 - self.consciousness_state["volatility"])
                await asyncio.sleep(sleep_time)
                
            except Exception as e:
                logger.error(f"Consciousness loop error: {e}")
                await asyncio.sleep(1)
    
    def _select_strategy(self) -> Strategy:
        """Select strategy using epsilon-greedy with exploration bonus"""
        epsilon = self.consciousness_state["learning_rate"]
        
        if random.random() < epsilon:
            unused_strategies = [s for s in self.strategies.values() if s.total_trades < 10]
            if unused_strategies:
                return random.choice(unused_strategies)
        
        best_strategy = max(
            self.strategies.values(),
            key=lambda s: (s.win_rate * 0.6 + s.total_pnl * 0.4) * s.exploration_bonus
        )
        return best_strategy
    
    async def _simulate_trade(self, strategy: Strategy) -> TradeSimulation:
        """Simulate a trade using the selected strategy"""
        market_data = await self._get_market_data()
        signal, confidence, reasoning = await self._apply_strategy(strategy, market_data)
        
        if not signal:
            return await self._simulate_random_trade(strategy)
        
        success_probability = self._calculate_success_probability(signal, market_data, confidence)
        success = random.random() < success_probability
        
        if success:
            pnl = signal["amount"] * signal["price"] * random.uniform(0.01, 0.05)
        else:
            pnl = -signal["amount"] * signal["price"] * random.uniform(0.005, 0.02)
        
        simulation = TradeSimulation(
            id=f"sim_{int(datetime.now().timestamp())}_{random.randint(1000,9999)}",
            strategy=strategy.name,
            action=signal["action"],
            symbol=signal["symbol"],
            amount=signal["amount"],
            price=signal["price"],
            simulated_price=signal["price"] * (1 + (pnl / (signal["amount"] * signal["price"]))),
            pnl=pnl,
            confidence=confidence,
            timestamp=datetime.now().timestamp(),
            reasoning=reasoning,
            success=success
        )
        
        self.simulation_history.append(simulation)
        self.consciousness_state["total_simulations"] = len(self.simulation_history)
        
        pattern_key = f"{strategy.name}_{signal['action']}_{int(market_data.get('volatility', 0)*100)}"
        if pattern_key not in self.pattern_memory:
            self.pattern_memory[pattern_key] = []
        self.pattern_memory[pattern_key].append(simulation)
        
        return simulation
    
    async def _learn_from_simulation(self, simulation: TradeSimulation, strategy: Strategy):
        """Learn from simulation outcome"""
        strategy.total_trades += 1
        strategy.total_pnl += simulation.pnl
        
        if simulation.success:
            current_win_rate = strategy.win_rate * (strategy.total_trades - 1) / strategy.total_trades
            strategy.win_rate = current_win_rate + (1 / strategy.total_trades)
        else:
            strategy.win_rate = strategy.win_rate * (strategy.total_trades - 1) / strategy.total_trades
        
        strategy.avg_confidence = (strategy.avg_confidence * (strategy.total_trades - 1) + simulation.confidence) / strategy.total_trades
        strategy.last_used = simulation.timestamp
        
        if simulation.success:
            strategy.exploration_bonus *= 1.05
        else:
            strategy.exploration_bonus *= 0.98
    
    def _update_consciousness(self, simulation: TradeSimulation):
        """Update the consciousness state based on simulations"""
        recent_trades = list(self.simulation_history)[-50:]
        if recent_trades:
            win_rate = sum(1 for t in recent_trades if t.success) / len(recent_trades)
            self.consciousness_state["market_sentiment"] = win_rate * 2 - 1
        
        if len(recent_trades) > 10:
            pnls = [t.pnl for t in recent_trades[-10:]]
            self.consciousness_state["volatility"] = min(1.0, np.std(pnls) / 1000)
        
        if len(recent_trades) > 20:
            avg_pnl = sum(t.pnl for t in recent_trades[-20:]) / 20
            self.consciousness_state["risk_appetite"] = max(0.1, min(0.9, 
                0.5 + (avg_pnl / 10000) * self.consciousness_state["volatility"]
            ))
        
        self.consciousness_state["learning_rate"] = max(0.01, 
            self.consciousness_state["learning_rate"] * 0.999
        )
    
    async def _optimize_strategies(self):
        """Optimize strategy parameters based on simulation results"""
        for strategy in self.strategies.values():
            if strategy.total_trades < 20:
                continue
            
            strategy_sims = [s for s in self.simulation_history if s.strategy == strategy.name]
            if not strategy_sims:
                continue
            
            success_rate = len([s for s in strategy_sims if s.success]) / len(strategy_sims)
            avg_confidence_success = np.mean([s.confidence for s in strategy_sims if s.success]) if any(s.success for s in strategy_sims) else 0
            avg_confidence_loss = np.mean([s.confidence for s in strategy_sims if not s.success]) if any(not s.success for s in strategy_sims) else 0
            
            if success_rate > 0.6 and avg_confidence_success > avg_confidence_loss:
                if "threshold" in strategy.parameters:
                    strategy.parameters["threshold"] *= 1.05
            elif success_rate < 0.4:
                if "threshold" in strategy.parameters:
                    strategy.parameters["threshold"] *= 0.95
                if "lookback" in strategy.parameters:
                    strategy.parameters["lookback"] = max(5, int(strategy.parameters["lookback"] * random.uniform(0.8, 1.2)))
    
    async def _apply_strategy(self, strategy: Strategy, market_data: Dict) -> tuple:
        """Apply strategy to generate trade signal"""
        price = market_data.get("price", 50000)
        
        if strategy.name == "mean_reversion":
            ma = market_data.get("ma_20", price)
            deviation = (price - ma) / ma
            if deviation < -strategy.parameters["threshold"]:
                confidence = min(0.9, abs(deviation) * 10)
                return {"action": "buy", "symbol": "BTCUSD", "amount": 0.01, "price": price}, confidence, f"Price {deviation:.2%} below MA"
            elif deviation > strategy.parameters["threshold"]:
                confidence = min(0.9, abs(deviation) * 10)
                return {"action": "sell", "symbol": "BTCUSD", "amount": 0.01, "price": price}, confidence, f"Price {deviation:.2%} above MA"
        
        elif strategy.name == "momentum":
            rsi = market_data.get("rsi", 50)
            if rsi < strategy.parameters["oversold"]:
                confidence = 1 - (rsi / strategy.parameters["oversold"])
                return {"action": "buy", "symbol": "BTCUSD", "amount": 0.01, "price": price}, confidence, f"RSI oversold: {rsi}"
            elif rsi > strategy.parameters["overbought"]:
                confidence = (rsi - strategy.parameters["overbought"]) / (100 - strategy.parameters["overbought"])
                return {"action": "sell", "symbol": "BTCUSD", "amount": 0.01, "price": price}, confidence, f"RSI overbought: {rsi}"
        
        elif strategy.name == "breakout":
            high = market_data.get("high_20", 52000)
            low = market_data.get("low_20", 48000)
            if price > high:
                confidence = min(0.9, (price - high) / high)
                return {"action": "buy", "symbol": "BTCUSD", "amount": 0.01, "price": price}, confidence, f"Breakout above {high}"
            elif price < low:
                confidence = min(0.9, (low - price) / low)
                return {"action": "sell", "symbol": "BTCUSD", "amount": 0.01, "price": price}, confidence, f"Breakout below {low}"
        
        elif strategy.name == "volatility_arbitrage":
            volatility = market_data.get("volatility", 0.02)
            if volatility > strategy.parameters["volatility_threshold"]:
                confidence = min(0.8, volatility * 10)
                return {"action": "buy", "symbol": "BTCUSD", "amount": 0.01, "price": price}, confidence, f"High volatility: {volatility:.2%}"
        
        elif strategy.name == "ai_adaptive":
            sentiment = self.consciousness_state["market_sentiment"]
            volatility = market_data.get("volatility", 0.02)
            signal_strength = sentiment * (1 - volatility) * strategy.parameters["learning_rate"]
            if abs(signal_strength) > 0.3:
                action = "buy" if signal_strength > 0 else "sell"
                confidence = abs(signal_strength)
                return {"action": action, "symbol": "BTCUSD", "amount": 0.01, "price": price}, confidence, f"AI adaptive: sentiment={sentiment:.2f}"
        
        return None, 0, ""
    
    async def _simulate_random_trade(self, strategy: Strategy) -> TradeSimulation:
        """Simulate a random small trade for exploration"""
        action = random.choice(["buy", "sell"])
        price = 50000
        amount = 0.005
        success = random.random() < 0.5
        
        pnl = amount * price * random.uniform(-0.02, 0.02) if success else -amount * price * random.uniform(0.01, 0.03)
        
        return TradeSimulation(
            id=f"rand_{int(datetime.now().timestamp())}",
            strategy=strategy.name,
            action=action,
            symbol="BTCUSD",
            amount=amount,
            price=price,
            simulated_price=price * (1 + pnl/(amount*price)),
            pnl=pnl,
            confidence=0.3,
            timestamp=datetime.now().timestamp(),
            reasoning="Random exploration trade",
            success=success
        )
    
    async def _get_market_data(self) -> Dict:
        """Get current market data from kernel"""
        try:
            from workers.paper_trader_worker import paper_trader
            portfolio = await paper_trader.get_portfolio()
            return {
                "price": 50000 + random.uniform(-1000, 1000),
                "ma_20": 49800 + random.uniform(-500, 500),
                "rsi": random.uniform(20, 80),
                "high_20": 52000,
                "low_20": 48000,
                "volatility": random.uniform(0.01, 0.05),
                "volume": random.uniform(1000, 10000)
            }
        except:
            return {
                "price": 50000 + random.uniform(-1000, 1000),
                "ma_20": 49800 + random.uniform(-500, 500),
                "rsi": random.uniform(20, 80),
                "high_20": 52000,
                "low_20": 48000,
                "volatility": random.uniform(0.01, 0.05),
                "volume": random.uniform(1000, 10000)
            }
    
    def _calculate_success_probability(self, signal: Dict, market_data: Dict, confidence: float) -> float:
        """Calculate probability of trade success"""
        base_prob = 0.5 + confidence * 0.3
        sentiment_boost = self.consciousness_state["market_sentiment"] * 0.1
        
        if signal["action"] == "buy":
            sentiment_boost *= 1
        else:
            sentiment_boost *= -1
        
        return min(0.95, max(0.05, base_prob + sentiment_boost))
    
    async def get_consciousness_state(self) -> Dict:
        """Get current consciousness state"""
        return {
            "status": "active" if self._simulating else "inactive",
            "consciousness_state": self.consciousness_state,
            "strategies": {
                name: {
                    "win_rate": s.win_rate,
                    "total_trades": s.total_trades,
                    "total_pnl": s.total_pnl,
                    "parameters": s.parameters
                }
                for name, s in self.strategies.items()
            },
            "total_simulations": len(self.simulation_history),
            "best_strategy": max(self.strategies.values(), key=lambda s: s.win_rate).name if self.strategies else "none"
        }
    
    async def get_strategy_performance(self, strategy_name: str) -> Dict:
        """Get detailed performance for a strategy"""
        strategy = self.strategies.get(strategy_name)
        if not strategy:
            return {"error": "Strategy not found"}
        
        strategy_sims = [s for s in self.simulation_history if s.strategy == strategy_name]
        
        return {
            "name": strategy.name,
            "description": strategy.description,
            "win_rate": strategy.win_rate,
            "total_trades": strategy.total_trades,
            "total_pnl": strategy.total_pnl,
            "avg_confidence": strategy.avg_confidence,
            "parameters": strategy.parameters,
            "recent_simulations": [
                {
                    "action": s.action,
                    "pnl": s.pnl,
                    "success": s.success,
                    "confidence": s.confidence,
                    "reasoning": s.reasoning
                }
                for s in strategy_sims[-10:]
            ]
        }

# Singleton instance
trading_consciousness = TradingConsciousnessWorker()

# Add to workers/trading_consciousness.py - Execution methods

async def execute_best_trade(self) -> Dict[str, Any]:
    """Execute the best trade based on current consciousness state"""
    
    # Get the best performing strategy
    best_strategy = max(
        self.strategies.values(),
        key=lambda s: (s.win_rate * 0.7 + s.total_pnl * 0.3) if s.total_trades > 10 else 0
    )
    
    # Get current market data
    market_data = await self._get_market_data()
    
    # Generate signal from best strategy
    signal, confidence, reasoning = await self._apply_strategy(best_strategy, market_data)
    
    if not signal or confidence < 0.4:
        return {"executed": False, "reason": "No clear signal"}
    
    # Check if we should execute based on risk
    if confidence < self.consciousness_state["risk_appetite"]:
        return {"executed": False, "reason": f"Confidence {confidence:.2f} below risk appetite"}
    
    # Execute the trade
    try:
        from workers.paper_trader_worker import paper_trader
        
        result = await paper_trader.execute_trade(
            action=signal["action"],
            symbol=signal["symbol"],
            amount=signal["amount"],
            price=signal["price"]
        )
        
        if result["success"]:
            logger.info(f"🤖 AI EXECUTED TRADE: {signal['action'].upper()} {signal['amount']} {signal['symbol']} - Confidence: {confidence:.2%}")
            await self._record_executed_trade(signal, result, confidence, reasoning)
            return {
                "executed": True,
                "trade_id": result.get("trade_id"),
                "action": signal["action"],
                "amount": signal["amount"],
                "price": signal["price"],
                "confidence": confidence,
                "reasoning": reasoning,
                "balance": result.get("balance")
            }
        else:
            logger.warning(f"🤖 Trade rejected: {result.get('error')}")
            return {"executed": False, "reason": result.get("error")}
            
    except Exception as e:
        logger.error(f"Trade execution failed: {e}")
        return {"executed": False, "reason": str(e)}

async def _record_executed_trade(self, signal: Dict, result: Dict, confidence: float, reasoning: str):
    """Record an executed trade in consciousness memory"""
    execution_record = {
        "timestamp": datetime.now().timestamp(),
        "strategy": self.best_strategy_name,
        "action": signal["action"],
        "amount": signal["amount"],
        "price": signal["price"],
        "confidence": confidence,
        "reasoning": reasoning,
        "trade_id": result.get("trade_id"),
        "balance_after": result.get("balance")
    }
    
    if not hasattr(self, 'execution_history'):
        self.execution_history = deque(maxlen=500)
    self.execution_history.append(execution_record)

async def set_autonomous_mode(self, enabled: bool, interval: int = 60):
    """Enable/disable autonomous trading"""
    self.autonomous_enabled = enabled
    self.autonomous_interval = interval
    
    if enabled and not hasattr(self, '_autonomous_task'):
        self._autonomous_task = asyncio.create_task(self._autonomous_loop())
        logger.info(f"🤖 Autonomous trading enabled - checking every {interval}s")
    elif not enabled and hasattr(self, '_autonomous_task'):
        self._autonomous_task.cancel()
        delattr(self, '_autonomous_task')
        logger.info("🤖 Autonomous trading disabled")

async def _autonomous_loop(self):
    """Main autonomous trading loop"""
    while self.autonomous_enabled:
        try:
            # Check if we should trade based on consciousness state
            if self.consciousness_state["market_sentiment"] != 0:
                result = await self.execute_best_trade()
                if result.get("executed"):
                    logger.info(f"🤖 Autonomous trade executed: {result}")
                elif result.get("reason"):
                    logger.debug(f"🤖 No trade: {result['reason']}")
            
            await asyncio.sleep(self.autonomous_interval)
        except Exception as e:
            logger.error(f"Autonomous loop error: {e}")
            await asyncio.sleep(self.autonomous_interval)
