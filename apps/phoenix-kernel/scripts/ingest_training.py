# ingest_training.py
# Use Harvester Worker to ingest training blueprints

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

# Import our components
from memory_manager import SovereignMemoryManager

def ingest_conversation_blueprints():
    """Ingest our conversation blueprints into Rezhive"""
    
    print("🐝 Ingesting Conversation Training Blueprints...")
    print("=" * 60)
    
    # Connect to Rezhive
    memory_dir = Path("data/memory")
    with SovereignMemoryManager(memory_dir) as manager:
        stats = manager.get_stats()
        print(f"✅ Connected to Rezhive ({stats['total_entries']} existing entries)")
        
        # Blueprints from our conversation
        blueprints = [
            {
                "name": "Sovereign Memory Architecture",
                "content": "SQLite + vector search = sovereign memory. Event sourcing for immutable audit trails. Hash chain for cryptographic verification. Single file = complete portability.",
                "tags": ["memory", "architecture", "sqlite", "sovereign"],
                "metadata": {"source": "AI Conversation", "date": "2026-03-27"}
            },
            {
                "name": "Hash Chain Integrity Solution",
                "content": "Floating-point timestamps cause hash mismatches. Integer milliseconds solve precision issues. Unified hash computation across JSON and SQLite. All entries verified with consistent method.",
                "tags": ["security", "hash", "integrity", "timestamp"],
                "metadata": {"source": "AI Conversation", "date": "2026-03-27"}
            },
            {
                "name": "Training Bridge Architecture",
                "content": "Harvester Worker ingests chat exports. Rezhive stores as verified blueprints. Every conversation becomes permanent training. Hive cross-pollination shares anonymized wisdom.",
                "tags": ["training", "bridge", "harvester", "hive"],
                "metadata": {"source": "AI Conversation", "date": "2026-03-27"}
            },
            {
                "name": "Phoenix OS Complete Sovereign Stack",
                "content": "Memory Layer: Rezhive (verified blueprints). Worker Layer: 70+ specialized deterministic workers. Constitutional Layer: Bytecode-level enforcement. Training Layer: Harvester + Bridge. Hive Layer: Cross-pollination with privacy.",
                "tags": ["architecture", "sovereign", "complete", "stack"],
                "metadata": {"source": "AI Conversation", "date": "2026-03-27"}
            },
            {
                "name": "Harvester Worker Integration",
                "content": "Harvester Worker reads JSON exports from ChatGPT/Claude. Parses conversations into structured format. Stores to memory bus → Rezhive bridge. Creates searchable, verified training blueprints.",
                "tags": ["harvester", "integration", "chat", "export"],
                "metadata": {"source": "AI Conversation", "date": "2026-03-27"}
            }
        ]
        
        # Store each blueprint
        stored = []
        for bp in blueprints:
            drift_lock = manager.store(
                blueprint=bp,
                task=bp["name"],
                intent_type="training",
                tags=bp["tags"]
            )
            stored.append(drift_lock)
            print(f"   ✅ Stored: {bp['name']} → {drift_lock[:16]}...")
        
        # Get updated stats
        stats = manager.get_stats()
        print(f"\n📊 REZHIVE STATS AFTER INGEST:")
        print(f"   📊 Total entries: {stats['total_entries']}")
        print(f"   💾 Database size: {stats['db_size_mb']:.2f} MB")
        print(f"   📜 Audit entries: {stats['audit_entries']}")
        
        # Verify integrity
        print(f"\n🔗 Verifying hash chain...")
        if manager.verify_integrity():
            print("   ✅✅✅ ALL VERIFIED — New blueprints intact! ✅✅✅")
        else:
            print("   ⚠ Verification had issues")

if __name__ == "__main__":
    ingest_conversation_blueprints()
