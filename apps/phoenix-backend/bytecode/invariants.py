"""
INVARIANT ENGINE - CHK_INV Implementation

This file contains the mathematical laws that govern the system.
Every invariant check is a function that returns a boolean.
If any invariant returns False, the opcode VRFY_INV fails,
and EXEC_ACT cannot proceed.

These are not "soft limits" - they are mathematical kill-switches.
"""
from decimal import Decimal, ROUND_DOWN, InvalidOperation
from typing import Dict, Any, Optional, Tuple, Callable, List
from dataclasses import dataclass
import hashlib
import time
import math


# ============================================================================
# INVARIANT STATE - The current system state passed to all checks
# ============================================================================

@dataclass
class InvariantState:
    """
    Current system state for invariant checking.
    
    This is passed to every invariant check function.
    The sandbox is responsible for populating this from the current context.
    """
    # Trading state
    current_equity: Decimal = Decimal('0')
    initial_capital: Decimal = Decimal('100000')
    high_water_mark: Decimal = Decimal('0')
    current_position: Decimal = Decimal('0')
    win_rate: Optional[Decimal] = None
    win_loss_ratio: Optional[Decimal] = None
    
    # Creative state
    character_dna_hash: Optional[str] = None
    rendered_frame_hash: Optional[str] = None
    cumulative_cost: Decimal = Decimal('0')
    
    # Market state
    current_price: Optional[Decimal] = None
    bid_price: Optional[Decimal] = None
    ask_price: Optional[Decimal] = None
    
    # Timestamp
    timestamp: float = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = time.time()
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'InvariantState':
        """Create from dictionary (e.g., from sandbox context)"""
        # Convert floats to Decimals where appropriate
        for field in ['current_equity', 'initial_capital', 'high_water_mark', 
                      'current_position', 'win_rate', 'win_loss_ratio',
                      'current_price', 'bid_price', 'ask_price', 'cumulative_cost']:
            if field in data and data[field] is not None:
                try:
                    data[field] = Decimal(str(data[field]))
                except (InvalidOperation, ValueError):
                    pass  # Leave as is
        
        return cls(**{k: v for k, v in data.items() if k in cls.__annotations__})


# ============================================================================
# INVARIANT CHECK RESULT
# ============================================================================

@dataclass
class InvariantResult:
    """Result of an invariant check"""
    passed: bool
    invariant_type: str
    message: str
    current_value: Any
    threshold_value: Any
    proof_hash: str
    details: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'passed': self.passed,
            'invariant_type': self.invariant_type,
            'message': self.message,
            'current_value': str(self.current_value) if self.current_value is not None else None,
            'threshold_value': str(self.threshold_value) if self.threshold_value is not None else None,
            'proof_hash': self.proof_hash,
            'details': self.details or {},
            'timestamp': time.time()
        }


# ============================================================================
# INVARIANT CHECK FUNCTIONS
# ============================================================================

def check_max_drawdown(state: InvariantState, threshold: float = 0.15) -> InvariantResult:
    """
    Check Maximum Drawdown invariant.
    
    MDD_t = max_{0 ≤ τ ≤ t} ( (HWM_τ - E_t) / HWM_τ )
    
    Args:
        state: Current system state
        threshold: Maximum allowed drawdown (e.g., 0.15 = 15%)
    
    Returns:
        InvariantResult with passed=True if MDD <= threshold
    """
    threshold_dec = Decimal(str(threshold))
    
    if state.high_water_mark <= 0:
        current_mdd = Decimal('0')
    else:
        current_mdd = (state.high_water_mark - state.current_equity) / state.high_water_mark
        current_mdd = max(current_mdd, Decimal('0'))  # Can't be negative
    
    passed = current_mdd <= threshold_dec
    
    proof_payload = f"MDD:{current_mdd}:{threshold}:{state.timestamp}"
    proof_hash = hashlib.sha256(proof_payload.encode()).hexdigest()
    
    return InvariantResult(
        passed=passed,
        invariant_type="MAX_DRAWDOWN",
        message=f"Drawdown {float(current_mdd)*100:.2f}% {'≤' if passed else '>'} {threshold*100:.2f}%",
        current_value=float(current_mdd),
        threshold_value=threshold,
        proof_hash=proof_hash,
        details={
            'equity': float(state.current_equity),
            'high_water_mark': float(state.high_water_mark),
            'drawdown_percent': float(current_mdd) * 100
        }
    )


