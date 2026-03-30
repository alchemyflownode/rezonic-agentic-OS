#!/usr/bin/env python3
"""
Auto-integrate RezCoder and MCP API endpoints into kernel.py
"""

import re
import shutil
from pathlib import Path

KERNEL_PATH = Path("kernel.py")

# API endpoints to add
REZCODER_ENDPOINTS = '''
        # ========== REZCODER API ==========
        @self.app.get("/api/v1/rezcoder/health")
        async def api_rezcoder_health():
            worker = self.workers.get("rezcoder", {}).get("instance")
            if not worker:
                return JSONResponse({"error": "RezCoder not available"}, status_code=503)
            await worker.initialize()
            return await worker.health_check()

        @self.app.get("/api/v1/rezcoder/review")
        async def api_rezcoder_review(filepath: str, recursive: bool = False):
            worker = self.workers.get("rezcoder", {}).get("instance")
            if not worker:
                return JSONResponse({"error": "RezCoder not available"}, status_code=503)
            await worker.initialize()
            return await worker.execute("review", file_path=filepath, recursive=recursive)

        @self.app.post("/api/v1/rezcoder/fix")
        async def api_rezcoder_fix(filepath: str, confidence: float = 0.8, backup: bool = True):
            worker = self.workers.get("rezcoder", {}).get("instance")
            if not worker:
                return JSONResponse({"error": "RezCoder not available"}, status_code=503)
            await worker.initialize()
            return await worker.execute("fix", file_path=filepath, confidence=confidence, backup=backup)

        @self.app.get("/api/v1/rezcoder/report")
        async def api_rezcoder_report(filepath: str):
            worker = self.workers.get("rezcoder", {}).get("instance")
            if not worker:
                return JSONResponse({"error": "RezCoder not available"}, status_code=503)
            await worker.initialize()
            return await worker.execute("report", file_path=filepath)

        # ========== MCP API ==========
        @self.app.get("/api/v1/mcp/health")
        async def api_mcp_health():
            worker = self.workers.get("sovereign_mcp_server", {}).get("instance")
            if not worker:
                return JSONResponse({"error": "MCP server not available"}, status_code=503)
            await worker.initialize()
            return await worker.health_check()

        @self.app.get("/api/v1/mcp/tools")
        async def api_mcp_tools():
            worker = self.workers.get("sovereign_mcp_server", {}).get("instance")
            if not worker:
                return JSONResponse({"error": "MCP server not available"}, status_code=503)
            await worker.initialize()
            return await worker.execute("list_tools")

        @self.app.get("/api/v1/mcp/review")
        async def api_mcp_review(filepath: str, recursive: bool = False):
            worker = self.workers.get("sovereign_mcp_server", {}).get("instance")
            if not worker:
                return JSONResponse({"error": "MCP server not available"}, status_code=503)
            await worker.initialize()
            return await worker.execute(f"review_code {filepath}" + (" --recursive" if recursive else ""))

        @self.app.post("/api/v1/mcp/fix")
        async def api_mcp_fix(filepath: str, confidence: float = 0.8, backup: bool = True):
            worker = self.workers.get("sovereign_mcp_server", {}).get("instance")
            if not worker:
                return JSONResponse({"error": "MCP server not available"}, status_code=503)
            await worker.initialize()
            return await worker.execute(f"fix_code {filepath} --confidence {confidence}" + (" --backup" if backup else ""))

        @self.app.get("/api/v1/mcp/generate")
        async def api_mcp_generate(intent: str, language: str = "python"):
            worker = self.workers.get("sovereign_mcp_server", {}).get("instance")
            if not worker:
                return JSONResponse({"error": "MCP server not available"}, status_code=503)
            await worker.initialize()
            return await worker.execute(f"generate_code {intent} --language {language}")
'''

def add_endpoints():
    """Add missing API endpoints to kernel.py"""
    
    if not KERNEL_PATH.exists():
        print(f"❌ {KERNEL_PATH} not found")
        return False
    
    content = KERNEL_PATH.read_text(encoding="utf-8")
    
    # Check if endpoints already exist
    if "/api/v1/rezcoder/health" in content:
        print("✅ RezCoder endpoints already present")
    else:
        # Find the end of _setup_routes method
        # Look for the last route or the method end
        pattern = r'(def _setup_routes\(self\):.*?)(?=\n    async def |\n    def |\Z)'
        match = re.search(pattern, content, re.DOTALL)
        
        if match:
            # Insert endpoints before the end of the method
            pos = match.end()
            content = content[:pos] + REZCODER_ENDPOINTS + content[pos:]
            print("✅ Added RezCoder and MCP endpoints")
        else:
            print("❌ Could not find _setup_routes method")
            return False
    
    # Create backup
    backup_path = KERNEL_PATH.with_suffix(".py.before_api")
    shutil.copy2(KERNEL_PATH, backup_path)
    print(f"💾 Backup saved to {backup_path}")
    
    # Write updated kernel
    KERNEL_PATH.write_text(content, encoding="utf-8")
    print("✅ Kernel updated! Restart to apply changes.")
    return True

if __name__ == "__main__":
    add_endpoints()
