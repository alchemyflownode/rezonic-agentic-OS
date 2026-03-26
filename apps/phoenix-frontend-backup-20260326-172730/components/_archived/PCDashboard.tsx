export default function PCDashboard({ stats }: { stats: any }) {
  return (
    <div className="space-y-2">
      <div className="grid grid-cols-2 gap-2 text-[10px]">
        <div className="bg-white/5 p-2 rounded">
          <div className="text-white/40">CPU</div>
          <div className="text-cyan-400 font-mono">{stats?.cpu?.percent || 0}%</div>
        </div>
        <div className="bg-white/5 p-2 rounded">
          <div className="text-white/40">RAM</div>
          <div className="text-purple-400 font-mono">{stats?.memory?.percent || 0}%</div>
        </div>
      </div>
    </div>
  );
}
