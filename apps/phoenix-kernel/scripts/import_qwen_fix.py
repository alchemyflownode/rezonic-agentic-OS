#!/usr/bin/env python3
"""
Fixed Qwen Import - Messages are in fragments array
"""

import json
import sqlite3
import hashlib
import time
from pathlib import Path
from datetime import datetime

MEMORY_DB = Path("data/event_store/events.db")
DATA_DIR = Path("data/deepseek_qwen")

def create_drift_lock(data):
    content = json.dumps(data, sort_keys=True, default=str)
    return hashlib.sha256(content.encode()).hexdigest()[:16]

def extract_messages_from_qwen(item):
    """Extract messages from Qwen structure - messages in fragments array"""
    messages = []
    
    if isinstance(item, dict) and 'mapping' in item:
        mapping = item['mapping']
        
        for node_id, node in mapping.items():
            if isinstance(node, dict) and 'message' in node:
                msg = node['message']
                if isinstance(msg, dict) and 'fragments' in msg:
                    fragments = msg['fragments']
                    if isinstance(fragments, list):
                        for fragment in fragments:
                            if isinstance(fragment, dict):
                                # Get content and type (REQUEST/RESPONSE)
                                content = fragment.get('content', '')
                                frag_type = fragment.get('type', '')
                                
                                # Convert type to role (user/assistant)
                                role = 'user' if frag_type == 'REQUEST' else 'assistant'
                                
                                if content and len(content) > 5:
                                    messages.append({
                                        'content': content,
                                        'role': role,
                                        'node_id': node_id
                                    })
    
    return messages

def import_qwen(file_path):
    print(f"\n📥 Importing Qwen: {file_path.name} ({file_path.stat().st_size / 1024 / 1024:.1f} MB)")
    
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    conversations = data if isinstance(data, list) else [data]
    print(f"   Found {len(conversations)} conversations")
    
    conn = sqlite3.connect(MEMORY_DB)
    cursor = conn.cursor()
    imported = 0
    total_messages = 0
    
    for idx, conv in enumerate(conversations):
        messages = extract_messages_from_qwen(conv)
        total_messages += len(messages)
        
        for msg in messages:
            try:
                blueprint = {
                    "protocol_version": "1.0.0",
                    "timestamp": datetime.now().isoformat(),
                    "intent": {
                        "task": str(msg['content'])[:500],
                        "user": msg['role'],
                        "source": "qwen_import"
                    },
                    "dna": {
                        "imported": True,
                        "source_file": file_path.name,
                        "import_date": datetime.now().isoformat(),
                        "conversation_title": conv.get('title', 'Untitled')
                    },
                    "execution": {
                        "imported_content": str(msg['content'])
                    }
                }
                
                drift_lock = create_drift_lock(blueprint)
                
                cursor.execute("""
                    INSERT OR REPLACE INTO events 
                    (vera_proof, type, source, payload, timestamp, previous_hash, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    drift_lock,
                    "qwen.import",
                    "import_script",
                    json.dumps(blueprint),
                    time.time(),
                    "",
                    time.time()
                ))
                
                imported += 1
                if imported % 100 == 0:
                    print(f"   Imported {imported} messages...", end='\r')
                    
            except Exception as e:
                continue
        
        # Show progress every 50 conversations
        if (idx + 1) % 50 == 0:
            print(f"\n   Processed {idx + 1}/{len(conversations)} conversations, found {total_messages} messages so far...")
    
    conn.commit()
    conn.close()
    print(f"\n   ✅ Imported {imported} messages from {total_messages} total")
    return imported

def main():
    print("🧠 Qwen Import - Fixed for fragments structure")
    print("=" * 60)
    
    qwen_file = DATA_DIR / "qwenchat.json"
    if qwen_file.exists():
        count = import_qwen(qwen_file)
        
        print("\n" + "=" * 60)
        print("📊 Updated Memory Statistics:")
        
        conn = sqlite3.connect(MEMORY_DB)
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM events WHERE type = 'deepseek.import'")
        deepseek_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM events WHERE type = 'qwen.import'")
        qwen_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM events")
        total = cursor.fetchone()[0]
        
        conn.close()
        
        print(f"   DeepSeek memories: {deepseek_count:,}")
        print(f"   Qwen memories: {qwen_count:,}")
        print(f"   Total memories: {total:,}")
        print(f"   New memories added: {qwen_count:,}")
        
        print("\n✅ Import complete!")
        print("\nNow you can search:")
        print("   /memory/search 'deepseek'")
        print("   /memory/search 'qwen'")
        print("   /memory/search '[any content from your chats]'")
    else:
        print("❌ Qwen file not found")

if __name__ == "__main__":
    main()