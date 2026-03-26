# src/mcp/sovereign_mcp_server.py
import sys
import json
import subprocess
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("SovereignStack")

# TOOL 1: SYSTEM VITALS
@mcp.tool()
def get_system_vitals() -> dict:
    """Get live CPU, RAM, GPU stats from the Sovereign Stack."""
    result = subprocess.run(
        ["python", "src/workers/system_agent.py", "snapshot"],
        capture_output=True, text=True
    )
    return json.loads(result.stdout)

# TOOL 2: SELF_REPAIR
@mcp.tool()
def run_self_repair() -> dict:
    """Scan and fix code issues in the Sovereign Stack."""
    result = subprocess.run(
        ["python", "src/workers/mutation_worker.py", "."],
        capture_output=True, text=True
    )
    return json.loads(result.stdout)

# TOOL 3: DEEP RESEARCH
@mcp.tool()
def deep_research(query: str) -> dict:
    """Perform a deep web search and synthesize results."""
    result = subprocess.run(
        ["python", "src/workers/search_harvester.py", query],
        capture_output=True, text=True
    )
    return json.loads(result.stdout)

if __name__ == "__main__":
    print("🌐 Sovereign MCP Server Running...")
    mcp.run()
