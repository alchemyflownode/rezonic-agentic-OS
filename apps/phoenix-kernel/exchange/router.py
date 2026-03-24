# exchange/router.py
"""Multi-exchange router for failover and load balancing"""

import logging
from typing import Dict, Any, Optional, List
from enum import Enum

from exchange.base import ExchangeInterface, Order
from exchange.binance_connector import BinanceConnector

logger = logging.getLogger("phoenix.exchange.router")

class ExchangeType(Enum):
    BINANCE = "binance"
    BINANCE_TESTNET = "binance_testnet"

class ExchangeRouter:
    """Routes orders to appropriate exchange with failover"""
    
    def __init__(self):
        self.exchanges: Dict[str, ExchangeInterface] = {}
        self.primary: Optional[str] = None
        self.active: Optional[str] = None
    
    def register_exchange(self, name: str, exchange: ExchangeInterface, is_primary: bool = False):
        """Register an exchange connector"""
        self.exchanges[name] = exchange
        if is_primary:
            self.primary = name
            self.active = name
    
    async def connect_all(self) -> Dict[str, bool]:
        """Connect to all registered exchanges"""
        results = {}
        for name, exchange in self.exchanges.items():
            results[name] = await exchange.connect()
            if results[name]:
                logger.info(f"✅ Connected to {name}")
            else:
                logger.warning(f"❌ Failed to connect to {name}")
        return results
    
    async def execute_order(self, order: Order, exchange_name: str = None) -> Dict[str, Any]:
        """Execute order on specified exchange (or primary)"""
        target = exchange_name or self.active
        
        if not target or target not in self.exchanges:
            return {"success": False, "error": f"Exchange {target} not available"}
        
        exchange = self.exchanges[target]
        
        try:
            result = await exchange.execute_order(order)
            return {
                "success": result.status == "EXECUTED",
                "exchange": target,
                "order": result
            }
        except Exception as e:
            logger.error(f"Order failed on {target}: {e}")
            
            # Try failover if available
            if self.primary and target != self.primary:
                logger.info(f"Failing over to primary: {self.primary}")
                return await self.execute_order(order, self.primary)
            
            return {"success": False, "error": str(e), "exchange": target}
    
    async def get_balance(self, exchange_name: str = None) -> Dict[str, float]:
        """Get balance from exchange"""
        target = exchange_name or self.active
        if target in self.exchanges:
            return await self.exchanges[target].get_balance()
        return {}
    
    async def get_price(self, symbol: str, exchange_name: str = None) -> float:
        """Get price from exchange"""
        target = exchange_name or self.active
        if target in self.exchanges:
            return await self.exchanges[target].get_price(symbol)
        return 0
    
    async def health_check_all(self) -> Dict[str, bool]:
        """Check health of all exchanges"""
        results = {}
        for name, exchange in self.exchanges.items():
            results[name] = await exchange.health_check()
        return results
    
    def set_active(self, exchange_name: str) -> bool:
        """Set active exchange"""
        if exchange_name in self.exchanges:
            self.active = exchange_name
            logger.info(f"Active exchange set to {exchange_name}")
            return True
        return False