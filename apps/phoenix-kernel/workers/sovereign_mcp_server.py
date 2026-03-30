#!/usr/bin/env python3
"""
workers/sovereign_mcp_server.py — Sovereign MCP Protocol Server
"""

from __future__ import annotations

import asyncio
import datetime
import hashlib
import json
import logging
import time
import traceback
from pathlib import Path
from typing import Any, Dict, List, Optional, Callable, Coroutine

# Import base worker with fallback
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

# Import RezCoder
try:
    import importlib.util
    _cw_path = Path(__file__).parent.parent / "code_worker.py"
    if _cw_path.exists():
        spec = importlib.util.spec_from_file_location("code_worker", str(_cw_path))
        code_worker = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(code_worker)
    else:
        import code_worker
    CODE_WORKER_AVAILABLE = True
except Exception as e:
    CODE_WORKER_AVAILABLE = False
    code_worker = None
    print(f"Warning: code_worker not available: {e}")

logger = logging.getLogger("phoenix.mcp")

# Configuration
MCP_VERSION = "1.0.0"
RATE_LIMIT_MAX_CALLS = 30
RATE_LIMIT_WINDOW = 60.0
MAX_ISSUES_IN_RESPONSE = 25


class _RateLimiter:
    def __init__(self, max_calls: int = RATE_LIMIT_MAX_CALLS, window: float = RATE_LIMIT_WINDOW):
        self._max_calls = max_calls
        self._window = window
        self._calls: List[float] = []

    def allow(self) -> bool:
        now = time.monotonic()
        cutoff = now - self._window
        self._calls = [t for t in self._calls if t > cutoff]
        if len(self._calls) >= self._max_calls:
            return False
        self._calls.append(now)
        return True

    @property
    def remaining(self) -> int:
        now = time.monotonic()
        cutoff = now - self._window
        active = [t for t in self._calls if t > cutoff]
        return max(0, self._max_calls - len(active))


