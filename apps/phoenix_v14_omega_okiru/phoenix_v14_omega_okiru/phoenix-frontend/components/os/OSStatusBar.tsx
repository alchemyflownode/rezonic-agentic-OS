'use client';

import { useEffect, useState } from 'react';
import { motion } from 'framer-motion';

export const OSStatusBar = () => {
  const [latency, setLatency] = useState(12);
  const [cpuLoad, setCpuLoad] = useState(24);
  const [activeWorkers, setActiveWorkers] = useState(56);

  useEffect(() => {
    const interval = setInterval(() => {
      setLatency(prev => Math.max(8, Math.min(60, prev + (Math.random() * 10 - 5))));
      setCpuLoad(prev => Math.max(10, Math.min(90, prev + (Math.random() * 4 - 2))));
      setActiveWorkers(prev => Math.max(32, Math.min(68, prev + (Math.random() * 2 - 1))));
    }, 1500);
    return () => clearInterval(interval);
  }, []);

  return (
    <motion.div 
      className="h-10 border-t border-white/[0.05] bg-[#0a0a0c]/80 backdrop-blur-sm flex items-center px-6 text-[10px] font-mono uppercase tracking-widest text-[#565f89] justify-between"
      initial={{ y: 20, opacity: 0 }}
      animate={{ y: 0, opacity: 1 }}
      transition={{ duration: 0.3, delay: 0.2 }}
    >
      <div className="flex items-center gap-8">
        <div className="flex items-center gap-2">
          <motion.div 
            className="w-1.5 h-1.5 rounded-full bg-[#9ece6a]"
            animate={{ scale: [1, 1.2, 1] }}
            transition={{ duration: 1.5, repeat: Infinity }}
          />
          <span>Kernel: <span className="text-[#c0caf5]">Active</span></span>
        </div>
        <div>
          Workers: <span className="text-[#c0caf5] tabular-nums">{Math.floor(activeWorkers)} Online</span>
        </div>
        <div className="hidden md:block">
          CPU Load: <span className={cpuLoad > 80 ? 'text-[#f7768e]' : 'text-[#c0caf5]'}>
            {cpuLoad.toFixed(1)}%
          </span>
        </div>
      </div>

      <div className="flex items-center gap-8">
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-1">
            <div className="w-1 h-3 bg-white/[0.05] rounded-full overflow-hidden relative">
              <motion.div 
                className="absolute bottom-0 w-full bg-[#7dcfff]"
                style={{ height: `${Math.min(100, latency)}%` }}
                animate={{ height: `${latency}%` }}
                transition={{ duration: 0.3 }}
              />
            </div>
            <span>Ping: <span className="text-[#c0caf5] tabular-nums">{latency.toFixed(0)}ms</span></span>
          </div>
          <div className="flex items-center gap-1">
            <div className="w-1 h-3 bg-white/[0.05] rounded-full overflow-hidden relative">
              <motion.div 
                className="absolute bottom-0 w-full bg-[#00e5ff]"
                style={{ height: `${Math.min(100, cpuLoad)}%` }}
                animate={{ height: `${cpuLoad}%` }}
                transition={{ duration: 0.3 }}
              />
            </div>
          </div>
        </div>
        <div className="text-[#565f89] border-l border-white/[0.05] pl-8">
          <span className="tracking-[0.2em]">SCE v1.0</span>
        </div>
      </div>
    </motion.div>
  );
};