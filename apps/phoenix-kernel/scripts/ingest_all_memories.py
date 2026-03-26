#!/usr/bin/env python3
"""
Ingest your ChatGPT exports and sovereign archives into REZ HIVE memory
Run: python ingest_all_memories.py
"""

import json
import sqlite3
import hashlib
import time
import os
from pathlib import Path
from datetime import datetime

# ============================================================================
# CONFIGURATION
# ============================================================================

# Paths
SOVEREIGN_ARCHIVE_PATH = Path("D:/Rezonic_Agentic/apps/phoenix-kernel/data/sovereign_archives/alchemyflow/Google AI Studio")
CHATGPT_PATH = Path("D:/Rezonic_Agentic/apps/phoenix-kernel/data/deepseek_qwen/chatgpt/chatgpt")
MEMORY_DB = Path("data/event_store/events.db")

# Supported file types
FILE_TYPES = ['.txt', '.md', '.json', '.ts', '.js', '.yaml', '.yml', '.py', '.html', '.css']

# ============================================================================
# UTILITIES
# ============================================================================

def create_drift_lock(data):
    """Create SCE drift lock"""
    content = json.dumps(data, sort_keys=True, default=str)
    return hashlib.sha256(content.encode()).hexdigest()[:16]

def store_in_memory(blueprint, event_type, source):
    """Store blueprint in memory database"""
    try:
        drift_lock = create_drift_lock(blueprint)
        
        conn = sqlite3.connect(MEMORY_DB)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT OR REPLACE INTO events 
            (vera_proof, type, source, payload, timestamp, previous_hash, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            drift_lock,
            event_type,
            source,
            json.dumps(blueprint),
            time.time(),
            "",
            time.time()
        ))
        
        conn.commit()
        conn.close()
        return drift_lock
        
    except Exception as e:
        print(f"   ❌ Error storing: {e}")
        return None

def ingest_file(file_path, source_type, metadata):
    """Ingest a single file into memory"""
    try:
        # Read file content
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Skip empty files
        if not content.strip():
            return 0
        
        # Try to parse JSON if applicable
        parsed_content = None
        if file_path.suffix == '.json':
            try:
                parsed_content = json.loads(content)
            except:
                pass
        
        # Create blueprint
        blueprint = {
            "protocol_version": "1.0.0",
            "timestamp": datetime.now().isoformat(),
            "intent": {
                "task": f"File: {file_path.name}",
                "source": source_type,
                "type": "file_ingest"
            },
            "dna": {
                "file_name": file_path.name,
                "file_path": str(file_path),
                "file_size": len(content),
                "file_type": file_path.suffix,
                "import_date": datetime.now().isoformat(),
                **metadata
            },
            "execution": {
                "content": content[:10000] if not parsed_content else json.dumps(parsed_content, indent=2)[:10000],
                "full_content": content[:50000] if len(content) > 50000 else content,
                "parsed_data": parsed_content if parsed_content else None,
                "note": f"Imported from {source_type}"
            }
        }
        
        drift_lock = store_in_memory(blueprint, "memory.import", source_type)
        return 1 if drift_lock else 0
        
    except Exception as e:
        print(f"   ❌ Error ingesting {file_path.name}: {e}")
        return 0

def ingest_chatgpt_conversations(conv_file):
    """Ingest ChatGPT conversation files (special handling)"""
    try:
        print(f"\n📖 Processing: {conv_file.name}")
        
        with open(conv_file, 'r', encoding='utf-8') as f:
            conversations = json.load(f)
        
        print(f"   Found {len(conversations)} conversations")
        ingested = 0
        
        for conv in conversations:
            try:
                title = conv.get('title', 'Untitled')
                create_time = conv.get('create_time', 0)
                messages = conv.get('messages', [])
                
                # Format messages preview
                message_preview = []
                for msg in messages[:20]:
                    if isinstance(msg, dict):
                        role = msg.get('author', {}).get('role', 'unknown')
                        content = msg.get('content', {}).get('parts', [''])[0]
                        if content:
                            message_preview.append({
                                'role': role,
                                'content': content[:300]
                            })
                
                # Create blueprint
                blueprint = {
                    "protocol_version": "1.0.0",
                    "timestamp": datetime.now().isoformat(),
                    "intent": {
                        "task": title,
                        "source": "chatgpt_export",
                        "type": "conversation"
                    },
                    "dna": {
                        "file_name": conv_file.name,
                        "title": title,
                        "create_time": create_time,
                        "message_count": len(messages),
                        "import_date": datetime.now().isoformat()
                    },
                    "execution": {
                        "messages_preview": message_preview[:10],
                        "first_message": message_preview[0]['content'][:500] if message_preview else "",
                        "note": "Imported from ChatGPT export"
                    }
                }
                
                drift_lock = store_in_memory(blueprint, "chatgpt.conversation", "chatgpt_export")
                if drift_lock:
                    ingested += 1
                    if ingested % 10 == 0:
                        print(f"      ... {ingested} conversations imported")
                
            except Exception as e:
                print(f"   ❌ Error importing conversation: {e}")
        
        print(f"   ✅ Imported {ingested}/{len(conversations)} conversations")
        return ingested
        
    except Exception as e:
        print(f"   ❌ Error processing {conv_file.name}: {e}")
        return 0

