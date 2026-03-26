"""
OPCODE REGISTRY - The Sovereign Instruction Set
"""
from enum import Enum
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field

class OpcodeCategory(str, Enum):
    """Categories of opcodes for organization and permissioning"""
    STATE = "state"
    INVARIANT = "invariant"
    EXECUTION = "execution"
    LOCK = "lock"
    EMERGENCY = "emergency"

class OpcodeDefinition(BaseModel):
    """
    Definition of a single opcode.
    """
    name: str
    category: OpcodeCategory
    description: str
    required_params: List[str] = Field(default_factory=list)
    optional_params: List[str] = Field(default_factory=list)
    handler: str
    timeout_seconds: int = 30
    rate_limit: int = 100
    requires_invariant_check: bool = True

# Registry
OPCODE_REGISTRY: Dict[str, OpcodeDefinition] = {}

def register_opcode(**kwargs):
    """Factory function to create and register opcodes"""
    def decorator(cls):
        # Create instance with the provided kwargs plus class defaults
        instance = cls(**kwargs)
        OPCODE_REGISTRY[instance.name] = instance
        return cls
    return decorator

# State Opcodes
@register_opcode(
    name="LOD_STATE",
    category=OpcodeCategory.STATE,
    description="Load current capital/DNA state",
    required_params=["entity"],
    handler="handlers.state.load_state",
    requires_invariant_check=False
)
class LOD_STATE(OpcodeDefinition):
    pass

# Invariant Opcodes
@register_opcode(
    name="VRFY_MDD",
    category=OpcodeCategory.INVARIANT,
    description="Verify Maximum Drawdown",
    required_params=[],
    handler="handlers.invariant.check_mdd",
    timeout_seconds=1
)
class VRFY_MDD(OpcodeDefinition):
    pass

@register_opcode(
    name="VRFY_FLOOR",
    category=OpcodeCategory.INVARIANT,
    description="Verify equity above hard floor",
    required_params=[],
    handler="handlers.invariant.check_floor",
    timeout_seconds=1
)
class VRFY_FLOOR(OpcodeDefinition):
    pass

# Execution Opcodes
@register_opcode(
    name="EXEC_TRADE",
    category=OpcodeCategory.EXECUTION,
    description="Execute a trade",
    required_params=["exchange", "symbol", "side", "size"],
    handler="handlers.trading.execute_trade",
    timeout_seconds=5,
    rate_limit=10
)
class EXEC_TRADE(OpcodeDefinition):
    pass

# Emergency Opcodes
@register_opcode(
    name="EXIT_SAFE",
    category=OpcodeCategory.EMERGENCY,
    description="Emergency shutdown",
    required_params=["reason"],
    handler="handlers.emergency.exit_safe",
    timeout_seconds=30,
    rate_limit=1,
    requires_invariant_check=False
)
class EXIT_SAFE(OpcodeDefinition):
    pass

def validate_instruction(opcode: str, params: Dict[str, Any]) -> bool:
    if opcode not in OPCODE_REGISTRY:
        raise ValueError(f"Unknown opcode: {opcode}")
    defn = OPCODE_REGISTRY[opcode]
    for req in defn.required_params:
        if req not in params:
            raise ValueError(f"Missing required param: {req}")
    return True

__all__ = [
    'OpcodeCategory',
    'OpcodeDefinition',
    'OPCODE_REGISTRY',
    'validate_instruction'
]
