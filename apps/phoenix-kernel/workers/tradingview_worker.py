import sys
from pathlib import Path

# Add parent directory to path
parent_dir = Path(__file__).parent.parent
if str(parent_dir) not in sys.path:
    sys.path.insert(0, str(parent_dir))
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
# backend/workers/tradingview_worker.py
from fastapi import APIRouter, Request, HTTPException
import logging
import os
from typing import Dict, Any, Optional
from pydantic import BaseModel

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/tradingview", tags=["tradingview"])
WEBHOOK_SECRET = os.getenv("TRADINGVIEW_WEBHOOK_SECRET", "rez-secret-key-change-me")

class TradingViewAlert(BaseModel):
    token: Optional[str] = None
    ticker: str
    message: str
    price: float
    volume: Optional[float] = None
    time: Optional[str] = None

class TradingViewWorker:
    signature = {
        "id": "tradingview_worker",
        "label": "?? TradingView Bridge",
        "inputs": ["webhook_payload"],
        "outputs": ["trade_signals"],
        "threshold": 0.2,
        "parallel": False
    }
    
    def __init__(self):
        self.webhook_secret = WEBHOOK_SECRET
        self.signals_processed = 0
        
    async def validate_signal(self, alert: TradingViewAlert) -> Dict[str, Any]:
        msg_lower = alert.message.lower()
        signal = "HOLD"
        confidence = 0.5
        
        if any(word in msg_lower for word in ["buy", "long", "bull"]):
            signal = "BUY"
            confidence = 0.85
        elif any(word in msg_lower for word in ["sell", "short", "bear"]):
            signal = "SELL"
            confidence = 0.85
            
        ticker = alert.ticker.replace("BINANCE:", "").replace("BYBIT:", "")
        
        return {
            "source": "tradingview",
            "worker_id": "tradingview_worker",
            "pair": ticker,
            "signal": signal,
            "confidence": confidence,
            "price": alert.price,
            "volume": alert.volume,
            "timestamp": alert.time or "",
            "metadata": {"raw_message": alert.message}
        }

@router.post("/webhook")
async def handle_tradingview_webhook(request: Request):
    try:
        data = await request.json()
        alert = TradingViewAlert(**data)
        
        if alert.token != WEBHOOK_SECRET:
            logger.warning(f"Unauthorized webhook attempt")
            raise HTTPException(status_code=401, detail="Invalid token")
        
        worker = TradingViewWorker()
        signal = await worker.validate_signal(alert)
        worker.signals_processed += 1
        
        return {"status": "success", "signal": signal, "processed": worker.signals_processed}
        
    except Exception as e:
        logger.error(f"TradingView webhook error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/health")
async def health_check():
    return {
        "worker": "tradingview_worker",
        "status": "online",
        "webhook_secret_configured": WEBHOOK_SECRET != "rez-secret-key-change-me"
    }


    async def process(self, task: str, memory_bus=None):
        """Process task â€“ auto-generated stub"""
        return {"content": f"Processed: {task[:50]}", "worker": self.name}
    
    async def health_check(self):
        """Return worker health status"""
        return {"worker": self.name, "status": "healthy", "timestamp": __import__('time').time()}


