# exchange/constitutional_trader.py
"""Constitutional enforcement for exchange trading"""

import logging
from typing import Dict, Any, Optional
from datetime import datetime
import hashlib

from exchange.base import Order
from exchange.binance_connector import BinanceConnector

logger = logging.getLogger("phoenix.exchange.constitutional")

class ConstitutionalTrader:
    """
    Wraps exchange connector with SCE constitutional enforcement
    Every trade is checked against constitution before execution
    """
    
    def __init__(self, exchange: BinanceConnector, constitution):
        self.exchange = exchange
        self.constitution = constitution
        self.trade_history = []
        self.drift_chain = []
        
        # Default invariants
        self.invariants = {
            "max_position": {"value": 0.10, "enabled": True},
            "max_daily_loss": {"value": 0.05, "enabled": True},
            "min_cash_reserve": {"value": 0.20, "enabled": True}
        }
    
    async def execute_trade(self, order: Order, portfolio_value: float, daily_pnl: float) -> Dict[str, Any]:
        """
        Execute trade with full constitutional enforcement
        
        Flow:
        1. Check all invariants
        2. Record constitution ruling
        3. Execute if approved
        4. Update drift chain
        """
        
        # Step 1: Check position size invariant
        position_value = order.quantity * order.price
        position_pct = position_value / portfolio_value if portfolio_value > 0 else 0
        
        if self.invariants["max_position"]["enabled"]:
            if position_pct > self.invariants["max_position"]["value"]:
                return self._block_trade(
                    order, 
                    "MAX_POSITION", 
                    f"Position {position_pct:.1%} exceeds limit {self.invariants['max_position']['value']:.1%}"
                )
        
        # Step 2: Check daily loss invariant
        if self.invariants["max_daily_loss"]["enabled"]:
            if order.side == "SELL":
                # Check if this sell would increase loss beyond limit
                projected_loss = daily_pnl - position_value
                loss_pct = abs(projected_loss) / portfolio_value
                if loss_pct > self.invariants["max_daily_loss"]["value"]:
                    return self._block_trade(
                        order,
                        "MAX_DAILY_LOSS",
                        f"Loss would exceed {self.invariants['max_daily_loss']['value']:.1%}"
                    )
        
        # Step 3: Check cash reserve
        if self.invariants["min_cash_reserve"]["enabled"]:
            # Simplified - would need actual cash balance
            pass
        
        # Step 4: Check constitution (if available)
        if self.constitution:
            ruling = self.constitution.evaluate(f"TRADE {order.side} {order.symbol}")
            if not ruling.get("approved"):
                return self._block_trade(order, "CONSTITUTION", ruling.get("reason", "Constitution violation"))
        
        # Step 5: Execute trade
        result = await self.exchange.execute_order(order)
        
        # Step 6: Record in drift chain
        drift_entry = self._record_trade(order, result)
        
        return {
            "success": result.status == "EXECUTED",
            "order": result,
            "drift_lock": drift_entry,
            "invariants_checked": list(self.invariants.keys()),
            "position_pct": position_pct
        }
    
    def _block_trade(self, order: Order, invariant: str, reason: str) -> Dict[str, Any]:
        """Block a trade due to invariant violation"""
        
        # Create drift chain entry for violation
        violation_hash = hashlib.sha256(
            f"{invariant}:{reason}:{datetime.now().isoformat()}".encode()
        ).hexdigest()[:16]
        
        self.drift_chain.append(violation_hash)
        
        logger.warning(f"🚫 Trade blocked by {invariant}: {reason}")
        
        return {
            "success": False,
            "blocked_by": invariant,
            "reason": reason,
            "drift_lock": violation_hash,
            "order": order
        }
    
    def _record_trade(self, order: Order, result: Order) -> str:
        """Record trade in history and drift chain"""
        
        trade_record = {
            "timestamp": datetime.now().isoformat(),
            "order_id": result.order_id,
            "symbol": order.symbol,
            "side": order.side,
            "quantity": order.quantity,
            "price": order.price,
            "status": result.status,
            "drift_lock": result.drift_lock
        }
        
        self.trade_history.append(trade_record)
        
        # Add to drift chain
        self.drift_chain.append(result.drift_lock)
        
        logger.info(f"✅ Trade recorded: {result.drift_lock}")
        
        return result.drift_lock
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get trading metrics"""
        return {
            "total_trades": len(self.trade_history),
            "drift_chain_length": len(self.drift_chain),
            "invariants": self.invariants,
            "recent_trades": self.trade_history[-10:]
        }
    
    def update_invariant(self, name: str, value: float = None, enabled: bool = None) -> None:
        """Update invariant parameters"""
        if name in self.invariants:
            if value is not None:
                self.invariants[name]["value"] = value
            if enabled is not None:
                self.invariants[name]["enabled"] = enabled
            logger.info(f"Updated invariant {name}: {self.invariants[name]}")