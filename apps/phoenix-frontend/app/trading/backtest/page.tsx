'use client';

import React, { useState } from 'react';
import { BarChart2, Play, Calendar, TrendingUp, TrendingDown, Activity } from 'lucide-react';

export default function BacktestPage() {
  const [symbol, setSymbol] = useState('BTC/PHP');
  const [startDate, setStartDate] = useState('2024-01-01');
  const [endDate, setEndDate] = useState('2024-12-31');
  const [running, setRunning] = useState(false);
  const [results, setResults] = useState<any>(null);

  const handleRunBacktest = async () => {
    setRunning(true);
    // Simulate backtest
    setTimeout(() => {
      setResults({
        totalReturn: '+47.3%',
        sharpeRatio: 1.82,
        maxDrawdown: '-12.4%',
        winRate: '68%',
        trades: 156
      });
      setRunning(false);
    }, 2000);
  };

  return (
    <div className="min-h-screen bg-[#050505] p-8">
      <div className="max-w-7xl mx-auto">
        <div className="mb-8">
          <h1 className="text-2xl font-bold text-white flex items-center gap-3">
            <BarChart2 className="w-8 h-8 text-[#00E5FF]" />
            Backtest Engine
          </h1>
          <p className="text-zinc-500 mt-2">Historical strategy validation</p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-1 bg-[#0a0a0c] border border-white/5 rounded-xl p-6">
            <h2 className="text-lg font-bold text-white mb-4">Parameters</h2>
            <div className="space-y-4">
              <div>
                <label className="block text-sm text-zinc-500 mb-2">Symbol</label>
                <select 
                  value={symbol}
                  onChange={(e) => setSymbol(e.target.value)}
                  className="w-full bg-black/50 border border-white/10 rounded-lg px-4 py-2 text-white"
                >
                  <option>BTC/PHP</option>
                  <option>ETH/PHP</option>
                  <option>SOL/PHP</option>
                </select>
              </div>
              <div>
                <label className="block text-sm text-zinc-500 mb-2">Start Date</label>
                <input
                  type="date"
                  value={startDate}
                  onChange={(e) => setStartDate(e.target.value)}
                  className="w-full bg-black/50 border border-white/10 rounded-lg px-4 py-2 text-white"
                />
              </div>
              <div>
                <label className="block text-sm text-zinc-500 mb-2">End Date</label>
                <input
                  type="date"
                  value={endDate}
                  onChange={(e) => setEndDate(e.target.value)}
                  className="w-full bg-black/50 border border-white/10 rounded-lg px-4 py-2 text-white"
                />
              </div>
              <button
                onClick={handleRunBacktest}
                disabled={running}
                className="w-full py-3 bg-[#00E5FF]/20 border border-[#00E5FF]/30 rounded-lg text-[#00E5FF] hover:bg-[#00E5FF]/30 transition disabled:opacity-50 flex items-center justify-center gap-2"
              >
                <Play className="w-4 h-4" />
                {running ? 'Running...' : 'Run Backtest'}
              </button>
            </div>
          </div>

          <div className="lg:col-span-2 bg-[#0a0a0c] border border-white/5 rounded-xl p-6">
            <h2 className="text-lg font-bold text-white mb-4">Results</h2>
            {results ? (
              <div className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div className="bg-black/50 rounded-lg p-4 text-center">
                    <div className="text-sm text-zinc-500 mb-1">Total Return</div>
                    <div className="text-2xl font-bold text-green-400">{results.totalReturn}</div>
                  </div>
                  <div className="bg-black/50 rounded-lg p-4 text-center">
                    <div className="text-sm text-zinc-500 mb-1">Sharpe Ratio</div>
                    <div className="text-2xl font-bold text-[#00E5FF]">{results.sharpeRatio}</div>
                  </div>
                  <div className="bg-black/50 rounded-lg p-4 text-center">
                    <div className="text-sm text-zinc-500 mb-1">Max Drawdown</div>
                    <div className="text-2xl font-bold text-red-400">{results.maxDrawdown}</div>
                  </div>
                  <div className="bg-black/50 rounded-lg p-4 text-center">
                    <div className="text-sm text-zinc-500 mb-1">Win Rate</div>
                    <div className="text-2xl font-bold text-[#9B72CB]">{results.winRate}</div>
                  </div>
                </div>
                <div className="bg-black/50 rounded-lg p-4">
                  <div className="flex justify-between items-center">
                    <span className="text-zinc-500">Total Trades</span>
                    <span className="text-white font-bold">{results.trades}</span>
                  </div>
                </div>
              </div>
            ) : (
              <div className="flex flex-col items-center justify-center h-64 text-zinc-500">
                <Activity className="w-12 h-12 mb-4 opacity-30" />
                <p className="text-center">Configure parameters and run backtest to see results</p>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
