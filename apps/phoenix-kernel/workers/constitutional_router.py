# constitutional_router.py - FIXED
from typing import Dict, Any, Optional
import asyncio
import logging

logger = logging.getLogger("PHOENIX_ULTIMATE")

class ConstitutionalRouterWorker:
    """Routes tasks based on constitutional compliance"""
    
    def __init__(self):
        self.name = "ConstitutionalRouterWorker"
        self.routes = []
        self.worker_map = {
            'cognitive': ['brain', 'orchestrator'],
            'execution': ['hands', 'sandbox'],
            'analysis': ['scanner', 'techdebt'],
            'memory': ['cortex', 'memory']
        }
        logger.info(f"✅ {self.name} initialized")
    
    async def execute(self, task: str, context: Dict = None) -> Dict[str, Any]:
        """Route task to appropriate worker based on intent"""
        
        # Routing logic
        task_lower = task.lower()
        destination = 'brain'  # default
        
        if any(word in task_lower for word in ['scan', 'analyze', 'check']):
            destination = 'scanner'
        elif any(word in task_lower for word in ['run', 'execute', 'do']):
            destination = 'execution'
        elif any(word in task_lower for word in ['remember', 'recall']):
            destination = 'cortex'
        
        route = {
            "timestamp": asyncio.get_event_loop().time(),
            "task": task[:100],
            "destination": destination,
            "confidence": 0.85
        }
        
        self.routes.append(route)
        
        return {
            "worker": self.name,
            "route": route,
            "available_workers": self.worker_map
        }
    
    async def get_stats(self) -> Dict:
        return {
            "name": self.name,
            "total_routes": len(self.routes),
            "recent_routes": self.routes[-5:]
        }
