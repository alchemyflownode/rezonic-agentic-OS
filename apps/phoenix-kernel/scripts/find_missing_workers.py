# find_missing_workers.py
import sys
from pathlib import Path

sys.path.insert(0, str(Path.cwd()))

workers_dir = Path("workers")

# Get all Python files in workers directory
all_worker_files = []
for py_file in workers_dir.glob("*.py"):
    if py_file.name not in ['__init__.py', 'base_worker.py', 'decorators.py', 'registry.py']:
        all_worker_files.append(py_file.name)

print("=" * 70)
print("🔍 FINDING MISSING WORKERS")
print("=" * 70)

# Workers we saw loading in the log
loaded_from_log = [
    "backup_worker.py",
    "brain_worker.py",
    "browser_worker.py",
    "chronos_worker.py",
    "clipboard_worker.py",
    "comfyui_worker.py",
    "constitutional_council_fixed.py",
    "constitutional_governor.py",
    "constitutional_router.py",
    "core.py",
    "crypto_worker.py",
    "dream_worker.py",
    "entropy_worker.py",
    "evolution_worker.py",
    "execution_worker.py",
    "eyes_worker.py",
    "file_doctor_worker.py",
    "file_manager_worker.py",
    "forex_worker.py",
    "hybrid_orchestrator.py",
    "mock_trader.py",
    "ollama_constitutional_enhanced.py",
    "risk_worker.py",
    "sce_compiler.py",
    "system_control_worker.py",
    "test_worker.py",
    "trade_visualizer.py",
    "tradingview_worker.py",
    "voice_worker.py"
]

# Workers we added/fixed
fixed_workers = [
    "backtest_worker.py",
    "memory_worker.py",
    "rez_swarm_worker.py",
    "strategy_evolver.py",
    "paper_trader_worker.py",
    "validator_worker.py",
    "vision_worker.py"
]

# Combined loaded workers
loaded_workers = set(loaded_from_log + fixed_workers)

# Find missing
missing = []
for file in all_worker_files:
    if file not in loaded_workers:
        missing.append(file)

print(f"\n📊 SUMMARY:")
print(f"   Total worker files: {len(all_worker_files)}")
print(f"   Loaded workers: {len(loaded_workers)}")
print(f"   Missing workers: {len(missing)}")
print(f"   Success rate: {len(loaded_workers)/len(all_worker_files)*100:.1f}%")

print(f"\n❌ MISSING WORKERS ({len(missing)} files):")
for m in sorted(missing):
    print(f"   - {m}")

print("\n" + "=" * 70)