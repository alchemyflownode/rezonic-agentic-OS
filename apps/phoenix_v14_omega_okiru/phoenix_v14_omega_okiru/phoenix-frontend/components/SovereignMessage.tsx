'use client';

import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Bot, User, ShieldCheck, Wrench, Brain, Search, Play,
  ChevronDown, ChevronRight, CheckCircle, XCircle, Loader2,
  Clock, GitBranch, Zap, Sparkles, Lock, Eye, EyeOff
} from 'lucide-react';

// ==========================================
// TYPES
// ==========================================
interface AgentStep {
  id?: string;
  type: 'think' | 'search' | 'scan' | 'execute' | 'code' | 'respond';
  content: string;
  status?: 'pending' | 'active' | 'done' | 'error';
  duration?: number;
}

interface ToolCall {
  id?: string;
  name: string;
  input: any;
  output?: any;
  status?: 'pending' | 'running' | 'done' | 'error';
  duration?: number;
}

interface SovereignMessageProps {
  content: string;
  role: 'user' | 'assistant' | 'system';
  timestamp: string;
  isStreaming?: boolean;
  driftLock?: string;
  narrative?: string[];
  agentTrace?: AgentStep[];
  tools?: ToolCall[];
  confidence?: number;
  worker?: string;
  onReplay?: (stepIndex: number) => void;
  onFork?: () => void;
  className?: string;
}

// ==========================================
// HELPER COMPONENTS
// ==========================================

const StepIcon = ({ type, status }: { type: string; status?: string }) => {
  const icons = {
    think: Brain,
    search: Search,
    scan: Zap,
    execute: Play,
    code: GitBranch,
    respond: Sparkles
  };
  const Icon = icons[type as keyof typeof icons] || Brain;
  
  const colors = {
    think: '#9B72CB',
    search: '#7dcfff',
    scan: '#ff9e64',
    execute: '#9ece6a',
    code: '#f7768e',
    respond: '#7dcfff'
  };
  
  const color = colors[type as keyof typeof colors] || '#7dcfff';
  
  if (status === 'active') {
    return (
      <div className="relative">
        <Loader2 className="w-3 h-3 animate-spin" style={{ color }} />
      </div>
    );
  }
  
  if (status === 'done') {
    return <CheckCircle className="w-3 h-3 text-[#9ece6a]" />;
  }
  
  if (status === 'error') {
    return <XCircle className="w-3 h-3 text-[#f7768e]" />;
  }
  
  return <Icon className="w-3 h-3" style={{ color }} />;
};

const StatusBadge = ({ status }: { status: string }) => {
  const config = {
    pending: { icon: Clock, color: '#565f89', label: 'Pending' },
    active: { icon: Loader2, color: '#7dcfff', label: 'Active', animate: true },
    running: { icon: Loader2, color: '#7dcfff', label: 'Running', animate: true },
    done: { icon: CheckCircle, color: '#9ece6a', label: 'Done' },
    complete: { icon: CheckCircle, color: '#9ece6a', label: 'Complete' },
    error: { icon: XCircle, color: '#f7768e', label: 'Error' }
  };
  
  const cfg = config[status as keyof typeof config] || config.pending;
  const Icon = cfg.icon;
  
  return (
    <div className="flex items-center gap-1">
      {cfg.animate ? (
        <Icon className="w-2.5 h-2.5 animate-spin" style={{ color: cfg.color }} />
      ) : (
        <Icon className="w-2.5 h-2.5" style={{ color: cfg.color }} />
      )}
      <span className="text-[7px] font-mono" style={{ color: cfg.color }}>
        {cfg.label}
      </span>
    </div>
  );
};

const ConfidenceMeter = ({ score }: { score: number }) => {
  const color = score >= 85 ? '#9ece6a' : score >= 60 ? '#ff9e64' : '#f7768e';
  return (
    <div className="flex items-center gap-1.5">
      <div className="w-12 h-1 bg-white/10 rounded-full overflow-hidden">
        <div className="h-full rounded-full" style={{ width: `${score}%`, backgroundColor: color }} />
      </div>
      <span className="text-[8px] font-mono" style={{ color }}>{score}%</span>
    </div>
  );
};

