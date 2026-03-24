# security/rate_limiter.py
"""Rate limiting for API protection"""

import time
import asyncio
from collections import defaultdict
from typing import Dict, Optional
import logging

logger = logging.getLogger("phoenix.security")

class RateLimiter:
    """
    Token bucket rate limiter for API endpoints
    
    Usage:
        limiter = RateLimiter(rate=100, per_second=10)
        if await limiter.acquire("client_1"):
            # Process request
    """
    
    def __init__(self, rate: int = 100, per_second: int = 10):
        """
        Initialize rate limiter
        
        Args:
            rate: Maximum tokens in bucket
            per_second: Tokens added per second (refill rate)
        """
        self.rate = rate
        self.per_second = per_second
        self.tokens: Dict[str, float] = defaultdict(lambda: rate)
        self.last_update: Dict[str, float] = defaultdict(time.time)
        self._lock = asyncio.Lock()
    
    async def acquire(self, client_id: str, tokens: int = 1) -> bool:
        """
        Acquire tokens for a client
        
        Args:
            client_id: Unique identifier for the client
            tokens: Number of tokens to acquire (default 1)
        
        Returns:
            True if tokens acquired, False if rate limited
        """
        async with self._lock:
            now = time.time()
            
            # Calculate tokens to add
            elapsed = now - self.last_update[client_id]
            self.tokens[client_id] += elapsed * self.per_second
            self.tokens[client_id] = min(self.rate, self.tokens[client_id])
            self.last_update[client_id] = now
            
            # Check if enough tokens
            if self.tokens[client_id] >= tokens:
                self.tokens[client_id] -= tokens
                return True
            else:
                return False
    
    async def wait_and_acquire(self, client_id: str, tokens: int = 1) -> bool:
        """
        Wait until tokens are available, then acquire
        
        Args:
            client_id: Unique identifier for the client
            tokens: Number of tokens to acquire
        
        Returns:
            True when tokens acquired
        """
        while True:
            if await self.acquire(client_id, tokens):
                return True
            await asyncio.sleep(0.1)  # Wait before retry
    
    def get_available_tokens(self, client_id: str) -> float:
        """Get available tokens for a client"""
        now = time.time()
        elapsed = now - self.last_update.get(client_id, now)
        tokens = self.tokens.get(client_id, self.rate)
        tokens += elapsed * self.per_second
        return min(self.rate, tokens)
    
    def reset(self, client_id: str) -> None:
        """Reset rate limit for a client"""
        self.tokens[client_id] = self.rate
        self.last_update[client_id] = time.time()


class PerEndpointLimiter:
    """Rate limiter with per-endpoint configuration"""
    
    def __init__(self, default_limits: dict = None):
        self.default_limits = default_limits or {
            "trading": {"rate": 50, "per_second": 5},
            "market": {"rate": 100, "per_second": 10},
            "auth": {"rate": 20, "per_second": 2},
            "default": {"rate": 30, "per_second": 3}
        }
        self.limiters: Dict[str, RateLimiter] = {}
    
    def _get_limiter(self, endpoint: str) -> RateLimiter:
        """Get or create rate limiter for an endpoint"""
        if endpoint not in self.limiters:
            limits = self.default_limits.get(endpoint, self.default_limits["default"])
            self.limiters[endpoint] = RateLimiter(
                rate=limits["rate"],
                per_second=limits["per_second"]
            )
        return self.limiters[endpoint]
    
    async def check(self, endpoint: str, client_id: str) -> bool:
        """Check if request is allowed"""
        limiter = self._get_limiter(endpoint)
        return await limiter.acquire(client_id)
    
    def get_status(self) -> dict:
        """Get status of all limiters"""
        return {
            endpoint: {
                "available_tokens": limiter.get_available_tokens("status"),
                "rate": limiter.rate,
                "per_second": limiter.per_second
            }
            for endpoint, limiter in self.limiters.items()
        }

__all__ = ['RateLimiter', 'PerEndpointLimiter']