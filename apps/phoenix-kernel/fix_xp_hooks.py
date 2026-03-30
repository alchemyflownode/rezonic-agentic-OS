import re
from pathlib import Path

kernel_path = Path("kernel.py")
content = kernel_path.read_text(encoding="utf-8")

# Find the correct async functions in _setup_routes
# RezCoder review endpoint is async
review_pattern = r'(async def api_rezcoder_review\(.*?\):\s*.*?return await.*?\)\n)'
match = re.search(review_pattern, content, re.DOTALL)
if match:
    print("Found review endpoint")
    # Add XP tracking before the return
    xp_code = '''
        
        # Add XP for review
        mastery = self.workers.get("mastery", {}).get("instance")
        if mastery:
            await mastery.add_xp("code_review", amount=50, description=f"Reviewed {filepath}", source="rezcoder")
'''
    content = content.replace(match.group(0), match.group(0) + xp_code)
    print("✅ Added XP to review")

# Fix endpoint
fix_pattern = r'(async def api_rezcoder_fix\(.*?\):\s*.*?return await.*?\)\n)'
match = re.search(fix_pattern, content, re.DOTALL)
if match:
    print("Found fix endpoint")
    xp_code = '''
        
        # Add XP for fix
        mastery = self.workers.get("mastery", {}).get("instance")
        if mastery:
            await mastery.add_xp("code_fix", amount=100, description=f"Fixed {filepath}", source="rezcoder")
'''
    content = content.replace(match.group(0), match.group(0) + xp_code)
    print("✅ Added XP to fix")

# Generate endpoint
generate_pattern = r'(async def api_mcp_generate\(.*?\):\s*.*?return await.*?\)\n)'
match = re.search(generate_pattern, content, re.DOTALL)
if match:
    print("Found generate endpoint")
    xp_code = '''
        
        # Add XP for code generation
        mastery = self.workers.get("mastery", {}).get("instance")
        if mastery:
            await mastery.add_xp("code_generate", amount=75, description=f"Generated code for {intent}", source="mcp")
'''
    content = content.replace(match.group(0), match.group(0) + xp_code)
    print("✅ Added XP to generate")

# Write backup
backup = kernel_path.with_suffix(".py.before_xp_fix")
kernel_path.rename(backup)
kernel_path.write_text(content, encoding="utf-8")
print(f"💾 Backup: {backup}")
print("✅ XP hooks fixed! Restart kernel.")
