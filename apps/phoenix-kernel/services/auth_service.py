"""
Auth Service - Handles API key authentication and rate limiting
"""

import secrets
import time
import hashlib
from typing import Dict, Optional, Set
from dataclasses import dataclass
from fastapi import HTTPException

@dataclass
class ApiKey:
    key: str
    role: str
    created_at: float
    last_used: float
    rate_limit: int = 100  # requests per minute

class AuthManager:
    def __init__(self):
        self._keys: Dict[str, ApiKey] = {}
        self._rate_limits: Dict[str, list] = {}
        self._initialize_default_keys()
    
    def _initialize_default_keys(self):
        """Initialize with default admin key"""
        admin_key = "rez-hive-admin-key-2026"
        self._keys[admin_key] = ApiKey(
            key=admin_key,
            role="admin",
            created_at=time.time(),
            last_used=0
        )
    
    def generate_key(self, role: str = "viewer") -> str:
        """Generate a new API key"""
        key = secrets.token_urlsafe(32)
        self._keys[key] = ApiKey(
            key=key,
            role=role,
            created_at=time.time(),
            last_used=0
        )
        return key
    
    def verify_key(self, api_key: Optional[str], client_ip: str = None) -> str:
        """Verify API key and return role"""
        if not api_key:
            raise HTTPException(status_code=403, detail="API key required")
        
        key_info = self._keys.get(api_key)
        if not key_info:
            raise HTTPException(status_code=403, detail="Invalid API key")
        
        # Update last used
        key_info.last_used = time.time()
        
        # Rate limiting
        if client_ip:
            self._check_rate_limit(client_ip, key_info.rate_limit)
        
        return key_info.role
    
    def _check_rate_limit(self, client_ip: str, limit: int):
        """Enforce rate limiting"""
        now = time.time()
        if client_ip not in self._rate_limits:
            self._rate_limits[client_ip] = []
        
        # Clean old requests
        self._rate_limits[client_ip] = [
            t for t in self._rate_limits[client_ip] 
            if t > now - 60
        ]
        
        if len(self._rate_limits[client_ip]) >= limit:
            raise HTTPException(status_code=429, detail="Rate limit exceeded")
        
        self._rate_limits[client_ip].append(now)
    
    def list_keys(self) -> list:
        """List all API keys (admin only)"""
        return [
            {
                "key": k.key[:8] + "...",
                "role": k.role,
                "created": k.created_at,
                "last_used": k.last_used
            }
            for k in self._keys.values()
        ]
    
    def revoke_key(self, api_key: str) -> bool:
        """Revoke an API key"""
        if api_key in self._keys:
            del self._keys[api_key]
            return True
        return False
    
    def require_role(self, required_role: str):
        """Dependency for FastAPI routes"""
        async def dep(
            api_key: Optional[str] = None,
            request: Optional[object] = None
        ) -> str:
            client_ip = None
            if request and hasattr(request, 'client'):
                client_ip = request.client.host if request.client else None
            
            # Extract API key from various sources
            if api_key:
                key = api_key
            elif hasattr(request, 'headers'):
                key = request.headers.get("X-Hive-API-Key")
            else:
                key = None
            
            role = self.verify_key(key, client_ip)
            if required_role == "admin" and role != "admin":
                raise HTTPException(status_code=403, detail="Admin access required")
            return role
        
        return dep

# Singleton instance for global use
auth_manager = AuthManager()