'use client';
import { motion } from 'framer-motion';
import { Shield, Activity, Cpu, Zap } from 'lucide-react';

export default function JurisdictionPage() {
  return (
    <div className="min-h-screen bg-[#030406] p-8">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="max-w-6xl mx-auto"
      >
        <div className="flex items-center gap-3 mb-8">
          <div className="w-12 h-12 rounded-xl bg-[#8AB4F8]/20 flex items-center justify-center">
            <Shield className="w-6 h-6 text-[#8AB4F8]" />
          </div>
          <div>
            <h1 className="text-3xl font-bold text-white">JURISDICTION</h1>
            <p className="text-[10px] font-mono text-[#64748B] tracking-widest">SOVEREIGN CAPABILITY  SCE PROTOCOL</p>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div className="border border-white/10 rounded-2xl bg-black/40 p-6">
            <h2 className="text-[10px] font-mono text-[#8AB4F8] uppercase tracking-widest mb-4">Status</h2>
            <div className="flex items-center gap-3">
              <div className="w-2 h-2 rounded-full bg-[#8AB4F8] animate-pulse" />
              <span className="text-sm font-mono text-zinc-300">Capability Active</span>
            </div>
          </div>
        </div>
      </motion.div>
    </div>
  );
}
