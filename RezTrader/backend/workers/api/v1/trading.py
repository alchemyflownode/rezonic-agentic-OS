from fastapi import APIRouter, Depends, HTTPException
from ..dependencies import require_active_user
from ...models.user import User
from ...workers.paper_trader import PaperTrader

router = APIRouter()

@router.post("/trade")
async def execute_trade(
    action: str,  # "buy" or "sell"
    symbol: str,
    amount: float,
    price: float = None,
    current_user: User = Depends(require_active_user)
):
    # In real app: fetch price from exchange if not provided
    if price is None:
        price = 50000  # Mock price
    
    trader = PaperTrader(user_id=current_user.id)
    result = await trader.execute(
        task=f"{action} {symbol}",
        symbol=symbol,
        amount=amount,
        price=price
    )
    
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["error"])
    
    # In real app: log to simplified event store (not VERA yet)
    return result

@router.get("/portfolio")
async def get_portfolio(current_user: User = Depends(require_active_user)):
    # Mock portfolio - in real app: fetch from DB
    return {
        "balance": 1_000_000.0,
        "positions": {"BTCUSDT": 0.5, "ETHUSDT": 2.0},
        "total_value": 1_025_000.0
    }