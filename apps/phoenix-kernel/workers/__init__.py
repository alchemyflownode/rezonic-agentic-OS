# workers/__init__.py
"""Phoenix Kernel Workers Package"""

import sys
from pathlib import Path

_parent_dir = Path(__file__).parent.parent
if str(_parent_dir) not in sys.path:
    sys.path.insert(0, str(_parent_dir))

from workers.base_worker import Worker, BaseWorker

WORKER_REGISTRY = {}

def register_worker(name: str, cls: type) -> type:
    WORKER_REGISTRY[name] = cls
    return cls

def _safe_import(module_path: str, class_name: str):
    try:
        import importlib
        mod = importlib.import_module(module_path)
        return getattr(mod, class_name, None)
    except Exception:
        return None

# Import workers
RezCoderWorker = _safe_import("workers.rezcoder", "RezCoderWorker")
SovereignMcpServer = _safe_import("workers.sovereign_mcp_server", "SovereignMcpServer")
CodeGenWorker = _safe_import("workers.code_gen_worker", "CodeGenWorker")
SandboxWorker = _safe_import("workers.sandbox_worker", "SandboxWorker")
MemoryWorker = _safe_import("workers.memory_worker", "MemoryWorker")
PaperTraderWorker = _safe_import("workers.paper_trader_worker", "PaperTraderWorker")
CodeExecutionWorker = _safe_import("workers.code_execution_worker", "CodeExecutionWorker")

# Register all that loaded
for name, cls in [
    ("rezcoder", RezCoderWorker),
    ("sovereign_mcp_server", SovereignMcpServer),
    ("code_gen", CodeGenWorker),
    ("sandbox", SandboxWorker),
    ("memory", MemoryWorker),
    ("paper_trader", PaperTraderWorker),
    ("code_execution", CodeExecutionWorker),
]:
    if cls is not None:
        WORKER_REGISTRY[name] = cls

__all__ = [
    "Worker", "BaseWorker", "register_worker", "WORKER_REGISTRY",
    "RezCoderWorker", "SovereignMcpServer", "CodeGenWorker",
    "SandboxWorker", "MemoryWorker",
]
