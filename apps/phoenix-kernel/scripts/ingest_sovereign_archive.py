#!/usr/bin/env python3
"""
Ingest your sovereign archive files into REZ HIVE memory
Run: python ingest_sovereign_archive.py
"""

import json
import sqlite3
import hashlib
import time
import os
from pathlib import Path
from datetime import datetime

# Paths
ARCHIVE_PATH = Path("D:/Rezonic_Agentic/apps/phoenix-kernel/data/sovereign_archives/alchemyflow/Google AI Studio")
MEMORY_DB = Path("data/event_store/events.db")

def create_drift_lock(data):
    """Create SCE drift lock"""
    content = json.dumps(data, sort_keys=True, default=str)
    return hashlib.sha256(content.encode()).hexdigest()[:16]

def ingest_file(file_path):
    """Ingest a single file into memory"""
    try:
        # Read file content
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Skip empty files
        if not content.strip():
            return 0
        
        # Create blueprint
        blueprint = {
            "protocol_version": "1.0.0",
            "timestamp": datetime.now().isoformat(),
            "intent": {
                "task": f"File: {file_path.name}",
                "source": "sovereign_archive",
                "type": "file_ingest"
            },
            "dna": {
                "file_name": file_path.name,
                "file_path": str(file_path),
                "file_size": len(content),
                "file_type": file_path.suffix,
                "import_date": datetime.now().isoformat(),
                "source_archive": "Google AI Studio"
            },
            "execution": {
                "content": content[:10000],  # Store first 10k chars
                "full_content": content,      # Full content for search
                "note": "Imported from sovereign archive"
            }
        }
        
        drift_lock = create_drift_lock(blueprint)
        
        # Connect to database
        conn = sqlite3.connect(MEMORY_DB)
        cursor = conn.cursor()
        
        # Store in database
        cursor.execute("""
            INSERT OR REPLACE INTO events 
            (vera_proof, type, source, payload, timestamp, previous_hash, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            drift_lock,
            "sovereign.import",
            "archive_ingest",
            json.dumps(blueprint),
            time.time(),
            "",
            time.time()
        ))
        
        conn.commit()
        conn.close()
        return 1
        
    except Exception as e:
        print(f"   ❌ Error ingesting {file_path.name}: {e}")
        return 0

def main():
    print("🏛️ REZ HIVE Sovereign Archive Ingestion")
    print("=" * 60)
    
    # Check if archive exists
    if not ARCHIVE_PATH.exists():
        print(f"❌ Archive path not found: {ARCHIVE_PATH}")
        print("\n📁 Creating archive directory...")
        ARCHIVE_PATH.mkdir(parents=True, exist_ok=True)
        print(f"   Created: {ARCHIVE_PATH}")
        print("\n⚠️  Please add your files to this folder and run again.")
        return
    
    # Find all files to ingest
    file_types = ['.txt', '.md', '.json', '.ts', '.js', '.yaml', '.yml', '.py', '.html', '.css']
    files = []
    
    for ext in file_types:
        files.extend(ARCHIVE_PATH.rglob(f"*{ext}"))
    
    print(f"\n📁 Archive path: {ARCHIVE_PATH}")
    print(f"📄 Found {len(files)} files to ingest")
    
    if len(files) == 0:
        print("\n⚠️  No files found. Please add your files to:")
        print(f"   {ARCHIVE_PATH}")
        return
    
    # Show sample files
    print("\n📋 Sample files:")
    for f in files[:10]:
        print(f"   • {f.name} ({f.stat().st_size} bytes)")
    
    if len(files) > 10:
        print(f"   ... and {len(files) - 10} more")
    
    print("\n" + "=" * 60)
    choice = input("Proceed with ingestion? (y/n): ")
    
    if choice.lower() != 'y':
        print("Ingestion cancelled.")
        return
    
    # Ingest files
    print("\n📥 Ingesting files...")
    total = 0
    ingested = 0
    
    for i, file_path in enumerate(files):
        total += 1
        print(f"   [{i+1}/{len(files)}] {file_path.name}...", end=' ')
        result = ingest_file(file_path)
        if result:
            ingested += 1
            print("✅")
        else:
            print("⏭️")
    
    # Show results
    print("\n" + "=" * 60)
    print("📊 Ingestion Results:")
    print(f"   Files processed: {total}")
    print(f"   Successfully ingested: {ingested}")
    print(f"   Failed: {total - ingested}")
    
    # Check memory stats
    conn = sqlite3.connect(MEMORY_DB)
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) FROM events WHERE type = 'sovereign.import'")
    imported_count = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM events")
    total_memories = cursor.fetchone()[0]
    
    conn.close()
    
    print(f"\n📈 Updated Memory Statistics:")
    print(f"   Sovereign archive memories: {imported_count:,}")
    print(f"   Total memories: {total_memories:,}")
    
    print("\n✅ Ingestion complete!")
    print("\nNow you can search your sovereign archive:")
    print("   /memory/search 'sovereign'")
    print("   /memory/search 'fleet protocol'")
    print("   /memory/search '[any project name]'")

if __name__ == "__main__":
    main()