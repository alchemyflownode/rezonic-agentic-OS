# debug_workers.py
import sys
from pathlib import Path

sys.path.insert(0, str(Path.cwd()))

print("=" * 70)
print("🔍 DIAGNOSING WORKER LOADING")
print("=" * 70)

workers_dir = Path("workers")
loaded = []
failed = []

for py_file in workers_dir.glob("*.py"):
    if py_file.name in ['__init__.py', 'base_worker.py', 'decorators.py', 'registry.py']:
        continue
    
    try:
        # Try to import the module
        import importlib.util
        spec = importlib.util.spec_from_file_location(py_file.stem, py_file)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        
        # Look for Worker classes
        import inspect
        found = False
        for name, obj in inspect.getmembers(module, inspect.isclass):
            if hasattr(obj, 'execute') or 'Worker' in name:
                found = True
                loaded.append(py_file.name)
                break
        
        if not found:
            failed.append(f"{py_file.name} - No worker class found")
            
    except Exception as e:
        failed.append(f"{py_file.name} - {str(e)[:80]}")

print(f"\n✅ LOADED ({len(loaded)} workers):")
for w in loaded[:20]:
    print(f"  - {w}")
if len(loaded) > 20:
    print(f"  ... and {len(loaded)-20} more")

print(f"\n❌ FAILED ({len(failed)} files):")
for f in failed:
    print(f"  - {f}")

print("\n" + "=" * 70)