'use client';

import React from 'react';

interface TwoBarMeterProps {
  sessionPercent: number;
  weeklyPercent: number;
  resetTime: number;
}

export const TwoBarMeter: React.FC<TwoBarMeterProps> = ({ 
  sessionPercent, 
  weeklyPercent, 
  resetTime 
}) => {
  const formatResetTime = (timestamp: number) => {
    const date = new Date(timestamp);
    return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  };

  return (
    <div className="space-y-3">
      <div className="space-y-1">
        <div className="flex justify-between text-xs">
          <span className="text-white/40 font-mono">SESSION</span>
          <span className="text-cyan-400 font-mono">{Math.min(sessionPercent, 100).toFixed(1)}%</span>
        </div>
        <div className="h-2 bg-white/10 rounded-full overflow-hidden">
          <div 
            className="h-full bg-gradient-to-r from-cyan-400 to-blue-400 rounded-full transition-all duration-500"
            style={{ width: `${Math.min(sessionPercent, 100)}%` }}
          />
        </div>
      </div>
      <div className="space-y-1">
        <div className="flex justify-between text-xs">
          <span className="text-white/40 font-mono">WEEKLY</span>
          <span className="text-purple-400 font-mono">{Math.min(weeklyPercent, 100).toFixed(1)}%</span>
        </div>
        <div className="h-2 bg-white/10 rounded-full overflow-hidden">
          <div 
            className="h-full bg-gradient-to-r from-purple-400 to-pink-400 rounded-full transition-all duration-500"
            style={{ width: `${Math.min(weeklyPercent, 100)}%` }}
          />
        </div>
      </div>
      <div suppressHydrationWarning className="flex justify-between text-[10px] text-white/30 font-mono pt-1 border-t border-white/5">
        <span>RESET</span>
        <span suppressHydrationWarning>{formatResetTime(resetTime)}</span>
      </div>
    </div>
  );
};

export default TwoBarMeter;