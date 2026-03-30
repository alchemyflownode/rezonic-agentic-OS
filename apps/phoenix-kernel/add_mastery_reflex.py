# add_mastery_reflex.py
import re
from pathlib import Path

kernel_path = Path("kernel.py")
content = kernel_path.read_text(encoding="utf-8")

# Find the reflex command registration section
if 'self.reflex.commands["/xp"]' in content:
    print("✅ Mastery commands already registered")
else:
    # Find where other reflex commands are registered
    reflex_pattern = r'self\.reflex\.commands = \{(.*?)\}'
    match = re.search(reflex_pattern, content, re.DOTALL)
    
    if match:
        commands_block = match.group(1)
        # Add mastery commands
        new_commands = commands_block.rstrip() + ',\n        "/xp": self._cmd_mastery,\n        "/add_xp": self._cmd_mastery,\n        "/achievements": self._cmd_mastery,\n        "/level": self._cmd_mastery,\n        "/reset_mastery": self._cmd_mastery'
        content = content.replace(commands_block, new_commands)
        print("✅ Added mastery commands to reflex")
    
    # Also need to add the _cmd_mastery method
    if "async def _cmd_mastery" not in content:
        mastery_method = '''
    async def _cmd_mastery(self, cmd: str):
        """Handle mastery commands."""
        worker = self.workers.get("mastery", {}).get("instance")
        if not worker:
            return {"type": "reflex", "content": "🎮 Mastery system initializing..."}
        await worker.initialize()
        result = await worker.execute(cmd)
        return result
'''
        # Insert after another method
        content = content.replace("async def _cmd_", mastery_method + "    async def _cmd_", 1)
        print("✅ Added _cmd_mastery method")
    
    # Write backup and save
    backup = kernel_path.with_suffix(".py.before_mastery_reflex")
    kernel_path.rename(backup)
    kernel_path.write_text(content, encoding="utf-8")
    print(f"💾 Backup: {backup}")
    print("✅ Reflex commands added! Restart kernel.")

