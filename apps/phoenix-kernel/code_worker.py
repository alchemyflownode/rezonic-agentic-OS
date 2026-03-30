#!/usr/bin/env python3
"""
code-worker.py — Automated Code Review, Fix & Augmentation Engine
=================================================================

Production-grade multi-pass code analysis with modular analyzers,
safe auto-fix pipeline, confidence scoring, and unified diff output.

Architecture:
    ReviewEngine
    ├── BaseAnalyzer (pluggable analysis passes)
    │   ├── ImportAnalyzer        — import ordering and placement
    │   ├── DocstringAnalyzer     — missing docstrings
    │   ├── TypeHintAnalyzer      — missing type annotations
    │   ├── SecurityAnalyzer      — secrets, eval, pickle, injection
    │   ├── MemoryAnalyzer        — unbounded collections, missing cleanup
    │   ├── AsyncAnalyzer         — blocking calls in async context
    │   ├── StyleAnalyzer         — line length, trailing whitespace
    │   ├── ErrorHandlingAnalyzer — bare except, swallowed errors
    │   └── DuplicateLineAnalyzer — copy-paste detection
    ├── BaseFixer (safe auto-remediation)
    │   ├── TrailingWhitespaceFixer
    │   ├── BareExceptFixer
    │   ├── SecuritySecretFixer
    │   └── DocstringInsertFixer
    ├── StrengthDetector (positive pattern recognition)
    └── ReportGenerator (Markdown + diff + console output)

Usage (standalone):
    python code-worker.py <target_file>
    python code-worker.py <target_file> --dry-run --verbose
    python code-worker.py <target_file> --backup --fix-confidence 0.8
    python code-worker.py <directory> --recursive
    python code-worker.py <target_file> --report-only --json

Usage (as library):
    from code_worker import ReviewEngine, inspect_file
    engine = ReviewEngine(fix_confidence=0.8)
    result = engine.review_file(Path("my_module.py"))
"""

from __future__ import annotations

import argparse
import ast
import datetime
import difflib
import hashlib
import json
import os
import platform
import re
import shutil
import subprocess
import sys
import textwrap
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Optional


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  CONFIGURATION
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

SECTION_SIZE = 100
MAX_LINE_LENGTH = 120
BACKUP_SUFFIX = ".bak"
REPORT_SUFFIX = "_review.md"
DEFAULT_FIX_CONFIDENCE = 0.7
SUPPORTED_EXTENSIONS = {
    ".py", ".js", ".ts", ".tsx", ".jsx",
    ".rs", ".go", ".java", ".rb", ".cpp", ".c",
}

SECRET_PATTERNS = [
    re.compile(r"""(['"])(sk-[a-zA-Z0-9]{20,})\1"""),
    re.compile(r"""(['"])(ghp_[a-zA-Z0-9]{36,})\1"""),
    re.compile(r"""(['"])(AKIA[A-Z0-9]{16})\1"""),
    re.compile(r"""api[_-]?key\s*=\s*(['"])([^'"]{10,})\1""", re.I),
    re.compile(r"""password\s*=\s*(['"])([^'"]{4,})\1""", re.I),
    re.compile(r"""secret\s*=\s*(['"])([^'"]{8,})\1""", re.I),
    re.compile(r"""token\s*=\s*(['"])([^'"]{10,})\1""", re.I),
    re.compile(r"""(['"])(eyJ[a-zA-Z0-9_-]{20,}\.eyJ[a-zA-Z0-9_-]{20,})\1"""),
]

UNSAFE_CALL_PATTERNS = [
    (re.compile(r"""\beval\s*\("""), "eval()",
     "Use ast.literal_eval() or a safe parser"),
    (re.compile(r"""\bexec\s*\("""), "exec()",
     "Avoid exec(); use structured dispatch"),
    (re.compile(r"""\bpickle\.loads?\s*\("""), "pickle.load()",
     "Use json or msgpack for serialization"),
    (re.compile(r"""\byaml\.load\s*\("""), "yaml.load()",
     "Use yaml.safe_load() instead"),
    (re.compile(r"""\b__import__\s*\("""), "__import__()",
     "Use importlib.import_module()"),
    (re.compile(r"""\bos\.system\s*\("""), "os.system()",
     "Use subprocess.run() with shell=False"),
    (re.compile(r"""\bsubprocess\.call\s*\(.*shell\s*=\s*True"""),
     "subprocess with shell=True",
     "Avoid shell=True; pass args as list"),
]


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  DATA MODELS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


class Severity(Enum):
    """Issue severity — maps to exit codes and report sections."""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"

    @property
    def emoji(self) -> str:
        """TODO: Document emoji()."""
        return {
            Severity.INFO: "ℹ️",
            Severity.WARNING: "⚠️",
            Severity.ERROR: "❌",
            Severity.CRITICAL: "🔥",
        }[self]

    @property
    def weight(self) -> int:
        """TODO: Document weight()."""
        return {
            Severity.INFO: 1,
            Severity.WARNING: 2,
            Severity.ERROR: 5,
            Severity.CRITICAL: 10,
        }[self]


@dataclass
class Issue:
    """A single detected code issue with confidence scoring."""
    severity: Severity
    category: str
    line: Optional[int]
    message: str
    suggestion: str = ""
    auto_fixable: bool = False
    confidence: float = 1.0

    def __str__(self) -> str:
        """TODO: Document __str__()."""
        loc = f"L{self.line}" if self.line else "—"
        return (
            f"{self.severity.emoji} [{self.category}] "
            f"{loc}: {self.message}"
        )

    def to_dict(self) -> dict[str, Any]:
        """Serialize for JSON / API responses."""
        return {
            "severity": self.severity.value,
            "category": self.category,
            "line": self.line,
            "message": self.message,
            "suggestion": self.suggestion,
            "auto_fixable": self.auto_fixable,
            "confidence": self.confidence,
        }


@dataclass
class Fix:
    """A structured auto-fix with safety metadata."""
    description: str
    category: str
    confidence: float
    apply: Callable[[str], str]
    line: Optional[int] = None

    def __str__(self) -> str:
        return (
            f"🔧 [{self.category}] {self.description} "
            f"(conf={self.confidence:.0%})"
        )


