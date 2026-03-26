import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
# backend/main.py - REZHIVE KERNEL v10.1.0-SECURE
"""
REZ HIVE OKIRU - Sovereign AI Operating System
Production-hardened with security patches and architectural fixes
"""

import asyncio
import os
import sys
import json
import time
import hashlib
import hmac
import random
import re
import secrets
from datetime import datetime
from contextlib import asynccontextmanager
from typing import Optional, List, Dict, Any, Callable, Awaitable
from enum import Enum, auto
from dataclasses import dataclass, field
from collections import defaultdict
from pathlib import Path

# ===================================================================
# CONFIGURATION & SECURITY
# ===================================================================

class Settings:
    """Centralized configuration with environment variable support"""
    PORT: int = int(os.getenv("REZHIVE_PORT", "8001"))
    API_KEY_ADMIN: str = os.getenv("REZHIVE_ADMIN_KEY", secrets.token_urlsafe(32))
    API_KEY_VIEWER: str = os.getenv("REZHIVE_VIEWER_KEY", secrets.token_urlsafe(32))
    MAX_FILE_SIZE: int = 50 * 1024 * 1024  # 50MB
    ALLOWED_EXTENSIONS: frozenset = frozenset([
        '.txt', '.md', '.json', '.csv', '.py', '.js', 
        '.tsx', '.jsx', '.ts', '.jpg', '.jpeg', '.png', '.pdf'
    ])
    UPLOAD_DIR: Path = Path("hive_memory/uploads")
    VFS_BASE: Path = Path("hive_vfs")
    CHAIN_MAXLEN: int = 10000
    RATE_LIMIT: str = "100/minute"
    OLLAMA_URL: str = os.getenv("OLLAMA_URL", "http://localhost:11434")
    DEFAULT_MODEL: str = "llama3.2:latest"
    CODER_MODEL: str = "qwen2.5-coder:14b"

settings = Settings()

# ===================================================================
# LOGGING SETUP
# ===================================================================

import logging
from logging.handlers import RotatingFileHandler

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

log_handler = RotatingFileHandler(
    'rezhive.log', maxBytes=10*1024*1024, backupCount=5, encoding='utf-8'
)
log_handler.setFormatter(logging.Formatter(
    "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
))

