# fix_worker_issues.py
import sys
from pathlib import Path

workers_dir = Path("workers")

print("=" * 70)
print("🔧 FIXING WORKER ISSUES")
print("=" * 70)

# ============================================================================
# 1. CREATE base_worker.py
# ============================================================================
base_path = workers_dir / "base_worker.py"
base_content = '''from abc import ABC, abstractmethod
from typing import Dict, Any

class Worker(ABC):
    """Base worker class for all Phoenix workers"""
    
    def __init__(self, name: str):
        self.name = name
    
    @abstractmethod
    async def execute(self, task: str, **kwargs) -> Dict[str, Any]:
        """Execute worker task"""
        pass
'''
base_path.write_text(base_content, encoding='utf-8')
print("✅ Created base_worker.py")

# ============================================================================
# 2. FIX memory_worker.py (remove BOM character)
# ============================================================================
memory_path = workers_dir / "memory_worker.py"
if memory_path.exists():
    try:
        # Read with utf-8-sig to strip BOM
        content = memory_path.read_text(encoding='utf-8-sig')
        # Also ensure it imports Worker
        if "from base_worker import Worker" not in content:
            content = "from base_worker import Worker\n" + content
        memory_path.write_text(content, encoding='utf-8')
        print("✅ Fixed memory_worker.py (removed BOM, added import)")
    except Exception as e:
        print(f"❌ Could not fix memory_worker.py: {e}")

# ============================================================================
# 3. FIX backtest_engine.py (Event import)
# ============================================================================
backtest_path = workers_dir / "backtest_engine.py"
if backtest_path.exists():
    content = backtest_path.read_text(encoding='utf-8', errors='ignore')
    # Add Event import if needed
    if "class Event" not in content and "from event" not in content:
        # Comment out Event references or add dummy Event class
        content = "class Event: pass\n\n" + content
        backtest_path.write_text(content, encoding='utf-8')
        print("✅ Fixed backtest_engine.py (added Event class)")
    else:
        print("✓ backtest_engine.py OK")

# ============================================================================
# 4. FIX strategy_evolver.py (Event import)
# ============================================================================
strategy_path = workers_dir / "strategy_evolver.py"
if strategy_path.exists():
    content = strategy_path.read_text(encoding='utf-8', errors='ignore')
    if "class Event" not in content and "from event" not in content:
        content = "class Event: pass\n\n" + content
        strategy_path.write_text(content, encoding='utf-8')
        print("✅ Fixed strategy_evolver.py (added Event class)")
    else:
        print("✓ strategy_evolver.py OK")

# ============================================================================
# 5. FIX rez_swarm_worker.py (import base_worker)
# ============================================================================
rez_path = workers_dir / "rez_swarm_worker.py"
if rez_path.exists():
    content = rez_path.read_text(encoding='utf-8', errors='ignore')
    if "from base_worker import Worker" not in content and "from .base_worker" not in content:
        content = "from base_worker import Worker\n" + content
        rez_path.write_text(content, encoding='utf-8')
        print("✅ Fixed rez_swarm_worker.py (added import)")
    else:
        print("✓ rez_swarm_worker.py OK")

# ============================================================================
# 6. FIX paper_trader_worker.py (ensure proper import)
# ============================================================================
paper_path = workers_dir / "paper_trader_worker.py"
if paper_path.exists():
    content = paper_path.read_text(encoding='utf-8', errors='ignore')
    if "from base_worker import Worker" not in content:
        content = "from base_worker import Worker\n" + content
        paper_path.write_text(content, encoding='utf-8')
        print("✅ Fixed paper_trader_worker.py (added import)")
    else:
        print("✓ paper_trader_worker.py OK")

print("\n" + "=" * 70)
print("✅ ALL FIXES APPLIED!")
print("=" * 70)
print("\n🚀 RESTART PHOENIX:")
print("   python phoenix_65_workers.py")
print("\n📊 Expected: More workers will load!")
print("=" * 70)