@dataclass
class FileMetadata:
    """Metadata about the target file."""
    path: Path
    size_bytes: int = 0
    line_count: int = 0
    sha256: str = ""
    language: str = "python"
    encoding: str = "utf-8"

    def to_dict(self) -> dict[str, Any]:
        """Serialize for JSON / API responses."""
        return {
            "path": str(self.path),
            "size_bytes": self.size_bytes,
            "line_count": self.line_count,
            "sha256": self.sha256,
            "language": self.language,
            "encoding": self.encoding,
        }


@dataclass
class ReviewResult:
    """Full review output — serializable for API or file output."""
    metadata: FileMetadata
    issues: list[Issue] = field(default_factory=list)
    strengths: list[str] = field(default_factory=list)
    fixes_applied: list[str] = field(default_factory=list)
    fixes_skipped: list[str] = field(default_factory=list)
    original_source: str = ""
    fixed_source: str = ""
    timestamp: str = field(
        default_factory=lambda: datetime.datetime.now().isoformat()
    )

    @property
    def error_count(self) -> int:
        """TODO: Document error_count()."""
        return sum(
            1 for i in self.issues
            if i.severity in (Severity.ERROR, Severity.CRITICAL)
        )

    @property
    def warning_count(self) -> int:
        """TODO: Document warning_count()."""
        return sum(1 for i in self.issues if i.severity == Severity.WARNING)

    @property
    def health_score(self) -> float:
        """0–100 score. Deductions weighted by severity."""
        if not self.issues:
            return 100.0
        total_weight = sum(i.severity.weight for i in self.issues)
        score = max(0.0, 100.0 - total_weight * 2)
        return round(score, 1)

    def unified_diff(self) -> str:
        """Generate a unified diff between original and fixed source."""
        if self.original_source == self.fixed_source:
            return ""
        orig_lines = self.original_source.splitlines(keepends=True)
        fixed_lines = self.fixed_source.splitlines(keepends=True)
        diff = difflib.unified_diff(
            orig_lines,
            fixed_lines,
            fromfile=f"{self.metadata.path.name} (original)",
            tofile=f"{self.metadata.path.name} (fixed)",
            lineterm="",
        )
        return "\n".join(diff)

    def to_dict(self) -> dict[str, Any]:
        """Full serialization for JSON output."""
        return {
            "metadata": self.metadata.to_dict(),
            "health_score": self.health_score,
            "total_issues": len(self.issues),
            "error_count": self.error_count,
            "warning_count": self.warning_count,
            "issues": [i.to_dict() for i in self.issues],
            "strengths": self.strengths,
            "fixes_applied": self.fixes_applied,
            "fixes_skipped": self.fixes_skipped,
            "timestamp": self.timestamp,
            "success": True,
        }


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  STEP 1 — FILE INSPECTION
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


def inspect_file(filepath: Path) -> tuple[FileMetadata, str]:
    """
    Read file and collect metadata.
    On Windows, also runs PowerShell size verification.

    Returns:
        Tuple of (FileMetadata, source_content_string).

    Raises:
        SystemExit: If file does not exist or is not a file.
    """
    if not filepath.exists():
        print(f"❌ File not found: {filepath}")
        sys.exit(1)

    if not filepath.is_file():
        print(f"❌ Not a file: {filepath}")
        sys.exit(1)

    meta = FileMetadata(path=filepath.resolve())
    meta.size_bytes = filepath.stat().st_size
    content = filepath.read_text(encoding="utf-8", errors="replace")
    meta.line_count = content.count("\n") + (1 if content else 0)
    meta.sha256 = hashlib.sha256(content.encode()).hexdigest()
    meta.language = _detect_language(filepath)

    # PowerShell parity check on Windows
    if platform.system() == "Windows":
        try:
            escaped = str(filepath).replace("'", "''")
            ps_cmd = (
                f"powershell -NoProfile -Command "
                f"\"Get-Item -Path '{escaped}' "
                f"| Select-Object -ExpandProperty Length\""
            )
            result = subprocess.run(
                ps_cmd, shell=True, capture_output=True,
                text=True, timeout=10,
            )
            ps_size = result.stdout.strip()
            if ps_size and ps_size.isdigit():
                if int(ps_size) != meta.size_bytes:
                    print(
                        f"  ⚠️  Size mismatch: Python={meta.size_bytes}, "
                        f"PowerShell={ps_size}"
                    )
                else:
                    print(f"  📎 PowerShell confirms size: {ps_size} bytes")
        except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
            pass

    print(f"\n{'═' * 60}")
    print(f"  📄 File     : {meta.path}")
    print(f"  📏 Size     : {meta.size_bytes:,} bytes")
    print(f"  📝 Lines    : {meta.line_count:,}")
    print(f"  🔒 SHA-256  : {meta.sha256[:16]}…")
    print(f"  🗣  Language : {meta.language}")
    print(f"{'═' * 60}\n")
    return meta, content


def _detect_language(p: Path) -> str:
    """Map file extension to language identifier."""
    ext_map = {
        ".py": "python", ".js": "javascript", ".ts": "typescript",
        ".tsx": "typescript-react", ".jsx": "javascript-react",
        ".rs": "rust", ".go": "go", ".java": "java",
        ".rb": "ruby", ".cpp": "cpp", ".c": "c",
    }
    return ext_map.get(p.suffix.lower(), "unknown")


def discover_files(target: Path, recursive: bool = False) -> list[Path]:
    """Find all supported source files under a target path."""
    if target.is_file():
        return [target]

    if not target.is_dir():
        print(f"❌ Not a file or directory: {target}")
        sys.exit(1)

    pattern = "**/*" if recursive else "*"
    files = sorted(
        p for p in target.glob(pattern)
        if p.is_file() and p.suffix.lower() in SUPPORTED_EXTENSIONS
    )
    if not files:
        print(f"⚠️  No supported source files found in: {target}")
    return files


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  STEP 2 — MODULAR ANALYZERS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


class BaseAnalyzer(ABC):
    """
    Abstract base for all code analyzers.
    Each subclass focuses on a single concern.
    """
    name: str = "base"
    languages: set[str] = {"python"}

    @abstractmethod
    def analyze(
        self,
        source: str,
        lines: list[str],
        tree: Optional[ast.Module],
        meta: FileMetadata,
    ) -> list[Issue]:
        """Run analysis and return discovered issues."""
        ...


