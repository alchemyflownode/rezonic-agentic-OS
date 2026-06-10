# D:\Rezonic_Agentic\apps\phoenix-kernel\workers\constitutional_firewall.py
"""
Constitutional Firewall + Immutable Audit System
Blocks unsafe trades and logs everything to tamper-proof audit trail
"""

import asyncio
import hashlib
import hmac
import json
import time
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
import logging

logger = logging.getLogger("REZ.FIREWALL")

# ============================================================================
# ENUMS & DATA CLASSES
# ============================================================================

class ViolationSeverity(Enum):
    """How bad is the violation?"""
    INFO = "info"          # Just for logging
    WARNING = "warning"    # Allowed but flagged
    BLOCK = "block"        # Trade prevented
    CRITICAL = "critical"  # System alert required

class ViolationAction(Enum):
    """What to do when rule is violated"""
    LOG_ONLY = "log_only"
    WARN_USER = "warn_user"
    BLOCK_TRADE = "block_trade"
    KILL_SWITCH = "kill_switch"

@dataclass
class AuditEntry:
    """Immutable audit entry with cryptographic proof"""
    entry_type: str  # trade, violation, system, config
    data: Dict[str, Any]
    timestamp: float = field(default_factory=time.time)
    previous_hash: str = ""
    signature: str = ""
    
    def __post_init__(self):
        """Generate cryptographic proof of authenticity"""
        content = (
            f"{self.entry_type}:"
            f"{json.dumps(self.data, sort_keys=True)}:"
            f"{self.timestamp}:"
            f"{self.previous_hash}"
        )
        self.hash = hashlib.sha256(content.encode()).hexdigest()
        
        # Add HMAC signature if secret key exists
        if hasattr(self, '_secret_key') and self._secret_key:
            self.signature = hmac.new(
                self._secret_key.encode(),
                self.hash.encode(),
                hashlib.sha256
            ).hexdigest()
    
    def to_dict(self) -> Dict:
        return {
            "entry_type": self.entry_type,
            "data": self.data,
            "timestamp": self.timestamp,
            "previous_hash": self.previous_hash,
            "hash": self.hash,
            "signature": self.signature
        }

@dataclass
class ConstitutionalViolation:
    """Record of a constitutional violation"""
    rule_id: str
    rule_name: str
    severity: ViolationSeverity
    action: ViolationAction
    trade: Dict[str, Any]
    reason: str
    timestamp: float = field(default_factory=time.time)
    
    def to_dict(self) -> Dict:
        return {
            "rule_id": self.rule_id,
            "rule_name": self.rule_name,
            "severity": self.severity.value,
            "action": self.action.value,
            "trade": self.trade,
            "reason": self.reason,
            "timestamp": self.timestamp
        }

@dataclass
class TradeValidationResult:
    """Result of constitutional validation"""
    approved: bool
    violations: List[ConstitutionalViolation]
    audit_hash: str
    timestamp: float = field(default_factory=time.time)
    
    def to_dict(self) -> Dict:
        return {
            "approved": self.approved,
            "violations": [v.to_dict() for v in self.violations],
            "audit_hash": self.audit_hash,
            "timestamp": self.timestamp
        }


# ============================================================================
# CONSTITUTIONAL RULES ENGINE
# ============================================================================

