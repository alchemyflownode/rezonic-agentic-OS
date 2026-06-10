# scan_workers.py
# Scan and analyze all workers in the workers directory

import os
import ast
import sys
from pathlib import Path
from datetime import datetime
from collections import defaultdict

# Configuration
WORKERS_DIR = Path("D:/Rezonic_Agentic/apps/phoenix-kernel/workers")
COWORKER_DIR = WORKERS_DIR / "coworker"
SKILLS_DIR = COWORKER_DIR / "skills"

def get_file_size(path):
    """Get file size in bytes"""
    try:
        return path.stat().st_size
    except:
        return 0

def count_lines(path):
    """Count lines in file"""
    try:
        with open(path, 'r', encoding='utf-8', errors='ignore') as f:
            return sum(1 for _ in f)
    except:
        return 0

def count_functions(path):
    """Count functions in Python file using AST"""
    try:
        with open(path, 'r', encoding='utf-8', errors='ignore') as f:
            tree = ast.parse(f.read())
            functions = [node for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)]
            classes = [node for node in ast.walk(tree) if isinstance(node, ast.ClassDef)]
            methods = []
            for cls in classes:
                methods.extend([m for m in cls.body if isinstance(m, ast.FunctionDef)])
            return len(functions), len(classes), len(methods)
    except Exception as e:
        return 0, 0, 0

