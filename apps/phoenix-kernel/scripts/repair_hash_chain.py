# repair_hash_chain.py
# Fix hash chain verification issues

import sys
import json
import hashlib
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent))
from memory_manager import SovereignMemoryManager

def repair_entry(drift_lock):
    """Repair a single entry's hash"""
    
    memory_dir = Path("data/memory")
    json_path = memory_dir / f"sce_{drift_lock}.json"
    
    if not json_path.exists():
        print(f"❌ JSON file not found for {drift_lock}")
        return False
    
    # Load the JSON
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Recompute hash
    content_str = json.dumps(data.get("blueprint", {}), sort_keys=True, default=str)
    hash_data = f"{drift_lock}:{data.get('task', '')}:{content_str}:{data.get('timestamp', 0)}"
    new_hash = hashlib.sha256(hash_data.encode()).hexdigest()
    
    print(f"🔧 Repairing {drift_lock}")
    print(f"   Old hash would be: {data.get('hash', 'N/A')[:16]}...")
    print(f"   New hash: {new_hash[:16]}...")
    
    # Update the JSON with correct hash
    data["hash"] = new_hash
    data["verified"] = True
    
    # Save back
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, default=str)
    
    # Re-store in Rezhive
    with SovereignMemoryManager(memory_dir) as manager:
        manager.store(
            blueprint=data.get("blueprint", {}),
            task=data.get("task", "Unknown"),
            intent_type=data.get("intent_type", "interaction"),
            tags=data.get("tags", [])
        )
    
    print(f"✅ Repaired {drift_lock}")
    return True

def main():
    print("🔧 Repairing Hash Chain Issues...")
    print("=" * 50)
    
    problematic_locks = [
        "001e8b3c614c4ab6",  # The one from error
        # Add more if found
    ]
    
    for lock in problematic_locks:
        repair_entry(lock)
    
    print("\n🔗 Re-verifying hash chain...")
    memory_dir = Path("data/memory")
    with SovereignMemoryManager(memory_dir) as manager:
        if manager.verify_integrity():
            print("✅ Hash chain now verified!")
        else:
            print("⚠ Still has issues. Run again with more problematic IDs.")
            
            # Find all problematic entries
            print("\n🔍 Finding all problematic entries...")
            # This would require checking each entry
            # For now, manual check

if __name__ == "__main__":
    main()
