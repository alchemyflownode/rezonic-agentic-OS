'use client';

import { useState, useEffect } from 'react';
import { Terminal, Cpu, HardDrive, Activity, Settings, Minimize, Maximize, X } from 'lucide-react';

export function SovereignTitleBar() {
  const [time, setTime] = useState('');
  const [cpuTemp, setCpuTemp] = useState(42);
  const [memory, setMemory] = useState(8.4);

  useEffect(() => {
    const updateTime = () => {
      const now = new Date();
      setTime(now.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }));
    };
    
    updateTime();
    const interval = setInterval(updateTime, 1000);
    
    // Simulate system stats
    const statsInterval = setInterval(() => {
      setCpuTemp(Math.floor(Math.random() * 15) + 38);
      setMemory((Math.random() * 4 + 6).toFixed(1));
    }, 5000);
    
    return () => {
      clearInterval(interval);
      clearInterval(statsInterval);
    };
  }, []);

  return (
    <div className="ide-title-bar">
      <div className="flex items-center gap-2 text-[var(--ide-text-dim)] text-xs font-mono no-drag">
        <span className="text-[var(--ide-accent)] font-bold">SOVEREIGN OS</span>
        <span className="text-[10px]">v2026.2</span>
      </div>
      
      <div className="flex-1 flex items-center justify-center gap-4 text-xs text-[var(--ide-text-dim)] font-mono">
        <div className="flex items-center gap-1">
          <Cpu className="w-3 h-3" />
          <span>{cpuTemp}°C</span>
        </div>
        <div className="flex items-center gap-1">
          <HardDrive className="w-3 h-3" />
          <span>{memory}GB</span>
        </div>
        <div className="flex items-center gap-1">
          <Activity className="w-3 h-3" />
          <span>28 workers</span>
        </div>
      </div>
      
      <div className="flex items-center gap-3 text-xs text-[var(--ide-text-dim)] font-mono no-drag">
        <span>{time}</span>
        <div className="flex items-center gap-1">
          <Minimize className="w-3 h-3 cursor-pointer hover:text-[var(--ide-text-bright)]" />
          <Maximize className="w-3 h-3 cursor-pointer hover:text-[var(--ide-text-bright)]" />
          <X className="w-3 h-3 cursor-pointer hover:text-red-500" />
        </div>
      </div>
    </div>
  );
}
