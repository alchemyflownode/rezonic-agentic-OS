# main.py
import asyncio
import os
from dotenv import load_dotenv
from core.event_bus import EventBus
from core.exchange import ExchangeConnector
from strategies.rsi_macd_confluence import RSIMACDStrategy

load_dotenv()

async def main():
    # 1. Initialize Core
    bus = EventBus()
    connector = ExchangeConnector(
        api_key=os.getenv("API_KEY"),
        secret=os.getenv("API_SECRET"),
        sandbox=True
    )
    
    # 2. Initialize Strategy
    symbol = "BTC/USDT"
    strategy = RSIMACDStrategy(symbol, bus, connector)
    
    # 3. Wire Events
    bus.subscribe("ticker", strategy.on_market_data)
    
    print(f"🚀 Starting Sovereign Kernel for {symbol}...")
    
    try:
        # 4. Start Data Feed
        await connector.watch_ticker(symbol, lambda data: asyncio.create_task(bus.emit("ticker", data)))
    except KeyboardInterrupt:
        print("🛑 Shutting down...")
    finally:
        await connector.close()

if __name__ == "__main__":
    asyncio.run(main())