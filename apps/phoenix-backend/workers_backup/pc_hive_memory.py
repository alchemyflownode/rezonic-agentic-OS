"""
PC Hive Memory - Physical machine memory integration
"""
from .base_worker import BaseWorker
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
        self.initialize()
        
    def initialize(self):
        """Initialize PC Hive Memory"""
        logger.info("  🖥️ PCHiveMemory mounted")
        self.status = "ready"
        
    async def process(self, task, **kwargs):
        """Process memory-related tasks"""
        task_type = task.get('type', 'status')
        
        if task_type == 'status':
            return self.get_memory_status()
        elif task_type == 'alert':
            return self.check_alerts()
        elif task_type == 'optimize':
            return self.suggest_optimization()
        else:
            return {'status': 'error', 'message': f'Unknown task: {task_type}'}
            
    def get_memory_status(self):
        """Get current memory status"""
        memory = psutil.virtual_memory()
        swap = psutil.swap_memory()
        
        return {
            'status': 'success',
            'memory': {
                'total_gb': memory.total / (1024**3),
                'available_gb': memory.available / (1024**3),
                'used_gb': memory.used / (1024**3),
                'percent': memory.percent
            },
            'swap': {
                'total_gb': swap.total / (1024**3),
                'used_gb': swap.used / (1024**3),
                'percent': swap.percent
            },
            'timestamp': datetime.now().isoformat()
        }
        
    def check_alerts(self):
        """Check for memory alerts"""
        memory = psutil.virtual_memory()
        alerts = []
        
        if memory.percent > self.memory_threshold:
            alerts.append({
                'level': 'warning',
                'message': f'Memory usage at {memory.percent}%',
                'threshold': self.memory_threshold
            })
            
        return {
            'status': 'success',
            'alerts': alerts,
            'alert_count': len(alerts)
        }
        
    def suggest_optimization(self):
        """Suggest memory optimizations"""
        memory = psutil.virtual_memory()
        suggestions = []
        
        if memory.percent > 90:
            suggestions.append("Critical: Close unused applications")
        elif memory.percent > 75:
            suggestions.append("Warning: Consider closing memory-heavy applications")
            
        # Check for memory leaks
        process = psutil.Process()
        if process.memory_percent() > 10:
            suggestions.append(f"Process using {process.memory_percent():.1f}% of memory")
            
        return {
            'status': 'success',
            'suggestions': suggestions
        }
        
    async def health_check(self):
        """Check worker health"""
        base_health = super().health_check()
        memory = psutil.virtual_memory()
        
        base_health.update({
            'memory_usage': memory.percent,
            'healthy': base_health['healthy'] and memory.percent < 95
        })
        return base_health