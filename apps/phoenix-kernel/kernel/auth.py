# kernel/auth.py
"""
Authentication and authorization for Phoenix Kernel.
"""

import jwt
import bcrypt
from datetime import datetime, timedelta
from typing import Dict, Optional
from fastapi import HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from .config import config

security = HTTPBearer(auto_error=False)

class AuthManager:
    """JWT-based authentication manager"""
    
    @staticmethod
    def hash_password(password: str) -> str:
        """Hash a password using bcrypt"""
        salt = bcrypt.gensalt()
        return bcrypt.hashpw(password.encode(), salt).decode()
    
    @staticmethod
    def verify_password(password: str, hashed: str) -> bool:
        """Verify a password against its hash"""
        return bcrypt.checkpw(password.encode(), hashed.encode())
    
    @staticmethod
    def create_token(user_id: str, role: str = "user") -> str:
        """Create a JWT token for a user"""
        payload = {
            "user_id": user_id,
            "role": role,
            "exp": datetime.utcnow() + timedelta(minutes=config.access_token_expire_minutes),
            "iat": datetime.utcnow()
        }
        return jwt.encode(payload, config.jwt_secret, algorithm=config.jwt_algorithm)
    
    @staticmethod
    def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Dict:
        """Verify and decode a JWT token"""
        if not credentials:
            raise HTTPException(status_code=401, detail="Missing authentication")
        
        token = credentials.credentials
        try:
            return jwt.decode(token, config.jwt_secret, algorithms=[config.jwt_algorithm])
        except jwt.ExpiredSignatureError:
            raise HTTPException(status_code=401, detail="Token expired")
        except jwt.InvalidTokenError:
            raise HTTPException(status_code=401, detail="Invalid token")