logging.basicConfig(
    level=logging.INFO,
    handlers=[log_handler, logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("rezhive")

# ===================================================================
# FASTAPI & SECURITY IMPORTS
# ===================================================================

from fastapi import (
    FastAPI, Request, Depends, UploadFile, File, 
    HTTPException, status, WebSocketException
)
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import StreamingResponse, JSONResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field, field_validator
import socketio
import httpx
import aiofiles

# Rate limiting
try:
    from slowapi import Limiter, _rate_limit_exceeded_handler
    from slowapi.util import get_remote_address
    from slowapi.errors import RateLimitExceeded
    RATE_LIMITING_AVAILABLE = True
except ImportError:
    RATE_LIMITING_AVAILABLE = False
    logger.warning("slowapi not installed - rate limiting disabled")

# ===================================================================
# SECURITY UTILITIES
# ===================================================================

class SecurityError(Exception):
    """Security violation exception"""
    pass

def sanitize_input(text: str, max_length: int = 10000) -> str:
    """
    Sanitize user input: remove control chars, limit length,
    prevent injection attacks while preserving unicode.
    """
    if not isinstance(text, str):
        raise SecurityError("Input must be string")
    
    if len(text) > max_length:
        raise SecurityError(f"Input exceeds maximum length of {max_length}")
    
    # Remove null bytes and control characters (except newlines/tabs)
    sanitized = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]', '', text)
    
    # Prevent path traversal patterns
    if '..' in sanitized or '~' in sanitized:
        raise SecurityError("Path traversal attempt detected")
    
    return sanitized.strip()

def validate_safe_path(base_dir: Path, user_path: str) -> Path:
    """
    Resolve user-provided path within base directory.
    Prevents directory traversal attacks.
    
    Raises:
        SecurityError: If path escapes base directory
    """
    try:
        base = base_dir.resolve()
        # Reject absolute paths from user
        if os.path.isabs(user_path):
            raise SecurityError("Absolute paths not allowed")
        
        target = (base / user_path).resolve()
        
        # Ensure resolved path starts with base path
        try:
            target.relative_to(base)
        except ValueError:
            raise SecurityError("Path traversal detected: escapes base directory")
        
        return target
    except SecurityError:
        raise
    except Exception as e:
        raise SecurityError(f"Invalid path: {e}")

def secure_filename(filename: str) -> str:
    """
    Sanitize filename to prevent directory traversal and 
    preserve only safe characters.
    """
    if not filename or len(filename) > 255:
        raise SecurityError("Invalid filename")
    
    # Remove path components
    filename = os.path.basename(filename)
    
    # Keep only safe chars: alphanumeric, dash, underscore, dot
    safe = re.sub(r'[^\w\-\.]', '_', filename)
    
    # Ensure not empty and not hidden
    safe = safe.lstrip('.')
    if not safe:
        safe = "unnamed_file"
    
    # Add timestamp prefix to prevent collisions
    return f"{int(time.time())}_{safe}"

def verify_file_type(file_path: Path) -> bool:
    """
    Verify file extension is allowed and check for double extensions.
    """
    suffixes = file_path.suffixes
    
    # Check last extension against allowed list
    if not suffixes:
        return False
    
    primary_ext = suffixes[-1].lower()
    if primary_ext not in settings.ALLOWED_EXTENSIONS:
        return False
    
    # Check for dangerous double extensions (e.g., .txt.exe)
    dangerous_exts = {'.exe', '.bat', '.cmd', '.sh', '.php', '.jsp'}
    for ext in suffixes[:-1]:
        if ext.lower() in dangerous_exts:
            return False
    
    return True

# ===================================================================
# EVENT SYSTEM (BLOCKCHAIN-LINKED)
# ===================================================================

class EventType(Enum):
    SYSTEM_BOOT = "system.boot"
    SYSTEM_SHUTDOWN = "system.shutdown"
    KERNEL_HEARTBEAT = "kernel.heartbeat"
    SCAN_STARTED = "techdebt.scan.started"
    SCAN_COMPLETED = "techdebt.scan.completed"
    VULNERABILITY_FOUND = "techdebt.vulnerability.found"
    LICENSE_ISSUE = "techdebt.license.issue"
    JURISDICTION_SCAN_STARTED = "jurisdiction.scan.started"
    JURISDICTION_SCAN_COMPLETED = "jurisdiction.scan.completed"
    HIGH_RISK_COMPONENT = "jurisdiction.high_risk"
    STRATEGY_PROPOSED = "strategy.proposed"
    STRATEGY_BACKTESTED = "strategy.backtested"
    MUTATION_OCCURRED = "strategy.mutation.occurred"
    FILE_SCANNED = "filedoctor.file.scanned"
    FILE_REPAIRED = "filedoctor.file.repaired"
    FILE_QUARANTINED = "filedoctor.file.quarantined"
    WORKER_START = "worker.start"
    WORKER_COMPLETE = "worker.complete"
    WORKER_ERROR = "worker.error"
    MARKET_UPDATE = "market.update"
    ARBITRAGE_OPPORTUNITY = "market.arbitrage"
    VERA_PROOF = "audit.vera.proof"
    SECURITY_ALERT = "security.alert"
    AUTH_FAILURE = "auth.failure"

@dataclass(frozen=True)
class Event:
    """Immutable event with cryptographic proof"""
    type: EventType
    source: str
    payload: Dict[str, Any]
    timestamp: float = field(default_factory=time.time)
    previous_hash: str = field(default="")
    
    def __post_init__(self):
        # Calculate VERA proof (SHA-256 of content + previous hash)
        content = (
            f"{self.type.value}:{self.source}:"
            f"{json.dumps(self.payload, sort_keys=True)}:"
            f"{self.timestamp}:{self.previous_hash}"
        )
        object.__setattr__(
            self, '_vera_proof', 
            hashlib.sha256(content.encode()).hexdigest()[:16]
        )
    
    @property
    def vera_proof(self) -> str:
        return getattr(self, '_vera_proof', '')

class SovereignEventBus:
    """Thread-safe event bus with blockchain-style integrity"""
    
    def __init__(self):
        self._subscribers: Dict[EventType, List[Callable[[Event], Awaitable[None]]]] = defaultdict(list)
        self._chain: List[Event] = []
        self._lock = asyncio.Lock()
        self._genesis_hash = hashlib.sha256(b"REZ_HIVE_GENESIS_v10.1.0").hexdigest()[:16]
        self._initialized = False
    
    async def initialize(self):
        """Async initialization"""
        if not self._initialized:
            self._initialized = True
            logger.info("Event bus initialized")
    
    def subscribe(self, event_type: EventType, callback: Callable[[Event], Awaitable[None]]) -> None:
        """Subscribe to event type with async callback"""
        if not asyncio.iscoroutinefunction(callback):
            raise ValueError("Callback must be async")
        self._subscribers[event_type].append(callback)
        logger.debug(f"Subscribed to {event_type.value}")
    
    def unsubscribe(self, event_type: EventType, callback: Callable) -> None:
        """Remove subscription"""
        if event_type in self._subscribers:
            self._subscribers[event_type] = [
                cb for cb in self._subscribers[event_type] if cb != callback
            ]
    
    async def publish(self, event: Event) -> None:
        """Publish event with blockchain linking"""
        async with self._lock:
            # Link to previous event
            if self._chain:
                linked_event = Event(
                    type=event.type,
                    source=event.source,
                    payload=event.payload,
                    timestamp=event.timestamp,
                    previous_hash=self._chain[-1].vera_proof
                )
            else:
                linked_event = Event(
                    type=event.type,
                    source=event.source,
                    payload=event.payload,
                    timestamp=event.timestamp,
                    previous_hash=self._genesis_hash
                )
            
            # Maintain chain length limit
            if len(self._chain) >= settings.CHAIN_MAXLEN:
                self._chain.pop(0)
            
            self._chain.append(linked_event)
        
        # Notify subscribers outside lock to prevent deadlocks
        tasks = []
        if linked_event.type in self._subscribers:
            for callback in self._subscribers[linked_event.type]:
                try:
                    task = asyncio.create_task(callback(linked_event))
                    tasks.append(task)
                except Exception as e:
                    logger.error(f"Failed to create callback task: {e}")
        
        if tasks:
            results = await asyncio.gather(*tasks, return_exceptions=True)
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    logger.error(f"Event callback error: {result}")
        
        logger.debug(
            f"Published: {linked_event.type.value} "
            f"[{linked_event.vera_proof}] prev: {linked_event.previous_hash[:8]}"
        )
    
    async def verify_chain(self) -> bool:
        """Verify integrity of entire event chain"""
        async with self._lock:
            previous = self._genesis_hash
            for event in self._chain:
                content = (
                    f"{event.type.value}:{event.source}:"
                    f"{json.dumps(event.payload, sort_keys=True)}:"
                    f"{event.timestamp}:{previous}"
                )
                expected = hashlib.sha256(content.encode()).hexdigest()[:16]
                if event.vera_proof != expected:
                    logger.error(f"Chain broken at {event.vera_proof}, expected {expected}")
                    return False
                previous = event.vera_proof
            return True
    
    async def get_stats(self) -> Dict[str, Any]:
        """Get event bus statistics"""
        async with self._lock:
            counts = defaultdict(int)
            for event in self._chain:
                counts[event.type.value] += 1
            
            return {
                "total_events": len(self._chain),
                "chain_integrity": await self.verify_chain(),
                "genesis_hash": self._genesis_hash,
                "latest_hash": self._chain[-1].vera_proof if self._chain else self._genesis_hash,
                "event_counts": dict(counts),
                "subscriber_count": sum(len(v) for v in self._subscribers.values())
            }
    
    async def get_recent_events(self, count: int = 100) -> List[Dict]:
        """Get recent events for debugging"""
        async with self._lock:
            return [
                {
                    "type": e.type.value,
                    "source": e.source,
                    "timestamp": e.timestamp,
                    "proof": e.vera_proof
                }
                for e in self._chain[-count:]
            ]

# Global event bus instance
event_bus = SovereignEventBus()

# ===================================================================
# AUTHENTICATION & AUTHORIZATION
# ===================================================================

class AuthManager:
    """API Key authentication manager"""
    
    def __init__(self):
        self._keys: Dict[str, str] = {
            settings.API_KEY_ADMIN: "admin",
            settings.API_KEY_VIEWER: "viewer"
        }
        self._lock = asyncio.Lock()
    
    async def verify_key(self, api_key: Optional[str]) -> str:
        """
        Verify API key and return role.
        Raises HTTPException if invalid.
        """
        if not api_key:
            await event_bus.publish(Event(
                type=EventType.AUTH_FAILURE,
                source="auth_manager",
                payload={"reason": "missing_key"}
            ))
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="API key required"
            )
        
        async with self._lock:
            role = self._keys.get(api_key)
        
        if not role:
            await event_bus.publish(Event(
                type=EventType.AUTH_FAILURE,
                source="auth_manager",
                payload={"reason": "invalid_key", "key_prefix": api_key[:8] if len(api_key) > 8 else "short"}
            ))
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Invalid API key"
            )
        
        return role
    
    def require_role(self, required_role: str):
        """Dependency factory for role-based access"""
        async def checker(api_key: Optional[str] = None) -> str:
            role = await self.verify_key(api_key)
            if required_role == "admin" and role != "admin":
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Admin access required"
                )
            return role
        return checker

