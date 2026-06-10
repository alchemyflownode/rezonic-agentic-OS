"""
Filesystem Worker for Phoenix Coworker

Handles all file system operations.
"""

import os
import shutil
from pathlib import Path
from typing import Dict, List, Optional, Any
from .base import BaseWorker


class FilesystemWorker(BaseWorker):
    """
    Filesystem worker for file operations.
    
    Provides safe, validated file system access.
    """
    
    def __init__(self, kernel: Any):
        super().__init__(kernel, "filesystem")
        
        # Allowed base directories (safety)
        self.allowed_bases = [
            Path.home(),
            Path.home() / "Downloads",
            Path.home() / "Documents",
            Path.home() / "Desktop",
            Path.home() / "Pictures",
            Path.home() / "Videos",
            Path.home() / "Music",
            Path.home() / ".phoenix",
        ]
    
    async def run(self):
        """Filesystem worker doesn't need a continuous loop"""
        while self._running:
            await asyncio.sleep(1)
    
    def _resolve_path(self, path: str) -> Path:
        """Resolve and validate a path"""
        # Expand user and environment variables
        expanded = os.path.expanduser(os.path.expandvars(path))
        resolved = Path(expanded).resolve()
        
        # Check if within allowed bases
        for base in self.allowed_bases:
            try:
                resolved.relative_to(base)
                return resolved
            except ValueError:
                continue
        
        # If not in allowed bases, check if it's under home
        try:
            resolved.relative_to(Path.home())
            return resolved
        except ValueError:
            pass
        
        # Default to home directory for safety
        print(f"⚠ Path '{path}' not in allowed bases, defaulting to home")
        return Path.home() / Path(path).name
    
    async def process(self, command: str, context: Dict = None) -> Dict:
        """Process a filesystem command"""
        context = context or {}
        
        words = command.lower().split()
        if not words:
            return {"success": False, "error": "Empty command"}
        
        action = words[0]
        
        if action == "list" or action == "ls":
            path = context.get("path", " ".join(words[1:]) if len(words) > 1 else ".")
            return await self.list_directory(path)
        
        elif action == "read" or action == "cat":
            path = context.get("path", words[1] if len(words) > 1 else None)
            if path:
                return await self.read_file(path)
            return {"success": False, "error": "No file specified"}
        
        elif action == "write":
            path = context.get("path")
            content = context.get("content", " ".join(words[1:]))
            if path:
                return await self.write_file(path, content)
            return {"success": False, "error": "No file specified"}
        
        elif action == "move" or action == "mv":
            src = context.get("source")
            dst = context.get("destination")
            if src and dst:
                return await self.move_file(src, dst)
            return {"success": False, "error": "Source or destination missing"}
        
        elif action == "copy" or action == "cp":
            src = context.get("source")
            dst = context.get("destination")
            if src and dst:
                return await self.copy_file(src, dst)
            return {"success": False, "error": "Source or destination missing"}
        
        elif action == "delete" or action == "rm":
            path = context.get("path", words[1] if len(words) > 1 else None)
            if path:
                return await self.delete_file(path)
            return {"success": False, "error": "No file specified"}
        
        elif action == "mkdir":
            path = context.get("path", words[1] if len(words) > 1 else None)
            if path:
                return await self.create_directory(path)
            return {"success": False, "error": "No directory specified"}
        
        elif action == "organize":
            path = context.get("path", "~/Downloads")
            return await self.organize_directory(path)
        
        return {"success": False, "error": f"Unknown filesystem action: {action}"}
    
    async def list_directory(self, path: str) -> Dict:
        """List directory contents"""
        try:
            resolved = self._resolve_path(path)
            
            if not resolved.exists():
                return {"success": False, "error": f"Path does not exist: {path}"}
            
            if not resolved.is_dir():
                return {"success": False, "error": f"Not a directory: {path}"}
            
            items = []
            for item in resolved.iterdir():
                items.append({
                    "name": item.name,
                    "type": "directory" if item.is_dir() else "file",
                    "size": item.stat().st_size if item.is_file() else None,
                    "modified": item.stat().st_mtime
                })
            
            return {
                "success": True,
                "path": str(resolved),
                "items": items
            }
        
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def read_file(self, path: str) -> Dict:
        """Read file contents"""
        try:
            resolved = self._resolve_path(path)
            
            if not resolved.exists():
                return {"success": False, "error": f"File does not exist: {path}"}
            
            if not resolved.is_file():
                return {"success": False, "error": f"Not a file: {path}"}
            
            # Size limit for safety (10MB)
            size = resolved.stat().st_size
            if size > 10 * 1024 * 1024:
                return {"success": False, "error": "File too large (>10MB)"}
            
            content = resolved.read_text()
            
            return {
                "success": True,
                "path": str(resolved),
                "size": size,
                "content": content
            }
        
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def write_file(self, path: str, content: str) -> Dict:
        """Write content to file"""
        try:
            resolved = self._resolve_path(path)
            
            # Create parent directories if needed
            resolved.parent.mkdir(parents=True, exist_ok=True)
            
            resolved.write_text(content)
            
            return {
                "success": True,
                "path": str(resolved),
                "size": len(content)
            }
        
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def move_file(self, source: str, destination: str) -> Dict:
        """Move a file"""
        try:
            src_path = self._resolve_path(source)
            dst_path = self._resolve_path(destination)
            
            if not src_path.exists():
                return {"success": False, "error": f"Source does not exist: {source}"}
            
            # Create parent directories if needed
            dst_path.parent.mkdir(parents=True, exist_ok=True)
            
            shutil.move(str(src_path), str(dst_path))
            
            return {
                "success": True,
                "source": str(src_path),
                "destination": str(dst_path)
            }
        
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def copy_file(self, source: str, destination: str) -> Dict:
        """Copy a file"""
        try:
            src_path = self._resolve_path(source)
            dst_path = self._resolve_path(destination)
            
            if not src_path.exists():
                return {"success": False, "error": f"Source does not exist: {source}"}
            
            # Create parent directories if needed
            dst_path.parent.mkdir(parents=True, exist_ok=True)
            
            if src_path.is_dir():
                shutil.copytree(str(src_path), str(dst_path))
            else:
                shutil.copy2(str(src_path), str(dst_path))
            
            return {
                "success": True,
                "source": str(src_path),
                "destination": str(dst_path)
            }
        
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def delete_file(self, path: str) -> Dict:
        """Delete a file or directory"""
        try:
            resolved = self._resolve_path(path)
            
            if not resolved.exists():
                return {"success": False, "error": f"Path does not exist: {path}"}
            
            if resolved.is_dir():
                shutil.rmtree(resolved)
            else:
                resolved.unlink()
            
            return {
                "success": True,
                "path": str(resolved)
            }
        
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def create_directory(self, path: str) -> Dict:
        """Create a directory"""
        try:
            resolved = self._resolve_path(path)
            resolved.mkdir(parents=True, exist_ok=True)
            
            return {
                "success": True,
                "path": str(resolved)
            }
        
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def organize_directory(self, path: str) -> Dict:
        """Organize files in a directory by type"""
        try:
            resolved = self._resolve_path(path)
            
            if not resolved.exists() or not resolved.is_dir():
                return {"success": False, "error": f"Invalid directory: {path}"}
            
            # Get brain worker for classification
            brain = self.kernel.get_worker("brain")
            
            # List files
            files = [f for f in resolved.iterdir() if f.is_file()]
            
            if not files:
                return {"success": True, "message": "No files to organize", "moved": 0}
            
            # Classify files
            if brain:
                categories = brain._classify_files([str(f) for f in files])
            else:
                # Simple fallback classification
                categories = {"other": [str(f) for f in files]}
            
            # Create category folders and move files
            moved = 0
            for category, file_list in categories.items():
                if not file_list:
                    continue
                
                category_dir = resolved / category.capitalize()
                category_dir.mkdir(exist_ok=True)
                
                for file_path in file_list:
                    src = Path(file_path)
                    if src.exists():
                        dst = category_dir / src.name
                        shutil.move(str(src), str(dst))
                        moved += 1
            
            return {
                "success": True,
                "message": f"Organized {moved} files",
                "moved": moved,
                "categories": list(categories.keys())
            }
        
        except Exception as e:
            return {"success": False, "error": str(e)}
