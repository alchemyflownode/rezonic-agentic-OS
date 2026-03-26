#!/usr/bin/env python3
"""Auto-fix import paths for all Phoenix workers"""
import sys
from pathlib import Path

FIX_SNIPPET = '''# AUTO-FIXED IMPORT PATH
import sys
from pathlib import Path
_workers_dir = Path(__file__).parent.resolve()
if str(_workers_dir) not in sys.path:
    sys.path.insert(0, str(_workers_dir))
# END AUTO-FIX
'''

def fix_worker_file(filepath: Path):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Skip if already fixed
    if '# AUTO-FIXED IMPORT PATH' in content:
        return False
    
    # Insert after shebang/encoding if present
    lines = content.split('\n')
    insert_idx = 0
    if lines and lines[0].startswith('#!'):
        insert_idx = 1
    if len(lines) > insert_idx and 'coding:' in lines[insert_idx]:
        insert_idx += 1
    
    lines.insert(insert_idx, FIX_SNIPPET.rstrip())
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))
    
    print(f"✅ Fixed: {filepath.name}")
    return True

if __name__ == "__main__":
    workers_dir = Path(__file__).parent
    fixed = 0
    for py_file in workers_dir.glob("*.py"):
        if py_file.name in ['__init__.py', 'fix_worker_imports.py']:
            continue
        if fix_worker_file(py_file):
            fixed += 1
    print(f"\n🔧 Fixed {fixed} worker files")
    print("🚀 Restart Phoenix to load all workers")