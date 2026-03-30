import re
from pathlib import Path

kernel_path = Path("kernel.py")
content = kernel_path.read_text(encoding="utf-8")

# Find the reflex try_execute method and add mastery commands
reflex_pattern = r'(async def try_execute\(self, cmd: str\) -> Optional\[Dict\]:.*?)(?=\n    def _response|\n\n    def)'
match = re.search(reflex_pattern, content, re.DOTALL)

if match:
    reflex_content = match.group(1)
    
    # Add mastery commands right after the docstring/comments
    mastery_handler = '''
        # Mastery commands
        if lower.startswith(("/xp", "/add_xp", "/achievements", "/level", "/reset_mastery")):
            worker = self.kernel.workers.get("mastery", {}).get("instance")
            if worker:
                await worker.initialize()
                result = await worker.execute(cmd)
                if result.get("type") == "reflex":
                    return result
            return self._response("🎮 Mastery system initializing...")
        
'''
    
    # Insert after the initial comments but before the first if
    lines = reflex_content.split('\n')
    insert_pos = 0
    for i, line in enumerate(lines):
        if line.strip().startswith('if lower =='):
            insert_pos = i
            break
    
    lines.insert(insert_pos, mastery_handler.rstrip())
    new_reflex_content = '\n'.join(lines)
    
    content = content.replace(reflex_content, new_reflex_content)
    
    # Write backup and save
    backup = kernel_path.with_suffix(".py.before_mastery_reflex_fix")
    kernel_path.rename(backup)
    kernel_path.write_text(content, encoding="utf-8")
    print(f"💾 Backup: {backup}")
    print("✅ Added mastery commands to reflex try_execute")
    print("🔄 Restart kernel to activate")
else:
    print("Could not find reflex pattern")
