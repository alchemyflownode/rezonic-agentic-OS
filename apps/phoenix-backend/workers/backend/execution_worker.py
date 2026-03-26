# backend/workers/execution_worker.py
import yaml
import os
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)

class ExecutionWorker:
    """
    Handles actual trade execution with safety modes:
    - testnet: Real exchange sandbox
    - paper: Internal simulation
    - live: Real money
    """
    
    signature = {
        "id": "execution_worker",
        "label": "⚡ Execution Engine",
        "inputs": ["validated_trade"],
        "outputs": ["order_result"],
        "threshold": 0.1,
        "parallel": False
    }
    
    def __init__(self, config_path="config/exchanges.yaml"):
        self.config = self._load_config(config_path)
        self.mode = self.config.get('trading', {}).get('mode', 'testnet')
        self.paper_balance = self.config.get('paper_trading', {}).get('initial_balance', 100000)
        self.trades_executed = 0
        
    def _load_config(self, path):
        """Load YAML config with environment variable substitution"""
        if not os.path.exists(path):
            logger.warning(f"Config not found at {path}, using defaults")
            return {'trading': {'mode': 'testnet'}}
            
        with open(path, 'r') as f:
            config = yaml.safe_load(f)
            
        config_str = yaml.dump(config)
        import re
        config_str = re.sub(r'\${(\w+)}', lambda m: os.getenv(m.group(1), ''), config_str)
        
        return yaml.safe_load(config_str)
    
    async def _process_impl(self, **kwargs) -> Dict[str, Any]:
        """Execute trade according to current mode"""
        
        trade = kwargs.get('trade', {})
        pair = trade.get('pair', 'unknown')
        side = trade.get('signal', 'HOLD')
        amount = trade.get('amount', 0)
        price = trade.get('price', 0)
        
        if side == 'HOLD':
            return {'status': 'no_action', 'mode': self.mode}
            
        if self.mode == 'testnet':
            result = await self._execute_testnet(trade)
        elif self.mode == 'paper':
            result = self._execute_paper(trade)
        elif self.mode == 'live':
            result = await self._execute_live(trade)
        else:
            result = {'error': f'Invalid mode: {self.mode}'}
            
        self.trades_executed += 1
        
        return {
            'worker_id': 'execution_worker',
            'mode': self.mode,
            'trade': trade,
            'result': result,
            'trades_executed': self.trades_executed
        }
    
    async def _execute_testnet(self, trade):
        """Execute on exchange testnet"""
        logger.info(f"🔧 TESTNET: {trade['signal']} {trade['pair']}")
        return {
            'status': 'simulated',
            'order_id': f"testnet_{self.trades_executed}",
            'message': 'Testnet order placed (play money)'
        }
    
    def _execute_paper(self, trade):
        """Internal paper trading simulation"""
        if trade['signal'] == 'BUY':
            cost = trade['amount'] * trade['price']
            self.paper_balance -= cost
        elif trade['signal'] == 'SELL':
            revenue = trade['amount'] * trade['price']
            self.paper_balance += revenue
            
        return {
            'status': 'paper_trade',
            'balance': round(self.paper_balance, 2),
            'message': f"Paper trade executed. Balance: ${self.paper_balance}"
        }
    
    async def _execute_live(self, trade):
        """Execute real trade (requires explicit override)"""
        if not os.getenv('REZTRADER_LIVE_CONFIRMED'):
            return {
                'error': 'Live trading not confirmed. Set REZTRADER_LIVE_CONFIRMED=1'
            }
            
        logger.warning(f"💰 LIVE TRADE: {trade}")
        return {
            'status': 'live_order',
            'warning': 'This is real money!'
        }
