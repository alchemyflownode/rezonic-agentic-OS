"""
The brain. Plugs into your existing kernel.
Uses YOUR workers, YOUR ollama client, YOUR event bus.
"""
import json
import re
import logging
from typing import Any, Dict, List, Optional, AsyncGenerator

logger = logging.getLogger("PHOENIX.AGENT")


def parse_action(text: str):
    """
    Parse LLM response into thinking + action.
    Returns (thinking, plan, tool_name, params) or (thinking, plan, None, None)
    """
    lines = text.split("\n")
    thinking = ""
    plan = ""
    action = None
    params = {}

    i = 0
    while i < len(lines):
        line = lines[i].strip()

        if line.upper().startswith("THINK:"):
            thinking = line[6:].strip()
        elif line.upper().startswith("PLAN:"):
            plan = line[5:].strip()
        elif line.upper().startswith("ACTION:"):
            action = line[7:].strip().lower()
        elif action == "read_file" and line.upper().startswith("PATH:"):
            params["path"] = line[5:].strip()
        elif action == "write_file" and line.upper().startswith("PATH:"):
            params["path"] = line[5:].strip()
        elif action == "write_file" and line.upper().startswith("CONTENT:"):
            params["content"] = "\n".join(lines[i+1:])
            break
        elif action == "run_code" and line.upper().startswith("CODE:"):
            params["code"] = "\n".join(lines[i+1:])
            params["language"] = "python"
            break
        elif action == "search" and line.upper().startswith("PATTERN:"):
            params["pattern"] = line[8:].strip()
        elif action == "list_files" and line.upper().startswith("DIRECTORY:"):
            params["directory"] = line[10:].strip()
        elif action and line.upper().startswith("TASK:"):
            params["task"] = line[5:].strip()
        i += 1

    return thinking, plan, action, params


