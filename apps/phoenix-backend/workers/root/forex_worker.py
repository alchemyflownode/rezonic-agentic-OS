import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
# backend/workers/forex_worker.py
import pandas as pd
import numpy as np
from typing import Dict, Any

class ForexWorker:
    signature = {'id': 'forex_worker', 'label': '?? Forex Trader'}
    
    def __init__(self):
        self.major_pairs = ['EUR/USD', 'GBP/USD', 'USD/JPY', 'USD/CHF']
    
    def _calculate_rsi(self, prices, period=14):
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        return 100 - (100 / (1 + rs))
    
    async def _process_impl(self, **kwargs) -> Dict[str, Any]:
        pair = kwargs.get('pair', 'EUR/USD')
        data = kwargs.get('data', [])
        if not data:
            return {'error': 'No data', 'pair': pair}
        df = pd.DataFrame(data, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        df['rsi'] = self._calculate_rsi(df['close'])
        current = df.iloc[-1]
        signal = 'BUY' if current['rsi'] < 30 else 'SELL' if current['rsi'] > 70 else 'HOLD'
        return {
            'worker_id': 'forex_worker',
            'pair': pair,
            'signal': signal,
            'price_usd': round(current['close'], 4),
            'price_php': round(current['close'] * 58, 2),
            'timestamp': int(current['timestamp'])
        }


    async def process(self, task: str, memory_bus=None):
        """Process task – auto-generated stub"""
        return {"content": f"Processed: {task[:50]}", "worker": self.name}
    
    async def health_check(self):
        """Return worker health status"""
        return {"worker": self.name, "status": "healthy", "timestamp": __import__('time').time()}

