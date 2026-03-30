# strategies/rsi_macd_confluence.py
import time
from enum import Enum

class PositionState(Enum):
    FLAT = "FLAT"
    LONG = "LONG"
    SHORT = "SHORT"

class SignalProcessor:
    def __init__(self):
        self.states = {}  # symbol -> state
        self.cooldown_seconds = 30  # Prevent rapid re-entry
        self.rsi_buy_threshold = 30
        self.rsi_sell_threshold = 70
        self.rsi_hysteresis = 5  # Buffer zone to prevent flip-flop
        self.macd_confluence_required = True  # Require MACD agreement

    def _get_state(self, symbol):
        if symbol not in self.states:
            self.states[symbol] = {
                'position': PositionState.FLAT,
                'last_trade_time': 0,
                'entry_price': None,
                'consecutive_signals': 0
            }
        return self.states[symbol]

    def generate_signal(self, symbol, price, rsi, macd):
        state = self._get_state(symbol)
        now = time.time()

        # 🔒 Cooldown check
        if now - state['last_trade_time'] < self.cooldown_seconds:
            return None

        # 🔒 Require valid indicators
        if rsi is None:
            return None
        if self.macd_confluence_required and (macd is None or macd.get('histogram') is None):
            return None

        signal = None

        # ─── ENTRY LOGIC ───
        if state['position'] == PositionState.FLAT:
            
            # BUY: RSI oversold + MACD bullish momentum
            if rsi < (self.rsi_buy_threshold - self.rsi_hysteresis):
                if not self.macd_confluence_required or macd['histogram'] > 0:
                    signal = {
                        'action': 'BUY',
                        'price': price,
                        'reason': f'RSI({rsi:.1f})<BUY_ZONE + MACD_bullish'
                    }
                    state['position'] = PositionState.LONG
                    state['entry_price'] = price
                    state['last_trade_time'] = now
                    state['consecutive_signals'] = 0

            # SELL: RSI overbought + MACD bearish momentum  
            elif rsi > (self.rsi_sell_threshold + self.rsi_hysteresis):
                if not self.macd_confluence_required or macd['histogram'] < 0:
                    signal = {
                        'action': 'SELL',
                        'price': price,
                        'reason': f'RSI({rsi:.1f})>SELL_ZONE + MACD_bearish'
                    }
                    state['position'] = PositionState.SHORT
                    state['entry_price'] = price
                    state['last_trade_time'] = now
                    state['consecutive_signals'] = 0

        # ─── EXIT LOGIC ───
        elif state['position'] == PositionState.LONG:
            # Exit when RSI returns to neutral (mean reversion)
            if rsi > 50:  # Crossed above midpoint
                signal = {
                    'action': 'EXIT_LONG',
                    'price': price,
                    'reason': f'RSI({rsi:.1f})>50_neutral_exit'
                }
                state['position'] = PositionState.FLAT
                state['last_trade_time'] = now
                state['consecutive_signals'] = 0
            else:
                state['consecutive_signals'] += 1

        elif state['position'] == PositionState.SHORT:
            # Exit when RSI returns to neutral
            if rsi < 50:
                signal = {
                    'action': 'EXIT_SHORT', 
                    'price': price,
                    'reason': f'RSI({rsi:.1f})<50_neutral_exit'
                }
                state['position'] = PositionState.FLAT
                state['last_trade_time'] = now
                state['consecutive_signals'] = 0
            else:
                state['consecutive_signals'] += 1

        return signal