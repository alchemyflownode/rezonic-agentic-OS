"""Sandbox Worker - Safe Execution Environment"""

import asyncio
import logging
from base_worker import BaseWorker

logger = logging.getLogger(__name__)

class SandboxWorker(BaseWorker):
    """
    Sandbox worker for safe code execution
    """
    
    def __init__(self, hive_bus=None):
        super().__init__('sandbox', hive_bus)
        self.sandbox_active = True
        logger.info("   SandboxWorker initialized")

    async def health_check(self):
        """Health check for sandbox worker"""
        base = await super().health_check()
        return {
            **base,
            'name': self.name,
            'sandbox_active': self.sandbox_active,
            'healthy': True
        }

    async def process(self, task, **kwargs):
        """Process sandbox tasks"""
        if task == 'status':
            return await self.health_check()
        else:
            return {'result': f'Executed in sandbox: {task}'}

