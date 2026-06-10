# D:\Rezonic_Agentic\apps\phoenix-kernel\config\constitution_core.py
"""
REZHIVE Core Constitution v1.0
The 3 Rules That Define ReZ Trader
"""

import time
from typing import Dict, List, Optional

class CoreConstitution:
    """The 3 rules that make ReZ Trader sovereign"""
    
    # Rule 1: Max Position Risk
    MAX_POSITION_RISK_PERCENT = 2.0
    
    # Rule 2: Stop Loss Required (for live trading)
    STOP_LOSS_REQUIRED_LIVE = True
    
    # Rule 3: No Martingale Doubling
    MARTINGALE_MULTIPLIER_LIMIT = 1.5
    
    @classmethod
    def validate_trade(cls, trade: Dict, portfolio: Dict, trade_history: List[Dict], 
                       mode: str = "live") -> Dict:
        """
        Validate a trade against all rules
        
        Args:
            trade: Dict with keys: symbol, amount, price, stop_loss
            portfolio: Dict with equity, balance, positions
            trade_history: List of past trades with pnl, amount
            mode: "live" or "paper"
        
        Returns:
            Dict with passed, violations, timestamp
        """
        violations = []
        
        # Rule 1: Max Position Risk
        risk_amount = trade.get("amount", 0) * trade.get("price", 0)
        portfolio_equity = portfolio.get("equity", 100000)
        risk_pct = (risk_amount / portfolio_equity) * 100
        
        if risk_pct > cls.MAX_POSITION_RISK_PERCENT:
            violations.append({
                "rule": "MAX_POSITION_RISK",
                "message": f"Position size {risk_pct:.1f}% exceeds {cls.MAX_POSITION_RISK_PERCENT}% limit",
                "action": "BLOCK",
                "severity": "critical"
            })
        
        # Rule 2: Stop Loss Required (only for live trading)
        if mode == "live" and cls.STOP_LOSS_REQUIRED_LIVE:
            if not trade.get("stop_loss"):
                violations.append({
                    "rule": "STOP_LOSS_REQUIRED",
                    "message": "Stop loss must be set for all live trades",
                    "action": "BLOCK",
                    "severity": "critical"
                })
        
        # Rule 3: No Martingale
        if trade_history and len(trade_history) > 0:
            last_trade = trade_history[-1]
            last_pnl = last_trade.get("pnl", 0)
            last_amount = last_trade.get("amount", 0)
            current_amount = trade.get("amount", 0)
            
            if last_pnl < 0 and current_amount > last_amount * cls.MARTINGALE_MULTIPLIER_LIMIT:
                violations.append({
                    "rule": "NO_MARTINGALE",
                    "message": f"Doubling down from {last_amount} to {current_amount} units",
                    "action": "BLOCK",
                    "severity": "critical"
                })
        
        return {
            "passed": len(violations) == 0,
            "violations": violations,
            "timestamp": time.time()
        }
    
    @classmethod
    def get_rules_summary(cls) -> Dict:
        """Get summary of all rules"""
        return {
            "max_position_risk_percent": cls.MAX_POSITION_RISK_PERCENT,
            "stop_loss_required_live": cls.STOP_LOSS_REQUIRED_LIVE,
            "martingale_multiplier_limit": cls.MARTINGALE_MULTIPLIER_LIMIT,
            "total_rules": 3
        }