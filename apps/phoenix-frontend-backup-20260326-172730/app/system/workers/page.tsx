// app/system/workers/page.tsx
'use client';

import React, { useState, useEffect } from 'react';
import { Cpu, Activity, CheckCircle, XCircle, RefreshCw, Search, Filter } from 'lucide-react';
import { usePhoenix, useAutoRefresh } from '@/hooks/usePhoenix';

export default function SystemWorkersPage() {
  const { workers, fetchWorkers, isLoading, telemetry } = usePhoenix();
  const [searchTerm, setSearchTerm] = useState('');
  const [filter, setFilter] = useState<'all' | 'active' | 'inactive'>('all');
  
  useAutoRefresh(10000);

  useEffect(() => {
    fetchWorkers();
  }, []);

  const filteredWorkers = workers.filter(worker => {
    const matchesSearch = worker.name.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesFilter = filter === 'all' || 
      (filter === 'active' && worker.status === 'active') ||
      (filter === 'inactive' && worker.status !== 'active');
    return matchesSearch && matchesFilter;
  });

  const activeCount = workers.filter(w => w.status === 'active').length;
  const inactiveCount = workers.filter(w => w.status !== 'active').length;

  return (
    <div className="min-h-screen bg-gradient-to-br from-[#0a0a0c] via-[#050505] to-[#0a0a0c] p-8">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-bold text-white flex items-center gap-3">
                <Cpu className="w-8 h-8 text-[#7dcfff]" />
                Worker Registry
              </h1>
              <p className="text-zinc-500 mt-2">
                {workers.length} total workers • {activeCount} active • {inactiveCount} inactive
              </p>
            </div>
            <div className="flex items-center gap-2">
              <div className="flex items-center gap-1 bg-black/30 rounded-lg p-1">
                <button
                  onClick={() => setFilter('all')}
                  className={`px-3 py-1.5 rounded-md text-xs transition ${
                    filter === 'all' ? 'bg-[#7dcfff]/20 text-[#7dcfff]' : 'text-zinc-500 hover:text-white'
                  }`}
                >
                  All
                </button>
                <button
                  onClick={() => setFilter('active')}
                  className={`px-3 py-1.5 rounded-md text-xs transition ${
                    filter === 'active' ? 'bg-[#9ece6a]/20 text-[#9ece6a]' : 'text-zinc-500 hover:text-white'
                  }`}
                >
                  Active
                </button>
                <button
                  onClick={() => setFilter('inactive')}
                  className={`px-3 py-1.5 rounded-md text-xs transition ${
                    filter === 'inactive' ? 'bg-[#f7768e]/20 text-[#f7768e]' : 'text-zinc-500 hover:text-white'
                  }`}
                >
                  Inactive
                </button>
              </div>
              <button
                onClick={fetchWorkers}
                disabled={isLoading}
                className="p-2 bg-white/5 border border-white/10 rounded-lg text-zinc-400 hover:text-white transition disabled:opacity-50"
              >
                <RefreshCw className={`w-4 h-4 ${isLoading ? 'animate-spin' : ''}`} />
              </button>
            </div>
          </div>
          
          {/* Search Bar */}
          <div className="mt-4 relative">
            <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-zinc-500" />
            <input
              type="text"
              placeholder="Search workers..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full bg-black/30 border border-[#7dcfff]/10 rounded-xl pl-10 pr-4 py-2.5 text-sm text-white placeholder:text-zinc-500 outline-none focus:border-[#7dcfff]/30 transition"
            />
          </div>
        </div>

        {/* Workers Grid */}
        {isLoading && workers.length === 0 ? (
          <div className="flex items-center justify-center h-64">
            <div className="animate-spin rounded-full h-8 w-8 border-2 border-[#7dcfff] border-t-transparent" />
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-3">
            {filteredWorkers.map((worker, i) => (
              <div
                key={i}
                className="bg-[#0a0a0c] border border-white/5 rounded-lg p-4 hover:border-[#7dcfff]/30 transition group"
              >
                <div className="flex items-center justify-between mb-2">
                  <span className="text-white font-mono text-sm truncate flex-1">{worker.name}</span>
                  {worker.status === 'active' ? (
                    <CheckCircle className="w-4 h-4 text-[#9ece6a] flex-shrink-0" />
                  ) : (
                    <XCircle className="w-4 h-4 text-[#f7768e] flex-shrink-0" />
                  )}
                </div>
                <div className="flex items-center justify-between text-xs">
                  <div className="flex items-center gap-1 text-zinc-500">
                    <Activity className="w-3 h-3" />
                    <span>{worker.status === 'active' ? 'ACTIVE' : 'INACTIVE'}</span>
                  </div>
                  <div className="text-[#7dcfff] font-mono">
                    {worker.drift_score?.toFixed(1) || 98.5}%
                  </div>
                </div>
                {worker.capabilities?.length > 0 && (
                  <div className="mt-2 flex flex-wrap gap-1">
                    {worker.capabilities.slice(0, 2).map((cap, idx) => (
                      <span key={idx} className="text-[8px] px-1.5 py-0.5 bg-white/5 rounded text-zinc-400">
                        {cap}
                      </span>
                    ))}
                    {worker.capabilities.length > 2 && (
                      <span className="text-[8px] px-1.5 py-0.5 bg-white/5 rounded text-zinc-400">
                        +{worker.capabilities.length - 2}
                      </span>
                    )}
                  </div>
                )}
              </div>
            ))}
          </div>
        )}

        {filteredWorkers.length === 0 && !isLoading && (
          <div className="text-center py-12">
            <Cpu className="w-12 h-12 text-zinc-600 mx-auto mb-3" />
            <p className="text-zinc-500">No workers found matching your criteria</p>
          </div>
        )}
      </div>
    </div>
  );
}