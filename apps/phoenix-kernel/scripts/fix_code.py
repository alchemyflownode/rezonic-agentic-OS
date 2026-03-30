#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
╔═══════════════════════════════════════════════════════════════════════════════╗
║  fix_code.py - Phoenix Kernel v15.3.1 Auto-Patcher                            ║
║  Adds missing /kill/status HTTP endpoint                                      ║
╚═══════════════════════════════════════════════════════════════════════════════╝

Usage:
    python fix_code.py                          # Apply fix with backup
    python fix_code.py --dry-run               # Preview changes only
    python fix_code.py --file custom.py        # Patch different file
    python fix_code.py --no-backup             # Skip backup creation
"""
import re
import sys
import shutil
from pathlib import Path
from datetime import datetime

# ═══════════════════════════════════════════════════════════════════════════════
# CONFIGURATION
# ═══════════════════════════════════════════════════════════════════════════════
DEFAULT_FILE = Path("rezonic_unified_v15.py")
BACKUP_DIR = Path("data/backups")

# The new endpoint code to inject
NEW_ENDPOINT = '''        @self.app.get("/kill/status", tags=["Security"], summary="Get kill switch status")
        async def kill_status():
            """Returns current kill switch state for monitoring dashboards.
            
            Returns:
                dict: {active: bool, triggered_at: float, triggered_by: str, reason: str}
            """
            return kill_switch.status()
'''

# ═══════════════════════════════════════════════════════════════════════════════
# CORE FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════════

def find_insertion_point(content: str) -> int:
    """
    Find the line number where we should insert the new endpoint.
    Strategy: Insert right before the first kill switch POST endpoint.
    """
    patterns = [
        r'# Kill Switch endpoints',
        r'@self\.app\.post\("/kill"\)',
        r'async def kill_endpoint',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, content)
        if match:
            return match.start()
    
    return -1


def apply_patch(content: str, insert_pos: int) -> str:
    """Insert the new endpoint code at the specified position."""
    # Ensure we're at a line boundary
    if insert_pos > 0 and content[insert_pos-1] != '\n':
        # Find the start of the current line
        newline_pos = content.rfind('\n', 0, insert_pos)
        insert_pos = newline_pos + 1 if newline_pos != -1 else 0
    
    return content[:insert_pos] + '\n' + NEW_ENDPOINT + '\n' + content[insert_pos:]


def create_backup(file_path: Path) -> Path:
    """Create timestamped backup of the original file."""
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = BACKUP_DIR / f"{file_path.stem}_v15.3.1_pre-fix_{timestamp}{file_path.suffix}"
    shutil.copy2(file_path, backup_path)
    return backup_path


def validate_patch(content: str) -> tuple[bool, str]:
    """Basic validation that the patch was applied correctly."""
    checks = [
        ('@self.app.get("/kill/status")', "Endpoint decorator"),
        ('async def kill_status():', "Function definition"),
        ('return kill_switch.status()', "Return statement"),
        ('tags=["Security"]', "OpenAPI tag"),
    ]
    
    for pattern, description in checks:
        if pattern not in content:
            return False, f"Missing: {description}"
    
    return True, "All checks passed"


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN EXECUTION
# ═══════════════════════════════════════════════════════════════════════════════

def main():
    # Parse command line arguments (simple parser, no external deps)
    args = sys.argv[1:]
    file_path = DEFAULT_FILE
    do_backup = True
    dry_run = False
    
    i = 0
    while i < len(args):
        arg = args[i]
        if arg in ("-f", "--file") and i + 1 < len(args):
            file_path = Path(args[i + 1])
            i += 2
        elif arg == "--no-backup":
            do_backup = False
            i += 1
        elif arg in ("-n", "--dry-run"):
            dry_run = True
            i += 1
        elif arg in ("-h", "--help"):
            print(__doc__)
            return 0
        else:
            i += 1
    
    # Resolve and validate file path
    file_path = file_path.resolve()
    if not file_path.exists():
        print(f"❌ File not found: {file_path}")
        print(f"💡 Tip: Run from Phoenix kernel directory or use --file PATH")
        return 1
    
    print(f"🔍 Reading: {file_path}")
    try:
        content = file_path.read_text(encoding='utf-8')
    except Exception as e:
        print(f"❌ Failed to read file: {e}")
        return 1
    
    # Find insertion point
    insert_pos = find_insertion_point(content)
    if insert_pos == -1:
        print("❌ Could not find insertion point for kill switch endpoints")
        print("💡 Ensure the file contains '# Kill Switch endpoints' comment")
        return 1
    
    print(f"📍 Found insertion point at character {insert_pos}")
    
    # Apply the patch
    patched_content = apply_patch(content, insert_pos)
    
    # Validate the result
    is_valid, message = validate_patch(patched_content)
    if not is_valid:
        print(f"❌ Patch validation failed: {message}")
        return 1
    print(f"✅ Patch validation: {message}")
    
    # Dry run mode
    if dry_run:
        print("🧪 DRY RUN - No changes written to disk")
        print("✅ Would add /kill/status endpoint successfully")
        return 0
    
    # Create backup if requested
    if do_backup:
        try:
            backup_path = create_backup(file_path)
            print(f"💾 Backup created: {backup_path}")
        except Exception as e:
            print(f"⚠️ Backup failed: {e}")
            response = input("Continue without backup? (y/N): ").strip().lower()
            if response != 'y':
                return 1
    
    # Write the patched file
    try:
        file_path.write_text(patched_content, encoding='utf-8')
        print(f"✅ Patched: {file_path}")
    except Exception as e:
        print(f"❌ Failed to write patched file: {e}")
        return 1
    
    # Success summary
    print("\n" + "═" * 70)
    print("🎉 PATCH COMPLETE")
    print("═" * 70)
    print("📋 What was added:")
    print("   • GET /kill/status endpoint")
    print("   • OpenAPI tag: Security")
    print("   • Returns kill_switch.status() dict")
    print("\n🧪 Test the fix:")
    print("   1. Restart Phoenix: python rezonic_unified_v15.py")
    print("   2. Test endpoint: curl http://127.0.0.1:8002/kill/status")
    print("   3. View docs: http://127.0.0.1:8002/docs")
    print("\n🔐 Expected response:")
    print('   {"active":false,"triggered_at":null,"triggered_by":null,"reason":null}')
    print("═" * 70 + "\n")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())