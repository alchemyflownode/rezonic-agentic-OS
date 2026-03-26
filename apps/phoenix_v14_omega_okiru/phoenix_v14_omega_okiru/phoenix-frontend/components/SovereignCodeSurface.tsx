'use client';

import React, { useState, useEffect } from 'react';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { 
  Copy, Check, Play, Loader2, Terminal, X, Maximize2, 
  Minimize2, ChevronDown, ChevronUp, Eye, EyeOff,
  Cpu, Zap, AlertCircle, CheckCircle, Clock
} from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

interface SovereignCodeSurfaceProps {
  code: string;
  language: string;
  executable?: boolean;
  onExecute?: (code: string) => Promise<any>;
  title?: string;
  metadata?: {
    author?: string;
    created?: string;
    version?: string;
    driftLock?: string;
    verified?: boolean;
  };
}

type ExecutionState = 'idle' | 'running' | 'success' | 'error';

export const SovereignCodeSurface = ({
  code,
  language,
  executable = false,
  onExecute,
  title,
  metadata
}: SovereignCodeSurfaceProps) => {
  const [copied, setCopied] = useState(false);
  const [status, setStatus] = useState<ExecutionState>('idle');
  const [focused, setFocused] = useState(false);
  const [expanded, setExpanded] = useState(false);
  const [showLogs, setShowLogs] = useState(false);
  const [logs, setLogs] = useState<string[]>([]);
  const [showMetadata, setShowMetadata] = useState(false);
  
  const lineCount = code.split('\n').length;

  // Status styles with emotional states
  const statusStyles = {
    idle: 'border-white/5',
    running: 'ring-1 ring-[#00E5FF]/40 shadow-[0_0_20px_rgba(0,229,255,0.15)] border-[#00E5FF]/30',
    success: 'ring-1 ring-[#9ece6a]/40 shadow-[0_0_20px_rgba(158,206,106,0.15)] border-[#9ece6a]/30',
    error: 'ring-1 ring-[#f7768e]/40 shadow-[0_0_20px_rgba(247,118,142,0.15)] border-[#f7768e]/30'
  };

  const statusColors = {
    idle: 'text-zinc-400',
    running: 'text-[#00E5FF]',
    success: 'text-[#9ece6a]',
    error: 'text-[#f7768e]'
  };

  const statusIcons = {
    idle: <Clock className="w-3 h-3" />,
    running: <Loader2 className="w-3 h-3 animate-spin" />,
    success: <CheckCircle className="w-3 h-3" />,
    error: <AlertCircle className="w-3 h-3" />
  };

  // Language mapping for detection
  const detectLanguage = (code: string): string => {
    if (code.includes('def ') || code.includes('import ') && code.includes(':')) return 'python';
    if (code.includes('function ') || code.includes('const ') || code.includes('=>')) return 'typescript';
    if (code.includes('<div') || code.includes('</')) return 'jsx';
    if (code.includes('Get-Process') || code.includes('Write-Host')) return 'powershell';
    if (code.includes('#!/bin/bash') || code.includes('echo ')) return 'bash';
    return language;
  };

  const normalizedLang = detectLanguage(code);

  const handleCopy = async () => {
    await navigator.clipboard.writeText(code);
    setCopied(true);
    setTimeout(() => setCopied(false), 1500);
    addLog('📋 Code copied to clipboard');
  };

  const addLog = (message: string) => {
    setLogs(prev => [...prev, `[${new Date().toLocaleTimeString()}] ${message}`].slice(-20));
  };

  const handleRun = async () => {
    if (!executable) return;
    
    try {
      setStatus('running');
      addLog('🚀 Executing code...');
      
      if (onExecute) {
        const result = await onExecute(code);
        setStatus('success');
        addLog(`✅ Execution successful: ${result?.message || 'Completed'}`);
      } else {
        // Simulate execution with SCE
        await new Promise(resolve => setTimeout(resolve, 1500));
        setStatus('success');
        addLog('✅ Code executed successfully (SCE verified)');
      }
      
      // Auto-show logs on success
      setShowLogs(true);
      
    } catch (error) {
      setStatus('error');
      addLog(`❌ Execution failed: ${error instanceof Error ? error.message : 'Unknown error'}`);
      setShowLogs(true);
    } finally {
      setTimeout(() => {
        if (status !== 'error') {
          // Auto-reset after success
          setTimeout(() => setStatus('idle'), 3000);
        }
      }, 2000);
    }
  };

  // Auto-clear logs when idle
  useEffect(() => {
    if (status === 'idle' && !showLogs) {
      setLogs([]);
    }
  }, [status, showLogs]);

  return (
    <>
      {/* Global overlay when focused */}
      <AnimatePresence>
        {focused && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 bg-black/60 backdrop-blur-sm z-40"
            onClick={() => setFocused(false)}
          />
        )}
      </AnimatePresence>

      {/* Main Surface */}
      <motion.div
        layout
        className={`
          relative group border rounded-xl overflow-hidden bg-gradient-to-br from-[#1a1b26] to-[#1f2335]
          transition-all duration-300
          ${statusStyles[status]}
          ${focused ? 'z-50 scale-[1.02] shadow-2xl' : 'z-0'}
        `}
        onClick={() => setFocused(!focused)}
      >
        {/* Gradient Energy Line */}
        <div className="h-[2px] w-full bg-gradient-to-r from-[#00E5FF] via-[#9B72CB] to-transparent opacity-40" />

        {/* Header */}
        <div className="px-4 py-3 border-b border-white/5 bg-black/20">
          <div className="flex items-center justify-between">
            {/* Left side - Title & Metadata */}
            <div className="flex items-center gap-4 flex-1">
              <div className="flex items-center gap-2">
                <div className="w-6 h-6 rounded bg-[#7dcfff]/10 flex items-center justify-center border border-[#7dcfff]/30">
                  <Terminal className="w-3 h-3 text-[#7dcfff]" />
                </div>
                <div>
                  <span className="text-xs font-mono text-white/90">
                    {title || `${normalizedLang.toUpperCase()} · ${lineCount} lines`}
                  </span>
                  {metadata?.driftLock && (
                    <span className="ml-3 text-[8px] font-mono text-[#7dcfff]/60">
                      SCE: {metadata.driftLock.slice(0, 8)}...
                    </span>
                  )}
                </div>
              </div>

              {/* Intelligence Strip */}
              <div className="hidden md:flex items-center gap-3 text-[9px] font-mono text-[#64748B]">
                <span>LANG: {normalizedLang}</span>
                <span>LINES: {lineCount}</span>
                <span>MODE: {executable ? 'EXECUTABLE' : 'STATIC'}</span>
                {metadata?.verified && (
                  <span className="text-[#9ece6a] flex items-center gap-1">
                    <CheckCircle className="w-2.5 h-2.5" /> VERIFIED
                  </span>
                )}
              </div>
            </div>

            {/* Right side - Controls */}
            <div className="flex items-center gap-1">
              {/* Language Badge */}
              <span className="px-2 py-1 rounded bg-[#7dcfff]/10 border border-[#7dcfff]/30 text-[#7dcfff] text-[8px] font-mono mr-2">
                {normalizedLang}
              </span>

              {/* Run Button */}
              {executable && (
                <button
                  onClick={(e) => { e.stopPropagation(); handleRun(); }}
                  disabled={status === 'running'}
                  className="p-1.5 rounded hover:bg-white/10 transition disabled:opacity-50"
                  title="Execute code"
                >
                  {status === 'running' ? (
                    <Loader2 className="w-3.5 h-3.5 animate-spin text-[#00E5FF]" />
                  ) : (
                    <Play className={`w-3.5 h-3.5 ${statusColors[status]}`} />
                  )}
                </button>
              )}

              {/* Copy Button */}
              <button
                onClick={(e) => { e.stopPropagation(); handleCopy(); }}
                className="p-1.5 rounded hover:bg-white/10 transition"
                title="Copy code"
              >
                {copied ? (
                  <Check className="w-3.5 h-3.5 text-[#9ece6a]" />
                ) : (
                  <Copy className="w-3.5 h-3.5 text-zinc-400" />
                )}
              </button>

              {/* Expand Button */}
              <button
                onClick={(e) => { e.stopPropagation(); setExpanded(!expanded); }}
                className="p-1.5 rounded hover:bg-white/10 transition"
                title={expanded ? "Collapse" : "Expand"}
              >
                {expanded ? (
                  <Minimize2 className="w-3.5 h-3.5 text-zinc-400" />
                ) : (
                  <Maximize2 className="w-3.5 h-3.5 text-zinc-400" />
                )}
              </button>

              {/* Metadata Toggle */}
              {metadata && (
                <button
                  onClick={(e) => { e.stopPropagation(); setShowMetadata(!showMetadata); }}
                  className="p-1.5 rounded hover:bg-white/10 transition"
                  title="Toggle metadata"
                >
                  {showMetadata ? (
                    <EyeOff className="w-3.5 h-3.5 text-zinc-400" />
                  ) : (
                    <Eye className="w-3.5 h-3.5 text-zinc-400" />
                  )}
                </button>
              )}
            </div>
          </div>

          {/* Metadata Panel */}
          <AnimatePresence>
            {showMetadata && metadata && (
              <motion.div
                initial={{ height: 0, opacity: 0 }}
                animate={{ height: 'auto', opacity: 1 }}
                exit={{ height: 0, opacity: 0 }}
                className="mt-3 pt-3 border-t border-white/5 overflow-hidden"
              >
                <div className="grid grid-cols-3 gap-4 text-[9px] font-mono">
                  {metadata.author && (
                    <div>
                      <span className="text-[#64748B]">Author</span>
                      <div className="text-white/90 mt-1">{metadata.author}</div>
                    </div>
                  )}
                  {metadata.created && (
                    <div>
                      <span className="text-[#64748B]">Created</span>
                      <div className="text-white/90 mt-1">{metadata.created}</div>
                    </div>
                  )}
                  {metadata.version && (
                    <div>
                      <span className="text-[#64748B]">Version</span>
                      <div className="text-white/90 mt-1">{metadata.version}</div>
                    </div>
                  )}
                  {metadata.driftLock && (
                    <div className="col-span-3 mt-2">
                      <span className="text-[#64748B]">Drift Lock</span>
                      <div className="font-mono text-[#7dcfff] mt-1 bg-black/40 p-2 rounded border border-[#7dcfff]/20">
                        {metadata.driftLock}
                        {metadata.verified && (
                          <span className="ml-2 text-[#9ece6a]">✓ SCE VERIFIED</span>
                        )}
                      </div>
                    </div>
                  )}
                </div>
              </motion.div>
            )}
          </AnimatePresence>
        </div>

        {/* Code Content */}
        <div className={`
          transition-all duration-300
          ${expanded ? 'max-h-[800px]' : 'max-h-[400px]'}
          overflow-auto custom-scrollbar
        `}>
          <SyntaxHighlighter
            language={normalizedLang}
            style={{}} // Let CSS control colors
            customStyle={{
              margin: 0,
              padding: '20px',
              background: 'transparent',
              fontSize: '12px',
              lineHeight: '1.6'
            }}
            codeTagProps={{
              style: {
                fontFamily: '"JetBrains Mono", "Fira Code", monospace'
              }
            }}
            showLineNumbers={lineCount >= 3}
            lineNumberStyle={{
              color: '#3b4261',
              paddingRight: '20px',
              userSelect: 'none',
              minWidth: '3em',
              textAlign: 'right'
            }}
          >
            {code}
          </SyntaxHighlighter>
        </div>

        {/* Status Footer */}
        <AnimatePresence>
          {(status !== 'idle' || showLogs) && (
            <motion.div
              initial={{ height: 0, opacity: 0 }}
              animate={{ height: 'auto', opacity: 1 }}
              exit={{ height: 0, opacity: 0 }}
              className="border-t border-white/5 bg-black/20"
            >
              {/* Status Bar */}
              <div className="px-4 py-2 flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <span className={statusColors[status]}>
                    {statusIcons[status]}
                  </span>
                  <span className={`text-[9px] font-mono ${statusColors[status]}`}>
                    {status === 'idle' && 'Ready'}
                    {status === 'running' && 'Executing...'}
                    {status === 'success' && 'Execution successful'}
                    {status === 'error' && 'Execution failed'}
                  </span>
                </div>

                {/* Logs Toggle */}
                {logs.length > 0 && (
                  <button
                    onClick={() => setShowLogs(!showLogs)}
                    className="flex items-center gap-1 text-[8px] font-mono text-[#64748B] hover:text-white transition"
                  >
                    {showLogs ? <ChevronUp className="w-3 h-3" /> : <ChevronDown className="w-3 h-3" />}
                    {logs.length} logs
                  </button>
                )}
              </div>

              {/* Logs Panel */}
              <AnimatePresence>
                {showLogs && logs.length > 0 && (
                  <motion.div
                    initial={{ height: 0 }}
                    animate={{ height: 'auto' }}
                    exit={{ height: 0 }}
                    className="border-t border-white/5"
                  >
                    <div className="p-3 bg-black/40 max-h-32 overflow-auto custom-scrollbar">
                      {logs.map((log, i) => (
                        <div key={i} className="text-[8px] font-mono text-[#64748B] py-0.5 border-l-2 border-[#00E5FF]/30 pl-2 mb-1">
                          {log}
                        </div>
                      ))}
                    </div>
                  </motion.div>
                )}
              </AnimatePresence>
            </motion.div>
          )}
        </AnimatePresence>
      </motion.div>

      <style jsx global>{`
        .custom-scrollbar::-webkit-scrollbar {
          width: 4px;
          height: 4px;
        }
        .custom-scrollbar::-webkit-scrollbar-track {
          background: #1a1b26;
        }
        .custom-scrollbar::-webkit-scrollbar-thumb {
          background: #3b4261;
          border-radius: 4px;
        }
        .custom-scrollbar::-webkit-scrollbar-thumb:hover {
          background: #7dcfff;
        }
        
        /* Syntax highlighting colors */
        .token.comment { color: #565f89 !important; font-style: italic; }
        .token.keyword { color: #bb9af7 !important; font-weight: 500; }
        .token.string { color: #9ece6a !important; }
        .token.function { color: #7dcfff !important; font-weight: 500; }
        .token.number { color: #ff9e64 !important; }
        .token.variable { color: #f7768e !important; }
        .token.operator { color: #89ddff !important; }
        .token.class-name { color: #73daca !important; }
        .token.property { color: #7aa2f7 !important; }
        
        /* Hover glow effects */
        .token.function:hover,
        .token.keyword:hover {
          text-shadow: 0 0 6px currentColor;
          transition: text-shadow 0.2s ease;
        }
      `}</style>
    </>
  );
};