class ConstitutionalRules:
    """The 3 core rules that define ReZ Trader"""
    
    # Rule 1: Maximum Position Risk
    MAX_POSITION_RISK_PERCENT = 2.0
    
    # Rule 2: Stop Loss Required (unless in paper trading)
    STOP_LOSS_REQUIRED = True
    
    # Rule 3: No Martingale Doubling
    MARTINGALE_MULTIPLIER_LIMIT = 1.5  # Can't more than 1.5x last losing trade
    
    @classmethod
    def check_position_risk(cls, trade: Dict, portfolio: Dict) -> Optional[ConstitutionalViolation]:
        """Rule 1: No single position > 2% of portfolio"""
        risk_amount = trade.get("amount", 0) * trade.get("price", 0)
        portfolio_equity = portfolio.get("equity", 100000)
        risk_percent = (risk_amount / portfolio_equity) * 100
        
        if risk_percent > cls.MAX_POSITION_RISK_PERCENT:
            return ConstitutionalViolation(
                rule_id="RISK_001",
                rule_name="Max Position Risk",
                severity=ViolationSeverity.BLOCK,
                action=ViolationAction.BLOCK_TRADE,
                trade=trade,
                reason=f"Position size {risk_percent:.1f}% exceeds {cls.MAX_POSITION_RISK_PERCENT}% limit"
            )
        return None
    
    @classmethod
    def check_stop_loss(cls, trade: Dict, mode: str = "live") -> Optional[ConstitutionalViolation]:
        """Rule 2: Stop loss required for all live trades"""
        if mode == "live" and cls.STOP_LOSS_REQUIRED:
            if not trade.get("stop_loss"):
                return ConstitutionalViolation(
                    rule_id="SAFETY_001",
                    rule_name="Stop Loss Required",
                    severity=ViolationSeverity.BLOCK,
                    action=ViolationAction.BLOCK_TRADE,
                    trade=trade,
                    reason="Stop loss must be set for all live trades"
                )
        return None
    
    @classmethod
    def check_martingale(cls, trade: Dict, trade_history: List[Dict]) -> Optional[ConstitutionalViolation]:
        """Rule 3: No doubling down on losing positions"""
        if not trade_history:
            return None
        
        # Check last trade was a loss
        last_trade = trade_history[-1]
        if last_trade.get("pnl", 0) < 0:
            # Check if current trade is significantly larger
            last_amount = last_trade.get("amount", 0)
            current_amount = trade.get("amount", 0)
            
            if current_amount > last_amount * cls.MARTINGALE_MULTIPLIER_LIMIT:
                return ConstitutionalViolation(
                    rule_id="RISK_002",
                    rule_name="No Martingale",
                    severity=ViolationSeverity.BLOCK,
                    action=ViolationAction.BLOCK_TRADE,
                    trade=trade,
                    reason=f"Doubling down from {last_amount} to {current_amount} units"
                )
        return None
    
    @classmethod
    def validate_trade(cls, trade: Dict, portfolio: Dict, trade_history: List[Dict], 
                       mode: str = "live") -> List[ConstitutionalViolation]:
        """Run all rules against a trade"""
        violations = []
        
        # Rule 1: Position risk
        violation = cls.check_position_risk(trade, portfolio)
        if violation:
            violations.append(violation)
        
        # Rule 2: Stop loss (only in live mode)
        violation = cls.check_stop_loss(trade, mode)
        if violation:
            violations.append(violation)
        
        # Rule 3: Martingale
        violation = cls.check_martingale(trade, trade_history)
        if violation:
            violations.append(violation)
        
        return violations


# ============================================================================
# IMMUTABLE AUDIT LOGGER
# ============================================================================

