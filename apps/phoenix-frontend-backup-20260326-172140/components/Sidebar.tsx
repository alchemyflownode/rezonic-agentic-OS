'use client';
import { Cpu, Globe, Code, Shield, HardDrive, Zap, Search, Activity } from 'lucide-react';

const workers = [
  { id: 'sys', name: 'System Monitor', icon: Activity, type: 'KerneL' },
  { id: 'search', name: 'Deep Search', icon: Search, type: 'Python' },
  { id: 'code', name: 'Code Mutation', icon: Code, type: 'Python' },
  { id: 'vram', name: 'VRAM Monitor', icon: Zap, type: 'Python' },
  // ... adding 24 more slots dynamically in the UI
];

export function Sidebar() {
  return (
    <aside className="w-[300px] bg-[#030405] border-r border-[#1E293B] flex flex-col h-full p-4">
      <div className="mb-8 px-2">
        <h1 className="text-xl font-bold tracking-tighter text-[#2DD4BF]">OBSIDIAN</h1>
        <p className="text-[10px] text-slate-500 uppercase tracking-widest">Unified Interface • 28 Active</p>
      </div>
      
      <div className="grid grid-cols-2 gap-2 overflow-y-auto pr-2 custom-scrollbar">
        {workers.map((worker) => (
          <button key={worker.id} className="flex flex-col items-center justify-center p-4 rounded-xl bg-[#0B0C0E] border border-[#1E293B] hover:border-[#2DD4BF] group transition-all">
            <worker.icon size={20} className="text-slate-500 group-hover:text-[#2DD4BF] mb-2" />
            <span className="text-[10px] text-center font-medium text-slate-400">{worker.name}</span>
            <div className="mt-2 w-1.5 h-1.5 rounded-full bg-[#2DD4BF] neural-pulse" />
          </button>
        ))}
      </div>
    </aside>
  );
}
