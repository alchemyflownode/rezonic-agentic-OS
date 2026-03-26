import ccxt.async_support as ccxt
import logging
import time

logger = logging.getLogger("REZ_HIVE_CRYPTO")

class CryptoWorker:
    """
    The Apex Brain's execution arm. 
    Connects to global liquidity nodes via CCXT for live data and paper trading.
    """
    def __init__(self, hive_bus=None):
        self.hive_bus = hive_bus`n        self.name = "CryptoWorker"
        # Initialize public exchange connections (No API keys needed for public data)
        self.binance = ccxt.binance({'enableRateLimit': True})
        self.mexc = ccxt.mexc({'enableRateLimit': True})
        
        # Sovereign Paper Trading Portfolio
        self.portfolio = {
            "USD": 10000.00,
            "BTC": 0.0,
            "ETH": 0.0,
            "PHP_RATE": 58.5  # Simulated USD to PHP conversion
        }
        logger.info("📈 CryptoWorker mounted. Liquidity nodes connected.")

    async def process(self, task: str) -> dict:
        """Process crypto commands"""
        try:
            task = task.strip()
            
            # Parse command
            if task.startswith('/price'):
                # Format: /price BTC/USDT
                parts = task.split()
                symbol = parts[1] if len(parts) > 1 else 'BTC/USDT'
                price_data = await self.get_price(symbol)
                
                if price_data["status"] == "success":
                    return {
                        "content": f"💰 **{symbol}**\n"
                                   f"Price: ${price_data['price']:,.2f}\n"
                                   f"24h Change: {price_data['change_24h']:+.2f}%\n"
                                   f"Volume: ${price_data['volume']:,.0f}\n"
                                   f"Exchange: {price_data['exchange']}"
                    }
                else:
                    return {"content": f"❌ Failed to fetch {symbol}: {price_data.get('message', 'Unknown error')}"}
                
            elif task.startswith('/trade') or task.startswith('/paper'):
                # Format: /trade BTC/USDT 0.01 buy
                parts = task.split()
                if len(parts) >= 4:
                    symbol = parts[1]
                    try:
                        amount = float(parts[2])
                    except ValueError:
                        return {"content": "❌ Invalid amount. Please use a number."}
                    
                    side = parts[3].upper()
                    
                    if side not in ["BUY", "SELL"]:
                        return {"content": "❌ Side must be BUY or SELL"}
                    
                    result = await self.execute_paper_trade(side, symbol, amount)
                    
                    if result["status"] == "success":
                        return {"content": result["message"]}
                    else:
                        return {"content": f"❌ {result['message']}"}
                else:
                    return {"content": "Usage: /trade <symbol> <amount> <BUY/SELL>\nExample: /trade BTC/USDT 100 BUY"}
            
            elif task.startswith('/portfolio'):
                # Get current prices
                btc_price_data = await self.get_price('BTC/USDT')
                eth_price_data = await self.get_price('ETH/USDT')
                
                btc_price = btc_price_data['price'] if btc_price_data['status'] == 'success' else 0
                eth_price = eth_price_data['price'] if eth_price_data['status'] == 'success' else 0
                
                btc_value = self.portfolio["BTC"] * btc_price
                eth_value = self.portfolio["ETH"] * eth_price
                total_value = self.portfolio["USD"] + btc_value + eth_value
                
                return {
                    "content": f"""📊 **PORTFOLIO**
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
USD Balance: ${self.portfolio['USD']:,.2f}

BTC Holdings: {self.portfolio['BTC']:.6f} BTC
BTC Value: ${btc_value:,.2f} @ ${btc_price:,.2f}

ETH Holdings: {self.portfolio['ETH']:.6f} ETH
ETH Value: ${eth_value:,.2f} @ ${eth_price:,.2f}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Total Value: ${total_value:,.2f}
PHP (est): ₱{total_value * self.portfolio['PHP_RATE']:,.2f}"""
                }
                
            elif task.startswith('/help') or task == '':
                return {"content": self._get_help()}
                
            else:
                # Try to extract a symbol from natural language
                for sym in ['BTC', 'ETH', 'SOL', 'XRP', 'ADA', 'DOT']:
                    if sym in task.upper():
                        price_data = await self.get_price(f"{sym}/USDT")
                        if price_data['status'] == 'success':
                            return {
                                "content": f"💰 **{sym}/USDT**: ${price_data['price']:,.2f}\n"
                                           f"24h: {price_data['change_24h']:+.2f}%"
                            }
                
                return {"content": self._get_help()}
                
        except Exception as e:
            logger.error(f"Crypto process error: {e}")
            return {"content": f"❌ Crypto error: {str(e)}"}

    def _get_help(self):
        """Get help text"""
        return """
💰 **CRYPTO WORKER COMMANDS**
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
/price <symbol>       - Get current price
  ex: /price BTC/USDT

/trade <symbol> <amt> <side> - Paper trade
  ex: /trade BTC/USDT 100 BUY

/portfolio            - View paper trading portfolio
/help                 - Show this help
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

💡 You can also just type a symbol like "BTC price"
"""

    async def get_price(self, symbol: str = 'BTC/USDT', exchange: str = 'binance') -> dict:
        """Fetches live ticker data - FIXED VERSION"""
        try:
            ex = self.binance if exchange.lower() == 'binance' else self.mexc
            
            # For Binance, we need to use the correct symbol format
            if exchange.lower() == 'binance':
                # Convert from BTC/USDT to BTCUSDT format
                symbol_fixed = symbol.replace('/', '').upper()
            else:
                symbol_fixed = symbol
                
            # Fetch ticker (this uses the correct endpoint automatically)
            ticker = await ex.fetch_ticker(symbol_fixed)
            
            # Calculate 24h change if available
            change_24h = 0.0
            if ticker.get('percentage') is not None:
                change_24h = ticker['percentage']
            elif ticker.get('high') and ticker.get('low') and ticker.get('last'):
                # Approximate from high/low
                if ticker['low'] > 0:
                    change_24h = ((ticker['last'] - ticker['low']) / ticker['low']) * 100
                    
            return {
                "status": "success",
                "symbol": symbol,
                "price": ticker['last'],
                "change_24h": round(change_24h, 2),
                "volume": ticker.get('quoteVolume', 0) or ticker.get('volume', 0),
                "exchange": exchange.upper()
            }
            
        except Exception as e:
            logger.error(f"Failed to fetch {symbol} on {exchange}: {e}")
            
            # Try alternate symbol format
            try:
                if exchange.lower() == 'binance' and '/' in symbol:
                    # Try with underscore format
                    alt_symbol = symbol.replace('/', '_').upper()
                    ticker = await ex.fetch_ticker(alt_symbol)
                    
                    change_24h = ticker.get('percentage', 0)
                    
                    return {
                        "status": "success",
                        "symbol": symbol,
                        "price": ticker['last'],
                        "change_24h": round(change_24h, 2),
                        "volume": ticker.get('quoteVolume', 0) or ticker.get('volume', 0),
                        "exchange": exchange.upper()
                    }
            except Exception as e2:
                logger.error(f"Alternate format also failed: {e2}")
                pass
            
            return {
                "status": "error", 
                "message": str(e), 
                "price": 0, 
                "change_24h": 0,
                "volume": 0,
                "exchange": exchange.upper()
            }

    async def execute_paper_trade(self, action: str, symbol: str, amount_usd: float) -> dict:
        """Executes a simulated trade against live orderbook prices"""
        action = action.upper()
        if action not in ["BUY", "SELL"]:
            return {"status": "error", "message": "Invalid action. Use BUY or SELL."}

        # Get live price to execute against
        price_data = await self.get_price(symbol)
        if price_data["status"] == "error":
            return {"status": "error", "message": f"Could not get price for {symbol}"}

        live_price = price_data["price"]
        base_currency = symbol.split('/')[0]  # BTC from BTC/USDT
        
        # Handle different base currencies
        if base_currency not in self.portfolio:
            self.portfolio[base_currency] = 0.0
            
        amount_coin = amount_usd / live_price

        # Paper Trade Logic
        if action == "BUY":
            if self.portfolio["USD"] >= amount_usd:
                self.portfolio["USD"] -= amount_usd
                self.portfolio[base_currency] += amount_coin
                msg = f"✅ BOUGHT {amount_coin:.6f} {base_currency} at ${live_price:,.2f}"
            else:
                return {
                    "status": "error", 
                    "message": f"Insufficient USD balance. You have ${self.portfolio['USD']:,.2f}"
                }
        else:  # SELL
            if self.portfolio.get(base_currency, 0) >= amount_coin:
                self.portfolio["USD"] += amount_usd
                self.portfolio[base_currency] -= amount_coin
                msg = f"✅ SOLD {amount_coin:.6f} {base_currency} at ${live_price:,.2f}"
            else:
                return {
                    "status": "error", 
                    "message": f"Insufficient {base_currency} balance. You have {self.portfolio.get(base_currency, 0):.6f}"
                }

        # Calculate total value
        total_value = self.portfolio["USD"]
        for currency, amount in self.portfolio.items():
            if currency not in ["USD", "PHP_RATE"] and amount > 0:
                try:
                    price_data = await self.get_price(f"{currency}/USDT")
                    if price_data["status"] == "success":
                        total_value += amount * price_data["price"]
                except:
                    pass

        return {
            "status": "success",
            "message": msg,
            "portfolio_value_usd": total_value
        }

    async def close_connections(self):
        """Cleanup required by CCXT async"""
        try:
            await self.binance.close()
            await self.mexc.close()
            logger.info("CryptoWorker connections closed")
        except Exception as e:
            logger.error(f"Error closing connections: {e}")
