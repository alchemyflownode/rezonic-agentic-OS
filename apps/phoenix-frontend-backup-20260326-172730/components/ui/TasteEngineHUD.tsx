"use client";
import { ZeroDriftGlass } from './ZeroDriftGlass';
import { RezMeter } from './RezMeter';

interface HUDStats {
  intent: number;
  clarity: number;
  load: number;
  entropy: number;
}

export const TasteEngineHUD = ({ stats }: { stats: HUDStats }) => (
  <ZeroDriftGlass className="p-4 space-y-3">
    <div className="flex items-center justify-between mb-2 border-b border-white/5 pb-2">
      <h3 className="text-[9px] font-mono uppercase tracking-[0.3em] text-white/40">System Invariants</h3>
      <div className="w-1.5 h-1.5 rounded-full bg-[var(--accent-cyan)] animate-pulse" />
    </div>

    <RezMeter label="INTENT" value={stats.intent} color="var(--accent-cyan)" />
    <RezMeter label="CLARITY" value={stats.clarity} color="var(--accent-blue)" />
    <RezMeter label="COGNITIVE LOAD" value={stats.load} color="var(--accent-amber)" />
    <RezMeter label="ENTROPY" value={stats.entropy} color="var(--accent-red)" />
    
    <div className="pt-2 mt-2 border-t border-white/5 flex justify-between items-center">
      <span className="text-[8px] font-mono text-white/20">PROOF</span>
      <span className="text-[8px] font-mono text-[var(--accent-cyan)]/60">0x{(Math.random()*0xFFFFFF<<0).toString(16).toUpperCase()}</span>
    </div>
  </ZeroDriftGlass>
);

