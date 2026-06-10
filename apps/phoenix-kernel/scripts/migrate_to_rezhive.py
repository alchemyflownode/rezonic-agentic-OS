# migrate_to_rezhive.py
# Migrate existing JSON memory files to Rezhive SQLite

import sys
import json
import time
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent))
from memory_manager import SovereignMemoryManager

def migrate():
    print("🐝 Migrating existing memory to Rezhive...")
    print("=" * 50)
    
    # Paths
    memory_dir = Path("data/memory")
    json_files = list(memory_dir.glob("sce_*.json"))
    
    print(f"📁 Found {len(json_files)} JSON memory files")
    
    if not json_files:
        print("❌ No JSON files found to migrate!")
        return 1
    
    # Open memory manager
    with SovereignMemoryManager(memory_dir) as manager:
        print(f"✅ Connected to Rezhive database")
        
        # Get existing entries count before migration
        before_stats = manager.get_stats()
        print(f"📊 Before migration: {before_stats['total_entries']} entries")
        
        # Migrate each JSON file
        migrated = 0
        errors = 0
        
        for i, file_path in enumerate(json_files):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                # Extract data from JSON
                drift_lock = data.get("drift_lock") or file_path.stem[4:]
                task = data.get("task", "Unknown")
                intent_type = data.get("intent_type", "interaction")
                blueprint = data.get("blueprint", {})
                tags = data.get("tags", [])
                timestamp = data.get("timestamp", time.time())
                
                # Ensure blueprint has master_drift_lock
                if "master_drift_lock" not in blueprint:
                    blueprint["master_drift_lock"] = drift_lock
                
                # Store in Rezhive
                manager.store(
                    blueprint=blueprint,
                    task=task,
                    intent_type=intent_type,
                    tags=tags
                )
                
                migrated += 1
                
                # Progress indicator every 500 files
                if (i + 1) % 500 == 0:
                    print(f"   📦 Migrated {i + 1}/{len(json_files)}...")
                    
            except Exception as e:
                errors += 1
                if errors <= 10:  # Show first 10 errors only
                    print(f"   ⚠ Error migrating {file_path.name}: {e}")
        
        # Get final stats
        after_stats = manager.get_stats()
        
        print("\n" + "=" * 50)
        print("📊 MIGRATION COMPLETE")
        print("=" * 50)
        print(f"✅ Migrated: {migrated} files")
        print(f"❌ Errors: {errors}")
        print(f"📊 Total entries in Rezhive: {after_stats['total_entries']}")
        print(f"💾 Database size: {after_stats['db_size_mb']:.2f} MB")
        print(f"📜 Audit entries: {after_stats['audit_entries']}")
        
        # Verify integrity
        print("\n🔗 Verifying hash chain...")
        if manager.verify_integrity():
            print("✅ Hash chain verified — All entries intact!")
        else:
            print("⚠ Hash chain verification had issues.")
        
        print("\n📈 Sample of migrated memories:")
        recent = manager.get_recent(limit=5)
        for e in recent:
            print(f"   🔒 {e.drift_lock[:16]}... | {e.intent_type} | {e.task[:50]}")
    
    print("\n✅ Migration complete!")
    return 0

if __name__ == "__main__":
    sys.exit(migrate())
