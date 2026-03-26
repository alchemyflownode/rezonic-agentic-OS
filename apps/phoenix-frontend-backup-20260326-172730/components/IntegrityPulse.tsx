'use client';

import { motion } from 'framer-motion';
import { useSovereignStore } from '@/lib/store/useSovereignStore';

export default function IntegrityPulse() {
  const { integrityHistory, telemetry } = useSovereignStore();
  const { integrity_score, status } = telemetry;
  const isDrifted = status === 'drifted';

  const getColor = (value: number) => {
    if (value > 95) return '#9ece6a';
    if (value > 85) return '#e0af68';
    if (value > 75) return '#ff9e64';
    return '#f7768e';
  };

  return (
    <div className="bg-black/30 backdrop-blur-xl border border-[#7dcfff]/10 rounded-2xl p-5">
      <div className="flex justify-between items-center mb-3">
        <h3 className="text-[10px] text-[#565f89] font-mono tracking-wider">
          {isDrifted ? '⚠️ PROTOCOL RED' : 'INTEGRITY PULSE'}
        </h3>
        <motion.span
          animate={{ color: isDrifted ? '#f7768e' : getColor(integrity_score) }}
          className="text-sm font-mono"
        >
          {integrity_score.toFixed(1)}%
        </motion.span>
      </div>
      
      <div className="h-12 w-full flex items-end gap-[2px]">
        {integrityHistory.map((value, i) => {
          const height = Math.max(8, (value / 100) * 40);
          const color = getColor(value);
          
          return (
            <motion.div
              key={i}
              initial={{ height: 0 }}
              animate={{ height: `${height}px` }}
              transition={{ duration: 0.3, delay: i * 0.01 }}
              className="flex-1 rounded-t-sm"
              style={{ backgroundColor: color, opacity: isDrifted ? 0.5 : 1 }}
            />
          );
        })}
      </div>
    </div>
  );
}
