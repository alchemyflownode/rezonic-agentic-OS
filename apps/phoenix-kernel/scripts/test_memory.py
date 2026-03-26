# AUTO-FIXED IMPORT PATH
import sys
from pathlib import Path
_workers_dir = Path(__file__).parent.resolve()
if str(_workers_dir) not in sys.path:
    sys.path.insert(0, str(_workers_dir))
# END AUTO-FIX
﻿# test_memory.py
# Test the new Sovereign Memory system

import asyncio
from pathlib import Path
from memory_manager import SovereignMemoryManager, MemoryCommandHandler

async def test():
    print("🧪 Testing Sovereign Memory System")
    print("="*50)
    
    memory_dir = Path("data/memory")
    manager = SovereignMemoryManager(memory_dir)
    
    print(f"📊 Loaded {manager.get_stats()['total_entries']} entries")
    print(f"📈 By intent: {manager.get_stats()['by_intent_type']}")
    
    # Test search
    results = manager.search("code", limit=5)
    print(f"\n🔍 Found {len(results)} results for 'code'")
    
    for r in results[:3]:
        print(f"   • {r.drift_lock[:12]}...: {r.task[:50]}")
    
    print("\n✅ Memory system working!")

if __name__ == "__main__":
    asyncio.run(test())
