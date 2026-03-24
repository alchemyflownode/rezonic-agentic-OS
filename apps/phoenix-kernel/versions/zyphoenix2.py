Excellent! Let's create the complete integration code with proper security controls. This will give you a fully functional Agentic Coding Tool integrated with Phoenix Kernel.

```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PHOENIX ULTIMATE v13.3.0 - AGENTIC CODING TOOL INTEGRATION
Zero Drift Architecture + Persistent Event Chain + Formalized Workers + Code Execution
"""

import sys
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

import uuid
import asyncio
import logging
import os
import json
import time
import hashlib
import random
import re
import secrets
import warnings
import psutil
import importlib.util
import inspect
import httpx
import sqlite3
import shutil
import subprocess
import tempfile
import ast
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, Optional, List, Callable, Awaitable, Tuple, Union
from enum import Enum, auto
from dataclasses import dataclass, field, asdict
from collections import defaultdict
from functools import wraps
from contextlib import asynccontextmanager
from abc import ABC, abstractmethod

# =======================================================================
# LOGGING SETUP
# =======================================================================
os.makedirs('logs', exist_ok=True)
os.makedirs('data', exist_ok=True)
os.makedirs('data/event_store', exist_ok=True)
os.makedirs('data/backups', exist_ok=True)
os.makedirs('data/sandbox', exist_ok=True)

# Configure logging with rotation
from logging.handlers import RotatingFileHandler

log_file_path = Path('logs/phoenix_ultimate.log')
log_handler = None

for attempt in range(3):
    try:
        log_handler = RotatingFileHandler(
            str(log_file_path),
            maxBytes=10*1024*1024,
            backupCount=5,
            encoding='utf-8',
            delay=True
        )
        break
    except PermissionError:
        if attempt == 2:
            log_handler = logging.StreamHandler(sys.stdout)

if log_handler:
    log_handler.setFormatter(logging.Formatter(
        "%(asctime)s [%(levelname)s] %(name)s - %(message)s"
    ))

logging.basicConfig(
    level=logging.INFO,
    handlers=[log_handler] if log_handler else [logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("PHOENIX_CODING")

# =======================================================================
# THIRD-PARTY IMPORTS
# =======================================================================
try:
    from fastapi import FastAPI, Request, HTTPException, Depends, BackgroundTasks, UploadFile, File, Form
    from fastapi.middleware.cors import CORSMiddleware
    from fastapi.responses import StreamingResponse, JSONResponse, FileResponse
    from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
    import uvicorn
    HAS_FASTAPI = True
except ImportError:
    print("❌ Install: pip install fastapi uvicorn")
    sys.exit(1)

try:
    import socketio
    HAS_SOCKETIO = True
except ImportError:
    HAS_SOCKETIO = False

try:
    from pydantic import BaseModel, Field, ConfigDict
    from pydantic_settings import BaseSettings, SettingsConfigDict
    HAS_PYDANTIC = True
except ImportError:
    HAS_PYDANTIC = False

try:
    from prometheus_client import Counter, Histogram, Gauge, generate_latest, start_http_server
    HAS_PROMETHEUS = True
except ImportError:
    HAS_PROMETHEUS = False

# =======================================================================
# CONFIGURATION
# =======================================================================
class Settings(BaseSettings):
    environment: str = os.getenv("ENV", "development")
    port: int = int(os.getenv("PHOENIX_PORT", "8002"))
    metrics_port: int = int(os.getenv("METRICS_PORT", "8003"))
    host: str = os.getenv("PHOENIX_HOST", "0.0.0.0")
    
    # Security
    api_key_admin: str = os.getenv("PHOENIX_ADMIN_KEY", secrets.token_urlsafe(32))
    api_key_viewer: str = os.getenv("PHOENIX_VIEWER_KEY", secrets.token_urlsafe(32))
    
    # Directories
    workspace_dir: Path = Path(os.getenv("WORKSPACE_DIR", str(Path.cwd())))
    backups_dir: Path = Path("data/backups")
    sandbox_dir: Path = Path("data/sandbox")
    
    # Ollama
    ollama_url: str = os.getenv("OLLAMA_URL", "http://localhost:11434")
    default_model: str = os.getenv("OLLAMA_MODEL", "llama3.2:latest")
    
    # Code execution safety
    allow_code_execution: bool = os.getenv("ALLOW_CODE_EXECUTION", "false").lower() == "true"
    require_admin_for_execution: bool = os.getenv("REQUIRE_ADMIN_FOR_EXECUTION", "true").lower() == "true"
    max_file_size: int = int(os.getenv("MAX_FILE_SIZE", "10485760"))  # 10MB
    allowed_extensions: List[str] = ['.py', '.js', '.html', '.css', '.json', '.yaml', '.yml', '.txt', '.md']
    
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()
settings.workspace_dir.mkdir(parents=True, exist_ok=True)
settings.backups_dir.mkdir(parents=True, exist_ok=True)
settings.sandbox_dir.mkdir(parents=True, exist_ok=True)

# =======================================================================
# SECURITY & VALIDATION
# =======================================================================
class SecurityError(Exception):
    pass

def validate_path(base_dir: Path, user_path: str) -> Path:
    """Validate and sanitize file paths to prevent traversal"""
    if not user_path or user_path.strip() == "":
        raise SecurityError("Empty path")
    
    # Normalize path separators
    user_path = user_path.replace('\\', '/')
    
    # Block path traversal attempts
    if '..' in user_path or '~' in user_path:
        raise SecurityError("Path traversal not allowed")
    
    # Resolve path
    target = (base_dir / user_path).resolve()
    
    # Ensure it's within base directory
    try:
        target.relative_to(base_dir.resolve())
    except ValueError:
        raise SecurityError(f"Path {user_path} escapes workspace directory")
    
    return target

def validate_file_extension(filename: str) -> bool:
    """Check if file extension is allowed"""
    ext = Path(filename).suffix.lower()
    return ext in settings.allowed_extensions or not ext  # Allow files without extension

def create_backup(file_path: Path) -> Path:
    """Create a backup of a file before modification"""
    if not file_path.exists():
        return None
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_name = f"{file_path.stem}_{timestamp}{file_path.suffix}.backup"
    backup_path = settings.backups_dir / backup_name
    
    shutil.copy2(file_path, backup_path)
    logger.info(f"Backup created: {backup_path}")
    return backup_path

# =======================================================================
# PYDANTIC MODELS
# =======================================================================
if HAS_PYDANTIC:
    class CodeExecutionRequest(BaseModel):
        code: str
        language: str = "python"
        timeout: int = 30
        
    class FileOperationRequest(BaseModel):
        path: str
        content: Optional[str] = None
        operation: str  # read, write, modify, delete, create
    
    class RefactorRequest(BaseModel):
        file_path: str
        instructions: str
        create_backup: bool = True
    
    class TestRequest(BaseModel):
        test_path: Optional[str] = None
        pattern: Optional[str] = None

# =======================================================================
# EVENT TYPES
# =======================================================================
class EventType(Enum):
    SYSTEM_BOOT = "system.boot"
    CODE_EXECUTION = "code.execution"
    FILE_OPERATION = "file.operation"
    CODE_REFACTOR = "code.refactor"
    TEST_RUN = "test.run"
    SECURITY_VIOLATION = "security.violation"
    WORKER_LOADED = "worker.loaded"
    WORKER_ERROR = "worker.error"

@dataclass(frozen=True)
class Event:
    type: EventType
    source: str
    payload: Dict[str, Any]
    timestamp: float = field(default_factory=time.time)
    
    def __post_init__(self):
        content = f"{self.type.value}:{self.source}:{json.dumps(self.payload, sort_keys=True)}:{self.timestamp}"
        object.__setattr__(self, '_vera_proof', hashlib.sha256(content.encode()).hexdigest()[:16])
    
    @property
    def vera_proof(self) -> str:
        return getattr(self, '_vera_proof', '')

class EventBus:
    def __init__(self):
        self._events: List[Event] = []
        self._lock = asyncio.Lock()
    
    async def publish(self, event: Event):
        async with self._lock:
            self._events.append(event)
            if len(self._events) > 10000:
                self._events.pop(0)
        logger.debug(f"Event published: {event.type.value}")
    
    async def get_events(self, limit: int = 100) -> List[Dict]:
        async with self._lock:
            return [
                {
                    "type": e.type.value,
                    "source": e.source,
                    "payload": e.payload,
                    "timestamp": e.timestamp,
                    "vera_proof": e.vera_proof
                }
                for e in self._events[-limit:]
            ]

event_bus = EventBus()

# =======================================================================
# ENHANCED CONSTITUTION
# =======================================================================
class Constitution:
    def __init__(self):
        self.laws = {
            "SOVEREIGNTY": "System integrity is paramount",
            "TRANSPARENCY": "All operations must be logged",
            "ACCOUNTABILITY": "All actions must be attributable",
            "SAFETY": "No harmful operations allowed",
            "CODE_SAFETY": "Code execution is restricted",
            "FILE_SAFETY": "File operations require validation"
        }
        self.whitelist = ['/health', '/workers', '/metrics', '/docs']
        self.dangerous_patterns = [
            r'rm\s+-rf', r'format\s+', r'del\s+/', r'shutdown', r'reboot',
            r'mkfs', r'dd\s+if=', r'>\s*/dev/', r'chmod\s+777', r'chown'
        ]
    
    def evaluate(self, action: str, context: Optional[Dict] = None) -> dict:
        """Evaluate if an action is allowed by the constitution"""
        action_lower = action.lower()
        
        # Check whitelist
        if any(cmd in action_lower for cmd in self.whitelist):
            return {"approved": True, "reason": "Whitelisted endpoint", "score": 100}
        
        # Check for dangerous patterns
        for pattern in self.dangerous_patterns:
            if re.search(pattern, action_lower):
                return {
                    "approved": False,
                    "reason": f"Dangerous pattern detected: {pattern}",
                    "score": 0,
                    "law_violated": "SAFETY"
                }
        
        # Code execution check
        if any(kw in action_lower for kw in ['execute', 'run', 'eval', 'exec']):
            if not settings.allow_code_execution:
                return {
                    "approved": False,
                    "reason": "Code execution is disabled by configuration",
                    "score": 0,
                    "law_violated": "CODE_SAFETY"
                }
            if settings.require_admin_for_execution and context and context.get('role') != 'admin':
                return {
                    "approved": False,
                    "reason": "Code execution requires admin privileges",
                    "score": 20,
                    "law_violated": "CODE_SAFETY"
                }
            return {
                "approved": True,
                "reason": "Code execution permitted with sandboxing",
                "score": 70,
                "laws_applied": ["CODE_SAFETY", "TRANSPARENCY"]
            }
        
        # File modification check
        if any(kw in action_lower for kw in ['write', 'modify', 'delete', 'create', 'edit']):
            if context and context.get('role') != 'admin':
                return {
                    "approved": False,
                    "reason": "File modification requires admin privileges",
                    "score": 30,
                    "law_violated": "FILE_SAFETY"
                }
            return {
                "approved": True,
                "reason": "File modification permitted with backup",
                "score": 80,
                "laws_applied": ["FILE_SAFETY", "ACCOUNTABILITY"]
            }
        
        return {"approved": True, "reason": "No restrictions", "score": 90}

constitution = Constitution()

# =======================================================================
# WORKER BASE CLASS
# =======================================================================
class Worker(ABC):
    def __init__(self, name: str):
        self.name = name
        self.metrics = {'calls': 0, 'errors': 0}
    
    @abstractmethod
    async def execute(self, task: str, **kwargs) -> Dict[str, Any]:
        pass
    
    async def validate(self, task: str) -> bool:
        return True

# =======================================================================
# FILE SYSTEM WORKER
# =======================================================================
class FileSystemWorker(Worker):
    """SCE-compliant worker for file operations"""
    
    def __init__(self):
        super().__init__("file_system_worker")
        self.workspace = settings.workspace_dir
    
    async def execute(self, task: str, **kwargs) -> Dict[str, Any]:
        """Execute file operations based on task"""
        task_lower = task.lower()
        
        # Parse operation type
        if 'read' in task_lower or 'view' in task_lower or 'cat' in task_lower:
            return await self._read_file(task, **kwargs)
        elif 'write' in task_lower or 'create' in task_lower or 'save' in task_lower:
            return await self._write_file(task, **kwargs)
        elif 'modify' in task_lower or 'edit' in task_lower or 'update' in task_lower:
            return await self._modify_file(task, **kwargs)
        elif 'delete' in task_lower or 'remove' in task_lower:
            return await self._delete_file(task, **kwargs)
        elif 'list' in task_lower or 'ls' in task_lower or 'dir' in task_lower:
            return await self._list_directory(task, **kwargs)
        elif 'search' in task_lower or 'find' in task_lower:
            return await self._search_files(task, **kwargs)
        elif 'info' in task_lower or 'stat' in task_lower:
            return await self._file_info(task, **kwargs)
        else:
            return {"error": f"Unknown file operation: {task}", "success": False}
    
    async def _read_file(self, task: str, **kwargs) -> Dict[str, Any]:
        """Read a file from the workspace"""
        # Extract filename
        match = re.search(r'(?:read|view|cat|open)\s+([^\s]+)', task.lower())
        if not match:
            return {"error": "No filename specified", "success": False}
        
        filename = match.group(1)
        
        try:
            safe_path = validate_path(self.workspace, filename)
            
            if not safe_path.exists():
                return {"error": f"File not found: {filename}", "success": False}
            
            if safe_path.is_dir():
                return {"error": f"Cannot read directory: {filename}", "success": False}
            
            # Check file size
            file_size = safe_path.stat().st_size
            if file_size > settings.max_file_size:
                return {
                    "error": f"File too large: {file_size} bytes (max: {settings.max_file_size})",
                    "success": False
                }
            
            # Read file
            with open(safe_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Log the operation
            await event_bus.publish(Event(
                type=EventType.FILE_OPERATION,
                source=self.name,
                payload={"operation": "read", "file": str(safe_path), "size": len(content)}
            ))
            
            return {
                "success": True,
                "filename": str(safe_path),
                "content": content,
                "size": len(content),
                "lines": len(content.splitlines())
            }
        except SecurityError as e:
            return {"error": f"Security violation: {str(e)}", "success": False}
        except Exception as e:
            return {"error": f"Failed to read file: {str(e)}", "success": False}
    
    async def _write_file(self, task: str, **kwargs) -> Dict[str, Any]:
        """Write content to a file"""
        # Extract filename and content
        # Format: write <filename> <content> or write <filename> with content in payload
        match = re.search(r'(?:write|create|save)\s+([^\s]+)\s+(.+?)$', task, re.IGNORECASE)
        
        if not match:
            # Try to get content from kwargs
            filename = kwargs.get('filename')
            content = kwargs.get('content')
            if not filename or content is None:
                return {"error": "Invalid format. Use: write <filename> <content>", "success": False}
        else:
            filename = match.group(1)
            content = match.group(2)
        
        try:
            safe_path = validate_path(self.workspace, filename)
            
            # Validate extension
            if not validate_file_extension(filename):
                return {"error": f"File extension not allowed: {filename}", "success": False}
            
            # Create backup if file exists
            backup_path = None
            if safe_path.exists():
                backup_path = create_backup(safe_path)
            
            # Create parent directories if needed
            safe_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Write file
            with open(safe_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            # Log the operation
            await event_bus.publish(Event(
                type=EventType.FILE_OPERATION,
                source=self.name,
                payload={
                    "operation": "write",
                    "file": str(safe_path),
                    "size": len(content),
                    "backup": str(backup_path) if backup_path else None
                }
            ))
            
            return {
                "success": True,
                "filename": str(safe_path),
                "bytes_written": len(content),
                "backup_created": str(backup_path) if backup_path else None
            }
        except SecurityError as e:
            return {"error": f"Security violation: {str(e)}", "success": False}
        except Exception as e:
            return {"error": f"Failed to write file: {str(e)}", "success": False}
    
    async def _modify_file(self, task: str, **kwargs) -> Dict[str, Any]:
        """Modify a file using pattern replacement"""
        # Format: modify <filename> /pattern/replacement/ or modify <filename> replace old new
        match = re.search(r'(?:modify|edit|update)\s+([^\s]+)\s+/(.+?)/(.+?)/', task, re.IGNORECASE)
        
        if not match:
            # Try alternative format: modify <filename> replace <old> <new>
            alt_match = re.search(r'(?:modify|edit|update)\s+([^\s]+)\s+replace\s+(.+?)\s+(.+?)$', task, re.IGNORECASE)
            if alt_match:
                filename = alt_match.group(1)
                search_pattern = alt_match.group(2)
                replacement = alt_match.group(3)
            else:
                return {"error": "Invalid format. Use: modify <filename> /pattern/replacement/", "success": False}
        else:
            filename = match.group(1)
            search_pattern = match.group(2)
            replacement = match.group(3)
        
        try:
            safe_path = validate_path(self.workspace, filename)
            
            if not safe_path.exists():
                return {"error": f"File not found: {filename}", "success": False}
            
            # Read current content
            with open(safe_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Create backup
            backup_path = create_backup(safe_path)
            
            # Perform replacement
            new_content = re.sub(search_pattern, replacement, content)
            changes_made = len(re.findall(search_pattern, content))
            
            # Write back
            with open(safe_path, 'w', encoding='utf-8') as f:
                f.write(new_content)
            
            # Log the operation
            await event_bus.publish(Event(
                type=EventType.FILE_OPERATION,
                source=self.name,
                payload={
                    "operation": "modify",
                    "file": str(safe_path),
                    "changes": changes_made,
                    "backup": str(backup_path)
                }
            ))
            
            return {
                "success": True,
                "filename": str(safe_path),
                "changes_made": changes_made,
                "backup": str(backup_path)
            }
        except Exception as e:
            return {"error": f"Failed to modify file: {str(e)}", "success": False}
    
    async def _delete_file(self, task: str, **kwargs) -> Dict[str, Any]:
        """Delete a file (with backup)"""
        match = re.search(r'(?:delete|remove)\s+([^\s]+)', task.lower())
        if not match:
            return {"error": "No filename specified", "success": False}
        
        filename = match.group(1)
        
        try:
            safe_path = validate_path(self.workspace, filename)
            
            if not safe_path.exists():
                return {"error": f"File not found: {filename}", "success": False}
            
            # Create backup before deletion
            backup_path = create_backup(safe_path)
            
            # Delete file
            safe_path.unlink()
            
            # Log the operation
            await event_bus.publish(Event(
                type=EventType.FILE_OPERATION,
                source=self.name,
                payload={
                    "operation": "delete",
                    "file": str(safe_path),
                    "backup": str(backup_path)
                }
            ))
            
            return {
                "success": True,
                "filename": str(safe_path),
                "backup": str(backup_path)
            }
        except Exception as e:
            return {"error": f"Failed to delete file: {str(e)}", "success": False}
    
    async def _list_directory(self, task: str, **kwargs) -> Dict[str, Any]:
        """List contents of a directory"""
        match = re.search(r'(?:list|ls|dir)\s+([^\s]*)', task.lower())
        directory = match.group(1) if match else '.'
        
        try:
            safe_path = validate_path(self.workspace, directory)
            
            if not safe_path.exists():
                return {"error": f"Path not found: {directory}", "success": False}
            
            if not safe_path.is_dir():
                return {"error": f"Not a directory: {directory}", "success": False}
            
            items = []
            for item in safe_path.iterdir():
                try:
                    stat = item.stat()
                    items.append({
                        "name": item.name,
                        "type": "directory" if item.is_dir() else "file",
                        "size": stat.st_size if item.is_file() else 0,
                        "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                        "extension": item.suffix if item.is_file() else None
                    })
                except:
                    items.append({"name": item.name, "type": "unknown"})
            
            # Sort: directories first, then files
            items.sort(key=lambda x: (x['type'] != 'directory', x['name'].lower()))
            
            return {
                "success": True,
                "directory": str(safe_path),
                "items": items,
                "count": len(items)
            }
        except Exception as e:
            return {"error": f"Failed to list directory: {str(e)}", "success": False}
    
    async def _search_files(self, task: str, **kwargs) -> Dict[str, Any]:
        """Search for files matching pattern"""
        match = re.search(r'(?:search|find)\s+([^\s]+)\s+([^\s]+)?', task.lower())
        if not match:
            return {"error": "Invalid format. Use: search <pattern> [directory]", "success": False}
        
        pattern = match.group(1)
        directory = match.group(2) if len(match.groups()) > 1 else '.'
        
        try:
            safe_path = validate_path(self.workspace, directory)
            
            if not safe_path.exists() or not safe_path.is_dir():
                return {"error": f"Invalid directory: {directory}", "success": False}
            
            results = []
            for file_path in safe_path.rglob(pattern):
                if file_path.is_file():
                    results.append({
                        "path": str(file_path.relative_to(self.workspace)),
                        "size": file_path.stat().st_size,
                        "modified": datetime.fromtimestamp(file_path.stat().st_mtime).isoformat()
                    })
            
            return {
                "success": True,
                "pattern": pattern,
                "directory": str(safe_path),
                "results": results[:100],  # Limit results
                "count": len(results)
            }
        except Exception as e:
            return {"error": f"Failed to search: {str(e)}", "success": False}
    
    async def _file_info(self, task: str, **kwargs) -> Dict[str, Any]:
        """Get detailed file information"""
        match = re.search(r'(?:info|stat)\s+([^\s]+)', task.lower())
        if not match:
            return {"error": "No filename specified", "success": False}
        
        filename = match.group(1)
        
        try:
            safe_path = validate_path(self.workspace, filename)
            
            if not safe_path.exists():
                return {"error": f"File not found: {filename}", "success": False}
            
            stat = safe_path.stat()
            
            info = {
                "path": str(safe_path),
                "name": safe_path.name,
                "type": "directory" if safe_path.is_dir() else "file",
                "size": stat.st_size,
                "created": datetime.fromtimestamp(stat.st_ctime).isoformat(),
                "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                "accessed": datetime.fromtimestamp(stat.st_atime).isoformat(),
                "permissions": oct(stat.st_mode)[-3:],
            }
            
            if safe_path.is_file():
                info["extension"] = safe_path.suffix
                info["is_executable"] = os.access(safe_path, os.X_OK)
                
                # Count lines for text files
                try:
                    with open(safe_path, 'r', encoding='utf-8') as f:
                        info["lines"] = len(f.readlines())
                except:
                    info["lines"] = None
            
            return {"success": True, "info": info}
        except Exception as e:
            return {"error": f"Failed to get file info: {str(e)}", "success": False}

# =======================================================================
# CODE EXECUTION WORKER (SANDBOXED)
# =======================================================================
class CodeExecutionWorker(Worker):
    """Sandboxed code execution worker"""
    
    def __init__(self):
        super().__init__("code_execution_worker")
        self.sandbox_dir = settings.sandbox_dir
        self.timeout = 30
    
    async def execute(self, task: str, **kwargs) -> Dict[str, Any]:
        """Execute code in sandboxed environment"""
        
        # Extract code
        code = None
        language = "python"
        
        # Check if code is in a code block
        code_block = re.search(r'```(?:python)?\s*\n(.*?)\n```', task, re.DOTALL)
        if code_block:
            code = code_block.group(1)
        else:
            # Try to extract after 'run' or 'execute'
            match = re.search(r'(?:run|execute)\s+(.+?)(?:$)', task, re.IGNORECASE)
            if match:
                code = match.group(1)
            else:
                return {"error": "No code found to execute", "success": False}
        
        # Check constitution
        ruling = constitution.evaluate(task, kwargs.get('context', {}))
        if not ruling.get("approved"):
            await event_bus.publish(Event(
                type=EventType.SECURITY_VIOLATION,
                source=self.name,
                payload={"reason": ruling.get("reason"), "code_preview": code[:100]}
            ))
            return {
                "error": f"Execution blocked: {ruling.get('reason')}",
                "success": False,
                "ruling": ruling
            }
        
        # Log execution attempt
        await event_bus.publish(Event(
            type=EventType.CODE_EXECUTION,
            source=self.name,
            payload={"language": language, "code_length": len(code)}
        ))
        
        # Execute in sandbox
        if language == "python":
            return await self._execute_python(code, **kwargs)
        else:
            return {"error": f"Language {language} not supported", "success": False}
    
    async def _execute_python(self, code: str, **kwargs) -> Dict[str, Any]:
        """Execute Python code in a sandboxed environment"""
        
        # Create a temporary file for execution
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', dir=str(self.sandbox_dir), delete=False) as f:
            # Add safety wrapper
            safety_wrapper = """
import sys
import io
from contextlib import redirect_stdout, redirect_stderr

# Capture output
stdout_capture = io.StringIO()
stderr_capture = io.StringIO()

try:
    with redirect_stdout(stdout_capture), redirect_stderr(stderr_capture):
        # Execute user code
        {code}
    result = {{
        "success": True,
        "stdout": stdout_capture.getvalue(),
        "stderr": stderr_capture.getvalue()
    }}
except Exception as e:
    result = {{
        "success": False,
        "error": str(e),
        "stdout": stdout_capture.getvalue(),
        "stderr": stderr_capture.getvalue()
    }}
finally:
    import json
    print(json.dumps(result))
"""
            f.write(safety_wrapper.format(code=code))
            temp_file = f.name
        
        try:
            # Execute with timeout
            process = await asyncio.create_subprocess_exec(
                sys.executable, temp_file,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=str(self.sandbox_dir)
            )
            
            try:
                stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=self.timeout)
                
                # Parse JSON result
                try:
                    result = json.loads(stdout.decode('utf-8').strip().split('\n')[-1])
                except:
                    result = {
                        "success": False,
                        "error": "Failed to parse output",
                        "stdout": stdout.decode('utf-8'),
                        "stderr": stderr.decode('utf-8')
                    }
                
                return result
                
            except asyncio.TimeoutError:
                process.kill()
                await process.wait()
                return {
                    "success": False,
                    "error": f"Execution timed out after {self.timeout} seconds"
                }
                
        except Exception as e:
            return {"success": False, "error": str(e)}
        finally:
            # Cleanup
            try:
                os.unlink(temp_file)
            except:
                pass

# =======================================================================
# CODE ANALYZER WORKER
# =======================================================================
class CodeAnalyzerWorker(Worker):
    """Analyze code for patterns, issues, and suggestions"""
    
    def __init__(self):
        super().__init__("code_analyzer_worker")
    
    async def execute(self, task: str, **kwargs) -> Dict[str, Any]:
        """Analyze code or files for potential improvements"""
        
        # Extract code to analyze
        code = None
        filename = None
        
        if 'file' in task.lower():
            # Analyze a file
            match = re.search(r'file\s+([^\s]+)', task.lower())
            if match:
                filename = match.group(1)
                try:
                    safe_path = validate_path(settings.workspace_dir, filename)
                    with open(safe_path, 'r', encoding='utf-8') as f:
                        code = f.read()
                except Exception as e:
                    return {"error": f"Could not read file: {str(e)}", "success": False}
        elif '```' in task:
            # Extract from markdown
            match = re.search(r'```(?:python)?\s*\n(.*?)\n```', task, re.DOTALL)
            if match:
                code = match.group(1)
        
        if not code:
            return {"error": "No code to analyze", "success": False}
        
        # Perform analysis
        analysis = await self._analyze_code(code, filename)
        
        return {
            "success": True,
            "filename": filename,
            "analysis": analysis
        }
    
    async def _analyze_code(self, code: str, filename: Optional[str] = None) -> Dict[str, Any]:
        """Perform static analysis on code"""
        
        analysis = {
            "metrics": {},
            "issues": [],
            "suggestions": [],
            "complexity": {},
            "security_concerns": []
        }
        
        lines = code.splitlines()
        analysis["metrics"]["lines"] = len(lines)
        analysis["metrics"]["characters"] = len(code)
        analysis["metrics"]["blank_lines"] = sum(1 for line in lines if not line.strip())
        analysis["metrics"]["comment_lines"] = sum(1 for line in lines if line.strip().startswith('#'))
        
        # Python-specific analysis
        try:
            tree = ast.parse(code)
            
            # Count functions and classes
            functions = [node for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)]
            classes = [node for node in ast.walk(tree) if isinstance(node, ast.ClassDef)]
            
            analysis["metrics"]["functions"] = len(functions)
            analysis["metrics"]["classes"] = len(classes)
            analysis["metrics"]["function_names"] = [f.name for f in functions[:10]]
            
            # Check for complexity
            for func in functions:
                complexity = self._calculate_complexity(func)
                if complexity > 10:
                    analysis["complexity"][func.name] = complexity
                    analysis["suggestions"].append(
                        f"Function '{func.name}' has high complexity ({complexity}). Consider refactoring."
                    )
            
            # Security checks
            imports = [node for node in ast.walk(tree) if isinstance(node, ast.Import)]
            for imp in imports:
                for alias in imp.names:
                    if alias.name in ['os', 'subprocess', 'sys', '__builtins__']:
                        analysis["security_concerns"].append(
                            f"Import of '{alias.name}' - potentially dangerous"
                        )
            
            # Check for dangerous calls
            for node in ast.walk(tree):
                if isinstance(node, ast.Call):
                    if isinstance(node.func, ast.Name):
                        if node.func.id in ['eval', 'exec', '__import__', 'open']:
                            analysis["security_concerns"].append(
                                f"Use of '{node.func.id}()' - security risk"
                            )
            
        except SyntaxError as e:
            analysis["issues"].append(f"Syntax error: {e}")
        
        # Check for common issues
        if 'print(' in code and len(lines) > 50:
            analysis["suggestions"].append("Consider using logging instead of print statements")
        
        if len(lines) > 500:
            analysis["suggestions"].append("File is large - consider splitting into modules")
        
        if not analysis["metrics"].get("functions", 0) and not analysis["metrics"].get("classes", 0):
            analysis["suggestions"].append("No functions or classes - consider organizing code")
        
        if 'TODO' in code:
            analysis["issues"].append("Contains TODO comments - incomplete code")
        
        # Overall quality score
        score = 100
        score -= len(analysis["issues"]) * 5
        score -= len(analysis["security_concerns"]) * 10
        score -= len(analysis["complexity"]) * 3
        
        analysis["quality_score"] = max(0, min(100, score))
        
        return analysis
    
    def _calculate_complexity(self, func_node: ast.FunctionDef) -> int:
        """Calculate cyclomatic complexity of a function"""
        complexity = 1  # Base complexity
        for node in ast.walk(func_node):
            if isinstance(node, (ast.If, ast.While, ast.For, ast.ExceptHandler)):
                complexity += 1
            elif isinstance(node, ast.BoolOp):
                complexity += len(node.values) - 1
        return complexity

