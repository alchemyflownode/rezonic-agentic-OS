'use client';
import { motion } from 'framer-motion';
import { Code, Activity, Cpu, Zap } from 'lucide-react';

export default function TechDebtPage() {
  return (
    <div className="min-h-screen bg-[#030406] p-8">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="max-w-6xl mx-auto"
      >
        <div className="flex items-center gap-3 mb-8">
          <div className="w-12 h-12 rounded-xl bg-[#9B72CB]/20 flex items-center justify-center">
            <Code className="w-6 h-6 text-[#9B72CB]" />
          </div>
          <div>
            <h1 className="text-3xl font-bold text-white">TECH DEBT SCANNER</h1>
            <p className="text-[10px] font-mono text-[#64748B] tracking-widest">SOVEREIGN CAPABILITY  SCE PROTOCOL</p>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div className="border border-white/10 rounded-2xl bg-black/40 p-6">
            <h2 className="text-[10px] font-mono text-[#9B72CB] uppercase tracking-widest mb-4">Status</h2>
            <div className="flex items-center gap-3">
              <div className="w-2 h-2 rounded-full bg-[#9B72CB] animate-pulse" />
              <span className="text-sm font-mono text-zinc-300">Capability Active</span>
            </div>
            <div className="mt-4 p-4 bg-white/5 rounded-lg">
              <div className="text-[8px] font-mono text-[#64748B]">WORKERS</div>
              <div className="text-2xl font-bold text-white mt-1">8</div>
            </div>
          </div>

          <div className="border border-white/10 rounded-2xl bg-black/40 p-6">
            <h2 className="text-[10px] font-mono text-[#9B72CB] uppercase tracking-widest mb-4">Recent Activity</h2>
            <div className="space-y-3">
              {[1,2,3].map(i => (
                <div key={i} className="flex items-center gap-3 p-2 bg-white/5 rounded-lg">
                  <Activity className="w-3 h-3 text-[#9B72CB]" />
                  <span className="text-[9px] font-mono text-zinc-400">Scan completed {i}m ago</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </motion.div>
    </div>
  );
}
