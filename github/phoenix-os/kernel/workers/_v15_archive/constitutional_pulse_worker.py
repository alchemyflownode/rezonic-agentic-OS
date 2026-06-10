# D:\Rezonic_Agentic\apps\phoenix-kernel\workers\constitutional_pulse_worker.py
"""
ReZ Trader Constitutional Pulse
Wraps existing constitutional_council_fixed.py and adds confidence scoring
"""

import asyncio
import time  # ← FIXED: Added missing import
from typing import Dict, Optional, Any
from datetime import datetime
import logging

logger = logging.getLogger("REZ.PULSE")

class ConstitutionalPulseWorker:
    """
    Sovereign confidence score using your existing constitutional evaluators
    """
    
    def __init__(self, kernel):
        self.kernel = kernel
        self.current_pulse = None
        self._update_task = None
        self._last_error = None
        
        # Try to get existing workers from kernel first
        self.constitutional_council = self._get_worker_instance("constitutional_council_fixed")
        self.ai_trader = self._get_worker_instance("ai_trader")
        self.risk_worker = self._get_worker_instance("risk")
        
        # Log what we found
        logger.info(f"💗 Pulse Worker initialized:")
        logger.info(f"  - Constitutional Council: {'✅' if self.constitutional_council else '⚠️ Missing'}")
        logger.info(f"  - AI Trader: {'✅' if self.ai_trader else '⚠️ Missing'}")
        logger.info(f"  - Risk Worker: {'✅' if self.risk_worker else '⚠️ Missing'}")
    
    def _get_worker_instance(self, worker_name: str) -> Optional[Any]:
        """Safely get worker instance from kernel"""
        worker_info = self.kernel.workers.get(worker_name, {})
        instance = worker_info.get("instance")
        
        if not instance:
            # Try alternative names
            alternatives = {
                "constitutional_council_fixed": ["constitutional_council", "constitutional", "council"],
                "ai_trader": ["ai_trader_worker", "ai", "trader"],
                "risk": ["risk_worker", "risk_manager"]
            }
            
            for alt in alternatives.get(worker_name, []):
                alt_info = self.kernel.workers.get(alt, {})
                if alt_info.get("instance"):
                    logger.debug(f"Found {worker_name} as {alt}")
                    return alt_info["instance"]
        
        return instance
    
    async def start(self, interval_seconds: int = 60):
        """Start pulse updates"""
        if self._update_task and not self._update_task.done():
            logger.warning("Pulse already running")
            return
        
        self._update_task = asyncio.create_task(self._update_loop(interval_seconds))
        logger.info(f"💗 Constitutional Pulse started (interval={interval_seconds}s)")
    
    async def stop(self):
        """Stop pulse updates"""
        if self._update_task:
            self._update_task.cancel()
            try:
                await self._update_task
            except asyncio.CancelledError:
                pass
            self._update_task = None
            logger.info("💗 Constitutional Pulse stopped")
    
    async def _update_loop(self, interval: int):
        """Background pulse calculation loop"""
        while True:
            try:
                pulse = await self.calculate_pulse()
                self.current_pulse = pulse
                
                # Broadcast to frontend via WebSocket
                if self.kernel.sio:
                    await self.kernel.sio.emit("pulse_update", pulse)
                
                await asyncio.sleep(interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                self._last_error = str(e)
                logger.error(f"Pulse update failed: {e}")
                await asyncio.sleep(10)
    
    async def _safe_call(self, worker: Any, method_names: list, default: int = 50) -> int:
        """Safely call a worker method with multiple possible names"""
        if not worker:
            return default
        
        for method_name in method_names:
            if hasattr(worker, method_name) and callable(getattr(worker, method_name)):
                try:
                    result = await getattr(worker, method_name)()
                    
                    # Handle different return types
                    if isinstance(result, dict):
                        # Try common keys
                        for key in ["score", "confidence", "value", "rating"]:
                            if key in result:
                                value = result[key]
                                if isinstance(value, (int, float)):
                                    return int(value)
                        # If no matching key, return first numeric value
                        for key, value in result.items():
                            if isinstance(value, (int, float)):
                                return int(value)
                    elif isinstance(result, (int, float)):
                        return int(result)
                    
                    # If we got here, return default
                    return default
                    
                except Exception as e:
                    logger.debug(f"Method {method_name} failed: {e}")
        
        return default
    
    async def calculate_pulse(self) -> Dict:
        """Calculate using your existing workers with flexible method detection"""
        
        # 1. Constitutional Safety
        constitutional_score = await self._safe_call(
            self.constitutional_council,
            ["evaluate_current_state", "get_score", "assess_risk", "evaluate", "get_constitutional_score"],
            70
        )
        
        # 2. AI Confidence
        ai_score = await self._safe_call(
            self.ai_trader,
            ["analyze_market", "get_confidence", "predict", "analyze"],
            50
        )
        
        # 3. Risk Assessment (higher score = safer)
        risk_percent = await self._safe_call(
            self.risk_worker,
            ["assess_portfolio_risk", "get_risk_score", "evaluate_risk", "calculate_risk"],
            30
        )
        # Convert risk_percent to safety score (100 - risk)
        risk_score = max(0, min(100, 100 - risk_percent))
        
        # Weighted total (40% constitutional, 40% AI, 20% risk)
        total = int(
            constitutional_score * 0.4 +
            ai_score * 0.4 +
            risk_score * 0.2
        )
        
        # Generate recommendation and next action
        if total >= 80:
            recommendation = "✅ Constitutional approval granted"
            next_action = "Consider scaling into position"
            color = "green"
        elif total >= 60:
            recommendation = "🟡 Approach with caution"
            next_action = "Wait for confirmation signals"
            color = "yellow"
        elif total >= 40:
            recommendation = "⚠️ Constitutional concerns detected"
            next_action = "Review rules before trading"
            color = "orange"
        else:
            recommendation = "🔴 Constitutional block recommended"
            next_action = "No trades until conditions improve"
            color = "red"
        
        pulse_data = {
            "total": total,
            "constitutional_safety": constitutional_score,
            "ai_confidence": ai_score,
            "market_risk": risk_score,
            "recommendation": recommendation,
            "next_action": next_action,
            "color": color,
            "timestamp": time.time(),
            "iso_timestamp": datetime.now().isoformat()
        }
        
        # Add debug info if missing workers
        if not self.constitutional_council or not self.ai_trader or not self.risk_worker:
            pulse_data["warning"] = "Some workers not available - using fallback values"
        
        return pulse_data
    
    async def get_pulse(self) -> Dict:
        """Get current pulse (cached)"""
        if self.current_pulse:
            return self.current_pulse
        return await self.calculate_pulse()
    
    async def get_status(self) -> Dict:
        """Get worker status"""
        return {
            "running": self._update_task is not None and not self._update_task.done(),
            "has_constitutional_council": self.constitutional_council is not None,
            "has_ai_trader": self.ai_trader is not None,
            "has_risk_worker": self.risk_worker is not None,
            "last_error": self._last_error,
            "current_pulse": self.current_pulse
        }