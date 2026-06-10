"""
Unified Memory System for Phoenix Coworker

Consolidates: hive_memory, memory/, cortex_worker.py, pc_hive_memory.py
Into a single system with:
- Vector storage (ChromaDB) for semantic search
- Graph storage (NetworkX) for relationships
- Event log (SQLite) for audit trail
"""

import asyncio
import json
import sqlite3
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, asdict
from enum import Enum
import numpy as np

# Optional imports - will gracefully degrade if not available
try:
    import chromadb
    from chromadb.config import Settings
    CHROMA_AVAILABLE = True
except ImportError:
    CHROMA_AVAILABLE = False

try:
    import networkx as nx
    NETWORKX_AVAILABLE = True
except ImportError:
    NETWORKX_AVAILABLE = False

try:
    from sentence_transformers import SentenceTransformer
    EMBEDDINGS_AVAILABLE = True
except ImportError:
    EMBEDDINGS_AVAILABLE = False


class MemoryType(Enum):
    FACT = "fact"
    EVENT = "event"
    TASK = "task"
    FILE = "file"
    CONVERSATION = "conversation"
    PREFERENCE = "preference"


@dataclass
class MemoryEntry:
    """A single memory entry"""
    id: str
    content: str
    memory_type: MemoryType
    source: str
    context: Dict[str, Any]
    timestamp: datetime
    embedding: Optional[List[float]] = None
    importance: float = 1.0
    access_count: int = 0
    last_accessed: Optional[datetime] = None
    
    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "content": self.content,
            "memory_type": self.memory_type.value,
            "source": self.source,
            "context": json.dumps(self.context),
            "timestamp": self.timestamp.isoformat(),
            "importance": self.importance,
            "access_count": self.access_count,
            "last_accessed": self.last_accessed.isoformat() if self.last_accessed else None
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> "MemoryEntry":
        return cls(
            id=data["id"],
            content=data["content"],
            memory_type=MemoryType(data["memory_type"]),
            source=data["source"],
            context=json.loads(data["context"]),
            timestamp=datetime.fromisoformat(data["timestamp"]),
            importance=data.get("importance", 1.0),
            access_count=data.get("access_count", 0),
            last_accessed=datetime.fromisoformat(data["last_accessed"]) if data.get("last_accessed") else None
        )


class EventBus:
    """Simple event bus for memory-related events"""
    
    def __init__(self):
        self._subscribers: Dict[str, List[Callable]] = {}
    
    def subscribe(self, event_type: str, callback: Callable):
        if event_type not in self._subscribers:
            self._subscribers[event_type] = []
        self._subscribers[event_type].append(callback)
    
    async def publish(self, event_type: str, data: Dict):
        if event_type in self._subscribers:
            for callback in self._subscribers[event_type]:
                if asyncio.iscoroutinefunction(callback):
                    await callback(data)
                else:
                    callback(data)


