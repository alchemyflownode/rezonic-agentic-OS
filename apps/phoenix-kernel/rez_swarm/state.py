import torch
from dataclasses import dataclass, field
from typing import Dict, Any, Optional
from enum import Enum

class DriftTolerance(Enum):
    EXACT = "exact"      # Bitwise reproducibility
    STRICT = "strict"    # < 0.01% variation
    LOOSE = "loose"      # < 2% variation (Turbo mode)
    QUALITY = "quality"  # Quality-focused, some variation allowed

@dataclass
class SwarmSignal:
    name: str
    value: Any
    source: str
    timestamp: float
    ttl: int = 5  # Time-to-live in seconds

class RezSwarmState:
    """Global coordination state for Rez Swarm nodes."""
    
    def __init__(self, constitution_path: str = "G:\\okiru-pure\\rezsparse-trainer\\.constitutional\\rules.json"):
        self.signals: Dict[str, SwarmSignal] = {}
        self.node_states: Dict[str, Dict[str, Any]] = {}
        self.constitution = RezConstitution(constitution_path)
        self.active_mode = "balanced"
        
        # Initialize deterministic RNG if needed
        if self.constitution.get("zero_drift", False):
            torch.manual_seed(0)
            if torch.cuda.is_available():
                torch.cuda.manual_seed_all(0)
    
    def signal(self, name: str, value: Any, source: str = "unknown"):
        """Emit a signal to the swarm."""
        import time
        self.signals[name] = SwarmSignal(
            name=name,
            value=value,
            source=source,
            timestamp=time.time()
        )
        # Clean old signals
        current_time = time.time()
        self.signals = {k: v for k, v in self.signals.items() 
                       if current_time - v.timestamp < v.ttl}
    
    def receive(self, name: str, default: Any = None) -> Any:
        """Receive a signal from the swarm."""
        signal = self.signals.get(name)
        if signal:
            return signal.value
        return default
    
    def set_mode(self, mode: str):
        """Set the global Rez Swarm mode."""
        valid_modes = ["balanced", "turbo", "quality", "zero_drift"]
        if mode in valid_modes:
            self.active_mode = mode
            # Apply mode-specific settings
            if mode == "zero_drift":
                self.constitution.set_drift_tolerance(DriftTolerance.EXACT)
            elif mode == "turbo":
                self.constitution.set_drift_tolerance(DriftTolerance.LOOSE)
    
    def get_active_nodes(self) -> list:
        """Get list of currently active Rez nodes."""
        return list(self.node_states.keys())