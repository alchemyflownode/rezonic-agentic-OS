# cortex_memory.py - Memory worker for Sovereign OS
import json
import os
from datetime import datetime
from pathlib import Path
import random

MEMORY_PATH = Path("D:/okiru-os/RezHive V12/data/memory/akashic-record.json")
USER_MEMORY_PATH = Path("D:/okiru-os/RezHive V12/data/memory/user-memory.json")

class CortexMemory:
    def __init__(self):
        self.memories = self.load_memories()
        self.user_memory = self.load_user_memory()
        
    def load_memories(self):
        """Load the massive conversations.json as Akashic Record"""
        try:
            if MEMORY_PATH.exists():
                with open(MEMORY_PATH, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    print(f"✅ Loaded {len(data) if isinstance(data, list) else 1} memory objects")
                    return data
            return {"conversations": [], "total": 0}
        except Exception as e:
            print(f"Error loading memory: {e}")
            return {"conversations": [], "total": 0}
    
    def load_user_memory(self):
        """Load user memory data"""
        try:
            if USER_MEMORY_PATH.exists():
                with open(USER_MEMORY_PATH, 'r', encoding='utf-8') as f:
                    return json.load(f)
            return {"preferences": {}, "history": []}
        except Exception as e:
            print(f"Error loading user memory: {e}")
            return {"preferences": {}, "history": []}
    
    def search_memories(self, query, limit=10):
        """Search through conversations"""
        results = []
        
        # Handle different JSON structures
        if isinstance(self.memories, list):
            items = self.memories[-1000:]  # Last 1000 items
        elif isinstance(self.memories, dict):
            items = self.memories.get('conversations', [])[-1000:]
        else:
            items = []
        
        for item in items:
            if query.lower() in str(item).lower():
                results.append(item)
                if len(results) >= limit:
                    break
        
        return {
            "results": results,
            "count": len(results),
            "total": len(items)
        }
    
    def get_stats(self):
        """Get memory statistics"""
        total = 0
        if isinstance(self.memories, list):
            total = len(self.memories)
        elif isinstance(self.memories, dict):
            total = len(self.memories.get('conversations', []))
        
        size_mb = MEMORY_PATH.stat().st_size / (1024 * 1024) if MEMORY_PATH.exists() else 0
        
        return {
            "total_memories": total,
            "memory_size_mb": round(size_mb, 2),
            "memory_size_gb": round(size_mb / 1024, 2),
            "last_updated": datetime.fromtimestamp(MEMORY_PATH.stat().st_mtime).isoformat() if MEMORY_PATH.exists() else None,
            "user_memories": len(self.user_memory.get('history', [])) if isinstance(self.user_memory, dict) else 0
        }
    
    def recall(self, query):
        """Recall memories based on query"""
        results = self.search_memories(query, limit=5)
        
        if results['count'] > 0:
            response = f"🧠 Found {results['count']} relevant memories:\n\n"
            for i, mem in enumerate(results['results'], 1):
                response += f"{i}. {str(mem)[:200]}...\n\n"
            return response
        else:
            return f"No memories found for: {query}"
    
    def remember(self, text):
        """Store a new memory"""
        timestamp = datetime.now().isoformat()
        
        # In a real implementation, you'd append to the file
        # For now, just store in user memory
        if isinstance(self.user_memory, dict):
            if 'history' not in self.user_memory:
                self.user_memory['history'] = []
            self.user_memory['history'].append({
                'timestamp': timestamp,
                'memory': text
            })
            
            # Keep only last 100
            self.user_memory['history'] = self.user_memory['history'][-100:]
            
            # Save (in a real implementation)
            try:
                with open(USER_MEMORY_PATH, 'w', encoding='utf-8') as f:
                    json.dump(self.user_memory, f, indent=2)
                return f"✅ Remembered: {text[:50]}..."
            except:
                return f"📝 Stored temporarily: {text[:50]}..."
        else:
            return "Error storing memory"

# Worker interface
async def process(task: str, context: dict):
    memory = CortexMemory()
    
    if task == "/memory stats" or task == "memory stats":
        stats = memory.get_stats()
        return f"""
🧠 **AKASHIC MEMORY VAULT**
━━━━━━━━━━━━━━━━━━━━━━━
Total Memories: {stats['total_memories']:,}
Memory Size: {stats['memory_size_mb']} MB ({stats['memory_size_gb']} GB)
Last Updated: {stats['last_updated'] or 'Unknown'}
User Memories: {stats['user_memories']}

💾 **Status**: ONLINE
📚 **Type**: Persistent Memory Store
🔮 **Capacity**: {stats['memory_size_mb']}MB Loaded
"""
    
    elif task.startswith("/recall "):
        query = task.replace("/recall ", "").strip()
        return memory.recall(query)
    
    elif task.startswith("remember "):
        text = task.replace("remember ", "").strip()
        return memory.remember(text)
    
    elif task == "/memory search" or task.startswith("/memory search "):
        query = task.replace("/memory search ", "").strip() if " " in task else ""
        if not query:
            return "Usage: /memory search <query>"
        results = memory.search_memories(query, limit=3)
        output = f"🔍 Search results for '{query}':\n\n"
        for i, res in enumerate(results['results'], 1):
            output += f"{i}. {str(res)[:150]}...\n\n"
        output += f"Found {results['count']} matches"
        return output
    
    elif task == "/memory":
        return """
🧠 **MEMORY COMMANDS**
━━━━━━━━━━━━━━━━━━
/memory stats - View memory statistics
/recall <query> - Search and recall memories
/remember <text> - Store a new memory
/memory search <query> - Search memory vault
"""
    
    else:
        # Try to interpret as a memory query
        return memory.recall(task)

# For direct testing - FIXED VERSION
if __name__ == "__main__":
    mem = CortexMemory()
    print("\n📊 MEMORY STATISTICS:")
    print(json.dumps(mem.get_stats(), indent=2))
    print("\n" + mem.recall("test"))