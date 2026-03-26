"use client";
import { motion } from 'framer-motion';

export const RezMeter = ({ value, label, color = "var(--accent-cyan)" }: { value: number; label: string; color?: string }) => (
  <div className="flex flex-col gap-1">
    <div className="flex justify-between items-baseline">
      <span className="text-[10px] font-mono uppercase tracking-[0.2em] text-white/30">{label}</span>
      <span className="text-xs font-mono font-bold" style={{ color }}>{Math.round(value * 100)}%</span>
    </div>
    <div className="relative h-[2px] bg-white/5 rounded-full overflow-hidden">
      <motion.div 
        className="absolute inset-y-0 left-0"
        style={{ backgroundColor: color }}
        initial={{ width: 0 }}
        animate={{ width: `${value * 100}%` }}
        transition={{ type: "spring", stiffness: 100, damping: 30 }}
      />
    </div>
  </div>
);

