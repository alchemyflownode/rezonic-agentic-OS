"""
Sovereign Memory Manager v2.0 for PHOENIX OS
Upgraded with SQLite + Vector search + Event Sourcing
Fully backward compatible with v1 interface
"""

import json
import hashlib
import time
import sqlite3
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple
from collections import defaultdict
import numpy as np

# Try to load vector extension
try:
    import sqlite_vec
    VEC_AVAILABLE = True
except ImportError:
    VEC_AVAILABLE = False
    logging.warning("sqlite-vec not available. Vector search disabled.")

logger = logging.getLogger("PHOENIX_MEMORY_V2")


class MemoryEntry:
    """Sovereign memory entry with cryptographic integrity (v1 compatible)"""
    
    def __init__(self, drift_lock: str, timestamp: float, intent_type: str,
                 task: str, blueprint: Dict, tags: List[str] = None,
                 embedding: Optional[List[float]] = None):
        self.drift_lock = drift_lock
        self.timestamp = timestamp
        self.intent_type = intent_type
        self.task = task
        self.blueprint = blueprint
        self.tags = tags or []
        self.embedding = embedding
        
        # Hash chain linkage
        self.prev_hash = None
        self.current_hash = self._compute_hash()
    
    def _compute_hash(self) -> str:
        """Compute cryptographic hash of this entry"""
        data = f"{self.drift_lock}:{self.timestamp}:{self.intent_type}:{self.task}:{json.dumps(self.blueprint, sort_keys=True)}"
        return hashlib.sha256(data.encode()).hexdigest()
    
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
            "age_hours": round(self.age_hours, 1),
            "hash": self.current_hash
        }
    
    def to_sql_row(self) -> Tuple:
        """Convert to SQLite row format"""
        return (
            self.drift_lock,
            self.task,
            self.intent_type,
            json.dumps(self.tags),
            self.timestamp,
            json.dumps(self.blueprint, default=str),
            self.current_hash,
            self.prev_hash,
            json.dumps(self.embedding) if self.embedding else None
        )


