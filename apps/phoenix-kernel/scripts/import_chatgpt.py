# import_chatgpt.py
"""Import ChatGPT conversations into Sovereign Memory"""

import json
import asyncio
import httpx
from pathlib import Path
from datetime import datetime

async def import_chatgpt():
    """Import all ChatGPT conversations"""
    
    chatgpt_dir = Path(r"D:\Rezonic_Agentic\apps\phoenix-kernel\data\deepseek_qwen\chatgpt\chatgpt")
    
    # Get all conversation files
    conv_files = sorted(chatgpt_dir.glob("conversations-*.json"))
    
    print(f"📁 Found {len(conv_files)} conversation files")
    
    total_imported = 0
    
    for conv_file in conv_files:
        print(f"\n📖 Reading: {conv_file.name} ({conv_file.stat().st_size / 1024 / 1024:.1f} MB)")
        
        with open(conv_file, 'r', encoding='utf-8') as f:
            conversations = json.load(f)
        
        print(f"   Found {len(conversations)} conversations")
        
        for conv in conversations:
            try:
                # Extract conversation data
                title = conv.get('title', 'Untitled Conversation')
                create_time = conv.get('create_time', 0)
                messages = conv.get('messages', [])
                
                # Format messages
                formatted_messages = []
                for msg in messages:
                    if isinstance(msg, dict):
                        role = msg.get('author', {}).get('role', 'unknown')
                        content = msg.get('content', {}).get('parts', [''])[0]
                        if content:
                            formatted_messages.append({
                                'role': role,
                                'content': content[:500]
                            })
                
                # Create blueprint
                blueprint = {
                    "source": conv_file.name,
                    "title": title,
                    "timestamp": datetime.fromtimestamp(create_time).isoformat() if create_time else datetime.now().isoformat(),
                    "message_count": len(messages),
                    "messages": formatted_messages[:50],  # First 50 messages
                    "conversation_preview": formatted_messages[0]['content'][:500] if formatted_messages else ""
                }
                
                # Store via API
                async with httpx.AsyncClient() as client:
                    response = await client.post(
                        "http://localhost:8002/memory/store",
                        json=blueprint,
                        headers={"X-Hive-API-Key": "rez-hive-admin-key-2026"}
                    )
                    
                    if response.status_code == 200:
                        result = response.json()
                        print(f"   ✅ Imported: {title[:50]}... -> {result.get('drift_lock', 'N/A')[:12]}...")
                        total_imported += 1
                    else:
                        print(f"   ❌ Failed: {title[:50]}... - {response.status_code}")
                        
            except Exception as e:
                print(f"   ❌ Error: {e}")
    
    print(f"\n📊 IMPORT COMPLETE!")
    print(f"   ✅ Imported: {total_imported} conversations")
    print(f"   📁 Source: {len(conv_files)} files")

if __name__ == "__main__":
    asyncio.run(import_chatgpt())