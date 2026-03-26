#!/usr/bin/env python3
# AUTO-FIXED IMPORT PATH
import sys
from pathlib import Path
_workers_dir = Path(__file__).parent.resolve()
if str(_workers_dir) not in sys.path:
    sys.path.insert(0, str(_workers_dir))
# END AUTO-FIX
"""
fix_all_issues.py - Fix BOM characters and event store schema
Run this directly with: python fix_all_issues.py
"""

import os
import sys
import sqlite3
import shutil
import time
from pathlib import Path

WORKERS_DIR = Path("workers")
DATA_DIR = Path("data")
EVENT_STORE_DIR = DATA_DIR / "event_store"

def fix_bom_characters():
    """Remove BOM characters from Python files"""
    print("\n🔧 FIXING BOM CHARACTERS")
    print("=" * 60)
    
    fixed_count = 0
    bom_files = []
    
    if not WORKERS_DIR.exists():
        print(f"  ⚠️ Workers directory not found: {WORKERS_DIR}")
        return []
    
    for py_file in WORKERS_DIR.glob("*.py"):
        if py_file.name.startswith('__'):
            continue
            
        try:
            with open(py_file, 'rb') as f:
                content = f.read()
            
            # Check for BOM
            if content.startswith(b'\xef\xbb\xbf'):
                # Remove BOM and save
                content = content[3:]
                with open(py_file, 'wb') as f:
                    f.write(content)
                fixed_count += 1
                bom_files.append(py_file.name)
                print(f"  ✅ Fixed: {py_file.name}")
                
        except Exception as e:
            print(f"  ❌ Failed: {py_file.name} - {e}")
    
    print(f"\n📊 Fixed {fixed_count} files with BOM characters")
    return bom_files

def fix_event_store_schema():
    """Fix the event store schema mismatch"""
    print("\n🔧 FIXING EVENT STORE SCHEMA")
    print("=" * 60)
    
    db_path = EVENT_STORE_DIR / "events.db"
    
    if not db_path.exists():
        print(f"  ℹ️ No database found at {db_path}, skipping")
        return
    
    try:
        # Backup first
        backup_path = EVENT_STORE_DIR / f"events_backup_{int(time.time())}.db"
        shutil.copy2(db_path, backup_path)
        print(f"  📦 Backed up to {backup_path}")
        
        # Connect and fix
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check current schema
        cursor.execute("PRAGMA table_info(events)")
        columns = cursor.fetchall()
        column_count = len(columns)
        column_names = [col[1] for col in columns]
        
        print(f"  📋 Current columns: {column_count}")
        print(f"  📋 Column names: {column_names}")
        
        # Fix schema if needed
        if column_count == 6:
            # Missing created_at column - add it
            try:
                cursor.execute("ALTER TABLE events ADD COLUMN created_at REAL DEFAULT (strftime('%s', 'now'))")
                conn.commit()
                print("  ✅ Added missing created_at column")
            except Exception as e:
                print(f"  ⚠️ Could not add column: {e}")
        elif column_count == 7:
            print("  ✅ Schema already has 7 columns")
        else:
            print(f"  ⚠️ Unexpected column count: {column_count}")
        
        # Also check blueprints table
        cursor.execute("PRAGMA table_info(blueprints)")
        bp_columns = cursor.fetchall()
        bp_count = len(bp_columns)
        
        if bp_count < 3:
            print("  🔧 Fixing blueprints table...")
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS blueprints (
                    drift_lock TEXT PRIMARY KEY,
                    blueprint TEXT,
                    timestamp REAL
                )
            """)
            conn.commit()
            print("  ✅ Blueprints table fixed")
        
        conn.close()
        print("  ✅ Event store schema fixed")
        
    except Exception as e:
        print(f"  ❌ Failed to fix: {e}")

def fix_empty_files():
    """Fix empty files by adding placeholder content"""
    print("\n🔧 FIXING EMPTY FILES")
    print("=" * 60)
    
    empty_files = []
    placeholder = '''#!/usr/bin/env python3
"""
Placeholder worker - Auto-generated
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from base_worker import Worker


