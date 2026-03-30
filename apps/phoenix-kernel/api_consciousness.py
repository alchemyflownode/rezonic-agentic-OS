# api_consciousness.py
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any
from datetime import datetime

router = APIRouter(prefix="/api/v1/consciousness", tags=["consciousness"])

class ConsciousnessControl(BaseModel):
    action: str

@router.get("/state")
async def get_consciousness_state():
    """Get current consciousness state"""
    try:
        from workers.trading_consciousness import trading_consciousness
        return await trading_consciousness.get_consciousness_state()
    except Exception as e:
        return {"status": "error", "message": str(e), "total_simulations": 0, "best_strategy": "none"}

@router.post("/control")
async def control_consciousness(control: ConsciousnessControl):
    """Start or stop the trading consciousness"""
    try:
        from workers.trading_consciousness import trading_consciousness
        if control.action == "start":
            result = await trading_consciousness.start_consciousness()
            return result
        elif control.action == "stop":
            result = await trading_consciousness.stop_consciousness()
            return result
        else:
            raise HTTPException(status_code=400, detail="Invalid action")
    except Exception as e:
        return {"status": "error", "message": str(e)}

@router.get("/insights")
async def get_consciousness_insights():
    """Get AI-generated insights"""
    try:
        from workers.trading_consciousness import trading_consciousness
        state = await trading_consciousness.get_consciousness_state()
        return {
            "market_sentiment": state["consciousness_state"]["market_sentiment"],
            "volatility": state["consciousness_state"]["volatility"],
            "risk_appetite": state["consciousness_state"]["risk_appetite"],
            "learning_progress": f"{state['total_simulations']} simulations processed",
            "recommended_action": "Analyzing market patterns...",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        return {"error": str(e), "market_sentiment": 0, "volatility": 0, "risk_appetite": 0.5}

@router.get("/simulations")
async def get_simulations(limit: int = 100):
    """Get recent simulations"""
    try:
        from workers.trading_consciousness import trading_consciousness
        simulations = list(trading_consciousness.simulation_history)[-limit:]
        return {
            "count": len(simulations),
            "simulations": [
                {
                    "id": s.id,
                    "strategy": s.strategy,
                    "action": s.action,
                    "pnl": s.pnl,
                    "success": s.success,
                    "confidence": s.confidence,
                    "reasoning": s.reasoning,
                    "timestamp": s.timestamp
                }
                for s in simulations
            ]
        }
    except Exception as e:
        return {"count": 0, "simulations": [], "error": str(e)}

@router.post("/autonomous/start")
async def start_autonomous(interval: int = 60):
    """Start autonomous trading"""
    try:
        from workers.trading_consciousness import trading_consciousness
        await trading_consciousness.set_autonomous_mode(True, interval)
        return {"status": "started", "message": f"Autonomous trading started - checking every {interval}s", "interval": interval}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@router.post("/autonomous/stop")
async def stop_autonomous():
    """Stop autonomous trading"""
    try:
        from workers.trading_consciousness import trading_consciousness
        await trading_consciousness.set_autonomous_mode(False)
        return {"status": "stopped", "message": "Autonomous trading stopped"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@router.get("/autonomous/status")
async def get_autonomous_status():
    """Get autonomous trading status"""
    try:
        from workers.trading_consciousness import trading_consciousness
        return {
            "enabled": getattr(trading_consciousness, 'autonomous_enabled', False),
            "interval": getattr(trading_consciousness, 'autonomous_interval', 60),
            "executions": len(getattr(trading_consciousness, 'execution_history', []))
        }
    except Exception as e:
        return {"enabled": False, "interval": 60, "executions": 0, "error": str(e)}

@router.post("/execute")
async def execute_consciousness_trade():
    """Manually execute one trade based on AI analysis"""
    try:
        from workers.trading_consciousness import trading_consciousness
        return await trading_consciousness.execute_best_trade()
    except Exception as e:
        return {"executed": False, "reason": str(e)}

@router.get("/executions")
async def get_execution_history(limit: int = 50):
    """Get history of AI-executed trades"""
    try:
        from workers.trading_consciousness import trading_consciousness
        history = list(getattr(trading_consciousness, 'execution_history', []))[-limit:]
        return {"count": len(history), "executions": history}
    except Exception as e:
        return {"count": 0, "executions": [], "error": str(e)}
