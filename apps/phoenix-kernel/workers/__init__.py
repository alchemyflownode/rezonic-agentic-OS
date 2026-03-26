# workers/__init__.py
import sys
from pathlib import Path

parent_dir = Path(__file__).parent.parent
if str(parent_dir) not in sys.path:
    sys.path.insert(0, str(parent_dir))

from workers.base_worker import BaseWorker

try:
    from hybrid_orchestrator import HybridOrchestrator
except ImportError:
    HybridOrchestrator = None

# Worker registry for auto-discovery
WORKER_REGISTRY = {}

def register_worker(name: str, cls):
    WORKER_REGISTRY[name] = cls
    return cls

__all__ = ['BaseWorker', 'register_worker', 'WORKER_REGISTRY']
if HybridOrchestrator:
    __all__.append('HybridOrchestrator')