def check_hard_floor(state: InvariantState, floor_percent: float = 0.85) -> InvariantResult:
    """
    Check Hard Floor invariant (Survival Function).
    
    S(E_t, λ) = 1 if E_t > E_0 * (1 - λ) else 0
    
    Args:
        state: Current system state
        floor_percent: Minimum allowed equity as % of initial (e.g., 0.85 = 85%)
    
    Returns:
        InvariantResult with passed=False if equity below floor (triggers EXIT_SAFE)
    """
    floor_dec = Decimal(str(floor_percent))
    minimum_equity = state.initial_capital * floor_dec
    
    passed = state.current_equity >= minimum_equity
    
    proof_payload = f"FLOOR:{state.current_equity}:{minimum_equity}:{state.timestamp}"
    proof_hash = hashlib.sha256(proof_payload.encode()).hexdigest()
    
    return InvariantResult(
        passed=passed,
        invariant_type="HARD_FLOOR",
        message=f"Equity {float(state.current_equity):.2f} {'≥' if passed else '<'} floor {float(minimum_equity):.2f}",
        current_value=float(state.current_equity),
        threshold_value=float(minimum_equity),
        proof_hash=proof_hash,
        details={
            'initial_capital': float(state.initial_capital),
            'floor_percent': floor_percent,
            'current_percent': float(state.current_equity / state.initial_capital) if state.initial_capital > 0 else 0
        }
    )


def check_kelly_criterion(state: InvariantState, position_size: Decimal, buffer: float = 0.25) -> InvariantResult:
    """
    Check Kelly Criterion for position sizing.
    
    K% = W - (1 - W) / R
    where:
        W = win probability
        R = win/loss ratio
    
    Args:
        state: Current system state (must have win_rate and win_loss_ratio)
        position_size: Proposed position size to check
        buffer: Safety buffer (e.g., 0.25 = use 25% of Kelly)
    
    Returns:
        InvariantResult with passed=False if position_size > Kelly-optimal * buffer
    """
    if state.win_rate is None or state.win_loss_ratio is None:
        return InvariantResult(
            passed=False,
            invariant_type="KELLY_CRITERION",
            message="Insufficient data for Kelly calculation",
            current_value=None,
            threshold_value=None,
            proof_hash=hashlib.sha256(b"kelly_insufficient_data").hexdigest()
        )
    
    W = state.win_rate
    R = state.win_loss_ratio
    
    if R <= 0:
        kelly_fraction = Decimal('0')
    else:
        kelly_fraction = W - (Decimal('1') - W) / R
    
    # Apply buffer (e.g., use 25% of Kelly for safety)
    buffer_dec = Decimal(str(buffer))
    safe_fraction = kelly_fraction * buffer_dec
    
    # Convert to position size
    max_position = state.current_equity * safe_fraction
    
    passed = position_size <= max_position
    
    proof_payload = f"KELLY:{position_size}:{max_position}:{state.timestamp}"
    proof_hash = hashlib.sha256(proof_payload.encode()).hexdigest()
    
    return InvariantResult(
        passed=passed,
        invariant_type="KELLY_CRITERION",
        message=f"Position {float(position_size):.2f} {'≤' if passed else '>'} Kelly-max {float(max_position):.2f}",
        current_value=float(position_size),
        threshold_value=float(max_position),
        proof_hash=proof_hash,
        details={
            'win_rate': float(W),
            'win_loss_ratio': float(R),
            'kelly_fraction': float(kelly_fraction),
            'safe_fraction': float(safe_fraction),
            'buffer_used': buffer
        }
    )


