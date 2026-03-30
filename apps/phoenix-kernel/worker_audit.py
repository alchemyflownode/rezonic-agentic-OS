#!/usr/bin/env python3
"""
worker_audit.py — Comprehensive Worker Integrity Audit
"""

import asyncio
import importlib
import sys
from pathlib import Path

sys.path.insert(0, str(Path.cwd()))

# Critical workers we MUST have
CRITICAL_WORKERS = [
    "base_worker",
    "rezcoder",
    "sovereign_mcp_server",
    "code_gen_worker",
    "sandbox_worker",
    "memory_worker",
]

# Expected methods per worker
EXPECTED_METHODS = {
    "base_worker": ["initialize", "execute", "health_check"],
    "rezcoder": ["initialize", "execute", "health_check"],
    "sovereign_mcp_server": ["initialize", "execute", "health_check"],
    "code_gen_worker": ["initialize", "execute", "health_check"],
    "sandbox_worker": ["initialize", "execute", "health_check"],
    "memory_worker": ["initialize", "execute", "health_check"],
}

# Map module names to class names
CLASS_MAP = {
    "base_worker": "Worker",
    "rezcoder": "RezCoderWorker",
    "sovereign_mcp_server": "SovereignMcpServer",
    "code_gen_worker": "CodeGenWorker",
    "sandbox_worker": "SandboxWorker",
    "memory_worker": "MemoryWorker",
}

async def audit_worker(module_name, class_name):
    """Audit a single worker."""
    results = {
        "name": module_name,
        "imports": False,
        "methods": [],
        "errors": [],
        "size": 0,
    }
    
    # Check file exists
    file_path = Path(f"workers/{module_name}.py")
    if file_path.exists():
        results["size"] = file_path.stat().st_size
    else:
        results["errors"].append(f"File not found: {module_name}.py")
        return results
    
    # Try to import
    try:
        module = importlib.import_module(f"workers.{module_name}")
        worker_class = getattr(module, class_name, None)
        if worker_class:
            results["imports"] = True
            # Try to instantiate
            try:
                worker = worker_class()
                # Check required methods
                expected = EXPECTED_METHODS.get(module_name, [])
                for method in expected:
                    if hasattr(worker, method):
                        results["methods"].append(f"{method} ✓")
                    else:
                        results["methods"].append(f"{method} ✗")
                        results["errors"].append(f"Missing method: {method}")
                
                # Check if we can call health_check
                try:
                    health = await worker.health_check()
                    results["methods"].append(f"health_check returned {health.get('status', 'unknown')}")
                except Exception as e:
                    results["errors"].append(f"health_check failed: {e}")
                    
            except Exception as e:
                results["errors"].append(f"Instantiation failed: {e}")
        else:
            results["errors"].append(f"Class {class_name} not found")
    except Exception as e:
        results["errors"].append(f"Import failed: {e}")
    
    return results

async def main():
    print("=" * 70)
    print("🦎 PHOENIX WORKER INTEGRITY AUDIT")
    print("=" * 70)
    
    results = {}
    for module, class_name in CLASS_MAP.items():
        result = await audit_worker(module, class_name)
        results[module] = result
    
    # Display results
    print("\n📊 AUDIT RESULTS\n")
    print(f"{'Worker':<25} {'Size':>8} {'Import':>8} {'Methods':<30} {'Status':<10}")
    print("-" * 85)
    
    for module, result in results.items():
        status = "✅ OK" if not result["errors"] else "❌ ISSUES"
        size_kb = result["size"] // 1024 if result["size"] else 0
        methods_str = result["methods"][0] if result["methods"] else "?"
        
        print(f"{module:<25} {size_kb:>7}KB  {'✓' if result['imports'] else '✗':>8}  {methods_str:<30} {status:<10}")
        
        if result["errors"]:
            for err in result["errors"][:3]:
                print(f"  ⚠️  {err}")
    
    # Summary
    total = len(results)
    ok = sum(1 for r in results.values() if not r["errors"])
    print("\n" + "=" * 70)
    print(f"  SUMMARY: {ok}/{total} workers passed integrity check")
    
    if ok < total:
        print(f"  ⚠️  {total - ok} workers need attention")
    else:
        print("  🎉 ALL WORKERS PASSED!")
    print("=" * 70)

if __name__ == "__main__":
    asyncio.run(main())
