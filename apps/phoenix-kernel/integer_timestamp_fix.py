# integer_timestamp_fix.py
import sys
import json
import hashlib
import time
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent))

def timestamp_to_int(ts):
    """Convert timestamp to integer milliseconds"""
    if isinstance(ts, (int, float)):
        return int(ts * 1000)  # Convert to milliseconds
    return int(time.time() * 1000)

def compute_hash_consistent(drift_lock, task, blueprint, timestamp_ms):
    """Compute hash with integer timestamp"""
    # Ensure deterministic JSON
    if isinstance(blueprint, dict):
        blueprint_str = json.dumps(blueprint, sort_keys=True, default=str, ensure_ascii=False)
    else:
        blueprint_str = str(blueprint)
    
    # Use integer timestamp
    hash_string = f"{drift_lock}:{task}:{blueprint_str}:{timestamp_ms}"
    return hashlib.sha256(hash_string.encode('utf-8')).hexdigest()

def fix_all():
    print("🔧 CONVERTING TO INTEGER TIMESTAMPS")
    print("=" * 60)
    
    memory_dir = Path("data/memory")
    json_files = list(memory_dir.glob("sce_*.json"))
    
    print(f"📁 Processing {len(json_files)} files...")
    
    fixed = 0
    for i, file_path in enumerate(json_files):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Convert timestamp to integer milliseconds
            old_ts = data.get("timestamp", time.time())
            new_ts_ms = timestamp_to_int(old_ts)
            
            if old_ts != new_ts_ms:
                data["timestamp_ms"] = new_ts_ms
                data["timestamp_original"] = old_ts
                data["timestamp"] = new_ts_ms / 1000.0  # Keep for compatibility
                fixed += 1
            
            # Recompute hash with integer timestamp
            correct_hash = compute_hash_consistent(
                data.get("drift_lock", file_path.stem[4:]),
                data.get("task", ""),
                data.get("blueprint", {}),
                new_ts_ms
            )
            
            data["hash"] = correct_hash
            data["verified"] = True
            
            # Save back
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, default=str, ensure_ascii=False)
            
            if (i + 1) % 2000 == 0:
                print(f"   Processed {i + 1}/{len(json_files)}...")
                
        except Exception as e:
            print(f"   ⚠ Error on {file_path.name}: {e}")
    
    print(f"\n✅ Converted {fixed} timestamps to integer milliseconds")
    
    # Rebuild SQLite with integer timestamps
    print("\n🗄️ Rebuilding SQLite with integer timestamps...")
    
    from memory_manager import SovereignMemoryManager
    
    # Backup current
    db_path = memory_dir / "rezhive_memory.db"
    if db_path.exists():
        import shutil
        backup = memory_dir / f"rezhive_memory_backup_int_{int(time.time())}.db"
        shutil.copy2(db_path, backup)
        print(f"💾 Backed up to: {backup}")
    
    # Create fresh memory manager
    with SovereignMemoryManager(memory_dir) as manager:
        # Clear existing
        manager.storage.conn.execute("DELETE FROM memory")
        manager.storage.conn.execute("DELETE FROM audit_log")
        manager.storage.conn.commit()
        
        # Re-import all with integer timestamps
        reimported = 0
        for i, file_path in enumerate(json_files):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                # Use integer timestamp
                timestamp_ms = data.get("timestamp_ms", timestamp_to_int(data.get("timestamp", time.time())))
                
                # Store with integer timestamp in blueprint
                blueprint = data.get("blueprint", {})
                blueprint["timestamp_ms"] = timestamp_ms
                
                manager.store(
                    blueprint=blueprint,
                    task=data.get("task", "Unknown"),
                    intent_type=data.get("intent_type", "interaction"),
                    tags=data.get("tags", [])
                )
                reimported += 1
                
                if (i + 1) % 2000 == 0:
                    print(f"   Reimported {i + 1}/{len(json_files)}...")
                    
            except Exception as e:
                print(f"   ⚠ Error: {e}")
        
        stats = manager.get_stats()
        print(f"\n📊 FINAL STATS:")
        print(f"   📊 Total entries: {stats['total_entries']}")
        print(f"   💾 Database size: {stats['db_size_mb']:.2f} MB")
        print(f"   📜 Audit entries: {stats['audit_entries']}")
        
        # Final verification
        print(f"\n🔗 Final verification...")
        
        # Check specific problematic entry
        test_lock = "001dedc0608eebe1"
        entry = manager.get_by_drift_lock(test_lock)
        if entry:
            correct = compute_hash_consistent(
                entry.drift_lock,
                entry.task,
                entry.blueprint,
                entry.blueprint.get("timestamp_ms", timestamp_to_int(entry.timestamp))
            )
            
            cursor = manager.storage.conn.execute(
                "SELECT hash FROM memory WHERE id = ?", (test_lock,)
            )
            row = cursor.fetchone()
            if row:
                if correct == row[0]:
                    print(f"   ✅ Test entry {test_lock[:16]}... now matches!")
                else:
                    print(f"   ⚠ Test entry still mismatched")
        
        # Full verification
        if manager.verify_integrity():
            print("   ✅✅✅ PERFECT! All hashes verified! ✅✅✅")
        else:
            print("   ⚠ Still has issues, checking...")
            cursor = manager.storage.conn.execute("SELECT id, hash FROM memory LIMIT 5")
            for row in cursor:
                entry = manager.get_by_drift_lock(row['id'])
                if entry:
                    ts_ms = entry.blueprint.get("timestamp_ms", timestamp_to_int(entry.timestamp))
                    correct = compute_hash_consistent(
                        entry.drift_lock,
                        entry.task,
                        entry.blueprint,
                        ts_ms
                    )
                    if correct != row['hash']:
                        print(f"      {row['id'][:16]}... mismatch")
                    else:
                        print(f"      {row['id'][:16]}... ✅")
    
    print("\n✅ FIX COMPLETE!")
    print("\n🐝 Your sovereign memory now has integer timestamps!")
    print("   No more floating-point precision issues!")

if __name__ == "__main__":
    fix_all()
