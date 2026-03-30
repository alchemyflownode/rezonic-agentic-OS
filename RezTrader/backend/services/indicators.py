# -*- coding: utf-8 -*-
# backend/services/indicators.py
"""
Technical indicator calculations for trading signals
RSI, MACD, and supporting functions
"""
import numpy as np
import pandas as pd
from typing import List, Dict, Optional
import logging

logger = logging.getLogger(__name__)


class IndicatorService:
    """Technical indicator calculations"""
    
    @staticmethod
    def calculate_rsi(prices: List[float], period: int = 14) -> Optional[float]:
        """
        Calculate the Relative Strength Index
        
        Args:
            prices: List of price data points
            period: RSI calculation period (default: 14)
            
        Returns:
            RSI value (0-100) or None if insufficient data
        """
        if len(prices) < period + 1:
            return None

        deltas = np.diff(prices[-period-1:])
        gain = np.mean([d for d in deltas if d > 0]) if any(d > 0 for d in deltas) else 0
        loss = abs(np.mean([d for d in deltas if d < 0])) if any(d < 0 for d in deltas) else 0

        if loss == 0:
            return 100.0

        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return round(rsi, 2)

    @staticmethod
    def compute_macd(prices: List[float], fast: int = 12, slow: int = 26, signal: int = 9) -> Dict[str, Optional[float]]:
        """
        Compute full MACD: MACD line, Signal line, Histogram
        
        Args:
            prices: List of price data points
            fast: Fast EMA period (default: 12)
            slow: Slow EMA period (default: 26)
            signal: Signal line EMA period (default: 9)
            
        Returns:
            Dict with macd, signal, histogram, and status fields
        """
        min_required = slow + signal + 5
        
        if len(prices) < min_required:
            return {
                'macd': None,
                'signal': None,
                'histogram': None,
                'status': f'insufficient_data: {len(prices)}/{min_required}'
            }
        
        try:
            series = pd.Series(prices)
            
            ema_fast = series.ewm(span=fast, adjust=False).mean()
            ema_slow = series.ewm(span=slow, adjust=False).mean()
            
            macd_line = ema_fast - ema_slow
            signal_line = macd_line.ewm(span=signal, adjust=False).mean()
            histogram = macd_line - signal_line
            
            latest_macd = macd_line.iloc[-1]
            latest_signal = signal_line.iloc[-1]
            latest_hist = histogram.iloc[-1]
            
            if pd.isna(latest_macd) or pd.isna(latest_signal) or pd.isna(latest_hist):
                return {
                    'macd': None,
                    'signal': None,
                    'histogram': None,
                    'status': 'ema_not_converged'
                }
            
            return {
                'macd': round(float(latest_macd), 4),
                'signal': round(float(latest_signal), 4),
                'histogram': round(float(latest_hist), 4),
                'status': 'ok'
            }
            
        except Exception as e:
            logger.error(f"MACD calculation error: {e}")
            return {
                'macd': None,
                'signal': None,
                'histogram': None,
                'status': f'error: {str(e)}'
            }

    # Backward compatibility alias
    calculate_macd = compute_macd