import { motion, AnimatePresence } from 'framer-motion';
import { useEffect, useState } from 'react';

export interface PipelineStep {
  id: string;
  name: string;
  worker: string;
  status: 'idle' | 'processing' | 'success' | 'error';
  timestamp?: string;
  latency?: number;
  output?: string;
}

interface LiveWorkerPipelineProps {
  steps: PipelineStep[];
  isActive: boolean;
  currentStepIndex: number;
  onStepClick?: (step: PipelineStep) => void;
  className?: string;
}

const statusConfig = {
  idle: { color: '#4B5563', glow: 'none', icon: '○' },
  processing: { color: '#00E5FF', glow: '0_0_15px_rgba(0,229,255,0.6)', icon: '◐' },
  success: { color: '#10b981', glow: '0_0_10px_rgba(16,185,129,0.4)', icon: '●' },
  error: { color: '#FF4500', glow: '0_0_15px_rgba(255,69,0,0.6)', icon: '✕' }
};

export default function LiveWorkerPipeline({ 
  steps, 
  isActive, 
  currentStepIndex,
  onStepClick,
  className = '' 
}: LiveWorkerPipelineProps) {
  const [expandedStep, setExpandedStep] = useState<string | null>(null);

  useEffect(() => {
    if (isActive && currentStepIndex >= 0 && steps[currentStepIndex]) {
      setExpandedStep(steps[currentStepIndex].id);
    }
  }, [currentStepIndex, isActive, steps]);

  if (!isActive && steps.length === 0) return null;

  return (
    <div className={`bg-[#0E1015]/90 backdrop-blur-md border border-[#1F222A] rounded-xl p-5 shadow-[0_8px_30px_rgba(0,0,0,0.5)] relative overflow-hidden ${className}`}>
      <div className="absolute top-0 right-0 w-64 h-64 bg-[#00E5FF]/5 rounded-full blur-3xl pointer-events-none" />
      
      <div className="flex items-center justify-between mb-6 relative z-10">
        <div className="flex items-center gap-2 text-xs font-bold tracking-[0.15em] uppercase text-white">
          <motion.div 
            animate={isActive ? { rotate: 360 } : {}}
            transition={{ duration: 4, repeat: Infinity, ease: "linear" }}
            className="text-[#00E5FF] drop-shadow-[0_0_5px_#00E5FF]"
          >
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5"/>
            </svg>
          </motion.div>
          Worker Pipeline
        </div>
        <div className="flex items-center gap-2">
          {isActive && (
            <motion.span 
              animate={{ opacity: [1, 0.5, 1] }}
              transition={{ duration: 1.5, repeat: Infinity }}
              className="text-[9px] px-2 py-0.5 rounded bg-[#00E5FF]/10 text-[#00E5FF] font-mono uppercase border border-[#00E5FF]/20"
            >
              EXECUTING
            </motion.span>
          )}
          <span className="text-[9px] text-[#8A8F9B] font-mono">
            {steps.filter(s => s.status === 'success').length}/{steps.length} COMPLETE
          </span>
        </div>
      </div>

      <div className="relative z-10 space-y-0">
        {steps.map((step, index) => {
          const config = statusConfig[step.status];
          const isCurrent = index === currentStepIndex;
          const isExpanded = expandedStep === step.id;
          const hasNext = index < steps.length - 1;

          return (
            <div key={step.id} className="relative">
              {hasNext && (
                <motion.div className="absolute left-[11px] top-[32px] w-[2px] h-[24px] bg-[#1F222A] rounded-full overflow-hidden" initial={false}>
                  <motion.div
                    className="w-full bg-gradient-to-b from-[#00E5FF] to-[#10b981]"
                    initial={{ height: "0%" }}
                    animate={{ height: steps[index + 1]?.status !== 'idle' ? "100%" : "0%" }}
                    transition={{ duration: 0.5, ease: "easeInOut" }}
                  />
                </motion.div>
              )}

              <motion.div
                layout
                onClick={() => { setExpandedStep(isExpanded ? null : step.id); onStepClick?.(step); }}
                className={`flex items-start gap-3 p-3 rounded-lg border transition-all cursor-pointer ${
                  isCurrent ? 'bg-[#00E5FF]/5 border-[#00E5FF]/30 shadow-[0_0_15px_rgba(0,229,255,0.1)]' : 'bg-[#12141A]/50 border-[#2A2E38] hover:border-[#4B5563]'
                }`}
                whileHover={{ x: 4 }}
              >
                <div className="flex flex-col items-center mt-1">
                  <motion.div
                    animate={step.status === 'processing' ? { boxShadow:[`0 0 5px ${config.color}`, `0 0 20px ${config.color}`, `0 0 5px ${config.color}`] } : {}}
                    transition={{ duration: 1.5, repeat: Infinity }}
                    className="w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold border-2"
                    style={{ borderColor: config.color, color: config.color, backgroundColor: `${config.color}10`, boxShadow: step.status === 'processing' ? 'none' : `var(--tw-shadow-${config.glow})` }}
                  >
                    {step.status === 'processing' ? (
                      <motion.div animate={{ rotate: 360 }} transition={{ duration: 1, repeat: Infinity, ease: "linear" }}>◐</motion.div>
                    ) : config.icon}
                  </motion.div>
                </div>

                <div className="flex-1 min-w-0">
                  <div className="flex items-center justify-between mb-1">
                    <span className={`text-sm font-medium tracking-wide ${isCurrent ? 'text-white' : 'text-[#8A8F9B]'}`}>{step.name}</span>
                    {step.latency && <span className="text-[9px] font-mono text-[#4B5563]">{step.latency}ms</span>}
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="text-[9px] px-1.5 py-0.5 rounded font-mono uppercase" style={{ color: config.color, backgroundColor: `${config.color}15`, border: `1px solid ${config.color}30` }}>
                      {step.worker}
                    </span>
                    {step.timestamp && <span className="text-[9px] text-[#4B5563] font-mono">{step.timestamp}</span>}
                  </div>
                  <AnimatePresence>
                    {isExpanded && step.output && (
                      <motion.div initial={{ height: 0, opacity: 0 }} animate={{ height: 'auto', opacity: 1 }} exit={{ height: 0, opacity: 0 }} className="mt-2 p-2 bg-[#0A0C10] rounded border border-[#1F222A] overflow-hidden">
                        <code className="text-[10px] font-mono text-[#00E5FF]/80 break-all">{step.output}</code>
                      </motion.div>
                    )}
                  </AnimatePresence>
                </div>
              </motion.div>
            </div>
          );
        })}
      </div>
      <div className="mt-4 relative z-10">
        <div className="h-1 bg-[#1A1D24] rounded-full overflow-hidden border border-[#2A2E38]">
          <motion.div className="h-full bg-gradient-to-r from-[#00E5FF] to-[#10b981] rounded-full" initial={{ width: 0 }} animate={{ width: `${(steps.filter(s => s.status === 'success').length / steps.length) * 100}%` }} transition={{ duration: 0.5, ease: "easeOut" }} />
        </div>
      </div>
    </div>
  );
}