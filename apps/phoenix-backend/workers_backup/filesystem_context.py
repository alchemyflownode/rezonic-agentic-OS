from .base_worker import BaseWorker
﻿import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
import os
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

class FilesystemContextWorker(BaseWorker):
    def __init__(self, base_path: str = "./hive_vfs", hive_bus=None):
        """Initialize the Virtual Filesystem for Agent Context"""
        super().__init__('filesystemcontext', hive_bus)
        # Resolve the absolute path to prevent traversal attacks
        self.base_path = Path(base_path).resolve()
        self.cwd = self.base_path
        
        # Create standard OS context directories if they don't exist
        for d in ["memory", "knowledge", "tools", "projects"]:
            (self.base_path / d).mkdir(parents=True, exist_ok=True)
            
    def _resolve_path(self, path: str) -> Path:
        """Safely resolve a path, preventing escapes from the VFS root."""
        if path.startswith("/"):
            # Treat '/' as the VFS root
            target = self.base_path / path.lstrip("/")
        else:
            target = self.cwd / path
            
        target = target.resolve()
        
        # Security Boundary: Prevent agent from accessing real PC files through this worker
        if not str(target).startswith(str(self.base_path)):
            raise PermissionError("VFS Security Exception: Access denied outside virtual context.")
            
        return target

    def pwd(self) -> str:
        """Get current working directory relative to VFS root."""
        try:
            rel_path = self.cwd.relative_to(self.base_path)
            return "/" + str(rel_path).replace("\\", "/") if str(rel_path) != "." else "/"
        except ValueError:
            return "/"

    def cd(self, path: str) -> str:
        """Change current context directory."""
        try:
            target = self._resolve_path(path)
            if target.is_dir():
                self.cwd = target
                return f"Context shifted. Current path: {self.pwd()}"
            return f"Error: Context path '{path}' not found."
        except Exception as e:
            return f"Error: {str(e)}"

    def ls(self, path: str = ".") -> str:
        """List contents of the current context directory."""
        try:
            target = self._resolve_path(path)
            if not target.is_dir():
                return f"Error: '{path}' is not a directory."
            
            items = []
            for item in target.iterdir():
                prefix = "[DIR] " if item.is_dir() else "[FILE]"
                items.append(f"{prefix} {item.name}")
            
            if not items:
                return f"Context directory '{self.pwd()}' is empty."
            return f"Contents of {self.pwd()}:\n" + "\n".join(sorted(items))
        except Exception as e:
            return f"Error: {str(e)}"

    def cat(self, path: str) -> str:
        """Read context from a file."""
        try:
            target = self._resolve_path(path)
            if not target.is_file():
                return f"Error: Knowledge file '{path}' not found."
            
            with open(target, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Optional: Add chunking here later if files are too massive
            return f"--- Content of {target.name} ---\n{content}\n--- End ---"
        except Exception as e:
            return f"Error: {str(e)}"
            
    def write_context(self, path: str, content: str) -> str:
        """Allow the AI to write notes/context back into the VFS."""
        try:
            target = self._resolve_path(path)
            with open(target, 'w', encoding='utf-8') as f:
                f.write(content)
            return f"Successfully wrote context to {path}"
        except Exception as e:
            return f"Error writing context: {str(e)}"

    async def process(self, task: str, memory_bus=None):
        """Process task – auto-generated stub"""
        return {"content": f"Processed: {task[:50]}", "worker": self.name}
    
    async def health_check(self):
        """Return worker health status"""
        return {"worker": self.name, "status": "healthy", "timestamp": __import__('time').time()}

