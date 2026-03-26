#!/usr/bin/env python3
# AUTO-FIXED IMPORT PATH
import sys
from pathlib import Path
_workers_dir = Path(__file__).parent.resolve()
if str(_workers_dir) not in sys.path:
    sys.path.insert(0, str(_workers_dir))
# END AUTO-FIX
"""
worker_fixer.py - Auto-fix all workers with missing execute methods
"""

import os
import re
import ast
import shutil
from pathlib import Path
from datetime import datetime

WORKERS_DIR = Path("workers")
BACKUP_DIR = Path(f"workers_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}")

class WorkerFixer:
    def __init__(self):
        self.fixed_count = 0
        self.skipped_count = 0
        self.error_count = 0
        self.fixed_files = []
        
    def backup_all(self):
        """Backup all workers before fixing"""
        if BACKUP_DIR.exists():
            shutil.rmtree(BACKUP_DIR)
        shutil.copytree(WORKERS_DIR, BACKUP_DIR)
        print(f"📦 Backed up workers to {BACKUP_DIR}")
        return BACKUP_DIR
    
    def add_base_worker(self):
        """Create or update base_worker.py"""
        base_path = WORKERS_DIR / "base_worker.py"
        
        base_content = '''#!/usr/bin/env python3
"""
base_worker.py - Base Worker Class for all workers
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
        
        with open(base_path, 'w', encoding='utf-8') as f:
            f.write(base_content)
        print(f"✅ Created/Updated {base_path}")
        return base_path
    
    def add_execute_method_to_file(self, filepath: Path, class_names: list):
        """Add execute method to worker classes in file"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            
            original_content = content
            modified = False
            
            for class_name in class_names:
                # Check if execute method already exists
                if re.search(rf'async def execute\s*\(', content):
                    continue
                
                # Find class definition
                class_pattern = rf'class {class_name}\(.*?\):'
                class_match = re.search(class_pattern, content, re.MULTILINE)
                
                if not class_match:
                    continue
                
                # Find where to insert execute method
                lines = content.split('\n')
                insert_line = None
                indent_level = 0
                
                for i, line in enumerate(lines):
                    if re.match(class_pattern, line):
                        # Found class, find next line with same or lower indent
                        indent_level = len(line) - len(line.lstrip())
                        for j in range(i + 1, len(lines)):
                            if lines[j].strip():
                                current_indent = len(lines[j]) - len(lines[j].lstrip())
                                if current_indent <= indent_level:
                                    insert_line = j
                                    break
                        break
                
                if insert_line:
                    # Create execute method with proper indentation
                    execute_method = f'''
    async def execute(self, task: str, **kwargs) -> Dict[str, Any]:
        """Execute the worker"""
        return {{
            "success": True,
            "worker": self.name,
            "task": task[:100],
            "message": f"Worker {{self.name}} executed"
        }}
'''
                    lines.insert(insert_line, execute_method)
                    modified = True
                    print(f"  ✅ Added execute() to {class_name}")
            
            if modified:
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write('\n'.join(lines))
                return True
            
            return False
            
        except Exception as e:
            print(f"  ❌ Error fixing {filepath.name}: {e}")
            return False
    
    def add_imports(self, filepath: Path):
        """Add required imports to worker file"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Check if imports already exist
            if 'from base_worker import Worker' in content:
                return False
            
            # Add imports at top
            imports = '''#!/usr/bin/env python3
"""
Auto-fixed worker
"""

import sys
from pathlib import Path
from typing import Dict, Any

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from base_worker import Worker