class ImportAnalyzer(BaseAnalyzer):
    """Checks import ordering, placement, and PEP-8 grouping."""
    name = "imports"
    languages = {"python"}

    def analyze(
        self, source: str, lines: list[str],
        tree: Optional[ast.Module], meta: FileMetadata,
    ) -> list[Issue]:
        """TODO: Document analyze()."""
        issues: list[Issue] = []
        if not tree:
            return issues

        import_nodes = [
            n for n in ast.walk(tree)
            if isinstance(n, (ast.Import, ast.ImportFrom))
        ]
        if not import_nodes:
            return issues

        stdlib_names: set[str] = set()
        if hasattr(sys, "stdlib_module_names"):
            stdlib_names = sys.stdlib_module_names
        else:
            # Fallback for Python < 3.10
            stdlib_names = {
                "os", "sys", "re", "json", "math", "datetime",
                "pathlib", "hashlib", "subprocess", "ast",
                "collections", "functools", "itertools", "typing",
                "abc", "enum", "dataclasses", "logging", "asyncio",
                "shutil", "textwrap", "difflib", "platform",
                "argparse", "copy", "io", "time", "threading",
            }

        stdlib_imports: list[ast.AST] = []
        third_party: list[ast.AST] = []
        local_imports: list[ast.AST] = []

        for node in import_nodes:
            if isinstance(node, ast.Import):
                names = [alias.name.split(".")[0] for alias in node.names]
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    names = [node.module.split(".")[0]]
                else:
                    names = []
                # Relative imports
                if node.level and node.level > 0:
                    local_imports.append(node)
                    continue
            else:
                names = []

            if any(n in stdlib_names for n in names):
                stdlib_imports.append(node)
            else:
                third_party.append(node)

        # Check for top-level imports scattered far from file top
        for node in import_nodes:
            if not hasattr(node, "lineno") or node.lineno <= 50:
                continue

            # Determine if this import is inside a function or class
            is_nested = self._is_nested_in_scope(tree, node)

            if not is_nested:
                mod_name = self._get_import_name(node)
                issues.append(Issue(
                    severity=Severity.WARNING,
                    category="Import Order",
                    line=node.lineno,
                    message=(
                        f"Import '{mod_name}' at line {node.lineno} is far "
                        f"from top-level imports"
                    ),
                    suggestion=(
                        "Move to top of file with other imports, "
                        "or wrap in a function for conditional import."
                    ),
                    auto_fixable=False,
                    confidence=0.7,
                ))

        # Check PEP-8 ordering: stdlib before third-party
        if stdlib_imports and third_party:
            last_stdlib = max(n.lineno for n in stdlib_imports)
            first_tp = min(n.lineno for n in third_party)
            if last_stdlib > first_tp:
                issues.append(Issue(
                    severity=Severity.WARNING,
                    category="Import Order",
                    line=first_tp,
                    message="Third-party imports appear before stdlib imports",
                    suggestion="Order: stdlib → third-party → local (PEP 8)",
                    auto_fixable=True,
                    confidence=0.8,
                ))

        return issues

    @staticmethod
    def _is_nested_in_scope(
        tree: ast.Module, target_node: ast.AST
    ) -> bool:
        """Check if target_node is inside a function or class body."""
        target_line = getattr(target_node, "lineno", 0)
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef,
                                 ast.ClassDef)):
                start = getattr(node, "lineno", 0)
                end = getattr(node, "end_lineno", 0) or 999999
                if start < target_line <= end:
                    return True
        return False

    @staticmethod
    def _get_import_name(node: ast.AST) -> str:
        """Extract the module name from an import node."""
        if isinstance(node, ast.Import) and node.names:
            return node.names[0].name
        elif isinstance(node, ast.ImportFrom) and node.module:
            return node.module
        return "<unknown>"


class DocstringAnalyzer(BaseAnalyzer):
    """Checks for missing docstrings on modules, classes, and functions."""
    name = "docstrings"
    languages = {"python"}

    def analyze(
        self, source: str, lines: list[str],
        tree: Optional[ast.Module], meta: FileMetadata,
    ) -> list[Issue]:
        """TODO: Document analyze()."""
        issues: list[Issue] = []
        if not tree:
            return issues

        # Module docstring
        if not ast.get_docstring(tree):
            issues.append(Issue(
                severity=Severity.INFO,
                category="Documentation",
                line=1,
                message="Module lacks a docstring",
                suggestion='Add a module-level """docstring""" explaining purpose.',
                auto_fixable=True,
                confidence=0.9,
            ))

        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                if not ast.get_docstring(node):
                    body_len = (
                        (node.end_lineno or node.lineno) - node.lineno
                    )
                    # Skip tiny private helpers
                    if node.name.startswith("_") and body_len < 5:
                        continue
                    issues.append(Issue(
                        severity=Severity.INFO,
                        category="Documentation",
                        line=node.lineno,
                        message=f"Function '{node.name}' lacks a docstring",
                        suggestion="Add docstring: purpose, args, returns.",
                        auto_fixable=True,
                        confidence=0.85,
                    ))

            elif isinstance(node, ast.ClassDef):
                if not ast.get_docstring(node):
                    issues.append(Issue(
                        severity=Severity.WARNING,
                        category="Documentation",
                        line=node.lineno,
                        message=f"Class '{node.name}' lacks a docstring",
                        suggestion="Add a class-level docstring.",
                        auto_fixable=True,
                        confidence=0.9,
                    ))

        return issues


class TypeHintAnalyzer(BaseAnalyzer):
    """Checks for missing type annotations on function signatures."""
    name = "type-hints"
    languages = {"python"}

    def analyze(
        self, source: str, lines: list[str],
        tree: Optional[ast.Module], meta: FileMetadata,
    ) -> list[Issue]:
        """TODO: Document analyze()."""
        issues: list[Issue] = []
        if not tree:
            return issues

        for node in ast.walk(tree):
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue

            # Skip dunder methods
            if node.name.startswith("__") and node.name.endswith("__"):
                continue

            if node.returns is None:
                issues.append(Issue(
                    severity=Severity.INFO,
                    category="Type Hints",
                    line=node.lineno,
                    message=(
                        f"Function '{node.name}' missing return type "
                        f"annotation"
                    ),
                    suggestion="Add -> ReturnType to the function signature.",
                    confidence=0.7,
                ))

            for arg in node.args.args:
                if arg.arg in ("self", "cls"):
                    continue
                if arg.annotation is None:
                    issues.append(Issue(
                        severity=Severity.INFO,
                        category="Type Hints",
                        line=node.lineno,
                        message=(
                            f"Parameter '{arg.arg}' in '{node.name}' "
                            f"missing type annotation"
                        ),
                        suggestion=f"Add type hint: {arg.arg}: <Type>",
                        confidence=0.6,
                    ))

        return issues