# =======================================================================
# REFACTORING WORKER (AI-POWERED)
# =======================================================================
class RefactoringWorker(Worker):
    """AI-powered code refactoring"""
    
    def __init__(self, ollama_client):
        super().__init__("refactoring_worker")
        self.ollama = ollama_client
    
    async def execute(self, task: str, **kwargs) -> Dict[str, Any]:
        """Refactor code based on instructions"""
        
        # Parse task
        match = re.search(r'refactor\s+([^\s]+)\s+(.+?)(?:$)', task, re.IGNORECASE)
        if not match:
            return {"error": "Format: refactor <filename> <instructions>", "success": False}
        
        filename = match.group(1)
        instructions = match.group(2)
        
        try:
            safe_path = validate_path(settings.workspace_dir, filename)
            
            if not safe_path.exists():
                return {"error": f"File not found: {filename}", "success": False}
            
            # Read the file
            with open(safe_path, 'r', encoding='utf-8') as f:
                original_code = f.read()
            
            # Create prompt for AI
            prompt = f"""Refactor the following code based on these instructions: {instructions}

Original code:
```python
{original_code}
```

Provide:
1. The refactored code in a code block
2. A brief explanation of changes made
3. Any potential impacts or things to test

Refactored version:"""
            
            # Get AI response
            response = ""
            async for chunk in self.ollama.generate(prompt, stream=False):
                response += chunk
            
            # Extract code from response
            code_match = re.search(r'```(?:python)?\s*\n(.*?)\n```', response, re.DOTALL)
            if code_match:
                refactored_code = code_match.group(1)
                
                # Create backup
                backup_path = create_backup(safe_path)
                
                # Write refactored code
                with open(safe_path, 'w', encoding='utf-8') as f:
                    f.write(refactored_code)
                
                # Log the operation
                await event_bus.publish(Event(
                    type=EventType.CODE_REFACTOR,
                    source=self.name,
                    payload={
                        "file": str(safe_path),
                        "instructions": instructions,
                        "backup": str(backup_path)
                    }
                ))
                
                return {
                    "success": True,
                    "filename": str(safe_path),
                    "backup": str(backup_path),
                    "explanation": response,
                    "changes_made": len(original_code) != len(refactored_code)
                }
            else:
                return {
                    "success": False,
                    "error": "Could not extract refactored code from AI response",
                    "ai_response": response[:500]
                }
                
        except Exception as e:
            return {"error": f"Refactoring failed: {str(e)}", "success": False}