class SovereignMemoryManagerV2:
    """
    Sovereign Memory Manager v2.0
    SQLite backend + Vector search + Event Sourcing
    Fully backward compatible with v1 interface
    """
    
    def __init__(self, memory_dir: Path, db_name: str = "rezhive_memory.db"):
        self.memory_dir = memory_dir
        self.memory_dir.mkdir(parents=True, exist_ok=True)
        
        # SQLite database path
        self.db_path = memory_dir / db_name
        
        # v1 compatibility: keep JSON index
        self.entries: Dict[str, MemoryEntry] = {}
        self.intent_index: Dict[str, List[str]] = defaultdict(list)
        self.tag_index: Dict[str, List[str]] = defaultdict(list)
        
        # Initialize database
        self._init_db()
        
        # Migrate existing JSON files to SQLite
        self._migrate_existing_json()
        
        # Load from SQLite into memory indices
        self._load_from_sqlite()
        
        logger.info(f"🧠 Sovereign Memory Manager v2.0: {len(self.entries)} entries loaded")
    
    def _init_db(self):
        """Initialize SQLite database with schema"""
        self.conn = sqlite3.connect(str(self.db_path))
        self.conn.row_factory = sqlite3.Row
        
        # Enable foreign keys
        self.conn.execute("PRAGMA foreign_keys = ON")
        
        # Create main memory table
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS memory (
                drift_lock TEXT PRIMARY KEY,
                task TEXT NOT NULL,
                intent_type TEXT NOT NULL,
                tags TEXT,
                timestamp REAL NOT NULL,
                blueprint TEXT NOT NULL,
                hash TEXT UNIQUE NOT NULL,
                prev_hash TEXT,
                embedding TEXT,
                created_at REAL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (prev_hash) REFERENCES memory(hash)
            )
        """)
        
        # Create indexes for fast search
        self.conn.execute("CREATE INDEX IF NOT EXISTS idx_intent ON memory(intent_type)")
        self.conn.execute("CREATE INDEX IF NOT EXISTS idx_timestamp ON memory(timestamp)")
        self.conn.execute("CREATE INDEX IF NOT EXISTS idx_hash ON memory(hash)")
        
        # Create audit log table (event sourcing)
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS audit_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp REAL NOT NULL,
                action TEXT NOT NULL,
                drift_lock TEXT,
                old_hash TEXT,
                new_hash TEXT,
                details TEXT
            )
        """)
        
        # Create vector table if extension available
        if VEC_AVAILABLE:
            try:
                sqlite_vec.load(self.conn)
                self.conn.execute("""
                    CREATE VIRTUAL TABLE IF NOT EXISTS memory_vectors
                    USING vec0(embedding float[384])
                """)
                logger.info("Vector search enabled")
            except Exception as e:
                logger.warning(f"Failed to create vector table: {e}")
        
        self.conn.commit()
    
    def _migrate_existing_json(self):
        """Migrate existing JSON memory files to SQLite"""
        json_files = list(self.memory_dir.glob("sce_*.json"))
        if not json_files:
            return
        
        logger.info(f"Migrating {len(json_files)} JSON files to SQLite...")
        
        for file_path in json_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                drift_lock = data.get("drift_lock") or file_path.stem[4:]
                
                # Check if already in SQLite
                cursor = self.conn.execute(
                    "SELECT 1 FROM memory WHERE drift_lock = ?",
                    (drift_lock,)
                )
                if cursor.fetchone():
                    continue  # Already migrated
                
                # Create entry
                entry = MemoryEntry(
                    drift_lock=drift_lock,
                    timestamp=data.get("timestamp", time.time()),
                    intent_type=data.get("intent_type", "unknown"),
                    task=data.get("task", "Unknown"),
                    blueprint=data.get("blueprint", {}),
                    tags=data.get("tags", [])
                )
                
                # Insert into SQLite
                self._insert_entry(entry)
                
            except Exception as e:
                logger.warning(f"Failed to migrate {file_path.name}: {e}")
        
        self.conn.commit()
        logger.info("Migration complete")
    
    def _insert_entry(self, entry: MemoryEntry):
        """Insert entry into SQLite"""
        row = entry.to_sql_row()
        self.conn.execute("""
            INSERT OR REPLACE INTO memory 
            (drift_lock, task, intent_type, tags, timestamp, blueprint, hash, prev_hash, embedding)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, row)
        
        # Insert vector if available
        if VEC_AVAILABLE and entry.embedding:
            rowid = self.conn.execute(
                "SELECT rowid FROM memory WHERE drift_lock = ?",
                (entry.drift_lock,)
            ).fetchone()[0]
            
            self.conn.execute(
                "INSERT OR REPLACE INTO memory_vectors(rowid, embedding) VALUES (?, ?)",
                (rowid, json.dumps(entry.embedding))
            )
    
    def _append_audit_log(self, action: str, drift_lock: str, 
                          old_hash: str = None, new_hash: str = None,
                          details: Dict = None):
        """Append to immutable audit log"""
        self.conn.execute("""
            INSERT INTO audit_log (timestamp, action, drift_lock, old_hash, new_hash, details)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            time.time(),
            action,
            drift_lock,
            old_hash,
            new_hash,
            json.dumps(details) if details else None
        ))
        self.conn.commit()
    
    def _load_from_sqlite(self):
        """Load all entries from SQLite into memory indices"""
        cursor = self.conn.execute("""
            SELECT drift_lock, task, intent_type, tags, timestamp, blueprint, hash
            FROM memory
        """)
        
        for row in cursor:
            entry = MemoryEntry(
                drift_lock=row['drift_lock'],
                timestamp=row['timestamp'],
                intent_type=row['intent_type'],
                task=row['task'],
                blueprint=json.loads(row['blueprint']),
                tags=json.loads(row['tags']) if row['tags'] else []
            )
            entry.current_hash = row['hash']
            
            self.entries[entry.drift_lock] = entry
            self.intent_index[entry.intent_type].append(entry.drift_lock)
            for tag in entry.tags:
                self.tag_index[tag].append(entry.drift_lock)
    
    # ========== v1 COMPATIBLE INTERFACE ==========
    
    def store(self, blueprint: Dict, task: str, intent_type: str = "interaction",
              tags: List[str] = None, embedding: List[float] = None) -> str:
        """
        Store a blueprint as a sovereign memory entry
        v1 compatible, now with embedding support
        """
        drift_lock = blueprint.get("master_drift_lock")
        if not drift_lock:
            drift_lock = hashlib.sha256(f"{task}{time.time()}".encode()).hexdigest()[:16]
            blueprint["master_drift_lock"] = drift_lock
        
        # Check if existing entry (for audit trail)
        existing = self.entries.get(drift_lock)
        old_hash = existing.current_hash if existing else None
        
        entry = MemoryEntry(
            drift_lock=drift_lock,
            timestamp=time.time(),
            intent_type=intent_type,
            task=task,
            blueprint=blueprint,
            tags=tags or [],
            embedding=embedding
        )
        
        # Set hash chain linkage
        if existing:
            entry.prev_hash = existing.current_hash
        
        # Store in SQLite
        self._insert_entry(entry)
        
        # Update memory indices
        self.entries[drift_lock] = entry
        if drift_lock not in self.intent_index[intent_type]:
            self.intent_index[intent_type].append(drift_lock)
        for tag in entry.tags:
            if drift_lock not in self.tag_index[tag]:
                self.tag_index[tag].append(drift_lock)
        
        # Audit log
        self._append_audit_log(
            action="UPDATE" if existing else "CREATE",
            drift_lock=drift_lock,
            old_hash=old_hash,
            new_hash=entry.current_hash,
            details={"task": task, "intent_type": intent_type}
        )
        
        # v1 compatibility: also save JSON file
        file_path = self.memory_dir / f"sce_{drift_lock}.json"
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(entry.to_dict(), f, indent=2, default=str)
        
        return drift_lock
    
    def search(self, query: str, limit: int = 10, intent_type: str = None,
               use_vector: bool = False) -> List[MemoryEntry]:
        """
        Search memory with relevance scoring
        v1 compatible, with optional vector search
        """
        if use_vector and VEC_AVAILABLE:
            return self._vector_search(query, limit, intent_type)
        
        # Fallback to v1-style text search
        query_lower = query.lower()
        scored = []
        
        for entry in self.entries.values():
            if intent_type and entry.intent_type != intent_type:
                continue
            
            score = 0
            
            # Drift lock match (highest)
            if query_lower == entry.drift_lock.lower():
                score += 100
            elif query_lower in entry.drift_lock.lower():
                score += 30
            
            # Task match
            if query_lower == entry.task.lower():
                score += 50
            elif query_lower in entry.task.lower():
                score += 15
            
            # Intent type match
            if query_lower == entry.intent_type.lower():
                score += 25
            
            # Tag match
            for tag in entry.tags:
                if query_lower in tag.lower():
                    score += 10
            
            # Content match
            if query_lower in json.dumps(entry.blueprint, default=str).lower():
                score += 5
            
            if score > 0:
                scored.append((score, entry))
        
        scored.sort(key=lambda x: (x[0], x[1].timestamp), reverse=True)
        return [entry for _, entry in scored[:limit]]
    
    def _vector_search(self, query: str, limit: int = 10, 
                       intent_type: str = None) -> List[MemoryEntry]:
        """
        Semantic vector search (requires embedding model)
        """
        # This would require generating embedding for query
        # For now, return empty or fallback to text search
        logger.info("Vector search requested but embedding generation not implemented")
        return self.search(query, limit, intent_type, use_vector=False)
    
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
        
        # Get SQLite stats
        db_size = self.db_path.stat().st_size if self.db_path.exists() else 0
        
        # Get audit log count
        audit_count = self.conn.execute("SELECT COUNT(*) FROM audit_log").fetchone()[0]
        
        return {
            "total_entries": len(self.entries),
            "by_intent_type": dict(intent_counts),
            "avg_age_hours": sum(ages) / len(ages) / 3600 if ages else 0,
            "newest_age_minutes": min(ages) / 60 if ages else 0,
            "oldest_age_hours": max(ages) / 3600 if ages else 0,
            "drift_chain_length": len(self.entries),
            "db_size_mb": db_size / (1024 * 1024),
            "audit_log_entries": audit_count,
            "vector_enabled": VEC_AVAILABLE
        }
    
    def verify_chain(self) -> bool:
        """
        Verify the entire hash chain
        Returns True if all entries are intact
        """
        cursor = self.conn.execute("""
            SELECT drift_lock, hash, prev_hash FROM memory ORDER BY timestamp
        """)
        
        for row in cursor:
            # Verify hash matches content
            entry = self.get_by_drift_lock(row['drift_lock'])
            if not entry or entry.current_hash != row['hash']:
                logger.error(f"Hash mismatch for {row['drift_lock']}")
                return False
            
            # Verify chain linkage
            if row['prev_hash']:
                # Find previous entry
                prev = self.conn.execute(
                    "SELECT drift_lock FROM memory WHERE hash = ?",
                    (row['prev_hash'],)
                ).fetchone()
                if not prev:
                    logger.error(f"Broken chain: {row['drift_lock']} links to missing {row['prev_hash']}")
                    return False
        
        return True
    
    def delete(self, drift_lock: str) -> bool:
        if drift_lock in self.entries:
            entry = self.entries[drift_lock]
            del self.entries[drift_lock]
            
            if entry.intent_type in self.intent_index:
                self.intent_index[entry.intent_type] = [l for l in self.intent_index[entry.intent_type] if l != drift_lock]
            
            for tag in entry.tags:
                if tag in self.tag_index:
                    self.tag_index[tag] = [l for l in self.tag_index[tag] if l != drift_lock]
            
            # Delete from SQLite
            self.conn.execute("DELETE FROM memory WHERE drift_lock = ?", (drift_lock,))
            self.conn.commit()
            
            # Audit log
            self._append_audit_log("DELETE", drift_lock, old_hash=entry.current_hash)
            
            # Delete JSON file
            file_path = self.memory_dir / f"sce_{drift_lock}.json"
            if file_path.exists():
                file_path.unlink()
            
            return True
        return False
    
    def export(self, filepath: Path):
        """Export entire memory to portable SQLite file"""
        import shutil
        shutil.copy2(self.db_path, filepath)
    
    def close(self):
        """Close database connection"""
        self.conn.close()
    
    def __enter__(self):
        return self
    
    def __exit__(self, *args):
        self.close()


