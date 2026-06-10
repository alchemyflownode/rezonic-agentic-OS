'use client';

import { motion } from 'framer-motion';
import { Shield, AlertTriangle, Power } from 'lucide-react';
import { useSovereignStore } from '@/lib/store/useSovereignStore';

export default function KillSwitch() {
  const { telemetry } = useSovereignStore();
  const isActive = telemetry.status === 'drifted';
  const integrity = telemetry.integrity_score;
  
  return (
    <motion.div
      className={`relative overflow-hidden rounded-2xl border ${
        isActive ? 'border-red-500/50 bg-red-500/10' : 'border-[#7dcfff]/20 bg-black/30'
      } backdrop-blur-xl p-5`}
      animate={{
        boxShadow: isActive
          ? ['0 0 0px rgba(239,68,68,0)', '0 0 20px rgba(239,68,68,0.5)', '0 0 0px rgba(239,68,68,0)']
          : 'none',
      }}
      transition={{ duration: 2, repeat: Infinity }}
    >
      <div className="relative z-10">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-2">
            <Shield className={`w-4 h-4 ${isActive ? 'text-red-500' : 'text-[#7dcfff]'}`} />
            <h3 className="text-sm font-bold text-white">Sovereign Kill Switch</h3>
          </div>
          <motion.div
            className={`px-2 py-1 rounded-full text-[10px] font-mono ${
              isActive
                ? 'bg-red-500 text-white'
                : integrity > 90
                ? 'bg-green-500/20 text-green-400'
                : 'bg-yellow-500/20 text-yellow-400'
            }`}
          >
            {isActive ? 'PROTOCOL RED' : integrity > 90 ? 'ARMED' : 'DRIFT DETECTED'}
          </motion.div>
        </div>
        
        <div className="mb-4">
          <div className="text-[10px] text-[#565f89] mb-1">Constitutional Integrity</div>
          <div className="w-full h-1.5 bg-white/10 rounded-full overflow-hidden">
            <motion.div
              className={`h-full rounded-full ${isActive ? 'bg-red-500' : integrity > 90 ? 'bg-green-500' : 'bg-yellow-500'}`}
              initial={{ width: 0 }}
              animate={{ width: `${integrity}%` }}
            />
          </div>
        </div>
        
        <button
          className={`w-full py-2.5 rounded-lg font-bold text-sm transition-all ${
            isActive
              ? 'bg-gradient-to-r from-red-500/20 to-red-600/20 border border-red-500/50 text-red-400'
              : 'bg-gradient-to-r from-[#7dcfff]/20 to-[#9B72CB]/20 border border-[#7dcfff]/30 text-[#7dcfff] hover:shadow-[0_0_15px_rgba(125,207,255,0.2)]'
          }`}
        >
          <span className="flex items-center justify-center gap-2">
            {isActive ? <Power className="w-4 h-4" /> : <AlertTriangle className="w-4 h-4" />}
            {isActive ? 'RESET PROTOCOL' : 'ACTIVATE KILL SWITCH'}
          </span>
        </button>
      </div>
    </motion.div>
  );
}
