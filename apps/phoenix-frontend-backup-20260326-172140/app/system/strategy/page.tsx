// app/system/strategy/page.tsx
'use client';

import { motion } from 'framer-motion';
import { TrendingUp, Activity, Cpu, Zap, Brain, Sparkles, GitBranch } from 'lucide-react';

export default function StrategyPage() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-[#0a0a0c] via-[#050505] to-[#0a0a0c] p-8">
      <div className="fixed inset-0 pointer-events-none opacity-20">
        <div className="absolute inset-0 bg-[radial-gradient(circle_at_50%_50%,_#7dcfff_0%,_transparent_50%)] opacity-5" />
        <div className="absolute inset-0" style={{ backgroundImage: 'linear-gradient(to right, #7dcfff0a 1px, transparent 1px), linear-gradient(to bottom, #7dcfff0a 1px, transparent 1px)', backgroundSize: '40px 40px' }} />
      </div>

      <div className="relative z-10 max-w-6xl mx-auto">
        <motion.div
          initial={{ y: -20, opacity: 0 }}
          animate={{ y: 0, opacity: 1 }}
          className="mb-8"
        >
          <div className="flex items-center gap-4">
            <div className="w-12 h-12 rounded-2xl bg-gradient-to-br from-[#00e676]/20 to-[#7dcfff]/20 border border-[#00e676]/30 flex items-center justify-center">
              <TrendingUp className="w-6 h-6 text-[#00e676]" />
            </div>
            <div>
              <h1 className="text-3xl font-bold bg-gradient-to-r from-[#c0caf5] to-[#00e676] bg-clip-text text-transparent">
                STRATEGY EVOLVER
              </h1>
              <p className="text-[#565f89] mt-1">Evolutionary Strategy Optimization • SCE Protocol</p>
            </div>
          </div>
        </motion.div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <motion.div
            initial={{ x: -20, opacity: 0 }}
            animate={{ x: 0, opacity: 1 }}
            transition={{ delay: 0.1 }}
            className="bg-black/30 backdrop-blur-xl border border-[#7dcfff]/10 rounded-2xl p-6"
          >
            <div className="flex items-center gap-2 mb-4">
              <Brain className="w-4 h-4 text-[#00e676]" />
              <h2 className="text-sm font-bold text-white">Active Strategies</h2>
            </div>
            <div className="space-y-3">
              {[
                { name: 'Momentum Crossover', winRate: 67.5, evolution: 'Generation 4', color: '#7dcfff' },
                { name: 'Mean Reversion', winRate: 58.2, evolution: 'Generation 3', color: '#9B72CB' },
                { name: 'Scalping', winRate: 61.3, evolution: 'Generation 5', color: '#9ece6a' },
                { name: 'Grid Trading', winRate: 52.8, evolution: 'Generation 2', color: '#ff9e64' },
              ].map((strategy, i) => (
                <div key={i} className="p-3 bg-white/5 rounded-lg border border-white/10">
                  <div className="flex justify-between items-center mb-2">
                    <span className="text-white text-sm font-mono" style={{ color: strategy.color }}>{strategy.name}</span>
                    <span className="text-xs text-[#9ece6a]">{strategy.winRate}% WR</span>
                  </div>
                  <div className="flex justify-between text-[9px]">
                    <span className="text-[#565f89]">{strategy.evolution}</span>
                    <span className="text-[#7dcfff] flex items-center gap-1">
                      <GitBranch className="w-2.5 h-2.5" /> 12 forks
                    </span>
                  </div>
                  <div className="w-full h-1 bg-white/10 rounded-full mt-2 overflow-hidden">
                    <div className="h-full rounded-full" style={{ width: `${strategy.winRate}%`, backgroundColor: strategy.color }} />
                  </div>
                </div>
              ))}
            </div>
          </motion.div>

          <motion.div
            initial={{ x: 20, opacity: 0 }}
            animate={{ x: 0, opacity: 1 }}
            transition={{ delay: 0.2 }}
            className="bg-black/30 backdrop-blur-xl border border-[#7dcfff]/10 rounded-2xl p-6"
          >
            <div className="flex items-center gap-2 mb-4">
              <Sparkles className="w-4 h-4 text-[#ff9e64]" />
              <h2 className="text-sm font-bold text-white">Evolution Metrics</h2>
            </div>
            <div className="space-y-4">
              <div>
                <div className="flex justify-between text-[10px] mb-1">
                  <span className="text-[#565f89]">Fitness Score</span>
                  <span className="text-[#7dcfff]">94.2%</span>
                </div>
                <div className="w-full h-1 bg-white/10 rounded-full overflow-hidden">
                  <div className="w-[94%] h-full bg-gradient-to-r from-[#7dcfff] to-[#00e676] rounded-full" />
                </div>
              </div>
              <div>
                <div className="flex justify-between text-[10px] mb-1">
                  <span className="text-[#565f89]">Max Drawdown</span>
                  <span className="text-[#ff9e64]">-12.4%</span>
                </div>
                <div className="w-full h-1 bg-white/10 rounded-full overflow-hidden">
                  <div className="w-[12%] h-full bg-[#ff9e64] rounded-full" />
                </div>
              </div>
              <div className="pt-4 mt-2 border-t border-white/10">
                <div className="flex items-center justify-between text-[9px]">
                  <span className="text-[#565f89]">Evolution Generation</span>
                  <span className="text-[#9ece6a]">Gen 47</span>
                </div>
                <div className="flex items-center justify-between text-[9px] mt-2">
                  <span className="text-[#565f89]">Population Size</span>
                  <span className="text-white">128</span>
                </div>
                <div className="flex items-center justify-between text-[9px] mt-2">
                  <span className="text-[#565f89]">Mutation Rate</span>
                  <span className="text-white">2.3%</span>
                </div>
              </div>
            </div>
          </motion.div>
        </div>

        <motion.div
          initial={{ y: 20, opacity: 0 }}
          animate={{ y: 0, opacity: 1 }}
          transition={{ delay: 0.3 }}
          className="mt-6 bg-black/30 backdrop-blur-xl border border-[#7dcfff]/10 rounded-2xl p-6"
        >
          <div className="flex items-center gap-2 mb-4">
            <Cpu className="w-4 h-4 text-[#9B72CB]" />
            <h2 className="text-sm font-bold text-white">Worker Pool</h2>
          </div>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
            {['MomentumWorker', 'ReversionWorker', 'ScalpingWorker', 'GridWorker'].map((worker, i) => (
              <div key={i} className="p-2 bg-white/5 rounded-lg text-center">
                <div className="text-[9px] text-white">{worker}</div>
                <div className="text-[7px] text-[#9ece6a] mt-1">ACTIVE</div>
              </div>
            ))}
          </div>
        </motion.div>
      </div>
    </div>
  );
}