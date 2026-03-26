'use client'
import React, { useState, useEffect, useCallback } from 'react';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { vscDarkPlus } from 'react-syntax-highlighter/dist/esm/styles/prism';
import { 
  Check, Copy, Download, Maximize2, X, Brain, Shield, 
  FileText, ChevronDown, ChevronUp
} from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

interface SCEContext {
  verified: boolean;
  driftLock?: string;
  narrative?: string[];
}

interface SovereignCodeBlockProps {
  language: string;
  code: string;
  sce?: SCEContext | null;
  className?: string;
  showLineNumbers?: boolean;
  wrapLines?: boolean;
}

export const SovereignCodeBlock = ({ 
  language = 'text',
  code,
  sce,
  className = '',
  showLineNumbers = true,
  wrapLines = true 
}: SovereignCodeBlockProps) => {
  const [copied, setCopied] = useState(false);
  const [isExpanded, setIsExpanded] = useState(false);
  const [showNarrative, setShowNarrative] = useState(false);
  const lineCount = code.split('\n').length;

  const languageMap: Record<string, string> = {
    js: 'javascript', ts: 'typescript', tsx: 'typescript', jsx: 'javascript',
    py: 'python', rb: 'ruby', sh: 'bash', bash: 'bash', ps1: 'powershell',
    json: 'json', yaml: 'yaml', yml: 'yaml', html: 'html', css: 'css',
    scss: 'scss', sql: 'sql', go: 'go', rs: 'rust', rust: 'rust',
    java: 'java', c: 'c', cpp: 'cpp', 'c++': 'cpp', php: 'php',
    md: 'markdown', markdown: 'markdown',
  };

  const normalizedLang = languageMap[language?.toLowerCase()] || language || 'text';

  const langColors: Record<string, string> = {
    javascript: 'from-yellow-500 to-yellow-600', typescript: 'from-blue-500 to-blue-600',
    python: 'from-blue-400 to-cyan-500', bash: 'from-green-500 to-green-600', powershell: 'from-purple-500 to-purple-600',
    json: 'from-orange-500 to-orange-600', html: 'from-red-500 to-red-600', css: 'from-pink-500 to-pink-600',
    rust: 'from-orange-600 to-red-600', go: 'from-cyan-400 to-blue-500',
    java: 'from-red-600 to-orange-500', sql: 'from-blue-600 to-indigo-600',
    markdown: 'from-gray-500 to-gray-600', scss: 'from-pink-600 to-purple-600',
    php: 'from-indigo-500 to-purple-500', c: 'from-blue-700 to-blue-800',
    cpp: 'from-blue-600 to-purple-600', text: 'from-gray-600 to-gray-700'
  };

  const bgGradient = langColors[normalizedLang] || 'from-cyan-500 to-blue-500';

  const copyToClipboard = useCallback(async () => {
    try {
      await navigator.clipboard.writeText(code);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch (err) {
      console.error('Failed to copy:', err);
    }
  }, [code]);

  const downloadCode = useCallback(() => {
    const extensions: Record<string, string> = {
      javascript: 'js', typescript: 'ts', python: 'py', bash: 'sh',
      powershell: 'ps1', json: 'json', yaml: 'yml', html: 'html',
      css: 'css', scss: 'scss', rust: 'rs', go: 'go', java: 'java',
      cpp: 'cpp', c: 'c', php: 'php', sql: 'sql', markdown: 'md',
    };

    const ext = extensions[normalizedLang] || 'txt';
    const filename = sovereign__.;

    const element = document.createElement('a');
    const file = new Blob([code], { type: 'text/plain;charset=utf-8' });
    element.href = URL.createObjectURL(file);
    element.download = filename;
    document.body.appendChild(element);
    element.click();
    document.body.removeChild(element);
    URL.revokeObjectURL(element.href);
  }, [code, normalizedLang]);

  useEffect(() => {
    if (!isExpanded) return;
    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === 'Escape') setIsExpanded(false);
    };
    window.addEventListener('keydown', handleEscape);
    return () => window.removeEventListener('keydown', handleEscape);
  }, [isExpanded]);

  // FIX: Use sce?.narrative instead of narrative
  const hasNarrative = sce?.narrative && sce.narrative.length > 0;

  return (
    <>
      <AnimatePresence>
        {isExpanded && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 bg-[#050505]/90 backdrop-blur-md z-[100] transition-opacity"
            onClick={() => setIsExpanded(false)}
          />
        )}
      </AnimatePresence>

      <div
        className={
          my-6 rounded-xl overflow-hidden border border-[#2A2E38] 
          bg-gradient-to-br from-[#0A0C10] to-[#12141A] 
          shadow-2xl transition-all duration-300 hover:shadow-[0_0_20px_rgba(0,229,255,0.1)]
          
          
        }
      >
        <div className="flex items-center justify-between px-4 py-2.5 bg-[#1A1D23]/80 border-b border-[#2A2E38]/50 backdrop-blur-md">
          <div className="flex items-center gap-3 flex-wrap">
            <span className={
              text-[10px] font-bold uppercase tracking-widest px-3 py-1.5 rounded-full
              bg-gradient-to-r  text-white shadow-sm border border-white/20
            }>
              {normalizedLang}
            </span>
            
            <span className="text-[9px] text-[#8A8F9B] font-mono tracking-wider hidden md:inline">
              {lineCount} {lineCount === 1 ? 'LINE' : 'LINES'}
            </span>

            {sce && (
              <span className={
                flex items-center gap-1 px-2.5 py-1 rounded-full text-[8px] font-bold uppercase
                border shadow-sm
                
              }>
                {sce.verified ? (
                  <>
                    <span className="w-1.5 h-1.5 rounded-full bg-[#00E676] shadow-[0_0_8px_#00E676]" />
                    SCE VERIFIED
                  </>
                ) : (
                  <>
                    <span className="w-1.5 h-1.5 rounded-full bg-red-400 shadow-[0_0_8px_#ef4444]" />
                    SCE DRIFTED
                  </>
                )}
                {sce.driftLock && (
                  <span className="ml-1 text-[7px] font-mono opacity-80">
                    {sce.driftLock.slice(0, 8)}...
                  </span>
                )}
              </span>
            )}
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={downloadCode}
              className="p-1.5 rounded hover:bg-white/10 text-[#8A8F9B] hover:text-white transition-all border border-transparent hover:border-[#2A2E38] group"
            >
              <Download size={14} className="group-hover:-translate-y-0.5 transition-transform" />
            </button>

            <button
              onClick={() => setIsExpanded(!isExpanded)}
              className="p-1.5 rounded hover:bg-white/10 text-[#8A8F9B] hover:text-white transition-all border border-transparent hover:border-[#2A2E38] group"
            >
              {isExpanded ? <X size={14} /> : <Maximize2 size={14} />}
            </button>

            <motion.button
              onClick={copyToClipboard}
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              className={
                flex items-center gap-1.5 px-4 py-1.5 rounded-full text-[9px] font-mono font-bold uppercase tracking-widest
                transition-all shadow-sm border hover:shadow-lg
                
              }
            >
              {copied ? <><Check size={12} /> COPIED</> : <><Copy size={12} /> COPY</>}
            </motion.button>
          </div>
        </div>

        <div className={lex-1 overflow-auto custom-scrollbar }>
          <SyntaxHighlighter
            language={normalizedLang}
            style={vscDarkPlus}
            customStyle={{
              margin: 0,
              padding: '1.5rem',
              background: 'transparent',
              fontSize: '13px',
              lineHeight: '1.65',
            }}
            wrapLines={wrapLines}
            wrapLongLines={true}
            showLineNumbers={showLineNumbers && lineCount >= 3}
            lineNumberStyle={{
              color: '#6B7280',
              paddingRight: '1.75rem',
              userSelect: 'none',
              minWidth: '3.5em',
              textAlign: 'right',
              fontSize: '12px',
            }}
          >
            {code}
          </SyntaxHighlighter>
        </div>

        {hasNarrative && (
          <motion.div
            initial={false}
            animate={{ height: showNarrative ? 'auto' : 0 }}
            className="border-t border-[#2A2E38]/50 overflow-hidden"
          >
            <button 
              onClick={() => setShowNarrative(!showNarrative)}
              className="w-full px-4 py-2.5 text-[10px] text-zinc-400 hover:text-zinc-200 flex items-center gap-2 font-mono tracking-wider transition-colors bg-[#0A0C10]/80 hover:bg-[#0A0C10]"
            >
              <Shield size={12} />
              {showNarrative ? <ChevronUp size={12} /> : <ChevronDown size={12} />}
              {showNarrative ? 'HIDE SCE NARRATIVE' : 'SHOW SCE NARRATIVE'} ({sce.narrative?.length || 0} entries)
            </button>
            
            <AnimatePresence>
              {showNarrative && sce.narrative && (
                <motion.div 
                  initial={{ opacity: 0, height: 0 }}
                  animate={{ opacity: 1, height: 'auto' }}
                  exit={{ opacity: 0, height: 0 }}
                  className="px-4 pb-4 pt-2 space-y-2 max-h-40 overflow-y-auto custom-scrollbar"
                >
                  {sce.narrative.map((entry, index) => (
                    <div 
                      key={index} 
                      className="text-[10px] text-zinc-400 italic leading-relaxed p-2 bg-black/20 rounded border border-zinc-700/30"
                    >
                      "{entry}"
                    </div>
                  ))}
                  {sce.driftLock && (
                    <div className="pt-3 mt-3 border-t border-zinc-700/30 text-[9px] font-mono text-[#00E5FF]/70 flex items-center gap-2">
                      <span>DRIFT_LOCK:</span>
                      <span className="font-bold">{sce.driftLock.slice(0, 16)}...</span>
                      <Check size={10} className="text-[#00E676] ml-auto" />
                    </div>
                  )}
                </motion.div>
              )}
            </AnimatePresence>
          </motion.div>
        )}
      </div>
    </>
  );
};
