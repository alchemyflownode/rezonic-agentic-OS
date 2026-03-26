'use client';

import React from 'react';
import { motion } from 'framer-motion';
import { Cpu, Activity, AlertCircle, CheckCircle, Clock } from 'lucide-react';

interface WorkerInfo {
  name: string;
  path: string;
  loaded: number;
  module: string;
  metrics?: {
    calls: number;
    errors: number;
    avg_duration: number;
  };
}

interface WorkerMetricsPanelProps {
  workers: Record<string, WorkerInfo>;
}

export const WorkerMetricsPanel: React.FC<WorkerMetricsPanelProps> = ({ workers }) => {
  const workerList = Object.entries(workers);
  
  if (workerList.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-8 text-zinc-500">
        <Cpu className="w-8 h-8 mb-2 opacity-30" />
        <p className="text-[9px] font-mono">No workers loaded</p>
      </div>
    );
  }

  const totalCalls = workerList.reduce((sum, [_, w]) => sum + (w.metrics?.calls || 0), 0);
  const totalErrors = workerList.reduce((sum, [_, w]) => sum + (w.metrics?.errors || 0), 0);
  const avgDuration = workerList.length > 0 
    ? workerList.reduce((sum, [_, w]) => sum + (w.metrics?.avg_duration || 0), 0) / workerList.length 
    : 0;

  return (
    <div className="space-y-3">
      {/* Summary Stats */}
      <div className="grid grid-cols-3 gap-2">
        <div className="bg-black/30 p-2 rounded">
          <div className="flex items-center gap-1 text-[#00E5FF] mb-1">
            <Activity className="w-3 h-3" />
            <span className="text-[7px] font-mono">CALLS</span>
          </div>
          <span className="text-[11px] font-bold text-white">{totalCalls}</span>
        </div>
        <div className="bg-black/30 p-2 rounded">
          <div className="flex items-center gap-1 text-[#ff0055] mb-1">
            <AlertCircle className="w-3 h-3" />
            <span className="text-[7px] font-mono">ERRORS</span>
          </div>
          <span className="text-[11px] font-bold text-white">{totalErrors}</span>
        </div>
        <div className="bg-black/30 p-2 rounded">
          <div className="flex items-center gap-1 text-[#9B72CB] mb-1">
            <Clock className="w-3 h-3" />
            <span className="text-[7px] font-mono">AVG MS</span>
          </div>
          <span className="text-[11px] font-bold text-white">{avgDuration.toFixed(1)}</span>
        </div>
      </div>

      {/* Worker List */}
      <div className="max-h-48 overflow-y-auto custom-scrollbar space-y-1">
        {workerList.slice(0, 8).map(([name, info]) => (
          <motion.div
            key={name}
            initial={{ opacity: 0, x: -10 }}
            animate={{ opacity: 1, x: 0 }}
            className="bg-black/20 p-2 rounded-lg border border-white/5 hover:border-[#00E5FF]/20 transition-colors"
          >
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <div className="w-1.5 h-1.5 rounded-full bg-[#00E5FF]" />
                <span className="text-[9px] font-mono font-bold text-white truncate max-w-[100px]">
                  {name}
                </span>
              </div>
              <span className="text-[6px] px-1 py-0.5 rounded bg-[#00E5FF]/10 text-[#00E5FF] border border-[#00E5FF]/20">
                {info.module}
              </span>
            </div>
            {info.metrics && (
              <div className="grid grid-cols-3 gap-1 mt-1.5 text-[7px] font-mono">
                <div>
                  <span className="text-zinc-500">Calls:</span>
                  <span className="text-white ml-1">{info.metrics.calls}</span>
                </div>
                <div>
                  <span className="text-zinc-500">Err:</span>
                  <span className={info.metrics.errors > 0 ? 'text-[#ff0055]' : 'text-white'}>
                    {info.metrics.errors}
                  </span>
                </div>
                <div>
                  <span className="text-zinc-500">Avg:</span>
                  <span className="text-white">{info.metrics.avg_duration?.toFixed(1)}ms</span>
                </div>
              </div>
            )}
          </motion.div>
        ))}
        
        {workerList.length > 8 && (
          <div className="text-center text-[7px] font-mono text-zinc-500 pt-1">
            +{workerList.length - 8} more workers
          </div>
        )}
      </div>
    </div>
  );
};