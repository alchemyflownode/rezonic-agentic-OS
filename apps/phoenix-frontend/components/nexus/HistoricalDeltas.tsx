'use client';

import { motion } from 'framer-motion';
import { GitBranch, TrendingUp, TrendingDown } from 'lucide-react';

export function HistoricalDeltas() {
  const deltas = [
    { label: 'Convergence Apex', value: '+23.4%', trend: 'up' },
    { label: 'Side Effects', value: '-2.1%', trend: 'down' },
    { label: 'Clarity', value: '98.2%', trend: 'up' },
    { label: 'Synthesis', value: '+45.6%', trend: 'up' },
  ];

  return (
    <motion.div
      className="nexus-panel p-4"
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
    >
      <div className="flex items-center gap-2 mb-4">
        <GitBranch className="w-4 h-4 text-[#00FFC2]" />
        <span className="nexus-spec-header">HISTORICAL DELTAS</span>
      </div>
      
      <div className="space-y-3">
        {deltas.map((delta, index) => (
          <motion.div
            key={index}
            className="flex items-center justify-between"
            initial={{ opacity: 0, x: -10 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: index * 0.1 }}
          >
            <span className="text-xs text-white/60">{delta.label}</span>
            <div className="flex items-center gap-2">
              <span className={`text-sm font-mono ${
                delta.trend === 'up' ? 'text-[#00FFC2]' : 'text-red-400'
              }`}>
                {delta.value}
              </span>
              {delta.trend === 'up' ? (
                <TrendingUp className="w-3 h-3 text-[#00FFC2]" />
              ) : (
                <TrendingDown className="w-3 h-3 text-red-400" />
              )}
            </div>
          </motion.div>
        ))}
      </div>
    </motion.div>
  );
}