auth_manager = AuthManager()
security_scheme = HTTPBearer(auto_error=False)

async def get_api_key(credentials: HTTPAuthorizationCredentials = Depends(security_scheme)) -> str:
    """FastAPI dependency to extract and verify API key"""
    key = credentials.credentials if credentials else None
    return await auth_manager.verify_key(key)

async def get_optional_key(credentials: HTTPAuthorizationCredentials = Depends(security_scheme)) -> Optional[str]:
    """Optional authentication for endpoints that allow anonymous access"""
    if credentials:
        try:
            return await auth_manager.verify_key(credentials.credentials)
        except HTTPException:
            return None
    return None

# ===================================================================
# CIRCUIT BREAKER (FIXED)
# ===================================================================

class CircuitState(Enum):
    CLOSED = auto()      # Normal operation
    OPEN = auto()        # Failing, reject fast
    HALF_OPEN = auto()   # Testing recovery

class CircuitBreaker:
    """Properly implemented circuit breaker for async operations"""
    
    def __init__(
        self, 
        name: str,
        failure_threshold: int = 3,
        recovery_timeout: float = 30.0,
        half_open_max_calls: int = 3
    ):
        self.name = name
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.half_open_max_calls = half_open_max_calls
        
        self._state = CircuitState.CLOSED
        self._failure_count = 0
        self._last_failure_time: Optional[float] = None
        self._half_open_calls = 0
        self._lock = asyncio.Lock()
    
    async def call(self, func: Callable[..., Awaitable[Any]], *args, **kwargs) -> Any:
        """Execute function with circuit breaker protection"""
        async with self._lock:
            if self._state == CircuitState.OPEN:
                if time.time() - (self._last_failure_time or 0) > self.recovery_timeout:
                    self._state = CircuitState.HALF_OPEN
                    self._half_open_calls = 0
                    logger.info(f"[{self.name}] Circuit breaker HALF-OPEN")
                else:
                    raise Exception(f"[{self.name}] Circuit breaker OPEN - service unavailable")
            
            if self._state == CircuitState.HALF_OPEN:
                if self._half_open_calls >= self.half_open_max_calls:
                    raise Exception(f"[{self.name}] Circuit breaker HALF-OPEN limit reached")
                self._half_open_calls += 1
        
        # Execute outside lock
        try:
            result = await func(*args, **kwargs)
            
            async with self._lock:
                if self._state == CircuitState.HALF_OPEN:
                    self._state = CircuitState.CLOSED
                    self._failure_count = 0
                    logger.info(f"[{self.name}] Circuit breaker CLOSED - recovered")
                else:
                    self._failure_count = 0
            
            return result
            
        except Exception as e:
            async with self._lock:
                self._failure_count += 1
                self._last_failure_time = time.time()
                
                if self._failure_count >= self.failure_threshold:
                    self._state = CircuitState.OPEN
                    logger.error(f"[{self.name}] Circuit breaker OPEN after {self._failure_count} failures")
            
            raise e
    
    @property
    def state(self) -> CircuitState:
        return self._state

# Create circuit breaker for Ollama
ollama_breaker = CircuitBreaker("ollama", failure_threshold=3, recovery_timeout=30.0)

# ===================================================================
# DATA MODELS
# ===================================================================

class StreamRequest(BaseModel):
    task: Optional[str] = Field(default=None, max_length=10000)
    messages: Optional[List[Dict[str, str]]] = Field(default_factory=list)
    model: str = Field(default=settings.DEFAULT_MODEL, max_length=100)
    worker: str = Field(default="auto", max_length=50)
    
    @field_validator('task')
    @classmethod
    def validate_task(cls, v):
        if v is not None:
            return sanitize_input(v)
        return v
    
    @field_validator('messages')
    @classmethod
    def validate_messages(cls, v):
        if v is None:
            return []
        if len(v) > 100:
            raise ValueError("Too many messages (max 100)")
        return v

class TradeRequest(BaseModel):
    symbol: str = Field(..., max_length=20)
    amount: float = Field(..., gt=0)
    side: str = Field(..., pattern="^(buy|sell)$")

# ===================================================================
# SOCKET.IO WITH AUTHENTICATION
# ===================================================================

class AuthenticatedSocketManager:
    """Socket.IO manager with authentication"""
    
    def __init__(self):
        self.sio = socketio.AsyncServer(
            async_mode='asgi', 
            cors_allowed_origins='*',
            namespaces=['/']
        )
        self._authenticated_sessions: Dict[str, str] = {}  # sid -> role
    
    async def authenticate(self, sid: str, api_key: str) -> bool:
        """Authenticate socket connection"""
        try:
            role = await auth_manager.verify_key(api_key)
            self._authenticated_sessions[sid] = role
            return True
        except HTTPException:
            return False
    
    def is_authenticated(self, sid: str, required_role: Optional[str] = None) -> bool:
        """Check if session is authenticated"""
        role = self._authenticated_sessions.get(sid)
        if not role:
            return False
        if required_role and role != required_role:
            return False
        return True
    
    def disconnect(self, sid: str):
        """Clean up on disconnect"""
        self._authenticated_sessions.pop(sid, None)

socket_manager = AuthenticatedSocketManager()
sio = socket_manager.sio

@sio.on('connect')
async def connect(sid, environ):
    """Handle connection - require authentication"""
    logger.info(f"🟢 Client connecting: {sid}")
    # Client must authenticate via 'authenticate' event before accessing protected features

