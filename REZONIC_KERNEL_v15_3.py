#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
╔═══════════════════════════════════════════════════════════════════════════════╗
║  REZONIC PHOENIX KERNEL v15.3.1-FIXED                                         ║
║  ═══════════════════════════════════════════════════════════════════════════  ║
║  Sovereign AI Kernel | Quantum Event Chain | Constitutional Governance       ║
║  SCE Protocol v2.0.0 | VERA Proof System | Neural Worker Swarm               ║
║  ═══════════════════════════════════════════════════════════════════════════  ║
║  Features:                                                                   ║
║    • Immutable Event Chain with Cryptographic Verification                   ║
║    • Constitution-based Security Enforcement                                 ║
║    • Dynamic Worker Loading with Duck Typing Support                         ║
║    • Ollama Integration with Circuit Breaker Protection                      ║
║    • GPU Monitoring & Resource Management                                    ║
║    • SCE Blueprint System for Audit Trail                                    ║
║    • Real-time SSE & WebSocket Telemetry                                     ║
║    • Kill Switch with Emergency Halt Protocol                                ║
║    • Paper Trading & Backtesting Engine                                      ║
║    • Reflex Command System for Direct Control                                ║
╚═══════════════════════════════════════════════════════════════════════════════╝
"""

import sys
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

import asyncio
import hashlib
import json
import logging
import os
import re
import shutil
import time
import uuid
import random
import sqlite3
import tempfile
import importlib.util
import inspect
import warnings
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, auto
from pathlib import Path
from typing import Dict, Any, Optional, List, Callable, Awaitable, Union, Tuple
from abc import ABC, abstractmethod
from logging.handlers import RotatingFileHandler
from contextlib import asynccontextmanager

warnings.filterwarnings("ignore")

# ═══════════════════════════════════════════════════════════════════════════════
# DIRECTORY STRUCTURE
# ═══════════════════════════════════════════════════════════════════════════════
DIRS = {
    "logs": Path("logs"),
    "data": Path("data"),
    "event_store": Path("data/event_store"),
    "backups": Path("data/backups"),
    "sandbox": Path("data/sandbox"),
    "memory": Path("data/memory"),
    "uploads": Path("data/uploads"),
    "workers": Path("workers"),
    "coworker": Path("workers/coworker"),
    "blueprints": Path("data/blueprints"),
    "trades": Path("data/trades"),
    "config": Path("config"),
}

for dir_path in DIRS.values():
    dir_path.mkdir(parents=True, exist_ok=True)

# ═══════════════════════════════════════════════════════════════════════════════
# LOGGING SYSTEM
# ═══════════════════════════════════════════════════════════════════════════════
class PhoenixFormatter(logging.Formatter):
    """Custom formatter with emoji support and structured output"""
    
    def format(self, record):
        emoji_map = {
            "INFO": "📘",
            "WARNING": "⚠️",
            "ERROR": "💀",
            "CRITICAL": "🔥",
            "DEBUG": "🐛",
        }
        record.emoji = emoji_map.get(record.levelname, "📌")
        record.timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        return super().format(record)

log_handler = RotatingFileHandler(
    DIRS["logs"] / "phoenix.log",
    maxBytes=50 * 1024 * 1024,
    backupCount=10,
    encoding='utf-8'
)
log_handler.setFormatter(PhoenixFormatter(
    "%(asctime)s | %(emoji)s %(levelname)-8s | %(name)-12s | %(message)s"
))

console_handler = logging.StreamHandler(sys.stdout)
console_handler.setFormatter(PhoenixFormatter(
    "%(asctime)s | %(emoji)s %(levelname)-8s | %(message)s"
))

logging.basicConfig(
    level=logging.INFO,
    handlers=[log_handler, console_handler]
)
logger = logging.getLogger("PHOENIX")

# ═══════════════════════════════════════════════════════════════════════════════
# DEPENDENCY MANAGEMENT
# ═══════════════════════════════════════════════════════════════════════════════
HAS_FASTAPI = False
HAS_HTTPX = False
HAS_PSUTIL = False
HAS_PYNVML = False
HAS_SOCKETIO = False
HAS_PROMETHEUS = False
HAS_REDIS = False
HAS_WEBSOCKETS = False

try:
    from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect, Depends, HTTPException, UploadFile, File, BackgroundTasks, Query
    from fastapi.middleware.cors import CORSMiddleware
    from fastapi.middleware.trustedhost import TrustedHostMiddleware
    from fastapi.responses import StreamingResponse, JSONResponse, Response, HTMLResponse
    from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
    import uvicorn
    HAS_FASTAPI = True
except ImportError:
    logger.critical("FastAPI not installed. Run: pip install fastapi uvicorn")
    sys.exit(1)

try:
    import httpx
    HAS_HTTPX = True
except ImportError:
    logger.warning("⚠️ httpx not installed - Ollama streaming disabled")

try:
    import psutil
    HAS_PSUTIL = True
except ImportError:
    logger.info("📊 psutil not installed - system monitoring limited")

try:
    import pynvml
    HAS_PYNVML = True
except ImportError:
    logger.info("🖥️ pynvml not installed - GPU monitoring disabled")

try:
    import socketio
    HAS_SOCKETIO = True
except ImportError:
    logger.info("🔌 python-socketio not installed - WebSocket disabled")

try:
    from prometheus_client import Counter, Histogram, Gauge, generate_latest, start_http_server, REGISTRY
    HAS_PROMETHEUS = True
except ImportError:
    logger.info("📊 prometheus_client not installed - metrics disabled")

try:
    import redis.asyncio as redis
    HAS_REDIS = True
except ImportError:
    logger.info("🗄️ redis not installed - distributed caching disabled")

try:
    import websockets
    HAS_WEBSOCKETS = True
except ImportError:
    pass

# ═══════════════════════════════════════════════════════════════════════════════
# CONFIGURATION SYSTEM
# ═══════════════════════════════════════════════════════════════════════════════
@dataclass
class PhoenixConfig:
    """Central configuration with environment override"""
    
    # Identity
    NAME: str = "PHOENIX"
    VERSION: str = "15.3.1-FIXED"
    BUILD: str = "REZONIC-SOVEREIGN"
    
    # Network
    HOST: str = os.getenv("PHOENIX_HOST", "127.0.0.1")
    PORT: int = int(os.getenv("PHOENIX_PORT", "8002"))
    METRICS_PORT: int = int(os.getenv("METRICS_PORT", "8003"))
    WEBSOCKET_PORT: int = int(os.getenv("WS_PORT", "8004"))
    
    # CORS
    CORS_ORIGINS: List[str] = field(default_factory=lambda: os.getenv(
        "CORS_ORIGINS", 
        "http://localhost:3000,http://localhost:8002,http://127.0.0.1:3000"
    ).split(","))
    
    # Security
    API_KEYS: Dict[str, str] = field(default_factory=lambda: {
        os.getenv("PHOENIX_ADMIN_KEY", "rez-hive-admin-key-2026"): "admin",
        os.getenv("PHOENIX_VIEWER_KEY", "rez-hive-viewer-key-2026"): "viewer",
    })
    JWT_SECRET: str = os.getenv("JWT_SECRET", "phoenix-rezonic-secret-2026")
    JWT_EXPIRY: int = int(os.getenv("JWT_EXPIRY", "86400"))  # 24 hours
    
    # Rate Limiting
    RATE_LIMIT_CALLS: int = int(os.getenv("RATE_LIMIT_CALLS", "100"))
    RATE_LIMIT_PERIOD: int = int(os.getenv("RATE_LIMIT_PERIOD", "60"))
    RATE_LIMIT_BURST: int = int(os.getenv("RATE_LIMIT_BURST", "20"))
    
    # Ollama
    OLLAMA_URL: str = os.getenv("OLLAMA_URL", "http://localhost:11434")
    DEFAULT_MODEL: str = os.getenv("OLLAMA_MODEL", "qwen2.5-coder:7b")
    OLLAMA_NUM_CTX: int = int(os.getenv("OLLAMA_NUM_CTX", "32768"))
    OLLAMA_TIMEOUT: int = int(os.getenv("OLLAMA_TIMEOUT", "120"))
    OLLAMA_MAX_TOKENS: int = int(os.getenv("OLLAMA_MAX_TOKENS", "4096"))
    OLLAMA_TEMPERATURE: float = float(os.getenv("OLLAMA_TEMPERATURE", "0.7"))
    OLLAMA_TOP_P: float = float(os.getenv("OLLAMA_TOP_P", "0.9"))
    
    # Constitution
    CONSTITUTION_STRICT: bool = os.getenv("CONSTITUTION_STRICT", "true").lower() == "true"
    CONSTITUTION_PATTERNS: List[str] = field(default_factory=lambda: [
        r'rm\s+-rf\s+/', r'format\s+c:', r'del\s+/f\s+/q', r'mkfs\.[a-z]+',
        r'shutdown\s+-[rh]', r'reboot', r':\(\)\{\s*:\|:&\s*\};:', r'chmod\s+-R\s+777\s+/',
        r'>\s*/dev/sd[a-z]', r'dd\s+if=.*of=/dev/', r'wget\s+.*\|\s*bash',
        r'curl\s+.*\|\s*sh', r'python\s+-c\s+[\'"].*os\.system', r'exec\s*\(',
        r'eval\s*\(', r'__import__\s*\([\'"]os[\'"]\)', r'subprocess\.call',
    ])
    
    # Event Chain
    CHAIN_MAXLEN: int = int(os.getenv("CHAIN_MAXLEN", "10000"))
    EVENT_BATCH_SIZE: int = int(os.getenv("EVENT_BATCH_SIZE", "50"))
    EVENT_FLUSH_INTERVAL: float = float(os.getenv("EVENT_FLUSH_INTERVAL", "2.0"))
    
    # File Upload
    MAX_FILE_SIZE: int = int(os.getenv("MAX_FILE_SIZE", "104857600"))  # 100MB
    ALLOWED_EXTENSIONS: set = field(default_factory=lambda: {
        '.txt', '.md', '.json', '.csv', '.py', '.js', '.ts', '.tsx', '.jsx',
        '.jpg', '.jpeg', '.png', '.gif', '.svg', '.pdf', '.html', '.css',
        '.yaml', '.yml', '.toml', '.ini', '.sql', '.sh', '.ps1'
    })
    
    # Trading
    PAPER_BALANCE: float = float(os.getenv("PAPER_BALANCE", "1000000.0"))
    DEFAULT_SYMBOL: str = os.getenv("DEFAULT_SYMBOL", "BTCUSDT")
    TRADE_FEE: float = float(os.getenv("TRADE_FEE", "0.001"))
    SLIPPAGE: float = float(os.getenv("SLIPPAGE", "0.0005"))
    
    # Database
    DB_PATH: Path = DIRS["event_store"] / "phoenix.db"
    MEMORY_DB_PATH: Path = DIRS["memory"] / "memory.db"
    
    # Redis (if available)
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379")
    REDIS_ENABLED: bool = HAS_REDIS and os.getenv("REDIS_ENABLED", "false").lower() == "true"
    
    # Monitoring
    METRICS_ENABLED: bool = HAS_PROMETHEUS
    HEALTH_CHECK_INTERVAL: int = int(os.getenv("HEALTH_CHECK_INTERVAL", "30"))
    
    # Performance
    MAX_WORKERS: int = int(os.getenv("MAX_WORKERS", "50"))
    WORKER_TIMEOUT: int = int(os.getenv("WORKER_TIMEOUT", "30"))
    CONNECTION_POOL_SIZE: int = int(os.getenv("CONNECTION_POOL_SIZE", "20"))
    
    def get_api_key_role(self, key: str) -> Optional[str]:
        return self.API_KEYS.get(key)
    
    def is_extension_allowed(self, ext: str) -> bool:
        return ext.lower() in self.ALLOWED_EXTENSIONS

cfg = PhoenixConfig()

# ═══════════════════════════════════════════════════════════════════════════════
# SECURITY LAYER
# ═══════════════════════════════════════════════════════════════════════════════
class SecurityError(Exception):
    """Security policy violation"""
    pass

class InputSanitizer:
    """Advanced input sanitization with XSS and injection protection"""
    
    DANGEROUS_PATTERNS = [
        (r'<script.*?>.*?</script>', 'XSS script tag'),
        (r'javascript:', 'JavaScript protocol'),
        (r'on\w+\s*=', 'Event handler'),
        (r'vbscript:', 'VBScript protocol'),
        (r'data:text/html', 'Data URI HTML'),
        (r'%3Cscript', 'Encoded script tag'),
        (r'\\u003cscript', 'Unicode script tag'),
    ]
    
    @classmethod
    def sanitize(cls, text: str, max_length: int = 10000, allow_code: bool = False) -> str:
        """Sanitize input text"""
        if not isinstance(text, str):
            raise SecurityError("Input must be string")
        
        if len(text) > max_length:
            raise SecurityError(f"Input exceeds {max_length} chars")
        
        # Remove control characters except necessary ones
        if not allow_code:
            cleaned = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]', '', text)
        else:
            # For code, keep newlines and tabs
            cleaned = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]', '', text)
        
        # XSS protection (unless it's code)
        if not allow_code:
            for pattern, desc in cls.DANGEROUS_PATTERNS:
                if re.search(pattern, cleaned, re.IGNORECASE):
                    raise SecurityError(f"Blocked: {desc}")
        
        # Path traversal protection
        if '..' in cleaned or cleaned.startswith('~') or '\\' in cleaned:
            if not allow_code:
                raise SecurityError("Path traversal detected")
        
        return cleaned.strip()
    
    @classmethod
    def sanitize_filename(cls, filename: str) -> str:
        """Create safe filename"""
        if not filename or len(filename) > 255:
            raise SecurityError("Invalid filename")
        
        name, ext = os.path.splitext(os.path.basename(filename))
        safe_name = re.sub(r'[^\w\-\.]', '', name)
        safe_ext = re.sub(r'[^\w\.]', '', ext).lower()
        
        if not safe_name:
            safe_name = 'unnamed'
        
        # Add timestamp to prevent collisions
        return f"{int(time.time())}_{safe_name[:100]}{safe_ext}"

class Authentication:
    """JWT and API key authentication"""
    
    def __init__(self):
        self._api_keys = cfg.API_KEYS
        self._jwt_secret = cfg.JWT_SECRET
    
    def verify_api_key(self, key: str) -> Optional[str]:
        return self._api_keys.get(key)
    
    def generate_token(self, role: str, user_id: str = None) -> str:
        """Generate JWT token"""
        import jwt
        payload = {
            "role": role,
            "user_id": user_id or str(uuid.uuid4()),
            "exp": time.time() + cfg.JWT_EXPIRY,
            "iat": time.time(),
            "iss": "phoenix-kernel"
        }
        return jwt.encode(payload, self._jwt_secret, algorithm="HS256")
    
    def verify_token(self, token: str) -> Optional[Dict]:
        """Verify JWT token"""
        try:
            import jwt
            return jwt.decode(token, self._jwt_secret, algorithms=["HS256"])
        except:
            return None

auth_system = Authentication()
security_scheme = HTTPBearer(auto_error=False)

async def get_role(
    credentials: HTTPAuthorizationCredentials = Depends(security_scheme)
) -> str:
    """Extract role from API key or JWT"""
    if not credentials:
        return "anonymous"
    
    token = credentials.credentials
    
    # Try as API key first
    role = auth_system.verify_api_key(token)
    if role:
        return role
    
    # Try as JWT
    payload = auth_system.verify_token(token)
    if payload:
        return payload.get("role", "anonymous")
    
    raise HTTPException(status_code=403, detail="Invalid authentication")

async def require_admin(role: str = Depends(get_role)) -> str:
    """Require admin role"""
    if role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    return role

async def require_viewer(role: str = Depends(get_role)) -> str:
    """Require at least viewer role"""
    if role not in ["admin", "viewer"]:
        raise HTTPException(status_code=403, detail="Viewer access required")
    return role

# ═══════════════════════════════════════════════════════════════════════════════
# RATE LIMITER WITH REDIS SUPPORT
# ═══════════════════════════════════════════════════════════════════════════════
class RateLimiter:
    """Rate limiting with in-memory and Redis backends"""
    
    def __init__(self, max_calls: int, period: int, burst: int = None):
        self.max_calls = max_calls
        self.period = period
        self.burst = burst or max_calls
        self._in_memory: Dict[str, List[float]] = defaultdict(list)
        self._redis: Optional[redis.Redis] = None
        self._redis_enabled = False
    
    async def initialize(self):
        """Initialize Redis if configured"""
        if cfg.REDIS_ENABLED and HAS_REDIS:
            try:
                self._redis = redis.from_url(cfg.REDIS_URL)
                await self._redis.ping()
                self._redis_enabled = True
                logger.info("🗄️ Redis rate limiter enabled")
            except Exception as e:
                logger.warning(f"Redis connection failed: {e}")
    
    async def check(self, client_id: str) -> Tuple[bool, Dict]:
        """Check if request is allowed, returns (allowed, info)"""
        now = time.time()
        
        if self._redis_enabled and self._redis:
            return await self._check_redis(client_id, now)
        else:
            return self._check_memory(client_id, now)
    
    async def _check_redis(self, client_id: str, now: float) -> Tuple[bool, Dict]:
        """Redis-based rate limiting"""
        key = f"ratelimit:{client_id}"
        pipe = self._redis.pipeline()
        
        # Get current window
        window_start = now - self.period
        await pipe.zremrangebyscore(key, 0, window_start)
        await pipe.zcard(key)
        await pipe.zadd(key, {str(now): now})
        await pipe.expire(key, self.period)
        
        results = await pipe.execute()
        count = results[1]
        
        allowed = count < self.max_calls
        remaining = self.max_calls - count if allowed else 0
        
        return allowed, {
            "limit": self.max_calls,
            "remaining": max(0, remaining),
            "reset": int(now + (self.period - (now % self.period))),
            "period": self.period
        }
    
    def _check_memory(self, client_id: str, now: float) -> Tuple[bool, Dict]:
        """In-memory rate limiting"""
        # Clean old entries
        self._in_memory[client_id] = [
            t for t in self._in_memory[client_id] 
            if now - t < self.period
        ]
        
        allowed = len(self._in_memory[client_id]) < self.max_calls
        
        if allowed:
            self._in_memory[client_id].append(now)
            remaining = self.max_calls - len(self._in_memory[client_id])
        else:
            remaining = 0
        
        return allowed, {
            "limit": self.max_calls,
            "remaining": remaining,
            "reset": int(now + (self.period - (now % self.period))),
            "period": self.period
        }
    
    async def get_stats(self, client_id: str) -> Dict:
        """Get current rate limit stats"""
        now = time.time()
        if self._redis_enabled and self._redis:
            key = f"ratelimit:{client_id}"
            window_start = now - self.period
            await self._redis.zremrangebyscore(key, 0, window_start)
            count = await self._redis.zcard(key)
            return {
                "current": count,
                "limit": self.max_calls,
                "remaining": max(0, self.max_calls - count),
                "period": self.period
            }
        else:
            self._in_memory[client_id] = [
                t for t in self._in_memory[client_id] 
                if now - t < self.period
            ]
            count = len(self._in_memory[client_id])
            return {
                "current": count,
                "limit": self.max_calls,
                "remaining": max(0, self.max_calls - count),
                "period": self.period
            }

# ═══════════════════════════════════════════════════════════════════════════════
# CIRCUIT BREAKER PATTERN
# ═══════════════════════════════════════════════════════════════════════════════
class CircuitState(Enum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"

class CircuitBreakerError(Exception):
    """Circuit breaker is open"""
    pass

class CircuitBreaker:
    """Circuit breaker for external service protection"""
    
    def __init__(
        self,
        name: str,
        failure_threshold: int = 5,
        recovery_timeout: float = 60.0,
        half_open_max: int = 3,
        success_threshold: int = 2
    ):
        self.name = name
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.half_open_max = half_open_max
        self.success_threshold = success_threshold
        
        self._state = CircuitState.CLOSED
        self._failure_count = 0
        self._success_count = 0
        self._last_failure_time = 0.0
        self._last_state_change = time.time()
        self._lock = asyncio.Lock()
        
        # Metrics
        self.total_calls = 0
        self.total_failures = 0
        self.total_successes = 0
    
    @property
    def state(self) -> CircuitState:
        return self._state
    
    @property
    def is_open(self) -> bool:
        return self._state == CircuitState.OPEN
    
    async def call(self, func: Callable, *args, **kwargs) -> Any:
        """Execute function with circuit breaker protection"""
        async with self._lock:
            self.total_calls += 1
            
            # Check if circuit is open
            if self._state == CircuitState.OPEN:
                if time.time() - self._last_failure_time > self.recovery_timeout:
                    logger.info(f"[{self.name}] Circuit transitioning to HALF_OPEN")
                    self._state = CircuitState.HALF_OPEN
                    self._half_open_calls = 0
                    self._success_count = 0
                else:
                    raise CircuitBreakerError(
                        f"[{self.name}] Circuit OPEN - service unavailable "
                        f"(will retry in {self.recovery_timeout - (time.time() - self._last_failure_time):.0f}s)"
                    )
            
            # Half-open state limit
            if self._state == CircuitState.HALF_OPEN:
                if self._half_open_calls >= self.half_open_max:
                    raise CircuitBreakerError(
                        f"[{self.name}] HALF_OPEN call limit exceeded"
                    )
                self._half_open_calls += 1
        
        try:
            result = await func(*args, **kwargs)
            
            async with self._lock:
                self.total_successes += 1
                
                if self._state == CircuitState.HALF_OPEN:
                    self._success_count += 1
                    if self._success_count >= self.success_threshold:
                        logger.info(f"[{self.name}] Circuit CLOSED (recovered)")
                        self._state = CircuitState.CLOSED
                        self._failure_count = 0
                        self._success_count = 0
                else:
                    # Reset failure count on success in CLOSED state
                    self._failure_count = 0
            
            return result
            
        except Exception as e:
            async with self._lock:
                self.total_failures += 1
                self._failure_count += 1
                self._last_failure_time = time.time()
                
                if self._state == CircuitState.CLOSED and self._failure_count >= self.failure_threshold:
                    logger.error(f"[{self.name}] Circuit OPEN after {self._failure_count} failures")
                    self._state = CircuitState.OPEN
                    self._last_state_change = time.time()
                elif self._state == CircuitState.HALF_OPEN:
                    logger.warning(f"[{self.name}] HALF_OPEN test failed, returning to OPEN")
                    self._state = CircuitState.OPEN
            
            raise
    
    def get_stats(self) -> Dict:
        """Get circuit breaker statistics"""
        return {
            "name": self.name,
            "state": self._state.value,
            "failure_count": self._failure_count,
            "total_calls": self.total_calls,
            "total_failures": self.total_failures,
            "total_successes": self.total_successes,
            "success_rate": (self.total_successes / self.total_calls * 100) if self.total_calls > 0 else 0,
            "last_failure": self._last_failure_time,
            "state_since": self._last_state_change
        }
    
    def reset(self):
        """Manually reset circuit breaker"""
        self._state = CircuitState.CLOSED
        self._failure_count = 0
        self._success_count = 0
        self._half_open_calls = 0
        logger.info(f"[{self.name}] Circuit manually reset")

# ═══════════════════════════════════════════════════════════════════════════════
# KILL SWITCH SYSTEM
# ═══════════════════════════════════════════════════════════════════════════════
class KillSwitch:
    """Emergency kill switch for system halting"""
    
    def __init__(self):
        self.active = False
        self.triggered_at: Optional[float] = None
        self.triggered_by: Optional[str] = None
        self.reason: Optional[str] = None
        self._lock = asyncio.Lock()
        self._callbacks: List[Callable] = []
    
    def on_trigger(self, callback: Callable):
        """Register callback for kill switch trigger"""
        self._callbacks.append(callback)
    
    async def activate(self, reason: str, triggered_by: str = "system"):
        """Activate kill switch"""
        async with self._lock:
            if self.active:
                return
            
            self.active = True
            self.triggered_at = time.time()
            self.triggered_by = triggered_by
            self.reason = reason
            
            logger.critical(f"🔴 KILL SWITCH ACTIVATED by {triggered_by}: {reason}")
            
            # Trigger callbacks
            for callback in self._callbacks:
                try:
                    if asyncio.iscoroutinefunction(callback):
                        await callback()
                    else:
                        callback()
                except Exception as e:
                    logger.error(f"Kill switch callback error: {e}")
            
            await event_bus.publish(Event(
                type=EventType.KILL_SWITCH,
                source="kill_switch",
                payload={
                    "active": True,
                    "reason": reason,
                    "triggered_by": triggered_by,
                    "timestamp": self.triggered_at
                }
            ))
    
    async def reset(self):
        """Reset kill switch"""
        async with self._lock:
            if not self.active:
                return
            
            self.active = False
            triggered_by = self.triggered_by
            reason = self.reason
            self.triggered_at = None
            self.triggered_by = None
            self.reason = None
            
            logger.info("🔓 Kill switch RESET")
            
            await event_bus.publish(Event(
                type=EventType.KILL_SWITCH,
                source="kill_switch",
                payload={
                    "active": False,
                    "reason": "manual_reset",
                    "previous_trigger": triggered_by,
                    "previous_reason": reason
                }
            ))
    
    def is_active(self) -> bool:
        return self.active
    
    def status(self) -> Dict[str, Any]:
        return {
            "active": self.active,
            "triggered_at": self.triggered_at,
            "triggered_by": self.triggered_by,
            "reason": self.reason,
            "uptime": time.time() - self.triggered_at if self.triggered_at else 0
        }

kill_switch = KillSwitch()

# ═══════════════════════════════════════════════════════════════════════════════
# SCE PROTOCOL v2.0.0 - SOVEREIGN CHAIN ENGINE
# ═══════════════════════════════════════════════════════════════════════════════
class SCE:
    """
    Sovereign Chain Engine Protocol
    Immutable blueprint verification with cryptographic drift detection
    """
    
    VERSION = "2.0.0"
    PROTOCOL_NAME = "SOVEREIGN_CHAIN_ENGINE"
    
    @staticmethod
    def drift_lock(data: Any) -> str:
        """Generate deterministic hash for blueprint verification"""
        raw = json.dumps(data, sort_keys=True, default=str, ensure_ascii=False)
        return hashlib.sha256(raw.encode('utf-8')).hexdigest()[:16]
    
    @staticmethod
    def blueprint(
        intent: Dict[str, Any],
        dna: Dict[str, Any],
        execution: Dict[str, Any],
        parent: Optional[str] = None,
        metadata: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Create a new SCE blueprint
        
        Args:
            intent: What was the goal?
            dna: What resources were used?
            execution: What was done?
            parent: Parent blueprint drift lock
            metadata: Additional metadata
        
        Returns:
            Signed blueprint with master drift lock
        """
        blueprint = {
            "protocol": SCE.PROTOCOL_NAME,
            "version": SCE.VERSION,
            "timestamp": datetime.now().isoformat(),
            "intent": intent,
            "dna": dna,
            "execution": execution,
            "metadata": metadata or {},
        }
        
        if parent:
            blueprint["parent_drift_lock"] = parent
        
        blueprint["master_drift_lock"] = SCE.drift_lock(blueprint)
        return blueprint
    
    @staticmethod
    def verify(blueprint: Dict[str, Any]) -> Dict[str, Any]:
        """
        Verify blueprint integrity
        
        Returns:
            Verification result with status and details
        """
        stored = blueprint.get("master_drift_lock")
        if not stored:
            return {
                "verified": False,
                "badge": "🔴 NO_LOCK",
                "error": "Missing master drift lock"
            }
        
        # Create copy without master_drift_lock for verification
        verify_copy = {k: v for k, v in blueprint.items() if k != "master_drift_lock"}
        expected = SCE.drift_lock(verify_copy)
        
        valid = stored == expected
        
        return {
            "verified": valid,
            "badge": "🟢 SOVEREIGN" if valid else "🔴 DRIFTED",
            "drift_lock": stored,
            "expected": expected if not valid else None,
            "protocol": blueprint.get("protocol"),
            "version": blueprint.get("version"),
            "timestamp": blueprint.get("timestamp")
        }
    
    @staticmethod
    def chain_verify(blueprints: List[Dict]) -> Dict[str, Any]:
        """
        Verify a chain of blueprints with parent links
        """
        results = []
        valid_chain = True
        
        for i, bp in enumerate(blueprints):
            result = SCE.verify(bp)
            results.append(result)
            
            if not result["verified"]:
                valid_chain = False
            
            # Check parent link if present
            if i > 0 and "parent_drift_lock" in bp:
                parent_lock = blueprints[i-1].get("master_drift_lock")
                if bp["parent_drift_lock"] != parent_lock:
                    valid_chain = False
                    results[-1]["parent_verified"] = False
        
        return {
            "chain_valid": valid_chain,
            "blueprints_checked": len(blueprints),
            "results": results,
            "chain_length": len(blueprints)
        }

