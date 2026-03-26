'use client';

import React from 'react';
import { DollarSign, TrendingUp, TrendingDown, RotateCcw, Bot, User, Brain } from 'lucide-react';
import { usePaperTrading } from '@/app/hooks/usePaperTrading';

export function PaperTradingPanel() {
  const { portfolio, mode, botActive, executeTrade, setTradingMode, resetPortfolio } = usePaperTrading();
  const [amount, setAmount] = React.useState('');
  const [selectedSymbol, setSelectedSymbol] = React.useState('BTC/PHP');

  const handleTrade = (type: 'BUY' | 'SELL') => {
    const numAmount = parseFloat(amount);
    if (isNaN(numAmount) || numAmount <= 0) {
      alert('Please enter a valid amount');
      return;
    }
    const result = executeTrade(selectedSymbol, type, numAmount);
    if (result.success) {
      setAmount('');
      alert(result.message);
    } else {
      alert(result.message);
    }
  };

  const formatPHP = (val: number) => {
    return new Intl.NumberFormat('en-PH', {
      style: 'currency',
      currency: 'PHP',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0
    }).format(val);
  };

  return (
    <div className="bg-[#0a0a0c] border border-white/5 rounded-2xl p-4">
      <div className="flex items-center justify-between mb-3">
        <h3 className="text-[10px] font-mono tracking-widest uppercase text-zinc-400 flex items-center gap-2">
          <DollarSign className="w-3 h-3 text-[#00e676]" /> PAPER TRADING
        </h3>
        <button
          onClick={resetPortfolio}
          className="text-[8px] font-mono text-zinc-500 hover:text-yellow-500 transition flex items-center gap-1"
        >
          <RotateCcw className="w-2 h-2" /> Reset
        </button>
      </div>

      {/* Portfolio Stats */}
      <div className="grid grid-cols-2 gap-2 mb-3">
        <div className="bg-black/30 rounded-lg p-2">
          <div className="text-[7px] text-zinc-500">Balance</div>
          <div className="text-[11px] font-bold text-white">{formatPHP(portfolio.balance)}</div>
        </div>
        <div className="bg-black/30 rounded-lg p-2">
          <div className="text-[7px] text-zinc-500">Total Value</div>
          <div className="text-[11px] font-bold text-white">{formatPHP(portfolio.totalValue)}</div>
        </div>
      </div>

      {/* Trading Mode Selector */}
      <div className="flex gap-1 mb-3">
        {(['manual', 'ai', 'hybrid'] as const).map((m) => (
          <button
            key={m}
            onClick={() => setTradingMode(m)}
            className={lex-1 py-1.5 rounded text-[8px] font-mono uppercase transition }
          >
            {m === 'manual' && <User className="w-2 h-2 inline mr-1" />}
            {m === 'ai' && <Bot className="w-2 h-2 inline mr-1" />}
            {m === 'hybrid' && <Brain className="w-2 h-2 inline mr-1" />}
            {m}
          </button>
        ))}
      </div>

      {/* Trade Form */}
      <div className="space-y-2">
        <select
          value={selectedSymbol}
          onChange={(e) => setSelectedSymbol(e.target.value)}
          className="w-full bg-black/50 border border-white/10 rounded-lg p-1.5 text-[9px] font-mono text-white"
        >
          <option>BTC/PHP</option>
          <option>ETH/PHP</option>
          <option>SOL/PHP</option>
        </select>
        <input
          type="number"
          value={amount}
          onChange={(e) => setAmount(e.target.value)}
          placeholder="Amount (units)"
          className="w-full bg-black/50 border border-white/10 rounded-lg p-1.5 text-[9px] font-mono text-white placeholder:text-zinc-600"
        />
        <div className="flex gap-2">
          <button
            onClick={() => handleTrade('BUY')}
            className="flex-1 py-1.5 bg-green-500/20 border border-green-500/30 rounded text-[9px] text-green-500 font-mono hover:bg-green-500/30"
          >
            BUY
          </button>
          <button
            onClick={() => handleTrade('SELL')}
            className="flex-1 py-1.5 bg-red-500/20 border border-red-500/30 rounded text-[9px] text-red-500 font-mono hover:bg-red-500/30"
          >
            SELL
          </button>
        </div>
      </div>

      {/* Positions */}
      {portfolio.positions.length > 0 && (
        <div className="mt-3 pt-3 border-t border-white/5">
          <div className="text-[7px] text-zinc-500 mb-2">Open Positions</div>
          {portfolio.positions.map((pos, i) => (
            <div key={i} className="flex justify-between text-[8px] font-mono mb-1">
              <span className="text-white">{pos.symbol}</span>
              <span className={pos.pnl >= 0 ? 'text-green-500' : 'text-red-500'}>
                {pos.pnl >= 0 ? '+' : ''}{pos.pnl.toFixed(2)}
              </span>
            </div>
          ))}
        </div>
      )}

      {/* Status */}
      <div className="mt-2 pt-2 border-t border-white/5">
        <div className="flex justify-between text-[7px] font-mono">
          <span className="text-zinc-500">Mode:</span>
          <span className={botActive ? 'text-[#00e676]' : 'text-zinc-400'}>
            {mode.toUpperCase()} {botActive ? '🤖' : '🔹'}
          </span>
        </div>
        <div className="flex justify-between text-[7px] font-mono mt-1">
          <span className="text-zinc-500">PnL:</span>
          <span className={portfolio.totalPnL >= 0 ? 'text-green-500' : 'text-red-500'}>
            {portfolio.totalPnL >= 0 ? '+' : ''}{formatPHP(portfolio.totalPnL)}
          </span>
        </div>
      </div>
    </div>
  );
}