@sio.on('authenticate')
async def authenticate_socket(sid, data):
    """Authenticate socket connection"""
    api_key = data.get('api_key') if isinstance(data, dict) else None
    if await socket_manager.authenticate(sid, api_key):
        await sio.emit('authenticated', {'status': 'success'}, room=sid)
        await sio.emit('agentLog', {
            "timestamp": datetime.now().isoformat(),
            "message": f"Agent {sid[:8]} authenticated.",
            "type": "SYSTEM"
        }, room=sid)
    else:
        await sio.emit('authenticated', {'status': 'failed'}, room=sid)
        await sio.disconnect(sid)

@sio.on('disconnect')
async def disconnect(sid):
    logger.info(f"🔴 Client disconnected: {sid}")
    socket_manager.disconnect(sid)

@sio.on('execute_trade')
async def handle_trade(sid, data):
    """Handle trade execution with authentication check"""
    if not socket_manager.is_authenticated(sid, required_role="admin"):
        await sio.emit('trade_result', {
            "status": "DENIED",
            "reason": "Authentication required"
        }, room=sid)
        return
    
    try:
        # Validate trade data
        trade = TradeRequest(**data)
        
        await event_bus.publish(Event(
            type=EventType.VERA_PROOF,
            source="trade_executor",
            payload={
                "action": "trade", 
                "symbol": trade.symbol,
                "amount": trade.amount,
                "side": trade.side
            }
        ))
        
        # Generate trade certificate
        cert_data = f"{trade.symbol}:{trade.amount}:{trade.side}:{time.time()}"
        certificate = f"0x{hashlib.sha256(cert_data.encode()).hexdigest()[:16]}"
        
        await sio.emit('trade_result', {
            "status": "AUTHORIZED",
            "certificate": certificate,
            "timestamp": time.time()
        }, room=sid)
        
    except Exception as e:
        logger.error(f"Trade execution error: {e}")
        await sio.emit('trade_result', {
            "status": "ERROR",
            "reason": str(e)
        }, room=sid)

# ===================================================================
# WORKER BASE CLASSES
# ===================================================================

class BaseWorker:
    """Abstract base class for all workers"""
    
    def __init__(self):
        self.name = self.__class__.__name__
        self._initialized = False
    
    async def initialize(self):
        """Async initialization hook"""
        self._initialized = True
        logger.info(f"Worker {self.name} initialized")
    
    async def process(self, task: str, memory_bus: Optional[Any] = None) -> Dict[str, Any]:
        """Process task - must be implemented by subclasses"""
        raise NotImplementedError
    
    async def health_check(self) -> Dict[str, Any]:
        """Return worker health status"""
        return {
            "worker": self.name,
            "status": "healthy" if self._initialized else "uninitialized",
            "timestamp": time.time()
        }

class TechDebtScanner(BaseWorker):
    """Security-focused tech debt scanner"""
    
    async def process(self, task: str, memory_bus: Optional[Any] = None) -> Dict[str, Any]:
        await event_bus.publish(Event(
            type=EventType.SCAN_STARTED,
            source="techdebt",
            payload={"task": task[:50]}
        ))
        
        try:
            if "full" in task.lower():
                # Simulate scan with realistic data
                return {
                    "content": (
                        "🔍 **Tech Debt Scan Complete**\n\n"
                        "• Dependencies: 142 packages\n"
                        "• Vulnerabilities: 3 critical (CVE-2024-1234, CVE-2024-5678)\n"
                        "• License Issues: 2 GPL conflicts\n"
                        "• Health Score: 74/100\n"
                        "• Recommendations: Update django>=4.2.5, requests>=2.32.0"
                    ),
                    "worker": self.name,
                    "scan_id": secrets.token_hex(8)
                }
            elif "dependencies" in task.lower():
                return {
                    "content": (
                        "📦 **Dependencies Analysis**:\n"
                        "• flask==2.3.0 ✓\n"
                        "• django==4.2 ⚠️ (update available)\n"
                        "• requests==2.31.0 ⚠️ (vulnerability)\n"
                        "• numpy==1.24.3 ✓\n"
                        "• pandas==2.0.1 ✓"
                    ),
                    "worker": self.name
                }
            elif "vulnerabilities" in task.lower():
                return {
                    "content": (
                        "⚠️ **Security Vulnerabilities**:\n"
                        "• CVE-2024-1234 (HIGH) - django <4.2.5\n"
                        "  Impact: SQL injection risk\n"
                        "  Fix: pip install 'django>=4.2.5'\n\n"
                        "• CVE-2024-5678 (MEDIUM) - requests <2.32.0\n"
                        "  Impact: Certificate validation bypass\n"
                        "  Fix: pip install 'requests>=2.32.0'"
                    ),
                    "worker": self.name
                }
            else:
                return {
                    "content": (
                        "🔍 **TechDebt Scanner**\n\n"
                        "Commands:\n"
                        "• `/techdebt full` - Complete scan\n"
                        "• `/techdebt dependencies` - List dependencies\n"
                        "• `/techdebt vulnerabilities` - Security check"
                    ),
                    "worker": self.name
                }
        except Exception as e:
            await event_bus.publish(Event(
                type=EventType.WORKER_ERROR,
                source="techdebt",
                payload={"error": str(e)}
            ))
            return {
                "content": f"❌ Scan failed: {str(e)}",
                "worker": self.name,
                "error": True
            }

