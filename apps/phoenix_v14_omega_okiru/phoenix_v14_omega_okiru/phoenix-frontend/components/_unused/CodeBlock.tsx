import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Copy, Check, Download, Expand, Shrink } from 'lucide-react';

interface CodeBlockProps {
  language: string;
  code: string;
  sce?: {
    verified: boolean;
    driftLock?: string;
  };
}

export const CodeBlock: React.FC<CodeBlockProps> = ({ language, code, sce }) => {
  const [copied, setCopied] = useState(false);
  const [expanded, setExpanded] = useState(false);

  const handleCopy = () => {
    navigator.clipboard.writeText(code);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleDownload = () => {
    const blob = new Blob([code], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `code.${language || 'txt'}`;
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="my-4 rounded-xl overflow-hidden border border-white/10 bg-[#0D1117] font-mono">
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-2 bg-black/30 border-b border-white/5">
        <div className="flex items-center gap-3">
          {/* Language Badge */}
          <span className="px-2 py-0.5 text-[9px] font-bold uppercase tracking-wider rounded bg-gradient-to-r from-[#00E5FF]/20 to-[#9B72CB]/20 text-[#00E5FF] border border-[#00E5FF]/20">
            {language || 'code'}
          </span>
          
          {/* SCE Badge */}
          {sce && (
            <span className={`flex items-center gap-1 px-2 py-0.5 rounded text-[8px] font-bold uppercase ${
              sce.verified 
                ? 'bg-[#00e676]/10 text-[#00e676] border border-[#00e676]/20' 
                : 'bg-red-500/10 text-red-400 border border-red-500/20'
            }`}>
              <span className={`w-1.5 h-1.5 rounded-full ${sce.verified ? 'bg-[#00e676]' : 'bg-red-400'}`} />
              {sce.verified ? 'SCE VERIFIED' : 'SCE FAILED'}
            </span>
          )}
        </div>

        {/* Actions */}
        <div className="flex items-center gap-2">
          <button onClick={handleDownload} className="p-1.5 rounded hover:bg-white/10 text-zinc-500 hover:text-white transition-colors">
            <Download size={14} />
          </button>
          <button onClick={() => setExpanded(!expanded)} className="p-1.5 rounded hover:bg-white/10 text-zinc-500 hover:text-white transition-colors">
            {expanded ? <Shrink size={14} /> : <Expand size={14} />}
          </button>
          <button onClick={handleCopy} className="p-1.5 rounded hover:bg-white/10 text-zinc-500 hover:text-white transition-colors">
            <AnimatePresence mode="wait" initial={false}>
              {copied ? (
                <motion.div key="check" initial={{ scale: 0 }} animate={{ scale: 1 }} exit={{ scale: 0 }}>
                  <Check size={14} className="text-[#00e676]" />
                </motion.div>
              ) : (
                <motion.div key="copy" initial={{ scale: 0 }} animate={{ scale: 1 }} exit={{ scale: 0 }}>
                  <Copy size={14} />
                </motion.div>
              )}
            </AnimatePresence>
          </button>
        </div>
      </div>

      {/* Code Content */}
      <div className={`relative overflow-auto custom-scrollbar ${expanded ? 'max-h-[80vh]' : 'max-h-64'}`}>
        <pre className="p-4 text-[11px] leading-relaxed text-zinc-300">
          <code>{code}</code>
        </pre>
      </div>
    </div>
  );
};