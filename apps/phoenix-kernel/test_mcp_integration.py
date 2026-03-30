#!/usr/bin/env python3
"""
test_mcp_integration.py — Validate MCP + RezCoder Integration
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path.cwd()))

PASS = "✅"
FAIL = "❌"
SKIP = "⏭️"


async def run_tests(verbose: bool = False) -> dict:
    """Run all integration tests."""
    print("🧪 MCP + REZCODER INTEGRATION TESTS")
    print("=" * 55)

    results = {}
    details = {}

    # Test 1: Import code_worker
    test = "import_code_worker"
    try:
        import code_worker
        results[test] = PASS
        details[test] = f"ReviewEngine has {len(code_worker.ReviewEngine().analyzers)} analyzers"
    except Exception as e:
        results[test] = FAIL
        details[test] = str(e)

    # Test 2: Import RezCoderWorker
    test = "import_rezcoder"
    try:
        from workers.rezcoder import RezCoderWorker
        w = RezCoderWorker()
        results[test] = PASS
        details[test] = f"Worker: {w.name}"
    except Exception as e:
        results[test] = FAIL
        details[test] = str(e)

    # Test 3: Import MCP Server
    test = "import_mcp_server"
    try:
        from workers.sovereign_mcp_server import SovereignMcpServer
        w = SovereignMcpServer()
        results[test] = PASS
        details[test] = f"{len(w.tools)} tools"
    except Exception as e:
        results[test] = FAIL
        details[test] = str(e)

    # Test 4: Import Code Gen
    test = "import_code_gen"
    try:
        from workers.code_gen_worker import CodeGenWorker
        results[test] = PASS
        details[test] = "OK"
    except Exception as e:
        results[test] = FAIL
        details[test] = str(e)

    # Test 5: Import Sandbox
    test = "import_sandbox"
    try:
        from workers.sandbox_worker import SandboxWorker
        results[test] = PASS
        details[test] = "OK"
    except Exception as e:
        results[test] = FAIL
        details[test] = str(e)

    # Test 6: Import Memory
    test = "import_memory"
    try:
        from workers.memory_worker import MemoryWorker
        results[test] = PASS
        details[test] = "OK"
    except Exception as e:
        results[test] = FAIL
        details[test] = str(e)

    # Test 7: Initialize MCP Server
    test = "mcp_initialize"
    try:
        from workers.sovereign_mcp_server import SovereignMcpServer
        server = SovereignMcpServer()
        await server.initialize()
        results[test] = PASS
        details[test] = "Initialized"
    except Exception as e:
        results[test] = FAIL
        details[test] = str(e)

    # Test 8: MCP list_tools
    test = "mcp_list_tools"
    try:
        result = await server.execute("list_tools")
        if result.get("success"):
            results[test] = PASS
            details[test] = f"{result.get('tool_count', 0)} tools"
        else:
            results[test] = FAIL
            details[test] = result.get("error", "unknown")
    except Exception as e:
        results[test] = FAIL
        details[test] = str(e)

    # Test 9: MCP get_health
    test = "mcp_get_health"
    try:
        result = await server.execute("get_health")
        if result.get("success"):
            results[test] = PASS
            details[test] = f"Status: {result.get('status')}"
        else:
            results[test] = FAIL
            details[test] = result.get("error", "unknown")
    except Exception as e:
        results[test] = FAIL
        details[test] = str(e)

    # Test 10: MCP generate_code
    test = "mcp_generate_code"
    try:
        result = await server.execute("generate_code async web scraper")
        if result.get("success") and result.get("code"):
            results[test] = PASS
            details[test] = f"Generated {len(result['code'])} chars"
        else:
            results[test] = FAIL
            details[test] = result.get("error", "no code")
    except Exception as e:
        results[test] = FAIL
        details[test] = str(e)

    # Test 11: MCP unknown tool
    test = "mcp_unknown_tool"
    try:
        result = await server.execute("nonexistent_tool")
        if not result.get("success") and result.get("error_code") == 404:
            results[test] = PASS
            details[test] = "Correctly rejected"
        else:
            results[test] = FAIL
            details[test] = "Wrong response"
    except Exception as e:
        results[test] = FAIL
        details[test] = str(e)

    # Print results
    print(f"\n{'─' * 55}")
    print("📋 TEST RESULTS")
    print(f"{'─' * 55}")

    for test, status in results.items():
        detail = details.get(test, "")
        name = test.replace("_", " ").title()
        print(f"  {status} {name}")
        if verbose and detail:
            print(f"     → {detail}")

    passed = sum(1 for v in results.values() if v == PASS)
    failed = sum(1 for v in results.values() if v == FAIL)
    total = len(results)

    print(f"\n{'─' * 55}")
    print(f"  🏁 {passed}/{total} passed, {failed} failed")
    print(f"{'─' * 55}")

    return results


async def main():
    verbose = "--verbose" in sys.argv or "-v" in sys.argv
    results = await run_tests(verbose=verbose)
    failed = sum(1 for v in results.values() if v == FAIL)
    return 1 if failed > 0 else 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
