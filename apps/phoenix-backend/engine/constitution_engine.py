"""
CONSTITUTION ENGINE - Risk & Strategy Constraints
"""
from typing import Dict, Any, Optional
from dataclasses import dataclass
import hashlib
import time

@dataclass
class InvariantState:
    current_equity: float = 0
    initial_capital: float = 100000
    high_water_mark: float = 0
    current_position: float = 0
    timestamp: float = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = time.time()

@dataclass
class InvariantResult:
    passed: bool
    invariant_type: str
    message: str
    current_value: Any
    threshold_value: Any
    proof_hash: str

class ConstitutionEngine:
    """Layer 2: Zero Strategy Drift - Guardrails & Strategy Constraints"""
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.regimes = ["BULL", "BEAR", "CRAB", "VOLATILE"]
        self.current_regime = "CRAB"
        self.max_drawdown = 3.0
        self.caps = {"BTC": 40, "ETH": 30, "SOL": 20}
        self.current_drawdown = 1.24
        self.current_exposure = {"BTC": 32, "ETH": 18, "SOL": 8}
        self.invariant_history = []
    
    def evaluate_state(self) -> dict:
        """Evaluate current portfolio against Constitution limits"""
        import random
        
        # Simulate market fluctuation
        self.current_drawdown += random.uniform(-0.1, 0.15)
        self.current_drawdown = max(0, min(self.current_drawdown, 5.0))
        
        for asset in self.current_exposure:
            self.current_exposure[asset] += random.uniform(-1.0, 1.5)
            self.current_exposure[asset] = max(0, self.current_exposure[asset])
        
        # Occasionally change regime
        if random.random() < 0.05:
            self.current_regime = random.choice(self.regimes)
        
        blocked = False
        message = ""
        action = "ALLOW"
        
        # Check Drawdown Guardrail
        if self.current_drawdown > self.max_drawdown:
            blocked = True
            action = "BLOCK"
            message = f"Daily drawdown {self.current_drawdown:.2f}% exceeds limit"
        
        # Check Exposure Guardrail
        if not blocked:
            for asset, cap in self.caps.items():
                if self.current_exposure.get(asset, 0) > cap:
                    blocked = True
                    action = "BLOCK"
                    message = f"Trade blocked: {asset} exposure {self.current_exposure[asset]:.1f}% > {cap}%"
                    break
        
        return {
            "regime": self.current_regime,
            "exposure": self.current_exposure,
            "blocked": blocked,
            "last_check": {
                "passed": not blocked,
                "message": message,
                "action": action,
                "expected_impact": self.current_drawdown / self.max_drawdown
            },
            "timestamp": time.time() * 1000
        }
    
    def check_invariant(self, invariant_type: str, state: InvariantState) -> InvariantResult:
        """Check a specific invariant"""
        if invariant_type == "HARD_FLOOR":
            return self._check_hard_floor(state)
        elif invariant_type == "MAX_DRAWDOWN":
            return self._check_max_drawdown(state)
        else:
            return InvariantResult(False, invariant_type, "Unknown invariant", None, None, "")
    
    def _check_hard_floor(self, state: InvariantState) -> InvariantResult:
        floor_pct = self.config.get('hard_floor', 0.85)
        minimum = state.initial_capital * floor_pct
        passed = state.current_equity >= minimum
        proof = hashlib.sha256(f"FLOOR:{state.current_equity}:{minimum}".encode()).hexdigest()
        return InvariantResult(
            passed=passed,
            invariant_type="HARD_FLOOR",
            message=f"Equity {state.current_equity:.2f} {'≥' if passed else '<'} floor {minimum:.2f}",
            current_value=state.current_equity,
            threshold_value=minimum,
            proof_hash=proof
        )
    
    def _check_max_drawdown(self, state: InvariantState) -> InvariantResult:
        threshold = self.config.get('max_drawdown', 0.15)
        if state.high_water_mark <= 0:
            current_mdd = 0
        else:
            current_mdd = (state.high_water_mark - state.current_equity) / state.high_water_mark
            current_mdd = max(current_mdd, 0)
        
        passed = current_mdd <= threshold
        proof = hashlib.sha256(f"MDD:{current_mdd}:{threshold}".encode()).hexdigest()
        return InvariantResult(
            passed=passed,
            invariant_type="MAX_DRAWDOWN",
            message=f"Drawdown {current_mdd*100:.1f}% {'≤' if passed else '>'} {threshold*100:.1f}%",
            current_value=current_mdd,
            threshold_value=threshold,
            proof_hash=proof
        )
