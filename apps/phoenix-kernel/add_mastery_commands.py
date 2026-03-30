import re
from pathlib import Path

kernel_path = Path("kernel.py")
content = kernel_path.read_text(encoding="utf-8")

# Look for the reflex command pattern
# Based on your banner, commands are likely in a list or dict
reflex_pattern = r'(if lower == "/health":.*?)(?=\n        if lower)'
reflex_match = re.search(reflex_pattern, content, re.DOTALL)

if reflex_match:
    print("Found reflex pattern, adding mastery commands...")
    
    # Add mastery commands before the health check
    mastery_commands = '''
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
    content = content.replace(reflex_match.group(0), mastery_commands + reflex_match.group(0))
    print("✅ Added mastery commands")
    
    # Write backup
    backup = kernel_path.with_suffix(".py.before_mastery")
    kernel_path.rename(backup)
    kernel_path.write_text(content, encoding="utf-8")
    print(f"💾 Backup: {backup}")
    print("✅ Restart kernel to activate")
else:
    print("Could not find reflex pattern. Let's try another approach...")
