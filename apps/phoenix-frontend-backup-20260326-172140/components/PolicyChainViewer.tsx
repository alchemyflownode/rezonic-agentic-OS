'use client';

import { motion } from 'framer-motion';

interface ChainStep {
  worker: string;
  status: 'pending' | 'active' | 'complete' | 'error';
}

interface PolicyChainViewerProps {
  chain?: string[]; // Made optional to prevent crashes if parent is fetching data
  activeStep?: number;
  drift?: number;
  isExecuting?: boolean;
  onClose?: () => void;
}

const workerIcons: Record<string, string> = {
  brain: '🧠',
  search: '👁️',
  code: '👐',
  files: '💾',
  system: '⚙️',
  photo: '📷',
  video: '🎬',
  style: '🎨',
  post: '📤',
  analytics: '📊'
};

const workerColors: Record<string, string> = {
  brain: '#00E5FF',
  search: '#10b981',
  code: '#B388FF',
  files: '#FF9800',
  system: '#FF4500',
  photo: '#FF6B6B',
  video: '#4ECDC4',
  style: '#A8E6CF',
  post: '#FFD93D',
  analytics: '#6C5CE7'
};

export default function PolicyChainViewer({
  chain =[], // Provide default empty array fallback
  activeStep = -1,
  drift = 0,
  isExecuting = false,
  onClose
}: PolicyChainViewerProps) {
  
  // 🔥 FIX 1: Removed useState and useEffect. 
  // Derive steps directly from props to prevent render lagging and synchronization bugs.
  const steps: ChainStep[] = chain.map((worker, i) => ({
    worker,
    status: i < activeStep ? 'complete' : i === activeStep ? 'active' : 'pending'
  }));

  // Don't render if there's no chain to display
  if (steps.length === 0) return null;

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -20 }}
      className="fixed bottom-24 left-1/2 transform -translate-x-1/2 z-50 w-[90%] max-w-3xl pointer-events-none"
    >
      <div className="bg-[#0E1015]/95 border border-[#2A2E38] rounded-xl shadow-[0_15px_50px_rgba(0,0,0,0.8)] overflow-hidden backdrop-blur-xl pointer-events-auto">
        
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-[#1F222A] bg-[#0A0C10]">
          <div className="flex items-center gap-3">
            <div className="w-2 h-2 bg-[#00E5FF] rounded-full animate-pulse shadow-[0_0_10px_#00E5FF]" />
            <h3 className="text-sm font-bold text-white uppercase tracking-[0.15em]">
              Agamoto-X Policy Chain
            </h3>
          </div>
          <div className="flex items-center gap-4">
            <div className="flex items-center gap-2">
              <span className="text-[10px] font-mono text-[#8A8F9B]">DRIFT</span>
              <span className={`text-xs font-mono ${drift < 0.25 ? 'text-[#10b981]' : 'text-[#FF4500] drop-shadow-[0_0_5px_#FF4500]'}`}>
                {(drift * 100).toFixed(1)}%
              </span>
            </div>
            {onClose && (
              <button 
                onClick={onClose}
                className="text-[#8A8F9B] hover:text-white transition-colors p-1"
              >
                ✕
              </button>
            )}
          </div>
        </div>

        {/* Chain Visualization */}
        <div className="p-6">
          <div className="flex items-center justify-center gap-2 flex-wrap">
            {steps.map((step, index) => (
              <div key={index} className="flex items-center">
                
                {/* Worker Node */}
                <motion.div
                  animate={
                    step.status === 'active' 
                      ? { scale: [1, 1.05, 1], borderColor: workerColors[step.worker] || '#00E5FF' }
                      : { scale: 1, borderColor: '#2A2E38' }
                  }
                  transition={{ repeat: step.status === 'active' ? Infinity : 0, duration: 1.5 }}
                  className={`relative flex flex-col items-center p-3 rounded-lg border-2 min-w-[80px] ${
                    step.status === 'complete' ? 'opacity-60' : ''
                  }`}
                  style={{
                    backgroundColor: step.status === 'active' 
                      ? `${workerColors[step.worker] || '#00E5FF'}10` 
                      : 'transparent'
                  }}
                >
                  <span className="text-2xl mb-1">
                    {workerIcons[step.worker] || '⚙️'}
                  </span>
                  <span className="text-[10px] font-mono uppercase tracking-wider text-white/80">
                    {step.worker}
                  </span>
                  {step.status === 'active' && (
                    <motion.div
                      layoutId="active-glow"
                      className="absolute inset-0 rounded-lg pointer-events-none"
                      style={{
                        boxShadow: `0 0 20px ${workerColors[step.worker] || '#00E5FF'}`,
                        opacity: 0.5
                      }}
                    />
                  )}
                </motion.div>

                {/* Connector Arrow */}
                {index < steps.length - 1 && (
                  <div className="mx-2 flex flex-col items-center">
                    {/* 🔥 FIX 2: Corrected arrow logic. Flow animates if current OR next step is active */}
                    {steps[index].status === 'active' || steps[index + 1].status === 'active' ? (
                      <motion.div
                        animate={{ x: [0, 5, 0], opacity: [0.5, 1, 0.5] }}
                        transition={{ repeat: Infinity, duration: 1.5 }}
                        className="text-[#00E5FF]"
                      >
                        ▶
                      </motion.div>
                    ) : steps[index].status === 'complete' ? (
                      <span className="text-[#00E5FF]">▶</span> /* Solid cyan for completed paths */
                    ) : (
                      <span className="text-[#2A2E38]">▶</span> /* Dim gray for pending paths */
                    )}
                  </div>
                )}
              </div>
            ))}
          </div>

          {/* Drift Meter */}
          <div className="mt-6 pt-4 border-t border-[#1F222A]">
            <div className="flex justify-between text-[10px] font-mono text-[#8A8F9B] mb-2">
              <span>ZERO DRIFT TARGET</span>
              <span>{(drift * 100).toFixed(1)}% / 25.0%</span>
            </div>
            <div className="h-2 bg-[#12141A] rounded-full overflow-hidden border border-[#1F222A]">
              <motion.div
                initial={{ width: 0 }}
                animate={{ width: `${Math.min((drift / 0.25) * 100, 100)}%` }}
                className={`h-full ${
                  drift < 0.15 
                    ? 'bg-[#10b981]' 
                    : drift < 0.25 
                    ? 'bg-yellow-500' 
                    : 'bg-[#FF4500]'
                }`}
                style={{
                  boxShadow: drift < 0.15 
                    ? '0 0 10px #10b981' 
                    : drift < 0.25 
                    ? '0 0 10px #eab308' 
                    : '0 0 10px #FF4500'
                }}
              />
            </div>
          </div>
        </div>
      </div>
    </motion.div>
  );
}