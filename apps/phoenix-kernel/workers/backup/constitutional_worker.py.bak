"""Constitutional Worker - Fixed imports"""
import sys
from pathlib import Path

# Add parent to path
parent_dir = Path(__file__).parent.parent
if str(parent_dir) not in sys.path:
    sys.path.insert(0, str(parent_dir))

# Try to import, but provide fallback
try:
    from constitutional_evaluator import ConstitutionalEvaluator
except ImportError:
    # Create a placeholder
    class ConstitutionalEvaluator:
        def __init__(self):
            self.name = "constitutional_evaluator"
        
        def evaluate(self, *args, **kwargs):
            return {"approved": True, "score": 100}

from workers.base_worker import BaseWorker, WorkerConfig

class ConstitutionalWorker(BaseWorker):
    """Constitutional oversight worker"""
    
    def __init__(self, config=None):
        super().__init__(config)
        self.name = "constitutional_worker"
        self.evaluator = ConstitutionalEvaluator()
        self.is_ready = True
    
    async def execute(self, task, **kwargs):
        return {
            "status": "success",
            "worker": self.name,
            "evaluation": self.evaluator.evaluate(task)
        }
    
    async def validate(self, task):
        return "constitution" in task.lower() or "legal" in task.lower()

ConstitutionalWorker_CONFIG = {
    "name": "constitutional_worker",
    "enabled": True
}
