'use client';

import { motion } from 'framer-motion';
import { Clock, Activity } from 'lucide-react';

export function TraceEngine() {
  const traces = [
    { time: '19:06:29', event: 'SYNTH', status: 'complete' },
    { time: '19:06:28', event: 'Spec Mirror Workstation v3.1', status: 'info' },
    { time: '19:06:27', event: 'Initialized', status: 'success' },
    { time: '19:06:26', event: 'MATERIAL OPTIMAL', status: 'active' },
    { time: '19:06:25', event: 'ENTRYPOINT: 0.002%', status: 'info' },
  ];

  return (
    <motion.div
      className="nexus-panel p-4 h-full"
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
    >
      <div className="flex items-center gap-2 mb-4">
        <Clock className="w-4 h-4 text-[#00FFC2]" />
        <span className="nexus-spec-header">TRACE ENGINE</span>
      </div>
      
      <div className="space-y-2 font-mono text-xs">
        {traces.map((trace, index) => (
          <motion.div
            key={index}
            className="flex items-center gap-3 text-white/70"
            initial={{ opacity: 0, x: -10 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: index * 0.1 }}
          >
            <span className="text-white/30 w-16">{trace.time}</span>
            <span className={`flex-1 ${
              trace.status === 'active' ? 'text-[#00FFC2]' :
              trace.status === 'success' ? 'text-green-400' :
              trace.status === 'info' ? 'text-blue-400' : ''
            }`}>
              {trace.event}
            </span>
            {trace.status === 'active' && (
              <Activity className="w-3 h-3 text-[#00FFC2] animate-pulse" />
            )}
          </motion.div>
        ))}
      </div>
      
      <div className="mt-4 pt-3 border-t border-white/10">
        <div className="flex items-center justify-between text-[10px]">
          <span className="text-white/30">SURFACE STATUS</span>
          <span className="text-[#00FFC2] font-mono">LOCKED</span>
        </div>
      </div>
    </motion.div>
  );
}