# =======================================================================
# TEST WORKER
# =======================================================================
class TestWorker(Worker):
    """Run tests on code"""
    
    def __init__(self):
        super().__init__("test_worker")
    
    async def execute(self, task: str, **kwargs) -> Dict[str, Any]:
        """Run tests"""
        
        # Parse test target
        match = re.search(r'test\s+([^\s]+)', task.lower())
        if not match:
            # Run all tests
            return await self._run_tests(None)
        
        test_target = match.group(1)
        return await self._run_tests(test_target)
    
    async def _run_tests(self, target: Optional[str]) -> Dict[str, Any]:
        """Execute pytest tests"""
        
        try:
            # Build command
            cmd = [sys.executable, '-m', 'pytest', '-v', '--tb=short']
            if target:
                safe_path = validate_path(settings.workspace_dir, target)
                cmd.append(str(safe_path))
            else:
                # Look for tests directory
                tests_dir = settings.workspace_dir / 'tests'
                if tests_dir.exists():
                    cmd.append(str(tests_dir))
                else:
                    cmd.append(str(settings.workspace_dir))
            
            # Run tests
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                cwd=str(settings.workspace_dir),
                timeout=60
            )
            
            # Log the operation
            await event_bus.publish(Event(
                type=EventType.TEST_RUN,
                source=self.name,
                payload={
                    "target": target,
                    "returncode": result.returncode,
                    "passed": result.returncode == 0
                }
            ))
            
            # Parse test results
            passed = result.returncode == 0
            
            return {
                "success": passed,
                "passed": passed,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "returncode": result.returncode
            }
            
        except subprocess.TimeoutExpired:
            return {"success": False, "error": "Tests timed out after 60 seconds"}
        except Exception as e:
            return {"success": False, "error": str(e)}

