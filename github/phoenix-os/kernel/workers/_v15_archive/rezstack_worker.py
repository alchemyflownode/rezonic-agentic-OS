# workers/rezstack_worker.py
"""REZStack Worker - Convert intensity to motion parameters with drift lock"""

import hashlib
from typing import Dict, Any
from base_worker import Worker


class RezStackWorker(Worker):
    """Map numerical values to spring physics parameters"""
    
    def __init__(self):
        super().__init__("rezstack")
        self.version = "2.0.0"
    
    async def execute(self, task: str, **kwargs) -> Dict[str, Any]:
        """Convert intensity to motion parameters"""
        intensity = kwargs.get("intensity", 50)
        
        # Calculate motion parameters
        weight = min(2, max(0, intensity * 0.02))
        stiffness = 100 + weight * 400
        damping = max(5, 20 - weight * 7)
        speed_ms = max(200, 500 - weight * 150)
        
        # Determine symbol based on weight
        if weight < 0.3:
            symbol = "🌀"
            emotion = "bliss"
        elif weight < 0.8:
            symbol = "🐦"
            emotion = "violation"
        elif weight < 1.2:
            symbol = "💥"
            emotion = "rage"
        elif weight < 1.6:
            symbol = "🔥"
            emotion = "strategy"
        else:
            symbol = "🧠"
            emotion = "triumph"
        
        # Generate drift lock
        motion_data = {
            "intensity": intensity,
            "weight": weight,
            "stiffness": stiffness,
            "damping": damping,
            "symbol": symbol
        }
        drift_lock = hashlib.sha256(
            json.dumps(motion_data, sort_keys=True).encode()
        ).hexdigest()[:16]
        
        return {
            "success": True,
            "motion": {
                "weight": round(weight, 3),
                "stiffness": round(stiffness, 1),
                "damping": round(damping, 1),
                "speed_ms": round(speed_ms),
                "symbol": symbol,
                "emotion": emotion
            },
            "drift_lock": drift_lock,
            "worker": self.name,
            "version": self.version
        }
    
    async def batch(self, intensities: list) -> Dict[str, Any]:
        """Process multiple intensities in batch"""
        results = {}
        for intensity in intensities:
            result = await self.execute("", intensity=intensity)
            results[str(intensity)] = result["motion"]
        
        batch_lock = hashlib.sha256(
            json.dumps(intensities).encode()
        ).hexdigest()[:16]
        
        return {
            "success": True,
            "results": results,
            "batch_drift_lock": batch_lock,
            "count": len(intensities),
            "worker": self.name
        }