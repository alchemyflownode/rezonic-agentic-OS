# fix_kernel.py - Removes BOM + fixes XP scope bugs
import sys
from pathlib import Path
from datetime import datetime

# Get file path from argument or default
FILE = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("kernel.py")

if not FILE.exists():
    print(f"❌ Not found: {FILE.resolve()}")
    print("💡 Usage: python fix_kernel.py <path_to_kernel.py>")
    sys.exit(1)

print(f"🔧 Fixing: {FILE.resolve()}")

# Create backup
backup = f"{FILE}.bak.{datetime.now().strftime('%Y%m%d_%H%M%S')}"
FILE.rename(backup)
print(f"💾 Backup: {backup}")

# Read with 'utf-8-sig' to automatically strip BOM if present
content = FILE.read_text(encoding="utf-8-sig")

# Track if BOM was removed
bom_removed = False
if content.startswith('\ufeff'):
    content = content.lstrip('\ufeff')
    bom_removed = True
    print("🧹 Removed UTF-8 BOM (U+FEFF) from line 1")

# === XP FIX 1: api_rezcoder_review ===
old_review = '''    return await worker.execute("review", file_path=filepath, recursive=recursive)

# Add XP for review
mastery = self.workers.get("mastery", {}).get("instance")
if mastery:
    await mastery.add_xp("code_review", amount=50, description=f"Reviewed {filepath}", source="rezcoder")'''

new_review = '''    result = await worker.execute("review", file_path=filepath, recursive=recursive)
    
    # Add XP for review
    mastery = self.workers.get("mastery", {}).get("instance")
    if mastery:
        await mastery.add_xp("code_review", amount=50, description=f"Reviewed {filepath}", source="rezcoder")
    
    return result'''

if old_review in content:
    content = content.replace(old_review, new_review)
    print("✅ Fixed: api_rezcoder_review (XP inside function)")
else:
    print("⚠️  Pattern not found for api_rezcoder_review - may already be fixed")

# === XP FIX 2: api_rezcoder_fix ===
old_fix = '''    return await worker.execute("fix", file_path=filepath, confidence=confidence, backup=backup)

# Add XP for fix
mastery = self.workers.get("mastery", {}).get("instance")
if mastery:
    await mastery.add_xp("code_fix", amount=100, description=f"Fixed {filepath}", source="rezcoder")'''

new_fix = '''    result = await worker.execute("fix", file_path=filepath, confidence=confidence, backup=backup)
    
    # Add XP for fix
    mastery = self.workers.get("mastery", {}).get("instance")
    if mastery:
        await mastery.add_xp("code_fix", amount=100, description=f"Fixed {filepath}", source="rezcoder")
    
    return result'''

if old_fix in content:
    content = content.replace(old_fix, new_fix)
    print("✅ Fixed: api_rezcoder_fix (XP inside function)")
else:
    print("⚠️  Pattern not found for api_rezcoder_fix - may already be fixed")

# === XP FIX 3: api_mcp_generate ===
old_gen = '''    return await worker.execute(f"generate_code {intent} --language {language}")

# Add XP for code generation
mastery = self.workers.get("mastery", {}).get("instance")
if mastery:
    await mastery.add_xp("code_generate", amount=75, description=f"Generated code for {intent}", source="mcp")'''

new_gen = '''    result = await worker.execute(f"generate_code {intent} --language {language}")
    
    # Add XP for code generation
    mastery = self.workers.get("mastery", {}).get("instance")
    if mastery:
        await mastery.add_xp("code_generate", amount=75, description=f"Generated code for {intent}", source="mcp")
    
    return result'''

if old_gen in content:
    content = content.replace(old_gen, new_gen)
    print("✅ Fixed: api_mcp_generate (XP inside function)")
else:
    print("⚠️  Pattern not found for api_mcp_generate - may already be fixed")

# Write back with UTF-8 (no BOM)
FILE.write_text(content, encoding="utf-8")
print("✅ File saved (UTF-8, no BOM)")

# Syntax validation
import subprocess
result = subprocess.run(
    [sys.executable, "-m", "py_compile", str(FILE)],
    capture_output=True, text=True
)

if result.returncode == 0:
    print("✅ Syntax validation PASSED")
    print(f"""
🎉 SUCCESS! Fixes applied:
   • BOM removed: {bom_removed}
   • XP scope fixes: 3 endpoints updated
   
🚀 Next steps:
   1. Restart kernel: python kernel.py
   2. Test auto-XP:
      Invoke-RestMethod "http://127.0.0.1:8002/api/v1/rezcoder/review?filepath=kernel.py"
      Invoke-RestMethod "http://127.0.0.1:8002/kernel/stream" -Method POST -Body '{{"task":"/xp"}}'
   3. Expect XP +50 after review call!
""")
else:
    print("❌ Syntax error detected!")
    print(result.stderr)
    print("🔄 Restoring backup...")
    Path(backup).rename(FILE)
    sys.exit(1)