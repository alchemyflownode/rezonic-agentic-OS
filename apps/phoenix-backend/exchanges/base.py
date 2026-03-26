import ccxt.async_support as ccxt
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

class BaseExchange:
    def __init__(self, config: Dict[str, Any]):
        self.name = config.get('name')
        self.testnet = config.get('testnet', True)
        self.api_key = config.get('api_key', '')
        self.secret = config.get('secret', '')
        self.exchange = None
        
    async def connect(self):
        try:
            exchange_class = getattr(ccxt, self.name)
            self.exchange = exchange_class({
                'apiKey': self.api_key,
                'secret': self.secret,
                'enableRateLimit': True,
                'options': {'defaultType': 'spot'}
            })
            if self.testnet:
                self.exchange.set_sandbox_mode(True)
            logger.info(f"✅ Connected to {self.name.upper()} {'testnet' if self.testnet else 'live'}")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to connect to {self.name}: {e}")
            return False

    async def get_ticker(self, symbol: str):
        if not self.exchange: return None
        ticker = await self.exchange.fetch_ticker(symbol)
        return {'symbol': symbol, 'bid': ticker['bid'], 'ask': ticker['ask'], 'last': ticker['last'], 'exchange': self.name}
