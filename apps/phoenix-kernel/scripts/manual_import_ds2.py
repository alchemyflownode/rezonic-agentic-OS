# manual_import_ds2.py
"""Import ds2.json directly using SovereignMemoryManager (no API)"""

import sys
import json
import time
import hashlib
from pathlib import Path
from datetime import datetime

# Add kernel path
sys.path.insert(0, r"D:\Rezonic_Agentic\apps\phoenix-kernel")

from memory_manager import SovereignMemoryManager, MemoryEntry

async def manual_import():
    """Import ds2.json directly"""
    
    # Initialize memory manager
    memory_dir = Path(r"D:\Rezonic_Agentic\apps\phoenix-kernel\data\memory")
    manager = SovereignMemoryManager(memory_dir)
    
    # Read ds2.json
    file_path = Path(r"D:\Rezonic_Agentic\apps\phoenix-kernel\data\deepseek_qwen\ds2.json")
    
    print(f"📖 Reading: {file_path}")
    
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    print(f"📊 Found {len(data)} conversations")
    
    imported = 0
    errors = 0
    
    for i, item in enumerate(data):
        try:
            # Extract title and content
            if isinstance(item, dict):
                title = item.get('title', f'Conversation_{i+1}')
                # Get the actual conversation content
                messages = item.get('messages', [])
                if messages:
                    content = json.dumps(messages, indent=2)[:5000]
                else:
                    content = json.dumps(item, indent=2)[:5000]
            else:
                title = f'Entry_{i+1}'
                content = str(item)[:5000]
            
            # Create blueprint
            blueprint = {
                "source": "ds2.json",
                "title": title,
                "content": content,
                "index": i,
                "imported_at": datetime.now().isoformat()
            }
            
            # Store directly
            drift_lock = manager.store(
                blueprint=blueprint,
                task=f"Import from ds2.json: {title[:50]}",
                intent_type="chat_import",
                tags=["deepseek", "ds2", "chat"]
            )
            
            print(f"✅ [{i+1:3d}] {drift_lock[:12]}... - {title[:50]}")
            imported += 1
            
        except Exception as e:
            print(f"❌ [{i+1:3d}] Error: {e}")
            errors += 1
    
    print(f"\n📊 IMPORT COMPLETE:")
    print(f"   ✅ Imported: {imported}")
    print(f"   ❌ Errors: {errors}")
    print(f"   📁 Memory: {len(manager.entries)} total entries")

if __name__ == "__main__":
    import asyncio
    asyncio.run(manual_import())