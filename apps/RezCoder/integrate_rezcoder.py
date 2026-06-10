#!/usr/bin/env python3
"""
integrate_rezcoder.py — Patch kernel.py to register RezCoder
=============================================================

Safely adds:
  - Import statement
  - Worker registration in builtins
  - Reflex command /rez-review
  - API endpoints (health, review, fix)

Idempotent: safe to run multiple times.

Usage:
    python integrate_rezcoder.py
    python integrate_rezcoder.py --dry-run
"""

from __future__ import annotations

import argparse
import re
import shutil
import sys
from pathlib import Path


KERNEL_PATH = Path("kernel.py")

# ── Patches to apply (order matters) ────────────────────

IMPORT_LINE = "from workers.rezcoder import RezCoderWorker"
IMPORT_MARKER = "RezCoderWorker"

BUILTIN_ENTRY = '    ("rezcoder", RezCoderWorker),'
BUILTIN_MARKER = '"rezcoder"'

REFLEX_BLOCK = '''
    # ── RezCoder reflex commands ──────────────────────
    def _register_rezcoder_commands(self):
        """Register /rez-review command with the reflex system."""
        async def cmd_rez_review(cmd: str):
            parts = cmd.split(maxsplit=1)
            if len(parts) < 2:
                return {
                    "type": "reflex",
                    "content": "Usage: /rez-review <filepath>",
                }
            worker = self.workers.get("rezcoder", {}).get("instance")
            if not worker:
                return {
                    "type": "reflex",
                    "content": "❌ RezCoder worker not loaded",
                }
            await worker.initialize()
            result = await worker.execute(
                "review", file_path=parts[1]
            )
            if not result.get("success"):
                return {
                    "type": "reflex",
                    "content": f"❌ {result.get('error', 'unknown')}",
                }
            return {
                "type": "reflex",
                "content": (
                    f"📊 Health: {result['health_score']}/100\\n"
                    f"Issues: {result['total_issues']} "
                    f"({result['error_count']} errors, "
                    f"{result['warning_count']} warnings)"
                ),
            }

        if hasattr(self, "reflex") and hasattr(self.reflex, "commands"):
            self.reflex.commands["/rez-review"] = cmd_rez_review
            logger.info("✅ RezCoder /rez-review command registered")
'''

API_BLOCK = '''
        # ══════════ REZCODER API ══════════

        @self.app.get("/api/v1/rezcoder/health")
        async def api_rezcoder_health():
            """RezCoder worker health and statistics."""
            worker = self.workers.get("rezcoder", {}).get("instance")
            if not worker:
                return JSONResponse(
                    {"error": "RezCoder not available"},
                    status_code=503,
                )
            return await worker.health_check()

        @self.app.get("/api/v1/rezcoder/review")
        async def api_rezcoder_review(
            filepath: str,
            recursive: bool = False,
        ):
            """Review a file or directory for issues."""
            worker = self.workers.get("rezcoder", {}).get("instance")
            if not worker:
                return JSONResponse(
                    {"error": "RezCoder not available"},
                    status_code=503,
                )
            await worker.initialize()
            return await worker.execute(
                "review",
                file_path=filepath,
                recursive=recursive,
            )

        @self.app.post("/api/v1/rezcoder/fix")
        async def api_rezcoder_fix(
            filepath: str,
            confidence: float = 0.8,
            backup: bool = True,
        ):
            """Apply auto-fixes to a file."""
            worker = self.workers.get("rezcoder", {}).get("instance")
            if not worker:
                return JSONResponse(
                    {"error": "RezCoder not available"},
                    status_code=503,
                )
            await worker.initialize()
            return await worker.execute(
                "fix",
                file_path=filepath,
                confidence=confidence,
                backup=backup,
            )

        @self.app.get("/api/v1/rezcoder/report")
        async def api_rezcoder_report(filepath: str):
            """Generate a Markdown review report."""
            worker = self.workers.get("rezcoder", {}).get("instance")
            if not worker:
                return JSONResponse(
                    {"error": "RezCoder not available"},
                    status_code=503,
                )
            await worker.initialize()
            return await worker.execute(
                "report", file_path=filepath,
            )
'''


def patch_kernel(dry_run: bool = False) -> None:
    """Apply all RezCoder patches to kernel.py."""

    if not KERNEL_PATH.exists():
        print(f"❌ {KERNEL_PATH} not found. Run from phoenix-kernel/")
        sys.exit(1)

    content = KERNEL_PATH.read_text(encoding="utf-8")
    original = content
    changes: list[str] = []

    # ── 1. Add import ────────────────────────────────────
    if IMPORT_MARKER not in content:
        # Find last worker import line
        last_import_match = None
        for m in re.finditer(
            r"^from workers\.\w+ import \w+.*$",
            content, re.MULTILINE,
        ):
            last_import_match = m

        if last_import_match:
            pos = last_import_match.end()
            content = (
                content[:pos]
                + f"\n{IMPORT_LINE}"
                + content[pos:]
            )
            changes.append(f"Added import: {IMPORT_LINE}")
        else:
            # Fallback: add after last 'import' line
            lines = content.split("\n")
            last_import_idx = 0
            for i, line in enumerate(lines):
                if line.startswith("import ") or line.startswith("from "):
                    last_import_idx = i
            lines.insert(last_import_idx + 1, IMPORT_LINE)
            content = "\n".join(lines)
            changes.append(f"Added import (fallback): {IMPORT_LINE}")
    else:
        print("  ✓ Import already present")

    # ── 2. Add to builtins ───────────────────────────────
    if BUILTIN_MARKER not in content:
        # Find the builtins list closing bracket
        builtins_match = re.search(
            r"(builtins\s*=\s*\[)(.*?)(]\s*\n)",
            content,
            re.DOTALL,
        )
        if builtins_match