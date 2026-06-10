# -*- coding: utf-8 -*-
# workers/trading_engine.py
"""
Production-grade trading engine with RSI+MACD confluence
Plugs into Phoenix Kernel via Worker interface
"""
import asyncio
import logging
import time
from collections import deque
from enum import Enum
from typing import Dict, Optional, List, Any

from backend.services.indicators import IndicatorService
from backend.core.event_bus import EventBus  # Your kernel's EventBus
from backend.core.circuit_breaker import CircuitBreaker  # Your kernel's CircuitBreaker

logger = logging.getLogger("PHOENIX.trading_engine")


class PositionState(Enum):
    FLAT = "FLAT"
    LONG = "LONG"
    SHORT = "SHORT"


class TradingEngineWorker:
    """
    Sovereign trading engine with stateful signal processing.
    Integrates with Phoenix Kernel via Worker interface.
    """
    
    def __init__(self, name: str = "trading_engine"):
        self.name = name
        self.created_at = time.time()
        self.execution_count = 0
        self.error_count = 0
        
        # Trading state (per-symbol)
        self.states: Dict[str, Dict] = {}
        self.price_history: Dict[str, deque] = {}
        
        # Configuration (can be overridden via config)
        self.rsi_buy_threshold = 30
        self.rsi_sell_threshold = 70
        self.rsi_hysteresis = 5
        self.cooldown_seconds = 30
        self.macd_confluence_required = True
        self.min_data_for_entry = 35
        self.min_data_for_exit = 14
        
        # References to kernel services (injected at runtime)
        self.event_bus: Optional[EventBus] = None
        self.circuit_breaker: Optional[CircuitBreaker] = None
        self.paper_trader = None  # Will be set to kernel's paper_trader instance
        
        logger.info(f"ðŸ§  TradingEngineWorker initialized: {name}")

    def inject_kernel_services(self, event_bus, circuit_breaker, paper_trader):
        """Inject references to kernel services after worker loading"""
        self.event_bus = event_bus
        self.circuit_breaker = circuit_breaker
        self.paper_trader = paper_trader
        logger.info("âœ… TradingEngineWorker connected to kernel services")

    def _get_state(self, symbol: str) -> Dict:
        if symbol not in self.states:
            self.states[symbol] = {
                'position': PositionState.FLAT,
                'last_trade_time': 0,
                'entry_price': None,
                'consecutive_signals': 0
            }
        return self.states[symbol]

    async def update_price(self, symbol: str, price: float) -> Optional[Dict]:
        """Feed a price update and check for signals"""
        if symbol not in self.price_history:
            self.price_history[symbol] = deque(maxlen=200)
        
        self.price_history[symbol].append(price)
        
        # Only check signals when we have enough data
        if len(self.price_history[symbol]) >= self.min_data_for_exit:
            return await self._check_signals(symbol, price)
        return None

    async def _check_signals(self, symbol: str, price: float) -> Optional[Dict]:
        """State-aware signal generation with confluence"""
        prices = list(self.price_history[symbol])
        state = self._get_state(symbol)
        now = time.time()
        
        # Cooldown check
        if now - state['last_trade_time'] < self.cooldown_seconds:
            return None
        
        # Compute indicators
        rsi = IndicatorService.calculate_rsi(prices)
        macd = IndicatorService.compute_macd(prices)
        
        if rsi is None:
            return None
        
        # MACD confluence required for ENTRY only
        if self.macd_confluence_required and state['position'] == PositionState.FLAT:
            if macd is None or macd.get('histogram') is None or macd.get('status') != 'ok':
                return None
        
        signal = None
        
        # â”€â”€â”€ ENTRY LOGIC â”€â”€â”€
        if state['position'] == PositionState.FLAT:
            if len(prices) < self.min_data_for_entry:
                return None
            
            # BUY: RSI oversold + MACD bullish
            if rsi < 30:
                if macd and macd.get('histogram') and macd['histogram'] > 0:
                    signal = await self._execute_trade(symbol, price, "BUY", rsi, macd)
            
            # SELL: RSI overbought + MACD bearish (exit existing long)
            elif rsi > (self.rsi_sell_threshold + self.rsi_hysteresis):
                if not self.macd_confluence_required or macd['histogram'] < 0:
                    if self.paper_trader and self.paper_trader.positions.get(symbol, 0) > 0:
                        signal = await self._execute_trade(symbol, price, "SELL", rsi, macd, exit_only=True)
        
        # â”€â”€â”€ EXIT LOGIC â”€â”€â”€
        elif state['position'] == PositionState.LONG:
            if len(prices) < self.min_data_for_exit:
                return None
            if rsi > 50:  # Mean reversion exit
                signal = await self._execute_trade(symbol, price, "EXIT_LONG", rsi, None)
        
        elif state['position'] == PositionState.SHORT:
            if len(prices) < self.min_data_for_exit:
                return None
            if rsi < 50:
                state['position'] = PositionState.FLAT
                state['last_trade_time'] = now
                logger.info(f"ðŸ” EXIT_SHORT state reset: {symbol}")
        
        return signal

    async def _execute_trade(self, symbol: str, price: float, action: str, 
                          rsi: float, macd: Optional[Dict], exit_only: bool = False) -> Optional[Dict]:
        """Execute a trade via paper trader and emit events"""
        if not self.paper_trader:
            logger.error("âŒ Paper trader not available")
            return None
        
        state = self._get_state(symbol)
        now = time.time()
        
        try:
            if action == "BUY":
                result = await self.paper_trader.execute("buy", symbol, 0.01)
                if result.get("success"):
                    state['position'] = PositionState.LONG
                    state['entry_price'] = price
                    state['last_trade_time'] = now
                    reason = f"RSI({rsi:.1f})<BUY + MACD_bullish"
                    logger.info(f"âœ… BUY: {symbol} @ {price} | {reason}")
                    
                    # Emit event to kernel
                    if self.event_bus:
                        from core.events import Event, EventType  # Adjust import path
                        await self.event_bus.publish(Event(
                            type=EventType.TRADE_EXECUTED,
                            source="trading_engine",
                            payload={
                                "action": "BUY", "symbol": symbol, "price": price,
                                "rsi": rsi, "macd": macd, "reason": reason
                            }
                        ))
                    
                    return {"action": "BUY", "symbol": symbol, "price": price, "reason": reason}
            
            elif action == "SELL":
                if self.paper_trader.positions.get(symbol, 0) > 0:
                    amount = self.paper_trader.positions[symbol] / 2
                    result = await self.paper_trader.execute("sell", symbol, amount)
                    if result.get("success"):
                        state['position'] = PositionState.FLAT
                        state['last_trade_time'] = now
                        reason = f"RSI({rsi:.1f})>SELL + MACD_bearish"
                        logger.info(f"âœ… SELL: {symbol} @ {price} | {reason}")
                        
                        if self.event_bus:
                            from core.events import Event, EventType
                            await self.event_bus.publish(Event(
                                type=EventType.TRADE_EXECUTED,
                                source="trading_engine",
                                payload={
                                    "action": "SELL", "symbol": symbol, "price": price,
                                    "rsi": rsi, "macd": macd, "reason": reason
                                }
                            ))
                        
                        return {"action": "SELL", "symbol": symbol, "price": price, "reason": reason}
            
            elif action == "EXIT_LONG":
                if self.paper_trader.positions.get(symbol, 0) > 0:
                    result = await self.paper_trader.execute("sell", symbol, self.paper_trader.positions[symbol])
                    if result.get("success"):
                        state['position'] = PositionState.FLAT
                        state['last_trade_time'] = now
                        reason = f"RSI({rsi:.1f})>50_neutral_exit"
                        logger.info(f"âœ… EXIT: {symbol} @ {price} | {reason}")
                        
                        if self.event_bus:
                            from core.events import Event, EventType
                            await self.event_bus.publish(Event(
                                type=EventType.TRADE_EXECUTED,
                                source="trading_engine",
                                payload={
                                    "action": "EXIT_LONG", "symbol": symbol, "price": price,
                                    "rsi": rsi, "reason": reason
                                }
                            ))
                        
                        return {"action": "EXIT_LONG", "symbol": symbol, "price": price, "reason": reason}
        
        except Exception as e:
            self.error_count += 1
            logger.error(f"âŒ Trade execution failed: {e}")
            if self.circuit_breaker:
                self.circuit_breaker.record_failure()
        
        return None

    async def execute(self, task: str, **kwargs) -> Dict[str, Any]:
        """Worker interface: execute trading commands"""
        task_lower = task.lower()
        self.execution_count += 1
        
        try:
            if task_lower.startswith("feed_price"):
                symbol = kwargs.get("symbol", "BTCUSDT")
                price = float(kwargs.get("price", 0))
                signal = await self.update_price(symbol, price)
                return {"success": True, "signal": signal}
            
            elif task_lower == "get_state":
                symbol = kwargs.get("symbol")
                if symbol:
                    state = self._get_state(symbol)
                    return {
                        "success": True,
                        "symbol": symbol,
                        "position": state['position'].value,
                        "entry_price": state['entry_price'],
                        "last_trade": state['last_trade_time']
                    }
                return {"success": True, "states": {
                    sym: {
                        "position": st['position'].value,
                        "entry_price": st['entry_price']
                    } for sym, st in self.states.items()
                }}
            
            elif task_lower == "configure":
                # Allow runtime config updates
                for key, value in kwargs.items():
                    if hasattr(self, key) and key not in ['event_bus', 'circuit_breaker', 'paper_trader']:
                        setattr(self, key, value)
                return {"success": True, "config": {
                    "rsi_buy": self.rsi_buy_threshold,
                    "rsi_sell": self.rsi_sell_threshold,
                    "hysteresis": self.rsi_hysteresis,
                    "cooldown": self.cooldown_seconds
                }}
            
            elif task_lower == "health":
                return await self.health_check()
            
            else:
                return {"success": False, "error": f"Unknown task: {task}"}
        
        except Exception as e:
            self.error_count += 1
            logger.error(f"âŒ execute error: {e}")
            return {"success": False, "error": str(e)}

    async def health_check(self) -> Dict:
        """Worker interface: report health"""
        return {
            "name": self.name,
            "status": "healthy" if self.error_count < 10 else "degraded",
            "executions": self.execution_count,
            "errors": self.error_count,
            "uptime": time.time() - self.created_at,
            "active_positions": sum(
                1 for st in self.states.values() if st['position'] != PositionState.FLAT
            ),
            "tracked_symbols": list(self.price_history.keys())
        }

