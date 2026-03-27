"""
Sovereign Memory Manager v2.0 with Rezhive backend
Backward compatible with v1 interface
"""

import json
import hashlib
import time
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Optional
from collections import defaultdict

from memory.rezhive_storage import RezhiveStorage

logger = logging.getLogger("PHOENIX_MEMORY")

class MemoryEntry:
    """Memory entry (v1 compatible)"""
    
    def __init__(self, drift_lock: str, timestamp: float, intent_type: str,
                 task: str, blueprint: Dict, tags: List[str] = None):
        self.drift_lock = drift_lock
        self.timestamp = timestamp
        self.intent_type = intent_type
        self.task = task
        self.blueprint = blueprint
        self.tags = tags or []
    
    @property
    def age_hours(self) -> float:
        return (time.time() - self.timestamp) / 3600
    
    def to_dict(self) -> Dict:
        return {
            "drift_lock": self.drift_lock,
            "timestamp": self.timestamp,
            "date": datetime.fromtimestamp(self.timestamp).isoformat(),
            "intent_type": self.intent_type,
            "task": self.task,
            "blueprint": self.blueprint,
            "tags": self.tags,
            "age_hours": round(self.age_hours, 1)
        }


class SovereignMemoryManager:
    """Sovereign Memory Manager with Rezhive backend"""
    
    def __init__(self, memory_dir: Path):
        self.memory_dir = memory_dir
        self.memory_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize Rezhive storage
        self.db_path = memory_dir / "rezhive_memory.db"
        self.storage = RezhiveStorage(self.db_path)
        
        # In-memory indices (for v1 compatibility)
        self.entries: Dict[str, MemoryEntry] = {}
        self.intent_index: Dict[str, List[str]] = defaultdict(list)
        self.tag_index: Dict[str, List[str]] = defaultdict(list)
        
        # Load existing memory
        self._load_from_storage()
        
        logger.info(f"🧠 Sovereign Memory Manager: {len(self.entries)} entries loaded")
    
    def _load_from_storage(self):
        """Load memory from Rezhive storage"""
        # Get all memory entries
        cursor = self.storage.conn.execute(
            "SELECT id, name, category, content, tags, timestamp FROM memory"
        )
        
        for row in cursor:
            entry = MemoryEntry(
                drift_lock=row['id'],
                timestamp=row['timestamp'],
                intent_type=row['category'],
                task=row['name'],
                blueprint=json.loads(row['content']) if row['content'] else {},
                tags=json.loads(row['tags']) if row['tags'] else []
            )
            
            self.entries[entry.drift_lock] = entry
            self.intent_index[entry.intent_type].append(entry.drift_lock)
            for tag in entry.tags:
                self.tag_index[tag].append(entry.drift_lock)
    
    def store(self, blueprint: Dict, task: str, intent_type: str = "interaction",
              tags: List[str] = None) -> str:
        """Store a blueprint as a sovereign memory entry"""
        
        drift_lock = blueprint.get("master_drift_lock")
        if not drift_lock:
            drift_lock = hashlib.sha256(f"{task}{time.time()}".encode()).hexdigest()[:16]
            blueprint["master_drift_lock"] = drift_lock
        
        # Store in Rezhive
        self.storage.store(
            memory_id=drift_lock,
            name=task,
            category=intent_type,
            content=json.dumps(blueprint, default=str),
            tags=tags or [],
            metadata={"source": "phoenix_memory_manager"}
        )
        
        # Update in-memory indices
        entry = MemoryEntry(
            drift_lock=drift_lock,
            timestamp=time.time(),
            intent_type=intent_type,
            task=task,
            blueprint=blueprint,
            tags=tags or []
        )
        
        self.entries[drift_lock] = entry
        self.intent_index[intent_type].append(drift_lock)
        for tag in entry.tags:
            self.tag_index[tag].append(drift_lock)
        
        # Also save JSON file for v1 compatibility
        file_path = self.memory_dir / f"sce_{drift_lock}.json"
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(entry.to_dict(), f, indent=2, default=str)
        
        return drift_lock
    
    def search(self, query: str, limit: int = 10, intent_type: str = None) -> List[MemoryEntry]:
        """Search memory (v1 compatible)"""
        query_lower = query.lower()
        scored = []
        
        for entry in self.entries.values():
            if intent_type and entry.intent_type != intent_type:
                continue
            
            score = 0
            
            if query_lower == entry.drift_lock.lower():
                score += 100
            elif query_lower in entry.drift_lock.lower():
                score += 30
            
            if query_lower == entry.task.lower():
                score += 50
            elif query_lower in entry.task.lower():
                score += 15
            
            if query_lower == entry.intent_type.lower():
                score += 25
            
            for tag in entry.tags:
                if query_lower in tag.lower():
                    score += 10
            
            if score > 0:
                scored.append((score, entry))
        
        scored.sort(key=lambda x: (x[0], x[1].timestamp), reverse=True)
        return [entry for _, entry in scored[:limit]]
    
    def get_by_drift_lock(self, drift_lock: str) -> Optional[MemoryEntry]:
        return self.entries.get(drift_lock)
    
    def get_recent(self, limit: int = 10, intent_type: str = None) -> List[MemoryEntry]:
        entries = list(self.entries.values())
        if intent_type:
            entries = [e for e in entries if e.intent_type == intent_type]
        entries.sort(key=lambda e: e.timestamp, reverse=True)
        return entries[:limit]
    
    def get_stats(self) -> Dict:
        intent_counts = defaultdict(int)
        for entry in self.entries.values():
            intent_counts[entry.intent_type] += 1
        
        now = time.time()
        ages = [now - e.timestamp for e in self.entries.values()]
        
        # Get Rezhive stats
        rezhive_stats = self.storage.get_stats()
        
        return {
            "total_entries": len(self.entries),
            "by_intent_type": dict(intent_counts),
            "avg_age_hours": sum(ages) / len(ages) / 3600 if ages else 0,
            "newest_age_minutes": min(ages) / 60 if ages else 0,
            "oldest_age_hours": max(ages) / 3600 if ages else 0,
            "drift_chain_length": len(self.entries),
            "db_size_mb": rezhive_stats["db_size_mb"],
            "audit_entries": rezhive_stats["audit_entries"],
            "vector_enabled": rezhive_stats["vector_enabled"]
        }
    
    def verify_integrity(self) -> bool:
        """Verify hash chain integrity"""
        return self.storage.verify_chain()
    
    def delete(self, drift_lock: str) -> bool:
        if drift_lock in self.entries:
            del self.entries[drift_lock]
            
            # Delete from Rezhive
            self.storage.conn.execute(
                "DELETE FROM memory WHERE id = ?", (drift_lock,)
            )
            self.storage.conn.commit()
            
            # Delete JSON file
            file_path = self.memory_dir / f"sce_{drift_lock}.json"
            if file_path.exists():
                file_path.unlink()
            
            return True
        return False
    
    def close(self):
        """Close storage connection"""
        self.storage.close()
    
    def __enter__(self):
        return self
    
    def __exit__(self, *args):
        self.close()


