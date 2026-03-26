import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
# backend/workers/memory_worker.py

import os
import json
import sqlite3
import hashlib
from pathlib import Path
from datetime import datetime

class PCHiveMemory:
    """
    The Hippocampus of REZ HIVE.
    Persistent, local, multi-layer symbiote memory.
    """
    def __init__(self, base_path="D:/okiru-os/RezHiveOS/memory_bank"):
        self.base_path = Path(base_path)
        self.conversations_path = self.base_path / "conversations"
        self.trading_data_path = self.base_path / "trading"
        self.exports_path = self.base_path / "chat_exports"
        
        for p in[self.conversations_path, self.trading_data_path, self.exports_path]:
            p.mkdir(parents=True, exist_ok=True)
            
        self.db_path = self.base_path / "hive_memory.db"
        self._init_db()

    def _init_db(self):
        conn = sqlite3.connect(str(self.db_path))
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS conversations 
                    (id TEXT PRIMARY KEY, timestamp DATETIME, title TEXT, content TEXT, source TEXT)''')
        c.execute('''CREATE TABLE IF NOT EXISTS trading_strategies 
                    (id TEXT PRIMARY KEY, timestamp DATETIME, name TEXT, code TEXT, performance REAL)''')
        conn.commit()
        conn.close()

    async def store_memory(self, title: str, content: str, source="terminal"):
        """Stores memory to disk and SQLite DB."""
        doc_id = hashlib.sha256(content.encode()).hexdigest()[:16]
        timestamp = datetime.now()
        
        # 1. Store in SQLite for fast relational queries
        conn = sqlite3.connect(str(self.db_path))
        c = conn.cursor()
        c.execute('INSERT OR REPLACE INTO conversations VALUES (?, ?, ?, ?, ?)', 
                  (doc_id, timestamp, title, content, source))
        conn.commit()
        conn.close()
        
        # 2. Store JSON backup
        file_path = self.conversations_path / f"{doc_id}.json"
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump({'id': doc_id, 'timestamp': str(timestamp), 'title': title, 'content': content, 'source': source}, f, indent=2)
        
        return doc_id

    async def harvest_chatgpt_export(self, filepath: str) -> str:
        """Ingests standard ChatGPT data exports into the Symbiote Cortex."""
        path = Path(filepath)
        if not path.exists():
            return f"âŒ Error: Could not find export file at {filepath}"
            
        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            count = 0
            for convo in data:
                title = convo.get('title', 'Untitled')
                mapping = convo.get('mapping', {})
                convo_text = f"Title: {title}\n\n"
                
                for node_id, node in mapping.items():
                    if node and node.get('message') and node['message'].get('content'):
                        parts = node['message']['content'].get('parts', [])
                        role = node['message']['author']['role']
                        if parts and isinstance(parts[0], str):
                            convo_text += f"[{role.upper()}]: {parts[0]}\n"
                
                await self.store_memory(title, convo_text, "chatgpt_export")
                count += 1
                
            return f"âœ… Successfully harvested {count} conversation threads into the Symbiote Cortex."
        except Exception as e:
            return f"âŒ Harvest failed: {str(e)}"

    async def search_memory(self, query: str, limit=5) -> list:
        """Searches the SQLite Hippocampus for context."""
        conn = sqlite3.connect(str(self.db_path))
        c = conn.cursor()
        c.execute('''
            SELECT title, content, timestamp FROM conversations
            WHERE content LIKE ? OR title LIKE ?
            ORDER BY timestamp DESC LIMIT ?
        ''', (f'%{query}%', f'%{query}%', limit))
        
        results = [{"title": row[0], "snippet": row[1][:300] + "...", "timestamp": row[2]} for row in c.fetchall()]
        conn.close()
        return results

    async def process(self, task: str, memory_bus=None):
        """Process task – auto-generated stub"""
        return {"content": f"Processed: {task[:50]}", "worker": self.name}
    
    async def health_check(self):
        """Return worker health status"""
        return {"worker": self.name, "status": "healthy", "timestamp": __import__('time').time()}