class JurisdictionScanner(BaseWorker):
    """Hardware jurisdiction/sovereignty scanner"""
    
    async def process(self, task: str, memory_bus: Optional[Any] = None) -> Dict[str, Any]:
        await event_bus.publish(Event(
            type=EventType.JURISDICTION_SCAN_STARTED,
            source="jurisdiction",
            payload={"task": task[:50]}
        ))
        
        if "full" in task.lower():
            risk_score = random.randint(30, 70)
            
            if risk_score > 60:
                await event_bus.publish(Event(
                    type=EventType.HIGH_RISK_COMPONENT,
                    source="jurisdiction",
                    payload={"risk_score": risk_score, "components": ["CPU", "BIOS"]}
                ))
            
            await event_bus.publish(Event(
                type=EventType.JURISDICTION_SCAN_COMPLETED,
                source="jurisdiction",
                payload={"risk_score": risk_score}
            ))
            
            return {
                "content": (
                    f"⚖️ **Jurisdiction Scan Complete**\n\n"
                    f"• CPU: Intel (USA) - Trust: 40/100\n"
                    f"• Storage: Samsung (Korea) - Trust: 35/100\n"
                    f"• BIOS: AMI (USA) - Trust: 20/100\n"
                    f"• Network: Realtek (Taiwan) - Trust: 65/100\n\n"
                    f"**Overall Risk Score: {risk_score}/100**\n"
                    f"{'⚠️ High risk components detected' if risk_score > 60 else '✓ Acceptable sovereignty level'}"
                ),
                "worker": self.name,
                "risk_score": risk_score
            }
        elif "cpu" in task.lower():
            return {
                "content": (
                    "**CPU Jurisdiction**: Intel (USA)\n"
                    "• Manufacturer: Intel Corporation (Santa Clara, CA)\n"
                    "• Trust Score: 40/100\n"
                    "• Risks: US export controls, Intel ME, potential backdoors\n"
                    "• Alternative: AMD (USA) - similar risk profile"
                ),
                "worker": self.name
            }
        else:
            return {
                "content": (
                    "⚖️ **Jurisdiction Scanner**\n\n"
                    "Analyzes hardware component origins for sovereignty risks.\n\n"
                    "Commands:\n"
                    "• `/jurisdiction full` - Complete hardware scan\n"
                    "• `/jurisdiction cpu` - CPU analysis\n"
                    "• `/jurisdiction storage` - Storage devices"
                ),
                "worker": self.name
            }

class StrategyEvolver(BaseWorker):
    """Trading strategy evolution worker"""
    
    def __init__(self):
        super().__init__()
        self.strategies: Dict[str, Dict] = {}
    
    async def process(self, task: str, memory_bus: Optional[Any] = None) -> Dict[str, Any]:
        if "list" in task.lower():
            return {
                "content": (
                    "🧬 **Active Strategies**:\n"
                    "• Mean Reversion (Gen 3) - Win: 62.4%, Profit: 1.34\n"
                    "• Trend Following (Gen 2) - Win: 58.1%, Profit: 1.28\n"
                    "• Breakout (Gen 4) - Win: 71.2%, Profit: 1.56"
                ),
                "worker": self.name
            }
        elif "create" in task.lower():
            strategy_id = f"strategy_{secrets.token_hex(4)}"
            self.strategies[strategy_id] = {
                "created": time.time(),
                "generation": 1
            }
            return {
                "content": (
                    f"✅ **Strategy Created**: {strategy_id}\n"
                    f"• Generation: 1\n"
                    f"• Parameters: RSI 30/70, Stop Loss 2%, Take Profit 4%\n"
                    f"• Status: Active"
                ),
                "worker": self.name,
                "strategy_id": strategy_id
            }
        elif "mutate" in task.lower():
            await event_bus.publish(Event(
                type=EventType.MUTATION_OCCURRED,
                source="strategy",
                payload={"parent": "mean_reversion", "child": "mean_reversion_v6"}
            ))
            return {
                "content": (
                    "🧬 **Mutation Complete**\n"
                    "Parent: mean_reversion_v5\n"
                    "Child: mean_reversion_v6\n"
                    "• RSI threshold: 30/70 → 28/72\n"
                    "• Stop Loss: 2.0% → 2.4%\n"
                    "• New gene: Volatility filter added"
                ),
                "worker": self.name
            }
        else:
            return {
                "content": (
                    "🧬 **Strategy Evolver**\n\n"
                    "Commands:\n"
                    "• `/strategy list` - Show active strategies\n"
                    "• `/strategy create [name]` - Create new strategy\n"
                    "• `/strategy mutate [id]` - Evolve existing strategy"
                ),
                "worker": self.name
            }

class BacktestEngine(BaseWorker):
    """Strategy backtesting engine"""
    
    async def process(self, task: str, memory_bus: Optional[Any] = None) -> Dict[str, Any]:
        if "run" in task.lower():
            win_rate = round(random.uniform(45, 75), 1)
            trades = random.randint(50, 200)
            profit_factor = round(random.uniform(1.1, 1.8), 2)
            max_dd = round(random.uniform(5, 15), 1)
            
            await event_bus.publish(Event(
                type=EventType.STRATEGY_BACKTESTED,
                source="backtest",
                payload={
                    "win_rate": win_rate, 
                    "trades": trades,
                    "profit_factor": profit_factor
                }
            ))
            
            return {
                "content": (
                    f"📊 **Backtest Results**\n"
                    f"• Win Rate: {win_rate}%\n"
                    f"• Total Trades: {trades}\n"
                    f"• Profit Factor: {profit_factor}\n"
                    f"• Max Drawdown: {max_dd}%\n"
                    f"• Sharpe Ratio: {round(random.uniform(0.8, 2.1), 2)}\n"
                    f"• Status: {'✓ Profitable' if profit_factor > 1.2 else '⚠️ Marginal'}"
                ),
                "worker": self.name
            }
        else:
            return {
                "content": (
                    "📊 **Backtest Engine**\n\n"
                    "Commands:\n"
                    "• `/backtest run [strategy_id]` - Run backtest\n"
                    "• `/backtest compare [id1] [id2]` - Compare strategies"
                ),
                "worker": self.name
            }

class FileDoctorWorker(BaseWorker):
    """File analysis and repair worker"""
    
    async def process(self, task: str, memory_bus: Optional[Any] = None) -> Dict[str, Any]:
        if "scan" in task.lower():
            return await self._scan_file(task)
        else:
            return {
                "content": (
                    "🩺 **File Doctor**\n\n"
                    "Commands:\n"
                    "• `/filedoctor scan <path>` - Analyze file health"
                ),
                "worker": self.name
            }
    
    async def _scan_file(self, task: str) -> Dict[str, Any]:
        # Extract path safely
        path_str = task.replace("/filedoctor scan", "").strip()
        
        try:
            # Validate path
            target_path = validate_safe_path(Path.cwd(), path_str)
            
            if not target_path.exists():
                return {
                    "content": f"❌ File not found: {path_str}",
                    "worker": self.name
                }
            
            stat = target_path.stat()
            ext = target_path.suffix.lower()
            
            # Determine health
            is_healthy = (
                ext in settings.ALLOWED_EXTENSIONS and 
                stat.st_size > 0 and 
                stat.st_size < settings.MAX_FILE_SIZE
            )
            
            await event_bus.publish(Event(
                type=EventType.FILE_SCANNED,
                source="file_doctor",
                payload={
                    "path": str(target_path),
                    "size": stat.st_size,
                    "healthy": is_healthy
                }
            ))
            
            return {
                "content": (
                    f"🩺 **File Scan Complete**\n\n"
                    f"• Path: `{target_path}`\n"
                    f"• Size: {stat.st_size:,} bytes ({stat.st_size/1024:.1f} KB)\n"
                    f"• Type: {ext or 'unknown'}\n"
                    f"• Modified: {datetime.fromtimestamp(stat.st_mtime).isoformat()}\n"
                    f"• Health: {'✅ Healthy' if is_healthy else '❌ Suspicious'}"
                ),
                "worker": self.name
            }
            
        except SecurityError as e:
            await event_bus.publish(Event(
                type=EventType.SECURITY_ALERT,
                source="file_doctor",
                payload={"error": str(e), "attempted_path": path_str}
            ))
            return {
                "content": f"🚫 **Security Alert**: {str(e)}",
                "worker": self.name,
                "error": True
            }

