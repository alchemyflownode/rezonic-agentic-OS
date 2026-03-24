# exchange/base.py
"""Base exchange interface for all exchange connectors"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from datetime import datetime
import logging

logger = logging.getLogger("phoenix.exchange")

@dataclass
class Order:
    """Order structure"""
    symbol: str
    side: str  # BUY or SELL
    order_type: str  # MARKET or LIMIT
    quantity: float
    price: Optional[float] = None
    order_id: Optional[str] = None
    status: str = "PENDING"
    timestamp: Optional[datetime] = None
    drift_lock: Optional[str] = None

@dataclass
class MarketData:
    """Market data structure"""
    symbol: str
    price: float
    volume: float
    bid: Optional[float] = None
    ask: Optional[float] = None
    timestamp: datetime = None

class ExchangeInterface(ABC):
    """Base interface for exchange integration"""
    
    @abstractmethod
    async def connect(self) -> bool:
        """Connect to exchange"""
        pass
    
    @abstractmethod
    async def disconnect(self) -> bool:
        """Disconnect from exchange"""
        pass
    
    @abstractmethod
    async def get_balance(self, asset: Optional[str] = None) -> Dict[str, float]:
        """Get account balance"""
        pass
    
    @abstractmethod
    async def get_price(self, symbol: str) -> float:
        """Get current price for symbol"""
        pass
    
    @abstractmethod
    async def execute_order(self, order: Order) -> Order:
        """Execute an order on the exchange"""
        pass
    
    @abstractmethod
    async def get_order_status(self, order_id: str) -> Dict[str, Any]:
        """Get status of an order"""
        pass
    
    @abstractmethod
    async def stream_prices(self, symbols: List[str], callback) -> None:
        """Stream real-time prices via WebSocket"""
        pass
    
    @abstractmethod
    async def health_check(self) -> bool:
        """Check if exchange connection is healthy"""
        pass