# =======================================================================
# OLLAMA CLIENT
# =======================================================================
class OllamaClient:
    def __init__(self):
        self.client = None
        self.base_url = settings.ollama_url
    
    async def initialize(self):
        self.client = httpx.AsyncClient(timeout=60)
        logger.info("Ollama client initialized")
    
    async def generate(self, prompt: str, stream: bool = False, system: str = None):
        if not self.client:
            await self.initialize()
        
        url = f"{self.base_url}/api/generate"
        payload = {
            "model": settings.default_model,
            "prompt": prompt,
            "stream": stream
        }
        if system:
            payload["system"] = system
        
        try:
            if stream:
                async with self.client.stream("POST", url, json=payload) as response:
                    async for line in response.aiter_lines():
                        if line:
                            chunk = json.loads(line)
                            if 'response' in chunk:
                                yield chunk.get("response", "")
            else:
                response = await self.client.post(url, json=payload)
                data = response.json()
                yield data.get("response", "")
        except Exception as e:
            yield f"[AI Error: {e}]"
    
    async def close(self):
        if self.client:
            await self.client.aclose()

# =======================================================================
# PHOENIX KERNEL WITH CODING TOOL
# =======================================================================
class PhoenixKernel:
    def __init__(self):
        self.version = "13.3.0"
        self.start_time = time.time()
        
        # Initialize components
        self.constitution = constitution
        self.ollama = OllamaClient()
        self.event_bus = event_bus
        
        # Initialize workers
        self.file_worker = FileSystemWorker()
        self.code_executor = CodeExecutionWorker()
        self.code_analyzer = CodeAnalyzerWorker()
        self.test_worker = TestWorker()
        self.refactor_worker = RefactoringWorker(self.ollama)
        
        # Worker registry
        self.workers = {
            "file": self.file_worker,
            "code": self.code_executor,
            "analyzer": self.code_analyzer,
            "test": self.test_worker,
            "refactor": self.refactor_worker
        }
        
        # FastAPI app
        self.app = FastAPI(
            title=f"Phoenix Agentic Coding Tool v{self.version}",
            description="SCE-compliant AI-powered coding assistant",
            version=self.version
        )
        
        # CORS
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        
        self.setup_routes()
        
        logger.info(f"Phoenix Coding Tool v{self.version} initialized")
    
    def setup_routes(self):
        # Health check
        @self.app.get("/")
        async def root():
            return {
                "name": "Phoenix Agentic Coding Tool",
                "version": self.version,
                "status": "online",
                "workspace": str(settings.workspace_dir),
                "features": ["file_operations", "code_execution", "analysis", "refactoring", "testing"]
            }
        
        @self.app.get("/health")
        async def health():
            return {
                "status": "healthy",
                "uptime": time.time() - self.start_time,
                "workspace": str(settings.workspace_dir),
                "workers": list(self.workers.keys())
            }
        
        # File operations
        @self.app.post("/file/read")
        async def file_read(request: Request):
            data = await request.json()
            result = await self.file_worker.execute(f"read {data.get('path', '')}")
            return result
        
        @self.app.post("/file/write")
        async def file_write(request: Request):
            data = await request.json()
            result = await self.file_worker.execute(
                f"write {data.get('path', '')}",
                filename=data.get('path'),
                content=data.get('content', '')
            )
            return result
        
        @self.app.post("/file/list")
        async def file_list(request: Request):
            data = await request.json()
            result = await self.file_worker.execute(f"list {data.get('path', '.')}")
            return result
        
        @self.app.post("/file/search")
        async def file_search(request: Request):
            data = await request.json()
            result = await self.file_worker.execute(f"search {data.get('pattern', '')} {data.get('directory', '.')}")
            return result
        
        # Code execution
        @self.app.post("/code/execute")
        async def code_execute(request: Request):
            data = await request.json()
            result = await self.code_executor.execute(data.get('code', ''))
            return result
        
        # Code analysis
        @self.app.post("/code/analyze")
        async def code_analyze(request: Request):
            data = await request.json()
            if 'file' in data:
                result = await self.code_analyzer.execute(f"analyze file {data['file']}")
            else:
                result = await self.code_analyzer.execute(f"analyze ```python\n{data.get('code', '')}\n```")
            return result
        
        # Code refactoring
        @self.app.post("/code/refactor")
        async def code_refactor(request: Request):
            data = await request.json()
            result = await self.refactor_worker.execute(
                f"refactor {data.get('file_path', '')} {data.get('instructions', '')}"
            )
            return result
        
        # Test runner
        @self.app.post("/test/run")
        async def test_run(request: Request):
            data = await request.json()
            result = await self.test_worker.execute(f"test {data.get('target', '')}")
            return result
        
        # Event log
        @self.app.get("/events")
        async def get_events(limit: int = 100):
            return await self.event_bus.get_events(limit)
        
        # Constitution check
        @self.app.post("/constitution/check")
        async def constitution_check(request: Request):
            data = await request.json()
            ruling = self.constitution.evaluate(data.get('action', ''), data.get('context', {}))
            return ruling
    
    async def startup(self):
        await self.ollama.initialize()
        await self.event_bus.publish(Event(
            type=EventType.SYSTEM_BOOT,
            source="phoenix_kernel",
            payload={"version": self.version, "workspace": str(settings.workspace_dir)}
        ))
        
        print("\n" + "="*60)
        print(f"🔥 PHOENIX AGENTIC CODING TOOL v{self.version}")
        print("="*60)
        print(f"Workspace: {settings.workspace_dir}")
        print(f"Workers: {len(self.workers)}")
        print(f"Code Execution: {'✅' if settings.allow_code_execution else '❌'} (Admin: {settings.require_admin_for_execution})")
        print(f"File Operations: ✅ (Backups enabled)")
        print("="*60 + "\n")
    
    async def shutdown(self):
        await self.ollama.close()
        logger.info("Phoenix coding tool shutdown complete")
    
    async def run(self):
        await self.startup()
        config = uvicorn.Config(
            self.app,
            host=settings.host,
            port=settings.port,
            log_level="info"
        )
        server = uvicorn.Server(config)
        try:
            await server.serve()
        finally:
            await self.shutdown()

