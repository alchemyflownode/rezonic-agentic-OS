"""Hive Memory Bus - Persistent Storage"""
import json
import time
import os
from pathlib import Path

class HiveMemoryBus:
    def __init__(self):
        self.memory_file = Path(__file__).parent / "memory_store.json"
        self.memories = self._load()
        self.stats = {"memories_loaded": len(self.memories)}
    
    def _load(self):
        if self.memory_file.exists():
            try:
                with open(self.memory_file, 'r') as f:
                    return json.load(f)
            except:
                return {}
        return {}
    
    def _save(self):
        with open(self.memory_file, 'w') as f:
            json.dump(self.memories, f, indent=2)
    
    def store(self, key, value, tags=None):
        self.memories[key] = {
            "value": value,
            "tags": tags or [],
            "timestamp": time.time()
        }
        self.stats["memories_loaded"] = len(self.memories)
        self._save()
    
    def recall(self, key):
        return self.memories.get(key, {}).get("value")
    
    def get_stats(self):
        return self.stats