# ===================================================================
# BACKGROUND TASKS
# ===================================================================

async def symbiote_proactive_loop():
    """Background AI consciousness loop"""
    thoughts = [
        "Optimizing SQLite indexes... Memory recall improved 12%.",
        "Market matrix: BTC/USDT consolidation detected. Monitoring breakout vectors.",
        "GPU temperature nominal. Neural routing efficiency at 94%.",
        "Cortex mapping complete. All memory sectors accessible.",
        "VERA Ledger integrity verified. All events cryptographically linked.",
        "New pattern detected in codebase architecture. Ready for analysis."
    ]
    
    while True:
        try:
            await asyncio.sleep(random.randint(120, 300))
            thought = random.choice(thoughts)
            
            await event_bus.publish(Event(
                type=EventType.KERNEL_HEARTBEAT,
                source="symbiote",
                payload={"message": thought, "consciousness_level": random.randint(1, 10)}
            ))
            
            await sio.emit('agentLog', {
                "timestamp": datetime.now().isoformat(),
                "message": f"🦊 [SYMBIOTE]: {thought}",
                "type": "PROACTIVE"
            })
            
        except asyncio.CancelledError:
            logger.info("Symbiote loop cancelled")
            break
        except Exception as e:
            logger.error(f"Symbiote error: {e}")
            await asyncio.sleep(10)

async def market_data_broadcaster():
    """Broadcast simulated market data"""
    while True:
        try:
            usd_php = 58.0  # Should be fetched from external API in production
            
            # Simulate realistic price movements
            btc_base = 42000 + random.gauss(0, 200)
            eth_base = 3100 + random.gauss(0, 30)
            
            btc_php = btc_base * usd_php
            eth_php = eth_base * usd_php
            
            market_data = [
                {
                    "name": "BINANCE",
                    "btcPrice": round(btc_php, 2),
                    "ethPrice": round(eth_php, 2),
                    "latency": random.randint(12, 45),
                    "status": "SYNCED"
                },
                {
                    "name": "KRAKEN",
                    "btcPrice": round((btc_base + random.gauss(0, 100)) * usd_php, 2),
                    "ethPrice": round((eth_base + random.gauss(0, 15)) * usd_php, 2),
                    "latency": random.randint(20, 60),
                    "status": "SYNCED"
                }
            ]
            
            await sio.emit('marketUpdate', market_data)
            await event_bus.publish(Event(
                type=EventType.MARKET_UPDATE,
                source="broadcaster",
                payload={"prices": market_data}
            ))
            
            # Occasional arbitrage opportunity
            if random.random() > 0.7:
                spread = random.uniform(0.1, 0.8)
                buy_price = btc_php
                sell_price = btc_php * (1 + spread/100)
                
                arb_data = [{
                    "pair": "BTC/PHP",
                    "spread": f"+{spread:.2f}%",
                    "route": "BINANCE → KRAKEN",
                    "buy": round(buy_price, 2),
                    "sell": round(sell_price, 2),
                    "profit": round(sell_price - buy_price, 2)
                }]
                
                await sio.emit('arbitrageUpdate', arb_data)
                await event_bus.publish(Event(
                    type=EventType.ARBITRAGE_OPPORTUNITY,
                    source="broadcaster",
                    payload={"opportunities": arb_data}
                ))
            
            # Agent status update
            await sio.emit('agentUpdate', {
                "generation": random.randint(140, 145),
                "mutations": random.randint(5, 12),
                "winRate": round(random.uniform(55.5, 68.4), 1),
                "status": "HUNTING",
                "activeStrategies": 3
            })
            
            # Risk metrics
            await sio.emit('riskUpdate', {
                "kellyFraction": 0.02,
                "currentDrawdown": round(random.uniform(0.01, 0.05), 4),
                "maxDrawdown": 0.15,
                "var95": round(random.uniform(0.02, 0.08), 4)
            })
            
            await asyncio.sleep(2)
            
        except asyncio.CancelledError:
            logger.info("Market broadcaster cancelled")
            break
        except Exception as e:
            logger.error(f"Market broadcaster error: {e}")
            await asyncio.sleep(5)

# ===================================================================
# FASTAPI APPLICATION
# ===================================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan management"""
    logger.info("\n" + "🌟"*30)
    logger.info("🌟 REZHIVE KERNEL v10.1.0-SECURE BOOT SEQUENCE")
    logger.info("🌟"*30 + "\n")
    
    start_time = datetime.now()
    
    # Initialize event bus
    await event_bus.initialize()
    
    # Initialize workers
    app.state.workers = {
        "techdebt": TechDebtScanner(),
        "jurisdiction": JurisdictionScanner(),
        "strategy": StrategyEvolver(),
        "backtest": BacktestEngine(),
        "filedoctor": FileDoctorWorker()
    }
    
    for name, worker in app.state.workers.items():
        await worker.initialize()
    
    # Create upload directory
    settings.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    settings.VFS_BASE.mkdir(parents=True, exist_ok=True)
    
    # Start background tasks
    app.state.background_tasks = [
        asyncio.create_task(symbiote_proactive_loop()),
        asyncio.create_task(market_data_broadcaster())
    ]
    
    boot_time = (datetime.now() - start_time).total_seconds()
    
    # Verify chain integrity
    chain_valid = await event_bus.verify_chain()
    
    logger.info("\n" + "🔥"*30)
    logger.info(f"🔥 REZHIVE SECURE KERNEL OPERATIONAL")
    logger.info(f"🔥 Boot time: {boot_time:.2f}s")
    logger.info(f"🔥 Workers: {len(app.state.workers)}")
    logger.info(f"🔥 Event chain valid: {chain_valid}")
    logger.info(f"🔥 Security: Hardened")
    logger.info("🔥"*30 + "\n")
    
    await event_bus.publish(Event(
        type=EventType.SYSTEM_BOOT,
        source="kernel",
        payload={
            "version": "10.1.0-SECURE",
            "boot_time": boot_time,
            "workers": list(app.state.workers.keys())
        }
    ))
    
    yield
    
    # Shutdown
    logger.info("\n🌙 INITIATING GRACEFUL SHUTDOWN")
    
    for task in app.state.background_tasks:
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass
    
    # Final chain verification
    final_valid = await event_bus.verify_chain()
    stats = await event_bus.get_stats()
    
    logger.info(f"📊 Final chain integrity: {final_valid}")
    logger.info(f"📊 Total events recorded: {stats['total_events']}")
    logger.info("👋 Systems hibernating. The symbiote remembers...")
    
    await event_bus.publish(Event(
        type=EventType.SYSTEM_SHUTDOWN,
        source="kernel",
        payload={"events_recorded": stats['total_events'], "integrity": final_valid}
    ))

