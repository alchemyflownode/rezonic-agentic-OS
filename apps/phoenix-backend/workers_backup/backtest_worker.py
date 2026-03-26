import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
# backend/workers/backtest_worker.py
import pandas as pd
import numpy as np
from typing import Dict, Any, List
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class BacktestWorker:
    """Professional backtesting with institutional metrics"""
    
    signature = {
        "id": "backtest_worker",
        "label": "?? Strategy Validator",
        "inputs": ["historical_data", "strategy_params"],
        "outputs": ["performance_metrics"],
        "threshold": 0.4,
        "parallel": True
    }
    
    async def _process_impl(self, **kwargs) -> Dict[str, Any]:
        """Run backtest and return professional metrics"""
        
        data = kwargs.get('data', [])
        strategy_name = kwargs.get('strategy_name', 'Custom Strategy')
        
        if not data:
            return {'error': 'No data provided'}
            
        # Convert to DataFrame
        df = pd.DataFrame(data, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        
        # Run simulation (simplified for example)
        trades = self._simulate_trades(df)
        
        # Calculate professional metrics
        metrics = self._calculate_metrics(trades, df)
        
        return {
            "worker_id": "backtest_worker",
            "strategy": strategy_name,
            "metrics": metrics,
            "trades": len(trades),
            "period": {
                "start": df['timestamp'].iloc[0],
                "end": df['timestamp'].iloc[-1],
                "days": len(df)
            }
        }
    
    def _simulate_trades(self, df):
        """Simplified trade simulation"""
        trades = []
        in_position = False
        entry_price = 0
        
        for i in range(20, len(df)):
            fast_ma = df['close'].iloc[i-10:i].mean()
            slow_ma = df['close'].iloc[i-30:i].mean()
            
            if fast_ma > slow_ma and not in_position:
                entry_price = df['close'].iloc[i]
                in_position = True
                
            elif fast_ma < slow_ma and in_position:
                exit_price = df['close'].iloc[i]
                pnl = (exit_price - entry_price) / entry_price
                trades.append({
                    'entry': entry_price,
                    'exit': exit_price,
                    'pnl': pnl,
                    'timestamp': df['timestamp'].iloc[i]
                })
                in_position = False
                
        return trades
    
    def _calculate_metrics(self, trades, df):
        """Calculate institutional-grade metrics"""
        
        if not trades:
            return {
                "win_rate": 0,
                "profit_factor": 0,
                "max_drawdown": 0,
                "sharpe_ratio": 0,
                "expectancy": 0,
                "total_return": 0
            }
            
        df_trades = pd.DataFrame(trades)
        winning_trades = df_trades[df_trades['pnl'] > 0]
        losing_trades = df_trades[df_trades['pnl'] <= 0]
        
        win_rate = len(winning_trades) / len(trades) if trades else 0
        
        gross_profit = winning_trades['pnl'].sum() if not winning_trades.empty else 0
        gross_loss = abs(losing_trades['pnl'].sum()) if not losing_trades.empty else 1
        
        profit_factor = gross_profit / gross_loss if gross_loss != 0 else 0
        
        cumulative = (1 + df_trades['pnl']).cumprod()
        running_max = cumulative.expanding().max()
        drawdown = (cumulative - running_max) / running_max
        max_drawdown = drawdown.min() if not drawdown.empty else 0
        
        returns = df_trades['pnl'].values
        sharpe = np.sqrt(252) * returns.mean() / returns.std() if returns.std() > 0 else 0
        
        avg_win = winning_trades['pnl'].mean() if not winning_trades.empty else 0
        avg_loss = losing_trades['pnl'].mean() if not losing_trades.empty else 0
        expectancy = (win_rate * avg_win) - ((1 - win_rate) * abs(avg_loss))
        
        total_return = (cumulative.iloc[-1] - 1) if not cumulative.empty else 0
        
        return {
            "win_rate": round(win_rate * 100, 1),
            "profit_factor": round(profit_factor, 2),
            "max_drawdown": round(abs(max_drawdown) * 100, 1),
            "sharpe_ratio": round(sharpe, 2),
            "expectancy": round(expectancy * 100, 2),
            "total_return": round(total_return * 100, 1)
        }


    async def process(self, task: str, memory_bus=None):
        """Process task – auto-generated stub"""
        return {"content": f"Processed: {task[:50]}", "worker": self.name}
    
    async def health_check(self):
        """Return worker health status"""
        return {"worker": self.name, "status": "healthy", "timestamp": __import__('time').time()}

