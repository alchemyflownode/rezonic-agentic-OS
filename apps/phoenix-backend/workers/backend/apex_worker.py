"""
APEX WORKER - Autonomous Trading Bot
3-layer risk protection with real exchange integration
"""

import asyncio
import ccxt.async_support as ccxt
import redis.asyncio as redis
import json
import os
import time
import logging
import numpy as np
from datetime import datetime
from dotenv import load_dotenv
from typing import Dict, Any, Optional, List

from .base_worker import BaseWorker

load_dotenv()
logger = logging.getLogger(__name__)

class ApexWorker(BaseWorker):
    """Autonomous trading bot with 3-layer risk protection"""
    
    def __init__(self, hive_bus=None):
        super().__init__("apex", "Autonomous Trading Bot with 3-layer risk")
        self.bot_id = "apex_001"
        self.redis_client = None
        self.exchanges = {}
        self.running = True
        self.halted = False
        self.bots = {}  # For multiple bot instances
        
        # Risk state
        self.peak_balance = 100000
        self.current_balance = 100000
        self.drawdown = 0
        self.max_drawdown_limit = 0.15
        
        # Circuit breaker
        self.error_count = 0
        self.error_threshold = 5
        self.circuit_breaker_active = False
        
        # Performance tracking
        self.wins = 0
        self.losses = 0
        self.total_trades = 0
        self.generation = 142
        
        # PHP conversion
        self.php_rate = 58.0
        
        self.is_ready = True
        
    async def process(self, task: str, **kwargs) -> Dict[str, Any]:
        """Process trading commands"""
        self.log("info", f"Processing trading command: {task[:50]}...")
        
        task_lower = task.lower()
        
        # Command routing
        if task_lower.startswith("/trade "):
            return await self._handle_trade_command(task[7:])
        elif task_lower.startswith("/status"):
            return await self._get_status()
        elif task_lower.startswith("/risk"):
            return await self._get_risk_metrics()
        elif task_lower.startswith("/halt"):
            self.halted = True
            return {"content": "🛑 Trading halted by user command"}
        elif task_lower.startswith("/resume"):
            self.halted = False
            return {"content": "▶️ Trading resumed"}
        else:
            return await self._analyze_market(task)
    
    async def initialize(self):
        """Initialize connections"""
        # Connect to Redis
        self.redis_client = await redis.from_url(
            'redis://localhost:6379',
            decode_responses=True
        )
        self.log("info", f"Connected to Redis")
        
        # Initialize exchanges (testnet first!)
        self.exchanges['binance'] = ccxt.binance({
            'apiKey': os.getenv('BINANCE_TESTNET_KEY', ''),
            'secret': os.getenv('BINANCE_TESTNET_SECRET', ''),
            'enableRateLimit': True,
            'options': {'defaultType': 'spot'}
        })
        self.exchanges['binance'].set_sandbox_mode(True)
        
        self.exchanges['okx'] = ccxt.okx({
            'apiKey': os.getenv('OKX_TESTNET_KEY', ''),
            'secret': os.getenv('OKX_TESTNET_SECRET', ''),
            'password': os.getenv('OKX_TESTNET_PASSWORD', ''),
            'enableRateLimit': True
        })
        self.exchanges['okx'].set_sandbox_mode(True)
        
        self.log("info", "Connected to exchanges")
        
        # Subscribe to commands
        asyncio.create_task(self._listen_for_commands())
        
        # Start main loop
        asyncio.create_task(self._run())
    
    async def _listen_for_commands(self):
        """Listen for Redis commands from gateway"""
        pubsub = self.redis_client.pubsub()
        await pubsub.subscribe('bot_commands')
        
        async for message in pubsub.listen():
            if message['type'] == 'message':
                try:
                    cmd = json.loads(message['data'])
                    await self._handle_redis_command(cmd)
                except Exception as e:
                    self.log("error", f"Command error: {e}")
    
    async def _handle_redis_command(self, cmd):
        """Handle incoming Redis commands"""
        action = cmd.get('action')
        
        if action == 'HALT_ALL':
            self.log("warning", "🛑 EMERGENCY HALT RECEIVED")
            self.halted = True
            await self._publish_log('ERROR', '⚠️ BOT HALTED BY KILL SWITCH')
            
        elif action == 'RESUME':
            self.log("info", "▶️ Resume command received")
            self.halted = False
            self.error_count = 0
            self.circuit_breaker_active = False
            await self._publish_log('INFO', 'Trading resumed')
            
        elif action == 'UPDATE_RISK':
            self.log("info", f"⚖️ Risk update: {cmd.get('data')}")
            if 'max_drawdown' in cmd['data']:
                self.max_drawdown_limit = cmd['data']['max_drawdown']
                
        elif action == 'MANUAL_TRADE':
            self.log("info", f"📊 Manual trade: {cmd.get('data')}")
            await self._execute_trade(cmd['data'])
    
    async def _fetch_market_data(self) -> List[Dict]:
        """Fetch real market data from exchanges"""
        market_data = []
        
        for name, exchange in self.exchanges.items():
            try:
                start = time.time()
                ticker = await exchange.fetch_ticker('BTC/USDT')
                latency = int((time.time() - start) * 1000)
                
                market_data.append({
                    "name": name.upper(),
                    "btcPrice": ticker['last'] * self.php_rate,
                    "ethPrice": 0,
                    "latency": latency,
                    "status": "SYNCED" if latency < 100 else "DEGRADED"
                })
                
                self.error_count = max(0, self.error_count - 1)
                
            except Exception as e:
                self.log("error", f"Error fetching from {name}: {e}")
                self.error_count += 1
                
                if self.error_count >= self.error_threshold:
                    self.circuit_breaker_active = True
                    await self._publish_log('ERROR', 'CIRCUIT BREAKER ACTIVE')
        
        return market_data
    
    async def _calculate_risk(self) -> Dict:
        """Calculate current risk metrics"""
        import random
        change = random.uniform(-0.02, 0.03)
        self.current_balance *= (1 + change)
        
        if self.current_balance > self.peak_balance:
            self.peak_balance = self.current_balance
        
        self.drawdown = (self.peak_balance - self.current_balance) / self.peak_balance
        
        if self.drawdown >= self.max_drawdown_limit:
            self.halted = True
            await self._publish_log('ERROR', f'MAX DRAWDOWN: {self.drawdown:.2%}')
        
        win_rate = self.wins / max(self.total_trades, 1)
        kelly = max(0, min(0.25, win_rate - (1 - win_rate) / 2))
        
        return {
            "kellyFraction": round(kelly, 2),
            "circuitBreakerStatus": "ACTIVE" if self.circuit_breaker_active else "ARMED",
            "currentDrawdown": round(self.drawdown, 3),
            "maxDrawdown": self.max_drawdown_limit
        }
    
    async def _generate_arbitrage(self) -> List[Dict]:
        """Find arbitrage opportunities"""
        arbitrage = []
        
        if len(self.exchanges) >= 2 and not self.halted:
            try:
                binance = await self.exchanges['binance'].fetch_ticker('BTC/USDT')
                okx = await self.exchanges['okx'].fetch_ticker('BTC/USDT')
                
                spread = abs(binance['last'] - okx['last']) / min(binance['last'], okx['last'])
                
                if spread > 0.001:
                    arbitrage.append({
                        "pair": "BTC/USDT",
                        "spread": f"+{spread*100:.2f}%",
                        "route": "BINANCE → OKX" if binance['last'] < okx['last'] else "OKX → BINANCE",
                        "buy": min(binance['last'], okx['last']) * self.php_rate,
                        "sell": max(binance['last'], okx['last']) * self.php_rate
                    })
            except Exception as e:
                self.log("error", f"Arbitrage error: {e}")
        
        return arbitrage
    
    async def _execute_trade(self, signal):
        """Execute a trade with risk checks"""
        if self.halted or self.circuit_breaker_active:
            await self._publish_log('WARNING', 'Trade blocked by risk system')
            return None
        
        try:
            exchange = self.exchanges['binance']
            order = await exchange.create_order(
                symbol='BTC/USDT',
                type='limit' if signal.get('limit') else 'market',
                side=signal.get('side', 'buy').lower(),
                amount=signal.get('amount', 0.001),
                price=signal.get('price')
            )
            
            self.total_trades += 1
            
            await self._publish_log('EXECUTION', 
                f"Trade executed: {signal.get('side')} {signal.get('amount')} BTC")
            
            await self.redis_client.publish('tradeExecution', json.dumps({
                "botId": self.bot_id,
                "pair": "BTC/USDT",
                "side": signal.get('side'),
                "amount": signal.get('amount'),
                "price": signal.get('price'),
                "timestamp": datetime.now().isoformat()
            }))
            
            return {"status": "success", "order": str(order)}
            
        except Exception as e:
            self.log("error", f"Trade failed: {e}")
            await self._publish_log('ERROR', f"Trade failed: {str(e)}")
            return {"status": "error", "message": str(e)}
    
    async def _publish_log(self, log_type, message):
        """Publish log to Redis"""
        log_entry = {
            "timestamp": datetime.now().strftime("%H:%M:%S"),
            "type": log_type,
            "message": message
        }
        await self.redis_client.publish('agentLog', json.dumps(log_entry))
    
    async def _run(self):
        """Main bot loop"""
        await self._publish_log('INFO', 'Apex Worker initialized')
        
        while self.running:
            try:
                if not self.halted and not self.circuit_breaker_active:
                    # Update UI data
                    market_data = await self._fetch_market_data()
                    if market_data:
                        await self.redis_client.publish('marketUpdate', json.dumps(market_data))
                    
                    arbitrage = await self._generate_arbitrage()
                    if arbitrage:
                        await self.redis_client.publish('arbitrageUpdate', json.dumps(arbitrage))
                    
                    risk = await self._calculate_risk()
                    await self.redis_client.publish('riskUpdate', json.dumps(risk))
                
                await asyncio.sleep(1)
                
            except Exception as e:
                self.log("error", f"Main loop error: {e}")
                await self._publish_log('ERROR', f"System error: {str(e)}")
                await asyncio.sleep(5)
    
    # Command handlers for VERA
    async def _handle_trade_command(self, args: str) -> Dict:
        """Handle /trade command"""
        parts = args.split()
        if len(parts) < 2:
            return {"content": "⚠️ Usage: /trade [buy/sell] [amount]"}
        
        side = parts[0].upper()
        amount = float(parts[1]) if len(parts) > 1 else 0.001
        
        signal = {
            "side": side,
            "amount": amount,
            "limit": False
        }
        
        result = await self._execute_trade(signal)
        
        if result.get("status") == "success":
            return {"content": f"✅ Trade executed: {side} {amount} BTC"}
        else:
            return {"content": f"❌ Trade failed: {result.get('message', 'Unknown error')}"}
    
    async def _get_status(self) -> Dict:
        """Get bot status"""
        return {
            "content": f"""🤖 **Apex Worker Status**
• Generation: {self.generation}
• Status: {'HALTED' if self.halted else 'HUNTING'}
• Trades: {self.total_trades}
• Win Rate: {(self.wins/max(self.total_trades,1)*100):.1f}%
• Circuit Breaker: {'ACTIVE' if self.circuit_breaker_active else 'ARMED'}
• Balance: ${self.current_balance:,.0f}"""
        }
    
    async def _get_risk_metrics(self) -> Dict:
        """Get risk metrics"""
        risk = await self._calculate_risk()
        return {
            "content": f"""⚖️ **Risk Metrics**
• Kelly Fraction: {risk['kellyFraction']*100}%
• Current Drawdown: {risk['currentDrawdown']*100:.1f}%
• Max Drawdown Limit: {risk['maxDrawdown']*100}%
• Circuit Breaker: {risk['circuitBreakerStatus']}"""
        }
    
    async def _analyze_market(self, query: str) -> Dict:
        """Analyze market based on query"""
        # Simple market analysis
        market_data = await self._fetch_market_data()
        arbitrage = await self._generate_arbitrage()
        risk = await self._calculate_risk()
        
        response = f"""📊 **Market Analysis**
        
**Exchange Status:**
"""
        for ex in market_data:
            response += f"• {ex['name']}: ₱{ex['btcPrice']:,.0f} ({ex['latency']}ms) {ex['status']}\n"
        
        if arbitrage:
            response += f"\n**Arbitrage Opportunity:**\n"
            for arb in arbitrage:
                response += f"• {arb['pair']}: {arb['spread']} ({arb['route']})\n"
        
        response += f"\n**Risk Status:**\n"
        response += f"• Kelly: {risk['kellyFraction']*100}%\n"
        response += f"• Drawdown: {risk['currentDrawdown']*100:.1f}%\n"
        response += f"• Circuit Breaker: {risk['circuitBreakerStatus']}"
        
        return {"content": response}
