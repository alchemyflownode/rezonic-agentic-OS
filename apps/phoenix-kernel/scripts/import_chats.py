#!/usr/bin/env python3
"""
Import DeepSeek and Qwen chat exports into REZ HIVE memory
Based on actual structure:
- DeepSeek: {success, request_id, data: [...]}
- Qwen: list of conversations with mapping structure
"""

import json
import sqlite3
import hashlib
import time
from pathlib import Path
from datetime import datetime

# Paths
MEMORY_DB = Path("data/event_store/events.db")
DATA_DIR = Path("data/deepseek_qwen")

def create_drift_lock(data):
    """Create SCE drift lock for imported memories"""
    content = json.dumps(data, sort_keys=True, default=str)
    return hashlib.sha256(content.encode()).hexdigest()[:16]

def extract_messages_from_deepseek(item):
    """Extract messages from DeepSeek conversation structure"""
    messages = []
    
    # DeepSeek structure: data contains conversation objects
    if isinstance(item, dict):
        # Check for chat history structure
        if 'chat' in item and isinstance(item['chat'], dict):
            chat = item['chat']
            if 'history' in chat and isinstance(chat['history'], dict):
                history = chat['history']
                if 'messages' in history:
                    # Messages might be a list or dict
                    msg_data = history['messages']
                    if isinstance(msg_data, list):
                        for msg in msg_data:
                            if isinstance(msg, dict):
                                content = msg.get('content', '')
                                role = msg.get('role', 'user')
                                if content:
                                    messages.append({'content': content, 'role': role})
                    elif isinstance(msg_data, dict):
                        # If it's a dict, iterate through values
                        for msg in msg_data.values():
                            if isinstance(msg, dict):
                                content = msg.get('content', '')
                                role = msg.get('role', 'user')
                                if content:
                                    messages.append({'content': content, 'role': role})
        
        # Alternative: check for direct messages
        if 'messages' in item:
            if isinstance(item['messages'], list):
                for msg in item['messages']:
                    if isinstance(msg, dict):
                        content = msg.get('content', '')
                        role = msg.get('role', 'user')
                        if content:
                            messages.append({'content': content, 'role': role})
    
    return messages

def extract_messages_from_qwen(item):
    """Extract messages from Qwen conversation structure"""
    messages = []
    
    # Qwen structure: mapping contains message nodes
    if isinstance(item, dict) and 'mapping' in item:
        mapping = item['mapping']
        if isinstance(mapping, dict):
            # Iterate through mapping to find messages
            for node_id, node in mapping.items():
                if isinstance(node, dict):
                    # Check for message content
                    if 'message' in node and isinstance(node['message'], dict):
                        msg = node['message']
                        content = msg.get('content', '')
                        role = msg.get('role', 'user')
                        if content and role != 'system':  # Skip system messages
                            # Handle different content types
                            if isinstance(content, dict):
                                # Some messages have content as dict with parts
                                if 'parts' in content and isinstance(content['parts'], list):
                                    content = ' '.join(str(part) for part in content['parts'])
                                elif 'text' in content:
                                    content = content['text']
                                else:
                                    content = str(content)
                            elif isinstance(content, list):
                                content = ' '.join(str(c) for c in content)
                            
                            if content and len(str(content)) > 5:
                                messages.append({'content': str(content), 'role': role})
    
    return messages

