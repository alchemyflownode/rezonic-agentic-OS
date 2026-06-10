'use client';

interface SystemMetricsProps {
  stats: {
    cpu?: { percent: number };
    memory?: { percent: number };
    disk?: { percent: number };
    gpu?: { load: number };
  };
}

export function SystemMetrics({ stats }: SystemMetricsProps) {
  return (
    <div className="grid grid-cols-2 gap-2 text-[10px]">
      <div className="bg-white/5 p-2 rounded flex justify-between">
        <span className="text-white/50">CPU</span>
        <span className="text-cyan-400 font-mono">{stats?.cpu?.percent || 0}%</span>
      </div>
      <div className="bg-white/5 p-2 rounded flex justify-between">
        <span className="text-white/50">RAM</span>
        <span className="text-purple-400 font-mono">{stats?.memory?.percent || 0}%</span>
      </div>
      <div className="bg-white/5 p-2 rounded flex justify-between">
        <span className="text-white/50">DISK</span>
        <span className="text-emerald-400 font-mono">{stats?.disk?.percent || 0}%</span>
      </div>
      <div className="bg-white/5 p-2 rounded flex justify-between">
        <span className="text-white/50">GPU</span>
        <span className="text-amber-400 font-mono">{stats?.gpu?.load || 0}%</span>
      </div>
    </div>
  );
}
