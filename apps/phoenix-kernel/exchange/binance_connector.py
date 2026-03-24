# exchange/binance_connector.py
"""Binance exchange connector with real-time market data"""

import asyncio
import hmac
import hashlib
import time
import json
import logging
from typing import Dict, Any, Optional, List, Callable
from datetime import datetime
from decimal import Decimal
import aiohttp
import websockets

from exchange.base import ExchangeInterface, Order, MarketData

logger = logging.getLogger("phoenix.exchange.binance")

class BinanceConnector(ExchangeInterface):
    """Binance exchange connector"""
    
    def __init__(self, api_key: str = None, api_secret: str = None, testnet: bool = True):
        self.api_key = api_key
        self.api_secret = api_secret
        self.testnet = testnet
        
        # Set URLs based on testnet/live
        if testnet:
            self.rest_url = "https://testnet.binance.vision/api/v3"
            self.ws_url = "wss://testnet.binance.vision/ws"
        else:
            self.rest_url = "https://api.binance.com/api/v3"
            self.ws_url = "wss://stream.binance.com:9443/ws"
        
        self.session: Optional[aiohttp.ClientSession] = None
        self.ws_connections: Dict[str, websockets.WebSocketClientProtocol] = {}
        self._connected = False
        self._rate_limiter = None  # Will be injected
        self._key_manager = None  # Will be injected
    
    async def connect(self) -> bool:
        """Connect to Binance"""
        try:
            self.session = aiohttp.ClientSession()
            # Test connection
            async with self.session.get(f"{self.rest_url}/ping") as resp:
                if resp.status == 200:
                    self._connected = True
                    logger.info(f"✅ Binance {'testnet' if self.testnet else 'live'} connected")
                    return True
            return False
        except Exception as e:
            logger.error(f"Binance connection failed: {e}")
            return False
    
    async def disconnect(self) -> bool:
        """Disconnect from Binance"""
        try:
            # Close WebSocket connections
            for ws in self.ws_connections.values():
                await ws.close()
            self.ws_connections.clear()
            
            # Close HTTP session
            if self.session:
                await self.session.close()
            
            self._connected = False
            logger.info("Binance disconnected")
            return True
        except Exception as e:
            logger.error(f"Disconnect error: {e}")
            return False
    
    async def get_balance(self, asset: Optional[str] = None) -> Dict[str, float]:
        """Get account balance"""
        if not self._connected:
            raise ConnectionError("Not connected to Binance")
        
        try:
            # Create signature
            timestamp = int(time.time() * 1000)
            params = f"timestamp={timestamp}"
            signature = hmac.new(
                self.api_secret.encode('utf-8'),
                params.encode('utf-8'),
                hashlib.sha256
            ).hexdigest()
            
            headers = {"X-MBX-APIKEY": self.api_key}
            url = f"{self.rest_url}/account?{params}&signature={signature}"
            
            async with self.session.get(url, headers=headers) as resp:
                data = await resp.json()
                if resp.status != 200:
                    logger.error(f"Balance error: {data}")
                    return {}
                
                balances = {}
                for balance in data.get("balances", []):
                    free = float(balance.get("free", 0))
                    locked = float(balance.get("locked", 0))
                    if free > 0 or locked > 0:
                        balances[balance["asset"]] = free + locked
                
                if asset:
                    return {asset: balances.get(asset, 0)}
                return balances
                
        except Exception as e:
            logger.error(f"Failed to get balance: {e}")
            return {}
    
    async def get_price(self, symbol: str) -> float:
        """Get current price for symbol"""
        try:
            url = f"{self.rest_url}/ticker/price"
            params = {"symbol": symbol.upper()}
            
            async with self.session.get(url, params=params) as resp:
                data = await resp.json()
                return float(data.get("price", 0))
        except Exception as e:
            logger.error(f"Failed to get price for {symbol}: {e}")
            return 0
    
    async def get_klines(self, symbol: str, interval: str = "1m", limit: int = 100) -> List[Dict]:
        """Get candlestick data"""
        try:
            url = f"{self.rest_url}/klines"
            params = {
                "symbol": symbol.upper(),
                "interval": interval,
                "limit": limit
            }
            
            async with self.session.get(url, params=params) as resp:
                data = await resp.json()
                
                candles = []
                for k in data:
                    candles.append({
                        "timestamp": k[0],
                        "open": float(k[1]),
                        "high": float(k[2]),
                        "low": float(k[3]),
                        "close": float(k[4]),
                        "volume": float(k[5])
                    })
                return candles
        except Exception as e:
            logger.error(f"Failed to get klines: {e}")
            return []
    
    async def execute_order(self, order: Order) -> Order:
        """Execute an order on Binance"""
        if not self._connected:
            raise ConnectionError("Not connected to Binance")
        
        try:
            # Prepare order parameters
            timestamp = int(time.time() * 1000)
            params = {
                "symbol": order.symbol.upper(),
                "side": order.side.upper(),
                "type": order.order_type.upper(),
                "quantity": order.quantity,
                "timestamp": timestamp
            }
            
            if order.order_type.upper() == "LIMIT":
                params["price"] = order.price
                params["timeInForce"] = "GTC"
            
            # Create query string for signature
            query_string = "&".join([f"{k}={v}" for k, v in params.items()])
            signature = hmac.new(
                self.api_secret.encode('utf-8'),
                query_string.encode('utf-8'),
                hashlib.sha256
            ).hexdigest()
            
            # Add signature to params
            params["signature"] = signature
            
            headers = {"X-MBX-APIKEY": self.api_key}
            url = f"{self.rest_url}/order"
            
            async with self.session.post(url, headers=headers, params=params) as resp:
                data = await resp.json()
                
                if resp.status == 200:
                    order.order_id = data.get("orderId")
                    order.status = data.get("status", "EXECUTED")
                    order.timestamp = datetime.now()
                    
                    # Calculate drift lock
                    import hashlib
                    order.drift_lock = hashlib.sha256(
                        f"{order.order_id}{order.symbol}{order.quantity}{order.timestamp}".encode()
                    ).hexdigest()[:16]
                    
                    logger.info(f"✅ Order executed: {order.side} {order.quantity} {order.symbol}")
                    return order
                else:
                    logger.error(f"Order failed: {data}")
                    order.status = "FAILED"
                    return order
                    
        except Exception as e:
            logger.error(f"Order execution error: {e}")
            order.status = "ERROR"
            return order
    
    async def get_order_status(self, order_id: str) -> Dict[str, Any]:
        """Get status of an order"""
        try:
            timestamp = int(time.time() * 1000)
            params = {
                "orderId": order_id,
                "timestamp": timestamp
            }
            
            query_string = "&".join([f"{k}={v}" for k, v in params.items()])
            signature = hmac.new(
                self.api_secret.encode('utf-8'),
                query_string.encode('utf-8'),
                hashlib.sha256
            ).hexdigest()
            
            params["signature"] = signature
            headers = {"X-MBX-APIKEY": self.api_key}
            url = f"{self.rest_url}/order"
            
            async with self.session.get(url, headers=headers, params=params) as resp:
                data = await resp.json()
                return data
                
        except Exception as e:
            logger.error(f"Failed to get order status: {e}")
            return {}
    
    async def stream_prices(self, symbols: List[str], callback: Callable) -> None:
        """Stream real-time prices via WebSocket"""
        try:
            # Format symbols for Binance stream
            streams = [f"{s.lower()}@ticker" for s in symbols]
            stream_url = f"{self.ws_url}/stream?streams={'/'.join(streams)}"
            
            async with websockets.connect(stream_url) as websocket:
                for symbol in symbols:
                    self.ws_connections[symbol] = websocket
                
                while True:
                    try:
                        message = await websocket.recv()
                        data = json.loads(message)
                        
                        # Parse stream data
                        if "data" in data:
                            ticker = data["data"]
                            market_data = MarketData(
                                symbol=ticker.get("s", ""),
                                price=float(ticker.get("c", 0)),
                                volume=float(ticker.get("v", 0)),
                                bid=float(ticker.get("b", 0)),
                                ask=float(ticker.get("a", 0)),
                                timestamp=datetime.now()
                            )
                            await callback(market_data)
                            
                    except websockets.exceptions.ConnectionClosed:
                        logger.warning("WebSocket connection closed, reconnecting...")
                        break
                    except Exception as e:
                        logger.error(f"WebSocket error: {e}")
                        await asyncio.sleep(1)
                        
        except Exception as e:
            logger.error(f"Failed to stream prices: {e}")
    
    async def health_check(self) -> bool:
        """Check if exchange connection is healthy"""
        try:
            async with self.session.get(f"{self.rest_url}/ping") as resp:
                return resp.status == 200
        except:
            return False
    
    def set_rate_limiter(self, rate_limiter):
        """Inject rate limiter"""
        self._rate_limiter = rate_limiter
    
    def set_key_manager(self, key_manager):
        """Inject key manager"""
        self._key_manager = key_manager
        if key_manager:
            # Load keys from key manager
            keys = key_manager.decrypt_api_key("binance")
            if keys.get("success"):
                self.api_key = keys["api_key"]
                self.api_secret = keys["api_secret"]