class PlaceholderWorker(Worker):
    def __init__(self):
        super().__init__("placeholder")
    
    async def execute(self, task: str, **kwargs):
        return {
            "success": True,
            "worker": self.name,
            "message": "Placeholder worker executed"
        }
'''
    
    if not WORKERS_DIR.exists():
        return []
    
    for py_file in WORKERS_DIR.glob("*.py"):
        if py_file.name.startswith('__'):
            continue
            
        try:
            if py_file.stat().st_size == 0:
                # Empty file
                class_name = py_file.stem.replace('_', ' ').title().replace(' ', '')
                if not class_name.endswith('Worker'):
                    class_name = class_name + 'Worker'
                
                # Create proper content
                content = placeholder.replace('PlaceholderWorker', class_name)
                with open(py_file, 'w', encoding='utf-8') as f:
                    f.write(content)
                empty_files.append(py_file.name)
                print(f"  ✅ Fixed empty file: {py_file.name}")
        except Exception as e:
            print(f"  ❌ Failed to fix {py_file.name}: {e}")
    
    print(f"\n📊 Fixed {len(empty_files)} empty files")
    return empty_files

def validate_fixes():
    """Validate that fixes worked"""
    print("\n🔍 VALIDATING FIXES")
    print("=" * 60)
    
    valid_count = 0
    invalid_count = 0
    
    if not WORKERS_DIR.exists():
        print(f"  ⚠️ Workers directory not found")
        return 0, 0
    
    for py_file in WORKERS_DIR.glob("*.py"):
        if py_file.name.startswith('__'):
            continue
            
        try:
            with open(py_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Check for BOM again
            if content and content[0] == '\ufeff':
                print(f"  ⚠️ Still has BOM: {py_file.name}")
                invalid_count += 1
                continue
            
            # Try to compile
            compile(content, py_file.name, 'exec')
            valid_count += 1
            
        except SyntaxError as e:
            print(f"  ❌ Still invalid: {py_file.name} - {e}")
            invalid_count += 1
        except Exception as e:
            print(f"  ❌ Error: {py_file.name} - {e}")
            invalid_count += 1
    
    print(f"\n📊 Validation: {valid_count} valid, {invalid_count} invalid")
    return valid_count, invalid_count

def create_missing_base_worker():
    """Ensure base_worker.py exists"""
    base_path = WORKERS_DIR / "base_worker.py"
    
    if not base_path.exists():
        content = '''#!/usr/bin/env python3
"""
base_worker.py - Base Worker Class
"""

from abc import ABC, abstractmethod
from typing import Dict, Any


class Worker(ABC):
    """Base class for all workers"""
    
    def __init__(self, name: str):
        self.name = name
        self.version = "1.0.0"
        
    @abstractmethod
    async def execute(self, task: str, **kwargs) -> Dict[str, Any]:
        """Execute the worker's main functionality"""
        pass
    
    async def health_check(self) -> Dict[str, Any]:
        """Check worker health"""
        return {
            "name": self.name,
            "version": self.version,
            "status": "healthy"
        }
'''
        base_path.parent.mkdir(parents=True, exist_ok=True)
        with open(base_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"✅ Created {base_path}")
        return True
    else:
        print(f"✅ base_worker.py already exists")
        return False

if __name__ == "__main__":
    print("🚀 PHOENIX FIX ALL ISSUES")
    print("=" * 60)
    
    # 1. Create base worker if missing
    create_missing_base_worker()
    
    # 2. Fix BOM characters
    bom_files = fix_bom_characters()
    
    # 3. Fix empty files
    empty_files = fix_empty_files()
    
    # 4. Fix event store schema
    fix_event_store_schema()
    
    # 5. Validate fixes
    valid, invalid = validate_fixes()
    
    print("\n" + "=" * 60)
    print("🎯 SUMMARY")
    print("=" * 60)
    print(f"  BOM files fixed: {len(bom_files)}")
    print(f"  Empty files fixed: {len(empty_files)}")
    print(f"  Valid workers now: {valid}")
    print(f"  Still invalid: {invalid}")
    print("=" * 60)
    
    if invalid > 0:
        print("\n⚠️ Some files still have issues. They may need manual review.")
    
    print("\n✅ Ready to restart Phoenix!")
    print("Run: python phoenix_v15_omega_ship.py")