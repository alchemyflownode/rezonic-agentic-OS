#!/usr/bin/env python3
"""
workers/sandbox_worker.py — Secure Code Execution Sandbox
"""

from __future__ import annotations

import asyncio
import datetime
import logging
import os
import platform
import re
import sys
import tempfile
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

try:
    from workers.base_worker import Worker
except ImportError:
    try:
        from base_worker import Worker
    except ImportError:
        class Worker:
            def __init__(self, name: str = "worker") -> None:
                self.name = name
                self.execution_count = 0
                self.error_count = 0
            async def initialize(self) -> None:
                pass
            async def execute(self, task: str, **kwargs: Any) -> Dict[str, Any]:
                return {"error": "not implemented"}
            async def health_check(self) -> Dict[str, Any]:
                return {"status": "unknown"}

logger = logging.getLogger("phoenix.sandbox")
IS_WINDOWS = platform.system() == "Windows"

SANDBOX_CONFIG = {
    "timeout_seconds": 30,
    "max_stdout_bytes": 10000,
    "max_stderr_bytes": 5000,
    "max_code_length": 50000,
}

BLOCKED_PATTERNS = [
    (re.compile(r"\bos\.system\s*\("), "os.system()"),
    (re.compile(r"\beval\s*\("), "eval()"),
    (re.compile(r"\bexec\s*\("), "exec()"),
    (re.compile(r"\b__import__\s*\("), "__import__()"),
    (re.compile(r"\bimportlib\b"), "importlib"),
    (re.compile(r"\bctypes\b"), "ctypes"),
    (re.compile(r"\bsubprocess\b"), "subprocess"),
    (re.compile(r"^\s*import\s+os\b", re.MULTILINE), "import os"),
    (re.compile(r"^\s*import\s+sys\b", re.MULTILINE), "import sys"),
]

def _build_safe_env() -> Dict[str, str]:
    safe_env = {}
    keep = {"PATH", "HOME", "USER", "LANG"} if not IS_WINDOWS else {"PATH", "TEMP", "SYSTEMROOT"}
    for k in keep:
        v = os.environ.get(k)
        if v:
            safe_env[k] = v
    return safe_env


class SandboxWorker(Worker):
    name = "sandbox_worker"
    version = "2.0.0"

    def __init__(self) -> None:
        super().__init__("sandbox_worker")
        self.timeout = SANDBOX_CONFIG["timeout_seconds"]
        self.max_stdout = SANDBOX_CONFIG["max_stdout_bytes"]
        self.max_stderr = SANDBOX_CONFIG["max_stderr_bytes"]
        self.max_code_length = SANDBOX_CONFIG["max_code_length"]
        self._initialized = False
        self._start_time = None
        self.success_count = 0
        self.timeout_count = 0
        self.blocked_count = 0

    async def initialize(self) -> None:
        if self._initialized:
            return
        self._initialized = True
        self._start_time = datetime.datetime.now()
        logger.info(f"SandboxWorker initialized")

    async def execute(self, task: str, **kwargs: Any) -> Dict[str, Any]:
        if not self._initialized:
            await self.initialize()

        self.execution_count += 1
        start_time = time.monotonic()
        timeout = max(1, min(kwargs.get("timeout", self.timeout), 120))

        code = self._extract_code(task)

        if not code.strip():
            return self._response(False, error="No code provided", elapsed=time.monotonic() - start_time)

        if len(code) > self.max_code_length:
            return self._response(False, error=f"Code too long", elapsed=time.monotonic() - start_time)

        violations = self._scan_for_violations(code)
        if violations:
            self.blocked_count += 1
            return self._response(False, error="Dangerous code detected", violations=violations)

        try:
            with tempfile.TemporaryDirectory() as tmpdir:
                script_path = Path(tmpdir) / "script.py"
                script_path.write_text(code, encoding="utf-8")

                proc = await asyncio.create_subprocess_exec(
                    sys.executable, "-u", str(script_path),
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                    cwd=tmpdir, env=_build_safe_env(),
                )

                try:
                    stdout_raw, stderr_raw = await asyncio.wait_for(proc.communicate(), timeout=timeout)
                except asyncio.TimeoutError:
                    proc.kill()
                    await proc.wait()
                    self.timeout_count += 1
                    return self._response(False, error=f"Timeout after {timeout}s", timed_out=True)

                stdout = stdout_raw.decode("utf-8", errors="replace")[:self.max_stdout]
                stderr = stderr_raw.decode("utf-8", errors="replace")[:self.max_stderr]

                if proc.returncode == 0:
                    self.success_count += 1
                else:
                    self.error_count += 1

                return self._response(proc.returncode == 0, stdout=stdout, stderr=stderr, returncode=proc.returncode)

        except Exception as e:
            self.error_count += 1
            return self._response(False, error=str(e))

    def _extract_code(self, task: str) -> str:
        match = re.search(r"```(?:python|py)?\s*\n(.*?)\n\s*```", task, re.DOTALL)
        if match:
            return match.group(1).strip()
        match = re.search(r"```\s*\n(.*?)\n\s*```", task, re.DOTALL)
        if match:
            return match.group(1).strip()
        return task.strip()

    @staticmethod
    def _scan_for_violations(code: str) -> List[str]:
        violations = []
        for pattern, desc in BLOCKED_PATTERNS:
            if pattern.search(code):
                violations.append(desc)
        return violations

    def _response(self, success: bool, elapsed: float = 0.0, **extra: Any) -> Dict[str, Any]:
        return {"success": success, "worker": self.name, "elapsed_seconds": round(elapsed, 3), **extra}

    async def health_check(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "status": "healthy" if self._initialized else "not_initialized",
            "executions": self.execution_count,
            "errors": self.error_count,
            "successes": self.success_count,
            "timeouts": self.timeout_count,
            "blocked": self.blocked_count,
        }