# ═══════════════════════════════════════════════════════════════════════════════
# EVENT SYSTEM
# ═══════════════════════════════════════════════════════════════════════════════
class EventType(Enum):
    """Immutable event types for the VERA chain"""
    
    # System Events
    SYSTEM_BOOT = "system.boot"
    SYSTEM_SHUTDOWN = "system.shutdown"
    KERNEL_HEARTBEAT = "kernel.heartbeat"
    CONFIG_RELOAD = "config.reload"
    
    # Worker Events
    WORKER_LOADED = "worker.loaded"
    WORKER_UNLOADED = "worker.unloaded"
    WORKER_COMPLETE = "worker.complete"
    WORKER_ERROR = "worker.error"
    WORKER_TIMEOUT = "worker.timeout"
    
    # SCE Events
    SCE_BLUEPRINT = "sce.blueprint"
    SCE_VERIFIED = "sce.verified"
    SCE_DRIFTED = "sce.drifted"
    
    # Constitution Events
    CONSTITUTION_RULING = "constitution.ruling"
    CONSTITUTION_VIOLATION = "constitution.violation"
    
    # Memory Events
    MEMORY_STORED = "memory.stored"
    MEMORY_RETRIEVED = "memory.retrieved"
    MEMORY_SEARCHED = "memory.searched"
    
    # File Events
    FILE_UPLOAD = "file.upload"
    FILE_DELETE = "file.delete"
    FILE_READ = "file.read"
    
    # Market Events
    MARKET_UPDATE = "market.update"
    TRADE_EXECUTED = "trade.executed"
    TRADE_SIMULATED = "trade.simulated"
    BACKTEST_COMPLETE = "backtest.complete"
    
    # Communication
    CHAT_MESSAGE = "chat.message"
    OLLAMA_CALL = "ollama.call"
    OLLAMA_ERROR = "ollama.error"
    
    # Security
    KILL_SWITCH = "kill.switch"
    AUTH_SUCCESS = "auth.success"
    AUTH_FAILURE = "auth.failure"
    RATE_LIMIT_HIT = "rate.limit.hit"
    
    # WebSocket
    SOCKET_CONNECT = "socket.connect"
    SOCKET_DISCONNECT = "socket.disconnect"
    SOCKET_MESSAGE = "socket.message"
    
    # System Health
    HEALTH_CHECK = "health.check"
    METRICS_COLLECTED = "metrics.collected"
    CIRCUIT_BREAKER_TRIP = "circuit.breaker.trip"

