"use client";
import React, { useState, useEffect } from 'react';
import { Cpu, HardDrive, Wifi, Activity, RefreshCw } from 'lucide-react';

interface SystemStats {
  cpu: { percent: number };
  memory: { percent: number };
  disk: { percent: number };
  gpu: { available: boolean; name?: string; load?: number; temp?: number };
}

interface PCManagerWidgetProps {
  onAction: (cmd: string) => void;
}

const PCManagerWidget: React.FC<PCManagerWidgetProps> = ({ onAction }) => {
  const [stats, setStats] = useState<SystemStats | null>(null);
  const [loading, setLoading] = useState(true);

  const fetchStats = async () => {
    setLoading(true);
    try {
      const res = await fetch('/api/system/snapshot');
      const data = await res.json();
      setStats(data);
    } catch {
      setStats({
        cpu: { percent: 25 },
        memory: { percent: 50 },
        disk: { percent: 60 },
        gpu: { available: false }
      });
    }
    setLoading(false);
  };

  useEffect(() => { 
    fetchStats(); 
    const i = setInterval(fetchStats, 3000); 
    return () => clearInterval(i); 
  }, []);

  if (!stats) return <div className="p-4 text-white/50">Loading...</div>;

  return (
    <div className="bg-black/30 border border-white/10 rounded-xl p-4 space-y-4">
      <div className="flex justify-between items-center mb-2">
        <h3 className="text-sm font-bold text-white/80">PC COMMAND CENTER</h3>
        <button onClick={fetchStats} className="p-1 hover:bg-white/10 rounded">
          <RefreshCw className={`w-4 h-4 text-white/60 ${loading ? 'animate-spin' : ''}`} />
        </button>
      </div>

      <div className="grid grid-cols-4 gap-2 text-center text-xs">
        <div>
          <div className="text-white/40">CPU</div>
          <div className="text-lg font-bold text-cyan-400">{stats.cpu.percent}%</div>
        </div>
        <div>
          <div className="text-white/40">RAM</div>
          <div className="text-lg font-bold text-purple-400">{stats.memory.percent}%</div>
        </div>
        <div>
          <div className="text-white/40">DISK</div>
          <div className="text-lg font-bold text-emerald-400">{stats.disk.percent}%</div>
        </div>
        <div>
          <div className="text-white/40">GPU</div>
          {stats.gpu.available ? (
             <div className="text-lg font-bold text-amber-400">{stats.gpu.load}%</div>
          ) : (
             <div className="text-lg font-bold text-white/20">N/A</div>
          )}
        </div>
      </div>

      <div className="grid grid-cols-2 gap-2 pt-2 border-t border-white/10">
        <button 
          onClick={() => onAction('Check system health')}
          className="flex items-center gap-2 p-2 rounded-lg bg-white/5 hover:bg-white/10 text-xs text-white/80 transition-colors"
        >
          <Activity className="w-3 h-3" /> System Health
        </button>
        
        <button 
          onClick={() => onAction('Deep search: Latest AI news 2024')}
          className="flex items-center gap-2 p-2 rounded-lg bg-white/5 hover:bg-white/10 text-xs text-white/80 transition-colors"
        >
          <RefreshCw className="w-3 h-3" /> AI News
        </button>
      </div>
    </div>
  );
};

// Export as default
export default PCManagerWidget;
