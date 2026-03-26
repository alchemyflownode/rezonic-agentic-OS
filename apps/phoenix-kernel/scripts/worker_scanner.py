#!/usr/bin/env python3
# AUTO-FIXED IMPORT PATH
import sys
from pathlib import Path
_workers_dir = Path(__file__).parent.resolve()
if str(_workers_dir) not in sys.path:
    sys.path.insert(0, str(_workers_dir))
# END AUTO-FIX
"""
Worker Security Scanner & Validator
Scans all workers for: security issues, code quality, loading problems
"""

import os
import sys
import ast
import re
import json
import importlib.util
import inspect
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Set, Tuple, Any

WORKERS_DIR = Path("D:/Rezonic_Agentic/apps/phoenix-kernel/workers")
REPORT_DIR = Path("worker_reports")
REPORT_DIR.mkdir(exist_ok=True)

class WorkerSecurityScanner:
    """Scan workers for security issues and loading problems"""
    
    # Dangerous patterns to detect
    DANGEROUS_PATTERNS = [
        (r'os\.system\s*\(', "System command execution"),
        (r'subprocess\.', "Subprocess execution"),
        (r'eval\s*\(', "Eval execution"),
        (r'exec\s*\(', "Exec execution"),
        (r'__import__\s*\(', "Dynamic import"),
        (r'compile\s*\(', "Compile execution"),
        (r'pickle\.loads', "Unsafe deserialization"),
        (r'rm\s+-rf', "Dangerous file operation"),
        (r'del\s+/f', "Dangerous Windows command"),
        (r'format\s+[a-z]:', "Format command"),
        (r'mkfs', "Filesystem creation"),
        (r'shutdown', "System shutdown"),
        (r'reboot', "System reboot"),
        (r':\(\).*:\|:.*&:;:', "Fork bomb"),
    ]
    
    # Suspicious imports
    SUSPICIOUS_IMPORTS = [
        'os.system', 'subprocess', 'socket', 'requests', 'urllib',
        'pickle', 'marshal', 'base64', 'codecs', 'cryptography'
    ]
    
    def __init__(self, workers_dir: Path):
        self.workers_dir = workers_dir
        self.results = {
            "total_files": 0,
            "valid_workers": 0,
            "invalid_workers": 0,
            "security_issues": [],
            "syntax_errors": [],
            "import_errors": [],
            "workers_found": [],
            "worker_classes": [],
            "security_score": 100,
        }
    
    def scan_file(self, filepath: Path) -> Dict[str, Any]:
        """Scan a single worker file"""
        result = {
            "filename": filepath.name,
            "valid": False,
            "security_issues": [],
            "syntax_error": None,
            "import_errors": [],
            "worker_classes": [],
            "dangerous_patterns": [],
            "size": filepath.stat().st_size,
            "modified": datetime.fromtimestamp(filepath.stat().st_mtime).isoformat()
        }
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Check for BOM
            if content.startswith('\ufeff'):
                result["security_issues"].append("BOM character detected (U+FEFF)")
                self.results["security_score"] -= 5
            
            # Check for dangerous patterns
            for pattern, desc in self.DANGEROUS_PATTERNS:
                if re.search(pattern, content, re.IGNORECASE):
                    result["dangerous_patterns"].append(desc)
                    result["security_issues"].append(f"Dangerous pattern: {desc}")
                    self.results["security_score"] -= 10
            
            # Parse AST for deeper analysis
            try:
                tree = ast.parse(content)
                
                # Find imports
                imports = []
                for node in ast.walk(tree):
                    if isinstance(node, ast.Import):
                        for alias in node.names:
                            imports.append(alias.name)
                    elif isinstance(node, ast.ImportFrom):
                        module = node.module or ""
                        for alias in node.names:
                            imports.append(f"{module}.{alias.name}")
                
                # Check suspicious imports
                for imp in imports:
                    for suspicious in self.SUSPICIOUS_IMPORTS:
                        if suspicious in imp:
                            result["security_issues"].append(f"Suspicious import: {imp}")
                            self.results["security_score"] -= 5
                
                # Find Worker classes
                for node in ast.walk(tree):
                    if isinstance(node, ast.ClassDef):
                        # Check if it inherits from Worker
                        inherits_worker = False
                        for base in node.bases:
                            if isinstance(base, ast.Name) and base.id == 'Worker':
                                inherits_worker = True
                            elif isinstance(base, ast.Attribute) and base.attr == 'Worker':
                                inherits_worker = True
                        
                        if inherits_worker or 'Worker' in node.name:
                            # Check for execute method
                            has_execute = any(
                                isinstance(n, ast.FunctionDef) and n.name == 'execute'
                                for n in ast.walk(node)
                            )
                            
                            result["worker_classes"].append({
                                "name": node.name,
                                "has_execute": has_execute,
                                "line": node.lineno
                            })
                            
                            if not has_execute:
                                result["security_issues"].append(f"Class {node.name} missing execute() method")
                                self.results["security_score"] -= 10
                
                result["valid"] = len(result["worker_classes"]) > 0
                
            except SyntaxError as e:
                result["syntax_error"] = f"Line {e.lineno}: {e.msg}"
                self.results["syntax_errors"].append(filepath.name)
                result["valid"] = False
                self.results["security_score"] -= 50
                
        except Exception as e:
            result["syntax_error"] = str(e)
            result["valid"] = False
            self.results["security_score"] -= 50
        
        return result
    
    def test_import(self, filepath: Path) -> Tuple[bool, str]:
        """Test if worker can be imported"""
        try:
            spec = importlib.util.spec_from_file_location(filepath.stem, filepath)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            return True, "Import successful"
        except Exception as e:
            return False, str(e)[:200]
    
    def scan_all(self):
        """Scan all worker files"""
        print("🔍 SCANNING WORKERS FOR SECURITY ISSUES")
        print("=" * 80)
        
        py_files = list(self.workers_dir.glob("*.py"))
        self.results["total_files"] = len(py_files)
        
        for py_file in sorted(py_files):
            if py_file.name.startswith('__'):
                continue
            
            print(f"\n📄 {py_file.name}")
            
            # Scan file
            scan_result = self.scan_file(py_file)
            
            # Test import
            can_import, import_error = self.test_import(py_file)
            
            if scan_result["valid"] and can_import:
                self.results["valid_workers"] += 1
                print(f"  ✅ VALID WORKER")
                for wc in scan_result["worker_classes"]:
                    self.results["worker_classes"].append({
                        "file": py_file.name,
                        "class": wc["name"],
                        "has_execute": wc["has_execute"]
                    })
                    self.results["workers_found"].append(wc["name"])
                    print(f"     📦 {wc['name']} (execute: {wc['has_execute']})")
            else:
                self.results["invalid_workers"] += 1
                print(f"  ❌ INVALID")
                if scan_result["syntax_error"]:
                    print(f"     🔴 Syntax error: {scan_result['syntax_error']}")
                if not can_import:
                    print(f"     🔴 Import error: {import_error}")
            
            # Report security issues
            if scan_result["security_issues"]:
                print(f"  ⚠️ Security issues:")
                for issue in scan_result["security_issues"][:5]:
                    print(f"     • {issue}")
                self.results["security_issues"].append({
                    "file": py_file.name,
                    "issues": scan_result["security_issues"]
                })
            
            # Store result
            self.results[py_file.name] = scan_result
        
        return self.results
    
    def generate_report(self):
        """Generate detailed security report"""
        print("\n" + "=" * 80)
        print("📊 SECURITY REPORT")
        print("=" * 80)
        
        print(f"\n📁 Directory: {self.workers_dir}")
        print(f"📄 Total files: {self.results['total_files']}")
        print(f"✅ Valid workers: {self.results['valid_workers']}")
        print(f"❌ Invalid workers: {self.results['invalid_workers']}")
        print(f"🔒 Security score: {self.results['security_score']}/100")
        
        print(f"\n📦 Worker classes found: {len(self.results['worker_classes'])}")
        for wc in self.results['worker_classes'][:20]:
            print(f"  • {wc['class']} ({wc['file']})")
        if len(self.results['worker_classes']) > 20:
            print(f"  ... and {len(self.results['worker_classes'])-20} more")
        
        if self.results['security_issues']:
            print(f"\n⚠️ Security issues found: {len(self.results['security_issues'])} files")
            for issue in self.results['security_issues'][:10]:
                print(f"  • {issue['file']}: {len(issue['issues'])} issue(s)")
        
        if self.results['syntax_errors']:
            print(f"\n🔴 Files with syntax errors: {len(self.results['syntax_errors'])}")
            for err in self.results['syntax_errors'][:10]:
                print(f"  • {err}")
        
        # Save detailed report
        report_file = REPORT_DIR / f"worker_scan_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w') as f:
            # Convert results to serializable format
            serializable = {k: v for k, v in self.results.items() 
                          if isinstance(v, (str, int, float, bool, list, dict))}
            json.dump(serializable, f, indent=2, default=str)
        
        print(f"\n📄 Detailed report saved: {report_file}")
        
        return self.results
    
    def create_fixed_worker(self, filename: str, class_name: str):
        """Create a fixed version of a broken worker"""
        template = '''#!/usr/bin/env python3
"""
{filename} - Fixed Worker
Auto-generated by security scanner
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from base_worker import Worker


class {class_name}(Worker):
    """Fixed worker - {filename}"""
    
    def __init__(self):
        super().__init__("{worker_name}")
    
    async def execute(self, task: str, **kwargs):
        """Execute worker task"""
        return {{
            "success": True,
            "worker": self.name,
            "task": task[:100],
            "message": f"Worker {self.name} executed"
        }}
'''
        
        worker_name = class_name.replace('Worker', '').lower()
        content = template.format(
            filename=filename,
            class_name=class_name,
            worker_name=worker_name
        )
        
        output_path = self.workers_dir / f"fixed_{filename}"
        with open(output_path, 'w') as f:
            f.write(content)
        
        print(f"  ✅ Created fixed worker: {output_path.name}")
        return output_path

