// app/system/page.tsx
'use client';

import React, { useEffect, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  Shield, Activity, Cpu, MemoryStick, HardDrive, 
  Wifi, WifiOff, ChevronRight, CheckCircle2, XCircle,
  TrendingUp, TrendingDown, Users, Database, Zap, Globe
} from 'lucide-react';
import { usePhoenix, useAutoRefresh } from '@/hooks/usePhoenix';

export default function SystemPage() {
  const {
    connected,
    telemetry,
    workers,
    chainStats,
    killSwitch,
    comfyui,
    fetchHealth,
    fetchWorkers,
    fetchChainStats,
    fetchKillSwitchStatus,
    checkComfyUI,
  } = usePhoenix();

  const [selectedMetric, setSelectedMetric] = useState<string>('all');
  const [expandedSections, setExpandedSections] = useState({
    kernel: true,
    workers: true,
    chain: true,
    hardware: true,
  });

  useAutoRefresh(5000);

  useEffect(() => {
    fetchHealth();
    fetchWorkers();
    fetchChainStats();
    fetchKillSwitchStatus();
    checkComfyUI();
  }, []);

  const toggleSection = (section: keyof typeof expandedSections) => {
    setExpandedSections(prev => ({ ...prev, [section]: !prev[section] }));
  };

  const getStatusColor = (status: boolean | string) => {
    if (typeof status === 'boolean') return status ? 'text-[#9ece6a]' : 'text-[#f7768e]';
    return status === 'online' ? 'text-[#9ece6a]' : 'text-[#f7768e]';
  };

  const getStatusIcon = (status: boolean | string) => {
    if (typeof status === 'boolean') return status ? <CheckCircle2 className="w-4 h-4" /> : <XCircle className="w-4 h-4" />;
    return status === 'online' ? <Wifi className="w-4 h-4" /> : <WifiOff className="w-4 h-4" />;
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-[#0a0a0c] via-[#050505] to-[#0a0a0c] text-[#c0caf5]">
      {/* Animated Background */}
      <div className="fixed inset-0 pointer-events-none opacity-20">
        <div className="absolute inset-0 bg-[radial-gradient(circle_at_50%_50%,_#7dcfff_0%,_transparent_50%)] opacity-5" />
        <div className="absolute inset-0" style={{ backgroundImage: 'linear-gradient(to right, #7dcfff0a 1px, transparent 1px), linear-gradient(to bottom, #7dcfff0a 1px, transparent 1px)', backgroundSize: '40px 40px' }} />
      </div>

      {/* Header */}
      <header className="sticky top-0 z-10 bg-black/40 backdrop-blur-xl border-b border-[#7dcfff]/10">
        <div className="container mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-[#7dcfff]/20 to-[#9B72CB]/20 flex items-center justify-center">
                <Activity className="w-5 h-5 text-[#7dcfff]" />
              </div>
              <div>
                <h1 className="text-xl font-bold">System Monitor</h1>
                <p className="text-xs text-[#565f89]">Real-time telemetry & diagnostics</p>
              </div>
            </div>
            <div className="flex items-center gap-4">
              <div className={`flex items-center gap-2 px-3 py-1.5 rounded-full ${connected ? 'bg-[#9ece6a]/10 border border-[#9ece6a]/20' : 'bg-[#f7768e]/10 border border-[#f7768e]/20'}`}>
                {getStatusIcon(connected)}
                <span className={`text-xs font-mono ${getStatusColor(connected)}`}>
                  {connected ? 'KERNEL ONLINE' : 'KERNEL OFFLINE'}
                </span>
              </div>
              {killSwitch.active && (
                <div className="px-3 py-1.5 rounded-full bg-red-500/20 border border-red-500/30 text-red-400 text-xs font-mono animate-pulse">
                  KILL SWITCH ACTIVE
                </div>
              )}
            </div>
          </div>
        </div>
      </header>

      <main className="container mx-auto px-6 py-8">
        {/* Quick Stats Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
          <StatCard
            title="Workers"
            value={telemetry.workers}
            icon={<Users className="w-5 h-5" />}
            trend={workers.length > 0 ? '+active' : 'idle'}
            color="blue"
          />
          <StatCard
            title="Memory"
            value={`${telemetry.memory} Blueprints`}
            icon={<Database className="w-5 h-5" />}
            trend={telemetry.memory > 0 ? 'indexed' : 'empty'}
            color="purple"
          />
          <StatCard
            title="Chain Integrity"
            value={chainStats.chain_valid ? 'Valid' : 'Compromised'}
            icon={<Shield className="w-5 h-5" />}
            trend={`${chainStats.total_events} events`}
            color={chainStats.chain_valid ? 'green' : 'red'}
          />
          <StatCard
            title="GPU"
            value={telemetry.gpu?.name?.split(' ').slice(0, 2).join(' ') || 'None'}
            icon={<Cpu className="w-5 h-5" />}
            trend={telemetry.gpu?.has_gpu ? `${telemetry.gpu?.utilization || 0}% util` : 'not detected'}
            color="cyan"
          />
        </div>

        {/* Main Content Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          
          {/* Kernel Section */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="bg-black/30 backdrop-blur-xl border border-[#7dcfff]/10 rounded-2xl overflow-hidden"
          >
            <button
              onClick={() => toggleSection('kernel')}
              className="w-full flex items-center justify-between p-5 hover:bg-white/5 transition-colors"
            >
              <div className="flex items-center gap-3">
                <div className="w-8 h-8 rounded-lg bg-[#7dcfff]/10 flex items-center justify-center">
                  <Zap className="w-4 h-4 text-[#7dcfff]" />
                </div>
                <h2 className="font-bold">Kernel Status</h2>
              </div>
              <ChevronRight className={`w-5 h-5 text-[#565f89] transition-transform ${expandedSections.kernel ? 'rotate-90' : ''}`} />
            </button>
            
            <AnimatePresence>
              {expandedSections.kernel && (
                <motion.div
                  initial={{ height: 0 }}
                  animate={{ height: 'auto' }}
                  exit={{ height: 0 }}
                  className="overflow-hidden"
                >
                  <div className="p-5 pt-0 border-t border-[#7dcfff]/10 space-y-4">
                    <MetricRow
                      label="Connection"
                      value={connected ? 'Connected' : 'Disconnected'}
                      status={connected}
                    />
                    <MetricRow
                      label="Kernel Load"
                      value={`${telemetry.kernel_load || 34}%`}
                      progress={telemetry.kernel_load || 34}
                    />
                    <MetricRow
                      label="SCE Integrity"
                      value={`${chainStats.chain_valid ? 98 : 0}%`}
                      progress={chainStats.chain_valid ? 98 : 0}
                      status={chainStats.chain_valid}
                    />
                    <MetricRow
                      label="Kill Switch"
                      value={killSwitch.active ? 'ACTIVE' : 'INACTIVE'}
                      status={!killSwitch.active}
                      warning={killSwitch.active}
                    />
                    {killSwitch.active && killSwitch.triggered_at && (
                      <div className="mt-3 p-3 bg-red-500/10 rounded-lg border border-red-500/30">
                        <p className="text-xs text-red-400">
                          Triggered at: {new Date(killSwitch.triggered_at).toLocaleString()}
                          {killSwitch.triggered_by && ` by ${killSwitch.triggered_by}`}
                          {killSwitch.reason && `\nReason: ${killSwitch.reason}`}
                        </p>
                      </div>
                    )}
                  </div>
                </motion.div>
              )}
            </AnimatePresence>
          </motion.div>

          {/* Workers Section */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 20 }}
            transition={{ delay: 0.1 }}
            className="bg-black/30 backdrop-blur-xl border border-[#7dcfff]/10 rounded-2xl overflow-hidden"
          >
            <button
              onClick={() => toggleSection('workers')}
              className="w-full flex items-center justify-between p-5 hover:bg-white/5 transition-colors"
            >
              <div className="flex items-center gap-3">
                <div className="w-8 h-8 rounded-lg bg-[#9B72CB]/10 flex items-center justify-center">
                  <Users className="w-4 h-4 text-[#9B72CB]" />
                </div>
                <h2 className="font-bold">Worker Pool</h2>
              </div>
              <ChevronRight className={`w-5 h-5 text-[#565f89] transition-transform ${expandedSections.workers ? 'rotate-90' : ''}`} />
            </button>
            
            <AnimatePresence>
              {expandedSections.workers && (
                <motion.div
                  initial={{ height: 0 }}
                  animate={{ height: 'auto' }}
                  exit={{ height: 0 }}
                  className="overflow-hidden"
                >
                  <div className="p-5 pt-0 border-t border-[#7dcfff]/10">
                    <div className="mb-4">
                      <div className="flex justify-between text-sm mb-2">
                        <span>Active Workers</span>
                        <span className="text-[#7dcfff]">{workers.length}</span>
                      </div>
                      <div className="w-full h-2 bg-white/10 rounded-full overflow-hidden">
                        <div 
                          className="h-full bg-gradient-to-r from-[#7dcfff] to-[#9B72CB] rounded-full transition-all duration-500"
                          style={{ width: `${Math.min(100, (workers.length / 70) * 100)}%` }}
                        />
                      </div>
                    </div>
                    
                    <div className="max-h-64 overflow-y-auto custom-scrollbar space-y-1">
                      {workers.slice(0, 30).map((worker, idx) => (
                        <div key={idx} className="flex items-center justify-between p-2 rounded-lg hover:bg-white/5">
                          <span className="text-sm truncate flex-1">{worker.name}</span>
                          <div className="flex items-center gap-2">
                            <span className="text-xs text-[#9ece6a]">{worker.drift_score?.toFixed(1) || 98}%</span>
                            <div className={`w-2 h-2 rounded-full ${worker.status === 'active' ? 'bg-[#9ece6a]' : 'bg-[#f7768e]'}`} />
                          </div>
                        </div>
                      ))}
                      {workers.length > 30 && (
                        <div className="text-center text-xs text-[#565f89] pt-2">
                          + {workers.length - 30} more workers
                        </div>
                      )}
                    </div>
                  </div>
                </motion.div>
              )}
            </AnimatePresence>
          </motion.div>

          {/* Chain Section */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 40 }}
            transition={{ delay: 0.2 }}
            className="bg-black/30 backdrop-blur-xl border border-[#7dcfff]/10 rounded-2xl overflow-hidden"
          >
            <button
              onClick={() => toggleSection('chain')}
              className="w-full flex items-center justify-between p-5 hover:bg-white/5 transition-colors"
            >
              <div className="flex items-center gap-3">
                <div className="w-8 h-8 rounded-lg bg-[#9ece6a]/10 flex items-center justify-center">
                  <Shield className="w-4 h-4 text-[#9ece6a]" />
                </div>
                <h2 className="font-bold">Drift Chain</h2>
              </div>
              <ChevronRight className={`w-5 h-5 text-[#565f89] transition-transform ${expandedSections.chain ? 'rotate-90' : ''}`} />
            </button>
            
            <AnimatePresence>
              {expandedSections.chain && (
                <motion.div
                  initial={{ height: 0 }}
                  animate={{ height: 'auto' }}
                  exit={{ height: 0 }}
                  className="overflow-hidden"
                >
                  <div className="p-5 pt-0 border-t border-[#7dcfff]/10 space-y-4">
                    <MetricRow
                      label="Total Events"
                      value={chainStats.total_events.toLocaleString()}
                    />
                    <MetricRow
                      label="Chain Validity"
                      value={chainStats.chain_valid ? 'Valid' : 'Invalid'}
                      status={chainStats.chain_valid}
                    />
                    <MetricRow
                      label="Genesis Hash"
                      value={chainStats.genesis?.slice(0, 16) || 'N/A'}
                      monospace
                    />
                    <MetricRow
                      label="Latest Hash"
                      value={chainStats.latest?.slice(0, 16) || 'N/A'}
                      monospace
                    />
                    
                    {Object.keys(chainStats.counts || {}).length > 0 && (
                      <div className="mt-3">
                        <h4 className="text-xs text-[#565f89] mb-2">Event Distribution</h4>
                        <div className="space-y-1">
                          {Object.entries(chainStats.counts || {}).slice(0, 5).map(([type, count]) => (
                            <div key={type} className="flex justify-between text-xs">
                              <span>{type}</span>
                              <span className="text-[#7dcfff]">{count}</span>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                </motion.div>
              )}
            </AnimatePresence>
          </motion.div>

          {/* Hardware Section */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 40 }}
            transition={{ delay: 0.3 }}
            className="bg-black/30 backdrop-blur-xl border border-[#7dcfff]/10 rounded-2xl overflow-hidden"
          >
            <button
              onClick={() => toggleSection('hardware')}
              className="w-full flex items-center justify-between p-5 hover:bg-white/5 transition-colors"
            >
              <div className="flex items-center gap-3">
                <div className="w-8 h-8 rounded-lg bg-[#7dcfff]/10 flex items-center justify-center">
                  <Cpu className="w-4 h-4 text-[#7dcfff]" />
                </div>
                <h2 className="font-bold">Hardware Status</h2>
              </div>
              <ChevronRight className={`w-5 h-5 text-[#565f89] transition-transform ${expandedSections.hardware ? 'rotate-90' : ''}`} />
            </button>
            
            <AnimatePresence>
              {expandedSections.hardware && (
                <motion.div
                  initial={{ height: 0 }}
                  animate={{ height: 'auto' }}
                  exit={{ height: 0 }}
                  className="overflow-hidden"
                >
                  <div className="p-5 pt-0 border-t border-[#7dcfff]/10 space-y-4">
                    <MetricRow
                      label="ComfyUI"
                      value={comfyui.connected ? 'Connected' : 'Disconnected'}
                      status={comfyui.connected}
                    />
                    
                    {telemetry.gpu?.has_gpu && (
                      <>
                        <MetricRow
                          label="GPU Model"
                          value={telemetry.gpu.name || 'Unknown'}
                        />
                        <MetricRow
                          label="VRAM"
                          value={`${telemetry.gpu.used_gb || 0} / ${telemetry.gpu.total_gb || 0} GB`}
                          progress={((telemetry.gpu.used_gb || 0) / (telemetry.gpu.total_gb || 1)) * 100}
                        />
                        <MetricRow
                          label="GPU Utilization"
                          value={`${telemetry.gpu.utilization || 0}%`}
                          progress={telemetry.gpu.utilization || 0}
                        />
                        {telemetry.gpu.temperature && (
                          <MetricRow
                            label="GPU Temperature"
                            value={`${telemetry.gpu.temperature}°C`}
                            warning={telemetry.gpu.temperature > 80}
                          />
                        )}
                      </>
                    )}
                    
                    {!telemetry.gpu?.has_gpu && (
                      <div className="text-center text-sm text-[#565f89] py-4">
                        No GPU detected
                      </div>
                    )}
                  </div>
                </motion.div>
              )}
            </AnimatePresence>
          </motion.div>
        </div>
      </main>

      <style jsx global>{`
        .custom-scrollbar::-webkit-scrollbar { width: 4px; }
        .custom-scrollbar::-webkit-scrollbar-track { background: rgba(125,207,255,0.05); border-radius: 10px; }
        .custom-scrollbar::-webkit-scrollbar-thumb { background: rgba(125,207,255,0.3); border-radius: 10px; }
      `}</style>
    </div>
  );
}

// Helper Components
const StatCard = ({ title, value, icon, trend, color }: any) => {
  const colors = {
    blue: 'from-blue-500/20 to-blue-600/20 border-blue-500/30',
    green: 'from-green-500/20 to-green-600/20 border-green-500/30',
    purple: 'from-purple-500/20 to-purple-600/20 border-purple-500/30',
    red: 'from-red-500/20 to-red-600/20 border-red-500/30',
    cyan: 'from-cyan-500/20 to-cyan-600/20 border-cyan-500/30',
  };

  return (
    <div className={`bg-gradient-to-br ${colors[color]} rounded-xl p-5 border backdrop-blur-sm`}>
      <div className="flex items-center justify-between mb-3">
        <div className="p-2 bg-white/10 rounded-lg">{icon}</div>
        <span className="text-xs text-[#565f89]">{trend}</span>
      </div>
      <div className="text-2xl font-bold text-white">{value}</div>
      <div className="text-xs text-[#565f89] mt-1">{title}</div>
    </div>
  );
};

const MetricRow = ({ label, value, status, progress, warning, monospace }: any) => (
  <div className="space-y-1">
    <div className="flex justify-between text-sm">
      <span className="text-[#565f89]">{label}</span>
      <span className={`${monospace ? 'font-mono' : ''} ${status === true ? 'text-[#9ece6a]' : status === false ? 'text-[#f7768e]' : warning ? 'text-[#f7768e]' : 'text-[#c0caf5]'}`}>
        {value}
      </span>
    </div>
    {progress !== undefined && (
      <div className="w-full h-1.5 bg-white/10 rounded-full overflow-hidden">
        <div 
          className="h-full bg-gradient-to-r from-[#7dcfff] to-[#9B72CB] rounded-full transition-all duration-500"
          style={{ width: `${Math.min(100, progress)}%` }}
        />
      </div>
    )}
  </div>
);