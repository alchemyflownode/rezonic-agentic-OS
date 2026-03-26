import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
# backend/workers/strategy_evolver.py
"""
Strategy Evolver - Learns from backtest results
Creates mutations, tracks win rates, advances generations
"""

import random
import json
import time
from typing import Dict, List, Any
from dataclasses import dataclass, field

from backend.core.event_bus import event_bus, Event, EventType


@dataclass
class Strategy:
    """A trading or decision strategy"""
    id: str
    name: str
    type: str  # 'mean_reversion', 'trend_following', 'arbitrage', etc.
    parameters: Dict[str, Any]
    parent_id: Optional[str] = None
    generation: int = 1
    win_rate: float = 0.0
    total_trades: int = 0
    profitable_trades: int = 0
    created_at: float = field(default_factory=time.time)
    
    @property
    def profit_factor(self) -> float:
        """Calculate profit factor"""
        return self.win_rate * 100


class StrategyEvolver:
    """
    Autonomous strategy evolution
    Listens to backtest results, creates mutations
    """
    
    def __init__(self):
        self.name = "StrategyEvolver"
        self.strategies: Dict[str, Strategy] = {}
        self.generation = 1
        self.mutation_rate = 0.3
        self.population_size = 50
        
        # Subscribe to events
        event_bus.subscribe(EventType.STRATEGY_BACKTESTED, self.on_backtest_result)
        event_bus.subscribe(EventType.MARKET_UPDATE, self.on_market_update)
        
    async def on_backtest_result(self, event: Event):
        """Process backtest results and evolve"""
        strategy_id = event.payload.get("strategy_id")
        win_rate = event.payload.get("win_rate", 0)
        trades = event.payload.get("trades", 0)
        
        if strategy_id in self.strategies:
            strategy = self.strategies[strategy_id]
            strategy.win_rate = win_rate
            strategy.total_trades = trades
            
            # If win rate is good, create mutations
            if win_rate > 55:
                await self._create_mutations(strategy)
                
            # Publish evolution event
            await event_bus.publish(Event(
                type=EventType.WIN_RATE_UPDATED,
                source="strategy_evolver",
                payload={
                    "strategy_id": strategy_id,
                    "win_rate": win_rate,
                    "generation": strategy.generation
                }
            ))
    
    async def _create_mutations(self, parent: Strategy):
        """Create mutated copies of successful strategy"""
        for i in range(3):  # Create 3 mutations
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
                
                # Publish mutation event
                await event_bus.publish(Event(
                    type=EventType.MUTATION_OCCURRED,
                    source="strategy_evolver",
                    payload={
                        "parent_id": parent.id,
                        "mutation_id": mutation_id,
                        "parameters": mutated_params
                    }
                ))
                
                # Auto-backtest new mutation
                await event_bus.publish(Event(
                    type=EventType.STRATEGY_PROPOSED,
                    source="strategy_evolver",
                    payload={
                        "strategy_id": mutation_id,
                        "strategy": {
                            "name": mutation.name,
                            "type": mutation.type,
                            "parameters": mutation.parameters
                        }
                    }
                ))
    
    def _mutate_parameters(self, params: Dict) -> Dict:
        """Mutate strategy parameters"""
        mutated = params.copy()
        
        # Different mutation strategies based on parameter type
        for key, value in mutated.items():
            if isinstance(value, (int, float)):
                # Numeric mutation: Â±10-30%
                factor = 1 + random.uniform(-0.3, 0.3)
                mutated[key] = value * factor
                
                # Keep within bounds if specified
                if key == "rsi_oversold":
                    mutated[key] = max(20, min(40, mutated[key]))
                elif key == "rsi_overbought":
                    mutated[key] = max(60, min(80, mutated[key]))
                elif key == "stop_loss":
                    mutated[key] = max(1, min(5, mutated[key]))
                    
            elif isinstance(value, bool):
                # Boolean mutation: 10% chance to flip
                if random.random() < 0.1:
                    mutated[key] = not value
                    
        return mutated
    
    async def on_market_update(self, event: Event):
        """React to market conditions"""
        # Could trigger strategy adjustments based on volatility
        pass
    
    async def get_best_strategies(self, limit: int = 5) -> List[Strategy]:
        """Get top performing strategies"""
        sorted_strategies = sorted(
            self.strategies.values(),
            key=lambda s: s.win_rate,
            reverse=True
        )
        return sorted_strategies[:limit]

    async def process(self, task: str, memory_bus=None):
        """Process task – auto-generated stub"""
        return {"content": f"Processed: {task[:50]}", "worker": self.name}
    
    async def health_check(self):
        """Return worker health status"""
        return {"worker": self.name, "status": "healthy", "timestamp": __import__('time').time()}


from typing import Optional