class SecurityAnalyzer(BaseAnalyzer):
    """Detects hardcoded secrets, eval/exec, pickle, shell injection."""
    name = "security"
    languages = {
        "python", "javascript", "typescript",
        "typescript-react", "javascript-react",
    }

    def analyze(
        self, source: str, lines: list[str],
        tree: Optional[ast.Module], meta: FileMetadata,
    ) -> list[Issue]:
        """TODO: Document analyze()."""
        issues: list[Issue] = []

        # Hardcoded secrets
        for i, line in enumerate(lines, 1):
            stripped = line.strip()
            if stripped.startswith("#") or stripped.startswith("//"):
                continue
            for pattern in SECRET_PATTERNS:
                if pattern.search(line):
                    issues.append(Issue(
                        severity=Severity.CRITICAL,
                        category="Security",
                        line=i,
                        message=(
                            "Possible hardcoded secret/credential detected"
                        ),
                        suggestion=(
                            "Use environment variables or a secrets manager."
                        ),
                        auto_fixable=True,
                        confidence=0.75,
                    ))
                    break

        # Unsafe function calls (Python only)
        if meta.language == "python":
            for i, line in enumerate(lines, 1):
                stripped = line.strip()
                if stripped.startswith("#"):
                    continue
                for pattern, name, fix_hint in UNSAFE_CALL_PATTERNS:
                    if pattern.search(line):
                        issues.append(Issue(
                            severity=Severity.ERROR,
                            category="Security",
                            line=i,
                            message=f"Unsafe call: {name}",
                            suggestion=fix_hint,
                            confidence=0.9,
                        ))

        return issues


class MemoryAnalyzer(BaseAnalyzer):
    """Detects memory leak patterns — unbounded dicts/lists, no cleanup."""
    name = "memory"
    languages = {"python"}

    def analyze(
        self, source: str, lines: list[str],
        tree: Optional[ast.Module], meta: FileMetadata,
    ) -> list[Issue]:
        """TODO: Document analyze()."""
        issues: list[Issue] = []
        if not tree:
            return issues

        for node in ast.walk(tree):
            if not isinstance(node, ast.ClassDef):
                continue

            init_method: Optional[ast.FunctionDef] = None
            has_cleanup = False

            for item in node.body:
                if (isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef))
                        and item.name == "__init__"):
                    init_method = item
                if (isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef))
                        and item.name in (
                            "cleanup", "clear", "reset",
                            "_cleanup", "__del__", "close",
                        )):
                    has_cleanup = True

            if not init_method:
                continue

            # Find self.xxx = {} or self.xxx = [] in __init__
            growing_attrs: list[str] = []
            for stmt in ast.walk(init_method):
                if not isinstance(stmt, ast.Assign):
                    continue
                for target in stmt.targets:
                    if (isinstance(target, ast.Attribute)
                            and isinstance(target.value, ast.Name)
                            and target.value.id == "self"
                            and isinstance(stmt.value, (ast.Dict, ast.List))):
                        growing_attrs.append(target.attr)

            if growing_attrs and not has_cleanup:
                issues.append(Issue(
                    severity=Severity.WARNING,
                    category="Memory",
                    line=node.lineno,
                    message=(
                        f"Class '{node.name}' has growing collections "
                        f"({', '.join(growing_attrs)}) but no cleanup method"
                    ),
                    suggestion=(
                        "Add a cleanup/reset method, or use bounded "
                        "collections (maxlen deque, LRU cache)."
                    ),
                    auto_fixable=True,
                    confidence=0.65,
                ))

        return issues


class AsyncAnalyzer(BaseAnalyzer):
    """Detects blocking calls inside async functions."""
    name = "async"
    languages = {"python"}

    BLOCKING_CALLS = {
        "time.sleep", "open", "sqlite3.connect",
        "requests.get", "requests.post", "requests.put",
        "requests.delete", "requests.patch",
        "input", "os.system",
    }

    def analyze(
        self, source: str, lines: list[str],
        tree: Optional[ast.Module], meta: FileMetadata,
    ) -> list[Issue]:
        """TODO: Document analyze()."""
        issues: list[Issue] = []
        if not tree:
            return issues

        for node in ast.walk(tree):
            if not isinstance(node, ast.AsyncFunctionDef):
                continue

            for child in ast.walk(node):
                if not isinstance(child, ast.Call):
                    continue
                call_name = self._get_call_name(child)
                if call_name in self.BLOCKING_CALLS:
                    issues.append(Issue(
                        severity=Severity.ERROR,
                        category="Async",
                        line=getattr(child, "lineno", node.lineno),
                        message=(
                            f"Blocking call '{call_name}' inside async "
                            f"function '{node.name}'"
                        ),
                        suggestion=(
                            "Use async equivalent: asyncio.sleep / "
                            "aiofiles / aiosqlite / httpx"
                        ),
                        confidence=0.85,
                    ))

        return issues

    @staticmethod
    def _get_call_name(node: ast.Call) -> str:
        """Extract dotted call name from AST Call node."""
        if isinstance(node.func, ast.Name):
            return node.func.id
        elif isinstance(node.func, ast.Attribute):
            parts: list[str] = []
            current: ast.expr = node.func
            while isinstance(current, ast.Attribute):
                parts.append(current.attr)
                current = current.value
            if isinstance(current, ast.Name):
                parts.append(current.id)
            return ".".join(reversed(parts))
        return ""


class StyleAnalyzer(BaseAnalyzer):
    """Line length, trailing whitespace."""
    name = "style"
    languages = {
        "python", "javascript", "typescript",
        "typescript-react", "javascript-react",
    }

    def analyze(
        self, source: str, lines: list[str],
        tree: Optional[ast.Module], meta: FileMetadata,
    ) -> list[Issue]:
        """TODO: Document analyze()."""
        issues: list[Issue] = []
        long_lines = 0

        for i, line in enumerate(lines, 1):
            raw = line.rstrip("\n").rstrip("\r")

            if raw != raw.rstrip():
                issues.append(Issue(
                    severity=Severity.INFO,
                    category="Style",
                    line=i,
                    message="Trailing whitespace",
                    auto_fixable=True,
                    confidence=1.0,
                ))

            if len(raw) > MAX_LINE_LENGTH:
                long_lines += 1
                if long_lines <= 10:
                    issues.append(Issue(
                        severity=Severity.INFO,
                        category="Style",
                        line=i,
                        message=(
                            f"Line too long "
                            f"({len(raw)} > {MAX_LINE_LENGTH})"
                        ),
                        confidence=1.0,
                    ))

        if long_lines > 10:
            issues.append(Issue(
                severity=Severity.INFO,
                category="Style",
                line=None,
                message=(
                    f"{long_lines} total lines exceed "
                    f"{MAX_LINE_LENGTH} chars"
                ),
                confidence=1.0,
            ))

        return issues


