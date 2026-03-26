'use client';
import { motion } from 'framer-motion';
import { Activity, Cpu, Zap } from 'lucide-react';

export default function BacktestPage() {
  return (
    <div className="min-h-screen bg-[#030406] p-8">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="max-w-6xl mx-auto"
      >
        <div className="flex items-center gap-3 mb-8">
          <div className="w-12 h-12 rounded-xl bg-[#ff0055]/20 flex items-center justify-center">
            <Activity className="w-6 h-6 text-[#ff0055]" />
          </div>
          <div>
            <h1 className="text-3xl font-bold text-white">BACKTEST ENGINE</h1>
            <p className="text-[10px] font-mono text-[#64748B] tracking-widest">SOVEREIGN CAPABILITY  SCE PROTOCOL</p>
          </div>
        </div>
      </motion.div>
    </div>
  );
}
