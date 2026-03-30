# add_mastery_api.py
import re
from pathlib import Path

kernel_path = Path("kernel.py")
content = kernel_path.read_text(encoding="utf-8")

# Add mastery API endpoint to _setup_routes
mastery_api = '''
        # ========== MASTERY API ==========
        @self.app.get("/api/v1/mastery/stats")
        async def api_mastery_stats():
            worker = self.workers.get("mastery", {}).get("instance")
            if not worker:
                return JSONResponse({"error": "Mastery not available"}, status_code=503)
            await worker.initialize()
            stats = await worker.get_stats()
            return stats
        
        @self.app.post("/api/v1/mastery/add_xp")
        async def api_mastery_add_xp(action: str, amount: int, description: str = ""):
            worker = self.workers.get("mastery", {}).get("instance")
            if not worker:
                return JSONResponse({"error": "Mastery not available"}, status_code=503)
            await worker.initialize()
            result = await worker.add_xp(action, amount, description, source="api")
            return result
'''

# Find _setup_routes and add mastery API
routes_pattern = r'(def _setup_routes\(self\):.*?)(?=\n    async def |\n    def |\Z)'
match = re.search(routes_pattern, content, re.DOTALL)

if match:
    pos = match.end()
    content = content[:pos] + mastery_api + content[pos:]
    print("✅ Added mastery API endpoints")
    
    backup = kernel_path.with_suffix(".py.before_mastery_api")
    kernel_path.rename(backup)
    kernel_path.write_text(content, encoding="utf-8")
    print(f"💾 Backup: {backup}")
    print("✅ Restart kernel")
