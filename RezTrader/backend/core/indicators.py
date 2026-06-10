# utils/indicators.py
def compute_macd(self, prices, fast=12, slow=26, signal=9):
    """Compute MACD with proper minimum data handling"""
    min_required = slow + signal + 5  # Buffer for EMA warmup
    
    if len(prices) < min_required:
        # Return partial state instead of None
        return {
            'macd': None,
            'signal': None, 
            'histogram': None,
            'status': f'insufficient_data: {len(prices)}/{min_required}'
        }
    
    series = pd.Series(prices)
    ema_fast = self.calculate_ema(series, fast)
    ema_slow = self.calculate_ema(series, slow)
    
    macd_line = ema_fast - ema_slow
    signal_line = self.calculate_ema(macd_line, signal)
    histogram = macd_line - signal_line
    
    # Return latest values with safety check
    latest_idx = -1
    if pd.isna(macd_line.iloc[latest_idx]) or pd.isna(signal_line.iloc[latest_idx]):
        return {
            'macd': None,
            'signal': None,
            'histogram': None,
            'status': 'ema_not_converged'
        }
    
    return {
        'macd': float(macd_line.iloc[latest_idx]),
        'signal': float(signal_line.iloc[latest_idx]),
        'histogram': float(histogram.iloc[latest_idx]),
        'status': 'ok'
    }