import re
from pathlib import Path

kernel_path = Path("kernel.py")
content = kernel_path.read_text(encoding="utf-8")

# Add XP reward after RezCoder review
review_pattern = r'(async def api_rezcoder_review.*?return await.*?\)\n)'
match = re.search(review_pattern, content, re.DOTALL)
if match:
    # Add XP tracking after review
    xp_tracking = '''
        # Add XP for review
        mastery = self.workers.get("mastery", {}).get("instance")
        if mastery:
            await mastery.add_xp("code_review", amount=50, description=f"Reviewed {filepath}", source="rezcoder")
        
'''
    content = content.replace(match.group(0), match.group(0) + xp_tracking)
    print("✅ Added XP tracking to review endpoint")

# Add XP reward after RezCoder fix
fix_pattern = r'(async def api_rezcoder_fix.*?return await.*?\)\n)'
match = re.search(fix_pattern, content, re.DOTALL)
if match:
    xp_tracking = '''
        # Add XP for fix
        mastery = self.workers.get("mastery", {}).get("instance")
        if mastery:
            await mastery.add_xp("code_fix", amount=100, description=f"Fixed {filepath}", source="rezcoder")
        
'''
    content = content.replace(match.group(0), match.group(0) + xp_tracking)
    print("✅ Added XP tracking to fix endpoint")

# Add XP reward after MCP generate
generate_pattern = r'(async def api_mcp_generate.*?return await.*?\)\n)'
match = re.search(generate_pattern, content, re.DOTALL)
if match:
    xp_tracking = '''
        # Add XP for code generation
        mastery = self.workers.get("mastery", {}).get("instance")
        if mastery:
            await mastery.add_xp("code_generate", amount=75, description=f"Generated code for {intent}", source="mcp")
        
'''
    content = content.replace(match.group(0), match.group(0) + xp_tracking)
    print("✅ Added XP tracking to generate endpoint")

# Write backup and save
backup = kernel_path.with_suffix(".py.before_xp_hooks")
kernel_path.rename(backup)
kernel_path.write_text(content, encoding="utf-8")
print(f"💾 Backup: {backup}")
print("✅ XP hooks added! Restart kernel to activate.")
