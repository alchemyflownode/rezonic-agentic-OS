"use client";
import { useState, useEffect } from 'react';
export function SystemHealthOverlay({ show }: { show: boolean }) {
  const [health, setHealth] = useState(null);
  useEffect(() => {
    if (!show) return;
    const fetchHealth = async () => { const res = await fetch('/api/frontend/health'); const data = await res.json(); setHealth(data.health); };
    fetchHealth();
    const interval = setInterval(fetchHealth, 5000);
    return () => clearInterval(interval);
  }, [show]);
  if (!show || !health) return null;
  return (
    <div className="fixed bottom-4 right-4 text-xs bg-black/90 text-green-400 p-3 rounded-lg font-mono z-50 border border-green-500/30">
      <div className="font-bold mb-2">⚙️ SYSTEM HEALTH</div>
      <div>CPU: {health.cpu}%</div>
      <div>MEM: {health.memory}%</div>
      <div>DSK: {health.disk}%</div>
      <div>Workers: {health.workers?.healthy}/{health.workers?.total}</div>
      <div className="text-[8px] mt-2 opacity-50">Uptime: {Math.round(health.uptime / 60)}m</div>
    </div>
  );
}
