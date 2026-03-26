import sys
from pathlib import Path

# Add parent directory to path
parent_dir = Path(__file__).parent.parent
if str(parent_dir) not in sys.path:
    sys.path.insert(0, str(parent_dir))
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
import ccxt.async_support as ccxt
import logging
import time

logger = logging.getLogger("REZ_HIVE_CRYPTO")

class CryptoWorker:
    """
    The Apex Brain's execution arm. 
    Connects to global liquidity nodes via CCXT for live data and paper trading.
    """
    def __init__(self):
        self.name = "CryptoWorker"
        # Initialize public exchange connections (No API keys needed for public data)
        self.binance = ccxt.binance({'enableRateLimit': True})
        self.mexc = ccxt.mexc({'enableRateLimit': True})
        
        # Sovereign Paper Trading Portfolio
        self.portfolio = {
            "USD": 10000.00,
            "BTC": 0.0,
            "PHP_RATE": 58.5 # Simulated USD to PHP conversion
        }
        logger.info("Ã°Å¸â€œË† CryptoWorker mounted. Liquidity nodes connected.")

    async def get_price(self, symbol: str = 'BTC/USDT', exchange: str = 'binance') -> dict:
        """Fetches live ticker data"""
        try:
            ex = self.binance if exchange.lower() == 'binance' else self.mexc
            ticker = await ex.fetch_ticker(symbol)
            return {
                "status": "success",
                "symbol": symbol,
                "price": ticker['last'],
                "change": ticker.get('percentage', 0),
                "volume": ticker.get('quoteVolume', 0),
                "exchange": exchange.upper()
            }
        except Exception as e:
            logger.error(f"Failed to fetch {symbol} on {exchange}: {e}")
            return {"status": "error", "message": str(e)}

    async def execute_paper_trade(self, action: str, symbol: str, amount_usd: float) -> dict:
        """Executes a simulated trade against live orderbook prices"""
        action = action.upper()
        if action not in ["BUY", "SELL"]:
            return {"status": "error", "message": "Invalid action. Use BUY or SELL."}

        # Get live price to execute against
        price_data = await self.get_price(symbol)
        if price_data["status"] == "error":
            return price_data

        live_price = price_data["price"]
        amount_coin = amount_usd / live_price

        # Basic Paper Trade Logic
        if action == "BUY":
            if self.portfolio["USD"] >= amount_usd:
                self.portfolio["USD"] -= amount_usd
                self.portfolio["BTC"] += amount_coin
                msg = f"Ã¢Å“â€¦ BOUGHT {amount_coin:.6f} {symbol.split('/')[0]} at ${live_price:,.2f}"
            else:
                return {"status": "error", "message": "Insufficient USD balance."}
        else: # SELL
            if self.portfolio["BTC"] >= amount_coin:
                self.portfolio["USD"] += amount_usd
                self.portfolio["BTC"] -= amount_coin
                msg = f"Ã¢Å“â€¦ SOLD {amount_coin:.6f} {symbol.split('/')[0]} at ${live_price:,.2f}"
            else:
                return {"status": "error", "message": "Insufficient BTC balance."}

        return {
            "status": "success",
            "message": msg,
            "portfolio_value_usd": self.portfolio["USD"] + (self.portfolio["BTC"] * live_price)
        }

    async def close_connections(self):
        """Cleanup required by CCXT async"""
        await self.binance.close()
        await self.mexc.close()

    async def process(self, task: str, memory_bus=None):
        """Process task â€“ auto-generated stub"""
        return {"content": f"Processed: {task[:50]}", "worker": self.name}
    
    async def health_check(self):
        """Return worker health status"""
        return {"worker": self.name, "status": "healthy", "timestamp": __import__('time').time()}


