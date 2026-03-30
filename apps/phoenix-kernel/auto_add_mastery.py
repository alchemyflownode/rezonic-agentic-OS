#!/usr/bin/env python3
"""
auto_add_mastery.py — Automatically add MasteryWorker to kernel.py
"""

import re
from pathlib import Path

KERNEL_PATH = Path("kernel.py")

# Read kernel.py
content = KERNEL_PATH.read_text(encoding="utf-8")

# Check if mastery already imported
if "from workers.mastery_worker import MasteryWorker" in content:
    print("✅ MasteryWorker already imported")
else:
    # Find last import line and add new import
    import_lines = re.findall(r'^from workers\.\w+ import \w+$', content, re.MULTILINE)
    if import_lines:
        last_import = import_lines[-1]
        new_import = "from workers.mastery_worker import MasteryWorker"
        content = content.replace(last_import, last_import + "\n" + new_import)
        print("✅ Added import for MasteryWorker")
    else:
        print("⚠️ Could not find import pattern")

# Check if mastery in builtins
if '("mastery", MasteryWorker)' in content:
    print("✅ MasteryWorker already in builtins")
else:
    # Find builtins list and add mastery
    builtins_match = re.search(r'builtins\s*=\s*\[(.*?)\]', content, re.DOTALL)
    if builtins_match:
        builtins_content = builtins_match.group(1)
        if '("rezcoder"' in builtins_content:
            # Add after rezcoder
            builtins_content = builtins_content.replace(
                '("rezcoder", RezCoderWorker),',
                '("rezcoder", RezCoderWorker),\n    ("mastery", MasteryWorker),'
            )
        else:
            # Add at the end
            builtins_content = builtins_content.rstrip() + ',\n    ("mastery", MasteryWorker)'
        
        content = content.replace(builtins_match.group(0), f'builtins = [{builtins_content}]')
        print("✅ Added MasteryWorker to builtins")
    else:
        print("⚠️ Could not find builtins list")

# Add reflex commands for mastery
if "async def cmd_mastery" in content:
    print("✅ Mastery reflex commands already exist")
else:
    # Find the reflex commands section
    reflex_match = re.search(r'(async def cmd_\w+\(cmd: str\):.*?)(?=async def |\Z)', content, re.DOTALL)
    if reflex_match:
        # Add mastery commands
        mastery_commands = '''
    async def cmd_mastery(cmd: str):
        """Handle mastery commands: /xp, /add_xp, /achievements, /level"""
        worker = self.workers.get("mastery", {}).get("instance")
        if not worker:
            return {"type": "reflex", "content": "🎮 Mastery system initializing..."}
        await worker.initialize()
        return await worker.execute(cmd)
'''
        content = content.replace(reflex_match.group(0), reflex_match.group(0) + mastery_commands)
        
        # Register the command
        content = content.replace(
            'self.reflex.commands["/rez-review"] = cmd_rez_review',
            'self.reflex.commands["/rez-review"] = cmd_rez_review\n        self.reflex.commands["/xp"] = cmd_mastery\n        self.reflex.commands["/add_xp"] = cmd_mastery\n        self.reflex.commands["/achievements"] = cmd_mastery\n        self.reflex.commands["/level"] = cmd_mastery'
        )
        print("✅ Added mastery reflex commands")
    else:
        print("⚠️ Could not find reflex command section")

# Write updated kernel
backup_path = KERNEL_PATH.with_suffix(".py.before_mastery")
KERNEL_PATH.rename(backup_path)
KERNEL_PATH.write_text(content, encoding="utf-8")
print(f"💾 Backup saved to {backup_path}")
print("✅ Kernel updated! Restart to apply changes.")
