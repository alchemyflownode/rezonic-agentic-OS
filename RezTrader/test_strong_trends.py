# -*- coding: utf-8 -*-
"""
Test strong trend handling: downtrend -> sideways -> uptrend
Verifies state machine prevents flip-flopping
"""
import asyncio
import sys
sys.path.insert(0, '.')

from backend.services.indicators import IndicatorService
from backend.services.signal_processor import SignalProcessor


class MockPaperTrader:
    """Mock trader for testing"""
    
    def __init__(self):
        self.balance = 10000.0
        self.positions = {}
        self.trades = []

    async def execute(self, side, symbol, amount):
        """Mock order execution"""
        if side == "buy":
            cost = amount * 50000
            if cost <= self.balance:
                self.balance -= cost
                self.positions[symbol] = self.positions.get(symbol, 0) + amount
                self.trades.append({"side": "BUY", "symbol": symbol, "amount": amount})
                print(f"  [BUY] Executed: {amount} {symbol}")
                return {"success": True}
        elif side == "sell":
            if self.positions.get(symbol, 0) >= amount:
                self.positions[symbol] -= amount
                self.trades.append({"side": "SELL", "symbol": symbol, "amount": amount})
                print(f"  [SELL] Executed: {amount} {symbol}")
                return {"success": True}
        return {"success": False, "error": "Insufficient funds/position"}


async def test_strong_trends():
    """Test state machine with strong trend phases"""
    print("=" * 70)
    print("Testing RSI with Strong Trends (Oversold -> Overbought)")
    print("=" * 70)

    mock_trader = MockPaperTrader()
    # Use cooldown=0 for testing (instant exits allowed)
    processor = SignalProcessor(mock_trader, cooldown_seconds=0)
    symbol = "BTCUSDT"

    # Phase 1: Strong downtrend (prices falling)
    print("\n[Phase 1] Strong DOWNTREND (RSI should drop below 30)")
    prices = [100 - i * 1.3 for i in range(30)]
    for price in prices:
        await processor.update_price(symbol, price)
    
    stats = processor.get_stats()
    print(f"  Final price: {prices[-1]:.2f}")
    print(f"  RSI: {IndicatorService.calculate_rsi(prices)}")
    print(f"  Signals so far: {stats['signals_generated']}")

    # Phase 2: Sideways market (should NOT flip-flop)
    print("\n[Phase 2] Sideways market (RSI should stay neutral)")
    sideways = [69 + (i % 5) - 2 for i in range(20)]
    for price in sideways:
        await processor.update_price(symbol, price)
    
    print(f"  Final price: {sideways[-1]:.2f}")
    print(f"  RSI: {IndicatorService.calculate_rsi(prices + sideways)}")

    # Phase 3: Strong uptrend (prices rising)
    print("\n[Phase 3] Strong UPTREND (RSI should rise above 70)")
    uptrend = [70 + i * 1.3 for i in range(30)]
    for price in uptrend:
        await processor.update_price(symbol, price)
    
    print(f"  Final price: {uptrend[-1]:.2f}")
    print(f"  RSI: {IndicatorService.calculate_rsi(prices + sideways + uptrend)}")

    # Final results
    print("\n" + "=" * 70)
    print("FINAL RESULTS")
    print("=" * 70)
    stats = processor.get_stats()
    print(f"  Total Signals Generated: {stats['signals_generated']}")
    print(f"  Total Trades Executed: {len(mock_trader.trades)}")
    print("\n  Trade History:")
    for t in mock_trader.trades:
        print(f"    - {t['side']} {t['amount']} {t['symbol']}")
    print(f"\n  Active States: {stats.get('active_states', {})}")
    print("=" * 70)

    # Verify expectations
    assert len(mock_trader.trades) <= 2, f"Expected <=2 trades, got {len(mock_trader.trades)}"
    print("\n[PASS] State machine prevented flip-flopping!")
    return True


if __name__ == "__main__":
    try:
        asyncio.run(test_strong_trends())
        print("\nAll tests passed!")
    except Exception as e:
        print(f"\nTest failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)