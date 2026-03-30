from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from .core.database import get_db
from .core.security import decode_access_token
from .models.user import User
import datetime

security = HTTPBearer()

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    payload = decode_access_token(credentials.credentials)
    user_id = payload.get("sub")
    
    if user_id is None:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    user = db.query(User).filter(User.id == int(user_id)).first()
    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="User not found")
    
    # Rate limiting
    today = datetime.datetime.utcnow().date()
    if user.last_api_call and user.last_api_call.date() == today:
        user.api_calls_today += 1
    else:
        user.api_calls_today = 1
        user.last_api_call = datetime.datetime.utcnow()
    
    limits = {"free": 100, "pro": 1000, "enterprise": -1}
    max_calls = limits.get(user.subscription_tier.value, 100)
    if max_calls > 0 and user.api_calls_today > max_calls:
        raise HTTPException(status_code=429, detail="Rate limit exceeded")
    
    db.commit()
    return user

async def require_pro_user(user: User = Depends(get_current_user)) -> User:
    if user.subscription_tier.value == "free":
        raise HTTPException(status_code=403, detail="PRO subscription required")
    return user