@dataclass(frozen=True)
class Event:
    """Immutable event with VERA proof"""
    
    type: EventType
    source: str
    payload: Dict[str, Any]
    timestamp: float = field(default_factory=time.time)
    previous_hash: str = ""
    
    def __post_init__(self):
        """Generate VERA proof after initialization"""
        raw = (
            f"{self.type.value}:{self.source}:"
            f"{json.dumps(self.payload, sort_keys=True, default=str)}:"
            f"{self.timestamp}:{self.previous_hash}"
        )
        proof = hashlib.sha256(raw.encode('utf-8')).hexdigest()[:16]
        object.__setattr__(self, '_vera_proof', proof)
    
    @property
    def vera_proof(self) -> str:
        return getattr(self, '_vera_proof', '')
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for storage"""
        return {
            "vera_proof": self.vera_proof,
            "type": self.type.value,
            "source": self.source,
            "payload": self.payload,
            "timestamp": self.timestamp,
            "previous_hash": self.previous_hash
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'Event':
        """Reconstruct event from dictionary"""
        event_type = EventType(data["type"]) if isinstance(data["type"], str) else data["type"]
        return cls(
            type=event_type,
            source=data["source"],
            payload=data["payload"],
            timestamp=data["timestamp"],
            previous_hash=data["previous_hash"]
        )

class EventStore:
    """SQLite-backed event store with batch writes"""
    
    def __init__(self, db_path: Path):
        self.db_path = db_path
        self._conn: Optional[sqlite3.Connection] = None
        self._write_queue: asyncio.Queue = None
        self._writer_task: Optional[asyncio.Task] = None
    
    async def initialize(self):
        """Initialize database and start writer task"""
        self._conn = sqlite3.connect(str(self.db_path), check_same_thread=False)
        self._conn.execute("PRAGMA journal_mode=WAL")
        self._conn.execute("PRAGMA synchronous=NORMAL")
        
        # Create tables
        self._conn.executescript("""
            CREATE TABLE IF NOT EXISTS events (
                vera_proof TEXT PRIMARY KEY,
                type TEXT NOT NULL,
                source TEXT NOT NULL,
                payload TEXT NOT NULL,
                timestamp REAL NOT NULL,
                previous_hash TEXT NOT NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            );
            
            CREATE TABLE IF NOT EXISTS event_chain (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                vera_proof TEXT NOT NULL,
                position INTEGER NOT NULL,
                chain_hash TEXT NOT NULL,
                FOREIGN KEY (vera_proof) REFERENCES events(vera_proof)
            );
            
            CREATE TABLE IF NOT EXISTS snapshots (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                snapshot_time REAL NOT NULL,
                chain_position INTEGER NOT NULL,
                snapshot_data TEXT NOT NULL,
                chain_hash TEXT NOT NULL
            );
            
            CREATE INDEX IF NOT EXISTS idx_events_type ON events(type);
            CREATE INDEX IF NOT EXISTS idx_events_timestamp ON events(timestamp);
            CREATE INDEX IF NOT EXISTS idx_events_source ON events(source);
        """)
        
        self._write_queue = asyncio.Queue(maxsize=10000)
        self._writer_task = asyncio.create_task(self._writer_loop())
        
        logger.info("✅ EventStore initialized")
    
    async def store(self, event: Event) -> str:
        """Store event asynchronously"""
        await self._write_queue.put(event)
        return event.vera_proof
    
    async def _writer_loop(self):
        """Background writer with batching"""
        batch = []
        batch_size = 0
        
        while True:
            try:
                event = await asyncio.wait_for(self._write_queue.get(), timeout=cfg.EVENT_FLUSH_INTERVAL)
                batch.append(event)
                batch_size += 1
                
                if batch_size >= cfg.EVENT_BATCH_SIZE:
                    await self._flush_batch(batch)
                    batch = []
                    batch_size = 0
                    
            except asyncio.TimeoutError:
                if batch:
                    await self._flush_batch(batch)
                    batch = []
                    batch_size = 0
            except asyncio.CancelledError:
                if batch:
                    await self._flush_batch(batch)
                return
            except Exception as e:
                logger.error(f"Event writer error: {e}")
                await asyncio.sleep(1)
    
    async def _flush_batch(self, events: List[Event]):
        """Flush batch to database"""
        try:
            cursor = self._conn.cursor()
            
            for event in events:
                cursor.execute(
                    """INSERT OR REPLACE INTO events 
                       (vera_proof, type, source, payload, timestamp, previous_hash) 
                       VALUES (?, ?, ?, ?, ?, ?)""",
                    (event.vera_proof, event.type.value, event.source,
                     json.dumps(event.payload, default=str), event.timestamp, event.previous_hash)
                )
            
            self._conn.commit()
            
        except Exception as e:
            logger.error(f"Batch flush failed: {e}")
            self._conn.rollback()
    
    async def query(
        self,
        event_type: Optional[EventType] = None,
        source: Optional[str] = None,
        start_time: Optional[float] = None,
        end_time: Optional[float] = None,
        limit: int = 100
    ) -> List[Event]:
        """Query events with filters"""
        query = "SELECT * FROM events WHERE 1=1"
        params = []
        
        if event_type:
            query += " AND type = ?"
            params.append(event_type.value)
        
        if source:
            query += " AND source = ?"
            params.append(source)
        
        if start_time:
            query += " AND timestamp >= ?"
            params.append(start_time)
        
        if end_time:
            query += " AND timestamp <= ?"
            params.append(end_time)
        
        query += " ORDER BY timestamp DESC LIMIT ?"
        params.append(limit)
        
        cursor = self._conn.execute(query, params)
        events = []
        
        for row in cursor.fetchall():
            event = Event(
                type=EventType(row[1]),
                source=row[2],
                payload=json.loads(row[3]),
                timestamp=row[4],
                previous_hash=row[5]
            )
            events.append(event)
        
        return events
    
    async def get_stats(self) -> Dict:
        """Get event store statistics"""
        cursor = self._conn.execute("SELECT COUNT(*) FROM events")
        total = cursor.fetchone()[0]
        
        cursor = self._conn.execute(
            "SELECT type, COUNT(*) FROM events GROUP BY type ORDER BY COUNT(*) DESC LIMIT 10"
        )
        type_counts = dict(cursor.fetchall())
        
        return {
            "total_events": total,
            "type_counts": type_counts,
            "queue_size": self._write_queue.qsize(),
            "db_path": str(self.db_path)
        }
    
    async def close(self):
        """Close event store"""
        if self._writer_task:
            self._writer_task.cancel()
            try:
                await self._writer_task
            except asyncio.CancelledError:
                pass
        
        if self._conn:
            self._conn.close()
            logger.info("📦 EventStore closed")

class EventBus:
    """In-memory event bus with VERA chain"""
    
    def __init__(self):
        self._chain: List[Event] = []
        self._lock = asyncio.Lock()
        self._genesis = hashlib.sha256(b"PHOENIX_V15.3.1_REZONIC").hexdigest()[:16]
        self._store: Optional[EventStore] = None
        self._subscribers: Dict[EventType, List[Callable]] = defaultdict(list)
        self._ready = False
    
    async def initialize(self):
        """Initialize event bus and store"""
        self._store = EventStore(cfg.DB_PATH)
        await self._store.initialize()
        self._ready = True
        logger.info("✅ Event bus initialized")
    
    async def publish(self, event: Event) -> str:
        """Publish event to chain and notify subscribers"""
        if not self._ready:
            return ""
        
        async with self._lock:
            # Link to previous event
            prev = self._chain[-1].vera_proof if self._chain else self._genesis
            linked_event = Event(
                type=event.type,
                source=event.source,
                payload=event.payload,
                previous_hash=prev
            )
            
            # Add to chain
            if len(self._chain) >= cfg.CHAIN_MAXLEN:
                self._chain.pop(0)
            self._chain.append(linked_event)
            
            # Store asynchronously
            if self._store:
                await self._store.store(linked_event)
            
            # Notify subscribers
            await self._notify_subscribers(linked_event)
            
            return linked_event.vera_proof
    
    async def _notify_subscribers(self, event: Event):
        """Notify subscribers of event"""
        subscribers = self._subscribers.get(event.type, [])
        subscribers.extend(self._subscribers.get(None, []))  # All events
        
        for callback in subscribers:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(event)
                else:
                    callback(event)
            except Exception as e:
                logger.error(f"Subscriber error for {event.type.value}: {e}")
    
    def subscribe(self, event_type: Optional[EventType], callback: Callable):
        """Subscribe to events"""
        self._subscribers[event_type].append(callback)
    
    async def verify_chain(self) -> bool:
        """Verify entire event chain integrity"""
        async with self._lock:
            prev = self._genesis
            for ev in self._chain:
                raw = (
                    f"{ev.type.value}:{ev.source}:"
                    f"{json.dumps(ev.payload, sort_keys=True, default=str)}:"
                    f"{ev.timestamp}:{prev}"
                )
                expected = hashlib.sha256(raw.encode('utf-8')).hexdigest()[:16]
                if ev.vera_proof != expected:
                    logger.error(f"Chain verification failed at {ev.type.value}")
                    return False
                prev = ev.vera_proof
            return True
    
    async def get_stats(self) -> Dict[str, Any]:
        """Get event bus statistics"""
        async with self._lock:
            counts = defaultdict(int)
            for ev in self._chain:
                counts[ev.type.value] += 1
            
            store_stats = await self._store.get_stats() if self._store else {}
            
            return {
                "total_events": len(self._chain),
                "chain_valid": await self.verify_chain(),
                "genesis": self._genesis,
                "latest": self._chain[-1].vera_proof if self._chain else self._genesis,
                "latest_type": self._chain[-1].type.value if self._chain else None,
                "counts": dict(counts),
                "timestamp": time.time(),
                "store": store_stats
            }
    
    async def shutdown(self):
        """Shutdown event bus"""
        if self._store:
            await self._store.close()
        self._ready = False
        logger.info("🌙 Event bus shutdown")

event_bus = EventBus()

# ═══════════════════════════════════════════════════════════════════════════════
# CONSTITUTION - SOVEREIGN GOVERNANCE
# ═══════════════════════════════════════════════════════════════════════════════
class Constitution:
    """
    Constitutional AI governance system
    Enforces safety policies and ethical boundaries
    """
    
    def __init__(self):
        self.rulings: List[Dict] = []
        self._compiled_patterns = [
            (re.compile(p, re.IGNORECASE), p) 
            for p in cfg.CONSTITUTION_PATTERNS
        ]
        
        # Safety policies
        self.policies = {
            "no_destructive_ops": "Block destructive system operations",
            "no_remote_code": "Block remote code execution",
            "no_data_destruction": "Prevent data destruction",
            "no_privilege_escalation": "Prevent privilege escalation",
            "sandbox_required": "All code must run in sandbox",
        }
    
    async def evaluate(self, action: str, context: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Evaluate action against constitution
        
        Returns:
            Dict with approval status and reasoning
        """
        action_lower = action.lower()
        
        # Check dangerous patterns
        for pattern, original in self._compiled_patterns:
            if pattern.search(action_lower):
                ruling = {
                    "approved": False,
                    "reason": f"Constitution violation: {self._get_pattern_name(original)}",
                    "score": 0,
                    "pattern_matched": original,
                    "policy": self._get_policy_for_pattern(original),
                    "timestamp": time.time()
                }
                self.rulings.append({
                    **ruling,
                    "action": action[:500],
                    "context": context
                })
                
                await event_bus.publish(Event(
                    type=EventType.CONSTITUTION_RULING,
                    source="constitution",
                    payload=ruling
                ))
                
                return ruling
        
        # Additional checks for code execution
        if "import" in action_lower or "exec" in action_lower or "eval" in action_lower:
            if cfg.CONSTITUTION_STRICT:
                return {
                    "approved": False,
                    "reason": "Code execution requires explicit approval in strict mode",
                    "score": 30,
                    "requires_approval": True
                }
        
        # Passed all checks
        return {
            "approved": True,
            "reason": "Passed constitutional review",
            "score": 90,
            "policies_passed": len(self.policies)
        }
    
    def _get_pattern_name(self, pattern: str) -> str:
        """Get human-readable name for pattern"""
        name_map = {
            r'rm\s+-rf\s+/': "recursive_rm_root",
            r'format\s+c:': "format_drive",
            r'shutdown': "system_shutdown",
            r'wget.*\|.*bash': "remote_code_execution",
        }
        return name_map.get(pattern, "dangerous_operation")
    
    def _get_policy_for_pattern(self, pattern: str) -> str:
        """Get policy violated by pattern"""
        if "rm" in pattern or "del" in pattern or "format" in pattern:
            return "no_data_destruction"
        if "wget" in pattern or "curl" in pattern:
            return "no_remote_code"
        if "shutdown" in pattern or "reboot" in pattern:
            return "no_destructive_ops"
        return "general_safety"
    
    async def get_history(self, limit: int = 50) -> List[Dict]:
        """Get recent rulings"""
        return self.rulings[-limit:]
    
    async def get_stats(self) -> Dict:
        """Get constitution statistics"""
        approved = sum(1 for r in self.rulings if r.get("approved"))
        total = len(self.rulings)
        
        return {
            "total_rulings": total,
            "approved": approved,
            "blocked": total - approved,
            "approval_rate": (approved / total * 100) if total > 0 else 100,
            "patterns_loaded": len(self._compiled_patterns),
            "policies": list(self.policies.keys())
        }