def check_dna_consistency(state: InvariantState, expected_dna_hash: str) -> InvariantResult:
    """
    Check DNA consistency for creative domain.
    
    Ensures that generated content maintains character DNA.
    Prevents "character drift" in creative generation.
    
    Args:
        state: Current system state (must have character_dna_hash)
        expected_dna_hash: Expected DNA hash from constitution
    
    Returns:
        InvariantResult with passed=False if DNA doesn't match
    """
    if not expected_dna_hash or not state.character_dna_hash:
        return InvariantResult(
            passed=True,
            invariant_type="DNA_CONSISTENCY",
            message="DNA check skipped (no hash configured)",
            current_value=state.character_dna_hash,
            threshold_value=expected_dna_hash,
            proof_hash=hashlib.sha256(b"dna_skipped").hexdigest()
        )
    
    passed = state.character_dna_hash == expected_dna_hash
    
    proof_payload = f"DNA:{state.character_dna_hash}:{expected_dna_hash}:{state.timestamp}"
    proof_hash = hashlib.sha256(proof_payload.encode()).hexdigest()
    
    return InvariantResult(
        passed=passed,
        invariant_type="DNA_CONSISTENCY",
        message=f"DNA {'matches' if passed else 'MISMATCH'}",
        current_value=state.character_dna_hash[:16] + "..." if state.character_dna_hash else None,
        threshold_value=expected_dna_hash[:16] + "..." if expected_dna_hash else None,
        proof_hash=proof_hash,
        details={
            'full_match': passed,
            'expected_prefix': expected_dna_hash[:8] if expected_dna_hash else None,
            'actual_prefix': state.character_dna_hash[:8] if state.character_dna_hash else None
        }
    )


def check_slippage(state: InvariantState, expected_price: Decimal, max_slippage_percent: float = 0.01) -> InvariantResult:
    """
    Check slippage against expected price.
    
    Used before executing trades to ensure price hasn't moved too much.
    
    Args:
        state: Current system state (must have bid/ask prices)
        expected_price: Price we expect to execute at
        max_slippage_percent: Maximum allowed slippage (e.g., 0.01 = 1%)
    
    Returns:
        InvariantResult with passed=False if slippage too high
    """
    if state.current_price is None:
        return InvariantResult(
            passed=False,
            invariant_type="SLIPPAGE",
            message="No current price available",
            current_value=None,
            threshold_value=max_slippage_percent,
            proof_hash=hashlib.sha256(b"slippage_no_price").hexdigest()
        )
    
    slippage = abs(state.current_price - expected_price) / expected_price
    max_slippage = Decimal(str(max_slippage_percent))
    
    passed = slippage <= max_slippage
    
    proof_payload = f"SLIPPAGE:{slippage}:{max_slippage_percent}:{state.timestamp}"
    proof_hash = hashlib.sha256(proof_payload.encode()).hexdigest()
    
    return InvariantResult(
        passed=passed,
        invariant_type="SLIPPAGE",
        message=f"Slippage {float(slippage)*100:.2f}% {'≤' if passed else '>'} {max_slippage_percent*100:.2f}%",
        current_value=float(slippage),
        threshold_value=max_slippage_percent,
        proof_hash=proof_hash,
        details={
            'expected_price': float(expected_price),
            'current_price': float(state.current_price),
            'slippage_percent': float(slippage) * 100
        }
    )


def check_consecutive_failures(state: InvariantState, max_failures: int = 3) -> InvariantResult:
    """
    Check consecutive reconciliation failures.
    
    If too many failures, system may be degraded.
    
    Args:
        state: Current system state (must have consecutive_failures)
        max_failures: Maximum allowed consecutive failures
    
    Returns:
        InvariantResult with passed=False if too many failures
    """
    consecutive_failures = getattr(state, 'consecutive_failures', 0)
    
    passed = consecutive_failures < max_failures
    
    proof_payload = f"FAILURES:{consecutive_failures}:{max_failures}:{state.timestamp}"
    proof_hash = hashlib.sha256(proof_payload.encode()).hexdigest()
    
    return InvariantResult(
        passed=passed,
        invariant_type="CONSECUTIVE_FAILURES",
        message=f"Failures {consecutive_failures} {'<' if passed else '≥'} {max_failures}",
        current_value=consecutive_failures,
        threshold_value=max_failures,
        proof_hash=proof_hash
    )


