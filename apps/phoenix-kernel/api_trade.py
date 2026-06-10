# api_trade.py
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime
import psutil

router = APIRouter(prefix="/api/v1", tags=["trading"])

class TradeRequest(BaseModel):
    action: str = Field(..., pattern="^(buy|sell)$")
    symbol: str = Field(..., min_length=1, max_length=10)
    amount: float = Field(..., gt=0, le=1000)
    price: Optional[float] = Field(None, gt=0)

@router.post("/trade")
async def execute_trade(request: TradeRequest):
    from workers.paper_trader_worker import paper_trader
    result = await paper_trader.execute_trade(
        action=request.action,
        symbol=request.symbol,
        amount=request.amount,
        price=request.price
    )
    return result

@router.get("/portfolio")
async def get_portfolio():
    from workers.paper_trader_worker import paper_trader
    return await paper_trader.get_portfolio()

@router.get("/trades")
async def get_trades(limit: int = 50, status: Optional[str] = None):
    from workers.paper_trader_worker import paper_trader
    trades = await paper_trader.get_trade_history(limit, status) if hasattr(paper_trader, 'get_trade_history') else []
    return {"trades": trades, "count": len(trades)}

@router.get("/metrics")
async def get_metrics():
    return {
        "cpu_percent": psutil.cpu_percent(interval=0.5),
        "memory_percent": psutil.virtual_memory().percent,
        "memory_used_gb": psutil.virtual_memory().used / (1024**3),
        "system": "Windows",
        "python_version": "3.10+",
        "timestamp": datetime.now().timestamp()
    }

@router.post("/reset")
async def reset_daily_stats():
    from workers.paper_trader_worker import paper_trader
    await paper_trader.reset_daily_stats()
    return {"success": True, "message": "Daily stats reset"}
