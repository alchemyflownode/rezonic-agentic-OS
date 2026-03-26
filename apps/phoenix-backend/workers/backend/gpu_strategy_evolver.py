import sys
sys.path.append('D:\\okiru-os\\RezHiveOS\\cognitive_imports')
from workers.mutation_worker import MutationWorker

class GPUStrategyEvolver(MutationWorker):
    def __init__(self, hive_bus=None):
        super().__init__()
        self.hive_bus = hive_bus
        self.name = "gpu_strategy_evolver"
    
    async def evolve(self, population):
        # Use GPU for parallel evolution
        return await self.gpu_evolve(population)