class SovereignMcpServer(Worker):
    name = "sovereign_mcp_server"
    version = MCP_VERSION

    def __init__(self) -> None:
        super().__init__("sovereign_mcp_server")
        self._engine = None
        self._initialized = False
        self._rate_limiter = _RateLimiter()
        self._start_time = None
        self._event_bus = None

        self.tools = {
            "review_code": self._tool_review_code,
            "fix_code": self._tool_fix_code,
            "check_integrity": self._tool_check_integrity,
            "generate_code": self._tool_generate_code,
            "analyze_patterns": self._tool_analyze_patterns,
            "get_health": self._tool_get_health,
            "list_tools": self._tool_list_tools,
        }

    async def initialize(self) -> None:
        if self._initialized:
            return
        if CODE_WORKER_AVAILABLE and code_worker:
            self._engine = code_worker.ReviewEngine()
        self._initialized = True
        self._start_time = datetime.datetime.now()
        logger.info(f"MCP Server initialized — {len(self.tools)} tools")

    def set_event_bus(self, event_bus):
        self._event_bus = event_bus

    async def execute(self, task: str, **kwargs: Any) -> Dict[str, Any]:
        if not self._initialized:
            await self.initialize()

        self.execution_count += 1

        if not self._rate_limiter.allow():
            self.error_count += 1
            return self._error("Rate limit exceeded", 429)

        parts = task.strip().split()
        if not parts:
            return self._error("No command provided", 400)

        tool = parts[0].lower()
        args = parts[1:] if len(parts) > 1 else []

        parsed = self._parse_args(args)
        parsed.update(kwargs)

        handler = self.tools.get(tool)
        if not handler:
            return self._error(f"Unknown tool: {tool}", 404, available_tools=list(self.tools.keys()))

        try:
            result = await handler(**parsed)
            await self._emit_event(tool, result)
            return result
        except Exception as e:
            self.error_count += 1
            logger.error(f"Tool {tool} failed: {e}")
            return self._error(str(e), 500, tool=tool)

    def _parse_args(self, args: List[str]) -> Dict[str, Any]:
        kwargs = {}
        i = 0
        while i < len(args):
            if args[i].startswith("--"):
                key = args[i][2:]
                if i + 1 < len(args) and not args[i + 1].startswith("--"):
                    val = args[i + 1]
                    try:
                        if "." in val:
                            val = float(val)
                        else:
                            val = int(val)
                    except:
                        pass
                    kwargs[key] = val
                    i += 2
                else:
                    kwargs[key] = True
                    i += 1
            else:
                if "file_path" not in kwargs:
                    kwargs["file_path"] = args[i]
                elif "intent" not in kwargs:
                    kwargs["intent"] = " ".join(args[i:])
                    break
                i += 1
        return kwargs

    async def _run_review(self, target: Path):
        if not self._engine:
            raise RuntimeError("ReviewEngine not available")
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, self._engine.review_file, target)

    async def _emit_event(self, tool: str, result: Dict[str, Any]):
        if not self._event_bus:
            return
        try:
            event = {
                "source": "mcp_server",
                "tool": tool,
                "success": result.get("success", False),
                "timestamp": datetime.datetime.now().isoformat(),
            }
            if hasattr(self._event_bus, "publish"):
                await self._event_bus.publish("mcp.tool.executed", event)
        except Exception:
            pass

    def _success(self, tool: str, data: Dict[str, Any] = None) -> Dict[str, Any]:
        return {
            "success": True,
            "tool": tool,
            "worker": self.name,
            "timestamp": datetime.datetime.now().isoformat(),
            **(data or {}),
        }

    def _error(self, error: str, code: int = 400, **extra) -> Dict[str, Any]:
        return {
            "success": False,
            "worker": self.name,
            "error": error,
            "error_code": code,
            "timestamp": datetime.datetime.now().isoformat(),
            **extra,
        }

    # ── Tools ─────────────────────────────────────────────

    async def _tool_review_code(self, file_path: str = "", **kwargs) -> Dict[str, Any]:
        if not file_path:
            return self._error("file_path required", 400)
        target = Path(file_path)
        if not target.exists():
            return self._error(f"File not found: {file_path}", 404)
        if not self._engine:
            return self._error("RezCoder not available", 503)

        result = await self._run_review(target)
        return self._success("review_code", {
            "file": str(target),
            "health_score": result.health_score,
            "total_issues": len(result.issues),
            "error_count": result.error_count,
            "warning_count": result.warning_count,
            "issues": [i.to_dict() for i in result.issues[:MAX_ISSUES_IN_RESPONSE]],
            "strengths": result.strengths,
        })

    async def _tool_fix_code(self, file_path: str = "", confidence: float = 0.7, backup: bool = True, dry_run: bool = False, **kwargs) -> Dict[str, Any]:
        if not file_path:
            return self._error("file_path required", 400)
        target = Path(file_path)
        if not target.exists():
            return self._error(f"File not found: {file_path}", 404)
        if not self._engine:
            return self._error("RezCoder not available", 503)

        old_conf = self._engine.fix_confidence
        old_dry = self._engine.dry_run
        self._engine.fix_confidence = max(0.0, min(1.0, confidence))
        self._engine.dry_run = dry_run

        try:
            result = await self._run_review(target)
            return self._success("fix_code", {
                "file": str(target),
                "health_score": result.health_score,
                "fixes_applied": result.fixes_applied,
                "fixes_skipped": result.fixes_skipped,
                "dry_run": dry_run,
            })
        finally:
            self._engine.fix_confidence = old_conf
            self._engine.dry_run = old_dry

    async def _tool_check_integrity(self, file_path: str = "", **kwargs) -> Dict[str, Any]:
        if not file_path:
            return self._error("file_path required", 400)
        target = Path(file_path)
        if not target.exists():
            return self._error(f"File not found: {file_path}", 404)

        issues = []
        try:
            content = target.read_text(encoding="utf-8", errors="replace")
            if "\x00" in content:
                issues.append({"severity": "critical", "message": "Null bytes found"})
            if "\r\n" in content and "\n" in content.replace("\r\n", ""):
                issues.append({"severity": "warning", "message": "Mixed line endings"})
        except Exception as e:
            issues.append({"severity": "error", "message": f"Cannot read: {e}"})

        return self._success("check_integrity", {
            "file": str(target),
            "corruption_detected": any(i["severity"] in ("critical", "error") for i in issues),
            "issues": issues,
            "size_bytes": target.stat().st_size,
        })

    async def _tool_generate_code(self, intent: str = "", language: str = "python", **kwargs) -> Dict[str, Any]:
        if not intent:
            return self._error("intent required", 400)

        if language == "python":
            code = f'"""Generated for: {intent}"""\n\ndef generated():\n    # TODO: implement\n    pass\n'
        else:
            code = f"// Generated for: {intent}\nfunction generated() {{\n    // TODO: implement\n}}\n"

        return self._success("generate_code", {
            "intent": intent[:100],
            "code": code,
            "language": language,
            "drift_lock": hashlib.sha256(intent.encode()).hexdigest()[:16],
        })

    async def _tool_analyze_patterns(self, file_path: str = "", pattern: str = "", **kwargs) -> Dict[str, Any]:
        if not file_path:
            return self._error("file_path required", 400)
        target = Path(file_path)
        if not target.exists():
            return self._error(f"File not found: {file_path}", 404)
        if not self._engine:
            return self._error("RezCoder not available", 503)

        result = await self._run_review(target)
        matched = [s for s in result.strengths if pattern.lower() in s.lower()] if pattern else result.strengths

        return self._success("analyze_patterns", {
            "file": str(target),
            "matches_found": len(matched),
            "patterns": matched[:20],
        })

    async def _tool_get_health(self, **kwargs) -> Dict[str, Any]:
        uptime = None
        if self._start_time:
            uptime = str(datetime.datetime.now() - self._start_time)

        return self._success("get_health", {
            "status": "healthy",
            "initialized": self._initialized,
            "uptime": uptime,
            "stats": {
                "executions": self.execution_count,
                "errors": self.error_count,
                "rate_limit_remaining": self._rate_limiter.remaining,
            },
            "tools": list(self.tools.keys()),
        })

    async def _tool_list_tools(self, **kwargs) -> Dict[str, Any]:
        descriptions = {
            "review_code": "Analyze a file for code quality issues",
            "fix_code": "Apply auto-fixes to a file",
            "check_integrity": "Check file for corruption",
            "generate_code": "Generate code stub from intent",
            "analyze_patterns": "Find positive code patterns",
            "get_health": "Server health and statistics",
            "list_tools": "List all available tools",
        }
        return self._success("list_tools", {
            "tools": descriptions,
            "tool_count": len(descriptions),
        })

    async def health_check(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "status": "healthy" if self._initialized else "not_initialized",
            "version": self.version,
            "code_worker_available": CODE_WORKER_AVAILABLE,
            "executions": self.execution_count,
            "errors": self.error_count,
            "tools": len(self.tools),
        }
