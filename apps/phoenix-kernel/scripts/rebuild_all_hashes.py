# rebuild_all_hashes.py
# Rebuild ALL hashes with consistent method

import sys
import json
import hashlib
import time
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent))
from memory_manager import SovereignMemoryManager

def compute_consistent_hash(entry):
    """Compute hash using consistent method"""
    # Get fields
    drift_lock = entry.get("drift_lock", "")
    task = entry.get("task", "")
    blueprint = entry.get("blueprint", {})
    timestamp = entry.get("timestamp", 0)
    
    # Sort keys for deterministic output
    blueprint_str = json.dumps(blueprint, sort_keys=True, default=str)
    
    # Build hash string
    hash_string = f"{drift_lock}:{task}:{blueprint_str}:{timestamp}"
    
    return hashlib.sha256(hash_string.encode()).hexdigest()

def rebuild_all_hashes():
    """Rebuild all hashes in JSON files and SQLite"""
    
    print("🔧 REBUILDING ALL HASHES")
    print("=" * 50)
    
    memory_dir = Path("data/memory")
    json_files = list(memory_dir.glob("sce_*.json"))
    
    print(f"📁 Found {len(json_files)} JSON files")
    
    # Step 1: Rebuild hashes in JSON files
    print("\n📝 Step 1: Updating JSON files...")
    fixed_count = 0
    
    for i, file_path in enumerate(json_files):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Compute correct hash
            correct_hash = compute_consistent_hash(data)
            data["hash"] = correct_hash
            data["verified"] = True
            
            # Save back
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, default=str)
            
            fixed_count += 1
            
            if (i + 1) % 1000 == 0:
                print(f"   Processed {i + 1}/{len(json_files)}...")
                
        except Exception as e:
            print(f"   ⚠ Error on {file_path.name}: {e}")
    
    print(f"✅ Updated {fixed_count} JSON files")
    
    # Step 2: Rebuild SQLite database
    print("\n🗄️ Step 2: Rebuilding SQLite database...")
    
    # Backup current DB
    db_path = memory_dir / "rezhive_memory.db"
    if db_path.exists():
        backup_path = memory_dir / f"rezhive_memory_backup_{int(time.time())}.db"
        import shutil
        shutil.copy2(db_path, backup_path)
        print(f"💾 Backed up to: {backup_path}")
    
    # Create new memory manager (will rebuild DB)
    with SovereignMemoryManager(memory_dir) as manager:
        print("✅ Rebuilding database...")
        
        # Re-import all JSON files
        reimported = 0
        for i, file_path in enumerate(json_files):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                # Store in new DB
                manager.store(
                    blueprint=data.get("blueprint", {}),
                    task=data.get("task", "Unknown"),
                    intent_type=data.get("intent_type", "interaction"),
                    tags=data.get("tags", [])
                )
                
                reimported += 1
                
                if (i + 1) % 1000 == 0:
                    print(f"   Reimported {i + 1}/{len(json_files)}...")
                    
            except Exception as e:
                print(f"   ⚠ Error reimporting {file_path.name}: {e}")
        
        # Get final stats
        stats = manager.get_stats()
        print(f"\n📊 DATABASE STATS:")
        print(f"   📊 Total entries: {stats['total_entries']}")
        print(f"   💾 Database size: {stats['db_size_mb']:.2f} MB")
        print(f"   📜 Audit entries: {stats['audit_entries']}")
        
        # Verify chain
        print(f"\n🔗 Verifying hash chain...")
        if manager.verify_integrity():
            print("   ✅ ALL GOOD — Hash chain verified!")
        else:
            print("   ⚠ Still has issues — checking...")
            # Find first problematic
            cursor = manager.storage.conn.execute(
                "SELECT id, hash FROM memory LIMIT 10"
            )
            for row in cursor:
                entry = manager.get_by_drift_lock(row['id'])
                if entry:
                    entry_dict = entry.to_dict()
                    correct = compute_consistent_hash(entry_dict)
                    if correct != row['hash']:
                        print(f"      Still mismatch: {row['id'][:16]}...")
                        break
    
    print("\n✅ Rebuild complete!")
    return 0

if __name__ == "__main__":
    sys.exit(rebuild_all_hashes())