class AgentLoop:
    """
    The THINK → PLAN → ACT → OBSERVE loop.
    Works with YOUR kernel's ollama client, YOUR workers, YOUR event bus.
    """

    def __init__(self, kernel):
        self.kernel = kernel
        self.tools = {}
        self._built_in_tools = {}
        self._setup_tools()

    def _setup_tools(self):
        """Register built-in file tools + your existing workers."""
        import os
        import asyncio
        import tempfile
        from pathlib import Path

        workspace = self.kernel.cfg.VSCODE_WORKSPACE

        def _safe_path(path: str) -> Path:
            full = (Path(workspace) / path).resolve()
            if not str(full).startswith(str(Path(workspace).resolve())):
                raise ValueError("Blocked: path escapes workspace")
            return full

        async def read_file(path: str, **kw) -> dict:
            try:
                full = _safe_path(path)
                if not full.exists():
                    return {"ok": False, "error": f"File not found: {path}"}
                text = full.read_text(encoding='utf-8', errors='replace')
                lines = text.splitlines()
                numbered = [f"{i+1:5d}| {line}" for i, line in enumerate(lines)]
                content = "\n".join(numbered)
                if len(content) > 6000:
                    content = content[:3000] + "\n... [truncated] ...\n" + content[-3000:]
                return {"ok": True, "path": path, "total_lines": len(lines), "content": content}
            except Exception as e:
                return {"ok": False, "error": str(e)}

        async def write_file(path: str, content: str = "", **kw) -> dict:
            try:
                full = _safe_path(path)
                full.parent.mkdir(parents=True, exist_ok=True)
                if full.exists():
                    bak = full.with_suffix(full.suffix + ".bak")
                    bak.write_text(full.read_text(encoding='utf-8', errors='replace'), encoding='utf-8')
                full.write_text(content, encoding='utf-8')
                return {"ok": True, "path": path, "lines_written": content.count('\n') + 1}
            except Exception as e:
                return {"ok": False, "error": str(e)}

        async def search_files(pattern: str, file_type: str = "*.py", **kw) -> dict:
            try:
                import re as _re
                regex = _re.compile(pattern, _re.IGNORECASE)
                results = []
                ws = Path(workspace).resolve()
                skip = {".git", "__pycache__", "node_modules", ".venv", "venv", "data", "logs"}
                for f in ws.rglob(file_type):
                    if any(s in f.parts for s in skip): continue
                    try:
                        txt = f.read_text(encoding='utf-8', errors='replace')
                        for i, ln in enumerate(txt.splitlines(), 1):
                            if regex.search(ln):
                                results.append({"file": str(f.relative_to(ws)), "line": i, "text": ln.strip()[:120]})
                                if len(results) >= 25: break
                    except: continue
                    if len(results) >= 25: break
                return {"ok": True, "pattern": pattern, "matches": len(results), "results": results}
            except Exception as e:
                return {"ok": False, "error": str(e)}

        async def list_dir(directory: str = ".", **kw) -> dict:
            try:
                full = _safe_path(directory)
                if not full.is_dir():
                    return {"ok": False, "error": f"Not a directory: {directory}"}
                entries = []
                for item in sorted(full.iterdir()):
                    if item.name.startswith("."): continue
                    if item.is_file():
                        entries.append({"name": item.name, "type": "file", "size": f"{item.stat().st_size}b"})
                    else:
                        entries.append({"name": item.name + "/", "type": "dir", "size": "-"})
                return {"ok": True, "path": directory, "count": len(entries), "files": entries}
            except Exception as e:
                return {"ok": False, "error": str(e)}

        async def run_code(code: str, language: str = "python", **kw) -> dict:
            if language != "python":
                return {"ok": False, "error": "Only Python supported"}
            blocked = ["os.system", "subprocess.Popen", "shutil.rmtree", "eval(", "__import__"]
            for b in blocked:
                if b in code:
                    return {"ok": False, "error": f"Blocked: {b}"}
            tmp = tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False)
            tmp.write(code)
            tmp.close()
            try:
                proc = await asyncio.create_subprocess_exec(
                    sys.executable, tmp.name,
                    stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE,
                    cwd=str(Path(workspace))
                )
                out, err = await asyncio.wait_for(proc.communicate(), timeout=30)
                return {"ok": proc.returncode == 0, "stdout": out.decode('utf-8', errors='replace')[-3000:], "stderr": err.decode('utf-8', errors='replace')[-1500:], "returncode": proc.returncode}
            except asyncio.TimeoutError:
                return {"ok": False, "error": "Timed out (30s)"}
            finally:
                try: os.unlink(tmp.name)
                except: pass

        # Register built-in tools
        self.tools["read_file"] = {"fn": read_file, "desc": "Read a file with line numbers. ALWAYS read before editing."}
        self.tools["write_file"] = {"fn": write_file, "desc": "Write content to a file. Creates dirs. Read first."}
        self.tools["search"] = {"fn": search_files, "desc": "Search for text pattern across files."}
        self.tools["list_files"] = {"fn": list_dir, "desc": "List files in a directory."}
        self.tools["run_code"] = {"fn": run_code, "desc": "Execute Python code in sandbox."}

        # Wrap YOUR existing workers as tools
        worker_configs = {
            "code_execution": "Execute Python code safely in a sandbox",
            "sandbox": "Run code in isolated sandbox environment",
            "system_monitor": "Get CPU, GPU, RAM stats",
            "paper_trader": "Execute paper trading actions (buy/sell/portfolio)",
            "backtest": "Run a strategy backtest",
        }

        for worker_name, desc in worker_configs.items():
            info = self.kernel.workers.get(worker_name)
            if info and info.get("instance"):
                instance = info["instance"]
                async def worker_tool(task: str, _instance=instance, **kw):
                    try:
                        return await _instance.execute(task, **kw)
                    except Exception as e:
                        return {"ok": False, "error": str(e)}
                self.tools[worker_name] = {"fn": worker_tool, "desc": desc}

        logger.info(f"🧠 Agent tools: {list(self.tools.keys())}")

    def _build_system_prompt(self) -> str:
        tool_list = "\n".join(f"- {name}: {t['desc']}" for name, t in self.tools.items())
        return f"""You are ReZonic, an AI agent that thinks and acts.

WORKSPACE: {self.kernel.cfg.VSCODE_WORKSPACE}

## YOUR TOOLS
{tool_list}

## HOW TO ACT

Every response MUST follow this structure:

THINK: <your reasoning>
PLAN: <one sentence about what you'll do>
ACTION: <tool_name>
<parameter on next line like PATH: filename.py or TASK: do something>

## PARAMETER FORMATS
- read_file → PATH: <file>
- write_file → PATH: <file> then CONTENT: on next line, then all content after
- search → PATTERN: <text>
- list_files → DIRECTORY: <path>
- run_code → CODE: on next line, then all code after
- Workers → TASK: <command string>

## RULES
1. ALWAYS start with THINK and PLAN
2. Read before editing
3. One action per response
4. If tool fails, THINK about why and retry
5. When done, respond without ACTION line
6. Be concise - just do it"""

    async def run(self, task: str) -> AsyncGenerator[dict, None]:
        """The agent loop. Streams steps as dicts."""
        messages = [
            {"role": "system", "content": self._build_system_prompt()},
            {"role": "user", "content": task}
        ]

        for step in range(15):
            yield {"type": "thinking"}

            # Call YOUR kernel's ollama client
            try:
                result = await self.kernel.ollama.chat(messages, stream=False)
                text = result if isinstance(result, str) else str(result)
            except Exception as e:
                yield {"type": "error", "text": f"LLM error: {e}"}
                return

            if not text.strip():
                yield {"type": "error", "text": "Empty response"}
                return

            thinking, plan, action, params = parse_action(text)

            if thinking:
                yield {"type": "think", "text": thinking}
            if plan:
                yield {"type": "plan", "text": plan}

            if not action or action not in self.tools:
                clean = re.sub(r'^(THINK|PLAN):.*\n', '', text, flags=re.MULTILINE).strip()
                yield {"type": "answer", "text": clean}
                return

            yield {"type": "act", "tool": action, "params": params}

            # Execute tool
            try:
                tool_result = await self.tools[action]["fn"](**params)
            except TypeError as e:
                tool_result = {"ok": False, "error": f"Bad params: {e}"}
            except Exception as e:
                tool_result = {"ok": False, "error": str(e)}

            # Format observation
            ok = tool_result.get("ok", tool_result.get("success", False))
            if ok:
                if action == "read_file":
                    summary = f"File: {tool_result.get('total_lines', '?')} lines"
                elif action == "write_file":
                    summary = f"Wrote {tool_result.get('lines_written', '?')} lines to {tool_result.get('path', '?')}"
                elif action == "run_code":
                    out = (tool_result.get("stdout") or "").strip()[:200]
                    summary = f"Exit {tool_result.get('returncode')}: {out}" if out else f"Exit {tool_result.get('returncode')}"
                elif action == "search":
                    summary = f"Found {tool_result.get('matches', 0)} matches"
                elif action == "list_files":
                    summary = f"{tool_result.get('count', 0)} items"
                else:
                    summary = "Done"
                yield {"type": "observe", "ok": True, "summary": summary, "result": tool_result}
            else:
                err = tool_result.get("error", "Unknown error")
                yield {"type": "observe", "ok": False, "summary": f"Error: {err}", "result": tool_result}

            # Feed back to LLM
            if ok:
                if action == "read_file":
                    feedback = f"File contents ({tool_result.get('total_lines')} lines):\n{tool_result.get('content', '')}"
                elif action == "write_file":
                    feedback = f"Success: wrote to {tool_result.get('path')}"
                elif action == "run_code":
                    parts = []
                    if tool_result.get("stdout"): parts.append(f"STDOUT:\n{tool_result['stdout']}")
                    if tool_result.get("stderr"): parts.append(f"STDERR:\n{tool_result['stderr']}")
                    feedback = "\n".join(parts) or "No output"
                elif action == "search":
                    matches = tool_result.get("results", [])
                    if matches:
                        feedback = "\n".join(f"  {m['file']}:{m['line']} — {m['text']}" for m in matches[:15])
                    else:
                        feedback = "No matches found"
                elif action == "list_files":
                    feedback = "\n".join(f"  {f['name']} ({f['size']})" for f in tool_result.get("files", [])[:30])
                else:
                    feedback = json.dumps(tool_result, indent=2, default=str)[:3000]
            else:
                feedback = f"ERROR: {tool_result.get('error', 'Unknown')}"

            messages.append({"role": "assistant", "content": text})
            messages.append({"role": "user", "content": f"TOOL RESULT:\n{feedback}\n\nWhat next? If done, give final answer."})

        yield {"type": "error", "text": "Max steps reached (15)"}