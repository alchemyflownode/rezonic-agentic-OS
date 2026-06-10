#!/usr/bin/env python3
"""
integrate_rezcoder.py — Patch kernel.py to register RezCoder + MCP
"""

import re
import shutil
import sys
from pathlib import Path

KERNEL_PATH = Path("kernel.py")

# Markers to detect if already patched
MARKERS = {
    "rezcoder_import": "from workers.rezcoder import RezCoderWorker",
    "mcp_import": "from workers.sovereign_mcp_server import SovereignMcpServer",
    "rezcoder_builtin": '"rezcoder"',
    "mcp_builtin": '"sovereign_mcp_server"',
}


def patch_kernel(dry_run: bool = False) -> int:
    """Apply all integration patches to kernel.py."""
    if not KERNEL_PATH.exists():
        print(f"❌ {KERNEL_PATH} not found")
        sys.exit(1)

    content = KERNEL_PATH.read_text(encoding="utf-8")
    original = content
    changes = []

    # Add imports
    import_lines = [
        "from workers.rezcoder import RezCoderWorker",
        "from workers.sovereign_mcp_server import SovereignMcpServer",
    ]

    for import_line in import_lines:
        marker = import_line.split()[-1]
        if marker in content:
            print(f"  ✓ Import already present: {marker}")
            continue

        # Find last import line
        last_match = None
        for m in re.finditer(r"^from workers\.\w+ import \w+.*$", content, re.MULTILINE):
            last_match = m

        if last_match:
            pos = last_match.end()
            content = content[:pos] + f"\n{import_line}" + content[pos:]
            changes.append(f"Added import: {import_line}")
        else:
            lines = content.split("\n")
            last_import = 0
            for i, line in enumerate(lines):
                if line.startswith("import ") or line.startswith("from "):
                    last_import = i
            lines.insert(last_import + 1, import_line)
            content = "\n".join(lines)
            changes.append(f"Added import: {import_line}")

    # Add to builtins
    builtin_entries = [
        '    ("rezcoder", RezCoderWorker),',
        '    ("sovereign_mcp_server", SovereignMcpServer),',
    ]

    for entry in builtin_entries:
        name_match = re.search(r'"(\w+)"', entry)
        if name_match:
            worker_name = name_match.group(1)
            if worker_name in content and "builtins" in content:
                builtins_match = re.search(r"builtins\s*=\s*\[(.*?)\]", content, re.DOTALL)
                if builtins_match and worker_name in builtins_match.group(1):
                    print(f"  ✓ Builtin already registered: {worker_name}")
                    continue

        builtins_pattern = re.search(r"(builtins\s*=\s*\[)(.*?)(\s*\])", content, re.DOTALL)
        if builtins_pattern:
            existing = builtins_pattern.group(2).rstrip()
            if existing and not existing.rstrip().endswith(","):
                existing = existing.rstrip() + ","
            new_builtins = builtins_pattern.group(1) + existing + f"\n{entry}" + builtins_pattern.group(3)
            content = content.replace(builtins_pattern.group(0), new_builtins)
            changes.append(f"Added to builtins: {worker_name}")

    if not changes:
        print("\n✅ kernel.py already fully integrated!")
        return 0

    if dry_run:
        print(f"\n⏸️  DRY RUN — {len(changes)} changes would be applied:")
        for c in changes:
            print(f"  • {c}")
        return len(changes)

    # Create backup
    backup_path = KERNEL_PATH.with_suffix(".py.pre_integration")
    shutil.copy2(KERNEL_PATH, backup_path)
    print(f"\n💾 Backup: {backup_path}")

    # Write patched kernel
    KERNEL_PATH.write_text(content, encoding="utf-8")
    print(f"\n✅ Applied {len(changes)} patches to kernel.py:")
    for c in changes:
        print(f"  ✅ {c}")

    print("\n🔄 Restart Phoenix to activate integration.")
    return len(changes)


def main():
    print(r"""
    ╔══════════════════════════════════════════════╗
    ║  🔌 Phoenix Kernel Integration Patcher       ║
    ║  RezCoder + SovereignMcpServer               ║
    ╚══════════════════════════════════════════════╝
    """)

    dry_run = "--dry-run" in sys.argv
    patch_kernel(dry_run=dry_run)
    return 0


if __name__ == "__main__":
    sys.exit(main())
