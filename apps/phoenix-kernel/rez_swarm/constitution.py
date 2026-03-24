import json
import os
from enum import Enum
from typing import Dict, Any

class DriftTolerance(Enum):
    EXACT = "exact"
    STRICT = "strict" 
    LOOSE = "loose"
    QUALITY = "quality"

class RezConstitution:
    """Loads and enforces constitutional rules."""
    
    def __init__(self, path: str):
        self.path = path
        self.rules = self._load_rules()
        self.drift_tolerance = DriftTolerance.STRICT
        
    def _load_rules(self) -> Dict[str, Any]:
        """Load constitutional rules from JSON file."""
        if os.path.exists(self.path):
            try:
                with open(self.path, 'r') as f:
                    return json.load(f)
            except Exception as e:
                pass
        # Default constitution
        return {
            "zero_drift": True,
            "sparse_execution": True,
            "swarm_coordination": True,
            "signal_ttl": 5,
            "allowed_modes": ["balanced", "turbo", "quality", "zero_drift"]
        }
    
    def set_drift_tolerance(self, tolerance: DriftTolerance):
        """Set the drift tolerance level."""
        self.drift_tolerance = tolerance
        
        # Apply tolerance rules
        if tolerance == DriftTolerance.EXACT:
            import torch
            torch.use_deterministic_algorithms(True)
        elif tolerance == DriftTolerance.LOOSE:
            self.rules["adaptive_sparsity"] = True
            self.rules["early_convergence"] = True
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get a constitutional rule value."""
        return self.rules.get(key, default)
    
    def validate_node(self, node_name: str, inputs: Dict) -> bool:
        """Validate if a node's operation is constitutional."""
        # Check for forbidden operations
        forbidden = self.get("forbidden_operations", [])
        for op in forbidden:
            if op in str(inputs):
                return False
        return True