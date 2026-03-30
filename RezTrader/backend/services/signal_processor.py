# -*- coding: utf-8 -*-
# backend/services/signal_processor.py
"""
State-aware signal processor with RSI + MACD confluence
Prevents flip-flopping through position state machine
"""
from collections import deque
from enum import Enum
import logging
import time
from typing import Dict, Optional, Any
from backend.services.indicators import IndicatorService

logger = logging.getLogger(__name__)


class PositionState(Enum):
    """Trading position states"""
    FLAT = "FLAT"
    LONG = "LONG"
    SHORT = "SHORT"


class SignalProcessor:
    """
    Stateful signal processor that prevents flip-flopping
    Uses position state machine + MACD confluence for entries
    """
    
    def __init__(self, paper_trader, cooldown_seconds=0):
        self.trader = paper_trader
        self.price_history: Dict[str, deque] = {}
        self.states: Dict[str, Dict] = {}
        self.signals_generated = 0
        
        # Configurable thresholds
        self.rsi_buy_threshold = 30
        self.rsi_sell_threshold = 70
        self.rsi_hysteresis = 5
        self.cooldown_seconds = cooldown_seconds  # 0 for testing, 30 for live
        self.macd_confluence_required = True

    def _get_state(self, symbol: str) -> Dict:
        """Get or initialize state for a symbol"""
        if symbol not in self.states:
            self.states[symbol] = {
                'position': PositionState.FLAT,
                'last_trade_time': 0,
                'entry_price': None,
                'consecutive_signals': 0
            }
        return self.states[symbol]

    async def update_price(self, symbol: str, price: float):
        """Record price and check for trading signals"""
        if symbol not in self.price_history:
            self.price_history[symbol] = deque(maxlen=100)
            logger.info(f"Started tracking {symbol}")

        self.price_history[symbol].append(price)

        # Check signals once we have enough data
        if len(self.price_history[symbol]) >= 35:
            await self._check_signals(symbol, price)

    async def _check_signals(self, symbol: str, price: float):
        """State-aware signal generation with confluence"""
        prices = list(self.price_history[symbol])
        state = self._get_state(symbol)
        now = time.time()

        # Cooldown check
        if now - state['last_trade_time'] < self.cooldown_seconds:
            return

        # Compute indicators
        rsi = IndicatorService.calculate_rsi(prices)
        macd = IndicatorService.compute_macd(prices)

        # Require valid RSI
        if rsi is None:
            return

        # MACD confluence required for ENTRY only (not exits)
        if self.macd_confluence_required and state['position'] == PositionState.FLAT:
            if macd is None or macd.get('histogram') is None or macd.get('status') != 'ok':
                return

        signal = None

        # ENTRY LOGIC (FLAT -> LONG)
        if state['position'] == PositionState.FLAT:
            
            # BUY: RSI oversold + MACD bullish momentum
            if rsi < (self.rsi_buy_threshold - self.rsi_hysteresis):
                if not self.macd_confluence_required or macd['histogram'] > 0:
                    signal = {
                        'action': 'BUY',
                        'price': price,
                        'reason': f'RSI({rsi:.1f})<BUY_ZONE + MACD_bullish'
                    }
                    result = await self.trader.execute("buy", symbol, 0.01)
                    if result.get("success"):
                        self.signals_generated += 1
                        state['position'] = PositionState.LONG
                        state['entry_price'] = price
                        state['last_trade_time'] = now
                        state['consecutive_signals'] = 0
                        logger.info(f"BUY: {symbol} @ {price} | {signal['reason']}")
                    else:
                        logger.warning(f"BUY failed: {result.get('error')}")

            # SELL: RSI overbought + MACD bearish (exit only, no shorting)
            elif rsi > (self.rsi_sell_threshold + self.rsi_hysteresis):
                if not self.macd_confluence_required or macd['histogram'] < 0:
                    if self.trader.positions.get(symbol, 0) > 0:
                        signal = {
                            'action': 'SELL',
                            'price': price,
                            'reason': f'RSI({rsi:.1f})>SELL_ZONE + MACD_bearish'
                        }
                        amount = self.trader.positions[symbol] / 2
                        result = await self.trader.execute("sell", symbol, amount)
                        if result.get("success"):
                            self.signals_generated += 1
                            state['position'] = PositionState.FLAT
                            state['last_trade_time'] = now
                            state['consecutive_signals'] = 0
                            logger.info(f"SELL: {symbol} @ {price} | {signal['reason']}")
                        else:
                            logger.warning(f"SELL failed: {result.get('error')}")

        # EXIT LOGIC (LONG -> FLAT) - NO MACD REQUIRED FOR EXITS
        elif state['position'] == PositionState.LONG:
            # Allow exit with less data than entry
            if len(prices) < 14:
                return
            
            # Exit when RSI returns to neutral or becomes overbought
            # Only RSI required - no MACD confluence for exits
            if rsi > 50:
                signal = {
                    'action': 'EXIT_LONG',
                    'price': price,
                    'reason': f'RSI({rsi:.1f})>50_neutral_exit'
                }
                if self.trader.positions.get(symbol, 0) > 0:
                    result = await self.trader.execute("sell", symbol, self.trader.positions[symbol])
                    if result.get("success"):
                        self.signals_generated += 1
                        state['position'] = PositionState.FLAT
                        state['last_trade_time'] = now
                        state['consecutive_signals'] = 0
                        logger.info(f"EXIT: {symbol} @ {price} | {signal['reason']}")

        # SHORT EXIT LOGIC (Future: if shorting enabled)
        elif state['position'] == PositionState.SHORT:
            if len(prices) < 14:
                return
            if rsi < 50:
                state['position'] = PositionState.FLAT
                state['last_trade_time'] = now
                state['consecutive_signals'] = 0
                logger.info(f"EXIT_SHORT state reset: {symbol}")

        else:
            state['consecutive_signals'] += 1

    def get_stats(self) -> Dict:
        """Get signal processor statistics"""
        return {
            "signals_generated": self.signals_generated,
            "tracked_symbols": list(self.price_history.keys()),
            "active_states": {
                sym: {
                    'position': st['position'].value,
                    'last_trade': st['last_trade_time'],
                    'entry_price': st['entry_price']
                }
                for sym, st in self.states.items()
            }
        }