# diagnose_hash_root_cause.py
import sys
import json
import hashlib
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from memory_manager import SovereignMemoryManager

def compute_detailed_hash(drift_lock, task, blueprint, timestamp):
    """Compute hash exactly as memory_manager does"""
    blueprint_str = json.dumps(blueprint, sort_keys=True, default=str)
    hash_string = f"{drift_lock}:{task}:{blueprint_str}:{timestamp}"
    return hashlib.sha256(hash_string.encode()).hexdigest()

def diagnose():
    print("🔍 DIAGNOSING HASH MISMATCH ROOT CAUSE")
    print("=" * 60)
    
    memory_dir = Path("data/memory")
    test_lock = "001dedc0608eebe1"  # First problematic one
    
    # 1. Check JSON file
    json_path = memory_dir / f"sce_{test_lock}.json"
    if json_path.exists():
        with open(json_path, 'r') as f:
            json_data = json.load(f)
        
        print(f"\n📁 JSON File: {json_path.name}")
        print(f"   Task: {json_data.get('task', 'N/A')[:50]}")
        print(f"   Intent: {json_data.get('intent_type', 'N/A')}")
        print(f"   Timestamp: {json_data.get('timestamp', 'N/A')}")
        
        # Compute hash from JSON
        computed = compute_detailed_hash(
            json_data.get('drift_lock', test_lock),
            json_data.get('task', ''),
            json_data.get('blueprint', {}),
            json_data.get('timestamp', 0)
        )
        stored = json_data.get('hash', 'N/A')
        
        print(f"\n   📦 Computed hash: {computed[:16]}...")
        print(f"   💾 Stored hash:   {stored[:16]}...")
        
        if computed != stored:
            print(f"   ⚠ MISMATCH!")
            
            # Check what's different
            print(f"\n   🔍 Analyzing mismatch...")
            print(f"   drift_lock: {json_data.get('drift_lock', test_lock)}")
            print(f"   task length: {len(json_data.get('task', ''))}")
            print(f"   blueprint keys: {list(json_data.get('blueprint', {}).keys())[:5]}")
            print(f"   timestamp: {json_data.get('timestamp', 0)}")
    
    # 2. Check SQLite
    with SovereignMemoryManager(memory_dir) as manager:
        entry = manager.get_by_drift_lock(test_lock)
        if entry:
            print(f"\n🗄️ SQLite Entry:")
            print(f"   Task: {entry.task[:50]}")
            print(f"   Intent: {entry.intent_type}")
            print(f"   Timestamp: {entry.timestamp}")
            
            # Get SQLite hash
            cursor = manager.storage.conn.execute(
                "SELECT hash FROM memory WHERE id = ?", (test_lock,)
            )
            row = cursor.fetchone()
            if row:
                sql_hash = row[0]
                print(f"   SQLite hash: {sql_hash[:16]}...")
    
    print("\n" + "=" * 60)
    print("💡 Root cause: The hash may be computed differently")
    print("   between storage and verification. Let's fix that.")

if __name__ == "__main__":
    diagnose()
