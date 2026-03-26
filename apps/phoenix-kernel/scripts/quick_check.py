# quick_check.py
from pathlib import Path

workers_dir = Path("workers")

# Workers we want to load
target_workers = [
    "backtest_worker.py",
    "memory_worker.py", 
    "rez_swarm_worker.py",
    "strategy_evolver.py",
    "paper_trader_worker.py",
    "validator_worker.py",
    "vision_worker.py"
]

print("🔍 Checking worker files:")
print("=" * 50)

for w in target_workers:
    file_path = workers_dir / w
    if file_path.exists():
        size = file_path.stat().st_size
        print(f"✅ {w} exists ({size} bytes)")
    else:
        print(f"❌ {w} NOT FOUND")

print("\n" + "=" * 50)
print("💡 If files exist but not loading, there may be:")
print("   - Syntax errors in the file")
print("   - Missing dependencies")
print("   - Circular imports")