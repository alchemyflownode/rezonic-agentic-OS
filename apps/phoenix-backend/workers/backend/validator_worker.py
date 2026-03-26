# backend/workers/validator_worker.py
import logging
import asyncio
from typing import Dict, Any
from .base_worker import BaseWorker

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
            return {"content": "🛡️ **Validator Ready.** Type `/audit system` or ask to `validate drift locks`."}

    async def _run_system_audit(self) -> dict:
        logger.info("🛡️ [VALIDATOR] Running full system cryptographic audit...")
        
        if not self.constitution:
            return {"content": "❌ **Audit Failed:** Constitution module not mounted."}

        total_rulings = len(self.constitution.rulings)
        valid_seals = 0
        corrupted =[]

        # Verify every historical ruling's cryptographic seal
        for ruling in self.constitution.rulings:
            action = ruling.get('action', {})
            violations = ruling.get('violations',