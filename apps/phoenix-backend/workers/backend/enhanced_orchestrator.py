# Enhanced with Compute Orchestrator patterns
from cognitive_patterns import ComputeOrchestrator

class EnhancedOrchestrator(ComputeOrchestrator):
    def __init__(self, hive_bus=None):
        super().__init__()
        self.hive_bus = hive_bus
        self.name = "enhanced_orchestrator"
    
    async def route_task(self, task):
        # Hardware-aware routing
        return await self.get_hardware_optimal(task)
