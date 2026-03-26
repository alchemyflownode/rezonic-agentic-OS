# workers/exchange_worker.py
"""Exchange worker for trading operations"""

import logging
from typing import Dict, Any

from workers.base_worker import BaseWorker
from workers.decorators import handle_errors, with_timeout, log_execution
from exchange.router import ExchangeRouter, ExchangeType
from exchange.binance_connector import BinanceConnector
from exchange.constitutional_trader import ConstitutionalTrader

logger = logging.getLogger("phoenix.workers.exchange")

class ExchangeWorker(BaseWorker):
    """Worker for exchange operations with constitutional enforcement"""
    
    def __init__(self, constitution=None):
        super().__init__("exchange_worker")
        self.router = ExchangeRouter()
        self.constitutional_trader = None
        self.constitution = constitution
        self._initialized = False
    
    @handle_errors("exchange_worker", retry_count=3)
    @with_timeout(30.0)
    @log_execution("exchange_worker")
    async def execute(self, task: str, **kwargs) -> Dict[str, Any]:
        """Execute exchange task"""
        
        if not self._initialized:
            await self._initialize()
        
        task_lower = task.lower()
        
        if task_lower == "connect":
            return await self._connect()
        
        elif task_lower == "trade":
            return await self._trade(kwargs)
        
        elif task_lower == "balance":
            return await self._get_balance(kwargs.get("asset"))
        
        elif task_lower == "price":
            return await self._get_price(kwargs.get("symbol", "BTCUSDT"))
        
        elif task_lower == "health":
            return await self._health()
        
        elif task_lower == "set_active":
            return self._set_active(kwargs.get("exchange"))
        
        else:
            return {"error": f"Unknown task: {task}", "success": False}
    
    async def _initialize(self):
        """Initialize exchange connections"""
        
        # Create connectors
        binance_testnet = BinanceConnector(testnet=True)
        
        # Register with router
        self.router.register_exchange("binance_testnet", binance_testnet, is_primary=True)
        
        # Create constitutional trader
        self.constitutional_trader = ConstitutionalTrader(
            binance_testnet,
            self.constitution
        )
        
        self._initialized = True
        logger.info("Exchange worker initialized with Binance testnet")
    
    async def _connect(self) -> Dict[str, Any]:
        """Connect to all exchanges"""
        results = await self.router.connect_all()
        
        if any(results.values()):
            return {
                "success": True,
                "connected": results,
                "active": self.router.active
            }
        return {
            "success": False,
            "error": "No exchanges connected",
            "results": results
        }
    
    async def _trade(self, params: Dict) -> Dict[str, Any]:
        """Execute a trade"""
        from exchange.base import Order
        
        # Validate parameters
        symbol = params.get("symbol", "BTCUSDT")
        side = params.get("side", "BUY")
        quantity = params.get("quantity", 0)
        order_type = params.get("type", "MARKET")
        price = params.get("price")
        
        if quantity <= 0:
            return {"error": "Invalid quantity", "success": False}
        
        # Create order
        order = Order(
            symbol=symbol,
            side=side,
            order_type=order_type,
            quantity=quantity,
            price=price
        )
        
        # Get portfolio value (simplified)
        portfolio_value = params.get("portfolio_value", 10000)
        daily_pnl = params.get("daily_pnl", 0)
        
        # Execute with constitutional enforcement
        result = await self.constitutional_trader.execute_trade(
            order,
            portfolio_value,
            daily_pnl
        )
        
        return result
    
    async def _get_balance(self, asset: str = None) -> Dict[str, Any]:
        """Get account balance"""
        balance = await self.router.get_balance()
        
        if asset:
            return {
                "success": True,
                "asset": asset,
                "balance": balance.get(asset, 0)
            }
        
        return {
            "success": True,
            "balance": balance
        }
    
    async def _get_price(self, symbol: str) -> Dict[str, Any]:
        """Get current price"""
        price = await self.router.get_price(symbol)
        
        return {
            "success": True,
            "symbol": symbol,
            "price": price,
            "timestamp": __import__('time').time()
        }
    
    async def _health(self) -> Dict[str, Any]:
        """Check exchange health"""
        health = await self.router.health_check_all()
        
        return {
            "success": True,
            "health": health,
            "active": self.router.active
        }
    
    def _set_active(self, exchange: str) -> Dict[str, Any]:
        """Set active exchange"""
        if self.router.set_active(exchange):
            return {"success": True, "active": exchange}
        return {"success": False, "error": f"Exchange {exchange} not found"}
    
    async def health_check(self) -> Dict[str, Any]:
        """Worker health check"""
        return {
            "worker": self.name,
            "status": "healthy" if self._initialized else "initializing",
            "active_exchange": self.router.active,
            "exchanges": list(self.router.exchanges.keys())
        }