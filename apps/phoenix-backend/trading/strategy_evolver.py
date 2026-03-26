# backend/trading/strategy_evolver.py
"""
STRATEGY EVOLVER
Autonomous strategy evolution for trading
"""

import random
import time
import json
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field

from backend.core.sovereign_event_bus import event_bus, Event, EventType


@dataclass
class Strategy:
    """Trading strategy"""
    id: str
    name: str
    type: str
    parameters: Dict[str, Any]
    parent_id: Optional[str] = None
    generation: int = 1
    win_rate: float = 0.0
    total_trades: int = 0
    created_at: float = field(default_factory=time.time)


class StrategyEvolver:
    """
    Autonomous strategy evolution
    Creates mutations, tracks performance
    """
    
    def __init__(self):
        self.name = "StrategyEvolver"
        self.strategies: Dict[str, Strategy] = {}
        self.generation = 1
        self.mutation_rate = 0.3
        
        # Subscribe to events
        event_bus.subscribe(EventType.STRATEGY_BACKTESTED, self.on_backtest_result)
        event_bus.subscribe(EventType.MARKET_UPDATE, self.on_market_update)
        
        # Create initial strategies
        self._create_initial_strategies()
    
    def _create_initial_strategies(self):
        """Create initial strategy population"""
        
        base_strategies = [
            {
                "name": "Mean Reversion",
                "type": "mean_reversion",
                "parameters": {
                    "rsi_oversold": 30,
                    "rsi_overbought": 70,
                    "stop_loss": 2,
                    "take_profit": 4
                }
            },
            {
                "name": "Trend Following",
                "type": "trend_following",
                "parameters": {
                    "ema_short": 9,
                    "ema_long": 21,
                    "stop_loss": 3
                }
            },
            {
                "name": "Breakout",
                "type": "breakout",
                "parameters": {
                    "lookback": 20,
                    "volume_threshold": 1.5,
                    "stop_loss": 2.5
                }
            }
        ]
        
        for strat in base_strategies:
            strategy_id = f"{strat['type']}_{int(time.time())}_{random.randint(1000, 9999)}"
            self.strategies[strategy_id] = Strategy(
                id=strategy_id,
                name=strat["name"],
                type=strat["type"],
                parameters=strat["parameters"]
            )
    
    async def process(self, task: str, memory_bus=None) -> Dict[str, Any]:
        """Process strategy commands"""
        
        if "list" in task.lower():
            return await self.list_strategies()
        elif "create" in task.lower():
            return await self.create_strategy(task)
        elif "mutate" in task.lower():
            return await self.mutate_strategy(task)
        else:
            return {
                "content": "🧬 **Strategy Evolver Commands:**\n• `/strategy list` - List all strategies\n• `/strategy create [name]` - Create new\n• `/strategy mutate [id]` - Mutate existing"
            }
    
    async def list_strategies(self) -> Dict[str, Any]:
        """List all strategies"""
        
        lines = ["🧬 **STRATEGY EVOLVER**", ""]
        
        # Sort by win rate
        sorted_strategies = sorted(
            self.strategies.values(),
            key=lambda s: s.win_rate,
            reverse=True
        )
        
        for strat in sorted_strategies[:10]:
            lines.append(
                f"**{strat.name}** (Gen {strat.generation})\n"
                f"  • ID: `{strat.id[:8]}`\n"
                f"  • Win Rate: {strat.win_rate:.1f}%\n"
                f"  • Type: {strat.type}"
            )
        
        return {"content": "\n\n".join(lines), "worker": self.name}
    
    async def on_backtest_result(self, event: Event):
        """Process backtest results"""
        strategy_id = event.payload.get("strategy_id")
        win_rate = event.payload.get("win_rate", 0)
        
        if strategy_id in self.strategies:
            self.strategies[strategy_id].win_rate = win_rate
            
            # If win rate is good, create mutations
            if win_rate > 55:
                await self._create_mutations(self.strategies[strategy_id])
    
    async def _create_mutations(self, parent: Strategy):
        """Create mutated copies"""
        for i in range(3):
            if random.random() < self.mutation_rate:
                mutated_params = self._mutate_parameters(parent.parameters)
                
                mutation_id = f"{parent.id}_mut_{int(time.time())}_{i}"
                mutation = Strategy(
                    id=mutation_id,
                    name=f"{parent.name} (Mutation)",
                    type=parent.type,
                    parameters=mutated_params,
                    parent_id=parent.id,
                    generation=parent.generation + 1
                )
                
                self.strategies[mutation_id] = mutation
                
                await event_bus.publish(Event(
                    type=EventType.MUTATION_OCCURRED,
                    source="strategy_evolver",
                    payload={
                        "parent_id": parent.id,
                        "mutation_id": mutation_id
                    }
                ))
    
    def _mutate_parameters(self, params: Dict) -> Dict:
        """Mutate parameters"""
        mutated = params.copy()
        
        for key, value in mutated.items():
            if isinstance(value, (int, float)):
                # Mutate by ±20%
                factor = 1 + random.uniform(-0.2, 0.2)
                mutated[key] = max(1, value * factor)
        
        return mutated
    
    async def on_market_update(self, event: Event):
        """React to market conditions"""
        # Could trigger re-evaluation
        pass