class ErrorHandlingAnalyzer(BaseAnalyzer):
    """Detects bare except, swallowed errors, broad catches."""
    name = "error-handling"
    languages = {"python"}

    def analyze(
        self, source: str, lines: list[str],
        tree: Optional[ast.Module], meta: FileMetadata,
    ) -> list[Issue]:
        """TODO: Document analyze()."""
        issues: list[Issue] = []
        if not tree:
            return issues

        for node in ast.walk(tree):
            if not isinstance(node, ast.ExceptHandler):
                continue

            if node.type is None:
                issues.append(Issue(
                    severity=Severity.WARNING,
                    category="Error Handling",
                    line=node.lineno,
                    message=(
                        "Bare 'except:' catches all exceptions "
                        "including SystemExit and KeyboardInterrupt"
                    ),
                    suggestion="Use 'except Exception:' at minimum.",
                    auto_fixable=True,
                    confidence=0.9,
                ))
            elif (isinstance(node.type, ast.Name)
                  and node.type.id == "Exception"):
                if (len(node.body) == 1
                        and isinstance(node.body[0], ast.Pass)):
                    issues.append(Issue(
                        severity=Severity.WARNING,
                        category="Error Handling",
                        line=node.lineno,
                        message=(
                            "'except Exception: pass' silently swallows "
                            "all errors"
                        ),
                        suggestion="At minimum, log the exception.",
                        confidence=0.85,
                    ))

        return issues


class DuplicateLineAnalyzer(BaseAnalyzer):
    """Finds blocks of duplicated lines (copy-paste detection)."""
    name = "duplicates"
    languages = {
        "python", "javascript", "typescript",
        "typescript-react", "javascript-react",
    }

    MIN_BLOCK = 4

    def analyze(
        self, source: str, lines: list[str],
        tree: Optional[ast.Module], meta: FileMetadata,
    ) -> list[Issue]:
        """TODO: Document analyze()."""
        issues: list[Issue] = []
        stripped = [l.strip() for l in lines]

        seen_blocks: dict[str, int] = {}
        i = 0
        while i < len(stripped) - self.MIN_BLOCK:
            block = "\n".join(stripped[i:i + self.MIN_BLOCK])

            non_empty = [
                l for l in stripped[i:i + self.MIN_BLOCK]
                if l and not l.startswith("#") and not l.startswith("//")
            ]
            if len(non_empty) < self.MIN_BLOCK - 1:
                i += 1
                continue

            h = hashlib.md5(block.encode()).hexdigest()
            if h in seen_blocks:
                issues.append(Issue(
                    severity=Severity.WARNING,
                    category="Duplication",
                    line=i + 1,
                    message=(
                        f"Lines {i + 1}–{i + self.MIN_BLOCK} duplicate "
                        f"lines {seen_blocks[h]}–"
                        f"{seen_blocks[h] + self.MIN_BLOCK - 1}"
                    ),
                    suggestion="Extract into a shared function or constant.",
                    confidence=0.7,
                ))
                i += self.MIN_BLOCK
            else:
                seen_blocks[h] = i + 1
                i += 1

        return issues


class StrengthDetector:
    """Detects positive patterns — produces strength notes, not issues."""

    STRENGTH_PATTERNS = [
        (r"async\s+def",
         "Async/await patterns — good for I/O concurrency"),
        (r"@dataclass",
         "Dataclass usage — clean data modeling"),
        (r"class\s+\w+\(.*ABC\)",
         "Abstract base classes — proper interface design"),
        (r"logging\.",
         "Structured logging in use"),
        (r"try:",
         "Error handling present"),
        (r"from typing import|from __future__ import annotations",
         "Type annotation awareness"),
        (r"def test_|class Test|import pytest|import unittest",
         "Test code present"),
        (r"\.env|environ|getenv",
         "Environment-based configuration"),
        (r"circuit.?break|rate.?limit|retry",
         "Resilience patterns (circuit breaker / rate limiter)"),
    ]

    def detect(self, source: str) -> list[str]:
        """Return list of strength descriptions found in source."""
        strengths: list[str] = []
        seen: set[str] = set()
        for pattern, description in self.STRENGTH_PATTERNS:
            if (re.search(pattern, source, re.IGNORECASE)
                    and description not in seen):
                strengths.append(f"✅ {description}")
                seen.add(description)
        return strengths


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  STEP 3 — MODULAR FIXERS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


class BaseFixer(ABC):
    """Abstract base for auto-fix passes."""
    name: str = "base"

    @abstractmethod
    def generate_fixes(
        self,
        source: str,
        issues: list[Issue],
        meta: FileMetadata,
    ) -> list[Fix]:
        """Return Fix objects. Each Fix.apply is a source→source transform."""
        ...


class TrailingWhitespaceFixer(BaseFixer):
    """Removes trailing whitespace from all lines."""
    name = "trailing-whitespace"

    def generate_fixes(
        self, source: str, issues: list[Issue], meta: FileMetadata,
    ) -> list[Fix]:
        """TODO: Document generate_fixes()."""
        ws_issues = [
            i for i in issues
            if i.category == "Style" and "Trailing whitespace" in i.message
        ]
        if not ws_issues:
            return []

        def apply(src: str) -> str:
            """TODO: Document apply()."""
            return "\n".join(line.rstrip() for line in src.split("\n"))

        return [Fix(
            description=(
                f"Remove trailing whitespace ({len(ws_issues)} lines)"
            ),
            category="Style",
            confidence=1.0,
            apply=apply,
        )]