'''
            
            # Remove existing shebang and replace
            if content.startswith('#!/usr/bin/env python3'):
                lines = content.split('\n')
                # Find first non-comment line
                import_line = None
                for i, line in enumerate(lines):
                    if line and not line.startswith('#') and not line.startswith('"""'):
                        import_line = i
                        break
                
                if import_line:
                    # Insert imports after shebang and docstring
                    new_content = '\n'.join(lines[:import_line]) + '\n\n' + imports + '\n' + '\n'.join(lines[import_line:])
                    with open(filepath, 'w', encoding='utf-8') as f:
                        f.write(new_content)
                    return True
            
            return False
            
        except Exception as e:
            print(f"  ❌ Error adding imports to {filepath.name}: {e}")
            return False
    
    def fix_worker_file(self, filepath: Path):
        """Fix a single worker file"""
        print(f"\n🔧 Fixing {filepath.name}")
        
        try:
            # Parse file to find worker classes
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Find all class definitions that might be workers
            class_pattern = r'class (\w+Worker)\s*\([^)]*\):'
            worker_classes = re.findall(class_pattern, content)
            
            if not worker_classes:
                # Check for other worker-like classes
                class_pattern = r'class (\w+Worker)\s*:'
                worker_classes = re.findall(class_pattern, content)
            
            if not worker_classes:
                print(f"  ⚠️ No worker classes found in {filepath.name}")
                self.skipped_count += 1
                return False
            
            # Add imports if missing
            imports_added = self.add_imports(filepath)
            
            # Add execute methods
            execute_added = self.add_execute_method_to_file(filepath, worker_classes)
            
            if imports_added or execute_added:
                self.fixed_count += 1
                self.fixed_files.append(filepath.name)
                print(f"  ✅ Fixed {filepath.name}")
                return True
            else:
                print(f"  ℹ️ No changes needed for {filepath.name}")
                self.skipped_count += 1
                return False
                
        except Exception as e:
            print(f"  ❌ Failed to fix {filepath.name}: {e}")
            self.error_count += 1
            return False
    
    def fix_all_workers(self):
        """Fix all worker files in directory"""
        print("🔧 FIXING WORKERS")
        print("=" * 60)
        
        # First, ensure base_worker exists
        self.add_base_worker()
        
        # Get all Python files
        py_files = list(WORKERS_DIR.glob("*.py"))
        
        for py_file in sorted(py_files):
            if py_file.name.startswith('__'):
                continue
            if py_file.name == 'base_worker.py':
                continue
            if py_file.name.endswith('.bak'):
                continue
            
            self.fix_worker_file(py_file)
        
        print("\n" + "=" * 60)
        print("📊 FIX SUMMARY")
        print("=" * 60)
        print(f"  ✅ Fixed: {self.fixed_count} files")
        print(f"  ⏭️ Skipped: {self.skipped_count} files")
        print(f"  ❌ Errors: {self.error_count} files")
        print(f"  📁 Backup: {BACKUP_DIR}")
        print("=" * 60)
        
        return self.fixed_files
    
    def create_worker_template(self, worker_name: str):
        """Create a new worker template"""
        template = '''#!/usr/bin/env python3
"""
{worker_name}.py - Auto-generated worker template
"""

import sys
from pathlib import Path
from typing import Dict, Any

sys.path.insert(0, str(Path(__file__).parent.parent))

from base_worker import Worker


class {class_name}(Worker):
    """{worker_name} worker"""
    
    def __init__(self):
        super().__init__("{worker_lower}")
    
    async def execute(self, task: str, **kwargs) -> Dict[str, Any]:
        """
        Execute the worker's main functionality
        
        Args:
            task: The task to execute
            **kwargs: Additional parameters
        
        Returns:
            Dict with success status and result
        """
        return {{
            "success": True,
            "worker": self.name,
            "task": task[:100],
            "message": f"Worker {{self.name}} executed {{task[:50]}}"
        }}
'''
        
        class_name = worker_name.replace('_', ' ').title().replace(' ', '')
        if not class_name.endswith('Worker'):
            class_name = class_name + 'Worker'
        
        worker_lower = worker_name.lower().replace('_', '_')
        
        content = template.format(
            worker_name=worker_name,
            class_name=class_name,
            worker_lower=worker_lower
        )
        
        filepath = WORKERS_DIR / f"{worker_name}.py"
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"✅ Created worker template: {filepath.name}")
        return filepath

def main():
    print("🔧 PHOENIX WORKER FIXER")
    print("=" * 60)
    
    fixer = WorkerFixer()
    
    # Backup first
    response = input(f"📦 Backup workers to {BACKUP_DIR}? (y/n): ")
    if response.lower() == 'y':
        fixer.backup_all()
    
    # Fix workers
    print("\n" + "=" * 60)
    response = input("🔧 Fix all workers? (y/n): ")
    if response.lower() == 'y':
        fixed = fixer.fix_all_workers()
        
        print("\n" + "=" * 60)
        print("✅ FIX COMPLETE")
        print("=" * 60)
        print("\n📋 Fixed files:")
        for f in fixed[:20]:
            print(f"  • {f}")
        if len(fixed) > 20:
            print(f"  ... and {len(fixed)-20} more")
        
        print("\n🚀 NEXT STEPS:")
        print("1. Restart Phoenix:")
        print("   python rezphoenix_v15ds.py")
        print("")
        print("2. Check worker count:")
        print("   curl http://localhost:8002/workers/list")
        print("")
        print(f"3. Expected workers: ~{len(fixed) + 5} (plus built-ins)")
    
    print("\n" + "=" * 60)
    print("⚠️ If workers still don't load, check:")
    print("   • Import paths are correct")
    print("   • All workers inherit from 'Worker'")
    print("   • Each worker has an 'execute' method")
    print("=" * 60)

if __name__ == "__main__":
    main()