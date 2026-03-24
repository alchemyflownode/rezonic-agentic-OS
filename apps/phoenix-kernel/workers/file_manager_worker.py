import os
import shutil
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List
import asyncio

class FileManagerWorker:
    """Enhanced file system operations for your PC"""
    
    def __init__(self):
        self.name = "file_manager"
        self.workspace = Path.cwd()
        self.safe_paths = [Path.home() / "Documents", Path.home() / "Downloads", Path.cwd()]
    
    async def execute(self, task: str, **kwargs) -> Dict[str, Any]:
        """Execute file operations"""
        task_lower = task.lower()
        
        # List directory
        if "list" in task_lower and ("dir" in task_lower or "folder" in task_lower):
            path = kwargs.get("path", str(self.workspace))
            return await self._list_directory(path)
        
        # Create folder
        elif "create" in task_lower and ("folder" in task_lower or "directory" in task_lower):
            name = kwargs.get("name", "")
            if not name:
                return {"error": "No folder name provided", "success": False}
            return await self._create_folder(name)
        
        # Read file
        elif "read" in task_lower or "open" in task_lower:
            filepath = kwargs.get("path", "")
            return await self._read_file(filepath)
        
        # Write/save file
        elif "write" in task_lower or "save" in task_lower or "create file" in task_lower:
            filename = kwargs.get("filename", "")
            content = kwargs.get("content", "")
            return await self._write_file(filename, content)
        
        # Search files
        elif "search" in task_lower and ("file" in task_lower or "find" in task_lower):
            pattern = kwargs.get("pattern", "")
            return await self._search_files(pattern)
        
        # Delete file (with safety)
        elif "delete" in task_lower:
            path = kwargs.get("path", "")
            return await self._safe_delete(path)
        
        return {"error": f"Unknown file operation: {task}", "success": False}
    
    async def _list_directory(self, path: str) -> Dict[str, Any]:
        try:
            p = Path(path).expanduser()
            if not p.exists():
                return {"error": f"Path not found: {path}", "success": False}
            
            items = []
            for item in p.iterdir():
                items.append({
                    "name": item.name,
                    "type": "directory" if item.is_dir() else "file",
                    "size": item.stat().st_size if item.is_file() else 0,
                    "modified": datetime.fromtimestamp(item.stat().st_mtime).isoformat()
                })
            
            return {
                "success": True,
                "path": str(p),
                "items": sorted(items, key=lambda x: (x["type"], x["name"])),
                "count": len(items)
            }
        except Exception as e:
            return {"error": str(e), "success": False}
    
    async def _create_folder(self, name: str) -> Dict[str, Any]:
        try:
            path = self.workspace / name
            path.mkdir(parents=True, exist_ok=True)
            return {"success": True, "path": str(path), "message": f"Created folder: {name}"}
        except Exception as e:
            return {"error": str(e), "success": False}
    
    async def _read_file(self, filepath: str) -> Dict[str, Any]:
        try:
            path = Path(filepath).expanduser()
            if not path.exists():
                return {"error": f"File not found: {filepath}", "success": False}
            
            with open(path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            return {
                "success": True,
                "path": str(path),
                "content": content,
                "size": len(content),
                "lines": len(content.splitlines())
            }
        except Exception as e:
            return {"error": str(e), "success": False}
    
    async def _write_file(self, filename: str, content: str) -> Dict[str, Any]:
        try:
            path = self.workspace / filename
            with open(path, 'w', encoding='utf-8') as f:
                f.write(content)
            return {"success": True, "path": str(path), "message": f"Saved: {filename}"}
        except Exception as e:
            return {"error": str(e), "success": False}
    
    async def _search_files(self, pattern: str) -> Dict[str, Any]:
        try:
            results = []
            for ext in ['*.py', '*.txt', '*.md', '*.json', '*.csv']:
                for path in self.workspace.rglob(ext):
                    if pattern.lower() in path.name.lower():
                        results.append(str(path))
            
            return {
                "success": True,
                "pattern": pattern,
                "results": results[:20],
                "count": len(results)
            }
        except Exception as e:
            return {"error": str(e), "success": False}
    
    async def _safe_delete(self, path: str) -> Dict[str, Any]:
        try:
            p = Path(path).expanduser()
            
            # Safety: Don't delete system paths
            forbidden = [Path.home(), Path.cwd(), Path("/"), Path("C:\\")]
            if p in forbidden:
                return {"error": "Cannot delete system path", "success": False}
            
            if p.is_file():
                # Move to trash instead of deleting
                trash = Path.home() / ".trash"
                trash.mkdir(exist_ok=True)
                dest = trash / f"{p.name}_{int(time.time())}"
                shutil.move(str(p), str(dest))
                return {"success": True, "message": f"Moved to trash: {p.name}"}
            elif p.is_dir():
                shutil.rmtree(str(p))
                return {"success": True, "message": f"Deleted folder: {p.name}"}
            
            return {"error": "Path not found", "success": False}
        except Exception as e:
            return {"error": str(e), "success": False}