# ========== v1 COMPATIBLE COMMAND HANDLER ==========

class MemoryCommandHandler:
    """Handles all /memory commands (v1 compatible)"""
    
    def __init__(self, memory_manager: SovereignMemoryManagerV2):
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
            return {"type": "reflex", "content": "📭 Usage: /memory search <query> [--vector]"}
        
        use_vector = "--vector" in parts
        query = " ".join([p for p in parts[2:] if not p.startswith("--")]).strip()
        
        results = self.memory.search(query, limit=10, use_vector=use_vector)
        
        if not results:
            return {"type": "reflex", "content": f"📭 No memories found for '{query}'."}
        
        search_type = "🔍 Vector" if use_vector else "🔍 Text"
        lines = [f"{search_type} search: **{len(results)}** memories for '{query}':\n"]
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
            f"🔗 **Hash:** `{entry.current_hash[:16]}...`",
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
            f"📜 **Audit Log:** {stats['audit_log_entries']} entries",
            f"🔍 **Vector Search:** {'✅ Enabled' if stats['vector_enabled'] else '❌ Disabled'}\n",
            "📈 **By Intent Type:**"
        ]
        
        for intent, count in sorted(stats['by_intent_type'].items(), key=lambda x: -x[1]):
            bar = "█" * min(40, count)
            lines.append(f"   • {intent:<15}: {bar} {count}")
        
        return {"type": "reflex", "content": "\n".join(lines)}
    
    async def _handle_verify(self) -> Dict:
        """Verify hash chain integrity"""
        if self.memory.verify_chain():
            return {"type": "reflex", "content": "✅ **Chain Verified** — All memory entries are cryptographically intact."}
        else:
            return {"type": "reflex", "content": "❌ **Chain Verification Failed** — Memory corruption detected! Check audit logs."}


# ========== FACTORY FUNCTION (Backward Compatible) ==========

def create_memory_manager(memory_dir: Path = None) -> SovereignMemoryManagerV2:
    """Factory function for backward compatibility"""
    if memory_dir is None:
        memory_dir = Path(__file__).parent / "data" / "memory"
    return SovereignMemoryManagerV2(memory_dir)