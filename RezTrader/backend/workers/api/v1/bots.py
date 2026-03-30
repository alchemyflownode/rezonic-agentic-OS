from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Dict, Any
from ...core.database import get_db
from ...dependencies import get_current_user
from ...models.user import User
from ...models.bot import BotConfig
from ...services.bot_engine import BotEngineManager

router = APIRouter()

class BotCreate(BaseModel):
    name: str
    strategy: str
    config: Dict[str, Any] = {}

@router.post("/")
async def create_bot(
    bot_data: BotCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Check bot limit per tier
    limits = {"free": 1, "pro": 5, "enterprise": -1}
    max_bots = limits.get(current_user.subscription_tier.value, 1)
    bot_count = db.query(BotConfig).filter(BotConfig.user_id == current_user.id).count()
    
    if max_bots > 0 and bot_count >= max_bots:
        raise HTTPException(status_code=403, detail="Bot limit reached for your tier")
    
    bot = BotConfig(
        user_id=current_user.id,
        name=bot_data.name,
        strategy=bot_data.strategy,
        config=bot_data.config
    )
    db.add(bot)
    db.commit()
    db.refresh(bot)
    return {"id": bot.id, "name": bot.name, "strategy": bot.strategy}

@router.get("/")
async def list_bots(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    bots = db.query(BotConfig).filter(BotConfig.user_id == current_user.id).all()
    return [{"id": b.id, "name": b.name, "strategy": b.strategy, "is_active": b.is_active} for b in bots]

@router.post("/{bot_id}/start")
async def start_bot(
    bot_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    bot = db.query(BotConfig).filter(
        BotConfig.id == bot_id,
        BotConfig.user_id == current_user.id
    ).first()
    if not bot:
        raise HTTPException(status_code=404, detail="Bot not found")
    
    engine = BotEngineManager(db)
    success = await engine.start_bot(bot, current_user)
    if not success:
        raise HTTPException(status_code=400, detail="Bot already running")
    return {"status": "started"}

@router.post("/{bot_id}/stop")
async def stop_bot(
    bot_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    engine = BotEngineManager(db)
    success = await engine.stop_bot(bot_id, current_user.id)
    if not success:
        raise HTTPException(status_code=400, detail="Bot not running")
    return {"status": "stopped"}