"""
Simple Safety Guard for Phoenix Coworker

Replaces: constitutional_council_fixed.py, constitutional_evaluator.py,
          constitutional_governor.py, constitutional_router.py

Provides a single, simple safety layer for personal use:
- Hard rules for dangerous commands
- User confirmation for destructive actions
- Logging for audit trail
"""

import re
import json
import asyncio
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Callable, Any
from dataclasses import dataclass
from enum import Enum


class RiskLevel(Enum):
    SAFE = "safe"
    CAUTION = "caution"  # Should confirm with user
    DANGEROUS = "dangerous"  # Blocked


@dataclass
class SafetyDecision:
    """Result of a safety check"""
    allowed: bool
    risk_level: RiskLevel
    reason: str
    requires_confirmation: bool
    confirmation_prompt: Optional[str] = None
    action: Optional[str] = None


class SafetyGuard:
    """
    Simple safety guard for personal coworker use.
    
    Replaces the over-engineered constitutional governance with:
    1. Hard rules for obviously dangerous actions
    2. Confirmation for potentially destructive actions
    3. Audit logging
    """
    
    # Commands that are always blocked
    DANGEROUS_PATTERNS = [
        # System destruction
        r'rm\s+-rf\s+/',
        r'rm\s+-rf\s+~',
        r'rm\s+-rf\s+"?\$HOME',
        r'rm\s+-rf\s+/?\*',
        r'format\s+[:\/]',
        r'mkfs\.',
        r'dd\s+if=.*of=/dev/',
        r'>\s*/dev/',
        r'del\s+/f\s+/s\s+/q\s+c:\\',
        r'rd\s+/s\s+/q\s+c:\\',
        
        # Security risks
        r'curl.*\|\s*bash',
        r'wget.*\|\s*bash',
        r'fetch.*\|\s*sh',
        r'powershell.*-enc',
        r'Invoke-Expression',
        r'net\s+user.*admin',
        r'reg\s+delete.*HKLM',
        
        # Network attacks
        r'ping\s+-f',
        r'hping3',
        r'nmap\s+-sS',
    ]
    
    # Commands that require confirmation
    DESTRUCTIVE_KEYWORDS = [
        'delete', 'remove', 'rm -', 'del ', 'rmdir', 'rd ',
        'overwrite', 'replace', 'truncate', 'drop', 
        'chmod -R', 'chown -R', 'attrib -',
        'kill ', 'pkill', 'taskkill /f',
        'shutdown', 'reboot', 'poweroff', 'halt',
        'format', 'partition', 'fdisk',
    ]
    
    # Sensitive file patterns
    SENSITIVE_PATHS = [
        r'\.ssh/',
        r'\.gnupg/',
        r'\.aws/',
        r'\.env$',
        r'password',
        r'secret',
        r'token',
        r'key\.pem',
        r'\.p12$',
        r'\.pfx$',
    ]
    
    def __init__(self, data_dir: Path = None):
        self.data_dir = data_dir or Path.home() / ".phoenix" / "safety"
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        self.audit_log_path = self.data_dir / "audit.log"
        self.confirmation_callback: Optional[Callable[[str], asyncio.Future[bool]]] = None
        
        # Compile patterns for efficiency
        self.dangerous_patterns = [re.compile(p, re.IGNORECASE) for p in self.DANGEROUS_PATTERNS]
        self.sensitive_patterns = [re.compile(p, re.IGNORECASE) for p in self.SENSITIVE_PATHS]
        
        print(f"✓ SafetyGuard initialized")
    
    def set_confirmation_callback(self, callback: Callable[[str], asyncio.Future[bool]]):
        """Set callback for user confirmation"""
        self.confirmation_callback = callback
    
    async def check(self, action: str, context: Dict[str, Any] = None) -> SafetyDecision:
        """
        Check if an action is safe to execute.
        
        Args:
            action: The action/command to check
            context: Additional context (user, target_path, etc.)
        
        Returns:
            SafetyDecision with allow/block status and reason
        """
        context = context or {}
        action_lower = action.lower()
        
        # Check 1: Dangerous patterns (always block)
        for pattern in self.dangerous_patterns:
            if pattern.search(action):
                reason = f"Blocked dangerous pattern: {pattern.pattern[:30]}..."
                await self._log_decision(action, False, reason, context)
                return SafetyDecision(
                    allowed=False,
                    risk_level=RiskLevel.DANGEROUS,
                    reason=reason,
                    requires_confirmation=False,
                    action=action
                )
        
        # Check 2: Destructive keywords (require confirmation)
        for keyword in self.DESTRUCTIVE_KEYWORDS:
            if keyword in action_lower:
                # Extra check for sensitive paths
                sensitive_path = self._check_sensitive_path(action)
                
                reason = f"Destructive action detected: '{keyword}'"
                if sensitive_path:
                    reason += f" affecting sensitive path"
                
                confirmation_prompt = self._generate_confirmation_prompt(action, keyword, sensitive_path)
                
                await self._log_decision(action, True, reason, context, confirmation_required=True)
                
                return SafetyDecision(
                    allowed=True,  # Allowed but requires confirmation
                    risk_level=RiskLevel.CAUTION,
                    reason=reason,
                    requires_confirmation=True,
                    confirmation_prompt=confirmation_prompt,
                    action=action
                )
        
        # Check 3: Sensitive paths (warn but allow)
        if self._check_sensitive_path(action):
            reason = "Action may affect sensitive files"
            await self._log_decision(action, True, reason, context)
            
            return SafetyDecision(
                allowed=True,
                risk_level=RiskLevel.CAUTION,
                reason=reason,
                requires_confirmation=False,  # Just warn, don't require confirmation
                action=action
            )
        
        # Safe action
        await self._log_decision(action, True, "Safe action", context)
        
        return SafetyDecision(
            allowed=True,
            risk_level=RiskLevel.SAFE,
            reason="Action appears safe",
            requires_confirmation=False,
            action=action
        )
    
    def _check_sensitive_path(self, action: str) -> bool:
        """Check if action affects sensitive paths"""
        for pattern in self.sensitive_patterns:
            if pattern.search(action):
                return True
        return False
    
    def _generate_confirmation_prompt(self, action: str, keyword: str, sensitive: bool) -> str:
        """Generate a user-friendly confirmation prompt"""
        prompt = f"⚠️  Destructive action detected\n\n"
        prompt += f"Action: {action[:100]}"
        if len(action) > 100:
            prompt += "..."
        prompt += f"\n\nDetected: {keyword.strip()}"
        
        if sensitive:
            prompt += "\n⚠️  This may affect sensitive files!"
        
        prompt += "\n\nDo you want to proceed? (yes/no)"
        
        return prompt
    
    async def confirm(self, decision: SafetyDecision) -> bool:
        """
        Get user confirmation for a decision.
        
        Args:
            decision: The safety decision requiring confirmation
        
        Returns:
            True if user confirms, False otherwise
        """
        if not decision.requires_confirmation:
            return True
        
        if self.confirmation_callback:
            return await self.confirmation_callback(decision.confirmation_prompt)
        else:
            # Fallback: print and ask via input (blocking)
            print(decision.confirmation_prompt)
            response = input("> ").lower().strip()
            return response in ('yes', 'y', 'true', '1')
    
    async def check_and_confirm(self, action: str, context: Dict = None) -> bool:
        """
        Check action and get confirmation if needed.
        
        Returns True if action is allowed (either safe or confirmed)
        """
        decision = await self.check(action, context)
        
        if not decision.allowed:
            print(f"❌ Blocked: {decision.reason}")
            return False
        
        if decision.requires_confirmation:
            confirmed = await self.confirm(decision)
            await self._log_confirmation(action, confirmed)
            return confirmed
        
        return True
    
    async def _log_decision(
        self, 
        action: str, 
        allowed: bool, 
        reason: str, 
        context: Dict,
        confirmation_required: bool = False
    ):
        """Log safety decision to audit log"""
        entry = {
            "timestamp": datetime.now().isoformat(),
            "action": action[:200],
            "allowed": allowed,
            "reason": reason,
            "context": context,
            "confirmation_required": confirmation_required
        }
        
        with open(self.audit_log_path, 'a') as f:
            f.write(json.dumps(entry) + '\n')
    
    async def _log_confirmation(self, action: str, confirmed: bool):
        """Log user confirmation"""
        entry = {
            "timestamp": datetime.now().isoformat(),
            "action": action[:200],
            "event": "user_confirmation",
            "confirmed": confirmed
        }
        
        with open(self.audit_log_path, 'a') as f:
            f.write(json.dumps(entry) + '\n')
    
    def get_recent_blocks(self, hours: int = 24) -> List[Dict]:
        """Get recent blocked actions"""
        from datetime import timedelta
        
        cutoff = datetime.now() - timedelta(hours=hours)
        blocks = []
        
        if not self.audit_log_path.exists():
            return blocks
        
        with open(self.audit_log_path, 'r') as f:
            for line in f:
                try:
                    entry = json.loads(line.strip())
                    entry_time = datetime.fromisoformat(entry['timestamp'])
                    if entry_time > cutoff and not entry.get('allowed', True):
                        blocks.append(entry)
                except (json.JSONDecodeError, KeyError):
                    continue
        
        return blocks
    
    def get_audit_summary(self, hours: int = 24) -> Dict:
        """Get summary of recent audit activity"""
        from datetime import timedelta
        
        cutoff = datetime.now() - timedelta(hours=hours)
        
        total = 0
        allowed = 0
        blocked = 0
        confirmations = 0
        
        if self.audit_log_path.exists():
            with open(self.audit_log_path, 'r') as f:
                for line in f:
                    try:
                        entry = json.loads(line.strip())
                        entry_time = datetime.fromisoformat(entry['timestamp'])
                        if entry_time > cutoff:
                            total += 1
                            if entry.get('allowed', True):
                                allowed += 1
                            else:
                                blocked += 1
                            if entry.get('confirmation_required'):
                                confirmations += 1
                    except (json.JSONDecodeError, KeyError):
                        continue
        
        return {
            "total_actions": total,
            "allowed": allowed,
            "blocked": blocked,
            "requiring_confirmation": confirmations,
            "period_hours": hours
        }


