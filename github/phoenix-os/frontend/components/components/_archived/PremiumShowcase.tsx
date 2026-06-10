'use client';

import React from 'react';
import { Brain, Eye, Hand, Database, Cpu, Zap, Activity, Network, Thermometer } from 'lucide-react';

export const PremiumShowcase = () => {
  return (
    <div className="fixed bottom-4 left-1/2 -translate-x-1/2 z-50">
      <div className="premium-glass px-6 py-3 flex items-center gap-6">
        <div className="flex items-center gap-2">
          <span className="w-2 h-2 bg-green-400 rounded-full animate-pulse-glow" />
          <span className="text-xs font-mono text-white/60">PREMIUM UI ACTIVE</span>
        </div>
        <div className="flex gap-3">
          <div className="w-6 h-6 rounded-full bg-gradient-to-r from-cyan-400 to-purple-400 animate-pulse" />
          <div className="w-6 h-6 rounded-full bg-gradient-to-r from-purple-400 to-orange-400 animate-pulse delay-100" />
          <div className="w-6 h-6 rounded-full bg-gradient-to-r from-orange-400 to-cyan-400 animate-pulse delay-200" />
        </div>
      </div>
    </div>
  );
};
