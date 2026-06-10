#!/usr/bin/env python3
"""
workers/simple_test_worker.py — Simple Test Worker
"""

import datetime
import logging
from typing import Any, Dict

# Import base worker with fallback
try:
    from workers.base_worker import Worker
except ImportError:
    from base_worker import Worker

logger = logging.getLogger("phoenix.simple_test")


class SimpleTestWorker(Worker):
    """Simple worker for testing purposes."""

    name = "simple_test_worker"
    version = "1.0.0"
    description = "Simple test worker for validation"

    def __init__(self) -> None:
        super().__init__("simple_test_worker")
        self._initialized = False
        self._start_time = None
        self.execution_count = 0
        self.error_count = 0
        self.test_results = []

    async def initialize(self) -> None:
        """Initialize the worker."""
        if self._initialized:
            return
        self._initialized = True
        self._start_time = datetime.datetime.now()
        logger.info("SimpleTestWorker initialized")

    async def execute(self, task: str, **kwargs: Any) -> Dict[str, Any]:
        """Execute a test task."""
        self.execution_count += 1

        test_value = kwargs.get("test_value", "default")
        self.test_results.append({
            "task": task[:100],
            "value": test_value,
            "timestamp": datetime.datetime.now().isoformat(),
        })

        return {
            "success": True,
            "worker": self.name,
            "message": f"Test executed: {task[:50]}",
            "test_value": test_value,
            "results_count": len(self.test_results),
            "timestamp": datetime.datetime.now().isoformat(),
        }

    async def health_check(self) -> Dict[str, Any]:
        """Return worker health status."""
        return {
            "name": self.name,
            "version": self.version,
            "status": "healthy" if self._initialized else "not_initialized",
            "initialized": self._initialized,
            "executions": self.execution_count,
            "errors": self.error_count,
            "test_count": len(self.test_results),
        }
