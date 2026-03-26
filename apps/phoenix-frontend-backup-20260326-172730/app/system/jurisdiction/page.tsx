// app/system/jurisdiction/page.tsx
'use client';

import { motion } from 'framer-motion';
import { Shield, Activity, Cpu, Zap, Lock, ShieldCheck, GitBranch } from 'lucide-react';

export default function JurisdictionPage() {
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
            <div className="w-12 h-12 rounded-2xl bg-gradient-to-br from-[#8AB4F8]/20 to-[#7dcfff]/20 border border-[#8AB4F8]/30 flex items-center justify-center">
              <Shield className="w-6 h-6 text-[#8AB4F8]" />
            </div>
            <div>
              <h1 className="text-3xl font-bold bg-gradient-to-r from-[#c0caf5] to-[#8AB4F8] bg-clip-text text-transparent">
                JURISDICTION
              </h1>
              <p className="text-[#565f89] mt-1">Hardware Trust & Security Enforcement</p>
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
              <Lock className="w-4 h-4 text-[#8AB4F8]" />
              <h2 className="text-sm font-bold text-white">Security Status</h2>
            </div>
            <div className="flex items-center gap-3 p-3 bg-white/5 rounded-lg">
              <div className="w-2 h-2 rounded-full bg-[#9ece6a] animate-pulse" />
              <span className="text-sm font-mono text-white">Capability Active</span>
              <span className="ml-auto text-[10px] text-[#9ece6a]">SCE ENFORCED</span>
            </div>

            <div className="mt-6 space-y-3">
              <div className="flex justify-between text-[10px]">
                <span className="text-[#565f89]">Hardware Trust Level</span>
                <span className="text-[#9ece6a]">Level 4</span>
              </div>
              <div className="w-full h-1 bg-white/10 rounded-full overflow-hidden">
                <div className="w-[98%] h-full bg-gradient-to-r from-[#8AB4F8] to-[#7dcfff] rounded-full" />
              </div>
              <div className="flex justify-between text-[10px] mt-3">
                <span className="text-[#565f89]">Constitutional Integrity</span>
                <span className="text-[#7dcfff]">98.2%</span>
              </div>
              <div className="w-full h-1 bg-white/10 rounded-full overflow-hidden">
                <div className="w-[98%] h-full bg-[#7dcfff] rounded-full" />
              </div>
            </div>
          </motion.div>

          <motion.div
            initial={{ x: 20, opacity: 0 }}
            animate={{ x: 0, opacity: 1 }}
            transition={{ delay: 0.2 }}
            className="bg-black/30 backdrop-blur-xl border border-[#7dcfff]/10 rounded-2xl p-6"
          >
            <div className="flex items-center gap-2 mb-4">
              <GitBranch className="w-4 h-4 text-[#9B72CB]" />
              <h2 className="text-sm font-bold text-white">Drift Chain</h2>
            </div>
            <div className="space-y-2">
              <div className="flex justify-between text-[9px] font-mono p-2 bg-white/5 rounded">
                <span className="text-[#565f89]">Current Lock</span>
                <code className="text-[#7dcfff]">0x7f3e8a2c1b9d4f5e</code>
              </div>
              <div className="flex justify-between text-[9px] font-mono p-2 bg-white/5 rounded">
                <span className="text-[#565f89]">Previous Lock</span>
                <code className="text-[#9ece6a]">0x4b2a1f9e8d7c6b5a</code>
              </div>
              <div className="flex justify-between text-[9px] font-mono p-2 bg-white/5 rounded">
                <span className="text-[#565f89]">Chain Length</span>
                <span className="text-white">1,247 blocks</span>
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
            <ShieldCheck className="w-4 h-4 text-[#9ece6a]" />
            <h2 className="text-sm font-bold text-white">Constitutional Oversight</h2>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="p-3 bg-white/5 rounded-lg">
              <div className="text-[8px] text-[#565f89] mb-1">Sovereignty Score</div>
              <div className="text-lg font-bold text-white">98/100</div>
            </div>
            <div className="p-3 bg-white/5 rounded-lg">
              <div className="text-[8px] text-[#565f89] mb-1">Transparency</div>
              <div className="text-lg font-bold text-white">100%</div>
            </div>
            <div className="p-3 bg-white/5 rounded-lg">
              <div className="text-[8px] text-[#565f89] mb-1">Accountability</div>
              <div className="text-lg font-bold text-white">Auditable</div>
            </div>
          </div>
        </motion.div>
      </div>
    </div>
  );
}