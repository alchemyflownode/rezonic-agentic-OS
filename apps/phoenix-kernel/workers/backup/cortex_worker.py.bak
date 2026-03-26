import sys
from pathlib import Path

# Add parent directory to path
parent_dir = Path(__file__).parent.parent
if str(parent_dir) not in sys.path:
    sys.path.insert(0, str(parent_dir))
# cortex_memory.py - Memory worker for Sovereign OS
import json
import os
from datetime import datetime
from pathlib import Path
import logging
from workers.base_worker import BaseWorker

logger = logging.getLogger(__name__)

MEMORY_PATH = Path("D:/okiru-os/RezHive V12/data/memory/akashic-record.json")
USER_MEMORY_PATH = Path("D:/okiru-os/RezHive V12/data/memory/user-memory.json")

class CortexMemory(BaseWorker):
    """Memory worker for Sovereign OS - Akashic Memory Vault"""
    
    def __init__(self, hive_bus=None):
        super().__init__("cortex", hive_bus)
        self.description = "Akashic Memory Vault - 285MB persistent memory"
        self.version = "1.0.0"
        self.memories = self.load_memories()
        self.user_memory = self.load_user_memory()
        logger.info(f"  ðŸ§  CortexMemory initialized: {self.get_stats()['total_memories']} memories loaded")
        
    def load_memories(self):
        """Load the massive conversations.json as Akashic Record"""
        try:
            if MEMORY_PATH.exists():
                with open(MEMORY_PATH, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    return data
            return {"conversations": [], "total": 0}
        except Exception as e:
            logger.error(f"Error loading memory: {e}")
            return {"conversations": [], "total": 0}
    
    def load_user_memory(self):
        """Load user memory data"""
        try:
            if USER_MEMORY_PATH.exists():
                with open(USER_MEMORY_PATH, 'r', encoding='utf-8') as f:
                    return json.load(f)
            return {"preferences": {}, "history": []}
        except Exception as e:
            logger.error(f"Error loading user memory: {e}")
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
            response = f"ðŸ§  Found {results['count']} relevant memories:\n\n"
            for i, mem in enumerate(results['results'], 1):
                response += f"{i}. {str(mem)[:200]}...\n\n"
            return response
        else:
            return f"No memories found for: {query}"
    
    def remember(self, text):
        """Store a new memory"""
        timestamp = datetime.now().isoformat()
        
        if isinstance(self.user_memory, dict):
            if 'history' not in self.user_memory:
                self.user_memory['history'] = []
            self.user_memory['history'].append({
                'timestamp': timestamp,
                'memory': text
            })
            
            # Keep only last 100
            self.user_memory['history'] = self.user_memory['history'][-100:]
            
            try:
                with open(USER_MEMORY_PATH, 'w', encoding='utf-8') as f:
                    json.dump(self.user_memory, f, indent=2)
                return f"âœ… Remembered: {text[:50]}..."
            except:
                return f"ðŸ“ Stored temporarily: {text[:50]}..."
        else:
            return "Error storing memory"
    
    async def health_check(self):
        """Health check for the worker"""
        stats = self.get_stats()
        return {
            "healthy": True,
            "worker": "cortex",
            "memories": stats['total_memories'],
            "memory_mb": stats['memory_size_mb']
        }
    
    async def process(self, task):
        """Process incoming tasks"""
        if isinstance(task, dict):
            task_str = task.get('task', '')
        else:
            task_str = str(task)
            
        if task_str == "/memory stats" or task_str == "memory stats":
            stats = self.get_stats()
            return f"""
ðŸ§  **AKASHIC MEMORY VAULT**
â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”
Total Memories: {stats['total_memories']:,}
Memory Size: {stats['memory_size_mb']} MB ({stats['memory_size_gb']} GB)
Last Updated: {stats['last_updated'] or 'Unknown'}
User Memories: {stats['user_memories']}

ðŸ’¾ **Status**: ONLINE
ðŸ“š **Type**: Persistent Memory Store
ðŸ”® **Capacity**: {stats['memory_size_mb']}MB Loaded
"""
        elif task_str.startswith("/recall "):
            query = task_str.replace("/recall ", "").strip()
            return self.recall(query)
        elif task_str.startswith("remember "):
            text = task_str.replace("remember ", "").strip()
            return self.remember(text)
        elif task_str == "/memory" or task_str == "memory":
            return """
ðŸ§  **MEMORY COMMANDS**
â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”
/memory stats - View memory statistics
/recall <query> - Search and recall memories
/remember <text> - Store a new memory
"""
        else:
            # Try to interpret as a memory query
            return self.recall(task_str)

# For direct testing
if __name__ == "__main__":
    mem = CortexMemory()
    print("\nðŸ“Š MEMORY STATISTICS:")
    print(json.dumps(mem.get_stats(), indent=2))
    print("\n" + mem.recall("test"))