class BareExceptFixer(BaseFixer):
    """Converts bare 'except:' to 'except Exception:'."""
    name = "bare-except"

    def generate_fixes(
        self, source: str, issues: list[Issue], meta: FileMetadata,
    ) -> list[Fix]:
        """TODO: Document generate_fixes()."""
        bare = [
            i for i in issues
            if i.category == "Error Handling" and "Bare" in i.message
        ]
        if not bare:
            return []

        def apply(src: str) -> str:
            """TODO: Document apply()."""
            return re.sub(
                r"^(\s*)except\s*:\s*$",
                r"\1except Exception:",
                src,
                flags=re.MULTILINE,
            )

        return [Fix(
            description=(
                f"Convert {len(bare)} bare except → except Exception"
            ),
            category="Error Handling",
            confidence=0.9,
            apply=apply,
        )]


class SecuritySecretFixer(BaseFixer):
    """Replaces hardcoded secrets with os.environ.get() placeholders."""
    name = "secrets"

    def generate_fixes(
        self, source: str, issues: list[Issue], meta: FileMetadata,
    ) -> list[Fix]:
        """TODO: Document generate_fixes()."""
        secret_issues = [
            i for i in issues
            if i.category == "Security" and "secret" in i.message.lower()
        ]
        if not secret_issues or meta.language != "python":
            return []

        def apply(src: str) -> str:
            """TODO: Document apply()."""
            result = src
            result = re.sub(
                r"""(api[_-]?key\s*=\s*)(['"])([^'"]{10,})\2""",
                r'\1os.environ.get("API_KEY", "")',
                result,
                flags=re.IGNORECASE,
            )
            result = re.sub(
                r"""(password\s*=\s*)(['"])([^'"]{4,})\2""",
                r'\1os.environ.get("PASSWORD", "")',
                result,
                flags=re.IGNORECASE,
            )
            result = re.sub(
                r"""(secret\s*=\s*)(['"])([^'"]{8,})\2""",
                r'\1os.environ.get("SECRET_KEY", "")',
                result,
                flags=re.IGNORECASE,
            )
            return result

        return [Fix(
            description=(
                f"Replace {len(secret_issues)} hardcoded secrets "
                f"with os.environ.get()"
            ),
            category="Security",
            confidence=0.75,
            apply=apply,
        )]


class DocstringInsertFixer(BaseFixer):
    """Inserts placeholder docstrings for undocumented classes/functions."""
    name = "docstrings"

    def generate_fixes(
        self, source: str, issues: list[Issue], meta: FileMetadata,
    ) -> list[Fix]:
        """TODO: Document generate_fixes()."""
        doc_issues = [
            i for i in issues
            if (i.category == "Documentation"
                and i.auto_fixable
                and "lacks a docstring" in i.message)
        ]
        if not doc_issues or meta.language != "python":
            return []

        def apply(src: str) -> str:
            """TODO: Document apply()."""
            try:
                tree = ast.parse(src)
            except SyntaxError:
                return src

            src_lines = src.split("\n")
            # Collect insertion points: (line_index, docstring_text)
            insertions: list[tuple[int, str]] = []

            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    if not ast.get_docstring(node) and node.body:
                        insert_at = node.body[0].lineno - 1
                        col = getattr(node, "col_offset", 0)
                        indent = " " * (col + 4)
                        doc = (
                            f'{indent}"""TODO: Document class '
                            f'{node.name}."""'
                        )
                        insertions.append((insert_at, doc))

                elif isinstance(
                    node, (ast.FunctionDef, ast.AsyncFunctionDef)
                ):
                    if not ast.get_docstring(node):
                        body_len = (
                            (node.end_lineno or node.lineno) - node.lineno
                        )
                        if node.name.startswith("_") and body_len < 5:
                            continue
                        if node.body:
                            insert_at = node.body[0].lineno - 1
                            col = getattr(node, "col_offset", 0)
                            indent = " " * (col + 4)
                            doc = (
                                f'{indent}"""TODO: Document '
                                f'{node.name}()."""'
                            )
                            insertions.append((insert_at, doc))

            # Insert in reverse order to keep line numbers stable
            for line_idx, docstring in sorted(
                insertions, key=lambda x: x[0], reverse=True
            ):
                if 0 <= line_idx <= len(src_lines):
                    src_lines.insert(line_idx, docstring)

            return "\n".join(src_lines)

        return [Fix(
            description=(
                f"Insert {len(doc_issues)} placeholder docstrings"
            ),
            category="Documentation",
            confidence=0.85,
            apply=apply,
        )]


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  STEP 4 — REVIEW ENGINE (ORCHESTRATOR)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


class ReviewEngine:
    """
    Orchestrates the full pipeline:
      inspect → analyze (multi-pass) → fix → report
    """

    def __init__(
        self,
        fix_confidence: float = DEFAULT_FIX_CONFIDENCE,
        dry_run: bool = False,
        verbose: bool = False,
    ):
        """TODO: Document __init__()."""
        self.fix_confidence = fix_confidence
        self.dry_run = dry_run
        self.verbose = verbose

        self.analyzers: list[BaseAnalyzer] = [
            ImportAnalyzer(),
            DocstringAnalyzer(),
            TypeHintAnalyzer(),
            SecurityAnalyzer(),
            MemoryAnalyzer(),
            AsyncAnalyzer(),
            StyleAnalyzer(),
            ErrorHandlingAnalyzer(),
            DuplicateLineAnalyzer(),
        ]

        self.fixers: list[BaseFixer] = [
            TrailingWhitespaceFixer(),
            BareExceptFixer(),
            SecuritySecretFixer(),
            DocstringInsertFixer(),
        ]

        self.strength_detector = StrengthDetector()

    def review_file(self, filepath: Path) -> ReviewResult:
        """Run the full pipeline on a single file."""
        print(f"\n🔍 REVIEWING: {filepath}")
        print("─" * 60)

        # Step 1: Inspect
        meta, source = inspect_file(filepath)

        result = ReviewResult(
            metadata=meta,
            original_source=source,
            fixed_source=source,
        )

        # Step 2: Parse AST (Python only)
        tree: Optional[ast.Module] = None
        if meta.language == "python":
            try:
                tree = ast.parse(source)
            except SyntaxError as e:
                result.issues.append(Issue(
                    severity=Severity.CRITICAL,
                    category="Syntax",
                    line=e.lineno,
                    message=f"SyntaxError: {e.msg}",
                    suggestion=(
                        "Fix syntax before other analysis can proceed."
                    ),
                ))

        lines = source.splitlines(keepends=True)

        # Step 3: Run analyzers
        print("\n📊 Running analysis passes...")
        for analyzer in self.analyzers:
            if meta.language not in analyzer.languages:
                continue
            try:
                found = analyzer.analyze(source, lines, tree, meta)
                result.issues.extend(found)
                if self.verbose and found:
                    print(
                        f"  ├─ {analyzer.name}: "
                        f"{len(found)} issues"
                    )
                elif self.verbose:
                    print(f"  ├─ {analyzer.name}: ✓ clean")
            except Exception as e:
                print(f"  ├─ {analyzer.name}: ⚠️ crashed ({e})")

        # Step 4: Detect strengths
        result.strengths = self.strength_detector.detect(source)

        # Step 5: Generate & apply fixes
        if not self.dry_run:
            print("\n🔧 Generating fixes...")
            all_fixes: list[Fix] = []

            for fixer in self.fixers:
                try:
                    fixes = fixer.generate_fixes(
                        source, result.issues, meta
                    )
                    all_fixes.extend(fixes)
                except Exception as e:
                    print(f"  ├─ {fixer.name}: ⚠️ crashed ({e})")

            current_source = source
            for fix in all_fixes:
                if fix.confidence >= self.fix_confidence:
                    try:
                        new_source = fix.apply(current_source)
                        if new_source != current_source:
                            current_source = new_source
                            result.fixes_applied.append(str(fix))
                            print(f"  ✅ Applied: {fix}")
                        else:
                            result.fixes_skipped.append(
                                f"{fix} (no change)"
                            )
                    except Exception as e:
                        result.fixes_skipped.append(
                            f"{fix} (error: {e})"
                        )
                        print(f"  ❌ Failed: {fix} — {e}")
                else:
                    result.fixes_skipped.append(
                        f"{fix} (below threshold "
                        f"{self.fix_confidence:.0%})"
                    )
                    if self.verbose:
                        print(f"  ⏭️  Skipped: {fix}")

            result.fixed_source = current_source
        else:
            print("\n⏸️  Dry run — no fixes applied")

        return result


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  STEP 5 — REPORT GENERATOR
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


