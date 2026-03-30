def compute_macd(self, prices, fast=12, slow=26, signal=9):
    """Compute MACD with proper minimum data handling"""
    import pandas as pd
    import numpy as np
    
    min_required = slow + signal + 5  # Buffer for EMA warmup
    
    if len(prices) < min_required:
        return {
            'macd': None,
            'signal': None, 
            'histogram': None,
            'status': f'insufficient_data: {len(prices)}/{min_required}'
        }
    
    series = pd.Series(prices)
    ema_fast = series.ewm(span=fast, adjust=False).mean()
    ema_slow = series.ewm(span=slow, adjust=False).mean()
    
    macd_line = ema_fast - ema_slow
    signal_line = macd_line.ewm(span=signal, adjust=False).mean()
    histogram = macd_line - signal_line
    
    latest_idx = -1
    if pd.isna(macd_line.iloc[latest_idx]) or pd.isna(signal_line.iloc[latest_idx]):
        return {'macd': None, 'signal': None, 'histogram': None, 'status': 'ema_not_converged'}
    
    return {
        'macd': float(macd_line.iloc[latest_idx]),
        'signal': float(signal_line.iloc[latest_idx]),
        'histogram': float(histogram.iloc[latest_idx]),
        'status': 'ok'
    }