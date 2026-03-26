import sys
from pathlib import Path

# Add parent directory to path
parent_dir = Path(__file__).parent.parent
if str(parent_dir) not in sys.path:
    sys.path.insert(0, str(parent_dir))
"""
PC Hive Memory - Physical machine memory integration
"""
from workers.base_worker import BaseWorker
import psutil
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class PCHiveMemory(BaseWorker):
    """
    Integrates with the physical machine's memory
    """

    def __init__(self, hive_bus=None):
        super().__init__('pc_hive', hive_bus)
        self.memory_threshold = 80  # Alert at 80% usage
        self.last_check = None
        self.status = "ready"
        logger.info("   PCHiveMemory mounted")

    async def health_check(self):
        """Health check for PC Hive Memory"""
        try:
            # Get base health info
            base = await super().health_check()
            
            # Get memory info
            memory = psutil.virtual_memory()
            self.last_check = datetime.now().isoformat()
            
            return {
                **base,
                'name': self.name,
                'status': self.status,
                'memory_percent': memory.percent,
                'memory_available': memory.available,
                'memory_total': memory.total,
                'healthy': memory.percent < self.memory_threshold,
                'last_check': self.last_check
            }
        except Exception as e:
            logger.error(f"PC Hive health check error: {e}")
            return {
                'name': self.name,
                'healthy': False,
                'error': str(e)
            }

    async def process(self, task, **kwargs):
        """Process memory-related tasks"""
        task_type = task.get('type', 'status') if isinstance(task, dict) else 'status'
        
        if task_type == 'status':
            return await self.health_check()
        elif task_type == 'memory_stats':
            return self.get_memory_stats()
        else:
            return {'error': f'Unknown task type: {task_type}'}

    def get_memory_stats(self):
        """Get current memory statistics"""
        try:
            memory = psutil.virtual_memory()
            return {
                'total': memory.total,
                'available': memory.available,
                'percent': memory.percent,
                'used': memory.used,
                'free': memory.free,
                'threshold': self.memory_threshold
            }
        except Exception as e:
            return {'error': str(e)}