class ReportGenerator:
    """Generates Markdown reports and console summaries."""

    @staticmethod
    def print_console(result: ReviewResult) -> None:
        """Pretty-print results to terminal with color."""
        print(f"\n{'═' * 60}")
        print("  📋 REVIEW REPORT")
        print(f"{'═' * 60}")
        print(f"  File   : {result.metadata.path.name}")
        print(f"  Health : {result.health_score}/100")
        print(
            f"  Issues : {len(result.issues)} "
            f"({result.error_count} errors, "
            f"{result.warning_count} warnings)"
        )
        print(
            f"  Fixes  : {len(result.fixes_applied)} applied, "
            f"{len(result.fixes_skipped)} skipped"
        )

        if result.strengths:
            print("\n  💪 Strengths:")
            for s in result.strengths:
                print(f"    {s}")

        if result.issues:
            print("\n  🔍 Issues by severity:")
            for severity in (
                Severity.CRITICAL, Severity.ERROR,
                Severity.WARNING, Severity.INFO,
            ):
                group = [
                    i for i in result.issues
                    if i.severity == severity
                ]
                if not group:
                    continue
                print(
                    f"\n    {severity.emoji} "
                    f"{severity.value.upper()} ({len(group)}):"
                )
                for issue in group[:15]:
                    print(f"      {issue}")
                    if issue.suggestion:
                        print(f"        💡 {issue.suggestion}")
                if len(group) > 15:
                    print(f"      … and {len(group) - 15} more")

        if result.fixes_applied:
            print("\n  🔧 Fixes Applied:")
            for f in result.fixes_applied:
                print(f"    {f}")

        diff = result.unified_diff()
        if diff:
            diff_lines = diff.split("\n")
            print(f"\n  📝 Diff Preview ({len(diff_lines)} lines):")
            for line in diff_lines[:30]:
                if line.startswith("+") and not line.startswith("+++"):
                    print(f"    \033[32m{line}\033[0m")
                elif line.startswith("-") and not line.startswith("---"):
                    print(f"    \033[31m{line}\033[0m")
                else:
                    print(f"    {line}")
            if len(diff_lines) > 30:
                print(f"    … ({len(diff_lines) - 30} more lines)")

        print(f"\n{'═' * 60}\n")

    @staticmethod
    def write_markdown(
        result: ReviewResult, output_path: Path
    ) -> None:
        """Write a full Markdown report to disk."""
        md: list[str] = []
        md.append("# Code Review Report\n")
        md.append(f"**Generated**: {result.timestamp}  ")
        md.append(f"**File**: `{result.metadata.path}`  ")
        md.append(f"**Language**: {result.metadata.language}  ")
        md.append(
            f"**Size**: {result.metadata.size_bytes:,} bytes "
            f"({result.metadata.line_count:,} lines)  "
        )
        md.append(f"**Health Score**: {result.health_score}/100  ")
        md.append(
            f"**SHA-256**: `{result.metadata.sha256[:32]}…`\n"
        )

        # Summary table
        md.append("## Summary\n")
        md.append("| Metric | Value |")
        md.append("|--------|-------|")
        md.append(f"| Total Issues | {len(result.issues)} |")
        crit = sum(
            1 for i in result.issues
            if i.severity == Severity.CRITICAL
        )
        errs = sum(
            1 for i in result.issues
            if i.severity == Severity.ERROR
        )
        infos = sum(
            1 for i in result.issues
            if i.severity == Severity.INFO
        )
        md.append(f"| Critical | {crit} |")
        md.append(f"| Errors | {errs} |")
        md.append(f"| Warnings | {result.warning_count} |")
        md.append(f"| Info | {infos} |")
        md.append(f"| Fixes Applied | {len(result.fixes_applied)} |")
        md.append(
            f"| Fixes Skipped | {len(result.fixes_skipped)} |\n"
        )

        if result.strengths:
            md.append("## Strengths\n")
            for s in result.strengths:
                md.append(f"- {s}")
            md.append("")

        if result.issues:
            md.append("## Issues\n")
            categories = sorted(
                set(i.category for i in result.issues)
            )
            for cat in categories:
                cat_issues = [
                    i for i in result.issues if i.category == cat
                ]
                md.append(f"### {cat} ({len(cat_issues)})\n")
                for issue in cat_issues:
                    loc = (
                        f"Line {issue.line}"
                        if issue.line else "General"
                    )
                    md.append(
                        f"- {issue.severity.emoji} **{loc}**: "
                        f"{issue.message}"
                    )
                    if issue.suggestion:
                        md.append(f"  - 💡 {issue.suggestion}")
                    md.append(
                        f"  - Confidence: {issue.confidence:.0%} "
                        f"| Auto-fixable: "
                        f"{'Yes' if issue.auto_fixable else 'No'}"
                    )
                md.append("")

        if result.fixes_applied:
            md.append("## Fixes Applied\n")
            for f in result.fixes_applied:
                md.append(f"- {f}")
            md.append("")

        if result.fixes_skipped:
            md.append("## Fixes Skipped\n")
            for f in result.fixes_skipped:
                md.append(f"- {f}")
            md.append("")

        diff = result.unified_diff()
        if diff:
            md.append("## Unified Diff\n")
            md.append("```diff")
            md.append(diff)
            md.append("```\n")

        output_path.write_text("\n".join(md), encoding="utf-8")
        print(f"📄 Report written: {output_path}")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  STEP 6 — FILE WRITER (backup + verify)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


