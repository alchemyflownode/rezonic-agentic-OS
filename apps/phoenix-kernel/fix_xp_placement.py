import re
from pathlib import Path

kernel_path = Path("kernel.py")
content = kernel_path.read_text(encoding="utf-8")

# Remove duplicate XP blocks that are outside functions
content = re.sub(r'\n        # Add XP for review\n        mastery = self\.workers\.get\("mastery".*?\n        if mastery:.*?\n            await mastery\.add_xp.*?\n', '', content, flags=re.DOTALL)
content = re.sub(r'\n        # Add XP for fix\n        mastery = self\.workers\.get\("mastery".*?\n        if mastery:.*?\n            await mastery\.add_xp.*?\n', '', content, flags=re.DOTALL)
content = re.sub(r'\n        # Add XP for code generation\n        mastery = self\.workers\.get\("mastery".*?\n        if mastery:.*?\n            await mastery\.add_xp.*?\n', '', content, flags=re.DOTALL)

# Write backup and save
backup = kernel_path.with_suffix(".py.before_xp_fix2")
kernel_path.rename(backup)
kernel_path.write_text(content, encoding="utf-8")
print(f"💾 Backup: {backup}")
print("✅ Removed duplicate XP code. Now manually add XP inside functions as shown above.")
