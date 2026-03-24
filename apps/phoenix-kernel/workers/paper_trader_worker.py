import sys
from pathlib import Path

# Add parent directory to path
parent_dir = Path(__file__).parent.parent
if str(parent_dir) not in sys.path:
    sys.path.insert(0, str(parent_dir))
"""Paper Trading Worker - Safe Practice Trading"""

import asyncio
import logging
import random
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from workers.base_worker import BaseWorker

logger = logging.getLogger(__name__)

class PaperTraderWorker(BaseWorker):
    """
    Paper Trading Worker - Practice trading with virtual money
    Simulates real market conditions for safe learning
    """
    
    def __init__(self, hive_bus=None):
        super().__init__("paper_trader", hive_bus)
        
        # Paper trading account
        self.account = {
            'balance': 1000000,  # Start with 1M PHP virtual money
            'equity': 1000000,
            'free_margin': 1000000,
            'margin_level': 100,
            'open_positions': [],
            'order_history': [],
            'total_trades': 0,
            'winning_trades': 0,
            'losing_trades': 0,
            'profit_loss': 0
        }
        
        # Market data simulation
        self.market_data = {
            'BTC/PHP': {'bid': 4500000, 'ask': 4510000, 'change': 2.3, 'volume': 1250},
            'ETH/PHP': {'bid': 189000, 'ask': 189500, 'change': 1.8, 'volume': 8500},
            'BNB/PHP': {'bid': 31500, 'ask': 31600, 'change': 0.5, 'volume': 15000},
            'SOL/PHP': {'bid': 12500, 'ask': 12600, 'change': -0.3, 'volume': 25000},
        }
        
        # Trading strategies
        self.strategies = {
            'momentum': self._momentum_strategy,
            'mean_reversion': self._mean_reversion_strategy,
            'grid': self._grid_strategy,
            'scalping': self._scalping_strategy
        }
        
        # AI Bot state
        self.ai_bot_active = False
        self.ai_bot_strategy = 'momentum'
        self.ai_bot_trades = []
        self.ai_bot_stats = {
            'total_trades': 0,
            'win_rate': 0,
            'profit_loss': 0,
            'avg_win': 0,
            'avg_loss': 0
        }
        
        logger.info("  ?? PaperTraderWorker initialized")
    
    async def health_check(self):
        """Health check for paper trader"""
        base = await super().health_check()
        return {
            **base,
            'balance': self.account['balance'],
            'open_positions': len(self.account['open_positions']),
            'ai_bot_active': self.ai_bot_active
        }
    
    async def process(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Process trading tasks"""
        action = task.get('action', 'status')
        
        if action == 'buy':
            return await self._execute_trade('BUY', task)
        elif action == 'sell':
            return await self._execute_trade('SELL', task)
        elif action == 'close':
            return await self._close_position(task.get('position_id'))
        elif action == 'market_data':
            return await self._get_market_data(task.get('pair'))
        elif action == 'account_status':
            return await self._get_account_status()
        elif action == 'ai_start':
            return await self._start_ai_bot(task)
        elif action == 'ai_stop':
            return await self._stop_ai_bot()
        elif action == 'ai_status':
            return await self._get_ai_status()
        elif action == 'reset':
            return await self._reset_account()
        else:
            return await self._get_account_status()
    
    async def _execute_trade(self, side: str, params: Dict) -> Dict:
        """Execute a paper trade"""
        pair = params.get('pair', 'BTC/PHP')
        amount = params.get('amount', 0.01)
        order_type = params.get('type', 'market')
        limit_price = params.get('price', None)
        
        # Get current market price
        market = self.market_data.get(pair, self.market_data['BTC/PHP'])
        price = market['ask'] if side == 'BUY' else market['bid']
        
        # Calculate cost
        cost = amount * price
        
        # Check if enough balance
        if cost > self.account['balance']:
            return {
                'status': 'REJECTED',
                'error': 'Insufficient balance',
                'required': cost,
                'available': self.account['balance']
            }
        
        # Create position
        position = {
            'id': f"pos_{int(time.time()*1000)}",
            'pair': pair,
            'side': side,
            'amount': amount,
            'entry_price': price,
            'current_price': price,
            'pnl': 0,
            'pnl_percent': 0,
            'timestamp': datetime.now().isoformat(),
            'status': 'OPEN'
        }
        
        self.account['open_positions'].append(position)
        self.account['balance'] -= cost
        self.account['total_trades'] += 1
        
        # Store in memory
        if self.hive_bus:
            self.hive_bus.store(
                f"trade:{position['id']}",
                position,
                tags=['paper_trade', side.lower(), pair.lower()]
            )
        
        return {
            'status': 'EXECUTED',
            'position': position,
            'account': await self._get_account_status()
        }
    
    async def _close_position(self, position_id: str) -> Dict:
        """Close an open position"""
        for i, pos in enumerate(self.account['open_positions']):
            if pos['id'] == position_id:
                # Get current price
                market = self.market_data.get(pos['pair'], self.market_data['BTC/PHP'])
                close_price = market['bid'] if pos['side'] == 'BUY' else market['ask']
                
                # Calculate P&L
                if pos['side'] == 'BUY':
                    pnl = (close_price - pos['entry_price']) * pos['amount']
                else:
                    pnl = (pos['entry_price'] - close_price) * pos['amount']
                
                # Update account
                pos['close_price'] = close_price
                pos['pnl'] = pnl
                pos['pnl_percent'] = (pnl / (pos['entry_price'] * pos['amount'])) * 100
                pos['status'] = 'CLOSED'
                pos['close_time'] = datetime.now().isoformat()
                
                self.account['balance'] += (pos['entry_price'] * pos['amount']) + pnl
                self.account['profit_loss'] += pnl
                
                if pnl > 0:
                    self.account['winning_trades'] += 1
                else:
                    self.account['losing_trades'] += 1
                
                # Move to history
                closed_pos = self.account['open_positions'].pop(i)
                self.account['order_history'].append(closed_pos)
                
                return {
                    'status': 'CLOSED',
                    'position': closed_pos,
                    'account': await self._get_account_status()
                }
        
        return {'status': 'ERROR', 'error': 'Position not found'}
    
    async def _get_market_data(self, pair: Optional[str] = None) -> Dict:
        """Get simulated market data"""
        # Simulate price movements
        for p in self.market_data:
            change = random.uniform(-0.02, 0.02)
            self.market_data[p]['bid'] *= (1 + change)
            self.market_data[p]['ask'] = self.market_data[p]['bid'] * (1 + random.uniform(0.001, 0.002))
            self.market_data[p]['change'] = change * 100
        
        if pair and pair in self.market_data:
            return self.market_data[pair]
        
        return self.market_data
    
    async def _get_account_status(self) -> Dict:
        """Get current account status"""
        # Update open positions with current prices
        total_pnl = 0
        for pos in self.account['open_positions']:
            market = self.market_data.get(pos['pair'], self.market_data['BTC/PHP'])
            current_price = market['bid'] if pos['side'] == 'BUY' else market['ask']
            pos['current_price'] = current_price
            
            if pos['side'] == 'BUY':
                pos['pnl'] = (current_price - pos['entry_price']) * pos['amount']
            else:
                pos['pnl'] = (pos['entry_price'] - current_price) * pos['amount']
            
            pos['pnl_percent'] = (pos['pnl'] / (pos['entry_price'] * pos['amount'])) * 100
            total_pnl += pos['pnl']
        
        self.account['equity'] = self.account['balance'] + total_pnl
        self.account['free_margin'] = self.account['equity']
        
        return self.account
    
    async def _reset_account(self) -> Dict:
        """Reset paper trading account"""
        self.account = {
            'balance': 1000000,
            'equity': 1000000,
            'free_margin': 1000000,
            'margin_level': 100,
            'open_positions': [],
            'order_history': [],
            'total_trades': 0,
            'winning_trades': 0,
            'losing_trades': 0,
            'profit_loss': 0
        }
        
        return {'status': 'RESET', 'account': self.account}
    
    # ===== AI BOT METHODS =====
    
    async def _start_ai_bot(self, params: Dict) -> Dict:
        """Start the AI trading bot"""
        self.ai_bot_active = True
        self.ai_bot_strategy = params.get('strategy', 'momentum')
        
        # Start bot loop in background
        asyncio.create_task(self._ai_bot_loop())
        
        return {
            'status': 'STARTED',
            'strategy': self.ai_bot_strategy,
            'message': f'AI Bot started with {self.ai_bot_strategy} strategy'
        }
    
    async def _stop_ai_bot(self) -> Dict:
        """Stop the AI trading bot"""
        self.ai_bot_active = False
        return {'status': 'STOPPED', 'stats': self.ai_bot_stats}
    
    async def _get_ai_status(self) -> Dict:
        """Get AI bot status"""
        return {
            'active': self.ai_bot_active,
            'strategy': self.ai_bot_strategy,
            'stats': self.ai_bot_stats,
            'trades': self.ai_bot_trades[-10:]  # Last 10 trades
        }
    
    async def _ai_bot_loop(self):
        """Main AI bot trading loop"""
        while self.ai_bot_active:
            try:
                # Get market data
                await self._get_market_data()
                
                # Run strategy
                strategy_func = self.strategies.get(self.ai_bot_strategy, self._momentum_strategy)
                signal = await strategy_func()
                
                # Execute if signal is strong
                if signal['confidence'] > 0.7:
                    result = await self._execute_trade(
                        signal['side'],
                        {
                            'pair': signal['pair'],
                            'amount': signal['amount'],
                            'type': 'market'
                        }
                    )
                    
                    if result['status'] == 'EXECUTED':
                        self.ai_bot_trades.append({
                            'time': datetime.now().isoformat(),
                            'signal': signal,
                            'result': 'EXECUTED'
                        })
                        
                        # Randomly close positions
                        if self.account['open_positions'] and random.random() > 0.7:
                            pos = random.choice(self.account['open_positions'])
                            await self._close_position(pos['id'])
                
                # Update stats
                await self._update_ai_stats()
                
                # Wait before next iteration
                await asyncio.sleep(5)  # Trade every 5 seconds
                
            except Exception as e:
                logger.error(f"AI Bot error: {e}")
                await asyncio.sleep(10)
    
    async def _momentum_strategy(self) -> Dict:
        """Momentum trading strategy"""
        pair = random.choice(list(self.market_data.keys()))
        market = self.market_data[pair]
        
        # Simple momentum signal
        if market['change'] > 1.5:
            return {
                'side': 'BUY',
                'pair': pair,
                'amount': 0.01,
                'confidence': random.uniform(0.7, 0.9),
                'reason': f'Strong momentum: {market["change"]:.1f}%'
            }
        elif market['change'] < -1.5:
            return {
                'side': 'SELL',
                'pair': pair,
                'amount': 0.01,
                'confidence': random.uniform(0.7, 0.9),
                'reason': f'Strong downward momentum: {market["change"]:.1f}%'
            }
        
        return {'side': 'HOLD', 'confidence': 0}
    
    async def _mean_reversion_strategy(self) -> Dict:
        """Mean reversion strategy"""
        pair = random.choice(list(self.market_data.keys()))
        market = self.market_data[pair]
        
        # Simulate moving average deviation
        deviation = random.uniform(-3, 3)
        
        if deviation < -2:
            return {
                'side': 'BUY',
                'pair': pair,
                'amount': 0.01,
                'confidence': 0.8,
                'reason': f'Price below MA by {abs(deviation):.1f}%'
            }
        elif deviation > 2:
            return {
                'side': 'SELL',
                'pair': pair,
                'amount': 0.01,
                'confidence': 0.8,
                'reason': f'Price above MA by {deviation:.1f}%'
            }
        
        return {'side': 'HOLD', 'confidence': 0}
    
    async def _grid_strategy(self) -> Dict:
        """Grid trading strategy"""
        pair = random.choice(list(self.market_data.keys()))
        
        # Simulate grid levels
        grid_level = random.randint(1, 10)
        
        if grid_level <= 3:
            return {
                'side': 'BUY',
                'pair': pair,
                'amount': 0.01,
                'confidence': 0.6,
                'reason': f'Grid level {grid_level} - accumulation zone'
            }
        elif grid_level >= 8:
            return {
                'side': 'SELL',
                'pair': pair,
                'amount': 0.01,
                'confidence': 0.6,
                'reason': f'Grid level {grid_level} - distribution zone'
            }
        
        return {'side': 'HOLD', 'confidence': 0}
    
    async def _scalping_strategy(self) -> Dict:
        """Scalping strategy - quick small profits"""
        pair = random.choice(list(self.market_data.keys()))
        
        # Quick in and out trades
        if random.random() > 0.5:
            return {
                'side': 'BUY',
                'pair': pair,
                'amount': 0.005,
                'confidence': 0.65,
                'reason': 'Quick scalp opportunity'
            }
        
        return {'side': 'HOLD', 'confidence': 0}
    
    async def _update_ai_stats(self):
        """Update AI bot statistics"""
        if self.account['total_trades'] > 0:
            win_rate = (self.account['winning_trades'] / self.account['total_trades']) * 100
            
            self.ai_bot_stats = {
                'total_trades': self.account['total_trades'],
                'win_rate': round(win_rate, 2),
                'profit_loss': self.account['profit_loss'],
                'open_positions': len(self.account['open_positions'])
            }
    
    async def shutdown(self):
        """Shutdown the paper trader"""
        self.ai_bot_active = False
        logger.info("  ?? PaperTraderWorker shutting down")