# Command handler (v1 compatible)
class MemoryCommandHandler:
    def __init__(self, memory_manager: SovereignMemoryManager):
        self.memory = memory_manager
    
    async def handle(self, cmd: str) -> Optional[Dict]:
        if cmd.startswith("/memory search"):
            return await self._handle_search(cmd)
        elif cmd.startswith("/memory show"):
            return await self._handle_show(cmd)
        elif cmd.startswith("/memory recent"):
            return await self._handle_recent(cmd)
        elif cmd == "/memory stats":
            return await self._handle_stats()
        elif cmd == "/memory verify":
            return await self._handle_verify()
        return None
    
    async def _handle_search(self, cmd: str) -> Dict:
        parts = cmd.split()
        if len(parts) < 3:
            return {"type": "reflex", "content": "📭 Usage: /memory search <query>"}
        
        query = " ".join(parts[2:]).strip()
        results = self.memory.search(query, limit=10)
        
        if not results:
            return {"type": "reflex", "content": f"📭 No memories found for '{query}'."}
        
        lines = [f"🔍 Found {len(results)} memories for '{query}':\n"]
        for r in results:
            date = datetime.fromtimestamp(r.timestamp).strftime("%Y-%m-%d %H:%M:%S")
            lines.append(f"🔒 `{r.drift_lock[:12]}...` • {r.intent_type} • {date}")
            lines.append(f"   📝 {r.task[:70]}")
        return {"type": "reflex", "content": "\n".join(lines)}
    
    async def _handle_show(self, cmd: str) -> Dict:
        parts = cmd.split()
        if len(parts) < 3:
            return {"type": "reflex", "content": "📭 Usage: /memory show <drift_lock>"}
        
        drift_lock = parts[2].strip()
        entry = self.memory.get_by_drift_lock(drift_lock)
        
        if not entry:
            return {"type": "reflex", "content": f"🔒 No memory found: {drift_lock}"}
        
        date = datetime.fromtimestamp(entry.timestamp).strftime("%Y-%m-%d %H:%M:%S")
        lines = [
            f"🔒 **Memory: `{entry.drift_lock}`**",
            f"📅 **Created:** {date}",
            f"🎯 **Intent:** {entry.intent_type}",
            f"📝 **Task:** {entry.task}",
            f"⏱️ **Age:** {entry.age_hours:.1f} hours\n",
            "📦 **Blueprint:**",
            f"```json\n{json.dumps(entry.blueprint, indent=2, default=str)[:2000]}\n```"
        ]
        return {"type": "reflex", "content": "\n".join(lines)}
    
    async def _handle_recent(self, cmd: str) -> Dict:
        parts = cmd.split()
        intent_type = parts[2] if len(parts) > 2 else None
        
        entries = self.memory.get_recent(limit=10, intent_type=intent_type)
        
        if not entries:
            return {"type": "reflex", "content": "📭 No recent memories."}
        
        lines = ["🕐 **Recent Memories**\n"]
        for e in entries:
            date = datetime.fromtimestamp(e.timestamp).strftime("%m-%d %H:%M")
            lines.append(f"   🔒 `{e.drift_lock[:12]}...` • {date} • {e.intent_type}")
            lines.append(f"      📝 {e.task[:70]}")
        return {"type": "reflex", "content": "\n".join(lines)}
    
    async def _handle_stats(self) -> Dict:
        stats = self.memory.get_stats()
        
        lines = [
            "🧠 **Sovereign Memory Statistics**\n",
            "═" * 45,
            f"📊 **Total Entries:** {stats['total_entries']}",
            f"🔗 **Drift Chain Length:** {stats['drift_chain_length']}",
            f"⏱️ **Average Age:** {stats['avg_age_hours']:.1f} hours",
            f"🆕 **Newest:** {stats['newest_age_minutes']:.0f} minutes ago",
            f"📜 **Oldest:** {stats['oldest_age_hours']:.1f} hours ago",
            f"💾 **Database Size:** {stats['db_size_mb']:.2f} MB",
            f"📜 **Audit Log:** {stats['audit_entries']} entries",
            f"🔍 **Vector Search:** {'✅ Enabled' if stats['vector_enabled'] else '❌ Disabled'}\n",
            "📈 **By Intent Type:**"
        ]
        
        for intent, count in sorted(stats['by_intent_type'].items(), key=lambda x: -x[1]):
            bar = "█" * min(40, count)
            lines.append(f"   • {intent:<15}: {bar} {count}")
        
        return {"type": "reflex", "content": "\n".join(lines)}
    
    async def _handle_verify(self) -> Dict:
        if self.memory.verify_integrity():
            return {"type": "reflex", "content": "✅ **Chain Verified** — All memory entries are cryptographically intact."}
        else:
            return {"type": "reflex", "content": "❌ **Chain Verification Failed** — Memory corruption detected!"}
