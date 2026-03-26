# constitutional_governor.py - FIXED
from typing import Dict, Any, Optional
import asyncio
import logging

logger = logging.getLogger("PHOENIX_ULTIMATE")

class ConstitutionalGovernorWorker:
    """Governor that enforces constitutional compliance"""
    
    def __init__(self):
        self.name = "ConstitutionalGovernorWorker"
        self.governance_actions = []
        self.veto_power = True
        logger.info(f"✅ {self.name} initialized")
    
    async def execute(self, proposal: Dict[str, Any]) -> Dict[str, Any]:
        """Review and approve/reject proposals"""
        
        # Governance logic
        approved = True
        reasons = []
        
        # Check for constitutional violations
        if proposal.get('action') in ['delete', 'remove', 'wipe']:
            approved = False
            reasons.append("Destructive actions require admin approval")
        
        decision = {
            "timestamp": asyncio.get_event_loop().time(),
            "proposal_id": proposal.get('id', 'unknown'),
            "approved": approved,
            "reasons": reasons,
            "veto_used": not approved and self.veto_power
        }
        
        self.governance_actions.append(decision)
        
        return {
            "worker": self.name,
            "decision": decision,
            "governance_count": len(self.governance_actions)
        }
    
    async def get_stats(self) -> Dict:
        approved = sum(1 for a in self.governance_actions if a['approved'])
        return {
            "name": self.name,
            "total_decisions": len(self.governance_actions),
            "approved": approved,
            "vetoed": len(self.governance_actions) - approved,
            "veto_power": self.veto_power
        }
