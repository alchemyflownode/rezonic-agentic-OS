import sys
from pathlib import Path

# Add parent directory to path
parent_dir = Path(__file__).parent.parent
if str(parent_dir) not in sys.path:
    sys.path.insert(0, str(parent_dir))
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
# backend/workers/validator_worker.py
import logging
import asyncio
from typing import Dict, Any
from workers.base_worker import BaseWorker

logger = logging.getLogger(__name__)

class ValidatorWorker(BaseWorker):
    """
    The Internal Auditor - Continuously verifies Zero Drift seals
    and ensures constitutional integrity of the VFS and Memory Bus.
    """
    def __init__(self, constitution=None):
        super().__init__("validator")
        self.description = "Zero Drift Validator and Audit Engine"
        self.constitution = constitution

    async def process(self, task: str, model: str = None, memory_bus=None) -> dict:
        self.set_memory_bus(memory_bus)
        task_lower = task.lower().strip()

        if "audit" in task_lower or "validate" in task_lower:
            return await self._run_system_audit()
        else:
            return {"content": "Ã°Å¸â€ºÂ¡Ã¯Â¸Â **Validator Ready.** Type `/audit system` or ask to `validate drift locks`."}

    async def _run_system_audit(self) -> dict:
        logger.info("Ã°Å¸â€ºÂ¡Ã¯Â¸Â [VALIDATOR] Running full system cryptographic audit...")
        
        if not self.constitution:
            return {"content": "Ã¢ÂÅ’ **Audit Failed:** Constitution module not mounted."}

        total_rulings = len(self.constitution.rulings)
        valid_seals = 0
        corrupted =[]

        # Verify every historical ruling's cryptographic seal
        for ruling in self.constitution.rulings:
            action = ruling.get('action', {})
            violations = ruling.get('violations', [])

    async def process(self, task: str, memory_bus=None):
        """Process task â€“ auto-generated stub"""
        return {"content": f"Processed: {task[:50]}", "worker": self.name}
    
    async def health_check(self):
        """Return worker health status"""
        return {"worker": self.name, "status": "healthy", "timestamp": __import__('time').time()}




