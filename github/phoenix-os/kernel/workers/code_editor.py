# workers/code_editor.py
"""
Code Editor Worker – precise, safe file mutation with diff preview, backup, and atomic write.
Supports search/replace, regex, and line‑range operations.
"""

import re
import shutil
import difflib
import logging
from pathlib import Path
from typing import Dict, Any, Optional

from .base_worker import Worker

logger = logging.getLogger("PHOENIX")


class CodeEditor(Worker):
    MAX_FILE_SIZE_BYTES = 1_000_000   # 1 MiB
    MAX_REGEX_MATCHES = 50

    def __init__(self):
        super().__init__("code_editor")
        self.description = "Apply precise edits to code files – search/replace, line ranges, or regex."
        self.input_schema = {
            "file": "string",                     # path to file
            "operation": "string",                # "replace", "search_replace", "line_range"
            "search": "string",                   # for search_replace operation
            "replace": "string",                  # replacement text
            "start_line": "integer",              # for line_range operation (1‑based)
            "end_line": "integer",                # for line_range operation (inclusive)
            "use_regex": "boolean",               # treat search as regex
            "backup": "boolean",                  # create .bak file before edit
        }

    async def execute(self, task: str = "", **kwargs) -> Dict[str, Any]:
        file_path = Path(kwargs["file"]).resolve()
        operation = kwargs.get("operation", "search_replace")
        backup = kwargs.get("backup", True)
        dry_run = kwargs.get("dry_run", False)   # passed from kernel

        # 1. Security – constitution already ran, but double‑check path
        if not file_path.exists():
            return {"success": False, "error": f"File not found: {file_path}"}
        if file_path.stat().st_size > self.MAX_FILE_SIZE_BYTES:
            return {"success": False, "error": f"File too large (> {self.MAX_FILE_SIZE_BYTES} bytes)"}

        # 2. Read original content
        original = file_path.read_text(encoding="utf-8")

        # 3. Apply edit (depending on operation)
        if operation == "search_replace":
            search = kwargs.get("search", "")
            replace = kwargs.get("replace", "")
            use_regex = kwargs.get("use_regex", False)

            if not search or not search.strip():
                return {"success": False, "error": "Search string cannot be empty"}

            if use_regex:
                try:
                    matches = list(re.finditer(search, original, flags=re.MULTILINE))
                    if len(matches) > self.MAX_REGEX_MATCHES:
                        return {"success": False, "error": f"Too many matches ({len(matches)}). Refine pattern."}
                    new_content = re.sub(search, replace, original, flags=re.MULTILINE)
                except re.error as e:
                    return {"success": False, "error": f"Invalid regex: {e}"}
            else:
                if search not in original:
                    return {"success": False, "error": "Search string not found – aborting"}
                new_content = original.replace(search, replace)

        elif operation == "line_range":
            start_line = kwargs.get("start_line", 1)
            end_line = kwargs.get("end_line", None)
            replace_text = kwargs.get("replace", "")

            lines = original.splitlines(keepends=True)
            if end_line is None:
                end_line = start_line
            if start_line < 1 or end_line > len(lines):
                return {"success": False, "error": f"Line range {start_line}–{end_line} out of bounds (1–{len(lines)})"}

            # Normalise replace_text (preserve newline)
            if not replace_text.endswith("\n"):
                replace_text += "\n"

            # Optional: preserve indentation of first replaced line
            first_line = lines[start_line-1]
            indent = re.match(r"^\s*", first_line).group()
            replace_text = indent + replace_text.lstrip()

            new_lines = lines[:start_line-1] + [replace_text] + lines[end_line:]
            new_content = "".join(new_lines)

        else:
            return {"success": False, "error": f"Unknown operation: {operation}"}

        # 4. If no change, early exit
        if new_content == original:
            return {"success": True, "message": "No changes needed", "diff": ""}

        # 5. Compute diff (for preview and audit)
        diff = self._compute_diff(original, new_content, file_path.name)

        # 6. Dry run: return diff without writing
        if dry_run:
            return {
                "success": True,
                "dry_run": True,
                "diff": diff,
                "message": "Preview of changes – run without --plan to apply."
            }

        # 7. Write to disk with backup + atomic write
        if backup:
            backup_path = file_path.with_suffix(file_path.suffix + ".bak")
            backup_path.write_text(original, encoding="utf-8")
            logger.info(f"Created backup: {backup_path}")

        temp_path = file_path.with_suffix(".tmp")
        temp_path.write_text(new_content, encoding="utf-8")
        shutil.move(str(temp_path), str(file_path))   # atomic on most OSes

        # 8. Log for audit trail
        logger.info(f"[{self.name}] Edited: {file_path}")

        # 9. Confidence score (for orchestrator)
        confidence = 1.0
        if operation == "search_replace" and not kwargs.get("use_regex", False):
            if kwargs.get("search", "") not in original:
                confidence -= 0.5
        if kwargs.get("use_regex", False):
            confidence -= 0.2
        diff_lines = diff.count("\n")
        if diff_lines > 50:
            confidence -= 0.2
        confidence = max(0.0, confidence)

        return {
            "success": True,
            "message": f"File edited: {file_path}",
            "diff": diff,
            "backup_created": backup,
            "confidence": confidence
        }

    def _compute_diff(self, original: str, new: str, filename: str) -> str:
        from_lines = original.splitlines(keepends=True)
        to_lines = new.splitlines(keepends=True)
        diff = difflib.unified_diff(
            from_lines, to_lines,
            fromfile=f"a/{filename}",
            tofile=f"b/{filename}"
        )
        return "".join(diff)