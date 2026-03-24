#!/usr/bin/env python3
"""
Debug Qwen JSON structure to find where messages are stored
"""

import json
from pathlib import Path

DATA_DIR = Path("data/deepseek_qwen")
qwen_file = DATA_DIR / "qwenchat.json"

print("🔍 Debugging Qwen Structure")
print("=" * 60)

with open(qwen_file, 'r', encoding='utf-8') as f:
    data = json.load(f)

print(f"\n📁 File loaded: {qwen_file.name}")
print(f"📊 Root type: {type(data)}")
print(f"📊 Root length: {len(data) if isinstance(data, (list, dict)) else 'N/A'}")

if isinstance(data, list):
    print(f"📊 Number of conversations: {len(data)}")
    
    # Look at first conversation in detail
    first_conv = data[0]
    print(f"\n📄 First conversation keys: {list(first_conv.keys())}")
    
    # Check mapping structure
    if 'mapping' in first_conv:
        mapping = first_conv['mapping']
        print(f"\n📋 Mapping has {len(mapping)} nodes")
        print(f"   Mapping keys: {list(mapping.keys())[:10]}")
        
        # Look at each node type
        print("\n🔍 Node analysis:")
        for node_id, node in list(mapping.items())[:5]:
            print(f"\n   Node ID: {node_id}")
            print(f"   Node keys: {list(node.keys()) if isinstance(node, dict) else 'Not a dict'}")
            
            if isinstance(node, dict):
                # Check for message
                if 'message' in node:
                    msg = node['message']
                    print(f"   Message type: {type(msg)}")
                    if msg:
                        print(f"   Message keys: {list(msg.keys()) if isinstance(msg, dict) else 'Not a dict'}")
                        if isinstance(msg, dict):
                            print(f"   Message content: {json.dumps(msg, indent=4)[:500]}")
                    else:
                        print("   Message is null")
                else:
                    print("   No message in node")
                
                # Check for children
                if 'children' in node:
                    print(f"   Children: {node['children']}")
    
    # Also check if there's a direct messages array
    if 'messages' in first_conv:
        print(f"\n📋 Direct messages found: {type(first_conv['messages'])}")
        if isinstance(first_conv['messages'], list):
            print(f"   Number of messages: {len(first_conv['messages'])}")
            if len(first_conv['messages']) > 0:
                print(f"   First message: {json.dumps(first_conv['messages'][0], indent=2)[:500]}")

# Also check for any conversation with messages
print("\n" + "=" * 60)
print("🔍 Searching for any conversation with messages...")

for idx, conv in enumerate(data[:20]):  # Check first 20
    has_messages = False
    
    if 'mapping' in conv:
        mapping = conv['mapping']
        for node_id, node in mapping.items():
            if isinstance(node, dict) and 'message' in node and node['message']:
                has_messages = True
                print(f"\n✅ Found messages in conversation {idx}")
                print(f"   Conversation title: {conv.get('title', 'No title')}")
                print(f"   Node ID with message: {node_id}")
                msg = node['message']
                print(f"   Message role: {msg.get('role', 'Unknown')}")
                print(f"   Message content preview: {str(msg.get('content', ''))[:200]}")
                break
    
    if has_messages:
        break
else:
    print("\n❌ No messages found in first 20 conversations")

# Check if the file might be empty or malformed
print("\n" + "=" * 60)
print("🔍 Checking file structure more broadly...")

# Look for any content field anywhere
def find_content(obj, path=""):
    if isinstance(obj, dict):
        for key, value in obj.items():
            if key == 'content' and value:
                print(f"\n✅ Found content at: {path}.{key}")
                print(f"   Preview: {str(value)[:200]}")
                return True
            elif isinstance(value, (dict, list)):
                if find_content(value, f"{path}.{key}"):
                    return True
    elif isinstance(obj, list):
        for idx, item in enumerate(obj):
            if find_content(item, f"{path}[{idx}]"):
                return True
    return False

print("\nSearching entire file for 'content' fields...")
find_content(data)