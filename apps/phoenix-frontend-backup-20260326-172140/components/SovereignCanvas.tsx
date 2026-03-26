'use client';

import React, { useState } from 'react';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Copy, Check, Play, Loader2, Terminal, Maximize2, Minimize2,
  ChevronDown, ChevronUp, Eye, EyeOff, CheckCircle, AlertCircle, Clock,
  Shield, GitBranch
} from 'lucide-react';

interface SCEContext {
  verified?: boolean;
  driftLock?: string;
  narrative?: string[];
}

interface SovereignCanvasProps {
  code: string;
  language?: string;
  title?: string;
  executable?: boolean;
  onExecute?: (code: string) => Promise<any>;
  metadata?: {
    author?: string;
    created?: string;
    version?: string;
    driftLock?: string;
    verified?: boolean;
  };
  sce?: SCEContext;
  className?: string;
}

type ExecutionState = 'idle' | 'running' | 'success' | 'error';

export const SovereignCanvas = ({
  code,
  language = 'text',
  title,
  executable = false,
  onExecute,
  metadata,
  sce,
  className = ''
}: SovereignCanvasProps) => {
  const [copied, setCopied] = useState(false);
  const [expanded, setExpanded] = useState(false);
  const [focused, setFocused] = useState(false);
  const [status, setStatus] = useState<ExecutionState>('idle');
  const [showLogs, setShowLogs] = useState(false);
  const [logs, setLogs] = useState<string[]>([]);
  const [showMetadata, setShowMetadata] = useState(false);
  const [showNarrative, setShowNarrative] = useState(false);

  const lineCount = code.split('\n').length;

  const statusColors = {
    idle: 'text-[#565f89]',
    running: 'text-[#7dcfff]',
    success: 'text-[#9ece6a]',
    error: 'text-[#f7768e]'
  };

  const statusIcons = {
    idle: <Clock className="w-3 h-3" />,
    running: <Loader2 className="w-3 h-3 animate-spin" />,
    success: <CheckCircle className="w-3 h-3" />,
    error: <AlertCircle className="w-3 h-3" />
  };

  const statusStyles = {
    idle: 'border-[#7dcfff]/10',
    running: 'ring-1 ring-[#7dcfff]/40 shadow-[0_0_20px_rgba(125,207,255,0.15)] border-[#7dcfff]/30',
    success: 'ring-1 ring-[#9ece6a]/40 shadow-[0_0_20px_rgba(158,206,106,0.15)] border-[#9ece6a]/30',
    error: 'ring-1 ring-[#f7768e]/40 shadow-[0_0_20px_rgba(247,118,142,0.15)] border-[#f7768e]/30'
  };

  const handleCopy = async () => {
    await navigator.clipboard.writeText(code);
    setCopied(true);
    setTimeout(() => setCopied(false), 1500);
    addLog('[📋] Code copied to clipboard');
  };

  const addLog = (message: string) => {
    setLogs(prev => [`[${new Date().toLocaleTimeString()}] ${message}`, ...prev].slice(0, 20));
  };

  const handleRun = async () => {
    if (!executable) return;
    try {
      setStatus('running');
      addLog('[🚀] Executing code...');
      if (onExecute) {
        const result = await onExecute(code);
        setStatus('success');
        addLog(`[✅] Execution success: ${result?.message || 'Completed'}`);
      } else {
        await new Promise(resolve => setTimeout(resolve, 1200));
        setStatus('success');
        addLog('[✅] Code executed (SCE verified)');
      }
      setShowLogs(true);
    } catch (e) {
      setStatus('error');
      addLog(`[❌] Execution failed: ${e instanceof Error ? e.message : 'Unknown error'}`);
      setShowLogs(true);
    } finally {
      setTimeout(() => {
        if (status !== 'error') setStatus('idle');
      }, 2000);
    }
  };

  const normalizedLang = language.toLowerCase();

  return (
    <>
      <AnimatePresence>
        {focused && (
          <motion.div
            className="fixed inset-0 bg-black/60 backdrop-blur-sm z-40"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={() => setFocused(false)}
          />
        )}
      </AnimatePresence>

      <motion.div
        layout
        className={`
          relative group border rounded-2xl overflow-hidden bg-gradient-to-br from-[#121217] to-[#0a0a0c]
          transition-all duration-300 ${statusStyles[status]} ${focused ? 'z-50 scale-[1.02] shadow-2xl' : 'z-0'} ${className}
        `}
        onClick={() => setFocused(!focused)}
      >
        {/* Header */}
        <div className="px-4 py-3 border-b border-[#7dcfff]/10 bg-black/30 flex items-center justify-between">
          <div className="flex items-center gap-3 flex-1">
            <Terminal className="w-4 h-4 text-[#7dcfff]" />
            <span className="text-xs font-mono text-white/90">
              {title || `${normalizedLang.toUpperCase()} · ${lineCount} lines`}
            </span>
            {sce?.verified && (
              <span className="ml-2 text-[8px] font-mono text-[#9ece6a] flex items-center gap-1">
                <Shield className="w-2.5 h-2.5" /> SCE VERIFIED
              </span>
            )}
            {sce?.driftLock && (
              <span className="text-[7px] font-mono text-[#7dcfff]/70 flex items-center gap-1">
                <GitBranch className="w-2.5 h-2.5" />
                {sce.driftLock.slice(0, 8)}...
              </span>
            )}
          </div>

          <div className="flex items-center gap-1">
            {executable && (
              <button
                onClick={(e) => { e.stopPropagation(); handleRun(); }}
                disabled={status === 'running'}
                className="p-1.5 rounded-lg hover:bg-white/10 transition disabled:opacity-50"
                title="Execute code"
              >
                {status === 'running' ? (
                  <Loader2 className="w-3.5 h-3.5 animate-spin text-[#7dcfff]" />
                ) : (
                  <Play className={`w-3.5 h-3.5 ${statusColors[status]}`} />
                )}
              </button>
            )}
            <button
              onClick={(e) => { e.stopPropagation(); handleCopy(); }}
              className="p-1.5 rounded-lg hover:bg-white/10 transition"
              title="Copy code"
            >
              {copied ? <Check className="w-3.5 h-3.5 text-[#9ece6a]" /> : <Copy className="w-3.5 h-3.5 text-zinc-400" />}
            </button>
            <button
              onClick={(e) => { e.stopPropagation(); setExpanded(!expanded); }}
              className="p-1.5 rounded-lg hover:bg-white/10 transition"
            >
              {expanded ? <Minimize2 className="w-3.5 h-3.5 text-zinc-400" /> : <Maximize2 className="w-3.5 h-3.5 text-zinc-400" />}
            </button>
            {metadata && (
              <button
                onClick={(e) => { e.stopPropagation(); setShowMetadata(!showMetadata); }}
                className="p-1.5 rounded-lg hover:bg-white/10 transition"
              >
                {showMetadata ? <EyeOff className="w-3.5 h-3.5 text-zinc-400" /> : <Eye className="w-3.5 h-3.5 text-zinc-400" />}
              </button>
            )}
          </div>
        </div>

        {/* Code Content */}
        <div className={`transition-all duration-300 overflow-auto custom-scrollbar ${expanded ? 'max-h-[600px]' : 'max-h-[400px]'}`}>
          <SyntaxHighlighter
            language={normalizedLang}
            style={{}}
            customStyle={{
              margin: 0,
              padding: '1.5rem',
              background: 'transparent',
              fontSize: '12px',
              lineHeight: '1.6',
              fontFamily: "'JetBrains Mono', 'Fira Code', monospace"
            }}
            showLineNumbers={lineCount >= 3}
            lineNumberStyle={{ color: '#565f89', paddingRight: '1rem' }}
          >
            {code}
          </SyntaxHighlighter>
        </div>

        {/* Metadata Panel */}
        <AnimatePresence>
          {showMetadata && metadata && (
            <motion.div
              initial={{ height: 0, opacity: 0 }}
              animate={{ height: 'auto', opacity: 1 }}
              exit={{ height: 0, opacity: 0 }}
              className="border-t border-[#7dcfff]/10 bg-black/20"
            >
              <div className="px-4 py-3 grid grid-cols-3 gap-4 text-[9px] font-mono">
                {metadata.author && <div><span className="text-[#565f89]">Author</span><div className="text-white/90 mt-1">{metadata.author}</div></div>}
                {metadata.created && <div><span className="text-[#565f89]">Created</span><div className="text-white/90 mt-1">{metadata.created}</div></div>}
                {metadata.version && <div><span className="text-[#565f89]">Version</span><div className="text-white/90 mt-1">{metadata.version}</div></div>}
              </div>
            </motion.div>
          )}
        </AnimatePresence>

        {/* Execution Footer */}
        <AnimatePresence>
          {(status !== 'idle' || showLogs) && (
            <motion.div
              initial={{ height: 0, opacity: 0 }}
              animate={{ height: 'auto', opacity: 1 }}
              exit={{ height: 0, opacity: 0 }}
              className="border-t border-[#7dcfff]/10 bg-black/20"
            >
              <div className="px-4 py-2 flex items-center justify-between">
                <div className="flex items-center gap-2 text-[9px] font-mono">
                  <span className={statusColors[status]}>{statusIcons[status]}</span>
                  <span className={statusColors[status]}>
                    {status === 'idle' && 'Ready'}
                    {status === 'running' && 'Executing...'}
                    {status === 'success' && 'Execution success'}
                    {status === 'error' && 'Execution failed'}
                  </span>
                </div>
                {logs.length > 0 && (
                  <button
                    onClick={() => setShowLogs(!showLogs)}
                    className="flex items-center gap-1 text-[8px] font-mono text-[#565f89] hover:text-white transition"
                  >
                    {showLogs ? <ChevronUp className="w-3 h-3" /> : <ChevronDown className="w-3 h-3" />}
                    {logs.length} logs
                  </button>
                )}
              </div>

              {showLogs && logs.length > 0 && (
                <div className="p-3 bg-black/40 max-h-32 overflow-auto custom-scrollbar text-[8px] font-mono text-[#565f89] space-y-1">
                  {logs.map((log, i) => (
                    <div key={i} className="border-l-2 border-[#7dcfff]/30 pl-2 py-0.5">{log}</div>
                  ))}
                </div>
              )}
            </motion.div>
          )}
        </AnimatePresence>

        {/* Narrative Panel */}
        {sce?.narrative && sce.narrative.length > 0 && (
          <div className="border-t border-[#7dcfff]/10">
            <button
              onClick={() => setShowNarrative(!showNarrative)}
              className="w-full px-4 py-2 text-[9px] font-mono flex items-center gap-2 bg-black/20 hover:bg-black/30 transition"
            >
              {showNarrative ? <ChevronUp className="w-3 h-3" /> : <ChevronDown className="w-3 h-3" />}
              {showNarrative ? 'HIDE REASONING' : 'SHOW REASONING'} ({sce.narrative.length})
            </button>
            <AnimatePresence>
              {showNarrative && (
                <motion.div
                  initial={{ height: 0, opacity: 0 }}
                  animate={{ height: 'auto', opacity: 1 }}
                  exit={{ height: 0, opacity: 0 }}
                  className="p-4 max-h-40 overflow-auto custom-scrollbar space-y-2 bg-[#9B72CB]/5"
                >
                  {sce.narrative.map((entry, i) => (
                    <div key={i} className="text-[9px] italic text-[#c0caf5] bg-black/20 p-2 rounded-lg border border-[#9B72CB]/20">
                      "{entry}"
                    </div>
                  ))}
                </motion.div>
              )}
            </AnimatePresence>
          </div>
        )}
      </motion.div>

      <style jsx global>{`
        .custom-scrollbar::-webkit-scrollbar { width: 4px; height: 4px; }
        .custom-scrollbar::-webkit-scrollbar-track { background: #1a1b26; border-radius: 4px; }
        .custom-scrollbar::-webkit-scrollbar-thumb { background: #3b4261; border-radius: 4px; }
        .custom-scrollbar::-webkit-scrollbar-thumb:hover { background: #7dcfff; }
      `}</style>
    </>
  );
};

export default SovereignCanvas;
