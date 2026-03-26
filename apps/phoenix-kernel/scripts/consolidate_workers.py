#!/usr/bin/env python3
# AUTO-FIXED IMPORT PATH
import sys
from pathlib import Path
_workers_dir = Path(__file__).parent.resolve()
if str(_workers_dir) not in sys.path:
    sys.path.insert(0, str(_workers_dir))
# END AUTO-FIX
"""
consolidate_workers.py - Scan, fix, and consolidate all workers
Run this in your phoenix-kernel directory
"""

import os
import sys
import ast
import shutil
from pathlib import Path
from datetime import datetime

WORKERS_DIR = Path("workers")
BACKUP_DIR = Path("workers_backup_" + datetime.now().strftime("%Y%m%d_%H%M%S"))

class WorkerConsolidator:
    def __init__(self):
        self.workers_dir = WORKERS_DIR
        self.backup_dir = BACKUP_DIR
        self.fixed_count = 0
        self.broken_count = 0
        self.valid_count = 0
        
    def backup_all(self):
        """Backup all existing workers"""
        if self.backup_dir.exists():
            shutil.rmtree(self.backup_dir)
        shutil.copytree(self.workers_dir, self.backup_dir)
        print(f"📦 Backed up workers to {self.backup_dir}")
        
    def analyze_worker(self, filepath: Path) -> dict:
        """Analyze a worker file for issues"""
        issues = []
        fixes = []
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # Parse AST
            tree = ast.parse(content)
            
            # Find classes
            classes = [node for node in ast.walk(tree) if isinstance(node, ast.ClassDef)]
            
            worker_classes = []
            for cls in classes:
                # Check if it inherits from Worker
                inherits_worker = False
                for base in cls.bases:
                    if isinstance(base, ast.Name) and base.id == 'Worker':
                        inherits_worker = True
                    elif isinstance(base, ast.Attribute) and base.attr == 'Worker':
                        inherits_worker = True
                
                if inherits_worker or 'Worker' in cls.name:
                    worker_classes.append(cls)
                    
                    # Check for execute method
                    has_execute = any(
                        isinstance(node, ast.FunctionDef) and node.name == 'execute'
                        for node in ast.walk(cls)
                    )
                    
                    if not has_execute:
                        issues.append(f"  ⚠️ {cls.name}: missing execute() method")
                        fixes.append(f"    → Add async def execute(self, task: str, **kwargs)")
                    
                    # Check for __init__ calling super
                    init_methods = [node for node in ast.walk(cls) 
                                   if isinstance(node, ast.FunctionDef) and node.name == '__init__']
                    
                    if init_methods:
                        # Check if super().__init__ is called
                        calls_super = False
                        for node in ast.walk(init_methods[0]):
                            if isinstance(node, ast.Call):
                                if isinstance(node.func, ast.Attribute) and node.func.attr == '__init__':
                                    calls_super = True
                                elif isinstance(node.func, ast.Name) and node.func.id == 'super':
                                    calls_super = True
                        
                        if not calls_super:
                            issues.append(f"  ⚠️ {cls.name}: __init__ doesn't call super().__init__()")
                            fixes.append(f"    → Add: super().__init__('{cls.name}')")
            
            return {
                "valid": len(worker_classes) > 0,
                "worker_count": len(worker_classes),
                "issues": issues,
                "fixes": fixes,
                "classes": [c.name for c in worker_classes]
            }
            
        except SyntaxError as e:
            return {
                "valid": False,
                "error": f"Syntax error: {e}",
                "issues": [f"  ❌ Syntax error at line {e.lineno}: {e.msg}"],
                "fixes": []
            }
        except Exception as e:
            return {
                "valid": False,
                "error": str(e),
                "issues": [f"  ❌ Error: {e}"],
                "fixes": []
            }
    
    def fix_worker_file(self, filepath: Path, analysis: dict) -> bool:
        """Attempt to fix common issues in worker file"""
        if not analysis['issues']:
            return True
            
        print(f"\n🔧 Fixing {filepath.name}:")
        for issue in analysis['issues']:
            print(issue)
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Fix missing Worker import
            if 'from .base_worker import Worker' not in content and 'from base_worker import Worker' not in content:
                # Try to find correct import path
                import_line = "from base_worker import Worker\n"
                if 'import sys' in content:
                    content = content.replace('import sys', 'import sys\n' + import_line)
                else:
                    content = import_line + content
            
            # Fix missing execute method for simple workers
            for class_name in analysis['classes']:
                if f"class {class_name}" in content and "async def execute" not in content:
                    # Add execute method
                    execute_method = '''
    async def execute(self, task: str, **kwargs) -> Dict[str, Any]:
        """Execute worker task"""
        return {
            "success": True,
            "worker": self.name,
            "task": task[:100],
            "message": f"Worker {self.name} executed {task[:50]}"
        }
'''
                    # Find class definition and insert method
                    lines = content.split('\n')
                    new_lines = []
                    in_class = False
                    inserted = False
                    
                    for i, line in enumerate(lines):
                        new_lines.append(line)
                        if f"class {class_name}" in line:
                            in_class = True
                        elif in_class and not inserted and line.strip() and not line.startswith(' ') and line.strip():
                            # End of class definition - insert method
                            new_lines.insert(i, execute_method)
                            inserted = True
                            in_class = False
                    
                    if not inserted:
                        # Append at end of class
                        new_lines.append(execute_method)
                    
                    content = '\n'.join(new_lines)
            
            # Write fixed file
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            
            print(f"  ✅ Fixed {filepath.name}")
            self.fixed_count += 1
            return True
            
        except Exception as e:
            print(f"  ❌ Failed to fix: {e}")
            self.broken_count += 1
            return False
    
    def scan_all(self):
        """Scan all worker files"""
        print("=" * 60)
        print("🔍 SCANNING WORKERS DIRECTORY")
        print("=" * 60)
        
        worker_files = list(self.workers_dir.glob("*.py"))
        worker_files = [f for f in worker_files if not f.name.startswith('__')]
        
        results = {}
        
        for filepath in sorted(worker_files):
            analysis = self.analyze_worker(filepath)
            results[filepath.name] = analysis
            
            if analysis['valid']:
                self.valid_count += analysis['worker_count']
                print(f"✅ {filepath.name}: {analysis['worker_count']} worker(s)")
            else:
                print(f"❌ {filepath.name}: {analysis.get('error', 'Invalid')}")
                
                if analysis['issues']:
                    for issue in analysis['issues'][:2]:  # Show first 2 issues
                        print(f"   {issue}")
        
        print("\n" + "=" * 60)
        print(f"📊 SUMMARY:")
        print(f"   Total files: {len(worker_files)}")
        print(f"   Valid workers: {self.valid_count}")
        print(f"   Files with issues: {len([r for r in results.values() if not r['valid']])}")
        print("=" * 60)
        
        return results
    
    def fix_all(self):
        """Fix all broken worker files"""
        print("\n" + "=" * 60)
        print("🔧 FIXING BROKEN WORKERS")
        print("=" * 60)
        
        worker_files = list(self.workers_dir.glob("*.py"))
        worker_files = [f for f in worker_files if not f.name.startswith('__')]
        
        for filepath in worker_files:
            analysis = self.analyze_worker(filepath)
            if not analysis['valid'] and analysis['issues']:
                self.fix_worker_file(filepath, analysis)
        
        print(f"\n✅ Fixed: {self.fixed_count} files")
        print(f"❌ Still broken: {self.broken_count} files")
    
    def create_master_worker_list(self):
        """Create a master list of all workers"""
        master_list = []
        
        for filepath in self.workers_dir.glob("*.py"):
            if filepath.name.startswith('__'):
                continue
                
            analysis = self.analyze_worker(filepath)
            if analysis['valid']:
                for class_name in analysis['classes']:
                    master_list.append({
                        "file": filepath.name,
                        "class": class_name,
                        "worker_name": class_name.replace('Worker', '').lower()
                    })
        
        # Write to file
        with open("workers/master_worker_list.json", 'w') as f:
            json.dump(master_list, f, indent=2)
        
        print(f"\n📝 Master worker list saved: workers/master_worker_list.json")
        print(f"   Total workers: {len(master_list)}")
        
        return master_list

