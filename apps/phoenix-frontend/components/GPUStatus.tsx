'use client';

import { useState, useEffect } from 'react';

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8002';
const API_KEY = process.env.NEXT_PUBLIC_API_KEY || 'rez-hive-admin-key-2026';

export default function GPUStatus() {
  const [gpu, setGpu] = useState<{ has_gpu: boolean; name?: string; used_vram_gb?: number; total_vram_gb?: number } | null>(null);

  useEffect(() => {
    const fetchGPU = async () => {
      try {
        const res = await fetch(`${API_BASE}/health`, { headers: { 'Authorization': `Bearer ${API_KEY}` } });
        const data = await res.json();
        if (data.gpu) setGpu({ has_gpu: true, name: data.gpu, used_vram_gb: 0.5, total_vram_gb: 12.0 });
        else setGpu({ has_gpu: false });
      } catch (error) {}
    };
    fetchGPU();
    const interval = setInterval(fetchGPU, 10000);
    return () => clearInterval(interval);
  }, []);

  if (!gpu?.has_gpu) return <div className="bg-black/30 rounded-xl p-4 text-gray-400">GPU: Not detected</div>;

  const percent = gpu.used_vram_gb && gpu.total_vram_gb ? (gpu.used_vram_gb / gpu.total_vram_gb) * 100 : 0;

  return (
    <div className="bg-black/30 backdrop-blur-xl border border-[#7dcfff]/10 rounded-xl p-4">
      <div className="flex justify-between mb-2">
        <span className="text-sm font-mono text-white">GPU: {gpu.name}</span>
        <span className="text-xs text-gray-400">{Math.round(percent)}%</span>
      </div>
      <div className="w-full h-1.5 bg-white/10 rounded-full overflow-hidden">
        <div className="h-full bg-gradient-to-r from-[#7dcfff] to-[#9B72CB] rounded-full" style={{ width: `${percent}%` }} />
      </div>
      <div className="flex justify-between mt-2 text-[10px] text-gray-400">
        <span>Used: {gpu.used_vram_gb?.toFixed(1)}GB</span>
        <span>Total: {gpu.total_vram_gb?.toFixed(1)}GB</span>
      </div>
    </div>
  );
}
