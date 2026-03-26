# check_missing_workers.py
import sys
from pathlib import Path

sys.path.insert(0, str(Path.cwd()))

workers_dir = Path("workers")

key_workers = [
    "backtest_engine.py",
    "backtest_worker.py", 
    "memory_worker.py",
    "paper_trader_worker.py",
    "rez_swarm_worker.py",
    "strategy_evolver.py",
    "validator_worker.py",
    "vision_worker.py"
]

print("🔍 Testing specific workers...")
print("=" * 60)

for worker_name in key_workers:
    file_path = workers_dir / worker_name
    if not file_path.exists():
        print(f"❌ {worker_name} - File not found")
        continue
    
    try:
        import importlib.util
        spec = importlib.util.spec_from_file_location(file_path.stem, file_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        
        # Look for worker classes
        import inspect
        found = False
        for name, obj in inspect.getmembers(module, inspect.isclass):
            if hasattr(obj, 'execute') and name != 'Worker':
                print(f"✅ {worker_name} - Found worker: {name}")
                found = True
                break
        
        if not found:
            print(f"⚠️ {worker_name} - No worker class found")
            
    except Exception as e:
        print(f"❌ {worker_name} - Error: {str(e)[:100]}")

print("\n" + "=" * 60)