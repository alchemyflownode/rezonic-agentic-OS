#!/usr/bin/env python3
# AUTO-FIXED IMPORT PATH
import sys
from pathlib import Path
_workers_dir = Path(__file__).parent.resolve()
if str(_workers_dir) not in sys.path:
    sys.path.insert(0, str(_workers_dir))
# END AUTO-FIX
"""
analyze_working_workers.py - See what's actually loading
"""

import sys
import importlib.util
import inspect
from pathlib import Path

# This simulates what your kernel does when loading workers
def analyze_worker_file(filepath):
    """Analyze how the kernel sees this worker"""
    try:
        # Import the module
        spec = importlib.util.spec_from_file_location(filepath.stem, filepath)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        
        # Find classes with execute method
        for name, obj in inspect.getmembers(module, inspect.isclass):
            if hasattr(obj, 'execute'):
                print(f"  ✅ {name} (has execute)")
            elif 'Worker' in name:
                print(f"  ⚠️ {name} (has Worker in name but no execute)")
        
        return True
    except Exception as e:
        print(f"  ❌ Error: {e}")
        return False

# Check a few workers
print("🔍 Analyzing workers...\n")

workers_to_check = [
    "workers/backup_worker.py",
    "workers/brain_worker.py", 
    "workers/system_worker.py",
    "workers/paper_trader_worker.py",
]

for worker_path in workers_to_check:
    path = Path(worker_path)
    if path.exists():
        print(f"\n📄 {path.name}:")
        analyze_worker_file(path)
    else:
        print(f"\n❌ {worker_path} not found")

print("\n" + "=" * 60)
print("💡 The kernel loads workers that:")
print("  1. Have a class with 'execute' method")
print("  2. OR have 'Worker' in the class name")
print("  3. OR are explicitly added as built-in")
print("=" * 60)