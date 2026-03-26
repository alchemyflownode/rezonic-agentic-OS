"""
AI Trader Worker - Intelligent trading using Ollama models
"""

import asyncio
import random
import json
import time
import hashlib
from typing import Dict, List, Any, Optional
from datetime import datetime
import numpy as np

from ..base_worker import SovereignWorker
from ..models.smart_router import smart_router, TaskType

class AITraderWorker(SovereignWorker):
    """
    AI-powered trading bot that uses Ollama models for decisions
    """
    
    def __init__(self, hive_bus=None, kernel_memory=None):
        super().__init__("ai_trader", hive_bus, kernel_memory)
        
        # Trading state
        self.balance = 1245678.0  # Starting balance
        self.positions = []
        self.trade_history = []
        self.total_trades = 0
        self.winning_trades = 0
        
        # AI strategy
        self.current_strategy = "momentum"
        self.risk_level = "medium"  # low, medium, high
        self.max_position_size = 0.1  # 10% of balance
        
        # Market data cache
        self.market_cache = {}
        self.last_update = 0
        
        # Performance tracking
        self.daily_pnl = 0
        self.peak_balance = self.balance
        self.max_drawdown = 0
        
        logger.info(f"  🤖 AITraderWorker initialized")
    
    async def analyze_market(self, pair: str, market_data: Dict) -> Dict:
        """Use AI to analyze market conditions"""
        
        # Prepare market context
        context = {
            'pair': pair,
            'price': market_data.get('price', 0),
            'change_24h': market_data.get('change', 0),
            'volume': market_data.get('volume', '0'),
            'rsi': self._calculate_rsi(market_data),
            'macd': self._calculate_macd(market_data),
            'support': market_data.get('price', 0) * 0.95,
            'resistance': market_data.get('price', 0) * 1.05
        }
        
        # Use different models based on strategy
        if self.current_strategy == "momentum":
            prompt = f"""Analyze this market data and determine if it's a good BUY/SELL/HOLD opportunity:

Pair: {pair}
Current Price: ${context['price']:,.2f}
24h Change: {context['change_24h']}%
Volume: {context['volume']}
RSI: {context['rsi']:.1f}
Support: ${context['support']:,.2f}
Resistance: ${context['resistance']:,.2f}

Consider:
1. Momentum indicators (RSI > 70 overbought, < 30 oversold)
2. Trend strength (strong uptrend if price > 20-day MA)
3. Volume confirmation

Respond with JSON:
{{
    "signal": "BUY/SELL/HOLD",
    "confidence": 0.0-1.0,
    "reasoning": "brief explanation",
    "suggested_size": 0.0-1.0,
    "stop_loss": price,
    "take_profit": price
}}"""
            
            # Use qwen2.5-coder for analysis
            model = "qwen2.5-coder:14b"
            
        elif self.current_strategy == "mean_reversion":
            prompt = f"""Analyze mean reversion opportunity:

Pair: {pair}
Price: ${context['price']:,.2f}
Support: ${context['support']:,.2f}
Resistance: ${context['resistance']:,.2f}
RSI: {context['rsi']:.1f}

Mean reversion signals:
- BUY when price near support and RSI < 30
- SELL when price near resistance and RSI > 70

Respond with JSON analysis."""
            model = "gemma2:9b"
            
        else:
            prompt = f"""Quick market analysis for {pair}:

Price: ${context['price']:,.2f}
Change: {context['change_24h']}%

Provide BUY/SELL/HOLD recommendation."""
            model = "phi3.5:3.8b"
        
        # Get AI analysis (simulated for now)
        # In production, this would call Ollama
        analysis = await self._simulate_ai_analysis(context)
        
        return analysis
    
    async def _simulate_ai_analysis(self, context: Dict) -> Dict:
        """Simulate AI analysis (replace with actual Ollama calls)"""
        
        # Simulate AI thinking
        await asyncio.sleep(0.5)
        
        price = context['price']
        rsi = context['rsi']
        change = context['change_24h']
        
        # Simple trading logic (replace with real AI)
        if rsi < 30 and change < -2:
            signal = "BUY"
            confidence = 0.85
            reasoning = "Oversold conditions with strong downward momentum - buying opportunity"
            size = 0.05
            stop_loss = price * 0.97
            take_profit = price * 1.05
        elif rsi > 70 and change > 2:
            signal = "SELL"
            confidence = 0.75
            reasoning = "Overbought conditions - taking profits"
            size = 0.03
            stop_loss = price * 1.03
            take_profit = price * 0.95
        else:
            signal = "HOLD"
            confidence = 0.6
            reasoning = "No clear signals - waiting for better entry"
            size = 0
            stop_loss = 0
            take_profit = 0
        
        # Add some randomness for realism
        if random.random() < 0.1:  # 10% chance of random signal
            signal = random.choice(["BUY", "SELL"])
            confidence = random.uniform(0.6, 0.9)
            
        return {
            'signal': signal,
            'confidence': confidence,
            'reasoning': reasoning,
            'suggested_size': size,
            'stop_loss': stop_loss,
            'take_profit': take_profit,
            'timestamp': time.time()
        }
    
    def _calculate_rsi(self, data: Dict) -> float:
        """Calculate Relative Strength Index"""
        # Simplified RSI calculation
        change = data.get('change', 0)
        if change > 0:
            return 50 + min(change * 5, 50)
        else:
            return 50 - min(abs(change) * 5, 50)
    
    def _calculate_macd(self, data: Dict) -> Dict:
        """Calculate MACD indicator"""
        # Simplified MACD
        return {
            'macd': random.uniform(-2, 2),
            'signal': random.uniform(-2, 2),
            'histogram': random.uniform(-1, 1)
        }
    
    async def execute_trade(self, pair: str, signal: str, size: float, price: float) -> Dict:
        """Execute a trade based on AI signal"""
        
        if signal == "HOLD" or size == 0:
            return {'executed': False, 'reason': 'No trade signal'}
        
        # Calculate position size
        position_value = self.balance * size
        if position_value > self.balance:
            position_value = self.balance * 0.5
        
        amount = position_value / price
        
        # Execute trade
        if signal == "BUY":
            cost = amount * price
            if cost <= self.balance:
                self.balance -= cost
                position = {
                    'id': f"pos_{len(self.positions)}_{int(time.time())}",
                    'pair': pair,
                    'type': 'LONG',
                    'amount': amount,
                    'entry_price': price,
                    'current_price': price,
                    'pnl': 0,
                    'timestamp': time.time()
                }
                self.positions.append(position)
                
                trade_result = {
                    'executed': True,
                    'type': 'BUY',
                    'pair': pair,
                    'amount': amount,
                    'price': price,
                    'cost': cost,
                    'new_balance': self.balance
                }
                
        elif signal == "SELL":
            # Find position to sell
            position = next((p for p in self.positions if p['pair'] == pair), None)
            if position:
                revenue = position['amount'] * price
                self.balance += revenue
                pnl = revenue - (position['amount'] * position['entry_price'])
                
                if pnl > 0:
                    self.winning_trades += 1
                
                self.positions.remove(position)
                
                trade_result = {
                    'executed': True,
                    'type': 'SELL',
                    'pair': pair,
                    'amount': position['amount'],
                    'price': price,
                    'revenue': revenue,
                    'pnl': pnl,
                    'new_balance': self.balance
                }
            else:
                return {'executed': False, 'reason': f'No {pair} position to sell'}
        
        # Update stats
        self.total_trades += 1
        self.daily_pnl += trade_result.get('pnl', 0)
        if self.balance > self.peak_balance:
            self.peak_balance = self.balance
        
        drawdown = (self.peak_balance - self.balance) / self.peak_balance * 100
        self.max_drawdown = max(self.max_drawdown, drawdown)
        
        # Log trade
        self.trade_history.append({
            **trade_result,
            'timestamp': time.time(),
            'balance_after': self.balance
        })
        
        return trade_result
    
    async def process(self, task: str) -> str:
        """Process trading commands"""
        task_lower = task.lower()
        
        if '/ai trade' in task_lower:
            return await self._manual_ai_trade(task)
        elif '/ai status' in task_lower:
            return await self._get_ai_status()
        elif '/ai strategy' in task_lower:
            return await self._set_strategy(task)
        elif '/ai risk' in task_lower:
            return await self._set_risk(task)
        
        return "🤖 AI Trader ready. Try: /ai trade, /ai status, /ai strategy momentum"
    
    async def _manual_ai_trade(self, task: str) -> str:
        """Manually trigger AI trade analysis"""
        parts = task.split()
        pair = parts[2] if len(parts) > 2 else 'BTC/PHP'
        
        # Get market data (simulated)
        market_data = {
            'price': 4524067 + random.randint(-10000, 10000),
            'change': random.uniform(-5, 5),
            'volume': f"{random.randint(100, 500)}M"
        }
        
        # AI analysis
        analysis = await self.analyze_market(pair, market_data)
        
        result = f"""🤖 **AI TRADING ANALYSIS**
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Pair: {pair}
Signal: {analysis['signal']} ({(analysis['confidence']*100):.0f}% confidence)
Reasoning: {analysis['reasoning']}

📊 Market Data:
  Price: ${market_data['price']:,.2f}
  24h Change: {market_data['change']:.1f}%
  Volume: {market_data['volume']}

💡 Suggestion: {
    'Buy' if analysis['signal'] == 'BUY' else 
    'Sell' if analysis['signal'] == 'SELL' else 
    'Hold'
} with {analysis['suggested_size']*100:.0f}% of portfolio
"""
        
        # Auto-execute if confidence is high
        if analysis['confidence'] > 0.8 and analysis['signal'] != 'HOLD':
            trade = await self.execute_trade(
                pair, 
                analysis['signal'], 
                analysis['suggested_size'],
                market_data['price']
            )
            
            if trade['executed']:
                result += f"\n✅ Auto-executed {analysis['signal']} order"
                if 'pnl' in trade:
                    result += f"\n   P&L: ${trade['pnl']:,.2f}"
        
        return result
    
    async def _get_ai_status(self) -> str:
        """Get AI trader status"""
        win_rate = (self.winning_trades / self.total_trades * 100) if self.total_trades > 0 else 0
        
        status = f"""🤖 **AI TRADER STATUS**
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
💰 Balance: ${self.balance:,.2f}
📈 Daily P&L: ${self.daily_pnl:,.2f}
📊 Positions: {len(self.positions)}
🎯 Win Rate: {win_rate:.1f}% ({self.winning_trades}/{self.total_trades})
📉 Max Drawdown: {self.max_drawdown:.1f}%

⚙️ Configuration:
  Strategy: {self.current_strategy.upper()}
  Risk Level: {self.risk_level.upper()}
  Max Position: {self.max_position_size*100:.0f}%

🔮 Current Signals:
"""
        # Show signals for each pair
        for pair in ['BTC/PHP', 'ETH/PHP', 'SOL/PHP']:
            market_data = {
                'price': 4524067 + random.randint(-10000, 10000),
                'change': random.uniform(-5, 5),
                'volume': f"{random.randint(100, 500)}M"
            }
            analysis = await self.analyze_market(pair, market_data)
            arrow = "🟢" if analysis['signal'] == 'BUY' else "🔴" if analysis['signal'] == 'SELL' else "⚪"
            status += f"\n  {arrow} {pair}: {analysis['signal']} ({(analysis['confidence']*100):.0f}%)"
        
        return status
    
    async def _set_strategy(self, task: str) -> str:
        """Set trading strategy"""
        parts = task.split()
        if len(parts) < 3:
            return "Usage: /ai strategy [momentum|mean_reversion|scalping|grid]"
        
        strategy = parts[2].lower()
        valid_strategies = ['momentum', 'mean_reversion', 'scalping', 'grid']
        
        if strategy in valid_strategies:
            self.current_strategy = strategy
            return f"✅ Strategy set to: {strategy.upper()}"
        else:
            return f"❌ Invalid strategy. Choose: {', '.join(valid_strategies)}"
    
    async def _set_risk(self, task: str) -> str:
        """Set risk level"""
        parts = task.split()
        if len(parts) < 3:
            return "Usage: /ai risk [low|medium|high]"
        
        risk = parts[2].lower()
        valid_risks = ['low', 'medium', 'high']
        
        if risk in valid_risks:
            self.risk_level = risk
            # Adjust position size based on risk
            if risk == 'low':
                self.max_position_size = 0.05
            elif risk == 'medium':
                self.max_position_size = 0.1
            else:  # high
                self.max_position_size = 0.2
            return f"✅ Risk set to: {risk.upper()} (Max position: {self.max_position_size*100:.0f}%)"
        else:
            return f"❌ Invalid risk. Choose: {', '.join(valid_risks)}"
    
    async def auto_trade_cycle(self):
        """Automatic trading cycle for bot mode"""
        pairs = ['BTC/PHP', 'ETH/PHP', 'SOL/PHP']
        
        while True:
            # Analyze each pair
            for pair in pairs:
                # Simulate market data
                market_data = {
                    'price': 4524067 + random.randint(-20000, 20000),
                    'change': random.uniform(-3, 3),
                    'volume': f"{random.randint(100, 500)}M"
                }
                
                # Get AI analysis
                analysis = await self.analyze_market(pair, market_data)
                
                # Execute if confident
                if analysis['confidence'] > 0.7 and analysis['signal'] != 'HOLD':
                    trade = await self.execute_trade(
                        pair,
                        analysis['signal'],
                        analysis['suggested_size'],
                        market_data['price']
                    )
                    
                    if trade['executed']:
                        # Publish trade event
                        if self.hive_bus:
                            self.hive_bus.publish('ai_trade.executed', {
                                'pair': pair,
                                'type': trade['type'],
                                'amount': trade.get('amount', 0),
                                'pnl': trade.get('pnl', 0),
                                'balance': self.balance
                            })
            
            # Wait before next cycle
            await asyncio.sleep(5)  # Trade every 5 seconds in simulation
            
    async def start_auto_trading(self):
        """Start the auto-trading loop"""
        asyncio.create_task(self.auto_trade_cycle())
        logger.info("🤖 AI Auto-trading started")

# Add to your worker factory