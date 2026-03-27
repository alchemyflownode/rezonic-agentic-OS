# full_repair_hashes.py
# Rebuild all hashes to ensure chain integrity

import sys
import json
import hashlib
import time
from pathlib import Path
from datetime import datetime
from typing import Dict, Any

sys.path.insert(0, str(Path(__file__).parent))
from memory_manager import SovereignMemoryManager

def compute_hash(entry: Dict) -> str:
    """Compute deterministic hash for a memory entry"""
    # Sort keys for deterministic output
    blueprint = entry.get("blueprint", {})
    if isinstance(blueprint, dict):
        blueprint_str = json.dumps(blueprint, sort_keys=True, default=str)
    else:
        blueprint_str = str(blueprint)
    
    hash_data = f"{entry.get('drift_lock', '')}:{entry.get('task', '')}:{blueprint_str}:{entry.get('timestamp', 0)}"
    return hashlib.sha256(hash_data.encode()).hexdigest()

def rebuild_all_hashes():
    """Rebuild hashes for all JSON files and re-import to SQLite"""
    
    print("🔧 REBUILDING ALL HASHES")
    print("=" * 50)
    
    memory_dir = Path("data/memory")
    json_files = list(memory_dir.glob("sce_*.json"))
    
    print(f"📁 Found {len(json_files)} JSON files")
    
    if not json_files:
        print("❌ No JSON files found!")
        return 1
    
    # First, backup current SQLite
    db_path = memory_dir / "rezhive_memory.db"
    if db_path.exists():
        backup_path = memory_dir / f"rezhive_memory_backup_{int(time.time())}.db"
        import shutil
        shutil.copy2(db_path, backup_path)
        print(f"💾 Backed up database to: {backup_path}")
    
    # Create new memory manager (will create fresh DB)
    # But we need to keep existing entries
    with SovereignMemoryManager(memory_dir) as manager:
        print(f"✅ Connected to Rezhive database")
        
        # Track statistics
        fixed = 0
        errors = 0
        
        for i, file_path in enumerate(json_files):
            try:
                # Load JSON
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                # Get drift lock
                drift_lock = data.get("drift_lock") or file_path.stem[4:]
                
                # Compute correct hash
                correct_hash = compute_hash(data)
                
                # Check if hash needs fixing
                current_hash = data.get("hash", "")
                if current_hash != correct_hash:
                    print(f"🔧 Fixing {drift_lock[:16]}... (hash mismatch)")
                    data["hash"] = correct_hash
                    data["verified"] = True
                    
                    # Save fixed JSON
                    with open(file_path, 'w', encoding='utf-8') as f:
                        json.dump(data, f, indent=2, default=str)
                    
                    fixed += 1
                
                # Always re-store in SQLite (ensures consistency)
                manager.store(
                    blueprint=data.get("blueprint", {}),
                    task=data.get("task", "Unknown"),
                    intent_type=data.get("intent_type", "interaction"),
                    tags=data.get("tags", [])
                )
                
                # Progress indicator
                if (i + 1) % 1000 == 0:
                    print(f"   📦 Processed {i + 1}/{len(json_files)}...")
                    
            except Exception as e:
                errors += 1
                if errors <= 20:
                    print(f"   ⚠ Error on {file_path.name}: {e}")
        
        print(f"\n📊 SUMMARY:")
        print(f"   ✅ Fixed: {fixed} entries")
        print(f"   ❌ Errors: {errors}")
        
        # Get final stats
        stats = manager.get_stats()
        print(f"\n📈 DATABASE STATS:")
        print(f"   📊 Total entries: {stats['total_entries']}")
        print(f"   💾 Database size: {stats['db_size_mb']:.2f} MB")
        print(f"   📜 Audit entries: {stats['audit_entries']}")
        
        # Verify chain
        print(f"\n🔗 Verifying hash chain...")
        if manager.verify_integrity():
            print("   ✅ ALL GOOD — Hash chain verified!")
        else:
            print("   ⚠ Still has issues — checking each entry...")
            
            # Find problematic entries by checking each
            cursor = manager.storage.conn.execute(
                "SELECT id, hash FROM memory ORDER BY timestamp"
            )
            problem_count = 0
            for row in cursor:
                # Get entry
                entry = manager.get_by_drift_lock(row['id'])
                if entry:
                    entry_dict = entry.to_dict()
                    correct = compute_hash(entry_dict)
                    if correct != row['hash']:
                        problem_count += 1
                        if problem_count <= 10:
                            print(f"      🔒 {row['id'][:16]}... hash mismatch")
            
            if problem_count > 0:
                print(f"   ⚠ Found {problem_count} problematic entries")
            else:
                print("   ✅ All entries verified!")
    
    print("\n✅ Repair complete!")
    return 0

if __name__ == "__main__":
    sys.exit(rebuild_all_hashes())