def main():
    print("🛡️ PHOENIX WORKER SECURITY SCANNER")
    print("=" * 80)
    
    if not WORKERS_DIR.exists():
        print(f"❌ Workers directory not found: {WORKERS_DIR}")
        return
    
    scanner = WorkerSecurityScanner(WORKERS_DIR)
    
    # Scan all workers
    results = scanner.scan_all()
    
    # Generate report
    scanner.generate_report()
    
    print("\n" + "=" * 80)
    print("🎯 RECOMMENDATIONS")
    print("=" * 80)
    
    if results['security_score'] < 70:
        print("⚠️ Low security score! Review security issues above.")
    
    if results['invalid_workers'] > 0:
        print("\n🔧 To fix invalid workers:")
        print("   1. Check syntax errors in the files listed")
        print("   2. Ensure all workers inherit from 'Worker' class")
        print("   3. Add missing 'execute' methods")
        print("   4. Check import dependencies")
    
    if results['valid_workers'] > 0:
        print(f"\n✅ You have {results['valid_workers']} valid workers ready to load!")
        print("   Restart Phoenix to load them all")
    
    print("\n📋 To fix a specific worker manually:")
    print("   python worker_fixer.py <worker_name>.py")
    
    # Ask if user wants to fix broken workers
    if results['invalid_workers'] > 0:
        print("\n" + "=" * 80)
        response = input("🔧 Attempt to fix broken workers? (y/n): ")
        if response.lower() == 'y':
            fixed = 0
            for wc in results['worker_classes']:
                if not any(wc['class'] in str(s) for s in results['syntax_errors']):
                    continue
                # Create fixed version
                scanner.create_fixed_worker(f"{wc['class']}.py", wc['class'])
                fixed += 1
            print(f"\n✅ Created {fixed} fixed worker templates")
            print("   Review and rename them to replace broken workers")

if __name__ == "__main__":
    main()