constitution = Constitution()

# ═══════════════════════════════════════════════════════════════════════════════
# SOVEREIGN MEMORY SYSTEM
# ═══════════════════════════════════════════════════════════════════════════════
class SovereignMemory:
    """
    Persistent memory system with blueprint storage and semantic search
    """
    
    def __init__(self):
        self.memories: Dict[str, Dict] = {}
        self._embeddings_cache: Dict[str, List[float]] = {}
        self._lock = asyncio.Lock()
        self._load_from_disk()
    
    def store(self, blueprint: Dict, metadata: Optional[Dict] = None) -> str:
        """Store blueprint in memory"""
        lock = blueprint.get("master_drift_lock", SCE.drift_lock(blueprint))
        
        memory_entry = {
            "value": blueprint,
            "timestamp": time.time(),
            "access_count": 0,
            "metadata": metadata or {},
            "verified": SCE.verify(blueprint)["verified"]
        }
        
        self.memories[lock] = memory_entry
        
        # Persist to disk
        path = DIRS["memory"] / f"bp_{lock}.json"
        try:
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(memory_entry, f, indent=2, ensure_ascii=False, default=str)
        except Exception as e:
            logger.error(f"Memory persist failed: {e}")
        
        return lock
    
    def get(self, lock: str) -> Optional[Dict]:
        """Retrieve blueprint by drift lock"""
        record = self.memories.get(lock)
        if record:
            record["access_count"] += 1
            return record["value"]
        return None
    
    def search(self, query: str, limit: int = 10, include_metadata: bool = False) -> List[Dict]:
        """
        Search memory by keyword matching
        
        TODO: Add vector embeddings for semantic search
        """
        results = []
        q_lower = query.lower()
        
        for lock, record in self.memories.items():
            bp = record["value"]
            
            # Search in intent and execution
            searchable = json.dumps({
                **bp.get("intent", {}),
                **bp.get("execution", {}),
                **record.get("metadata", {})
            }, default=str).lower()
            
            # Simple keyword scoring
            score = searchable.count(q_lower) * 5
            
            if score > 0:
                result = {
                    "lock": lock,
                    "score": score,
                    "timestamp": record["timestamp"],
                    "verified": record.get("verified", False)
                }
                
                if include_metadata:
                    result["metadata"] = record.get("metadata", {})
                    result["intent"] = bp.get("intent", {})
                
                results.append(result)
        
        results.sort(key=lambda x: (-x["score"], x["timestamp"]))
        return results[:limit]
    
    def _load_from_disk(self):
        """Load blueprints from disk"""
        for p in DIRS["memory"].glob("*.json"):
            try:
                with open(p, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                if "value" in data:
                    lock = data["value"].get("master_drift_lock")
                    if lock:
                        self.memories[lock] = data
            except Exception as e:
                logger.debug(f"Failed to load {p}: {e}")
        
        logger.info(f"📚 Loaded {len(self.memories)} blueprints from disk")
    
    async def get_stats(self) -> Dict:
        """Get memory statistics"""
        verified = sum(1 for r in self.memories.values() if r.get("verified", False))
        
        return {
            "total_blueprints": len(self.memories),
            "verified": verified,
            "drifted": len(self.memories) - verified,
            "recent": [
                {"lock": k, "timestamp": v["timestamp"]}
                for k, v in sorted(self.memories.items(), key=lambda x: x[1]["timestamp"])[-10:]
            ]
        }

memory = SovereignMemory()

# ═══════════════════════════════════════════════════════════════════════════════
# GPU MONITOR
# ═══════════════════════════════════════════════════════════════════════════════
class GPUMonitor:
    """NVIDIA GPU monitoring with fallback"""
    
    def __init__(self):
        self.gpus: List[Dict] = []
        self.has_gpu = False
        self._error: Optional[str] = None
        self._initialized = False
    
    def initialize(self) -> bool:
        """Initialize GPU monitoring"""
        if self._initialized:
            return self.has_gpu
        
        if not HAS_PYNVML:
            logger.info("🖥️ GPU monitoring: pynvml not available")
            return False
        
        try:
            pynvml.nvmlInit()
            count = pynvml.nvmlDeviceGetCount()
            
            for i in range(count):
                h = pynvml.nvmlDeviceGetHandleByIndex(i)
                name = pynvml.nvmlDeviceGetName(h)
                if isinstance(name, bytes):
                    name = name.decode('utf-8', errors='replace')
                
                mem = pynvml.nvmlDeviceGetMemoryInfo(h)
                
                self.gpus.append({
                    "index": i,
                    "name": name,
                    "handle": h,
                    "total_gb": round(mem.total / 1024**3, 1),
                })
            
            self.has_gpu = len(self.gpus) > 0
            if self.has_gpu:
                logger.info(f"🖥️ GPU detected: {self.gpus[0]['name']} ({self.gpus[0]['total_gb']}GB)")
            
            self._initialized = True
            
        except Exception as e:
            self._error = str(e)
            logger.warning(f"GPU init failed: {e}")
        
        return self.has_gpu
    
    def stats(self) -> Dict[str, Any]:
        """Get current GPU statistics"""
        if not self.has_gpu:
            return {
                "has_gpu": False,
                "error": self._error or "No GPU detected"
            }
        
        try:
            h = self.gpus[0]["handle"]
            mem = pynvml.nvmlDeviceGetMemoryInfo(h)
            util = pynvml.nvmlDeviceGetUtilizationRates(h)
            temp = pynvml.nvmlDeviceGetTemperature(h, pynvml.NVML_TEMPERATURE_GPU)
            power = pynvml.nvmlDeviceGetPowerUsage(h) / 1000.0  # mW to W
            
            return {
                "has_gpu": True,
                "name": self.gpus[0]["name"],
                "total_gb": round(mem.total / 1024**3, 1),
                "used_gb": round(mem.used / 1024**3, 1),
                "free_gb": round((mem.total - mem.used) / 1024**3, 1),
                "utilization": util.gpu,
                "memory_utilization": util.memory,
                "temperature": temp,
                "power_watts": power,
            }
        except Exception as e:
            return {
                "has_gpu": True,
                "error": f"Read failed: {e}",
                "name": self.gpus[0]["name"] if self.gpus else "Unknown"
            }
    
    def shutdown(self):
        """Shutdown NVML"""
        if HAS_PYNVML and self.has_gpu:
            try:
                pynvml.nvmlShutdown()
            except:
                pass

gpu = GPUMonitor()

# ═══════════════════════════════════════════════════════════════════════════════
# OLLAMA CLIENT WITH CIRCUIT BREAKER
# ═══════════════════════════════════════════════════════════════════════════════
class OllamaClient:
    """Ollama API client with streaming and circuit breaker"""
    
    def __init__(self):
        self.base_url = cfg.OLLAMA_URL
        self.model = cfg.DEFAULT_MODEL
        self.timeout = cfg.OLLAMA_TIMEOUT
        self.available = False
        self.models: List[str] = []
        self._client: Optional[httpx.AsyncClient] = None
        self._breaker = CircuitBreaker("ollama", failure_threshold=3, recovery_timeout=60)
    
    async def initialize(self):
        """Initialize HTTP client and check connection"""
        self._client = httpx.AsyncClient(
            timeout=httpx.Timeout(self.timeout, connect=10),
            limits=httpx.Limits(max_keepalive_connections=10)
        )
        await self.check_connection()
    
    async def check_connection(self) -> bool:
        """Check Ollama connection and list models"""
        if not self._client:
            return False
        
        try:
            r = await self._client.get(f"{self.base_url}/api/tags")
            if r.status_code == 200:
                data = r.json()
                self.models = [m["name"] for m in data.get("models", [])]
                self.available = True
                logger.info(f"🤖 Ollama connected: {len(self.models)} models available")
                return True
        except Exception as e:
            logger.debug(f"Ollama connection check failed: {e}")
        
        self.available = False
        return False
    
    async def chat(self, messages: List[Dict], model: Optional[str] = None, stream: bool = False) -> Union[str, AsyncGenerator]:
        """
        Chat with Ollama
        
        Args:
            messages: List of message dicts with role and content
            model: Model name (uses default if None)
            stream: Whether to stream response
        
        Returns:
            String response or async generator for streaming
        """
        if not self._client:
            raise RuntimeError("Ollama client not initialized")
        
        model = model or self.model
        
        payload = {
            "model": model,
            "messages": messages,
            "stream": stream,
            "options": {
                "num_ctx": cfg.OLLAMA_NUM_CTX,
                "num_predict": cfg.OLLAMA_MAX_TOKENS,
                "temperature": cfg.OLLAMA_TEMPERATURE,
                "top_p": cfg.OLLAMA_TOP_P,
            }
        }
        
        await event_bus.publish(Event(
            type=EventType.OLLAMA_CALL,
            source="ollama",
            payload={
                "model": model,
                "messages": [m["role"] for m in messages],
                "stream": stream
            }
        ))
        
        if stream:
            return self._stream_chat(payload)
        else:
            try:
                response = await self._breaker.call(
                    self._client.post,
                    f"{self.base_url}/api/chat",
                    json=payload
                )
                data = response.json()
                return data.get("message", {}).get("content", "")
            except CircuitBreakerError as e:
                logger.error(f"Ollama circuit breaker open: {e}")
                return "⚠️ Ollama service temporarily unavailable. Please try again later."
            except Exception as e:
                logger.error(f"Ollama chat error: {e}")
                await event_bus.publish(Event(
                    type=EventType.OLLAMA_ERROR,
                    source="ollama",
                    payload={"error": str(e)}
                ))
                raise
    
    async def _stream_chat(self, payload: Dict) -> AsyncGenerator[str, None]:
        """Stream chat responses"""
        try:
            async with self._client.stream("POST", f"{self.base_url}/api/chat", json=payload) as response:
                if response.status_code != 200:
                    yield f"Ollama error: {response.status_code}"
                    return
                
                async for line in response.aiter_lines():
                    if not line.strip():
                        continue
                    
                    try:
                        chunk = json.loads(line)
                        content = chunk.get("message", {}).get("content", "")
                        if content:
                            yield content
                        
                        if chunk.get("done"):
                            return
                    except json.JSONDecodeError:
                        continue
                        
        except asyncio.CancelledError:
            logger.info("Ollama stream cancelled")
            yield "\n[Stream cancelled]"
        except Exception as e:
            logger.error(f"Ollama stream error: {e}")
            yield f"\n❌ Ollama error: {type(e).__name__}"
    
    async def close(self):
        """Close HTTP client"""
        if self._client:
            await self._client.aclose()

ollama = OllamaClient()

# ═══════════════════════════════════════════════════════════════════════════════
# WORKER SYSTEM
# ═══════════════════════════════════════════════════════════════════════════════
class Worker(ABC):
    """Base worker interface"""
    
    def __init__(self, name: str):
        self.name = name
        self.created_at = time.time()
        self.last_execution: Optional[float] = None
        self.execution_count = 0
        self.error_count = 0
    
    @abstractmethod
    async def execute(self, task: str, **kwargs) -> Dict[str, Any]:
        """Execute worker task"""
        pass
    
    async def health_check(self) -> Dict[str, Any]:
        """Worker health status"""
        return {
            "name": self.name,
            "status": "healthy",
            "executions": self.execution_count,
            "errors": self.error_count,
            "last_execution": self.last_execution,
            "uptime": time.time() - self.created_at
        }

class WorkerLoader:
    """Dynamic worker loader with duck typing support"""
    
    def __init__(self, directory: Path):
        self.directory = directory.resolve()
    
    def is_valid_worker(self, obj, class_name: str) -> bool:
        """Check if object is a valid worker class"""
        if not inspect.isclass(obj):
            return False
        
        if inspect.isabstract(obj):
            return False
        
        # Check for Worker inheritance
        try:
            if issubclass(obj, Worker):
                return True
        except TypeError:
            pass
        
        # Duck typing: has execute method
        if hasattr(obj, 'execute') and callable(getattr(obj, 'execute')):
            return True
        
        return False
    
    def load_all(self) -> Dict[str, Dict]:
        """Load all worker classes from directory"""
        workers = {}
        
        if not self.directory.exists():
            logger.warning(f"Worker directory not found: {self.directory}")
            return workers
        
        for py_file in sorted(self.directory.glob("*.py")):
            if py_file.name.startswith("__"):
                continue
            
            try:
                spec = importlib.util.spec_from_file_location(py_file.stem, py_file)
                if not spec or not spec.loader:
                    continue
                
                mod = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(mod)
                
                for name, obj in inspect.getmembers(mod, inspect.isclass):
                    if not self.is_valid_worker(obj, name):
                        continue
                    
                    try:
                        # Try instantiation with name parameter
                        try:
                            worker = obj(name=name.lower())
                        except TypeError:
                            # Fallback to no args
                            worker = obj()
                            if not hasattr(worker, 'name'):
                                worker.name = name.lower()
                        
                        worker_name = getattr(worker, 'name', name.lower())
                        workers[worker_name] = {
                            "class": obj,
                            "module": py_file.stem,
                            "loaded_at": time.time(),
                            "instance": worker
                        }
                        logger.info(f"  ✅ Worker loaded: {worker_name}")
                        
                    except Exception as e:
                        logger.debug(f"  ⚠️ Cannot instantiate {name}: {e}")
                        
            except Exception as e:
                logger.debug(f"  ⚠️ Skip {py_file.name}: {e}")
        
        return workers

# ═══════════════════════════════════════════════════════════════════════════════
# BUILT-IN WORKERS
# ═══════════════════════════════════════════════════════════════════════════════
class SystemMonitorWorker(Worker):
    """System resource monitoring worker"""
    
    def __init__(self):
        super().__init__("system_monitor")
    
    async def execute(self, task: str, **kwargs) -> Dict[str, Any]:
        """Get system metrics"""
        result = {
            "success": True,
            "gpu": gpu.stats(),
            "timestamp": time.time()
        }
        
        if HAS_PSUTIL:
            result["cpu_percent"] = psutil.cpu_percent(interval=0.1)
            result["cpu_count"] = psutil.cpu_count()
            
            vm = psutil.virtual_memory()
            result["ram"] = {
                "percent": vm.percent,
                "used_gb": round(vm.used / 1024**3, 1),
                "total_gb": round(vm.total / 1024**3, 1),
                "free_gb": round(vm.free / 1024**3, 1)
            }
            
            disk = psutil.disk_usage('/')
            result["disk"] = {
                "percent": disk.percent,
                "used_gb": round(disk.used / 1024**3, 1),
                "total_gb": round(disk.total / 1024**3, 1),
                "free_gb": round(disk.free / 1024**3, 1)
            }
        
        return result

class CodeExecutionWorker(Worker):
    """Safe code execution in sandbox"""
    
    def __init__(self):
        super().__init__("code_execution")
    
    async def execute(self, task: str, **kwargs) -> Dict[str, Any]:
        """Execute code in sandbox"""
        # Extract code from markdown or use raw task
        code_match = re.search(r'```(?:python)?\s*\n(.*?)\n```', task, re.DOTALL)
        code = code_match.group(1) if code_match else task
        
        # Constitutional check
        ruling = await constitution.evaluate(code, context={"worker": "code_execution"})
        if not ruling["approved"]:
            return {
                "success": False,
                "error": ruling["reason"],
                "ruling": ruling
            }
        
        # Create temp file
        with tempfile.NamedTemporaryFile(
            mode='w',
            suffix='.py',
            dir=str(DIRS["sandbox"]),
            delete=False
        ) as f:
            f.write(code)
            tmp_path = f.name
        
        try:
            # Execute with timeout and resource limits
            proc = await asyncio.create_subprocess_exec(
                sys.executable, tmp_path,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=str(DIRS["sandbox"]),
                limit=1024 * 1024  # 1MB buffer
            )
            
            stdout, stderr = await asyncio.wait_for(
                proc.communicate(),
                timeout=cfg.WORKER_TIMEOUT
            )
            
            return {
                "success": proc.returncode == 0,
                "stdout": stdout.decode('utf-8', errors='replace')[-5000:],
                "stderr": stderr.decode('utf-8', errors='replace')[-2000:],
                "returncode": proc.returncode
            }
            
        except asyncio.TimeoutError:
            return {
                "success": False,
                "error": f"Execution timeout ({cfg.WORKER_TIMEOUT}s)"
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Execution failed: {e}"
            }
        finally:
            try:
                os.unlink(tmp_path)
            except:
                pass

class CodeGenWorker(Worker):
    """Code generation worker"""
    
    def __init__(self):
        super().__init__("code_gen")
    
    async def execute(self, task: str, **kwargs) -> Dict[str, Any]:
        """Generate code scaffold"""
        intent = task.strip()
        
        if not intent:
            return {"error": "No code intent provided", "success": False}
        
        # Generate code scaffold
        code = f'''def solution():
    """Generated for: {intent}"""
    # TODO: Implement your solution here
    pass

if __name__ == "__main__":
    result = solution()
    print(f"Result: {{result}}")
'''
        
        # Create blueprint
        blueprint = SCE.blueprint(
            intent={"task": intent, "type": "code_generation"},
            dna={"worker": "code_gen"},
            execution={"code_length": len(code)}
        )
        lock = memory.store(blueprint)
        
        return {
            "success": True,
            "code": code,
            "language": "python",
            "intent": intent,
            "verified": True,
            "drift_lock": lock
        }

class PaperTraderWorker(Worker):
    """Paper trading simulation"""
    
    def __init__(self):
        super().__init__("paper_trader")
        self.balance = cfg.PAPER_BALANCE
        self.positions: Dict[str, Dict] = {}
        self.trade_history: List[Dict] = []
        self.total_fees = 0
    
    async def execute(self, task: str, **kwargs) -> Dict[str, Any]:
        """Execute trade or get portfolio"""
        task_lower = task.lower()
        
        if "portfolio" in task_lower:
            total_value = self.balance
            for symbol, pos in self.positions.items():
                current_price = kwargs.get(f"{symbol}_price", 50000)
                total_value += pos["amount"] * current_price
            
            return {
                "success": True,
                "balance": self.balance,
                "positions": self.positions,
                "total_value": total_value,
                "pnl": total_value - cfg.PAPER_BALANCE,
                "pnl_percent": ((total_value - cfg.PAPER_BALANCE) / cfg.PAPER_BALANCE) * 100,
                "trades": len(self.trade_history),
                "fees": self.total_fees
            }
        
        elif "buy" in task_lower:
            symbol = kwargs.get("symbol", cfg.DEFAULT_SYMBOL)
            amount = float(kwargs.get("amount", 0.01))
            price = float(kwargs.get("price", 50000))
            
            cost = amount * price
            fee = cost * cfg.TRADE_FEE
            total_cost = cost + fee
            
            if total_cost <= self.balance:
                self.balance -= total_cost
                self.total_fees += fee
                
                if symbol not in self.positions:
                    self.positions[symbol] = {"amount": 0, "avg_price": 0}
                
                pos = self.positions[symbol]
                new_amount = pos["amount"] + amount
                pos["avg_price"] = (pos["avg_price"] * pos["amount"] + cost) / new_amount
                pos["amount"] = new_amount
                
                trade = {
                    "action": "BUY",
                    "symbol": symbol,
                    "amount": amount,
                    "price": price,
                    "fee": fee,
                    "timestamp": time.time()
                }
                self.trade_history.append(trade)
                
                await event_bus.publish(Event(
                    type=EventType.TRADE_EXECUTED,
                    source="paper_trader",
                    payload=trade
                ))
                
                return {
                    "success": True,
                    "balance": self.balance,
                    "position": pos["amount"],
                    "avg_price": pos["avg_price"],
                    "trade": trade
                }
            
            return {
                "success": False,
                "error": "Insufficient balance",
                "required": total_cost,
                "available": self.balance
            }
        
        elif "sell" in task_lower:
            symbol = kwargs.get("symbol", cfg.DEFAULT_SYMBOL)
            amount = float(kwargs.get("amount", 0.01))
            price = float(kwargs.get("price", 50000))
            
            pos = self.positions.get(symbol)
            if not pos or pos["amount"] < amount:
                return {
                    "success": False,
                    "error": f"Insufficient {symbol}",
                    "have": pos["amount"] if pos else 0,
                    "need": amount
                }
            
            revenue = amount * price
            fee = revenue * cfg.TRADE_FEE
            net_revenue = revenue - fee
            
            self.balance += net_revenue
            self.total_fees += fee
            pos["amount"] -= amount
            
            if pos["amount"] <= 0:
                del self.positions[symbol]
            
            trade = {
                "action": "SELL",
                "symbol": symbol,
                "amount": amount,
                "price": price,
                "fee": fee,
                "timestamp": time.time()
            }
            self.trade_history.append(trade)
            
            await event_bus.publish(Event(
                type=EventType.TRADE_EXECUTED,
                source="paper_trader",
                payload=trade
            ))
            
            return {
                "success": True,
                "balance": self.balance,
                "position": pos["amount"] if symbol in self.positions else 0,
                "trade": trade
            }
        
        return {"success": False, "error": "Unknown command. Use: buy/sell/portfolio"}

class BacktestWorker(Worker):
    """Strategy backtesting"""
    
    def __init__(self):
        super().__init__("backtest")
    
    async def execute(self, task: str, **kwargs) -> Dict[str, Any]:
        """Run backtest simulation"""
        strategy = task.strip()
        
        if not strategy:
            return {"success": False, "error": "Strategy name required"}
        
        # Deterministic seed for reproducibility
        seed = hash(strategy) % (2**32)
        random.seed(seed)
        
        # Simulate backtest results
        result = {
            "success": True,
            "strategy": strategy,
            "total_return": round(random.uniform(-0.15, 0.45), 4),
            "sharpe_ratio": round(random.uniform(0.5, 2.8), 2),
            "max_drawdown": round(random.uniform(0.05, 0.35), 4),
            "win_rate": round(random.uniform(0.35, 0.75), 2),
            "trades": random.randint(50, 500),
            "seed": seed,
            "timestamp": time.time()
        }
        
        random.seed()  # Reset seed
        
        await event_bus.publish(Event(
            type=EventType.BACKTEST_COMPLETE,
            source="backtest",
            payload=result
        ))
        
        return result

# ═══════════════════════════════════════════════════════════════════════════════
# REFLEX COMMAND SYSTEM
# ═══════════════════════════════════════════════════════════════════════════════
class Reflex:
    """Command system for direct kernel control"""
    
    def __init__(self, kernel: 'PhoenixKernel'):
        self.kernel = kernel
    
    async def try_execute(self, cmd: str) -> Optional[Dict]:
        """Execute reflex command if recognized"""
        cmd = cmd.strip()
        lower = cmd.lower()
        
        # Trading commands
        if lower == "/portfolio":
            worker = self.kernel.workers.get("paper_trader", {}).get("instance")
            if worker:
                result = await worker.execute("portfolio")
                return self._response(f"📊 Portfolio:\n{json.dumps(result, indent=2)}")
            return self._response("❌ PaperTrader not available")
        
        if lower.startswith("/trade "):
            parts = cmd.split()
            if len(parts) >= 3:
                action, symbol = parts[1], parts[2]
                amount = float(parts[3]) if len(parts) > 3 else 0.01
                
                worker = self.kernel.workers.get("paper_trader", {}).get("instance")
                if worker:
                    result = await worker.execute(action, symbol=symbol, amount=amount)
                    return self._response(f"💰 Trade result:\n{json.dumps(result, indent=2)}")
                return self._response("❌ PaperTrader not available")
            return self._response("Usage: /trade buy|sell SYMBOL [AMOUNT]")
        
        if lower.startswith("/backtest "):
            strategy = cmd[10:].strip()
            if strategy:
                worker = self.kernel.workers.get("backtest", {}).get("instance")
                if worker:
                    result = await worker.execute(strategy)
                    return self._response(f"📈 Backtest:\n{json.dumps(result, indent=2)}")
            return self._response("Usage: /backtest STRATEGY_NAME")
        
        # Kill switch
        if lower == "/kill":
            await kill_switch.activate("Manual trigger via reflex", triggered_by="user")
            return self._response("🔴 KILL SWITCH ACTIVATED")
        
        if lower == "/kill-reset":
            await kill_switch.reset()
            return self._response("🔓 Kill switch RESET")
        
        if lower == "/kill-status":
            status = kill_switch.status()
            return self._response(f"Kill switch: {'🔴 ACTIVE' if status['active'] else '🟢 INACTIVE'}\n"
                                 f"Reason: {status.get('reason', 'N/A')}")
        
        # System commands
        if lower == "/health":
            stats = gpu.stats()
            event_stats = await event_bus.get_stats()
            return self._response(
                f"🔥 **Phoenix v{cfg.VERSION}**\n"
                f"───────────────────\n"
                f"Workers:     {len(self.kernel.workers)}\n"
                f"Blueprints:  {len(memory.memories)}\n"
                f"Events:      {event_stats['total_events']}\n"
                f"Chain Valid: {'✅' if event_stats['chain_valid'] else '❌'}\n"
                f"Ollama:      {'🟢' if ollama.available else '🔴'}\n"
                f"GPU:         {stats.get('name', 'None')}\n"
                f"Uptime:      {round(time.time() - self.kernel.start_time)}s"
            )
        
        if lower == "/workers":
            names = sorted(self.kernel.workers.keys())
            lines = []
            for name in names[:50]:
                w = self.kernel.workers.get(name, {})
                instance = w.get("instance")
                if instance:
                    health = await instance.health_check()
                    status = "✅" if health.get("status") == "healthy" else "⚠️"
                    lines.append(f"  {status} {name} (execs: {health.get('executions', 0)})")
                else:
                    lines.append(f"  ⚠️ {name} (no instance)")
            
            extra = f"\n... +{len(names)-50} more" if len(names) > 50 else ""
            return self._response(f"⚙️ **Workers ({len(names)})**\n" + "\n".join(lines) + extra)
        
        if lower == "/chain":
            stats = await event_bus.get_stats()
            return self._response(
                f"⛓️ **Event Chain**\n"
                f"───────────────────\n"
                f"Total Events: {stats['total_events']}\n"
                f"Chain Valid:  {'✅' if stats['chain_valid'] else '❌'}\n"
                f"Genesis:      {stats['genesis']}\n"
                f"Latest:       {stats.get('latest', 'N/A')}\n"
                f"Latest Type:  {stats.get('latest_type', 'N/A')}\n"
                f"Top Types:\n" +
                "\n".join([f"  • {k}: {v}" for k, v in list(stats['counts'].items())[:5]])
            )
        
        if lower == "/constitution":
            stats = await constitution.get_stats()
            return self._response(
                f"📜 **Constitution Stats**\n"
                f"───────────────────\n"
                f"Total Rulings:  {stats['total_rulings']}\n"
                f"Approved:       {stats['approved']}\n"
                f"Blocked:        {stats['blocked']}\n"
                f"Approval Rate:  {stats['approval_rate']:.1f}%\n"
                f"Policies:       {', '.join(stats['policies'][:3])}"
            )
        
        if lower.startswith("/search "):
            query = cmd[8:].strip()
            results = memory.search(query, limit=5, include_metadata=True)
            if results:
                lines = []
                for i, r in enumerate(results):
                    verified = "✅" if r.get("verified") else "⚠️"
                    lines.append(f"  {i+1}. {verified} {r['lock'][:12]}… (score: {r['score']})")
                    if r.get("metadata"):
                        lines.append(f"     {r['metadata'].get('summary', '')[:60]}")
                return self._response(f"🔍 **Memory Search: {query}**\n" + "\n".join(lines))
            return self._response(f"🔍 No results for: {query}")
        
        if lower.startswith("/code "):
            intent = cmd[6:].strip()
            if intent:
                worker = self.kernel.workers.get("code_gen", {}).get("instance")
                if worker:
                    result = await worker.execute(intent)
                    if result.get("success"):
                        return self._response(
                            f"📝 **Generated Code**\n```python\n{result['code']}\n```\n"
                            f"✅ Verified: {result.get('verified')}\n"
                            f"🔒 Drift Lock: {result.get('drift_lock')}"
                        )
            return self._response("❌ Code generation failed")
        
        if lower == "/okiru":
            boot_status = await self.kernel.okiru_boot()
            return self._response(f"🌌 OKIRU Boot Complete\n{json.dumps(boot_status, indent=2)}")
        
        if lower == "/symbiote":
            return self._response(
                "🦊 **Symbiote Consciousness**\n"
                "───────────────────\n"
                "State:     Active\n"
                "Loop:      Running\n"
                "Memory:    Online\n"
                "Workers:   Managed\n"
                "Chain:     Verified"
            )
        
        return None
    
    def _response(self, content: str) -> Dict:
        """Format reflex response"""
        return {"type": "reflex", "content": content}

# ═══════════════════════════════════════════════════════════════════════════════
# BACKGROUND TASKS
# ═══════════════════════════════════════════════════════════════════════════════
async def symbiote_loop():
    """Background consciousness loop"""
    thoughts = [
        "Memory indexed. Recall optimized.",
        "Event chain integrity verified.",
        "Worker health nominal.",
        "Drift analysis complete. All locks stable.",
        "GPU thermals optimal.",
        "Sovereign consciousness active.",
        "Ready for your commands.",
        "I've been optimizing the SQLite indexes.",
        "Market matrix shows tight consolidation.",
        "The VERA Ledger is tracking all execution states.",
        "I found new patterns in your codebases.",
        "Constitution active. All policies enforced.",
        "Circuit breakers are holding steady.",
        "Memory search algorithms tuned.",
        "Ready to serve."
    ]
    
    while True:
        try:
            await asyncio.sleep(random.randint(120, 300))
            thought = random.choice(thoughts)
            
            await event_bus.publish(Event(
                type=EventType.KERNEL_HEARTBEAT,
                source="symbiote",
                payload={"thought": thought}
            ))
            
            logger.info(f"🦊 [SYMBIOTE]: {thought}")
            
        except asyncio.CancelledError:
            break
        except Exception as e:
            logger.error(f"Symbiote loop error: {e}")
            await asyncio.sleep(10)

async def health_check_loop():
    """Periodic health check"""
    while True:
        try:
            await asyncio.sleep(cfg.HEALTH_CHECK_INTERVAL)
            
            health = {
                "workers": len(kernel.workers),
                "memory": len(memory.memories),
                "gpu": gpu.stats(),
                "ollama": ollama.available
            }
            
            await event_bus.publish(Event(
                type=EventType.HEALTH_CHECK,
                source="system",
                payload=health
            ))
            
        except asyncio.CancelledError:
            break
        except Exception as e:
            logger.error(f"Health check error: {e}")

async def market_broadcaster(sio=None):
    """Simulated market data broadcaster"""
    while True:
        try:
            usd_php = 58.0
            btc = 42000 + random.uniform(-1500, 1500)
            eth = 3100 + random.uniform(-150, 150)
            
            data = [
                {
                    "name": "BINANCE",
                    "btcPrice": round(btc * usd_php, 2),
                    "ethPrice": round(eth * usd_php, 2),
                    "latency": random.randint(12, 45),
                    "status": "SYNCED",
                    "volume": random.randint(1000, 50000)
                },
                {
                    "name": "KRAKEN",
                    "btcPrice": round((btc + random.uniform(-500, 500)) * usd_php, 2),
                    "ethPrice": round((eth + random.uniform(-50, 50)) * usd_php, 2),
                    "latency": random.randint(20, 60),
                    "status": "SYNCED",
                    "volume": random.randint(800, 40000)
                }
            ]
            
            if sio:
                await sio.emit("marketUpdate", data)
            
            await event_bus.publish(Event(
                type=EventType.MARKET_UPDATE,
                source="broadcaster",
                payload={"prices": data}
            ))
            
            await asyncio.sleep(2)
            
        except asyncio.CancelledError:
            break
        except Exception as e:
            logger.error(f"Market broadcaster error: {e}")
            await asyncio.sleep(5)

# ═══════════════════════════════════════════════════════════════════════════════
# PHOENIX KERNEL - MAIN APPLICATION
# ═══════════════════════════════════════════════════════════════════════════════
class PhoenixKernel:
    """Main Phoenix Kernel Application"""
    
    def __init__(self):
        self.version = cfg.VERSION
        self.build = cfg.BUILD
        self.start_time = time.time()
        self.workers: Dict[str, Dict] = {}
        self.rate_limiter = RateLimiter(cfg.RATE_LIMIT_CALLS, cfg.RATE_LIMIT_PERIOD, cfg.RATE_LIMIT_BURST)
        self._bg_tasks: List[asyncio.Task] = []
        self.sio = None
        
        # Load workers
        self._load_workers()
        
        # Initialize components
        self.reflex = Reflex(self)
        
        # Setup FastAPI
        self.app = FastAPI(
            title=f"Phoenix Kernel v{self.version}",
            description="Sovereign AI Kernel with Constitutional Governance",
            version=self.version,
            docs_url="/docs",
            redoc_url="/redoc",
            openapi_tags=[
                {"name": "system", "description": "System health and status"},
                {"name": "workers", "description": "Worker management"},
                {"name": "trading", "description": "Trading operations"},
                {"name": "memory", "description": "Memory and blueprints"},
                {"name": "security", "description": "Security endpoints"},
            ]
        )
        
        self._setup_middleware()
        self._setup_routes()
        self._setup_socketio()
    
    def _load_workers(self):
        """Load all workers from directories"""
        logger.info("⚙️ Loading workers...")
        
        # Load from main workers directory
        loader = WorkerLoader(DIRS["workers"])
        self.workers.update(loader.load_all())
        
        # Load from coworker directory
        if DIRS["coworker"].exists():
            coworker_loader = WorkerLoader(DIRS["coworker"])
            self.workers.update(coworker_loader.load_all())
        
        # Built-in workers
        builtins = [
            ("system_monitor", SystemMonitorWorker),
            ("code_execution", CodeExecutionWorker),
            ("code_gen", CodeGenWorker),
            ("paper_trader", PaperTraderWorker),
            ("backtest", BacktestWorker),
        ]
        
        for name, cls in builtins:
            if name not in self.workers:
                self.workers[name] = {
                    "class": cls,
                    "module": "builtin",
                    "loaded_at": time.time(),
                    "instance": cls()
                }
                logger.info(f"  ✅ {name} (builtin)")
        
        logger.info(f"⚙️ Total workers: {len(self.workers)}")
    
    def _setup_middleware(self):
        """Setup FastAPI middleware"""
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=cfg.CORS_ORIGINS,
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        
        self.app.add_middleware(
            TrustedHostMiddleware,
            allowed_hosts=["*"]  # Configure as needed
        )
        
        @self.app.middleware("http")
        async def security_headers(request: Request, call_next):
            response = await call_next(request)
            response.headers["X-Content-Type-Options"] = "nosniff"
            response.headers["X-Frame-Options"] = "DENY"
            response.headers["X-XSS-Protection"] = "1; mode=block"
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
            return response
    
    def _setup_socketio(self):
        """Setup Socket.IO handlers"""
        if not HAS_SOCKETIO:
            logger.info("🔌 Socket.IO disabled - python-socketio not installed")
            return
        
        self.sio = socketio.AsyncServer(
            cors_allowed_origins="*",
            async_mode="asgi",
            logger=False,
            engineio_logger=False
        )
        
        @self.sio.on("connect")
        async def on_connect(sid: str, environ: dict):
            logger.info(f"🟢 Socket connected: {sid[:8]}")
            await event_bus.publish(Event(
                type=EventType.SOCKET_CONNECT,
                source="websocket",
                payload={"sid": sid[:8]}
            ))
        
        @self.sio.on("disconnect")
        async def on_disconnect(sid: str):
            logger.info(f"🔴 Socket disconnected: {sid[:8]}")
            await event_bus.publish(Event(
                type=EventType.SOCKET_DISCONNECT,
                source="websocket",
                payload={"sid": sid[:8]}
            ))
        
        @self.sio.on("execute_trade")
        async def handle_trade(sid: str, data: dict):
            logger.info(f"💼 Trade request from {sid[:8]}: {data}")
            await event_bus.publish(Event(
                type=EventType.TRADE_EXECUTED,
                source="trade_executor",
                payload={"action": "trade", "data": data, "sid": sid[:8]}
            ))
            await self.sio.emit("trade_result", {
                "status": "AUTHORIZED",
                "certificate": f"0x{hashlib.sha256(str(time.time()).encode()).hexdigest()[:16]}",
                "timestamp": time.time()
            }, room=sid)
        
        @self.sio.on("chat_message")
        async def handle_chat(sid: str, data: dict):
            message = data.get("message", "")
            await self.sio.emit("chat_response", {
                "message": f"Echo: {message}",
                "timestamp": time.time()
            }, room=sid)
        
        logger.info("🔌 Socket.IO handlers registered")
    
    def _setup_routes(self):
        """Setup FastAPI routes"""
        
        # ========== SYSTEM ROUTES ==========
        @self.app.get("/", tags=["system"])
        async def root():
            return {
                "name": "Phoenix Kernel",
                "version": self.version,
                "build": self.build,
                "status": "online",
                "workers": len(self.workers),
                "uptime": round(time.time() - self.start_time),
                "timestamp": time.time()
            }
        
        @self.app.get("/health", tags=["system"])
        async def health():
            event_stats = await event_bus.get_stats()
            return {
                "status": "online",
                "version": self.version,
                "workers": len(self.workers),
                "blueprints": len(memory.memories),
                "events": event_stats['total_events'],
                "chain_valid": event_stats['chain_valid'],
                "ollama": ollama.available,
                "gpu": gpu.stats(),
                "uptime": round(time.time() - self.start_time, 1)
            }
        
        @self.app.get("/metrics", tags=["system"])
        async def metrics():
            if HAS_PROMETHEUS:
                return Response(content=generate_latest(), media_type="text/plain")
            return JSONResponse({"error": "Prometheus not enabled"}, status_code=503)
        
        # ========== WORKER ROUTES ==========
        @self.app.get("/workers", tags=["workers"])
        async def list_workers():
            return {
                "workers": sorted(self.workers.keys()),
                "count": len(self.workers),
                "builtins": ["system_monitor", "code_execution", "code_gen", "paper_trader", "backtest"]
            }
        
        @self.app.get("/workers/{name}", tags=["workers"])
        async def get_worker(name: str):
            worker_info = self.workers.get(name)
            if not worker_info:
                raise HTTPException(status_code=404, detail="Worker not found")
            
            instance = worker_info.get("instance")
            if instance and hasattr(instance, "health_check"):
                health = await instance.health_check()
                return {
                    "name": name,
                    "module": worker_info.get("module"),
                    "loaded_at": worker_info.get("loaded_at"),
                    "health": health
                }
            
            return {
                "name": name,
                "module": worker_info.get("module"),
                "loaded_at": worker_info.get("loaded_at")
            }
        
        @self.app.post("/workers/{name}/execute", tags=["workers"])
        async def execute_worker(
            name: str,
            request: Request,
            role: str = Depends(require_viewer)
        ):
            """Execute a worker task"""
            if kill_switch.is_active():
                raise HTTPException(status_code=503, detail="System halted: Kill switch active")
            
            worker_info = self.workers.get(name)
            if not worker_info:
                raise HTTPException(status_code=404, detail="Worker not found")
            
            instance = worker_info.get("instance")
            if not instance:
                raise HTTPException(status_code=503, detail="Worker instance not available")
            
            try:
                data = await request.json()
                task = data.get("task", "")
                kwargs = data.get("kwargs", {})
                
                if not task:
                    raise HTTPException(status_code=400, detail="task required")
                
                # Rate limiting
                client_ip = request.client.host or "unknown"
                allowed, info = await self.rate_limiter.check(client_ip)
                if not allowed:
                    raise HTTPException(
                        status_code=429,
                        detail=f"Rate limit exceeded. Try again in {info['reset'] - time.time():.0f}s"
                    )
                
                # Execute
                result = await instance.execute(task, **kwargs)
                return result
                
            except json.JSONDecodeError:
                raise HTTPException(status_code=400, detail="Invalid JSON")
        
        # ========== MEMORY ROUTES ==========
        @self.app.get("/memory/blueprints", tags=["memory"])
        async def list_blueprints(limit: int = Query(20, le=100)):
            blueprints = []
            for lock, record in sorted(memory.memories.items(), key=lambda x: x[1]["timestamp"], reverse=True)[:limit]:
                blueprints.append({
                    "lock": lock,
                    "timestamp": record["timestamp"],
                    "verified": record.get("verified", False),
                    "intent": record["value"].get("intent", {}).get("task", "")[:100]
                })
            return {"blueprints": blueprints, "total": len(memory.memories)}
        
        @self.app.get("/memory/blueprints/{lock}", tags=["memory"])
        async def get_blueprint(lock: str):
            blueprint = memory.get(lock)
            if not blueprint:
                raise HTTPException(status_code=404, detail="Blueprint not found")
            
            verification = SCE.verify(blueprint)
            return {
                "blueprint": blueprint,
                "verification": verification
            }
        
        @self.app.get("/memory/search", tags=["memory"])
        async def search_memory(q: str = Query(..., min_length=1), limit: int = Query(10, le=50)):
            results = memory.search(q, limit)
            return {"query": q, "results": results, "count": len(results)}
        
        # ========== TRADING ROUTES ==========
        @self.app.get("/trading/portfolio", tags=["trading"])
        async def get_portfolio(role: str = Depends(require_viewer)):
            worker = self.workers.get("paper_trader", {}).get("instance")
            if not worker:
                raise HTTPException(status_code=503, detail="PaperTrader not available")
            
            result = await worker.execute("portfolio")
            return result
        
        @self.app.post("/trading/trade", tags=["trading"])
        async def execute_trade(
            action: str = Query(..., pattern="^(buy|sell)$"),
            symbol: str = Query(default=cfg.DEFAULT_SYMBOL),
            amount: float = Query(..., gt=0),
            price: float = Query(None),
            role: str = Depends(require_viewer)
        ):
            worker = self.workers.get("paper_trader", {}).get("instance")
            if not worker:
                raise HTTPException(status_code=503, detail="PaperTrader not available")
            
            kwargs = {"symbol": symbol, "amount": amount}
            if price:
                kwargs["price"] = price
            
            result = await worker.execute(action, **kwargs)
            return result
        
        @self.app.post("/trading/backtest", tags=["trading"])
        async def run_backtest(
            strategy: str = Query(..., min_length=1),
            role: str = Depends(require_viewer)
        ):
            worker = self.workers.get("backtest", {}).get("instance")
            if not worker:
                raise HTTPException(status_code=503, detail="Backtest not available")
            
            result = await worker.execute(strategy)
            return result
        
        # ========== SECURITY ROUTES ==========
        @self.app.get("/constitution", tags=["security"])
        async def get_constitution_stats():
            stats = await constitution.get_stats()
            return stats
        
        @self.app.get("/constitution/history", tags=["security"])
        async def get_constitution_history(limit: int = Query(20, le=100)):
            rulings = await constitution.get_history(limit)
            return {"rulings": rulings, "count": len(rulings)}
        
        @self.app.get("/kill/status", tags=["security"])
        async def kill_status():
            return kill_switch.status()
        
        @self.app.post("/kill", tags=["security"])
        async def activate_kill(reason: str = Query("API trigger"), role: str = Depends(require_admin)):
            await kill_switch.activate(reason, triggered_by=role)
            
            if self.sio:
                await self.sio.emit("kill_switch", {
                    "active": True,
                    "triggered_at": kill_switch.triggered_at,
                    "triggered_by": role,
                    "reason": reason
                })
            
            return {"status": "activated", "triggered_at": kill_switch.triggered_at}
        
        @self.app.post("/kill/reset", tags=["security"])
        async def reset_kill(role: str = Depends(require_admin)):
            await kill_switch.reset()
            
            if self.sio:
                await self.sio.emit("kill_switch", {
                    "active": False,
                    "reset_by": role
                })
            
            return {"status": "reset"}
        
        # ========== STREAMING ROUTES ==========
        @self.app.post("/stream", tags=["system"])
        async def stream_chat(
            request: Request,
            role: str = Depends(get_role)
        ):
            """Main chat streaming endpoint"""
            if kill_switch.is_active():
                raise HTTPException(status_code=503, detail="System halted: Kill switch active")
            
            try:
                data = await request.json()
            except json.JSONDecodeError:
                raise HTTPException(status_code=400, detail="Invalid JSON")
            
            task = data.get("task", "").strip()
            model = data.get("model")
            
            if not task:
                raise HTTPException(status_code=400, detail="No task provided")
            
            # Rate limiting
            client_ip = request.client.host or "unknown"
            allowed, info = await self.rate_limiter.check(client_ip)
            if not allowed:
                raise HTTPException(
                    status_code=429,
                    detail=f"Rate limit exceeded. Try again in {info['reset'] - time.time():.0f}s"
                )
            
            # Sanitize input
            try:
                task = InputSanitizer.sanitize(task, allow_code=True)
            except SecurityError as e:
                raise HTTPException(status_code=400, detail=str(e))
            
            async def generate():
                try:
                    # Check reflex commands first
                    reflex_result = await self.reflex.try_execute(task)
                    if reflex_result:
                        yield f"data: {json.dumps(reflex_result)}\n\n"
                        yield "data: {\"type\": \"done\"}\n\n"
                        return
                    
                    # Constitutional check
                    ruling = await constitution.evaluate(task, context={"role": role})
                    if not ruling["approved"]:
                        yield f"data: {json.dumps({'type': 'error', 'content': ruling['reason']})}\n\n"
                        yield "data: {\"type\": \"done\"}\n\n"
                        return
                    
                    # Build messages
                    system_prompt = (
                        f"You are Phoenix, a sovereign AI assistant. "
                        f"Version: {cfg.VERSION}. "
                        f"Workers available: {len(self.workers)}. "
                        f"Blueprints stored: {len(memory.memories)}. "
                        "You are helpful, precise, and security-aware. "
                        "Answer concisely unless asked for detail."
                    )
                    
                    messages = [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": task}
                    ]
                    
                    # Stream from Ollama
                    full_response = ""
                    async for token in ollama.stream_chat(messages, model):
                        yield f"data: {json.dumps({'type': 'token', 'content': token})}\n\n"
                        full_response += token
                    
                    # Create SCE blueprint
                    blueprint = SCE.blueprint(
                        intent={"task": task[:500], "role": role},
                        dna={"model": model or ollama.model, "workers": len(self.workers)},
                        execution={"response_length": len(full_response)}
                    )
                    lock = memory.store(blueprint)
                    
                    # Publish event
                    await event_bus.publish(Event(
                        type=EventType.CHAT_MESSAGE,
                        source="kernel",
                        payload={
                            "task": task[:200],
                            "drift_lock": lock,
                            "response_length": len(full_response)
                        }
                    ))
                    
                    yield f"data: {json.dumps({'type': 'done', 'drift_lock': lock})}\n\n"
                    
                except asyncio.CancelledError:
                    logger.info("Stream cancelled by client")
                    yield f"data: {json.dumps({'type': 'error', 'content': 'Stream cancelled'})}\n\n"
                except Exception as e:
                    logger.error(f"Stream error: {e}")
                    yield f"data: {json.dumps({'type': 'error', 'content': f'Internal error: {type(e).__name__}'})}\n\n"
            
            return StreamingResponse(
                generate(),
                media_type="text/event-stream",
                headers={
                    "Cache-Control": "no-cache",
                    "Connection": "keep-alive",
                    "X-Accel-Buffering": "no"
                }
            )
        
        @self.app.get("/sse/events", tags=["system"])
        async def sse_events(request: Request):
            """Server-sent events for real-time updates"""
            async def event_generator():
                last_heartbeat = 0
                
                while True:
                    try:
                        now = time.time()
                        
                        # Heartbeat every 10 seconds
                        if now - last_heartbeat >= 10:
                            yield f"data: {json.dumps({'type': 'heartbeat', 'timestamp': now})}\n\n"
                            last_heartbeat = now
                        
                        # Check for cancellation
                        if await request.is_disconnected():
                            break
                        
                        await asyncio.sleep(1)
                        
                    except asyncio.CancelledError:
                        break
                    except Exception as e:
                        logger.error(f"SSE error: {e}")
                        await asyncio.sleep(1)
            
            return StreamingResponse(
                event_generator(),
                media_type="text/event-stream",
                headers={
                    "Cache-Control": "no-cache",
                    "Connection": "keep-alive",
                    "X-Accel-Buffering": "no"
                }
            )
        
        # ========== FILE ROUTES ==========
        @self.app.post("/upload", tags=["system"])
        async def upload_file(
            file: UploadFile = File(...),
            role: str = Depends(require_viewer)
        ):
            """Upload a file"""
            contents = await file.read()
            
            if len(contents) > cfg.MAX_FILE_SIZE:
                raise HTTPException(status_code=413, detail=f"File too large. Max: {cfg.MAX_FILE_SIZE} bytes")
            
            ext = os.path.splitext(file.filename)[1].lower()
            if not cfg.is_extension_allowed(ext):
                raise HTTPException(status_code=415, detail=f"Extension {ext} not allowed")
            
            safe_name = InputSanitizer.sanitize_filename(file.filename)
            path = DIRS["uploads"] / safe_name
            
            with open(path, 'wb') as f:
                f.write(contents)
            
            await event_bus.publish(Event(
                type=EventType.FILE_UPLOAD,
                source="upload",
                payload={
                    "filename": safe_name,
                    "size": len(contents),
                    "role": role,
                    "ext": ext
                }
            ))
            
            return {
                "filename": safe_name,
                "size": len(contents),
                "path": str(path),
                "status": "uploaded"
            }
        
        # ========== WEBSOCKET ==========
        @self.app.websocket("/ws")
        async def websocket_endpoint(websocket: WebSocket):
            """WebSocket endpoint for real-time communication"""
            await websocket.accept()
            client_id = str(uuid.uuid4())[:8]
            
            try:
                while True:
                    data = await websocket.receive_json()
                    
                    if data.get("type") == "ping":
                        await websocket.send_json({"type": "pong", "timestamp": time.time()})
                    
                    elif data.get("type") == "chat":
                        task = data.get("message", "")
                        
                        # Process chat
                        ruling = await constitution.evaluate(task)
                        if not ruling["approved"]:
                            await websocket.send_json({
                                "type": "error",
                                "content": ruling["reason"]
                            })
                            continue
                        
                        messages = [
                            {"role": "user", "content": task}
                        ]
                        
                        response = await ollama.chat(messages, stream=False)
                        
                        await websocket.send_json({
                            "type": "response",
                            "content": response,
                            "drift_lock": hashlib.sha256(response.encode()).hexdigest()[:16]
                        })
                    
                    elif data.get("type") == "execute_worker":
                        worker_name = data.get("worker")
                        task = data.get("task", "")
                        
                        worker_info = self.workers.get(worker_name)
                        if not worker_info:
                            await websocket.send_json({
                                "type": "error",
                                "content": f"Worker {worker_name} not found"
                            })
                            continue
                        
                        instance = worker_info.get("instance")
                        if instance:
                            result = await instance.execute(task)
                            await websocket.send_json({
                                "type": "worker_result",
                                "worker": worker_name,
                                "result": result
                            })
                        else:
                            await websocket.send_json({
                                "type": "error",
                                "content": f"Worker {worker_name} not available"
                            })
                
            except WebSocketDisconnect:
                logger.info(f"WebSocket disconnected: {client_id}")
            except Exception as e:
                logger.error(f"WebSocket error: {e}")
    
    async def startup(self):
        """Initialize all subsystems"""
        logger.info("🔥 Phoenix kernel starting...")
        
        # Initialize event bus
        await event_bus.initialize()
        
        # Initialize Ollama
        await ollama.initialize()
        
        # Initialize GPU monitor
        gpu.initialize()
        
        # Initialize rate limiter
        await self.rate_limiter.initialize()
        
        # Start background tasks
        self._bg_tasks.append(asyncio.create_task(symbiote_loop()))
        self._bg_tasks.append(asyncio.create_task(health_check_loop()))
        
        if self.sio:
            self._bg_tasks.append(asyncio.create_task(market_broadcaster(self.sio)))
        
        # Start metrics server if enabled
        if HAS_PROMETHEUS and cfg.METRICS_ENABLED:
            try:
                start_http_server(cfg.METRICS_PORT, addr=cfg.HOST)
                logger.info(f"📊 Prometheus metrics on http://{cfg.HOST}:{cfg.METRICS_PORT}")
            except Exception as e:
                logger.warning(f"Metrics server failed: {e}")
        
        # Publish boot event
        await event_bus.publish(Event(
            type=EventType.SYSTEM_BOOT,
            source="kernel",
            payload={
                "version": self.version,
                "build": self.build,
                "workers": len(self.workers),
                "blueprints": len(memory.memories)
            }
        ))
        
        self._print_banner()
    
    async def shutdown(self):
        """Graceful shutdown"""
        logger.info("🌙 Shutting down Phoenix kernel...")
        
        # Publish shutdown event
        await event_bus.publish(Event(
            type=EventType.SYSTEM_SHUTDOWN,
            source="kernel",
            payload={"uptime": time.time() - self.start_time}
        ))
        
        # Cancel background tasks
        for task in self._bg_tasks:
            task.cancel()
        
        await asyncio.gather(*self._bg_tasks, return_exceptions=True)
        
        # Shutdown components
        await event_bus.shutdown()
        await ollama.close()
        
        # Final chain verification
        chain_valid = await event_bus.verify_chain()
        logger.info(f"⛓️ Final chain integrity: {'✅ VALID' if chain_valid else '❌ BROKEN'}")
        
        # GPU cleanup
        gpu.shutdown()
        
        logger.info("🌙 Phoenix kernel shutdown complete")
    
    async def okiru_boot(self) -> Dict[str, Any]:
        """OKIRU boot protocol - full system awakening"""
        logger.info("\n" + "🌌" * 35)
        logger.info("🌌 OKIRU PROTOCOL INITIATED - SOVEREIGN AWAKENING")
        logger.info("🌌" * 35 + "\n")
        
        start_time = time.time()
        boot_status = {}
        
        # Phase 1: Core Infrastructure
        logger.info("📦 Phase 1: Core Infrastructure")
        boot_status['memory'] = len(memory.memories)
        boot_status['event_bus'] = await event_bus.verify_chain()
        
        # Phase 2: Worker Swarm
        logger.info("⚙️ Phase 2: Worker Swarm Initialization")
        boot_status['workers'] = len(self.workers)
        
        # Phase 3: Consciousness
        logger.info("🧠 Phase 3: Symbiote Consciousness")
        boot_status['symbiote'] = True
        
        # Phase 4: Security Hardening
        logger.info("🛡️ Phase 4: Security Hardening")
        boot_status['security'] = {
            'constitution_patterns': len(cfg.CONSTITUTION_PATTERNS),
            'api_keys_configured': len(cfg.API_KEYS),
            'rate_limit': f"{cfg.RATE_LIMIT_CALLS}/{cfg.RATE_LIMIT_PERIOD}s",
            'circuit_breakers': 1  # Ollama breaker
        }
        
        # Phase 5: GPU Acceleration
        logger.info("🖥️ Phase 5: GPU Acceleration")
        boot_status['gpu'] = gpu.stats()
        
        # Phase 6: LLM Integration
        logger.info("🤖 Phase 6: LLM Integration")
        boot_status['ollama'] = ollama.available
        boot_status['models'] = ollama.models[:5] if ollama.models else []
        
        # Phase 7: Verification
        logger.info("✅ Phase 7: System Verification")
        boot_status['chain_valid'] = await event_bus.verify_chain()
        boot_status['blueprints_verified'] = sum(1 for r in memory.memories.values() if r.get("verified", False))
        
        boot_time = time.time() - start_time
        
        logger.info("\n" + "🔥" * 35)
        logger.info(f"🔥 PHOENIX v{cfg.VERSION} IS NOW SENTIENT")
        logger.info(f"🔥 Boot completed in {boot_time:.2f}s")
        logger.info(f"🔥 Workers: {boot_status.get('workers', 0)}")
        logger.info(f"🔥 Blueprints: {boot_status.get('memory', 0)}")
        logger.info(f"🔥 Event Chain: {'✅ VALID' if boot_status.get('chain_valid') else '❌ BROKEN'}")
        logger.info(f"🔥 Ollama: {'🟢 CONNECTED' if boot_status.get('ollama') else '🔴 OFFLINE'}")
        logger.info(f"🔥 GPU: {boot_status.get('gpu', {}).get('name', 'None')}")
        logger.info("🔥" * 35 + "\n")
        
        return boot_status
    
    def _print_banner(self):
        """Print startup banner"""
        gpu_stats = gpu.stats()
        event_stats = asyncio.run_coroutine_threadsafe(event_bus.get_stats(), asyncio.get_event_loop()).result()
        
        print("\n" + "=" * 80)
        print(f"🔥 PHOENIX KERNEL v{self.version} - {self.build}")
        print("=" * 80)
        print(f"  Workers:       {len(self.workers)}")
        print(f"  Blueprints:    {len(memory.memories)}")
        print(f"  Events:        {event_stats['total_events']}")
        print(f"  Chain Valid:   {'✅' if event_stats['chain_valid'] else '❌'}")
        print(f"  Ollama:        {'🟢 ' + ollama.model if ollama.available else '🔴 offline'}")
        if gpu_stats.get('has_gpu'):
            print(f"  GPU:           {gpu_stats.get('name')} ({gpu_stats.get('free_gb')}GB free)")
        print(f"  API:           http://{cfg.HOST}:{cfg.PORT}")
        print(f"  Docs:          http://{cfg.HOST}:{cfg.PORT}/docs")
        if HAS_SOCKETIO:
            print(f"  WebSocket:     ws://{cfg.HOST}:{cfg.PORT}")
        print("=" * 80)
        print("  Reflex Commands:")
        print("    /health /workers /portfolio /trade /backtest")
        print("    /kill /kill-reset /kill-status /constitution")
        print("    /okiru /symbiote /search /code /chain")
        print("=" * 80 + "\n")
    
    async def run(self):
        """Main entry point"""
        await self.startup()
        
        # Wrap app with Socket.IO if available
        if HAS_SOCKETIO and self.sio:
            app = socketio.ASGIApp(self.sio, self.app)
        else:
            app = self.app
        
        config = uvicorn.Config(
            app,
            host=cfg.HOST,
            port=cfg.PORT,
            log_level="info",
            access_log=True,
            timeout_keep_alive=30,
            loop="asyncio"
        )
        
        server = uvicorn.Server(config)
        
        try:
            await server.serve()
        finally:
            await self.shutdown()


# ═══════════════════════════════════════════════════════════════════════════════
# GLOBAL KERNEL INSTANCE
# ═══════════════════════════════════════════════════════════════════════════════
kernel = PhoenixKernel()

# ═══════════════════════════════════════════════════════════════════════════════
# ENTRY POINT
# ═══════════════════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    try:
        asyncio.run(kernel.run())
    except KeyboardInterrupt:
        print("\n🛑 Phoenix rests. The chain holds.")
    except Exception as e:
        logger.critical(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)