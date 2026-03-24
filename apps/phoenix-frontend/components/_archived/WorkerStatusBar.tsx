'use client';

import { motion } from 'framer-motion';

interface WorkerStatusBarProps {
  totalWorkers: number;
  activeCount: number;
  pythonCount: number;
  apiCount: number;
}

export function WorkerStatusBar({ totalWorkers, activeCount, pythonCount, apiCount }: WorkerStatusBarProps) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="fixed bottom-4 left-1/2 -translate-x-1/2 bg-black/80 backdrop-blur-xl border border-white/10 rounded-full px-6 py-3 flex items-center gap-6"
    >
      <div className="flex items-center gap-2">
        <div className="w-2 h-2 bg-green-400 rounded-full animate-pulse" />
        <span className="text-xs text-white/80">{activeCount} Active</span>
      </div>
      
      <div className="w-px h-4 bg-white/10" />
      
      <div className="flex items-center gap-4">
        <div className="flex items-center gap-1">
          <span className="text-xs text-white/50">Python:</span>
          <span className="text-xs text-[#00FFC2]">{pythonCount}</span>
        </div>
        <div className="flex items-center gap-1">
          <span className="text-xs text-white/50">API:</span>
          <span className="text-xs text-[#8B5CF6]">{apiCount}</span>
        </div>
        <div className="flex items-center gap-1">
          <span className="text-xs text-white/50">Total:</span>
          <span className="text-xs text-white">{totalWorkers}</span>
        </div>
      </div>
    </motion.div>
  );
}
