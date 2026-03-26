'use client';

import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  Brain, Cpu, Eye, Zap, Shield, Code, 
  Loader2, ChevronRight, Activity, Gauge, Rocket
} from 'lucide-react';

interface LoadingState {
  stage: string;
  message: string;
  progress: number;
  estimated_time_ms: number;
  model_name: string;
}

interface RoutingResult {
  task: string;
  analysis: any;
  selected_model: string;
  load_time_ms: number;
  drift_lock: string;
}

export const SmartRouter: React.FC = () => {
  const [task, setTask] = useState('');
  const[isRouting, setIsRouting] = useState(false);
  const [loadingState, setLoadingState] = useState<LoadingState | null>(null);
  const [result, setResult] = useState<RoutingResult | null>(null);
  const [showDetails, setShowDetails] = useState(false);

  const modelIcons: Record<string, any> = {
    'qwen2.5-coder:14b': Code,
    'qwen:32b': Brain,
    'gemma2:9b': Shield,
    'llama3.2-vision:11b': Eye,
    'phi3.5:3.8b': Zap,
    'default': Cpu
  };

  const modelColors: Record<string, string> = {
    'qwen2.5-coder:14b': '#00E5FF',
    'qwen:32b': '#9B72CB',
    'gemma2:9b': '#8AB4F8',
    'llama3.2-vision:11b': '#00e676',
    'phi3.5:3.8b': '#ffaa00',
    'default': '#ffffff'
  };

  const handleRoute = async () => {
    if (!task.trim() || isRouting) return;

    setIsRouting(true);
    setResult(null);
    setLoadingState(null);

    // Connect directly to the new Python async generator stream
    const eventSource = new EventSource(`http://localhost:8001/smart/route-stream?task=${encodeURIComponent(task)}`);

    eventSource.onmessage = (event) => {
      const data = JSON.parse(event.data);
      if (data.type === 'loading') {
        setLoadingState(data.state);
      } else if (data.type === 'complete') {
        setResult(data.result);
        setIsRouting(false);
        eventSource.close();
      } else if (data.type === 'error') {
        setIsRouting(false);
        eventSource.close();
        alert('Router Error: ' + data.content);
      }
    };

    eventSource.onerror = () => {
      setIsRouting(false);
      eventSource.close();
    };
  };

  const getStageIcon = (stage: string) => {
    switch(stage) {
      case 'analyzing': return <Activity className="w-4 h-4 animate-pulse" />;
      case 'selecting': return <Gauge className="w-4 h-4 animate-spin" />;
      case 'loading_model': return <Rocket className="w-4 h-4 animate-bounce" />;
      case 'executing': return <Brain className="w-4 h-4 animate-pulse" />;
      default: return <Loader2 className="w-4 h-4 animate-spin" />;
    }
  };

  const ModelIcon = result ? (modelIcons[result.selected_model] || modelIcons.default) : Cpu;

  return (
    <div className="bg-black/40 backdrop-blur-xl border border-white/10 rounded-2xl overflow-hidden w-full max-w-xl mx-auto shadow-2xl">
      {/* Header */}
      <div className="border-b border-white/10 p-4 bg-gradient-to-r from-black/80 to-black/40">
        <div className="flex items-center gap-2">
          <Brain className="w-5 h-5 text-[#00E5FF]" />
          <h2 className="text-sm font-bold text-white uppercase tracking-widest">
            AI SMART ROUTER
          </h2>
          <span className="px-2 py-0.5 bg-[#00E5FF]/10 border border-[#00E5FF]/30 rounded text-[8px] font-mono text-[#00E5FF] ml-auto">
            COGNITIVE LOAD BALANCING
          </span>
        </div>
      </div>

      {/* Input Area */}
      <div className="p-4">
        <textarea
          value={task}
          onChange={(e) => setTask(e.target.value)}
          placeholder="Describe what you need... (e.g., 'Write a React component', 'Analyze this strategy')"
          className="w-full bg-black/40 border border-white/10 rounded-lg p-3 text-[12px] text-white placeholder:text-zinc-600 outline-none focus:border-[#00E5FF]/50 transition-colors min-h-[80px] resize-none font-mono"
          disabled={isRouting}
        />

        <button
          onClick={handleRoute}
          disabled={!task.trim() || isRouting}
          className={`w-full mt-3 py-3 rounded-lg text-[10px] font-mono font-bold uppercase tracking-widest transition-all flex items-center justify-center gap-2 ${
            task.trim() && !isRouting
              ? 'bg-gradient-to-r from-[#00E5FF] to-[#9B72CB] text-black hover:opacity-90 shadow-[0_0_15px_rgba(0,229,255,0.4)]'
              : 'bg-white/5 text-zinc-500 cursor-not-allowed'
          }`}
        >
          {isRouting ? (
            <><Loader2 className="w-4 h-4 animate-spin" /> ROUTING TASK...</>
          ) : (
            <><Zap className="w-4 h-4" /> ROUTE TO OPTIMAL MODEL</>
          )}
        </button>
      </div>

      {/* Loading Animation */}
      <AnimatePresence>
        {isRouting && loadingState && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            className="overflow-hidden"
          >
            <div className="p-4 bg-white/5 border-t border-white/10">
              <div className="flex items-center gap-2 mb-4 text-[#00E5FF]">
                {getStageIcon(loadingState.stage)}
                <span className="text-[10px] font-mono uppercase tracking-wider text-white">
                  {loadingState.stage.replace('_', ' ')}
                </span>
                <span className="text-[9px] font-mono text-zinc-500 ml-auto">
                  {loadingState.estimated_time_ms}ms
                </span>
              </div>

              <motion.div
                key={loadingState.message}
                initial={{ y: 5, opacity: 0 }}
                animate={{ y: 0, opacity: 1 }}
                className="text-xs font-mono text-zinc-300 mb-3"
              >
                {loadingState.message}
              </motion.div>

              <div className="relative h-1.5 bg-black/50 rounded-full overflow-hidden border border-white/10">
                <motion.div
                  className="absolute top-0 left-0 h-full bg-gradient-to-r from-[#00E5FF] to-[#9B72CB]"
                  initial={{ width: `${loadingState.progress}%` }}
                  animate={{ width: `${loadingState.progress}%` }}
                  transition={{ duration: 0.3 }}
                />
              </div>

              <div className="mt-3 flex items-center gap-2 bg-black/30 p-2 rounded border border-white/5">
                <div className="w-6 h-6 rounded-full bg-white/5 border border-white/10 flex items-center justify-center">
                  {React.createElement(modelIcons[loadingState.model_name] || modelIcons.default, {
                    className: 'w-3 h-3',
                    style: { color: modelColors[loadingState.model_name] || modelColors.default }
                  })}
                </div>
                <span className="text-[9px] font-mono text-zinc-400">
                  Target: <span className="text-white font-bold">{loadingState.model_name}</span>
                </span>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Results */}
      <AnimatePresence>
        {result && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            className="overflow-hidden border-t border-white/10 bg-[#030406]/50"
          >
            <div className="p-4">
              <div className="bg-gradient-to-br from-[#00E5FF]/5 to-[#9B72CB]/5 border border-white/10 rounded-lg p-4 shadow-inner">
                <div className="flex items-center gap-3 mb-4">
                  <div 
                    className="w-12 h-12 rounded-xl flex items-center justify-center border"
                    style={{ 
                      backgroundColor: `${modelColors[result.selected_model]}10`,
                      borderColor: `${modelColors[result.selected_model]}30` 
                    }}
                  >
                    <ModelIcon className="w-6 h-6" style={{ color: modelColors[result.selected_model] }} />
                  </div>
                  <div>
                    <div className="text-[13px] font-mono font-bold text-white tracking-wide">
                      {result.selected_model}
                    </div>
                    <div className="text-[9px] font-mono text-zinc-500 uppercase tracking-widest">
                      Selected for: <span className="text-zinc-300">{result.analysis.task_type}</span>
                    </div>
                  </div>
                  <div className="ml-auto text-right bg-black/40 p-2 rounded-lg border border-white/5">
                    <div className="text-[8px] font-mono text-zinc-500 uppercase tracking-widest mb-0.5">Load Time</div>
                    <div className="text-[12px] font-mono text-[#00E5FF] font-bold">
                      {result.load_time_ms.toFixed(0)}ms
                    </div>
                  </div>
                </div>

                <div className="flex flex-wrap gap-2 mb-4">
                  <span className="px-2 py-1 bg-black/40 border border-white/10 rounded text-[9px] font-mono text-zinc-300">
                    CMPLX: {result.analysis.complexity.toFixed(1)}/10
                  </span>
                  <span className="px-2 py-1 bg-black/40 border border-white/10 rounded text-[9px] font-mono text-zinc-300">
                    TOKENS: ~{result.analysis.estimated_tokens}
                  </span>
                  {result.analysis.needs_code && (
                    <span className="px-2 py-1 bg-[#00E5FF]/10 border border-[#00E5FF]/30 rounded text-[9px] font-mono font-bold text-[#00E5FF]">
                      CODE REQ
                    </span>
                  )}
                  {result.analysis.needs_reasoning && (
                    <span className="px-2 py-1 bg-[#9B72CB]/10 border border-[#9B72CB]/30 rounded text-[9px] font-mono font-bold text-[#9B72CB]">
                      REASONING
                    </span>
                  )}
                </div>

                <div className="flex items-center gap-2 p-3 bg-[#00e676]/5 rounded-lg border border-[#00e676]/20">
                  <Shield className="w-4 h-4 text-[#00e676]" />
                  <span className="text-[9px] font-mono text-[#00e676] tracking-widest uppercase">Drift Lock Sealed:</span>
                  <code className="text-[10px] font-mono font-bold text-[#00e676] bg-black/40 px-2 py-0.5 rounded">{result.drift_lock}</code>
                </div>

                <button
                  onClick={() => setShowDetails(!showDetails)}
                  className="w-full mt-4 flex items-center justify-between text-[9px] font-mono tracking-widest uppercase text-zinc-500 hover:text-white transition-colors bg-black/20 p-2 rounded"
                >
                  <span>View Neural Telemetry</span>
                  <ChevronRight className={`w-3 h-3 transition-transform ${showDetails ? 'rotate-90' : ''}`} />
                </button>

                <AnimatePresence>
                  {showDetails && (
                    <motion.div
                      initial={{ height: 0, opacity: 0 }}
                      animate={{ height: 'auto', opacity: 1 }}
                      exit={{ height: 0, opacity: 0 }}
                      className="overflow-hidden"
                    >
                      <div className="mt-2 p-3 bg-black/60 rounded-lg border border-white/5 shadow-inner">
                        <pre className="text-[9px] leading-relaxed font-mono text-zinc-400 whitespace-pre-wrap">
                          {JSON.stringify(result.analysis, null, 2)}
                        </pre>
                      </div>
                    </motion.div>
                  )}
                </AnimatePresence>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
};