# verify_rezhive.py
# Verify Rezhive memory integrity

import sys
import os
from pathlib import Path

# Add parent directory to path
script_dir = Path(__file__).parent
parent_dir = script_dir.parent
sys.path.insert(0, str(parent_dir))

# Now import works
from memory_manager import SovereignMemoryManager

def main():
    print("🔍 Verifying Rezhive Memory Integrity...")
    print("=" * 50)

    memory_dir = parent_dir / "data" / "memory"
    if not memory_dir.exists():
        print("❌ Memory directory not found!")
        return 1

    with SovereignMemoryManager(memory_dir) as manager:
        stats = manager.get_stats()

        print(f"📊 Total Entries: {stats['total_entries']}")
        print(f"💾 Database Size: {stats['db_size_mb']:.2f} MB")
        print(f"📜 Audit Log: {stats['audit_entries']} entries")
        print(f"🔍 Vector Search: {'✅ Enabled' if stats['vector_enabled'] else '❌ Disabled'}")

        print("\n🔗 Verifying hash chain...")
        if manager.verify_integrity():
            print("✅ Hash chain verified — All entries intact!")
        else:
            print("❌ Hash chain verification FAILED!")
            return 1

        print("\n📈 Recent entries:")
        recent = manager.get_recent(limit=5)
        for e in recent:
            print(f"   🔒 {e.drift_lock[:16]}... | {e.intent_type} | {e.task[:40]}")

    print("\n✅ Verification complete!")
    return 0

if __name__ == "__main__":
    sys.exit(main())