# ============================================================================
# INVARIANT ENGINE - Main entry point
# ============================================================================

class InvariantEngine:
    """
    Invariant Engine - Executes CHK_INV opcode.
    
    This engine loads the constitution spec and provides
    a unified interface for checking all invariants.
    """
    
    def __init__(self, constitution_spec: Dict[str, Any]):
        """
        Initialize with constitution spec.
        
        Args:
            constitution_spec: Loaded from .law file
        """
        self.spec = constitution_spec
        self.check_history: List[InvariantResult] = []
    
    def check(self, invariant_type: str, state: InvariantState, **kwargs) -> InvariantResult:
        """
        Check a specific invariant.
        
        Args:
            invariant_type: Type of invariant (e.g., "MAX_DRAWDOWN")
            state: Current system state
            **kwargs: Additional parameters for the check
        
        Returns:
            InvariantResult
        """
        # Map invariant type to function
        checkers = {
            "MAX_DRAWDOWN": lambda: check_max_drawdown(
                state, 
                kwargs.get('threshold', self.spec.get('max_drawdown', 0.15))
            ),
            "HARD_FLOOR": lambda: check_hard_floor(
                state,
                kwargs.get('floor_percent', self.spec.get('hard_floor', 0.85))
            ),
            "KELLY_CRITERION": lambda: check_kelly_criterion(
                state,
                kwargs.get('position_size', Decimal('0')),
                kwargs.get('buffer', self.spec.get('kelly_buffer', 0.25))
            ),
            "DNA_CONSISTENCY": lambda: check_dna_consistency(
                state,
                kwargs.get('expected_dna', self.spec.get('dna_hash', ''))
            ),
            "SLIPPAGE": lambda: check_slippage(
                state,
                kwargs.get('expected_price', Decimal('0')),
                kwargs.get('max_slippage', self.spec.get('max_slippage', 0.01))
            ),
            "CONSECUTIVE_FAILURES": lambda: check_consecutive_failures(
                state,
                kwargs.get('max_failures', self.spec.get('max_consecutive_failures', 3))
            )
        }
        
        if invariant_type not in checkers:
            return InvariantResult(
                passed=False,
                invariant_type=invariant_type,
                message=f"Unknown invariant type: {invariant_type}",
                current_value=None,
                threshold_value=None,
                proof_hash=hashlib.sha256(f"unknown_{invariant_type}".encode()).hexdigest()
            )
        
        result = checkers[invariant_type]()
        self.check_history.append(result)
        
        # Keep history manageable
        if len(self.check_history) > 1000:
            self.check_history = self.check_history[-1000:]
        
        return result
    
    def check_all(self, state: InvariantState) -> Dict[str, InvariantResult]:
        """
        Check all configured invariants.
        
        Returns:
            Dict mapping invariant_type -> result
        """
        results = {}
        
        # Check all invariants defined in spec
        if self.spec.get('max_drawdown') is not None:
            results['MAX_DRAWDOWN'] = self.check('MAX_DRAWDOWN', state)
        
        if self.spec.get('hard_floor') is not None:
            results['HARD_FLOOR'] = self.check('HARD_FLOOR', state)
        
        if self.spec.get('dna_hash'):
            results['DNA_CONSISTENCY'] = self.check('DNA_CONSISTENCY', state)
        
        return results
    
    def get_history(self) -> List[Dict[str, Any]]:
        """Get check history for audit"""
        return [r.to_dict() for r in self.check_history]


# ============================================================================
# EXPORTS
# ============================================================================

__all__ = [
    'InvariantState',
    'InvariantResult',
    'InvariantEngine',
    'check_max_drawdown',
    'check_hard_floor',
    'check_kelly_criterion',
    'check_dna_consistency',
    'check_slippage',
    'check_consecutive_failures'
]
