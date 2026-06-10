'use client';

import { Shield, Wifi } from 'lucide-react';

export function PremiumHeader() {
  return (
    <header className="flex items-center justify-between px-6 py-4 bg-[#0F172A] border-b border-white/10">
      <div className="flex items-center gap-4">
        <div className="flex items-center gap-2">
          <Shield className="w-6 h-6 text-[#00FFC2]" />
          <h1 className="text-xl font-bold text-white tracking-tight">SOVEREIGN OS</h1>
        </div>
        <span className="text-sm text-white/40 px-3 py-1 bg-white/5 rounded-full">v2026 • LOCAL AI</span>
      </div>
      
      <div className="flex items-center gap-4">
        <div className="flex items-center gap-2 px-3 py-1.5 bg-white/5 rounded-full">
          <div className="w-2 h-2 bg-[#00FFC2] rounded-full animate-pulse" />
          <span className="text-sm text-white/80">LIVE</span>
        </div>
        
        <div className="flex items-center gap-1">
          <Wifi className="w-4 h-4 text-[#00FFC2]" />
          <span className="text-sm text-white/60">100%</span>
        </div>
      </div>
    </header>
  );
}
