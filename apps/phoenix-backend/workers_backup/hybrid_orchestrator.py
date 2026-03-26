import sys
import asyncio
import logging
from datetime import datetime
from .base_worker import BaseWorker

logger = logging.getLogger(__name__)

class HybridOrchestrator(BaseWorker):
    """
    Orchestrates hybrid execution between different worker types
    """
    
    def __init__(self, hive_bus=None):
        super().__init__('orchestrator', hive_bus)
        self.workers = {}
        self.task_queue = []
        self.status = "ready"
        self.stats = {
            'tasks_routed': 0,
            'workers_registered': 0,
            'errors': 0
        }
        logger.info("  ✅ HybridOrchestrator initialized with OKIRU triggers")
        
    async def process(self, task, **kwargs):
        """Process orchestration tasks"""
        task_type = task.get('type', 'unknown')
        
        if task_type == 'status':
            return self.get_status()
        elif task_type == 'register_worker':
            return await self.register_worker(task.get('name'), task.get('worker'))
        else:
            return {'status': 'error', 'message': f'Unknown task: {task_type}'}
    
    async def register_worker(self, name, worker):
        """Register a worker with the orchestrator"""
        self.workers[name] = worker
        self.stats['workers_registered'] += 1
        return {'status': 'success', 'name': name}
    
    async def health_check(self):
        """Check orchestrator health"""
        base = await super().health_check() if hasattr(super(), 'health_check') else {}
        return {
            **base,
            'name': self.name,
            'status': self.status,
            'workers_count': len(self.workers),
            'healthy': True
        }
    
    def get_status(self):
        """Get orchestrator status"""
        return {
            'name': self.name,
            'status': self.status,
            'workers': list(self.workers.keys()),
            'stats': self.stats
        }