def scan_and_ingest():
    """Main scanning and ingestion function"""
    
    print("🏛️ REZ HIVE - Complete Memory Ingestion")
    print("=" * 60)
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    total_ingested = 0
    
    # ========================================================================
    # PART 1: Sovereign Archives
    # ========================================================================
    
    print("\n📁 SCANNING SOVEREIGN ARCHIVES...")
    print("-" * 40)
    
    if SOVEREIGN_ARCHIVE_PATH.exists():
        # Find all files
        files = []
        for ext in FILE_TYPES:
            files.extend(SOVEREIGN_ARCHIVE_PATH.rglob(f"*{ext}"))
        
        print(f"   Path: {SOVEREIGN_ARCHIVE_PATH}")
        print(f"   Found {len(files)} files")
        
        if files:
            print("\n   Sample files:")
            for f in files[:10]:
                print(f"      • {f.name} ({f.stat().st_size:,} bytes)")
            
            print(f"\n   Ingesting...")
            for i, file_path in enumerate(files):
                print(f"      [{i+1}/{len(files)}] {file_path.name}...", end=' ')
                result = ingest_file(file_path, "sovereign_archive", {
                    "source_archive": "Google AI Studio",
                    "archive_type": "sovereign"
                })
                if result:
                    total_ingested += 1
                    print("✅")
                else:
                    print("⏭️")
    
    # ========================================================================
    # PART 2: ChatGPT Exports
    # ========================================================================
    
    print("\n📁 SCANNING CHATGPT EXPORTS...")
    print("-" * 40)
    
    if CHATGPT_PATH.exists():
        # Find conversation files
        conv_files = sorted(CHATGPT_PATH.glob("conversations-*.json"))
        
        print(f"   Path: {CHATGPT_PATH}")
        print(f"   Found {len(conv_files)} conversation files")
        
        # Show file sizes
        for f in conv_files:
            size_mb = f.stat().st_size / 1024 / 1024
            print(f"      • {f.name} ({size_mb:.1f} MB)")
        
        print(f"\n   Ingesting conversations...")
        for conv_file in conv_files:
            ingested = ingest_chatgpt_conversations(conv_file)
            total_ingested += ingested
        
        # Also ingest metadata files
        metadata_files = ['export_manifest.json', 'user.json', 'user_settings.json']
        for meta_file in metadata_files:
            meta_path = CHATGPT_PATH / meta_file
            if meta_path.exists():
                print(f"\n   Ingesting metadata: {meta_file}")
                result = ingest_file(meta_path, "chatgpt_metadata", {
                    "source_archive": "ChatGPT Export",
                    "archive_type": "metadata"
                })
                if result:
                    total_ingested += 1
    
    # ========================================================================
    # SUMMARY
    # ========================================================================
    
    print("\n" + "=" * 60)
    print("📊 INGESTION SUMMARY")
    print("=" * 60)
    
    # Get memory stats
    conn = sqlite3.connect(MEMORY_DB)
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) FROM events")
    total_memories = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM events WHERE type = 'sovereign.import'")
    sovereign_count = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM events WHERE type = 'chatgpt.conversation'")
    chatgpt_count = cursor.fetchone()[0]
    
    conn.close()
    
    print(f"\n📈 Updated Memory Statistics:")
    print(f"   Total memories: {total_memories:,}")
    print(f"   Sovereign archives: {sovereign_count:,}")
    print(f"   ChatGPT conversations: {chatgpt_count:,}")
    print(f"   New entries added: {total_ingested}")
    
    print("\n✅ Ingestion complete!")
    print("\n🔍 Now you can search your memories:")
    print("   /memory search 'chatgpt'")
    print("   /memory search 'sovereign'")
    print("   /memory search 'fleet protocol'")
    print("   /memory search '[any topic]'")
    
    print("\n🎯 Quick stats:")
    print(f"   Sovereign files: ~{sovereign_count} entries")
    print(f"   ChatGPT conversations: {chatgpt_count} entries")
    print(f"   Total: {total_memories:,} memories")

def main():
    try:
        scan_and_ingest()
    except KeyboardInterrupt:
        print("\n\n⏸️  Ingestion cancelled by user")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()