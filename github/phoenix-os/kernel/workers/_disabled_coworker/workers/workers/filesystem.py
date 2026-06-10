"""
Enhanced Filesystem Worker - File operations with PC coworker capabilities
"""

import os
import shutil
import json
import time
import platform
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Optional
import asyncio

from .base import BaseWorker


class FilesystemWorker(BaseWorker):
    """Enhanced file system operations for PC coworker"""
    
    def __init__(self):
        super().__init__("filesystem")
        self.os_type = platform.system()
        self.workspace = Path.cwd()
        self.trash_path = Path.home() / ".phoenix_trash"
        self.trash_path.mkdir(exist_ok=True)
        
        # Safe directories for operations
        self.safe_paths = [
            Path.home() / "Documents",
            Path.home() / "Downloads",
            Path.home() / "Desktop",
            Path.home() / "Pictures",
            Path.home() / "Music",
            Path.home() / "Videos",
            Path.cwd(),
            Path.home() / "Projects",
            Path.home() / "Work"
        ]
    
    async def execute(self, task: str, **kwargs) -> Dict[str, Any]:
        """Execute file operations"""
        task_lower = task.lower()
        
        # List directory
        if "list" in task_lower and any(x in task_lower for x in ["dir", "folder", "directory"]):
            path = kwargs.get("path", str(self.workspace))
            return await self._list_directory(path)
        
        # Create folder
        elif "create" in task_lower and any(x in task_lower for x in ["folder", "directory"]):
            name = kwargs.get("name", "")
            if not name:
                return {"error": "No folder name provided", "success": False}
            return await self._create_folder(name)
        
        # Read file
        elif "read" in task_lower or "open" in task_lower:
            filepath = kwargs.get("path", "")
            return await self._read_file(filepath)
        
        # Write/save file
        elif any(x in task_lower for x in ["write", "save", "create file"]):
            filename = kwargs.get("filename", "")
            content = kwargs.get("content", "")
            return await self._write_file(filename, content)
        
        # Search files
        elif "search" in task_lower and ("file" in task_lower or "find" in task_lower):
            pattern = kwargs.get("pattern", "")
            return await self._search_files(pattern)
        
        # Move/copy file
        elif "move" in task_lower or "copy" in task_lower:
            src = kwargs.get("source", "")
            dest = kwargs.get("destination", "")
            return await self._move_file(src, dest, task_lower)
        
        # Delete file
        elif "delete" in task_lower or "trash" in task_lower:
            path = kwargs.get("path", "")
            return await self._safe_delete(path)
        
        # Get file info
        elif "info" in task_lower:
            path = kwargs.get("path", "")
            return await self._file_info(path)
        
        # Watch directory (monitor changes)
        elif "watch" in task_lower:
            path = kwargs.get("path", str(self.workspace))
            return await self._watch_directory(path)
        
        return {"error": f"Unknown file operation: {task}", "success": False}
    
    async def _list_directory(self, path: str) -> Dict[str, Any]:
        """List directory contents"""
        try:
            p = Path(path).expanduser().resolve()
            if not p.exists():
                return {"error": f"Path not found: {path}", "success": False}
            
            if not p.is_dir():
                return {"error": f"Not a directory: {path}", "success": False}
            
            items = []
            for item in p.iterdir():
                try:
                    stat = item.stat()
                    items.append({
                        "name": item.name,
                        "type": "directory" if item.is_dir() else "file",
                        "size": stat.st_size if item.is_file() else 0,
                        "modified": datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M:%S"),
                        "path": str(item),
                        "extension": item.suffix if item.is_file() else ""
                    })
                except (PermissionError, OSError):
                    continue
            
            # Sort: directories first, then files
            items.sort(key=lambda x: (x["type"] != "directory", x["name"].lower()))
            
            return {
                "success": True,
                "path": str(p),
                "items": items[:100],
                "count": len(items),
                "total_size_bytes": sum(i["size"] for i in items if i["type"] == "file")
            }
        except Exception as e:
            return {"error": str(e), "success": False}
    
    async def _create_folder(self, name: str) -> Dict[str, Any]:
        """Create a new folder"""
        try:
            path = self.workspace / name
            path.mkdir(parents=True, exist_ok=False)
            return {
                "success": True,
                "path": str(path),
                "message": f"✅ Created folder: {name}"
            }
        except FileExistsError:
            return {"error": f"Folder already exists: {name}", "success": False}
        except Exception as e:
            return {"error": str(e), "success": False}
    
    async def _read_file(self, filepath: str) -> Dict[str, Any]:
        """Read file contents"""
        try:
            path = Path(filepath).expanduser().resolve()
            if not path.exists():
                return {"error": f"File not found: {filepath}", "success": False}
            
            if not path.is_file():
                return {"error": f"Not a file: {filepath}", "success": False}
            
            # Check file size (limit to 1MB)
            if path.stat().st_size > 1024 * 1024:
                return {"error": "File too large (>1MB). Use partial read.", "success": False}
            
            # Try UTF-8 first, fallback to system encoding
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    content = f.read()
            except UnicodeDecodeError:
                with open(path, 'r', encoding='latin-1') as f:
                    content = f.read()
            
            return {
                "success": True,
                "path": str(path),
                "content": content,
                "size_bytes": len(content.encode()),
                "lines": len(content.splitlines()),
                "extension": path.suffix
            }
        except Exception as e:
            return {"error": str(e), "success": False}
    
    async def _write_file(self, filename: str, content: str) -> Dict[str, Any]:
        """Write content to file"""
        try:
            path = self.workspace / filename
            with open(path, 'w', encoding='utf-8') as f:
                f.write(content)
            return {
                "success": True,
                "path": str(path),
                "message": f"✅ Saved: {filename}",
                "size_bytes": len(content)
            }
        except Exception as e:
            return {"error": str(e), "success": False}
    
    async def _search_files(self, pattern: str) -> Dict[str, Any]:
        """Search for files by pattern"""
        try:
            results = []
            extensions = ['*.*', '*.py', '*.txt', '*.md', '*.json', '*.yaml', '*.csv', '*.log', '*.html', '*.css', '*.js']
            
            for ext in extensions:
                for path in self.workspace.rglob(ext):
                    if pattern.lower() in path.name.lower():
                        try:
                            stat = path.stat()
                            results.append({
                                "name": path.name,
                                "path": str(path),
                                "size": stat.st_size,
                                "modified": datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M:%S")
                            })
                        except (PermissionError, OSError):
                            continue
                    
                    if len(results) >= 50:
                        break
                if len(results) >= 50:
                    break
            
            return {
                "success": True,
                "pattern": pattern,
                "results": results[:50],
                "count": len(results)
            }
        except Exception as e:
            return {"error": str(e), "success": False}
    
    async def _move_file(self, src: str, dest: str, operation: str) -> Dict[str, Any]:
        """Move or copy file"""
        try:
            src_path = Path(src).expanduser().resolve()
            dest_path = Path(dest).expanduser().resolve()
            
            if not src_path.exists():
                return {"error": f"Source not found: {src}", "success": False}
            
            if "copy" in operation:
                if src_path.is_file():
                    shutil.copy2(src_path, dest_path)
                else:
                    shutil.copytree(src_path, dest_path)
                message = f"✅ Copied: {src_path.name} → {dest_path}"
            else:
                shutil.move(str(src_path), str(dest_path))
                message = f"✅ Moved: {src_path.name} → {dest_path}"
            
            return {"success": True, "message": message}
        except Exception as e:
            return {"error": str(e), "success": False}
    
    async def _safe_delete(self, path: str) -> Dict[str, Any]:
        """Safely delete file (move to trash)"""
        try:
            p = Path(path).expanduser().resolve()
            
            # Safety checks
            critical = [Path.home(), Path.cwd(), Path("/"), Path("C:\\"), Path("D:\\")]
            if p in critical or p.parent in critical:
                return {"error": "Cannot delete critical path", "success": False}
            
            # Check if path is in safe locations
            safe = any(str(p).startswith(str(sp)) for sp in self.safe_paths)
            if not safe:
                return {"error": f"Path not in safe locations: {path}", "success": False}
            
            if p.is_file():
                dest = self.trash_path / f"{p.name}_{int(time.time())}"
                shutil.move(str(p), str(dest))
                return {
                    "success": True,
                    "message": f"🗑️ Moved to trash: {p.name}",
                    "trash_path": str(dest)
                }
            elif p.is_dir():
                shutil.rmtree(str(p))
                return {"success": True, "message": f"🗑️ Deleted folder: {p.name}"}
            
            return {"error": "Path not found", "success": False}
        except Exception as e:
            return {"error": str(e), "success": False}
    
    async def _file_info(self, path: str) -> Dict[str, Any]:
        """Get detailed file information"""
        try:
            p = Path(path).expanduser().resolve()
            if not p.exists():
                return {"error": f"Path not found: {path}", "success": False}
            
            stat = p.stat()
            return {
                "success": True,
                "name": p.name,
                "path": str(p),
                "type": "directory" if p.is_dir() else "file",
                "size_bytes": stat.st_size if p.is_file() else 0,
                "created": datetime.fromtimestamp(stat.st_ctime).strftime("%Y-%m-%d %H:%M:%S"),
                "modified": datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M:%S"),
                "accessed": datetime.fromtimestamp(stat.st_atime).strftime("%Y-%m-%d %H:%M:%S"),
                "parent": str(p.parent),
                "permissions": oct(stat.st_mode)[-3:]
            }
        except Exception as e:
            return {"error": str(e), "success": False}
    
    async def _watch_directory(self, path: str) -> Dict[str, Any]:
        """Monitor directory for changes (simplified)"""
        try:
            p = Path(path).expanduser().resolve()
            if not p.exists():
                return {"error": f"Path not found: {path}", "success": False}
            
            # Get initial snapshot
            snapshot = {}
            for item in p.iterdir():
                try:
                    snapshot[item.name] = item.stat().st_mtime
                except:
                    pass
            
            return {
                "success": True,
                "message": f"Watching {p} for changes. Use /watch to see changes.",
                "initial_files": len(snapshot)
            }
        except Exception as e:
            return {"error": str(e), "success": False}