class UnifiedMemory:
    """
    Unified memory system combining vector, graph, and event log storage.
    
    This consolidates:
    - hive_memory/ directory structure
    - memory/ directory
    - cortex_worker.py functionality
    - pc_hive_memory.py functionality
    """
    
    def __init__(self, data_dir: Path = None):
        self.data_dir = data_dir or Path.home() / ".phoenix" / "memory"
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # Event bus for memory events
        self.event_bus = EventBus()
        
        # Initialize storage backends
        self._init_sqlite()
        self._init_chroma()
        self._init_graph()
        self._init_embeddings()
        
        print(f"✓ UnifiedMemory initialized at {self.data_dir}")
    
    def _init_sqlite(self):
        """Initialize SQLite event log"""
        self.db_path = self.data_dir / "memory.db"
        self.conn = sqlite3.connect(str(self.db_path), check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        
        cursor = self.conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS memories (
                id TEXT PRIMARY KEY,
                content TEXT NOT NULL,
                memory_type TEXT NOT NULL,
                source TEXT NOT NULL,
                context TEXT,
                timestamp TEXT NOT NULL,
                importance REAL DEFAULT 1.0,
                access_count INTEGER DEFAULT 0,
                last_accessed TEXT
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS memory_relationships (
                source_id TEXT NOT NULL,
                target_id TEXT NOT NULL,
                relationship_type TEXT NOT NULL,
                strength REAL DEFAULT 1.0,
                timestamp TEXT NOT NULL,
                PRIMARY KEY (source_id, target_id, relationship_type)
            )
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_memories_type ON memories(memory_type)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_memories_timestamp ON memories(timestamp)
        """)
        
        self.conn.commit()
    
    def _init_chroma(self):
        """Initialize ChromaDB vector storage"""
        if CHROMA_AVAILABLE:
            self.chroma_client = chromadb.Client(Settings(
                chroma_db_impl="duckdb+parquet",
                persist_directory=str(self.data_dir / "chroma")
            ))
            self.collection = self.chroma_client.get_or_create_collection(
                name="phoenix_memories",
                metadata={"hnsw:space": "cosine"}
            )
        else:
            self.chroma_client = None
            self.collection = None
            print("⚠ ChromaDB not available. Vector search disabled.")
    
    def _init_graph(self):
        """Initialize NetworkX graph storage"""
        if NETWORKX_AVAILABLE:
            self.graph = nx.DiGraph()
            self.graph_path = self.data_dir / "memory_graph.json"
            if self.graph_path.exists():
                try:
                    with open(self.graph_path, 'r') as f:
                        data = json.load(f)
                        self.graph = nx.node_link_graph(data)
                except Exception as e:
                    print(f"⚠ Could not load graph: {e}")
        else:
            self.graph = None
            print("⚠ NetworkX not available. Graph relationships disabled.")
    
    def _init_embeddings(self):
        """Initialize embedding model"""
        if EMBEDDINGS_AVAILABLE:
            try:
                self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
            except Exception as e:
                print(f"⚠ Could not load embedding model: {e}")
                self.embedding_model = None
        else:
            self.embedding_model = None
            print("⚠ SentenceTransformers not available. Using simple embeddings.")
    
    def _generate_embedding(self, text: str) -> List[float]:
        """Generate embedding for text"""
        if self.embedding_model:
            return self.embedding_model.encode(text).tolist()
        else:
            # Simple fallback: hash-based embedding (not semantic but deterministic)
            hash_val = hashlib.md5(text.encode()).digest()
            return [b / 255.0 for b in hash_val[:16]]
    
    def _generate_id(self, content: str, timestamp: datetime) -> str:
        """Generate unique ID for memory"""
        data = f"{content}:{timestamp.isoformat()}"
        return hashlib.sha256(data.encode()).hexdigest()[:16]
    
    async def remember(
        self,
        content: str,
        memory_type: MemoryType = MemoryType.FACT,
        context: Dict = None,
        source: str = "user",
        importance: float = 1.0
    ) -> MemoryEntry:
        """
        Store a new memory across all storage backends.
        
        Args:
            content: The content to remember
            memory_type: Type of memory
            context: Additional context/metadata
            source: Who/what created this memory
            importance: Importance score (0.0 - 2.0)
        
        Returns:
            The created MemoryEntry
        """
        context = context or {}
        timestamp = datetime.now()
        memory_id = self._generate_id(content, timestamp)
        
        # Generate embedding
        embedding = self._generate_embedding(content)
        
        # Create entry
        entry = MemoryEntry(
            id=memory_id,
            content=content,
            memory_type=memory_type,
            source=source,
            context=context,
            timestamp=timestamp,
            embedding=embedding,
            importance=importance
        )
        
        # Store in SQLite
        cursor = self.conn.cursor()
        cursor.execute(
            """INSERT INTO memories 
               (id, content, memory_type, source, context, timestamp, importance) 
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (entry.id, entry.content, entry.memory_type.value, 
             entry.source, json.dumps(entry.context), 
             entry.timestamp.isoformat(), entry.importance)
        )
        self.conn.commit()
        
        # Store in ChromaDB
        if self.collection:
            self.collection.add(
                ids=[entry.id],
                embeddings=[embedding],
                documents=[entry.content],
                metadatas=[{
                    "memory_type": entry.memory_type.value,
                    "source": entry.source,
                    "timestamp": entry.timestamp.isoformat(),
                    "importance": entry.importance
                }]
            )
        
        # Add to graph
        if self.graph is not None:
            self.graph.add_node(
                entry.id,
                content=entry.content[:100],
                memory_type=entry.memory_type.value,
                timestamp=entry.timestamp.isoformat(),
                importance=entry.importance
            )
            self._save_graph()
        
        # Publish event
        await self.event_bus.publish("memory:stored", {
            "id": entry.id,
            "content": entry.content[:100],
            "type": entry.memory_type.value,
            "source": entry.source
        })
        
        return entry
    
    async def recall(
        self,
        query: str,
        memory_type: Optional[MemoryType] = None,
        limit: int = 5,
        min_importance: float = 0.0
    ) -> List[MemoryEntry]:
        """
        Recall memories matching a query.
        
        Uses vector similarity search if available, falls back to keyword search.
        
        Args:
            query: Search query
            memory_type: Filter by memory type
            limit: Maximum results
            min_importance: Minimum importance threshold
        
        Returns:
            List of matching MemoryEntry objects
        """
        results = []
        
        # Try vector search first
        if self.collection:
            query_embedding = self._generate_embedding(query)
            
            where_filter = {"importance": {"$gte": min_importance}}
            if memory_type:
                where_filter["memory_type"] = memory_type.value
            
            chroma_results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=limit,
                where=where_filter if where_filter else None
            )
            
            if chroma_results["ids"] and chroma_results["ids"][0]:
                for i, memory_id in enumerate(chroma_results["ids"][0]):
                    entry = self._get_by_id(memory_id)
                    if entry:
                        entry.access_count += 1
                        entry.last_accessed = datetime.now()
                        self._update_access_stats(entry)
                        results.append(entry)
        
        # Fallback to SQLite search
        if not results:
            cursor = self.conn.cursor()
            
            if memory_type:
                cursor.execute(
                    """SELECT * FROM memories 
                       WHERE memory_type = ? AND importance >= ?
                       AND (content LIKE ? OR context LIKE ?)
                       ORDER BY timestamp DESC LIMIT ?""",
                    (memory_type.value, min_importance, f"%{query}%", f"%{query}%", limit)
                )
            else:
                cursor.execute(
                    """SELECT * FROM memories 
                       WHERE importance >= ?
                       AND (content LIKE ? OR context LIKE ?)
                       ORDER BY timestamp DESC LIMIT ?""",
                    (min_importance, f"%{query}%", f"%{query}%", limit)
                )
            
            rows = cursor.fetchall()
            for row in rows:
                entry = MemoryEntry.from_dict(dict(row))
                entry.access_count += 1
                entry.last_accessed = datetime.now()
                self._update_access_stats(entry)
                results.append(entry)
        
        # Update access stats and publish event
        for entry in results:
            await self.event_bus.publish("memory:accessed", {
                "id": entry.id,
                "content": entry.content[:100]
            })
        
        return results
    
    async def get_recent(
        self,
        hours: int = 24,
        memory_type: Optional[MemoryType] = None,
        limit: int = 50
    ) -> List[MemoryEntry]:
        """Get recent memories from the last N hours"""
        from datetime import timedelta
        
        cutoff = (datetime.now() - timedelta(hours=hours)).isoformat()
        
        cursor = self.conn.cursor()
        
        if memory_type:
            cursor.execute(
                """SELECT * FROM memories 
                   WHERE timestamp > ? AND memory_type = ?
                   ORDER BY timestamp DESC LIMIT ?""",
                (cutoff, memory_type.value, limit)
            )
        else:
            cursor.execute(
                """SELECT * FROM memories 
                   WHERE timestamp > ?
                   ORDER BY timestamp DESC LIMIT ?""",
                (cutoff, limit)
            )
        
        rows = cursor.fetchall()
        return [MemoryEntry.from_dict(dict(row)) for row in rows]
    
    async def relate(
        self,
        source_id: str,
        target_id: str,
        relationship_type: str = "related",
        strength: float = 1.0
    ):
        """Create a relationship between two memories"""
        cursor = self.conn.cursor()
        cursor.execute(
            """INSERT OR REPLACE INTO memory_relationships 
               (source_id, target_id, relationship_type, strength, timestamp)
               VALUES (?, ?, ?, ?, ?)""",
            (source_id, target_id, relationship_type, strength, datetime.now().isoformat())
        )
        self.conn.commit()
        
        if self.graph is not None:
            self.graph.add_edge(
                source_id, target_id,
                relationship=relationship_type,
                strength=strength
            )
            self._save_graph()
        
        await self.event_bus.publish("memory:related", {
            "source": source_id,
            "target": target_id,
            "type": relationship_type
        })
    
    async def get_related(self, memory_id: str, depth: int = 1) -> List[MemoryEntry]:
        """Get memories related to a given memory"""
        if self.graph is None:
            # Fallback to SQL
            cursor = self.conn.cursor()
            cursor.execute(
                """SELECT target_id FROM memory_relationships WHERE source_id = ?
                   UNION
                   SELECT source_id FROM memory_relationships WHERE target_id = ?""",
                (memory_id, memory_id)
            )
            related_ids = [row[0] for row in cursor.fetchall()]
        else:
            # Use graph
            related_ids = []
            if memory_id in self.graph:
                related_ids = list(nx.single_source_shortest_path_length(
                    self.graph, memory_id, cutoff=depth
                ).keys())
                related_ids.remove(memory_id)  # Remove self
        
        results = []
        for rid in related_ids:
            entry = self._get_by_id(rid)
            if entry:
                results.append(entry)
        
        return results
    
    def _get_by_id(self, memory_id: str) -> Optional[MemoryEntry]:
        """Get a memory by ID"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM memories WHERE id = ?", (memory_id,))
        row = cursor.fetchone()
        if row:
            return MemoryEntry.from_dict(dict(row))
        return None
    
    def _update_access_stats(self, entry: MemoryEntry):
        """Update access statistics for a memory"""
        cursor = self.conn.cursor()
        cursor.execute(
            """UPDATE memories 
               SET access_count = ?, last_accessed = ?
               WHERE id = ?""",
            (entry.access_count, 
             entry.last_accessed.isoformat() if entry.last_accessed else None,
             entry.id)
        )
        self.conn.commit()
    
    def _save_graph(self):
        """Save graph to disk"""
        if self.graph is not None and self.graph_path:
            data = nx.node_link_data(self.graph)
            with open(self.graph_path, 'w') as f:
                json.dump(data, f)
    
    async def forget(self, memory_id: str) -> bool:
        """Remove a memory from all storage"""
        # Remove from SQLite
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM memories WHERE id = ?", (memory_id,))
        cursor.execute("DELETE FROM memory_relationships WHERE source_id = ? OR target_id = ?", 
                      (memory_id, memory_id))
        self.conn.commit()
        
        # Remove from ChromaDB
        if self.collection:
            self.collection.delete(ids=[memory_id])
        
        # Remove from graph
        if self.graph is not None and memory_id in self.graph:
            self.graph.remove_node(memory_id)
            self._save_graph()
        
        await self.event_bus.publish("memory:forgotten", {"id": memory_id})
        
        return cursor.rowcount > 0
    
    async def consolidate(self):
        """
        Consolidate memories - remove duplicates, strengthen frequently accessed memories,
        prune old unimportant memories.
        """
        cursor = self.conn.cursor()
        
        # Find and remove very old, unimportant, rarely accessed memories
        cutoff = (datetime.now() - timedelta(days=90)).isoformat()
        cursor.execute(
            """DELETE FROM memories 
               WHERE timestamp < ? AND importance < 0.5 AND access_count < 3""",
            (cutoff,)
        )
        deleted = cursor.rowcount
        self.conn.commit()
        
        # Strengthen frequently accessed memories
        cursor.execute(
            """UPDATE memories 
               SET importance = importance * 1.1
               WHERE access_count > 10"""
        )
        self.conn.commit()
        
        await self.event_bus.publish("memory:consolidated", {
            "deleted": deleted,
            "strengthened": cursor.rowcount
        })
        
        return {"deleted": deleted, "strengthened": cursor.rowcount}
    
    def get_stats(self) -> Dict:
        """Get memory system statistics"""
        cursor = self.conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM memories")
        total = cursor.fetchone()[0]
        
        cursor.execute("SELECT memory_type, COUNT(*) FROM memories GROUP BY memory_type")
        by_type = {row[0]: row[1] for row in cursor.fetchall()}
        
        cursor.execute("SELECT COUNT(*) FROM memory_relationships")
        relationships = cursor.fetchone()[0]
        
        return {
            "total_memories": total,
            "by_type": by_type,
            "relationships": relationships,
            "vector_storage": self.collection is not None,
            "graph_storage": self.graph is not None,
            "embeddings": self.embedding_model is not None
        }
    
    def close(self):
        """Close all connections"""
        if self.conn:
            self.conn.close()
        if self.chroma_client:
            self.chroma_client.persist()


# Singleton instance
_memory_instance: Optional[UnifiedMemory] = None


def get_memory(data_dir: Path = None) -> UnifiedMemory:
    """Get or create the singleton memory instance"""
    global _memory_instance
    if _memory_instance is None:
        _memory_instance = UnifiedMemory(data_dir)
    return _memory_instance


async def demo():
    """Demo the unified memory system"""
    memory = UnifiedMemory()
    
    # Store some memories
    print("\n--- Storing Memories ---")
    
    await memory.remember(
        "User prefers dark mode in all applications",
        memory_type=MemoryType.PREFERENCE,
        source="observation",
        importance=1.5
    )
    
    await memory.remember(
        "Downloaded file: quarterly_report.pdf",
        memory_type=MemoryType.FILE,
        source="filesystem",
        context={"path": "~/Downloads/quarterly_report.pdf", "size": 2048}
    )
    
    await memory.remember(
        "User asked me to organize the Downloads folder",
        memory_type=MemoryType.TASK,
        source="conversation",
        context={"completed": False}
    )
    
    # Recall memories
    print("\n--- Recalling Memories ---")
    
    results = await memory.recall("dark mode")
    print(f"Query 'dark mode': {len(results)} results")
    for r in results:
        print(f"  - {r.content[:60]}...")
    
    results = await memory.recall("Downloads")
    print(f"\nQuery 'Downloads': {len(results)} results")
    for r in results:
        print(f"  - {r.content[:60]}...")
    
    # Get recent memories
    print("\n--- Recent Memories ---")
    recent = await memory.get_recent(hours=1)
    print(f"Recent memories (last hour): {len(recent)}")
    
    # Get stats
    print("\n--- Memory Stats ---")
    stats = memory.get_stats()
    print(json.dumps(stats, indent=2))
    
    memory.close()


if __name__ == "__main__":
    asyncio.run(demo())
