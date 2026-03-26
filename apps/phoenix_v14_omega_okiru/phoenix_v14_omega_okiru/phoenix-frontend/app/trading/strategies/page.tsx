'use client';

import React, { useState } from 'react';
import { Brain, Zap, TrendingUp } from 'lucide-react';

export default function StrategiesPage() {
  const [strategies] = useState([
    { name: 'Momentum Crossover', status: 'active', pnl: '+12.4%', risk: 'Medium' },
    { name: 'Mean Reversion', status: 'active', pnl: '+8.2%', risk: 'Low' },
    { name: 'Breakout Scaler', status: 'inactive', pnl: '+5.1%', risk: 'High' },
    { name: 'Arbitrage Hunter', status: 'active', pnl: '+15.7%', risk: 'Medium' },
    { name: 'Neural Predictor', status: 'active', pnl: '+22.3%', risk: 'High' },
  ]);

  return (
    <div className="min-h-screen bg-[#050505] p-8">
      <div className="max-w-7xl mx-auto">
        <div className="mb-8">
          <h1 className="text-2xl font-bold text-white flex items-center gap-3">
            <Brain className="w-8 h-8 text-[#9B72CB]" />
            Trading Strategies
          </h1>
          <p className="text-zinc-500 mt-2">AI-powered trading algorithms</p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {strategies.map((strategy, i) => (
            <div key={i} className="bg-[#0a0a0c] border border-white/5 rounded-xl p-6 hover:border-[#00E5FF]/30 transition">
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center gap-2">
                  <Zap className="w-5 h-5 text-[#00E5FF]" />
                  <h3 className="text-white font-bold">{strategy.name}</h3>
                </div>
                <span className="px-2 py-1 rounded-full text-[10px] font-mono bg-green-500/20 text-green-400 border border-green-500/30">
                  {strategy.status.toUpperCase()}
                </span>
              </div>
              <div className="space-y-2">
                <div className="flex justify-between text-sm">
                  <span className="text-zinc-500">PnL:</span>
                  <span className="text-green-400">{strategy.pnl}</span>
                </div>
                <div className="flex justify-between text-sm">
                  <span className="text-zinc-500">Risk Profile:</span>
                  <span className="text-white">{strategy.risk}</span>
                </div>
              </div>
              <button className="w-full mt-4 px-4 py-2 bg-[#00E5FF]/10 border border-[#00E5FF]/30 rounded-lg text-[#00E5FF] text-sm hover:bg-[#00E5FF]/20 transition">
                Configure
              </button>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
