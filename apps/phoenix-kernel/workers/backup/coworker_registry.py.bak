"""
Coworker Worker Registry - Auto-discover and register all coworker workers
"""

import os
import sys
import importlib
import inspect
from pathlib import Path
from typing import Dict, Any, List, Optional

# Add coworker path
COWORKER_PATH = Path(__file__).parent / "coworker"
if str(COWORKER_PATH) not in sys.path:
    sys.path.insert(0, str(COWORKER_PATH))

def discover_workers() -> Dict[str, Dict[str, Any]]:
    """Discover all coworker workers - silences import errors"""
    workers = {}
    
    print("🔍 Discovering coworker workers...")
    
    # Scan all Python files in coworker directory
    for py_file in COWORKER_PATH.rglob("*.py"):
        if py_file.name.startswith("__"):
            continue
        
        try:
            # Try to import the module
            spec = importlib.util.spec_from_file_location(py_file.stem, py_file)
            if spec and spec.loader:
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                
                # Find worker classes
                for name, obj in inspect.getmembers(module, inspect.isclass):
                    if obj.__module__ != module.__name__:
                        continue
                    
                    # Check if it's a worker class
                    is_worker = False
                    worker_indicators = ['Worker', 'Agent', 'Manager', 'Handler', 'Processor', 'Service', 'Orchestrator']
                    
                    for indicator in worker_indicators:
                        if indicator in name:
                            is_worker = True
                            break
                    
                    # Also check for execute/process methods
                    if not is_worker:
                        methods = [m for m in dir(obj) if not m.startswith('_')]
                        if 'execute' in methods or 'process' in methods or 'run' in methods:
                            is_worker = True
                    
                    if is_worker and name not in workers:
                        workers[name] = {
                            "class": obj,
                            "module": py_file.stem,
                            "path": str(py_file),
                            "name": name
                        }
                        print(f"    ✅ Loaded: {name}")
                        
        except Exception as e:
            # Silently skip files that can't be imported
            pass
    
    print(f"\n📊 Total coworker workers discovered: {len(workers)}")
    return workers

# Auto-discover on import
COWORKER_WORKERS = discover_workers()

def get_coworker_classes() -> Dict[str, Any]:
    """Get dictionary of worker classes"""
    return {name: info["class"] for name, info in COWORKER_WORKERS.items()}

__all__ = ['COWORKER_WORKERS', 'get_coworker_classes']