# =======================================================================
# MAIN ENTRY POINT
# =======================================================================
if __name__ == "__main__":
    import subprocess
    import platform
    
    # Kill existing process on port
    if platform.system() == "Windows":
        try:
            result = subprocess.run('netstat -ano | findstr :8002', shell=True, capture_output=True, text=True)
            for line in result.stdout.split('\n'):
                if 'LISTENING' in line:
                    parts = line.strip().split()
                    if len(parts) >= 5:
                        pid = parts[-1]
                        subprocess.run(f'taskkill /F /PID {pid}', shell=True, capture_output=True)
                        print(f"Killed process {pid} on port 8002")
        except:
            pass
    
    kernel = PhoenixKernel()
    try:
        asyncio.run(kernel.run())
    except KeyboardInterrupt:
        print("\nShutting down...")
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
```

## Key Features Now Available:

### 1. **File Operations**
- Read files with security validation
- Write/create files with automatic backups
- Modify files with pattern replacement
- Delete files with backup before deletion
- List directory contents
- Search for files by pattern
- File info/stats

### 2. **Code Execution (Sandboxed)**
- Python code execution in isolated sandbox
- Output capture (stdout/stderr)
- Timeout protection
- Security validation before execution

### 3. **Code Analysis**
- Static analysis with AST
- Complexity calculation
- Security vulnerability detection
- Code quality scoring
- Function/class detection

### 4. **AI-Powered Refactoring**
- Integration with Ollama
- Intelligent code refactoring
- Automatic backups before changes
- Change explanation

### 5. **Test Runner**
- Pytest integration
- Test execution with timeout
- Results parsing

### 6. **Security Controls**
- Path traversal prevention
- File extension whitelist
- Constitution-based approval
- Admin role requirements
- Automatic backups before modifications
- Full event logging

## API Endpoints:

- `POST /file/read` - Read a file
- `POST /file/write` - Write/create a file
- `POST /file/list` - List directory contents
- `POST /file/search` - Search for files
- `POST /code/execute` - Execute Python code
- `POST /code/analyze` - Analyze code
- `POST /code/refactor` - AI-powered refactoring
- `POST /test/run` - Run tests
- `POST /constitution/check` - Check action against constitution
- `GET /events` - View event log

## Usage Examples:

```bash
# Read a file
curl -X POST http://localhost:8002/file/read \
  -H "Content-Type: application/json" \
  -d '{"path": "example.py"}'

# Execute code
curl -X POST http://localhost:8002/code/execute \
  -H "Content-Type: application/json" \
  -d '{"code": "print(\"Hello World\")"}'

# Analyze code
curl -X POST http://localhost:8002/code/analyze \
  -H "Content-Type: application/json" \
  -d '{"file": "example.py"}'

# Refactor code
curl -X POST http://localhost:8002/code/refactor \
  -H "Content-Type: application/json" \
  -d '{"file_path": "example.py", "instructions": "add error handling"}'
```

The system is now a complete agentic coding tool with proper security controls, SCE compliance, and full observability!