def import_deepseek(file_path):
    """Import deepseekchat.json"""
    print(f"\n📥 Importing DeepSeek: {file_path.name} ({file_path.stat().st_size / 1024 / 1024:.1f} MB)")
    
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Navigate to the data array
    conversations = []
    if isinstance(data, dict) and 'data' in data and isinstance(data['data'], list):
        conversations = data['data']
    elif isinstance(data, list):
        conversations = data
    
    print(f"   Found {len(conversations)} conversations")
    
    conn = sqlite3.connect(MEMORY_DB)
    cursor = conn.cursor()
    imported = 0
    total_messages = 0
    
    for conv in conversations:
        messages = extract_messages_from_deepseek(conv)
        total_messages += len(messages)
        
        for msg in messages:
            try:
                blueprint = {
                    "protocol_version": "1.0.0",
                    "timestamp": datetime.now().isoformat(),
                    "intent": {
                        "task": str(msg['content'])[:500],
                        "user": msg['role'],
                        "source": "deepseek_import"
                    },
                    "dna": {
                        "imported": True,
                        "source_file": file_path.name,
                        "import_date": datetime.now().isoformat()
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
                    "deepseek.import",
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
    
    conn.commit()
    conn.close()
    print(f"\n   ✅ Imported {imported} messages from {total_messages} total")
    return imported

def import_qwen(file_path):
    """Import qwenchat.json"""
    print(f"\n📥 Importing Qwen: {file_path.name} ({file_path.stat().st_size / 1024 / 1024:.1f} MB)")
    
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    conversations = data if isinstance(data, list) else [data]
    print(f"   Found {len(conversations)} conversations")
    
    conn = sqlite3.connect(MEMORY_DB)
    cursor = conn.cursor()
    imported = 0
    total_messages = 0
    
    for conv in conversations:
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
                        "import_date": datetime.now().isoformat()
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
    
    conn.commit()
    conn.close()
    print(f"\n   ✅ Imported {imported} messages from {total_messages} total")
    return imported

def debug_sample():
    """Debug sample to see actual structure"""
    print("\n🔍 Debug: Sample DeepSeek conversation structure")
    deepseek_file = DATA_DIR / "deepseekchat.json"
    
    with open(deepseek_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    if 'data' in data and len(data['data']) > 0:
        sample = data['data'][0]
        print(f"Sample conversation keys: {list(sample.keys())}")
        if 'chat' in sample:
            print(f"Chat keys: {list(sample['chat'].keys())}")
            if 'history' in sample['chat']:
                print(f"History keys: {list(sample['chat']['history'].keys())}")
                if 'messages' in sample['chat']['history']:
                    msgs = sample['chat']['history']['messages']
                    print(f"Messages type: {type(msgs)}")
                    if isinstance(msgs, dict):
                        print(f"Message keys sample: {list(msgs.keys())[:3]}")
                    elif isinstance(msgs, list) and len(msgs) > 0:
                        print(f"First message: {msgs[0]}")
    
    print("\n🔍 Debug: Sample Qwen conversation structure")
    qwen_file = DATA_DIR / "qwenchat.json"
    
    with open(qwen_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    if isinstance(data, list) and len(data) > 0:
        sample = data[0]
        print(f"Sample conversation keys: {list(sample.keys())}")
        if 'mapping' in sample:
            mapping = sample['mapping']
            print(f"Mapping keys sample: {list(mapping.keys())[:3]}")
            first_key = list(mapping.keys())[0]
            print(f"First mapping node: {json.dumps(mapping[first_key], indent=2)[:500]}")

def main():
    print("🧠 REZ HIVE Chat Import Tool (Fixed)")
    print("=" * 60)
    
    # Debug to understand structure
    debug_sample()
    
    print("\n" + "=" * 60)
    choice = input("Proceed with import? (y/n): ")
    
    if choice.lower() != 'y':
        print("Import cancelled.")
        return
    
    total = 0
    
    deepseek_file = DATA_DIR / "deepseekchat.json"
    if deepseek_file.exists():
        total += import_deepseek(deepseek_file)
    
    qwen_file = DATA_DIR / "qwenchat.json"
    if qwen_file.exists():
        total += import_qwen(qwen_file)
    
    # Show results
    print("\n" + "=" * 60)
    print("📊 Memory Statistics:")
    
    conn = sqlite3.connect(MEMORY_DB)
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) FROM events WHERE type = 'deepseek.import'")
    deepseek_count = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM events WHERE type = 'qwen.import'")
    qwen_count = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM events")
    total_memories = cursor.fetchone()[0]
    
    conn.close()
    
    print(f"   DeepSeek memories: {deepseek_count:,}")
    print(f"   Qwen memories: {qwen_count:,}")
    print(f"   Total memories: {total_memories:,}")
    print(f"   New memories added: {deepseek_count + qwen_count:,}")
    
    print("\n✅ Import complete!")
    print("\nNow you can search:")
    print("   /memory/search 'deepseek'")
    print("   /memory/search 'qwen'")
    print("   /memory/search '[any content from your chats]'")

if __name__ == "__main__":
    main()