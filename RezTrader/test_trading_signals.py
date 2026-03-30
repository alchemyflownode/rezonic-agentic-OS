# -*- coding: utf-8 -*-
# test_trading_signals.py
import asyncio
import sys
sys.path.insert(0, '.')

from workers.trading_engine import TradingEngineWorker
from backend.services.indicators import IndicatorService

async def test():
    print("=" * 60)
    print("TRADING ENGINE SIGNAL TEST")
    print("=" * 60)
    
    w = TradingEngineWorker()
    
    # Phase 1: Sharp downtrend
    print("\n[Phase 1] Downtrend (RSI should drop)")
    prices = []
    for i in range(40):
        price = 50000 - (i * 200)
        prices.append(price)
        signal = await w.update_price('BTCUSDT', price)
        
        if i >= 35:
            rsi = IndicatorService.calculate_rsi(prices)
            macd = IndicatorService.compute_macd(prices)
            hist = macd.get('histogram', None)
            hist_str = f"{hist:.2f}" if hist else "None"
            print(f"  Price {i}: {price:.0f} | RSI: {rsi:.1f} | MACD: {hist_str} | Signal: {signal is not None}")
        
        if signal:
            print(f"  BUY SIGNAL at {price}!")
    
    # Phase 2: Reversal
    print("\n[Phase 2] Reversal (MACD should turn positive)")
    for i in range(30):
        price = 42000 + (i * 50)
        prices.append(price)
        signal = await w.update_price('BTCUSDT', price)
        
        if i % 10 == 0:
            rsi = IndicatorService.calculate_rsi(prices)
            macd = IndicatorService.compute_macd(prices)
            hist = macd.get('histogram', None)
            hist_str = f"{hist:.2f}" if hist else "None"
            print(f"  Price {i}: {price:.0f} | RSI: {rsi:.1f} | MACD: {hist_str} | Signal: {signal is not None}")
        
        if signal:
            print(f"  BUY SIGNAL at {price}!")
    
    # Phase 3: Uptrend
    print("\n[Phase 3] Uptrend (Exit signal)")
    for i in range(40):
        price = 43500 + (i * 150)
        prices.append(price)
        signal = await w.update_price('BTCUSDT', price)
        
        if i % 10 == 0:
            rsi = IndicatorService.calculate_rsi(prices)
            print(f"  Price {i}: {price:.0f} | RSI: {rsi:.1f} | Signal: {signal is not None}")
        
        if signal:
            print(f"  EXIT SIGNAL at {price}!")
    
    # Final state
    state = await w.execute('get_state', symbol='BTCUSDT')
    print(f"\n[Final State] {state}")
    print("\n" + "=" * 60)

if __name__ == "__main__":
    asyncio.run(test())
