# run_visualizer.py
"""Launch RezTrader with full visualization"""

import asyncio
from workers.trade_visualizer import TradeVisualizerWorker

async def main():
    # Initialize visualizer
    visualizer = TradeVisualizerWorker()
    
    # Start WebSocket streaming
    asyncio.create_task(visualizer.start_streaming())
    
    # Simulate AI trading decisions
    workers = ["MomentumWorker", "ReversionWorker", "ScalpingWorker"]
    
    while True:
        for worker in workers:
            # Simulate market data
            signal = {
                "action": "buy" if np.random.random() > 0.5 else "sell",
                "symbol": "BTC/PHP",
                "price": 4_500_000 + np.random.randint(-10000, 10000),
                "quantity": 0.01 + np.random.random() * 0.05,
                "confidence": 0.5 + np.random.random() * 0.4,
                "rsi": 40 + np.random.randint(0, 60),
                "volume": 1_000_000 + np.random.randint(-500_000, 500_000),
                "trend": "bullish" if np.random.random() > 0.5 else "bearish"
            }
            
            # Process decision (will broadcast via WebSocket)
            decision = await visualizer.process_ai_decision(worker, signal)
            
            # Wait between trades
            await asyncio.sleep(np.random.uniform(0.5, 3))
        
        await asyncio.sleep(1)

if __name__ == "__main__":
    asyncio.run(main())