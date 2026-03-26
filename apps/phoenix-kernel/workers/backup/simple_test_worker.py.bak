"""Simple Test Worker for Phoenix"""
import sys
from pathlib import Path

parent_dir = Path(__file__).parent.parent
if str(parent_dir) not in sys.path:
    sys.path.insert(0, str(parent_dir))

from workers.base_worker import Worker, WorkerConfig

class SimpleTestWorker(Worker):
    """Simple test worker"""
    
    def __init__(self, config: WorkerConfig = None):
        super().__init__(config)
        self.name = "simple_test"
        self.is_ready = True
    
    async def execute(self, task: str, **kwargs) -> dict:
        self.log("info", f"Processing: {task[:30]}...")
        return {
            "status": "success",
            "worker": self.name,
            "content": f"Processed: {task}"
        }

SimpleTestWorker_CONFIG = {
    "name": "simple_test",
    "enabled": True
}
