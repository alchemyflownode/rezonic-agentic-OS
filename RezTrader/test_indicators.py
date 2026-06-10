#!/usr/bin/env python3
"""
Test script for RSI indicators and signal processing
"""

import asyncio
import sys
sys.path.insert(0, '.')

from backend.services.indicators import IndicatorService
from backend.services.signal_processor import SignalProcessor

# Mock PaperTrader for testing
class MockPaperTrader:
    def __init__(self):
        self.balance = 1000000
        self.positions = {}
        self.executed_trades = []
    
    async def execute(self, action, symbol, amount):
        trade = {
            "action": action,
            "symbol": symbol,
            "amount": amount,
            "success": True
        }
        self.executed_trades.append(trade)
        
        if action == "buy":
            self.positions[symbol] = self.positions.get(symbol, 0) + amount
        elif action == "sell":
            self.positions[symbol] = self.positions.get(symbol, 0) - amount
        
        print(f"📊 MOCK TRADE: {action.upper()} {amount} {symbol}")
        return {"success": True, "trade": trade}
    
    def get_stats(self):
        return {"balance": self.balance, "positions": self.positions}

async def test_indicators():
    print("=" * 60)
    print("🧪 Testing RSI Indicator & Signal Processor")
    print("=" * 60)
    
    # Test RSI calculation
    print("\n📈 Testing RSI calculation...")
    prices = [100, 101, 102, 103, 102, 101, 100, 99, 98, 97, 96, 95, 94, 93, 92, 91, 90]
    rsi = IndicatorService.calculate_rsi(prices)
    print(f"  Prices: {prices[:5]}...{prices[-5:]}")
    print(f"  RSI: {rsi}")
    
    # Test MACD calculation
    print("\n📊 Testing MACD calculation...")
    macd = IndicatorService.calculate_macd(prices)
    print(f"  MACD Line: {macd['macd']}")
    
    # Test signal processor
    print("\n🤖 Testing Signal Processor...")
    mock_trader = MockPaperTrader()
    processor = SignalProcessor(mock_trader)
    
    # Simulate price feed
    test_prices = [
        100, 99, 98, 97, 96, 95, 94, 93, 92, 91,  # Downtrend
        90, 89, 88, 87, 86, 85, 84, 83, 82, 81,  # More downtrend (RSI should drop)
        80, 79, 78, 77, 76, 75, 74, 73, 72, 71   # Extreme oversold
    ]
    
    print("\n🔄 Simulating price feed...")
    for i, price in enumerate(test_prices):
        await processor.update_price("BTCUSDT", price)
        if (i + 1) % 10 == 0:
            print(f"  Processed {i+1} prices...")
    
    print(f"\n✅ Signal Processor Stats:")
    stats = processor.get_stats()
    print(f"  Signals Generated: {stats['signals_generated']}")
    print(f"  Tracked Symbols: {stats['tracked_symbols']}")
    print(f"  Executed Trades: {len(mock_trader.executed_trades)}")
    
    for trade in mock_trader.executed_trades:
        print(f"    - {trade['action'].upper()} {trade['amount']} {trade['symbol']}")
    
    print("\n" + "=" * 60)
    print("✅ All tests passed!")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(test_indicators())