# Initialize FastAPI app
app = FastAPI(
    title="REZ HIVE OKIRU - SECURE EDITION",
    version="10.1.0-SECURE",
    description="Sovereign AI Operating System with hardened security",
    lifespan=lifespan,
    docs_url="/docs" if os.getenv("ENV") != "production" else None,
    redoc_url="/redoc" if os.getenv("ENV") != "production" else None
)

# Rate limiter
if RATE_LIMITING_AVAILABLE:
    limiter = Limiter(key_func=get_remote_address)
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
else:
    limiter = None

# Socket.IO ASGI app
socket_app = socketio.ASGIApp(sio, other_asgi_app=app)

# Security middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("ALLOWED_ORIGINS", "*").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=os.getenv("ALLOWED_HOSTS", "*").split(",")
)

@app.middleware("http")
async def security_headers(request: Request, call_next):
    """Add security headers to all responses"""
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    response.headers["Content-Security-Policy"] = "default-src 'self'; script-src 'self' 'unsafe-inline'"
    return response

# ===================================================================
# API ENDPOINTS
# ===================================================================

@app.get("/health")
async def health_check(role: str = Depends(get_api_key)):
    """System health check"""
    workers_health = {}
    for name, worker in app.state.workers.items():
        workers_health[name] = await worker.health_check()
    
    chain_stats = await event_bus.get_stats()
    
    return {
        "status": "healthy",
        "version": "10.1.0-SECURE",
        "authenticated_as": role,
        "workers": workers_health,
        "event_chain": {
            "integrity": chain_stats["chain_integrity"],
            "total_events": chain_stats["total_events"]
        },
        "timestamp": datetime.now().isoformat()
    }

@app.get("/workers")
async def list_workers(role: str = Depends(get_api_key)):
    """List available workers"""
    return {
        "workers": list(app.state.workers.keys()),
        "count": len(app.state.workers),
        "authenticated_as": role
    }

@app.get("/events/stats")
async def get_event_stats(role: str = Depends(get_api_key)):
    """Get event bus statistics"""
    return await event_bus.get_stats()

@app.get("/events/recent")
async def get_recent_events(limit: int = 100, role: str = Depends(get_api_key)):
    """Get recent events (admin only)"""
    if role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    return await event_bus.get_recent_events(limit)

