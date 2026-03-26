'use client';

import { motion } from 'framer-motion';
import { Search, Lock } from 'lucide-react';

export function SurfaceInterrogation() {
  return (
    <motion.div
      className="nexus-panel p-4"
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
    >
      <div className="flex items-center gap-2 mb-4">
        <Search className="w-4 h-4 text-[#00FFC2]" />
        <span className="nexus-spec-header">SURFACE INTERROGATION</span>
      </div>
      
      <div className="space-y-3">
        <div className="nexus-metric">
          <div className="text-xs text-white/40 mb-1">CONVERGENCE APEX</div>
          <div className="text-lg font-mono text-[#00FFC2]">87.3%</div>
        </div>
        
        <div className="grid grid-cols-2 gap-2">
          <div className="bg-[#1A1A1E] p-3 rounded">
            <div className="text-[10px] text-white/30">SIDE EFFECTS</div>
            <div className="text-sm font-mono text-white/80">12</div>
          </div>
          <div className="bg-[#1A1A1E] p-3 rounded">
            <div className="text-[10px] text-white/30">CLARITY</div>
            <div className="text-sm font-mono text-[#00FFC2]">98%</div>
          </div>
        </div>
        
        <div className="mt-3 pt-3 border-t border-white/10">
          <div className="flex items-center justify-between">
            <span className="text-[10px] text-white/30">SURFACE STATUS</span>
            <div className="flex items-center gap-1">
              <Lock className="w-3 h-3 text-[#00FFC2]" />
              <span className="text-xs text-[#00FFC2]">LOCKED</span>
            </div>
          </div>
        </div>
      </div>
    </motion.div>
  );
}
