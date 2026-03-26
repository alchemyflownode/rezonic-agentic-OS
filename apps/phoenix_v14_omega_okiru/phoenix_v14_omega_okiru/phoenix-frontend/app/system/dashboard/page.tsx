// app/system/dashboard/page.tsx
'use client';

import React, { useState, useEffect } from 'react';
import { Zap, Activity, ShieldCheck, Cpu, Database, Lock } from 'lucide-react';

export default function SystemDashboardPage() {
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Fetch system stats
    fetchSystemStats();
  }, []);

  const fetchSystemStats = async () => {
    try {
      const response = await fetch('http://localhost:8002/health');
      if (response.ok) {
        const data = await response.json();
        setStats(data);
      }
    } catch (err) {
      console.error('Failed to fetch stats:', err);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="text-center">
          <div className="w-12 h-12 border-2 border-[#7dcfff] border-t-transparent rounded-full animate-spin mx-auto mb-4" />
          <p className="text-[#565f89] font-mono">Loading system dashboard...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="p-8">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-2xl font-bold text-[#c0caf5] flex items-center gap-3">
            <Zap className="w-8 h-8 text-[#7dcfff]" />
            System Dashboard
          </h1>
          <p className="text-[#565f89] mt-2">Sovereign AI Kernel Status</p>
        </div>

        {/* Stats Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
          <div className="bg-[#121217] border border-white/[0.05] rounded-xl p-4">
            <div className="flex items-center justify-between mb-2">
              <span className="text-[#565f89] text-sm">Status</span>
              <div className={`w-2 h-2 rounded-full ${stats?.status === 'ONLINE' ? 'bg-[#9ece6a] animate-pulse' : 'bg-[#f7768e]'}`} />
            </div>
            <div className="text-2xl font-bold text-[#c0caf5]">{stats?.status || 'OFFLINE'}</div>
          </div>

          <div className="bg-[#121217] border border-white/[0.05] rounded-xl p-4">
            <div className="flex items-center gap-2 mb-2">
              <Cpu className="w-4 h-4 text-[#7dcfff]" />
              <span className="text-[#565f89] text-sm">Workers</span>
            </div>
            <div className="text-2xl font-bold text-[#c0caf5]">{stats?.workers || 0}</div>
          </div>

          <div className="bg-[#121217] border border-white/[0.05] rounded-xl p-4">
            <div className="flex items-center gap-2 mb-2">
              <Database className="w-4 h-4 text-[#9ece6a]" />
              <span className="text-[#565f89] text-sm">Memory</span>
            </div>
            <div className="text-2xl font-bold text-[#c0caf5]">{stats?.memory_entries?.toLocaleString() || 0}</div>
          </div>

          <div className="bg-[#121217] border border-white/[0.05] rounded-xl p-4">
            <div className="flex items-center gap-2 mb-2">
              <Lock className="w-4 h-4 text-[#7dcfff]" />
              <span className="text-[#565f89] text-sm">Drift Chain</span>
            </div>
            <div className="text-2xl font-bold text-[#c0caf5]">{stats?.drift_chain || 0}</div>
          </div>
        </div>

        {/* System Info */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div className="bg-[#121217] border border-white/[0.05] rounded-xl p-6">
            <h2 className="text-lg font-bold text-[#c0caf5] mb-4 flex items-center gap-2">
              <Activity className="w-5 h-5 text-[#7dcfff]" />
              System Information
            </h2>
            <div className="space-y-3">
              <div className="flex justify-between py-2 border-b border-white/[0.05]">
                <span className="text-[#565f89]">Version</span>
                <span className="text-[#c0caf5] font-mono">{stats?.version || 'N/A'}</span>
              </div>
              <div className="flex justify-between py-2 border-b border-white/[0.05]">
                <span className="text-[#565f89]">Uptime</span>
                <span className="text-[#c0caf5] font-mono">{stats?.uptime ? formatUptime(stats.uptime) : 'N/A'}</span>
              </div>
              <div className="flex justify-between py-2 border-b border-white/[0.05]">
                <span className="text-[#565f89]">GPU</span>
                <span className="text-[#c0caf5] font-mono">{stats?.gpu || 'None'}</span>
              </div>
              <div className="flex justify-between py-2">
                <span className="text-[#565f89]">Consciousness</span>
                <span className="text-[#7dcfff] font-bold">{stats?.consciousness || 0}/10</span>
              </div>
            </div>
          </div>

          <div className="bg-[#121217] border border-white/[0.05] rounded-xl p-6">
            <h2 className="text-lg font-bold text-[#c0caf5] mb-4 flex items-center gap-2">
              <ShieldCheck className="w-5 h-5 text-[#9ece6a]" />
              Constitutional Status
            </h2>
            <div className="space-y-3">
              <div className="flex justify-between py-2 border-b border-white/[0.05]">
                <span className="text-[#565f89]">SCE Protocol</span>
                <span className="text-[#9ece6a]">ACTIVE</span>
              </div>
              <div className="flex justify-between py-2 border-b border-white/[0.05]">
                <span className="text-[#565f89]">Integrity Score</span>
                <span className="text-[#7dcfff]">98.2%</span>
              </div>
              <div className="mt-4">
                <div className="w-full h-2 bg-white/[0.05] rounded-full overflow-hidden">
                  <div className="w-[98%] h-full bg-[#7dcfff] rounded-full" />
                </div>
                <p className="text-right text-xs text-[#565f89] mt-1">98.2% Integrity</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

function formatUptime(seconds: number) {
  const hours = Math.floor(seconds / 3600);
  const minutes = Math.floor((seconds % 3600) / 60);
  const secs = Math.floor(seconds % 60);
  return `${hours}h ${minutes}m ${secs}s`;
}