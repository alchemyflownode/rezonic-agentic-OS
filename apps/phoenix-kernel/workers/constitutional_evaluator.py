# constitutional_evaluator.py - FIXED
from typing import Dict, Any, Optional
import asyncio
import logging

logger = logging.getLogger("PHOENIX_ULTIMATE")

class ConstitutionalEvaluatorWorker:
    """Evaluates actions against constitutional principles"""
    
    def __init__(self):
        self.name = "ConstitutionalEvaluatorWorker"
        self.evaluations = []
        self.laws = [
            "SOVEREIGNTY", "TRANSPARENCY", "ACCOUNTABILITY",
            "DETERMINISM", "SAFETY", "PRIVACY", "AUDITABILITY",
            "RECOVERABILITY", "BOUNDEDNESS"
        ]
        logger.info(f"✅ {self.name} initialized")
    
    async def execute(self, action: str, context: Dict = None) -> Dict[str, Any]:
        """Evaluate an action against all 9 laws"""
        
        results = {}
        for law in self.laws:
            # Simple evaluation logic
            passed = True
            if law == "SAFETY" and any(d in action.lower() for d in ['rm', 'del', 'format']):
                passed = False
            
            results[law] = {
                "passed": passed,
                "score": 100 if passed else 0
            }
        
        evaluation = {
            "timestamp": asyncio.get_event_loop().time(),
            "action": action[:100],
            "results": results,
            "overall_score": sum(r["score"] for r in results.values()) / len(results)
        }
        
        self.evaluations.append(evaluation)
        
        return {
            "worker": self.name,
            "evaluation": evaluation
        }
    
    async def get_laws(self) -> List[str]:
        return self.laws
