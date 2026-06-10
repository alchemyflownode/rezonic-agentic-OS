# workers/code_context_worker.py
"""
Context Extractor – finds the exact code block (function, class, or keyword cluster) matching a query.
Returns line ranges and snippets for precise editing.
"""

import re
import logging
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional

from .base_worker import Worker

logger = logging.getLogger("PHOENIX")


class CodeContextWorker(Worker):
    def __init__(self):
        super().__init__("code_context")
        self.description = "Extract code block (function, class, or keyword cluster) matching a query"
        self.input_schema = {
            "file": "string",
            "query": "string",
            "context_lines": "integer",   # lines of context around block (default 10)
        }

    async def execute(self, task: str = "", **kwargs) -> Dict[str, Any]:
        file_path = Path(kwargs["file"]).resolve()
        query = kwargs.get("query", "").strip()
        context = kwargs.get("context_lines", 10)

        if not file_path.exists():
            return {"success": False, "error": f"File not found: {file_path}"}
        if not query:
            return {"success": False, "error": "Empty query"}

        content = file_path.read_text(encoding="utf-8")
        lines = content.splitlines()

        # Find all candidate blocks (functions/classes) and score them
        candidates = self._find_candidates(lines, query)

        if not candidates:
            return {"success": False, "error": "No relevant code block found"}

        # Add context lines around each candidate
        for cand in candidates:
            start = max(0, cand["start_line"] - context)
            end = min(len(lines), cand["end_line"] + context)
            cand["snippet"] = "\n".join(lines[start:end])
            cand["line_range"] = [start + 1, end]   # 1‑based for user

        return {
            "success": True,
            "file": str(file_path),
            "query": query,
            "candidates": candidates,
            "total_lines": len(lines)
        }

    def _find_candidates(self, lines: List[str], query: str) -> List[Dict]:
        # First, identify all blocks (functions, classes, or indented groups)
        blocks = self._extract_blocks(lines)

        # Score each block against the query
        keywords = set(re.findall(r"\b\w+\b", query.lower()))
        scored = []
        for block in blocks:
            code = "\n".join(lines[block["start"]:block["end"]])
            code_lower = code.lower()
            score = sum(1 for kw in keywords if kw in code_lower)
            # Bonus for exact name match
            if block["name"] and block["name"].lower() in query.lower():
                score += 5
            if score > 0:
                scored.append({
                    "type": block["type"],
                    "name": block["name"],
                    "start_line": block["start"] + 1,  # 1‑based
                    "end_line": block["end"],
                    "score": score,
                    "code": code[:500] + ("..." if len(code) > 500 else "")
                })

        scored.sort(key=lambda x: x["score"], reverse=True)
        return scored[:5]   # top 5 candidates

    def _extract_blocks(self, lines: List[str]) -> List[Dict]:
        blocks = []
        i = 0
        n = len(lines)
        while i < n:
            line = lines[i].strip()
            # Detect function or class definition
            match = re.match(r"^(def |class |function |async function )", line)
            if match:
                name_match = re.search(r"\b([a-zA-Z_][a-zA-Z0-9_]*)\s*\(", line)
                name = name_match.group(1) if name_match else "anonymous"
                start = i
                base_indent = len(lines[i]) - len(lines[i].lstrip())
                j = i + 1
                while j < n:
                    if lines[j].strip():
                        curr_indent = len(lines[j]) - len(lines[j].lstrip())
                        if curr_indent <= base_indent:
                            break
                    j += 1
                blocks.append({
                    "type": "function" if "def " in line or "function" in line else "class",
                    "name": name,
                    "start": start,
                    "end": j
                })
                i = j
            else:
                i += 1
        return blocks