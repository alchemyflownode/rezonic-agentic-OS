'use client';

import React from 'react';
import { motion } from 'framer-motion';
import { Activity } from 'lucide-react';

interface IntentMeterProps {
  entropy: number;
  onRequestClarification?: () => void;
}

export const IntentMeter: React.FC<IntentMeterProps> = ({ entropy, onRequestClarification }) => {
  const confidence = 1 - entropy;
  
  const getStatusText = () => {
    if (entropy > 0.8) return 'HIGHLY UNCERTAIN';
    if (entropy > 0.5) return 'NEEDS CLARIFICATION';
    if (entropy > 0.2) return 'MODERATE CONFIDENCE';
    return 'HIGH CONFIDENCE';
  };

  const getStatusColor = () => {
    if (entropy > 0.8) return 'text-[#FF4500]';
    if (entropy > 0.5) return 'text-[#FF9800]';
    if (entropy > 0.2) return 'text-[#B388FF]';
    return 'text-[#00E676]';
  };

  return (
    <motion.div 
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      className="bg-[#0E1015]/90 backdrop-blur-md border border-[#1F222A] rounded-xl p-4 shadow-[0_8px_30px_rgba(0,0,0,0.5)]"
    >
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <Activity className="w-4 h-4 text-[#00E5FF]" />
          <span className="text-xs font-mono text-white/60 uppercase tracking-wider">INTENT CONFIDENCE</span>
        </div>
        <span className={`text-xs font-mono font-bold ${getStatusColor()}`}>
          {getStatusText()}
        </span>
      </div>

      <div className="relative h-2 bg-[#1A1D24] rounded-full overflow-hidden">
        <motion.div
          initial={{ width: 0 }}
          animate={{ width: `${confidence * 100}%` }}
          transition={{ duration: 0.3 }}
          className={`absolute left-0 top-0 h-full rounded-full ${
            confidence > 0.8 ? 'bg-[#00E676]' :
            confidence > 0.5 ? 'bg-[#B388FF]' :
            confidence > 0.2 ? 'bg-[#FF9800]' : 'bg-[#FF4500]'
          }`}
        />
      </div>

      <div className="flex justify-between text-[8px] font-mono text-white/30 mt-2">
        <span>UNCERTAIN</span>
        <span>CONFIDENT</span>
      </div>

      {entropy > 0.5 && (
        <motion.button
          initial={{ opacity: 0, height: 0 }}
          animate={{ opacity: 1, height: 'auto' }}
          onClick={onRequestClarification}
          className="mt-3 w-full py-2 bg-[#FF9800]/10 border border-[#FF9800]/30 rounded-lg text-[10px] font-mono text-[#FF9800] hover:bg-[#FF9800] hover:text-black transition-colors"
        >
          REQUEST CLARIFICATION
        </motion.button>
      )}
    </motion.div>
  );
};