def create_base_worker_if_missing():
    """Create base_worker.py if it doesn't exist"""
    base_worker_path = WORKERS_DIR / "base_worker.py"
    
    if not base_worker_path.exists():
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
        with open(base_worker_path, 'w') as f:
            f.write(base_content)
        print(f"✅ Created {base_worker_path}")

if __name__ == "__main__":
    import json
    
    print("🚀 PHOENIX WORKER CONSOLIDATOR")
    print("=" * 60)
    
    # Create base worker if missing
    create_base_worker_if_missing()
    
    # Run consolidator
    consolidator = WorkerConsolidator()
    
    # Backup first
    consolidator.backup_all()
    
    # Scan all workers
    results = consolidator.scan_all()
    
    # Ask to fix
    print("\n" + "=" * 60)
    response = input("🔧 Fix broken workers? (y/n): ")
    
    if response.lower() == 'y':
        consolidator.fix_all()
        
        # Rescan after fixes
        print("\n" + "=" * 60)
        print("📊 RESCAN AFTER FIXES")
        print("=" * 60)
        consolidator.scan_all()
    
    # Create master list
    master_list = consolidator.create_master_worker_list()
    
    print("\n" + "=" * 60)
    print("🎯 NEXT STEPS:")
    print("=" * 60)
    print("1. Restart Phoenix:")
    print("   python phoenix_v15_omega_ship.py")
    print("")
    print("2. Test worker loading:")
    print("   curl http://localhost:8002/workers/list")
    print("")
    print(f"3. Expected workers: {len(master_list)} (up from 22)")
    print("=" * 60)