// ==========================================
// MAIN COMPONENT
// ==========================================
export const SovereignMessage: React.FC<SovereignMessageProps> = ({
  content,
  role,
  timestamp,
  isStreaming = false,
  driftLock,
  narrative = [],
  agentTrace = [],
  tools = [],
  confidence,
  worker,
  onReplay,
  onFork,
  className = ''
}) => {
  const [showNarrative, setShowNarrative] = useState(false);
  const [showTrace, setShowTrace] = useState(false);
  const [showTools, setShowTools] = useState(false);
  const [showDetails, setShowDetails] = useState(false);

  const isUser = role === 'user';
  const isSystem = role === 'system';
  const isAssistant = role === 'assistant';

  // User Message
  if (isUser) {
    return (
      <motion.div
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        exit={{ opacity: 0, y: -10 }}
        className="flex justify-end"
      >
        <div className="max-w-[85%] bg-gradient-to-r from-[#7dcfff]/20 to-[#9B72CB]/20 border border-[#7dcfff]/30 rounded-2xl rounded-br-sm p-4">
          <div className="text-sm leading-relaxed whitespace-pre-wrap">
            {content}
          </div>
          <div className="mt-2 text-[8px] text-[#565f89] text-right flex items-center justify-end gap-2">
            <Clock className="w-2.5 h-2.5" />
            {timestamp}
          </div>
        </div>
      </motion.div>
    );
  }

  // System Message
  if (isSystem) {
    return (
      <motion.div
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        exit={{ opacity: 0, y: -10 }}
        className="flex justify-center"
      >
        <div className="bg-[#f7768e]/10 border border-[#f7768e]/30 rounded-xl p-3 max-w-[90%]">
          <div className="flex items-center gap-2 mb-1">
            <ShieldCheck className="w-3 h-3 text-[#f7768e]" />
            <span className="text-[9px] font-mono text-[#f7768e]/80">SYSTEM</span>
          </div>
          <div className="text-[11px] text-[#f7768e]/90">{content}</div>
        </div>
      </motion.div>
    );
  }

  // Assistant Message - Full Intelligence Layer
  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -10 }}
      className="flex justify-start"
    >
      <div className={`max-w-[85%] bg-white/5 border border-white/10 rounded-2xl rounded-bl-sm overflow-hidden ${className}`}>
        
        {/* Header */}
        <div className="px-4 pt-3 pb-2 border-b border-white/5 bg-white/5 flex items-center justify-between flex-wrap gap-2">
          <div className="flex items-center gap-2">
            <Bot className="w-3 h-3 text-[#9ece6a]" />
            <span className="text-[10px] font-mono text-[#565f89] uppercase">ASSISTANT</span>
            {worker && (
              <span className="text-[8px] font-mono text-[#7dcfff] bg-[#7dcfff]/10 px-1.5 py-0.5 rounded">
                {worker}
              </span>
            )}
          </div>
          
          <div className="flex items-center gap-2">
            {confidence && <ConfidenceMeter score={confidence} />}
            
            {driftLock && (
              <div className="flex items-center gap-1">
                <Lock className="w-2.5 h-2.5 text-[#9ece6a]" />
                <code className="text-[7px] font-mono text-[#9ece6a]">
                  {driftLock.slice(0, 6)}...
                </code>
              </div>
            )}
            
            <button
              onClick={() => setShowDetails(!showDetails)}
              className="text-[8px] text-[#565f89] hover:text-white transition-colors"
            >
              {showDetails ? <EyeOff className="w-3 h-3" /> : <Eye className="w-3 h-3" />}
            </button>
          </div>
        </div>

        {/* Main Content */}
        <div className="p-4">
          <div className="text-sm leading-relaxed whitespace-pre-wrap">
            {content}
            {isStreaming && (
              <span className="inline-block w-2 h-4 ml-1 bg-[#7dcfff] animate-pulse" />
            )}
          </div>
        </div>

        {/* Details Panel - Collapsible Intelligence Layer */}
        <AnimatePresence>
          {showDetails && (
            <motion.div
              initial={{ height: 0, opacity: 0 }}
              animate={{ height: 'auto', opacity: 1 }}
              exit={{ height: 0, opacity: 0 }}
              className="border-t border-white/5"
            >
              {/* Agent Trace */}
              {agentTrace.length > 0 && (
                <div className="border-b border-white/5">
                  <button
                    onClick={() => setShowTrace(!showTrace)}
                    className="w-full px-4 py-2 flex items-center justify-between text-[9px] font-mono text-[#7dcfff] hover:bg-white/5 transition-colors"
                  >
                    <div className="flex items-center gap-2">
                      <Brain className="w-3 h-3" />
                      <span>Agent Trace ({agentTrace.length} steps)</span>
                    </div>
                    {showTrace ? <ChevronDown className="w-3 h-3" /> : <ChevronRight className="w-3 h-3" />}
                  </button>
                  
                  <AnimatePresence>
                    {showTrace && (
                      <motion.div
                        initial={{ height: 0 }}
                        animate={{ height: 'auto' }}
                        exit={{ height: 0 }}
                        className="overflow-hidden"
                      >
                        <div className="p-3 bg-black/20 space-y-2">
                          {agentTrace.map((step, idx) => (
                            <div key={step.id || idx} className="flex items-start gap-2 group">
                              <div className="mt-0.5">
                                <StepIcon type={step.type} status={step.status} />
                              </div>
                              <div className="flex-1">
                                <div className="flex items-center gap-2">
                                  <span className="text-[9px] font-mono uppercase" style={{ color: step.type === 'think' ? '#9B72CB' : '#7dcfff' }}>
                                    {step.type}
                                  </span>
                                  {step.status && <StatusBadge status={step.status} />}
                                  {step.duration && (
                                    <span className="text-[7px] text-[#565f89]">{step.duration}ms</span>
                                  )}
                                </div>
                                <div className="text-[10px] text-[#c0caf5] mt-0.5">{step.content}</div>
                                
                                {/* Replay Button */}
                                {onReplay && step.status === 'done' && (
                                  <button
                                    onClick={() => onReplay(idx)}
                                    className="mt-1 text-[7px] text-[#7dcfff] opacity-0 group-hover:opacity-100 transition-opacity"
                                  >
                                    ↺ Replay from here
                                  </button>
                                )}
                              </div>
                            </div>
                          ))}
                        </div>
                      </motion.div>
                    )}
                  </AnimatePresence>
                </div>
              )}

              {/* Tool Calls */}
              {tools.length > 0 && (
                <div className="border-b border-white/5">
                  <button
                    onClick={() => setShowTools(!showTools)}
                    className="w-full px-4 py-2 flex items-center justify-between text-[9px] font-mono text-[#f7768e] hover:bg-white/5 transition-colors"
                  >
                    <div className="flex items-center gap-2">
                      <Wrench className="w-3 h-3" />
                      <span>Tools Used ({tools.length})</span>
                    </div>
                    {showTools ? <ChevronDown className="w-3 h-3" /> : <ChevronRight className="w-3 h-3" />}
                  </button>
                  
                  <AnimatePresence>
                    {showTools && (
                      <motion.div
                        initial={{ height: 0 }}
                        animate={{ height: 'auto' }}
                        exit={{ height: 0 }}
                        className="overflow-hidden"
                      >
                        <div className="p-3 space-y-2">
                          {tools.map((tool, idx) => (
                            <div key={tool.id || idx} className="bg-black/40 border border-white/10 rounded-lg p-2">
                              <div className="flex items-center justify-between">
                                <div className="flex items-center gap-2">
                                  <Wrench className="w-2.5 h-2.5 text-[#f7768e]" />
                                  <span className="text-[9px] font-mono text-[#f7768e]">{tool.name}</span>
                                </div>
                                {tool.status && <StatusBadge status={tool.status} />}
                              </div>
                              <div className="mt-1 text-[9px] text-[#c0caf5]">
                                <span className="text-[#565f89]">Input:</span> {typeof tool.input === 'string' ? tool.input : JSON.stringify(tool.input)}
                              </div>
                              {tool.output && (
                                <div className="mt-1 text-[9px] text-[#9ece6a]">
                                  <span className="text-[#565f89]">Output:</span> {typeof tool.output === 'string' ? tool.output.slice(0, 100) : JSON.stringify(tool.output).slice(0, 100)}
                                  {tool.output.length > 100 && '...'}
                                </div>
                              )}
                              {tool.duration && (
                                <div className="mt-1 text-[7px] text-[#565f89]">Duration: {tool.duration}ms</div>
                              )}
                            </div>
                          ))}
                        </div>
                      </motion.div>
                    )}
                  </AnimatePresence>
                </div>
              )}

              {/* Narrative / Reasoning */}
              {narrative.length > 0 && (
                <div>
                  <button
                    onClick={() => setShowNarrative(!showNarrative)}
                    className="w-full px-4 py-2 flex items-center justify-between text-[9px] font-mono text-[#9ece6a] hover:bg-white/5 transition-colors"
                  >
                    <div className="flex items-center gap-2">
                      <Brain className="w-3 h-3" />
                      <span>Reasoning ({narrative.length} steps)</span>
                    </div>
                    {showNarrative ? <ChevronDown className="w-3 h-3" /> : <ChevronRight className="w-3 h-3" />}
                  </button>
                  
                  <AnimatePresence>
                    {showNarrative && (
                      <motion.div
                        initial={{ height: 0 }}
                        animate={{ height: 'auto' }}
                        exit={{ height: 0 }}
                        className="overflow-hidden"
                      >
                        <div className="p-3 bg-purple-500/5 space-y-1.5">
                          {narrative.map((step, idx) => (
                            <div key={idx} className="text-[9px] font-mono text-[#c0caf5] italic leading-relaxed border-l-2 border-[#9B72CB]/30 pl-2 py-0.5">
                              "{step}"
                            </div>
                          ))}
                        </div>
                      </motion.div>
                    )}
                  </AnimatePresence>
                </div>
              )}
            </motion.div>
          )}
        </AnimatePresence>

        {/* Footer */}
        <div className="px-4 py-2 border-t border-white/5 bg-black/20 flex items-center justify-between">
          <div className="flex items-center gap-2 text-[8px] text-[#565f89]">
            <Clock className="w-2.5 h-2.5" />
            {timestamp}
          </div>
          
          {onFork && (
            <button
              onClick={onFork}
              className="text-[7px] font-mono text-[#7dcfff] hover:text-white transition-colors flex items-center gap-1"
            >
              <GitBranch className="w-2.5 h-2.5" />
              Fork Run
            </button>
          )}
          
          <div className="text-[7px] font-mono text-[#565f89]">SCE VERIFIED</div>
        </div>
      </div>
    </motion.div>
  );
};

export default SovereignMessage;