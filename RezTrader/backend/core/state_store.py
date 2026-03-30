# core/state_store.py
import json
import os
import sqlite3
import tempfile
import logging
from pathlib import Path
from datetime import datetime
import threading

logger = logging.getLogger(__name__)

class StateStore:
    def __init__(self, path="state.json", db_path="reztrader.db"):
        self.path = path
        self.db_path = db_path
        self._lock = threading.Lock()
        self._init_db()

    def _init_db(self):
        """Initialize SQLite for persistent state"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS state_store 
            (key TEXT PRIMARY KEY, value TEXT, updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS state_history 
            (key TEXT, value TEXT, timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP)
        """)
        conn.commit()
        conn.close()

    def save(self, data: dict, key: str = "global"):
        """Atomic save with backup"""
        with self._lock:
            try:
                # Write to temp file first (atomic)
                dir_name = os.path.dirname(self.path) or '.'
                fd, temp_path = tempfile.mkstemp(dir=dir_name)
                try:
                    with os.fdopen(fd, 'w') as f:
                        json.dump(data, f, indent=2)
                    
                    # Atomic rename
                    os.replace(temp_path, self.path)
                    
                    # Also save to SQLite
                    self._save_db(key, data)
                    
                    logger.debug(f"State saved: {key}")
                except:
                    if os.path.exists(temp_path):
                        os.unlink(temp_path)
                    raise
            except Exception as e:
                logger.error(f"State save failed: {e}")
                raise

    def _save_db(self, key: str, data: dict):
        """Save to SQLite with history"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            "INSERT OR REPLACE INTO state_store (key, value) VALUES (?, ?)",
            (key, json.dumps(data))
        )
        cursor.execute(
            "INSERT INTO state_history (key, value) VALUES (?, ?)",
            (key, json.dumps(data))
        )
        conn.commit()
        conn.close()

    def load(self, key: str = "global") -> dict:
        """Load with fallback chain"""
        with self._lock:
            # Try SQLite first
            try:
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                cursor.execute("SELECT value FROM state_store WHERE key = ?", (key,))
                row = cursor.fetchone()
                conn.close()
                if row:
                    return json.loads(row[0])
            except Exception as e:
                logger.warning(f"SQLite load failed: {e}")

            # Fallback to JSON
            try:
                if os.path.exists(self.path):
                    with open(self.path, 'r') as f:
                        return json.load(f)
            except Exception as e:
                logger.warning(f"JSON load failed: {e}")

            return {"position": "FLAT"}

    def load_all(self) -> dict:
        """Load all state"""
        result = {}
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT key, value FROM state_store")
            for row in cursor.fetchall():
                result[row[0]] = json.loads(row[1])
            conn.close()
        except:
            if os.path.exists(self.path):
                with open(self.path, 'r') as f:
                    result = json.load(f)
        return result

    def get_history(self, key: str, limit: int = 10) -> list:
        """Get state change history"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT value, timestamp FROM state_history WHERE key = ? ORDER BY timestamp DESC LIMIT ?",
            (key, limit)
        )
        history = [{"value": json.loads(row[0]), "timestamp": row[1]} for row in cursor.fetchall()]
        conn.close()
        return history