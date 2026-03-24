'use client';

import React, { useState, useEffect } from 'react';
import { Cpu, Activity, CheckCircle, XCircle, RefreshCw } from 'lucide-react';

export default function SystemWorkersPage() {
  const [workers, setWorkers] = useState<string[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchWorkers();
    const interval = setInterval(fetchWorkers, 10000);
    return () => clearInterval(interval);
  }, []);

  const fetchWorkers = async () => {
    try {
      const response = await fetch('http://localhost:8002/workers/list');
      if (response.ok) {
        const data = await response.json();
        setWorkers(data.loaded || []);
      }
    } catch (err) {
      console.error('Failed to fetch workers:', err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#050505] p-8">
      <div className="max-w-7xl mx-auto">
        <div className="mb-8">
          <h1 className="text-2xl font-bold text-white flex items-center gap-3">
            <Cpu className="w-8 h-8 text-[#00E5FF]" />
            Worker Registry
          </h1>
          <p className="text-zinc-500 mt-2">{workers.length} active workers</p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
          {workers.map((worker, i) => (
            <div key={i} className="bg-[#0a0a0c] border border-white/5 rounded-lg p-4 hover:border-[#00E5FF]/30 transition">
              <div className="flex items-center justify-between mb-2">
                <span className="text-white font-mono text-sm">{worker}</span>
                <CheckCircle className="w-4 h-4 text-green-500" />
              </div>
              <div className="text-xs text-zinc-500 flex items-center gap-1">
                <Activity className="w-3 h-3" />
                STABLE
              </div>
            </div>
          ))}
        </div>

        <button
          onClick={fetchWorkers}
          className="mt-6 flex items-center gap-2 px-4 py-2 bg-white/5 border border-white/10 rounded-lg text-zinc-400 hover:text-white transition mx-auto"
        >
          <RefreshCw className="w-4 h-4" />
          Refresh
        </button>
      </div>
    </div>
  );
}
