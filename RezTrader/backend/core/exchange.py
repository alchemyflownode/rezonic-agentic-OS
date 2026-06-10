# core/exchange.py
import ccxt.pro as ccxtpro
import asyncio
import logging
from .circuit_breaker import CircuitBreaker

logger = logging.getLogger(__name__)

class ExchangeConnector:
    def __init__(self, api_key, secret, sandbox=True):
        # Use testnet URLs for sandbox mode
        config = {
            'apiKey': api_key,
            'secret': secret,
            'enableRateLimit': True,
            'options': {'defaultType': 'future'}
        }
        
        if sandbox:
            config['urls'] = {
                'api': {
                    'public': 'https://testnet.binancefuture.com',
                    'private': 'https://testnet.binancefuture.com',
                }
            }
        
        self.exchange = ccxtpro.binance(config)
        self.circuit_breaker = CircuitBreaker(max_failures=5)
        self.is_alive = True
        self._order_cache = {}  # Track pending orders

    async def watch_ticker(self, symbol: str, callback):
        """Watch ticker with circuit breaker protection"""
        while self.is_alive:
            try:
                if self.circuit_breaker.should_stop():
                    logger.warning("Circuit breaker OPEN - stopping data feed")
                    await asyncio.sleep(self.circuit_breaker.cooldown)
                    continue

                ticker = await self.exchange.watch_ticker(symbol)
                self.circuit_breaker.reset()
                await callback(ticker)

            except ccxtpro.NetworkError as e:
                self.circuit_breaker.record_failure()
                logger.error(f"Network error: {e}")
                await asyncio.sleep(5)
            except ccxtpro.ExchangeError as e:
                self.circuit_breaker.record_failure()
                logger.error(f"Exchange error: {e}")
                await asyncio.sleep(5)
            except Exception as e:
                self.circuit_breaker.record_failure()
                logger.error(f"Unexpected error: {e}")
                await asyncio.sleep(5)

    async def execute_order(self, symbol, side, amount, params=None):
        """Execute order with reconciliation"""
        if self.circuit_breaker.should_stop():
            logger.error("Circuit breaker OPEN - order rejected")
            return None

        try:
            order = await self.exchange.create_market_order(symbol, side, amount, params or {})
            
            # Cache for reconciliation
            self._order_cache[order['id']] = {
                'symbol': symbol,
                'side': side,
                'amount': amount,
                'status': order.get('status', 'open'),
                'timestamp': asyncio.get_event_loop().time()
            }
            
            logger.info(f"Order placed: {side} {amount} {symbol} @ {order.get('price', 'MARKET')}")
            return order

        except Exception as e:
            self.circuit_breaker.record_failure()
            logger.error(f"Order execution failed: {e}")
            return None

    async def reconcile_order(self, order_id):
        """Verify order state with exchange"""
        try:
            order = await self.exchange.fetch_order(order_id)
            cached = self._order_cache.get(order_id)
            
            if cached and cached['status'] != order['status']:
                logger.warning(f"Order state mismatch: {cached['status']} → {order['status']}")
                cached['status'] = order['status']
            
            return order
        except Exception as e:
            logger.error(f"Reconciliation failed: {e}")
            return None

    async def close(self):
        """Graceful shutdown"""
        self.is_alive = False
        await self.exchange.close()
        logger.info("Exchange connector closed")