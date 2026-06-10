#!/usr/bin/env python3
"""
workers/rezcoder.py — RezCoder: Phoenix Kernel Code Intelligence Worker
"""

from __future__ import annotations

import asyncio
import datetime
import json
import logging
import sys
import traceback
from pathlib import Path
from typing import Any, Optional

# Add parent directory to path
KERNEL_DIR = Path(__file__).resolve().parent.parent
if str(KERNEL_DIR) not in sys.path:
    sys.path.insert(0, str(KERNEL_DIR))

# Import code-worker directly (file is now in the kernel directory)
try:
    import code_worker
    logger = logging.getLogger("phoenix.rezcoder")
    logger.info(f"✅ Loaded code_worker from {code_worker.__file__}")
except ImportError as e:
    logger = logging.getLogger("phoenix.rezcoder")
    logger.error(f"❌ Cannot import code_worker: {e}")
    code_worker = None


class RezCoderWorker:
    """Phoenix Kernel worker for code review and auto-fix."""

    name = "rezcoder"
    version = "1.0.0"

    def __init__(self) -> None:
        self._engine: Optional[Any] = None
        self._initialized = False
        self._review_count = 0
        self._fix_count = 0
        self._total_issues = 0
        self._start_time: Optional[datetime.datetime] = None

    async def initialize(self) -> None:
        """Create the ReviewEngine."""
        if self._initialized:
            return

        if code_worker is None:
            raise ImportError("code-worker module not available")

        self._engine = code_worker.ReviewEngine(
            fix_confidence=0.7,
            dry_run=False,
            verbose=False,
        )
        self._initialized = True
        self._start_time = datetime.datetime.now()

        print(f"🦎 RezCoder initialized — {len(self._engine.analyzers)} analyzers, {len(self._engine.fixers)} fixers")

    async def execute(self, action: str, **kwargs) -> dict[str, Any]:
        """Execute a review, fix, report, or health action."""
        if not self._initialized:
            await self.initialize()

        handlers = {
            "review": self._handle_review,
            "fix": self._handle_fix,
            "report": self._handle_report,
            "health": self._handle_health,
        }

        handler = handlers.get(action)
        if not handler:
            return {"success": False, "error": f"Unknown action: {action}"}

        try:
            return await handler(**kwargs)
        except Exception as e:
            return {"success": False, "error": str(e), "traceback": traceback.format_exc()}

    async def _handle_review(self, file_path: str = "", recursive: bool = False, **kwargs) -> dict:
        """Review a file or directory."""
        if not file_path:
            return {"success": False, "error": "file_path required"}

        target = Path(file_path)
        if not target.exists():
            return {"success": False, "error": f"Path not found: {file_path}"}

        loop = asyncio.get_event_loop()

        if target.is_file():
            result = await loop.run_in_executor(None, self._engine.review_file, target)
            self._review_count += 1
            self._total_issues += len(result.issues)
            return result.to_dict()

        # Directory scan
        files = code_worker.discover_files(target, recursive=recursive)
        results = []
        for f in files:
            r = await loop.run_in_executor(None, self._engine.review_file, f)
            self._review_count += 1
            self._total_issues += len(r.issues)
            results.append(r.to_dict())

        return {
            "success": True,
            "files_reviewed": len(results),
            "results": results,
            "total_issues": sum(r["total_issues"] for r in results),
        }

    async def _handle_fix(self, file_path: str = "", confidence: float = 0.7, backup: bool = True, dry_run: bool = False, **kwargs) -> dict:
        """Apply auto-fixes."""
        if not file_path:
            return {"success": False, "error": "file_path required"}

        target = Path(file_path)
        if not target.is_file():
            return {"success": False, "error": f"Not a file: {file_path}"}

        old_conf = self._engine.fix_confidence
        old_dry = self._engine.dry_run
        self._engine.fix_confidence = confidence
        self._engine.dry_run = dry_run

        loop = asyncio.get_event_loop()
        try:
            result = await loop.run_in_executor(None, self._engine.review_file, target)
            self._fix_count += 1
            response = result.to_dict()
            response["fixes_applied"] = result.fixes_applied
            response["fixes_skipped"] = result.fixes_skipped
            return response
        finally:
            self._engine.fix_confidence = old_conf
            self._engine.dry_run = old_dry

    async def _handle_report(self, file_path: str = "", **kwargs) -> dict:
        """Generate Markdown report."""
        if not file_path:
            return {"success": False, "error": "file_path required"}

        target = Path(file_path)
        if not target.is_file():
            return {"success": False, "error": f"Not a file: {file_path}"}

        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(None, self._engine.review_file, target)

        report_path = target.with_suffix(target.suffix + code_worker.REPORT_SUFFIX)
        reporter = code_worker.ReportGenerator()
        await loop.run_in_executor(None, reporter.write_markdown, result, report_path)

        return {"success": True, "report_path": str(report_path), "health_score": result.health_score}

    async def _handle_health(self, **kwargs) -> dict:
        """Return health status."""
        uptime = None
        if self._start_time:
            uptime = str(datetime.datetime.now() - self._start_time)

        return {
            "success": True,
            "worker": self.name,
            "initialized": self._initialized,
            "uptime": uptime,
            "stats": {
                "reviews": self._review_count,
                "fixes": self._fix_count,
                "total_issues": self._total_issues,
            },
            "analyzers": [a.name for a in self._engine.analyzers] if self._engine else [],
            "fixers": [f.name for f in self._engine.fixers] if self._engine else [],
        }

    async def health_check(self) -> dict:
        """Alias for kernel compatibility."""
        return await self._handle_health()