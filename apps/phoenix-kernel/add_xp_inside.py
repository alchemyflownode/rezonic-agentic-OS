import re
from pathlib import Path

kernel_path = Path("kernel.py")
content = kernel_path.read_text(encoding="utf-8")

# Fix api_rezcoder_review
review_pattern = r'(async def api_rezcoder_review\(.*?\):\s*.*?result = await worker\.execute\("review".*?\)\n)(\s+return result)'
def add_xp_to_review(match):
    return match.group(1) + '''    
    # Add XP for review
    mastery = self.workers.get("mastery", {}).get("instance")
    if mastery:
        await mastery.add_xp("code_review", amount=50, description=f"Reviewed {filepath}", source="rezcoder")
    
''' + match.group(2)

if re.search(review_pattern, content, re.DOTALL):
    content = re.sub(review_pattern, add_xp_to_review, content, flags=re.DOTALL)
    print("✅ Added XP to review endpoint")
else:
    print("⚠️ Could not find review endpoint pattern")

# Fix api_rezcoder_fix
fix_pattern = r'(async def api_rezcoder_fix\(.*?\):\s*.*?result = await worker\.execute\("fix".*?\)\n)(\s+return result)'
def add_xp_to_fix(match):
    return match.group(1) + '''    
    # Add XP for fix
    mastery = self.workers.get("mastery", {}).get("instance")
    if mastery:
        await mastery.add_xp("code_fix", amount=100, description=f"Fixed {filepath}", source="rezcoder")
    
''' + match.group(2)

if re.search(fix_pattern, content, re.DOTALL):
    content = re.sub(fix_pattern, add_xp_to_fix, content, flags=re.DOTALL)
    print("✅ Added XP to fix endpoint")
else:
    print("⚠️ Could not find fix endpoint pattern")

# Fix api_mcp_generate
gen_pattern = r'(async def api_mcp_generate\(.*?\):\s*.*?result = await worker\.execute\(f"generate_code.*?\)\n)(\s+return result)'
def add_xp_to_gen(match):
    return match.group(1) + '''    
    # Add XP for code generation
    mastery = self.workers.get("mastery", {}).get("instance")
    if mastery:
        await mastery.add_xp("code_generate", amount=75, description=f"Generated code for {intent}", source="mcp")
    
''' + match.group(2)

if re.search(gen_pattern, content, re.DOTALL):
    content = re.sub(gen_pattern, add_xp_to_gen, content, flags=re.DOTALL)
    print("✅ Added XP to generate endpoint")
else:
    print("⚠️ Could not find generate endpoint pattern")

# Write backup and save
backup = kernel_path.with_suffix(".py.before_xp_inside")
kernel_path.rename(backup)
kernel_path.write_text(content, encoding="utf-8")
print(f"💾 Backup: {backup}")
print("✅ XP code added inside functions! Restart kernel.")
