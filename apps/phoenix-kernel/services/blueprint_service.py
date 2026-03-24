"""
Blueprint Service - Manages SCE blueprints and drift locks
"""

import hashlib
import json
import time
from datetime import datetime
from typing import Dict, Any, Optional, List
from pathlib import Path

class BlueprintService:
    def __init__(self, storage_path: Path):
        self.storage_path = storage_path
        self.storage_path.mkdir(parents=True, exist_ok=True)
        self._blueprints: Dict[str, Dict] = {}
        self._load_blueprints()
    
    def create_drift_lock(self, data: Any) -> str:
        """Create a drift lock from data"""
        content = json.dumps(data, sort_keys=True, default=str)
        return hashlib.sha256(content.encode()).hexdigest()[:16]
    
    def create_blueprint(
        self, 
        intent: dict, 
        dna: dict, 
        execution: dict, 
        parent_lock: Optional[str] = None
    ) -> Dict:
        """Create a new SCE blueprint"""
        blueprint = {
            "protocol_version": "1.0.0",
            "timestamp": datetime.now().isoformat(),
            "intent": intent,
            "dna": dna,
            "execution": execution
        }
        
        if parent_lock:
            blueprint["parent_drift_lock"] = parent_lock
        
        blueprint["master_drift_lock"] = self.create_drift_lock(blueprint)
        return blueprint
    
    def store_blueprint(self, blueprint: Dict) -> str:
        """Store a blueprint and return its drift lock"""
        lock = blueprint.get(
            "master_drift_lock", 
            self.create_drift_lock(blueprint)
        )
        
        self._blueprints[lock] = {
            "value": blueprint,
            "timestamp": time.time(),
            "access_count": 0
        }
        
        # Persist to disk
        try:
            path = self.storage_path / f"sce_{lock}.json"
            with open(path, 'w') as f:
                json.dump(self._blueprints[lock], f, indent=2)
        except Exception as e:
            print(f"Failed to persist blueprint: {e}")
        
        return lock
    
    def verify_blueprint(self, drift_lock: str) -> Dict:
        """Verify a blueprint's integrity"""
        record = self._blueprints.get(drift_lock)
        if not record:
            return {"verified": False, "error": "Blueprint not found"}
        
        record["access_count"] += 1
        
        blueprint = record["value"]
        stored_lock = blueprint.get("master_drift_lock")
        calculated_lock = self.create_drift_lock(blueprint)
        
        is_valid = stored_lock == calculated_lock
        
        return {
            "verified": is_valid,
            "badge": "🟢 SOVEREIGN" if is_valid else "🔴 DRIFTED",
            "drift_lock": stored_lock
        }
    
    def search(self, query: str, limit: int = 10) -> List[Dict]:
        """Search blueprints by intent/dna content"""
        results = []
        query_lower = query.lower()
        
        for lock, record in self._blueprints.items():
            blueprint = record["value"]
            score = 0
            
            intent_str = json.dumps(blueprint.get("intent", {})).lower()
            dna_str = json.dumps(blueprint.get("dna", {})).lower()
            
            if query_lower in intent_str:
                score += 5
            if query_lower in dna_str:
                score += 3
            
            if score > 0:
                results.append({
                    "lock": lock,
                    "score": score,
                    "timestamp": record["timestamp"],
                    "intent": blueprint.get("intent"),
                    "access_count": record.get("access_count", 0)
                })
        
        results.sort(key=lambda x: (x["score"], x["timestamp"]), reverse=True)
        return results[:limit]
    
    def _load_blueprints(self):
        """Load blueprints from disk"""
        for p in self.storage_path.glob("sce_*.json"):
            try:
                with open(p) as f:
                    data = json.load(f)
                    if "value" in data and "master_drift_lock" in data["value"]:
                        lock = data["value"]["master_drift_lock"]
                        self._blueprints[lock] = data
            except Exception:
                pass
    
    def get_stats(self) -> Dict:
        """Get blueprint statistics"""
        return {
            "total": len(self._blueprints),
            "verified": sum(
                1 for lock in self._blueprints 
                if self.verify_blueprint(lock)["verified"]
            )
        }