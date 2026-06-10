# workers/indicator_worker.py
import asyncio
import pandas as pd
import pandas_ta as ta
import httpx
from .base_worker import BaseWorker

class IndicatorWorker(BaseWorker):
    name = "indicator_worker"
    description = "Fetches market data and computes technical indicators"

    async def execute(self, world, **kwargs):
        symbol = kwargs.get("symbol", "BTCUSDT")
        interval = kwargs.get("interval", "1h")
        limit = kwargs.get("limit", 100)

        # 1. Fetch OHLCV from Binance public API
        url = f"https://api.binance.com/api/v3/klines?symbol={symbol}&interval={interval}&limit={limit}"
        async with httpx.AsyncClient() as client:
            resp = await client.get(url)
            data = resp.json()

        # 2. Build DataFrame
        df = pd.DataFrame(data, columns=[
            "timestamp", "open", "high", "low", "close", "volume",
            "close_time", "quote_asset_volume", "number_of_trades",
            "taker_buy_base_asset_volume", "taker_buy_quote_asset_volume", "ignore"
        ])
        df["close"] = df["close"].astype(float)
        df["volume"] = df["volume"].astype(float)

        # 3. Compute indicators using pandas_ta
        df["rsi"] = ta.rsi(df["close"], length=14)
        df["macd"] = ta.macd(df["close"])["MACD_12_26_9"]
        df["signal"] = ta.macd(df["close"])["MACDs_12_26_9"]
        df["ma_20"] = ta.sma(df["close"], length=20)
        df["ma_50"] = ta.sma(df["close"], length=50)
        df["volume_sma"] = ta.sma(df["volume"], length=20)

        # 4. Store latest values in World Model (for other workers / LLM)
        latest = df.iloc[-1]
        world.observe(f"{symbol}_price", latest["close"], self.name)
        world.observe(f"{symbol}_rsi", latest["rsi"], self.name)
        world.observe(f"{symbol}_macd", latest["macd"], self.name)
        world.observe(f"{symbol}_ma_20", latest["ma_20"], self.name)
        world.observe(f"{symbol}_ma_50", latest["ma_50"], self.name)
        world.observe(f"{symbol}_volume_sma", latest["volume_sma"], self.name)

        # Also store full DataFrame reference (optional, for deep analysis)
        world.observe(f"{symbol}_df", df.to_json(), self.name)

        return {"success": True, "latest": {k: v for k, v in latest.items() if not pd.isna(v)}}