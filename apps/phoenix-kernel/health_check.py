#!/usr/bin/env python3
"""Quick health check for all workers"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path.cwd()))

async def check_all():
    print("=" * 60)
    print("🦎 PHOENIX WORKER HEALTH CHECK")
    print("=" * 60)

    try:
        from workers import WORKER_REGISTRY
        
        for name, cls in WORKER_REGISTRY.items():
            try:
                w = cls()
                await w.initialize()
                health = await w.health_check()
                status = health.get('status', 'unknown')
                executions = health.get('executions', 0)
                errors = health.get('errors', 0)
                
                # Get worker-specific info
                info = ""
                if name == "rezcoder":
                    info = f", analyzers={len(w._engine.analyzers)}" if hasattr(w, '_engine') and w._engine else ""
                elif name == "sovereign_mcp_server":
                    info = f", tools={len(w.tools)}"
                elif name == "sandbox_worker":
                    info = f", blocked_patterns={len(w._scan_for_violations(''))}" if hasattr(w, '_scan_for_violations') else ""
                elif name == "memory":
                    info = f", entries={health.get('total_entries', 0)}"
                
                print(f"  ✅ {name:25} status: {status:12} (exec: {executions}, err: {errors}){info}")
            except Exception as e:
                print(f"  ❌ {name:25} failed: {e}")

        print("=" * 60)
        
        # Print MCP tools if available
        mcp = WORKER_REGISTRY.get("sovereign_mcp_server")
        if mcp:
            try:
                w = mcp()
                await w.initialize()
                tools = await w.execute("list_tools")
                if tools.get("success"):
                    print(f"\n📋 MCP Tools Available ({tools.get('tool_count', 0)}):")
                    for tool_name in list(tools.get('tools', {}).keys())[:7]:
                        print(f"  • {tool_name}")
            except Exception:
                pass
                
    except ImportError as e:
        print(f"❌ Cannot import workers: {e}")
        print("=" * 60)

if __name__ == "__main__":
    asyncio.run(check_all())