def write_fixed_file(
    result: ReviewResult,
    backup: bool = True,
    dry_run: bool = False,
) -> Optional[Path]:
    """
    Write the fixed source back to disk.

    Returns:
        Path to backup file if created, else None.
    """
    if result.original_source == result.fixed_source:
        print("📎 No changes to write.")
        return None

    if dry_run:
        print("⏸️  Dry run — would write changes but skipping.")
        return None

    filepath = result.metadata.path
    backup_path: Optional[Path] = None

    if backup:
        backup_path = filepath.with_suffix(
            filepath.suffix + BACKUP_SUFFIX
        )
        counter = 1
        while backup_path.exists():
            backup_path = filepath.with_suffix(
                f"{filepath.suffix}.{counter}{BACKUP_SUFFIX}"
            )
            counter += 1
        shutil.copy2(filepath, backup_path)
        print(f"💾 Backup: {backup_path}")

    filepath.write_text(result.fixed_source, encoding="utf-8")
    print(f"✅ Fixed file written: {filepath}")

    verify_hash = hashlib.sha256(
        filepath.read_text(encoding="utf-8").encode()
    ).hexdigest()
    print(f"🔒 New SHA-256: {verify_hash[:16]}…")

    return backup_path


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  CLI ENTRY POINT
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


def build_parser() -> argparse.ArgumentParser:
    """Build the CLI argument parser."""
    p = argparse.ArgumentParser(
        prog="code-worker",
        description=(
            "Automated Code Review, Fix & Augmentation Engine"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=textwrap.dedent("""\
            Examples:
              python code-worker.py app.py
              python code-worker.py app.py --dry-run --verbose
              python code-worker.py app.py --backup --fix-confidence 0.8
              python code-worker.py src/ --recursive
              python code-worker.py module.py --report-only
        """),
    )
    p.add_argument(
        "target", type=Path,
        help="File or directory to review",
    )
    p.add_argument(
        "--dry-run", action="store_true",
        help="Analyze without writing any changes",
    )
    p.add_argument(
        "--report-only", action="store_true",
        help="Only generate report, don't modify files",
    )
    p.add_argument(
        "--backup", action="store_true", default=True,
        help="Create .bak backup before modifying (default: True)",
    )
    p.add_argument(
        "--no-backup", action="store_true",
        help="Skip backup creation",
    )
    p.add_argument(
        "--recursive", action="store_true",
        help="Scan directories recursively",
    )
    p.add_argument(
        "--verbose", "-v", action="store_true",
        help="Show detailed analysis output",
    )
    p.add_argument(
        "--fix-confidence", type=float,
        default=DEFAULT_FIX_CONFIDENCE,
        metavar="THRESHOLD",
        help=(
            f"Only apply fixes above this confidence "
            f"(0.0–1.0, default: {DEFAULT_FIX_CONFIDENCE})"
        ),
    )
    p.add_argument(
        "--json", action="store_true",
        help="Output results as JSON to stdout",
    )
    return p


def main() -> int:
    """Main entry point. Returns exit code (1 if errors found)."""
    parser = build_parser()
    args = parser.parse_args()

    do_backup = args.backup and not args.no_backup
    is_dry_run = args.dry_run or args.report_only

    print(r"""
    ╔══════════════════════════════════════════════════╗
    ║   🛠️  CODE WORKER — Review & Fix Engine          ║
    ║   Production-Grade Static Analysis               ║
    ╚══════════════════════════════════════════════════╝
    """)

    files = discover_files(args.target, recursive=args.recursive)
    if not files:
        return 1

    print(f"📂 Found {len(files)} file(s) to review\n")

    engine = ReviewEngine(
        fix_confidence=args.fix_confidence,
        dry_run=is_dry_run,
        verbose=args.verbose,
    )

    reporter = ReportGenerator()
    all_results: list[ReviewResult] = []
    total_issues = 0
    total_fixes = 0

    for filepath in files:
        try:
            result = engine.review_file(filepath)
            all_results.append(result)
            total_issues += len(result.issues)
            total_fixes += len(result.fixes_applied)

            reporter.print_console(result)

            if (not is_dry_run
                    and result.fixed_source != result.original_source):
                write_fixed_file(
                    result, backup=do_backup, dry_run=False
                )

            report_path = filepath.with_suffix(
                filepath.suffix + REPORT_SUFFIX
            )
            reporter.write_markdown(result, report_path)

        except KeyboardInterrupt:
            print("\n⚠️ Interrupted by user")
            break
        except Exception as e:
            print(f"\n❌ Failed to review {filepath}: {e}")
            if args.verbose:
                import traceback
                traceback.print_exc()

    if args.json:
        json_output = [r.to_dict() for r in all_results]
        print(json.dumps(json_output, indent=2))

    print(f"\n{'━' * 60}")
    print("  🏁 FINAL SUMMARY")
    print(f"{'━' * 60}")
    print(f"  Files reviewed  : {len(all_results)}")
    print(f"  Total issues    : {total_issues}")
    print(f"  Total fixes     : {total_fixes}")
    if all_results:
        avg_health = (
            sum(r.health_score for r in all_results)
            / len(all_results)
        )
        print(f"  Avg health score: {avg_health:.1f}/100")
    print(f"{'━' * 60}\n")

    has_errors = any(r.error_count > 0 for r in all_results)
    return 1 if has_errors else 0


if __name__ == "__main__":
    sys.exit(main())