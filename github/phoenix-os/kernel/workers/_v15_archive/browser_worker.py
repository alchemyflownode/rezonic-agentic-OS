import webbrowser
import asyncio
from typing import Dict, Any
import subprocess
import platform

class BrowserWorker:
    """Control your browser - open tabs, search, navigate"""
    
    def __init__(self):
        self.name = "browser"
        self.os = platform.system()
    
    async def execute(self, task: str, **kwargs) -> Dict[str, Any]:
        task_lower = task.lower()
        
        # Open URL
        if "open" in task_lower and ("url" in task_lower or "site" in task_lower or "website" in task_lower):
            url = kwargs.get("url", "")
            return await self._open_url(url)
        
        # Search
        elif "search" in task_lower:
            query = kwargs.get("query", task)
            return await self._search(query)
        
        # Open new tab (if browser already open)
        elif "new tab" in task_lower:
            return await self._new_tab()
        
        return {"error": f"Unknown browser operation: {task}", "success": False}
    
    async def _open_url(self, url: str) -> Dict[str, Any]:
        try:
            if not url.startswith("http"):
                url = "https://" + url
            webbrowser.open(url)
            return {"success": True, "message": f"Opened: {url}"}
        except Exception as e:
            return {"error": str(e), "success": False}
    
    async def _search(self, query: str) -> Dict[str, Any]:
        try:
            # Clean query
            query = query.replace("search", "").replace("google", "").strip()
            if not query:
                return {"error": "No search query", "success": False}
            
            url = f"https://www.google.com/search?q={query.replace(' ', '+')}"
            webbrowser.open(url)
            return {"success": True, "message": f"Searched: {query}", "url": url}
        except Exception as e:
            return {"error": str(e), "success": False}
    
    async def _new_tab(self) -> Dict[str, Any]:
        try:
            if self.os == "Windows":
                subprocess.Popen(["start", "chrome", "about:blank"], shell=True)
            elif self.os == "Darwin":
                subprocess.Popen(["open", "-a", "Google Chrome"])
            else:
                subprocess.Popen(["google-chrome", "about:blank"])
            return {"success": True, "message": "Opened new tab"}
        except Exception as e:
            return {"error": str(e), "success": False}