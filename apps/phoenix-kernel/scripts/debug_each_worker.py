# debug_each_worker.py
import sys
import importlib.util
import inspect
from pathlib import Path

sys.path.insert(0, str(Path.cwd()))

workers_dir = Path("workers")

workers_to_test = [
    "backtest_worker.py",
    "memory_worker.py",
    "rez_swarm_worker.py",
    "strategy_evolver.py",
    "paper_trader_worker.py",
    "validator_worker.py",
    "vision_worker.py"
]

print("=" * 70)
print("🔍 DEBUGGING EACH WORKER")
print("=" * 70)

for worker_file in workers_to_test:
    file_path = workers_dir / worker_file
    print(f"\n📄 {worker_file}")
    print("-" * 50)
    
    try:
        # Try to import the module
        spec = importlib.util.spec_from_file_location(worker_file.replace('.py', ''), file_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        
        # Look for classes with execute method
        found_workers = []
        for name, obj in inspect.getmembers(module, inspect.isclass):
            if hasattr(obj, 'execute') and name != 'Worker':
                found_workers.append(name)
        
        if found_workers:
            print(f"✅ Found workers: {', '.join(found_workers)}")
        else:
            print(f"⚠️ No worker class found with 'execute' method")
            # Show what classes are in the module
            classes = [name for name, obj in inspect.getmembers(module, inspect.isclass)]
            if classes:
                print(f"   Classes found: {classes[:5]}")
            
    except SyntaxError as e:
        print(f"❌ Syntax error at line {e.lineno}: {e.msg}")
        # Show the problematic line
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()
            if e.lineno <= len(lines):
                print(f"   Line {e.lineno}: {lines[e.lineno-1].strip()}")
                
    except ImportError as e:
        print(f"❌ Import error: {e}")
        
    except Exception as e:
        print(f"❌ Other error: {type(e).__name__}: {e}")

print("\n" + "=" * 70)