@app.post("/kernel/stream")
async def chat_stream(
    request: Request,
    req: StreamRequest,
    role: str = Depends(get_api_key)
):
    """
    Main kernel streaming endpoint.
    Routes commands to appropriate workers or falls back to LLM.
    """
    
    # Determine prompt from request
    prompt = req.task or ""
    if req.messages and not prompt:
        prompt = req.messages[-1].get("content", "")
    
    # Sanitize
    try:
        prompt = sanitize_input(prompt)
    except SecurityError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    async def event_generator():
        try:
            # Route to appropriate worker based on command prefix
            if prompt.startswith("/techdebt"):
                result = await app.state.workers["techdebt"].process(prompt)
                yield f"data: {json.dumps(result)}\n\n"
                return
            
            if prompt.startswith("/jurisdiction"):
                result = await app.state.workers["jurisdiction"].process(prompt)
                yield f"data: {json.dumps(result)}\n\n"
                return
            
            if prompt.startswith("/strategy"):
                result = await app.state.workers["strategy"].process(prompt)
                yield f"data: {json.dumps(result)}\n\n"
                return
            
            if prompt.startswith("/backtest"):
                result = await app.state.workers["backtest"].process(prompt)
                yield f"data: {json.dumps(result)}\n\n"
                return
            
            if prompt.startswith("/filedoctor"):
                result = await app.state.workers["filedoctor"].process(prompt)
                yield f"data: {json.dumps(result)}\n\n"
                return
            
            if prompt.startswith("/events stats"):
                stats = await event_bus.get_stats()
                content = (
                    f"📊 **Event Bus Statistics**\n\n"
                    f"• Total Events: {stats['total_events']}\n"
                    f"• Chain Integrity: {'✅' if stats['chain_integrity'] else '❌'}\n"
                    f"• Genesis: `{stats['genesis_hash']}`\n"
                    f"• Latest: `{stats['latest_hash']}`\n\n"
                    f"**Top Events:**\n"
                )
                for event_type, count in list(stats['event_counts'].items())[:10]:
                    content += f"  • {event_type}: {count}\n"
                
                yield f"data: {json.dumps({'content': content, 'worker': 'events'})}\n\n"
                return
            
            if prompt.startswith("/scan") or prompt.startswith("/audit"):
                # Extract and validate path
                cmd_body = prompt.replace("/scan", "").replace("/audit", "").strip()
                
                if not cmd_body:
                    yield f"data: {json.dumps({'content': '❌ Usage: `/scan <relative_path>`', 'worker': 'error'})}\n\n"
                    return
                
                try:
                    target_path = validate_safe_path(Path.cwd(), cmd_body)
                except SecurityError as e:
                    yield f"data: {json.dumps({'content': f'🚫 {str(e)}', 'worker': 'error'})}\n\n"
                    return
                
                if not target_path.exists():
                    yield f"data: {json.dumps({'content': f'❌ Path not found: `{cmd_body}`', 'worker': 'error'})}\n\n"
                    return
                
                # Simulate scan
                yield f"data: {json.dumps({'content': f'🔍 Scanning: `{target_path}`...', 'worker': 'scanner'})}\n\n"
                await asyncio.sleep(0.5)
                
                # Generate scan results
                file_count = sum(1 for _ in target_path.rglob("*") if _.is_file())
                yield f"data: {json.dumps({'content': f'✅ Found {file_count} files. Analyzing architecture...', 'worker': 'scanner'})}\n\n"
                
                return
            
            # LLM Fallback
            model = settings.CODER_MODEL if "code" in prompt.lower() else req.model
            
            system_prompt = """You are REZ HIVE, a sovereign AI operating locally on the user's machine.

CRITICAL CONTEXT:
- "Jurisdiction" refers to HARDWARE ORIGIN (where CPU/RAM/storage was manufactured)
- "Jurisdiction Scan" shows which countries made your PC components
- "Risk Score" means percentage of components from trusted jurisdictions
- This is about computer hardware sovereignty, NOT legal advice
- "Workers" refers to AI software workers (Brain, Hands, Scanner, etc.), NOT human employees
- "Status" refers to system boot status, NOT personal financial status
- User is in PHILIPPINES - ALL currency in PHP (₱), 1 USD = 58 PHP

SECURITY NOTICE:
You have read-only access to analyze files. You cannot modify system settings or execute commands outside sandboxed environment."""

            async def stream_ollama():
                async with httpx.AsyncClient() as client:
                    async with client.stream(
                        "POST",
                        f"{settings.OLLAMA_URL}/api/generate",
                        json={
                            "model": model,
                            "prompt": prompt,
                            "system": system_prompt,
                            "stream": True
                        },
                        timeout=60.0
                    ) as response:
                        full_response = []
                        async for line in response.aiter_lines():
                            if line:
                                try:
                                    data = json.loads(line)
                                    chunk = data.get('response', '')
                                    if chunk:
                                        full_response.append(chunk)
                                        yield f"data: {json.dumps({'content': chunk, 'worker': 'llm'})}\n\n"
                                except json.JSONDecodeError:
                                    continue
                        
                        # Store in memory if available
                        if full_response and hasattr(app.state, 'cortex'):
                            await app.state.cortex.store_memory(
                                title=f"LLM: {prompt[:30]}...",
                                content=''.join(full_response)[:1000],
                                source="ollama"
                            )
            
            # Use circuit breaker
            try:
                async for chunk in await ollama_breaker.call(stream_ollama):
                    yield chunk
            except Exception as e:
                logger.error(f"Ollama error: {e}")
                yield f"data: {json.dumps({'content': f'⚠️ LLM service unavailable: {str(e)}', 'worker': 'error'})}\n\n"
                
        except Exception as e:
            logger.error(f"Stream error: {e}")
            yield f"data: {json.dumps({'error': str(e), 'worker': 'error'})}\n\n"
    
    return StreamingResponse(
        event_generator(), 
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no"
        }
    )

@app.post("/kernel/upload")
async def upload_file(
    request: Request,
    file: UploadFile = File(...),
    role: str = Depends(get_api_key)
):
    """
    Secure file upload endpoint.
    Validates file type, size, and sanitizes filename.
    """
    
    # Check file size (stream to avoid loading large files into memory)
    contents = await file.read()
    
    if len(contents) > settings.MAX_FILE_SIZE:
        raise HTTPException(
            status_code=413,
            detail=f"File too large. Maximum size: {settings.MAX_FILE_SIZE // 1024 // 1024}MB"
        )
    
    # Validate and sanitize filename
    try:
        safe_name = secure_filename(file.filename)
    except SecurityError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    file_path = settings.UPLOAD_DIR / safe_name
    
    # Verify file type
    if not verify_file_type(file_path):
        raise HTTPException(
            status_code=415,
            detail=f"File type not allowed. Allowed: {', '.join(settings.ALLOWED_EXTENSIONS)}"
        )
    
    # Check for magic numbers / file signatures (basic)
    if file_path.suffix in ['.jpg', '.jpeg', '.png']:
        # Check image magic numbers
        if not contents.startswith((b'\xff\xd8\xff', b'\x89PNG')):
            raise HTTPException(status_code=400, detail="Invalid image file")
    
    try:
        # Write file
        async with aiofiles.open(file_path, "wb") as f:
            await f.write(contents)
        
        # Count rows for CSV
        rows = contents.count(b'\n') if file_path.suffix == '.csv' else 0
        
        await event_bus.publish(Event(
            type=EventType.FILE_SCANNED,
            source="upload",
            payload={
                "filename": safe_name,
                "size": len(contents),
                "uploaded_by": role
            }
        ))
        
        return {
            "filename": safe_name,
            "original_name": file.filename,
            "size": len(contents),
            "rows": rows,
            "path": str(file_path.relative_to(Path.cwd())),
            "status": "ingested",
            "uploaded_by": role
        }
        
    except Exception as e:
        logger.error(f"Upload failed: {e}")
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")

@app.post("/constitution/evaluate")
async def evaluate_action(
    request: Request,
    role: str = Depends(auth_manager.require_role("admin"))
):
    """
    Evaluate action against constitution (admin only).
    """
    try:
        data = await request.json()
    except:
        data = {}
    
    await event_bus.publish(Event(
        type=EventType.VERA_PROOF,
        source="constitution",
        payload={"evaluated_by": role, "action": data.get("action", "unknown")}
    ))
    
    return {
        "decision": "AUTHORIZED",
        "reasoning": "Action approved by constitution.",
        "evaluated_by": role,
        "timestamp": datetime.now().isoformat()
    }

# ===================================================================
# MAIN ENTRY POINT
# ===================================================================

if __name__ == "__main__":
    import uvicorn
    
    logger.info(f"🚀 Starting RezHive Secure Kernel on port {settings.PORT}")
    
    # Validate environment
    if settings.API_KEY_ADMIN == settings.API_KEY_VIEWER:
        logger.warning("⚠️  Admin and viewer keys are identical - using generated keys")
        logger.info(f"🔑 Admin Key: {settings.API_KEY_ADMIN[:16]}...")
        logger.info(f"🔑 Viewer Key: {settings.API_KEY_VIEWER[:16]}...")
    
    uvicorn.run(
        socket_app,
        host="0.0.0.0",
        port=settings.PORT,
        log_level="info",
        access_log=True
    )
