# workers/base_worker.py
"""
Base Worker Module — Foundation for all Phoenix kernel workers.

Every worker inherits from Worker and implements:
    - execute(task, **kwargs)  — main functionality
    - initialize()             — async setup (called before first execute)
    - health_check()           — status reporting
    - cleanup()                — graceful shutdown

The kernel calls these in order:
    __init__() → initialize() → execute() → ... → cleanup()
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional


class Worker(ABC):
    """
    Abstract base class for all Phoenix kernel workers.

    Subclasses MUST implement:
        execute(task: str, **kwargs) -> Dict[str, Any]

    Subclasses MAY override:
        initialize()   — async setup (DB connections, model loading, etc.)
        health_check() — custom health reporting
        cleanup()      — release resources on shutdown

    Attributes:
        name:            Worker identifier (used in kernel registry)
        version:         Semantic version string
        description:     Human-readable purpose
        execution_count: Total execute() calls
        error_count:     Total failed execute() calls
    """

    def __init__(self, name: str) -> None:
        self.name: str = name
        self.version: str = "1.0.0"
        self.description: str = ""
        self.execution_count: int = 0
        self.error_count: int = 0
        self._initialized: bool = False

    async def initialize(self) -> None:
        """
        Async initialization — called by kernel before first execute().

        Override this for:
            - Database connections
            - Model loading
            - External service setup
            - File system preparation

        Safe to call multiple times (idempotent by default).
        """
        self._initialized = True

    @abstractmethod
    async def execute(self, task: str, **kwargs: Any) -> Dict[str, Any]:
        """
        Execute the worker's main functionality.

        Args:
            task: Command string or task description
            **kwargs: Additional parameters

        Returns:
            Dict with at minimum {"success": bool}
        """
        ...

    async def health_check(self) -> Dict[str, Any]:
        """
        Report worker health status.

        Returns:
            Dict with status, version, and worker-specific metrics.
        """
        return {
            "name": self.name,
            "version": self.version,
            "status": "healthy" if self._initialized else "not_initialized",
            "initialized": self._initialized,
            "executions": self.execution_count,
            "errors": self.error_count,
        }

    async def cleanup(self) -> None:
        """
        Graceful shutdown — release resources.

        Override this to close:
            - Database connections
            - File handles
            - Network sessions
            - Background tasks
        """
        pass

    def __repr__(self) -> str:
        return (
            f"<{self.__class__.__name__} "
            f"name='{self.name}' v{self.version}>"
        )


class BaseWorker(Worker):
    """Alias for Worker — backward compatibility."""
    pass