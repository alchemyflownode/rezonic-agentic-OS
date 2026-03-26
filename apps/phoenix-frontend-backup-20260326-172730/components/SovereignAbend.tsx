import React from 'react';
import { Terminal, AlertTriangle, Cpu, HardDrive, Activity } from 'lucide-react';

interface AbendProps {
  error: {
    code: string;
    message: string;
    state: {
      instructionPointer: number;
      workingStorage: Record<string, any>;
      activeDivision: string;
      timestamp?: string;
    };
  };
  onRetry?: () => void;
}

export function SovereignAbend({ error, onRetry }: AbendProps) {
  return (
    <div className="bg-gradient-to-br from-red-950/30 to-black border-2 border-red-500/40 rounded-xl p-6 font-mono text-xs overflow-hidden relative group">
      {/* Animated scanline effect */}
      <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-transparent via-red-500/50 to-transparent animate-scan" />
      
      {/* Header */}
      <div className="flex items-center gap-3 mb-4 border-b border-red-500/30 pb-4">
        <div className="relative">
          <AlertTriangle className="w-8 h-8 text-red-500 animate-pulse" />
          <div className="absolute -top-1 -right-1 w-2 h-2 bg-red-500 rounded-full animate-ping" />
        </div>
        <div>
          <div className="text-red-500 font-bold text-sm tracking-widest flex items-center gap-2">
            SYSTEM ABEND
            <span className="bg-red-500/20 px-2 py-0.5 rounded text-[10px] text-red-400">{error.code}</span>
          </div>
          <div className="text-red-400/60 text-[10px] mt-0.5">
            {new Date(error.state.timestamp || Date.now()).toLocaleString()} UTC
          </div>
        </div>
      </div>

      {/* Memory Dump Grid */}
      <div className="grid grid-cols-2 gap-6">
        {/* Left: WORKING-STORAGE */}
        <div className="space-y-3">
          <div className="flex items-center gap-2 text-red-400 border-b border-red-500/20 pb-1.5">
            <HardDrive className="w-3.5 h-3.5" /> 
            <span className="text-xs font-bold tracking-wider">WORKING-STORAGE</span>
            <span className="text-[8px] text-gray-600 ml-auto">HEX DUMP</span>
          </div>
          <div className="space-y-1.5 max-h-40 overflow-y-auto pr-1">
            {Object.entries(error.state.workingStorage).map(([key, val], idx) => (
              <div key={key} 
                   className="flex justify-between items-center bg-black/40 p-1.5 rounded border border-red-500/10 hover:border-red-500/30 transition-colors group/item">
                <span className="text-gray-500 text-[10px] font-mono">
                  {String(idx + 1).padStart(2, '0')} {key}:
                </span>
                <span className="text-red-300 font-mono truncate ml-2 max-w-[150px] group-hover/item:text-red-200">
                  "{String(val)}"
                </span>
              </div>
            ))}
          </div>
        </div>

        {/* Right: Register State */}
        <div className="space-y-3">
          <div className="flex items-center gap-2 text-red-400 border-b border-red-500/20 pb-1.5">
            <Cpu className="w-3.5 h-3.5" /> 
            <span className="text-xs font-bold tracking-wider">REGISTER STATE</span>
          </div>
          <div className="space-y-2">
            <div className="flex justify-between bg-black/40 p-2 rounded border border-red-500/10">
              <span className="text-gray-500 text-[10px]">IP (Program Counter):</span>
              <span className="text-white font-mono text-[11px]">
                0x{error.state.instructionPointer.toString(16).toUpperCase().padStart(4, '0')}
              </span>
            </div>
            <div className="flex justify-between bg-black/40 p-2 rounded border border-red-500/10">
              <span className="text-gray-500 text-[10px]">Active Division:</span>
              <span className="text-white font-mono text-[11px]">{error.state.activeDivision}</span>
            </div>
            <div className="flex justify-between bg-black/40 p-2 rounded border border-red-500/10">
              <span className="text-gray-500 text-[10px]">Stack Depth:</span>
              <span className="text-white font-mono text-[11px]">0x00{Object.keys(error.state.workingStorage).length}</span>
            </div>
          </div>

          {/* Live Activity Indicator */}
          <div className="mt-3 flex items-center gap-2 bg-red-500/5 p-2 rounded border border-red-500/20">
            <Activity className="w-3 h-3 text-red-400 animate-pulse" />
            <span className="text-[8px] text-red-400/70">CORE_DUMP_ACTIVE • ANALYZING</span>
          </div>
        </div>
      </div>

      {/* Error Message */}
      <div className="mt-4 bg-gradient-to-r from-red-500/10 via-red-500/5 to-transparent p-3 rounded border-l-2 border-red-500">
        <div className="text-red-400 mb-1 text-[10px] font-bold flex items-center gap-2">
          <Terminal className="w-3 h-3" />
          FAULT_LOG:
        </div>
        <div className="text-red-200/90 text-[11px] leading-relaxed font-mono pl-4 border-l border-red-500/30">
          "{error.message}"
        </div>
      </div>

      {/* Footer with Retry */}
      {onRetry && (
        <div className="mt-4 flex justify-end">
          <button
            onClick={onRetry}
            className="px-4 py-1.5 bg-red-500/10 hover:bg-red-500/20 border border-red-500/30 rounded text-red-400 text-[10px] font-bold transition-all hover:border-red-500/50 flex items-center gap-2"
          >
            <Terminal className="w-3 h-3" />
            RETRY_TRANSACTION
          </button>
        </div>
      )}

      {/* Decorative corner markers */}
      <div className="absolute top-2 left-2 w-2 h-2 border-t border-l border-red-500/50" />
      <div className="absolute top-2 right-2 w-2 h-2 border-t border-r border-red-500/50" />
      <div className="absolute bottom-2 left-2 w-2 h-2 border-b border-l border-red-500/50" />
      <div className="absolute bottom-2 right-2 w-2 h-2 border-b border-r border-red-500/50" />
    </div>
  );
}