def check_imports(path):
    """Check imports in Python file"""
    try:
        with open(path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
            imports = []
            for line in content.split('\n'):
                if line.startswith('import ') or line.startswith('from '):
                    imports.append(line.strip()[:50])
            return imports[:5]
    except:
        return []

def check_has_worker_class(path):
    """Check if file defines a Worker class"""
    try:
        with open(path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
            # Look for class definitions that inherit from Worker or contain 'Worker' in name
            lines = content.split('\n')
            for line in lines:
                if 'class' in line and 'Worker' in line:
                    return True
            return False
    except:
        return False

def categorize_worker(size):
    """Categorize worker by size"""
    if size >= 10000:
        return "EXCELLENT"
    elif size >= 3000:
        return "GOOD"
    elif size >= 1000:
        return "MEDIUM"
    else:
        return "STUB"

def scan_workers(directory):
    """Scan all workers in a directory"""
    results = []
    
    if not directory.exists():
        print(f"Directory not found: {directory}")
        return results
    
    py_files = list(directory.glob("*.py"))
    print(f"Found {len(py_files)} Python files in {directory}")
    
    for py_file in sorted(py_files):
        if py_file.name.startswith("__"):
            continue
            
        size = get_file_size(py_file)
        lines = count_lines(py_file)
        functions, classes, methods = count_functions(py_file)
        imports = check_imports(py_file)
        has_worker = check_has_worker_class(py_file)
        
        results.append({
            "name": py_file.name,
            "path": str(py_file.relative_to(WORKERS_DIR)),
            "size": size,
            "size_kb": round(size / 1024, 1),
            "lines": lines,
            "functions": functions,
            "classes": classes,
            "methods": methods,
            "imports": imports[:3],
            "has_worker": has_worker,
            "category": categorize_worker(size),
        })
    
    return results

def scan_skills(directory):
    """Scan skills in coworker/skills directory"""
    results = []
    
    if not directory.exists():
        return results
    
    for py_file in sorted(directory.glob("*.py")):
        if py_file.name.startswith("__"):
            continue
            
        size = get_file_size(py_file)
        lines = count_lines(py_file)
        functions, classes, methods = count_functions(py_file)
        
        results.append({
            "name": py_file.name,
            "path": str(py_file.relative_to(WORKERS_DIR)),
            "size": size,
            "size_kb": round(size / 1024, 1),
            "lines": lines,
            "functions": functions,
            "classes": classes,
            "methods": methods,
            "category": categorize_worker(size),
        })
    
    return results

def main():
    print("=" * 80)
    print("🐝 PHOENIX WORKER SCANNER")
    print(f"Scanning: {WORKERS_DIR}")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)
    
    # Scan main workers
    print("\n📁 MAIN WORKERS DIRECTORY")
    print("-" * 80)
    workers = scan_workers(WORKERS_DIR)
    
    if not workers:
        print("No workers found!")
        return
    
    # Statistics
    categories = defaultdict(int)
    total_size = 0
    total_lines = 0
    
    for w in workers:
        categories[w["category"]] += 1
        total_size += w["size"]
        total_lines += w["lines"]
    
    # Print summary
    print(f"\n📊 SUMMARY:")
    print(f"   Total workers: {len(workers)}")
    print(f"   Total size: {total_size / 1024:.1f} KB")
    print(f"   Total lines: {total_lines:,}")
    print(f"\n   Categories:")
    for cat, count in sorted(categories.items(), key=lambda x: -x[1]):
        print(f"     • {cat}: {count} workers")
    
    # Print stubs (< 1KB)
    stubs = [w for w in workers if w["category"] == "STUB"]
    if stubs:
        print(f"\n🔴 STUB WORKERS (< 1KB) — Need attention:")
        for w in stubs:
            print(f"   • {w['name']:<40} {w['size_kb']:>6} KB  {w['lines']:>4} lines")
    
    # Print small workers (1-3KB)
    small = [w for w in workers if 1000 <= w["size"] < 3000]
    if small:
        print(f"\n🟡 SMALL WORKERS (1-3KB) — May need review:")
        for w in small[:15]:
            print(f"   • {w['name']:<40} {w['size_kb']:>6} KB  {w['lines']:>4} lines")
        if len(small) > 15:
            print(f"   ... and {len(small) - 15} more")
    
    # Print largest workers
    large = sorted(workers, key=lambda x: -x["size"])[:15]
    print(f"\n✅ LARGEST WORKERS (Top 15):")
    for w in large:
        print(f"   • {w['name']:<40} {w['size_kb']:>6} KB  {w['lines']:>4} lines  {w['functions']} funcs")
    
    # Check workers without Worker class
    no_worker = [w for w in workers if not w["has_worker"] and w["size"] > 1000]
    if no_worker:
        print(f"\n⚠️ WORKERS WITHOUT 'Worker' CLASS (may be utilities):")
        for w in no_worker[:10]:
            print(f"   • {w['name']:<40} {w['size_kb']:>6} KB")
    
    # Scan coworker skills
    print("\n" + "=" * 80)
    print("📁 COWORKER SKILLS")
    print("-" * 80)
    
    skills = scan_skills(SKILLS_DIR)
    if skills:
        print(f"\n📊 Skills found: {len(skills)}")
        total_skill_size = sum(s["size"] for s in skills)
        print(f"   Total size: {total_skill_size / 1024:.1f} KB")
        
        print(f"\n   Skills:")
        for s in skills:
            print(f"   • {s['name']:<35} {s['size_kb']:>6} KB  {s['lines']:>4} lines")
    else:
        print("\nNo skills found in coworker/skills directory")
    
    # Detailed output for specific workers
    print("\n" + "=" * 80)
    print("🔍 DETAILED SCAN OF CRITICAL WORKERS")
    print("-" * 80)
    
    critical = ["sandbox_worker.py", "app_builder_worker.py", "rezstack_worker.py", "code_execution_worker.py"]
    for crit in critical:
        found = False
        for w in workers:
            if w["name"] == crit:
                print(f"\n📄 {crit}:")
                print(f"   Size: {w['size_kb']} KB ({w['size']} bytes)")
                print(f"   Lines: {w['lines']}")
                print(f"   Functions: {w['functions']}, Classes: {w['classes']}, Methods: {w['methods']}")
                print(f"   Has Worker class: {w['has_worker']}")
                print(f"   Imports: {w['imports'][:3] if w['imports'] else 'None'}")
                found = True
                break
        if not found:
            print(f"\n⚠️ {crit} not found")
    
    print("\n" + "=" * 80)
    print("🐝 SCAN COMPLETE")
    print("=" * 80)
    
    return workers

if __name__ == "__main__":
    workers = main()