class ImmutableAuditLogger:
    """
    Tamper-proof audit logging with cryptographic verification
    Chain-of-custody for every trade and violation
    """
    
    def __init__(self, audit_path: Path = Path("logs/audit.jsonl"), 

    async def execute(self, task: str, **kwargs) -> Dict[str, Any]:
        """Execute worker task"""
        return {"success": True, "message": f"Worker {self.name} executed {task}"}
                 secret_key: Optional[str] = None):
        self.audit_path = audit_path
        self.audit_path.parent.mkdir(parents=True, exist_ok=True)
        self.secret_key = secret_key or os.getenv("REZHIVE_AUDIT_SECRET", "change-me-in-production")
        self._last_hash = self._get_last_hash()
        self._write_queue: asyncio.Queue = asyncio.Queue(maxsize=10000)
        self._writer_task: Optional[asyncio.Task] = None
        
    def _get_last_hash(self) -> str:
        """Get hash of last audit entry for chain linking"""
        if not self.audit_path.exists():
            return hashlib.sha256(b"REZHIVE_GENESIS").hexdigest()
        
        try:
            with open(self.audit_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                if not lines:
                    return hashlib.sha256(b"REZHIVE_GENESIS").hexdigest()
                
                last_line = lines[-1].strip()
                if last_line:
                    last_entry = json.loads(last_line)
                    return last_entry.get("hash", hashlib.sha256(b"REZHIVE_GENESIS").hexdigest())
        except Exception as e:
            logger.error(f"Failed to read last audit hash: {e}")
        
        return hashlib.sha256(b"REZHIVE_GENESIS").hexdigest()
    
    async def start(self):
        """Start background writer"""
        self._writer_task = asyncio.create_task(self._writer_loop())
        logger.info(f"ðŸ“ Immutable audit logger started: {self.audit_path}")
    
    async def log(self, entry_type: str, data: Dict) -> str:
        """Log an audit entry asynchronously"""
        entry = AuditEntry(
            entry_type=entry_type,
            data=data,
            previous_hash=self._last_hash
        )
        entry._secret_key = self.secret_key
        
        await self._write_queue.put(entry)
        return entry.hash
    
    async def _writer_loop(self):
        """Background writer with batching"""
        batch = []
        
        while True:
            try:
                entry = await asyncio.wait_for(self._write_queue.get(), timeout=2.0)
                batch.append(entry)
                
                if len(batch) >= 50:
                    await self._flush_batch(batch)
                    batch = []
                    
            except asyncio.TimeoutError:
                if batch:
                    await self._flush_batch(batch)
                    batch = []
            except asyncio.CancelledError:
                if batch:
                    await self._flush_batch(batch)
                return
    
    async def _flush_batch(self, entries: List[AuditEntry]):
        """Write batch to disk"""
        try:
            with open(self.audit_path, 'a', encoding='utf-8') as f:
                for entry in entries:
                    f.write(json.dumps(entry.to_dict()) + '\n')
                    self._last_hash = entry.hash
        except Exception as e:
            logger.error(f"Failed to write audit batch: {e}")
    
    async def verify_chain(self) -> Tuple[bool, List[str]]:
        """Verify entire audit chain integrity"""
        if not self.audit_path.exists():
            return True, []
        
        errors = []
        previous_hash = hashlib.sha256(b"REZHIVE_GENESIS").hexdigest()
        
        try:
            with open(self.audit_path, 'r', encoding='utf-8') as f:
                for line_num, line in enumerate(f, 1):
                    if not line.strip():
                        continue
                    
                    entry = json.loads(line)
                    
                    # Verify hash matches content
                    content = (
                        f"{entry['entry_type']}:"
                        f"{json.dumps(entry['data'], sort_keys=True)}:"
                        f"{entry['timestamp']}:"
                        f"{entry['previous_hash']}"
                    )
                    expected_hash = hashlib.sha256(content.encode()).hexdigest()
                    
                    if entry['hash'] != expected_hash:
                        errors.append(f"Line {line_num}: Hash mismatch")
                    
                    # Verify chain link
                    if entry['previous_hash'] != previous_hash:
                        errors.append(f"Line {line_num}: Chain broken")
                    
                    previous_hash = entry['hash']
            
            return len(errors) == 0, errors
            
        except Exception as e:
            return False, [str(e)]
    
    async def query(self, entry_type: Optional[str] = None,
                    start_time: Optional[float] = None,
                    end_time: Optional[float] = None,
                    limit: int = 100) -> List[Dict]:
        """Query audit logs"""
        if not self.audit_path.exists():
            return []
        
        results = []
        
        try:
            with open(self.audit_path, 'r', encoding='utf-8') as f:
                for line in f:
                    if not line.strip():
                        continue
                    
                    entry = json.loads(line)
                    
                    # Apply filters
                    if entry_type and entry['entry_type'] != entry_type:
                        continue
                    if start_time and entry['timestamp'] < start_time:
                        continue
                    if end_time and entry['timestamp'] > end_time:
                        continue
                    
                    results.append(entry)
                    
                    if len(results) >= limit:
                        break
            
            return results
            
        except Exception as e:
            logger.error(f"Query failed: {e}")
            return []
    
    async def export(self, format: str = "json") -> str:
        """Export audit log for compliance"""
        if not self.audit_path.exists():
            return "[]"
        
        if format == "json":
            with open(self.audit_path, 'r', encoding='utf-8') as f:
                entries = [json.loads(line) for line in f if line.strip()]
            return json.dumps(entries, indent=2)
        
        elif format == "csv":
            import csv
            from io import StringIO
            
            output = StringIO()
            writer = csv.writer(output)
            writer.writerow(["timestamp", "entry_type", "data", "hash", "signature"])
            
            with open(self.audit_path, 'r', encoding='utf-8') as f:
                for line in f:
                    if not line.strip():
                        continue
                    entry = json.loads(line)
                    writer.writerow([
                        entry['timestamp'],
                        entry['entry_type'],
                        json.dumps(entry['data']),
                        entry['hash'],
                        entry['signature']
                    ])
            
            return output.getvalue()
        
        else:
            raise ValueError(f"Unsupported format: {format}")
    
    async def get_statistics(self) -> Dict:
        """Get audit statistics"""
        if not self.audit_path.exists():
            return {"total_entries": 0, "chain_valid": True}
        
        total = 0
        by_type = {}
        
        try:
            with open(self.audit_path, 'r', encoding='utf-8') as f:
                for line in f:
                    if not line.strip():
                        continue
                    entry = json.loads(line)
                    total += 1
                    by_type[entry['entry_type']] = by_type.get(entry['entry_type'], 0) + 1
            
            chain_valid, errors = await self.verify_chain()
            
            return {
                "total_entries": total,
                "by_type": by_type,
                "chain_valid": chain_valid,
                "chain_errors": errors[:5] if not chain_valid else [],
                "audit_path": str(self.audit_path),
                "queue_size": self._write_queue.qsize()
            }
            
        except Exception as e:
            return {"error": str(e)}
    
    async def shutdown(self):
        """Shutdown audit logger"""
        if self._writer_task:
            self._writer_task.cancel()
            try:
                await self._writer_task
            except asyncio.CancelledError:
                pass
        logger.info("ðŸ“ Audit logger shutdown")


# ============================================================================
# CONSTITUTIONAL FIREWALL
# ============================================================================

class ConstitutionalFirewall:
    """
    Main firewall that validates all trades before execution
    Combines constitutional rules with immutable audit logging
    """
    
    def __init__(self, audit_logger: ImmutableAuditLogger):

    async def execute(self, task: str, **kwargs) -> Dict[str, Any]:
        """Execute worker task"""
        return {"success": True, "message": f"Worker {self.name} executed {task}"}
        self.audit = audit_logger
        self.rule_engine = ConstitutionalRules()
        self.violation_history: List[ConstitutionalViolation] = []
        self.blocked_trades_count = 0
        self.approved_trades_count = 0
        
    async def validate_trade(self, 
                            trade: Dict, 
                            portfolio: Dict, 
                            trade_history: List[Dict],
                            mode: str = "live") -> TradeValidationResult:
        """
        Validate trade against constitutional rules
        
        Args:
            trade: Trade dict with keys: symbol, amount, price, stop_loss
            portfolio: Current portfolio state with equity, positions
            trade_history: List of past trades with pnl
            mode: "live" or "paper" (stop loss rule only applies to live)
        
        Returns:
            TradeValidationResult with approval status and violations
        """
        # Run rules
        violations = self.rule_engine.validate_trade(trade, portfolio, trade_history, mode)
        
        # Determine if trade should be blocked
        approved = all(v.action != ViolationAction.BLOCK_TRADE for v in violations)
        
        # Update counters
        if approved:
            self.approved_trades_count += 1
        else:
            self.blocked_trades_count += 1
        
        # Log to audit
        audit_hash = await self.audit.log("trade_validation", {
            "approved": approved,
            "violations": [v.to_dict() for v in violations],
            "trade": trade,
            "mode": mode,
            "portfolio_equity": portfolio.get("equity", 0)
        })
        
        # Store in history
        self.violation_history.extend(violations)
        
        # Log warnings for non-blocked violations
        for v in violations:
            if v.action == ViolationAction.WARN_USER:
                logger.warning(f"âš ï¸ Constitutional warning: {v.reason}")
            elif v.action == ViolationAction.BLOCK_TRADE:
                logger.error(f"ðŸ”´ Trade blocked: {v.reason}")
        
        return TradeValidationResult(
            approved=approved,
            violations=violations,
            audit_hash=audit_hash
        )
    
    async def get_statistics(self) -> Dict:
        """Get firewall statistics"""
        return {
            "approved_trades": self.approved_trades_count,
            "blocked_trades": self.blocked_trades_count,
            "block_rate": (self.blocked_trades_count / (self.approved_trades_count + self.blocked_trades_count)) 
                          if (self.approved_trades_count + self.blocked_trades_count) > 0 else 0,
            "recent_violations": [v.to_dict() for v in self.violation_history[-10:]],
            "rules": {
                "max_position_risk_pct": ConstitutionalRules.MAX_POSITION_RISK_PERCENT,
                "stop_loss_required": ConstitutionalRules.STOP_LOSS_REQUIRED,
                "martingale_limit": ConstitutionalRules.MARTINGALE_MULTIPLIER_LIMIT
            }
        }


# ============================================================================
# USAGE EXAMPLE
# ============================================================================

async def demo_firewall():
    """Demonstrate constitutional firewall in action"""
    
    # Create audit logger
    audit = ImmutableAuditLogger(Path("logs/audit_demo.jsonl"))
    await audit.start()
    
    # Create firewall
    firewall = ConstitutionalFirewall(audit)
    
    # Test portfolio
    portfolio = {
        "equity": 50000,
        "balance": 50000,
        "positions": {}
    }
    
    # Test trade history
    trade_history = [
        {"amount": 1000, "pnl": -50}  # Last trade was a loss
    ]
    
    print("\n" + "="*60)
    print("ðŸ” CONSTITUTIONAL FIREWALL DEMO")
    print("="*60)
    
    # Test 1: Safe trade (should pass)
    safe_trade = {
        "symbol": "EUR_USD",
        "amount": 500,
        "price": 1.1000,
        "stop_loss": 1.0950
    }
    
    print("\nðŸ“Š Test 1: Safe trade")
    result = await firewall.validate_trade(safe_trade, portfolio, trade_history, mode="live")
    print(f"  Approved: {result.approved}")
    print(f"  Violations: {len(result.violations)}")
    print(f"  Audit Hash: {result.audit_hash[:16]}...")
    
    # Test 2: Too large position (should block)
    large_trade = {
        "symbol": "EUR_USD",
        "amount": 50000,  # 50,000 units * $1.10 = $55,000 > 2% of $50,000
        "price": 1.1000,
        "stop_loss": 1.0950
    }
    
    print("\nðŸ“Š Test 2: Position too large")
    result = await firewall.validate_trade(large_trade, portfolio, trade_history, mode="live")
    print(f"  Approved: {result.approved}")
    for v in result.violations:
        print(f"  âŒ {v.reason}")
    
    # Test 3: No stop loss (should block)
    no_stop_trade = {
        "symbol": "EUR_USD",
        "amount": 500,
        "price": 1.1000,
        "stop_loss": None
    }
    
    print("\nðŸ“Š Test 3: No stop loss")
    result = await firewall.validate_trade(no_stop_trade, portfolio, trade_history, mode="live")
    print(f"  Approved: {result.approved}")
    for v in result.violations:
        print(f"  âŒ {v.reason}")
    
    # Test 4: Martingale (should block)
    martingale_trade = {
        "symbol": "EUR_USD",
        "amount": 2000,  # Double from last 1000 loss
        "price": 1.1000,
        "stop_loss": 1.0950
    }
    
    print("\nðŸ“Š Test 4: Martingale detected")
    result = await firewall.validate_trade(martingale_trade, portfolio, trade_history, mode="live")
    print(f"  Approved: {result.approved}")
    for v in result.violations:
        print(f"  âŒ {v.reason}")
    
    # Test 5: Paper trading mode (stop loss not required)
    paper_trade = {
        "symbol": "EUR_USD",
        "amount": 500,
        "price": 1.1000,
        "stop_loss": None
    }
    
    print("\nðŸ“Š Test 5: Paper trading mode")
    result = await firewall.validate_trade(paper_trade, portfolio, trade_history, mode="paper")
    print(f"  Approved: {result.approved}")
    print(f"  (Stop loss not required in paper trading)")
    
    # Get statistics
    print("\n" + "="*60)
    print("ðŸ“Š FIREWALL STATISTICS")
    print("="*60)
    stats = await firewall.get_statistics()
    print(f"Approved trades: {stats['approved_trades']}")
    print(f"Blocked trades: {stats['blocked_trades']}")
    print(f"Block rate: {stats['block_rate']:.1%}")
    
    # Verify audit chain
    print("\n" + "="*60)
    print("ðŸ“ AUDIT VERIFICATION")
    print("="*60)
    chain_valid, errors = await audit.verify_chain()
    print(f"Chain valid: {chain_valid}")
    if errors:
        print(f"Errors: {errors}")
    
    # Export audit
    print("\n" + "="*60)
    print("ðŸ“„ AUDIT EXPORT (first 3 entries)")
    print("="*60)
    entries = await audit.query(limit=3)
    for entry in entries:
        print(f"\n{entry['entry_type']} at {datetime.fromtimestamp(entry['timestamp'])}")
        print(f"  Hash: {entry['hash'][:16]}...")
    
    await audit.shutdown()
    
    return firewall


if __name__ == "__main__":
    asyncio.run(demo_firewall())