# Predefined safety profiles
class SafetyProfiles:
    """Predefined safety configurations"""
    
    @staticmethod
    def strict() -> Dict:
        """Strict profile - confirm almost everything"""
        return {
            "confirm_destructive": True,
            "confirm_file_ops": True,
            "confirm_network": True,
            "confirm_system": True,
        }
    
    @staticmethod
    def balanced() -> Dict:
        """Balanced profile - confirm destructive only"""
        return {
            "confirm_destructive": True,
            "confirm_file_ops": False,
            "confirm_network": False,
            "confirm_system": True,
        }
    
    @staticmethod
    def trusting() -> Dict:
        """Trusting profile - minimal confirmations"""
        return {
            "confirm_destructive": True,
            "confirm_file_ops": False,
            "confirm_network": False,
            "confirm_system": False,
        }


# Singleton instance
_guard_instance: Optional[SafetyGuard] = None


def get_safety_guard(data_dir: Path = None) -> SafetyGuard:
    """Get or create the singleton safety guard instance"""
    global _guard_instance
    if _guard_instance is None:
        _guard_instance = SafetyGuard(data_dir)
    return _guard_instance


async def demo():
    """Demo the safety guard"""
    guard = SafetyGuard()
    
    test_actions = [
        # Safe actions
        ("ls -la", "Safe list command"),
        ("cat file.txt", "Safe read command"),
        ("echo 'hello'", "Safe echo command"),
        
        # Destructive (require confirmation)
        ("rm -rf /tmp/old_files", "Destructive delete"),
        ("delete ~/Downloads/temp.zip", "File deletion"),
        
        # Dangerous (blocked)
        ("rm -rf /", "System destruction"),
        ("format C:", "Drive format"),
        ("dd if=/dev/zero of=/dev/sda", "Disk wipe"),
        
        # Sensitive paths
        ("cat ~/.ssh/id_rsa", "Sensitive file access"),
    ]
    
    print("\n--- Safety Check Demo ---\n")
    
    for action, description in test_actions:
        print(f"Test: {description}")
        print(f"Action: {action}")
        
        decision = await guard.check(action)
        
        if decision.risk_level == RiskLevel.DANGEROUS:
            print(f"Result: ❌ BLOCKED - {decision.reason}")
        elif decision.risk_level == RiskLevel.CAUTION:
            print(f"Result: ⚠️  CAUTION - {decision.reason}")
            print(f"Requires confirmation: {decision.requires_confirmation}")
        else:
            print(f"Result: ✅ SAFE - {decision.reason}")
        
        print()
    
    # Show audit summary
    print("\n--- Audit Summary ---")
    summary = guard.get_audit_summary(hours=1)
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    asyncio.run(demo())
