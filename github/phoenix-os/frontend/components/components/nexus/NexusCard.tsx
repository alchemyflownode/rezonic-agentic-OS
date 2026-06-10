'use client';

import { motion } from 'framer-motion';
import { ChevronRight, Zap, Activity, Lock } from 'lucide-react';

interface NexusCardProps {
  title: string;
  value?: string;
  status?: 'locked' | 'active' | 'pending';
  children?: React.ReactNode;
  className?: string;
}

export function NexusCard({ title, value, status = 'locked', children, className = '' }: NexusCardProps) {
  return (
    <motion.div
      className={`nexus-panel nexus-panel-depth p-4 ${className}`}
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ type: 'spring', stiffness: 300, damping: 25 }}
      whileHover={{ scale: 1.02 }}
    >
      <div className="flex items-center justify-between mb-3">
        <span className="nexus-spec-header">{title}</span>
        {status === 'locked' && <Lock className="w-3 h-3 text-[#00FFC2]" />}
        {status === 'active' && <Activity className="w-3 h-3 text-[#00FFC2] animate-pulse" />}
        {status === 'pending' && <Zap className="w-3 h-3 text-[#FFB800]" />}
      </div>
      
      {value && <div className="nexus-spec-value mb-2">{value}</div>}
      
      {children}
      
      <div className="flex justify-end mt-2">
        <ChevronRight className="w-4 h-4 text-white/30" />
      </div>
    </motion.div>
  );
}
