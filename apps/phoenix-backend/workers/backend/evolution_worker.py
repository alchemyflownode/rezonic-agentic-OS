# backend/workers/evolution_worker.py
import asyncio
import random
import logging
from typing import Dict, Any, List

logger = logging.getLogger(__name__)

class EvolutionWorker:
    """
    Self-optimizing AI for strategy evolution.
    Uses genetic algorithm principles to generate, evaluate, and select strategies.
    """

    signature = {
        "id": "evolution_worker",
        "label": "🧬 Evolution Engine",
        "inputs": ["performance_metrics", "strategy_library"],
        "outputs": ["new_strategies", "updated_library"],
        "threshold": 0.05,
        "parallel": True
    }

    def __init__(self, hive_bus=None):
        self.strategy_library: List[Dict[str, Any]] = []
        self.generation = 0
        self.max_strategies = 20  # max concurrent strategies

    async def evolve(self, backtest_results: List[Dict[str, Any]]):
        """
        Core evolution loop:
        1. Evaluate metrics
        2. Select top performers
        3. Mutate parameters
        4. Update strategy library
        """
        logger.info(f"🧬 Starting evolution cycle #{self.generation}")

        # 1️⃣ Select top performers
        sorted_results = sorted(backtest_results, key=lambda x: x['metrics']['expectancy'], reverse=True)
        top_strategies = sorted_results[:max(1, len(sorted_results)//2)]

        # 2️⃣ Mutate and generate new strategies
        new_strategies = []
        for strat in top_strategies:
            mutated = self._mutate_strategy(strat['strategy_params'])
            new_strategies.append(mutated)

        # 3️⃣ Maintain strategy library size
        self.strategy_library = top_strategies + new_strategies
        if len(self.strategy_library) > self.max_strategies:
            self.strategy_library = self.strategy_library[:self.max_strategies]

        self.generation += 1
        logger.info(f"🧬 Evolution cycle #{self.generation} complete. Library size: {len(self.strategy_library)}")
        return self.strategy_library

    def _mutate_strategy(self, strategy_params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Slightly tweak parameters for exploration
        """
        mutated = strategy_params.copy()
        for key, value in strategy_params.items():
            if isinstance(value, (int, float)):
                # small random tweak ±5%
                delta = value * random.uniform(-0.05, 0.05)
                mutated[key] = round(value + delta, 6)
        return mutated
