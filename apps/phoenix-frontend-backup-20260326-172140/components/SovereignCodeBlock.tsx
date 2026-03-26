$livingCodeBlock = @'
// components/SovereignCodeBlock.tsx - 2026 Living Code Canvas

'use client';

import React, { useState, useRef } from 'react';
import { motion, useMotionValue, useSpring } from 'framer-motion';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { oneDark } from 'react-syntax-highlighter/dist/esm/styles/prism';
import { Copy, Check, Terminal, Sparkles, Maximize2, Minimize2, Cpu } from 'lucide-react';

interface CodeBlockProps {
  code: string;
  language: string;
  title?: string;
  showLineNumbers?: boolean;
  executable?: boolean;
  onExecute?: () => void;
  driftLock?: string;
}

export const SovereignCodeBlock: React.FC<CodeBlockProps> = ({
  code,
  language,
  title,
  showLineNumbers = true,
  executable = false,
  onExecute,
  driftLock,
}) => {
  const [copied, setCopied] = useState(false);
  const [expanded, setExpanded] = useState(false);
  const [hovered, setHovered] = useState(false);
  const lines = code.split('\n').length;
  const containerRef = useRef<HTMLDivElement>(null);
  const glowX = useMotionValue(0);
  const glowY = useMotionValue(0);
  
  const springX = useSpring(glowX, { stiffness: 300, damping: 30 });
  const springY = useSpring(glowY, { stiffness: 300, damping: 30 });

  const handleCopy = async () => {
    await navigator.clipboard.writeText(code);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleMouseMove = (e: React.MouseEvent) => {
    const rect = e.currentTarget.getBoundingClientRect();
    glowX.set((e.clientX - rect.left) / rect.width);
    glowY.set((e.clientY - rect.top) / rect.height);
  };

  return (
    <motion.div
      ref={containerRef}
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ type: "spring", stiffness: 500, damping: 30 }}
      className="relative group my-4"
      onMouseMove={handleMouseMove}
      onMouseEnter={() => setHovered(true)}
      onMouseLeave={() => setHovered(false)}
    >
      {/* Animated Energy Field */}
      <motion.div
        className="absolute -inset-1 rounded-xl blur-2xl opacity-0 group-hover:opacity-100 transition-opacity duration-500"
        style={{
          background: `radial-gradient(circle at ${springX.get() * 100}% ${springY.get() * 100}%, rgba(125,207,255,0.4), rgba(155,114,203,0.2), transparent)`,
        }}
      />
      
      {/* Main Container */}
      <div className="relative rounded-xl overflow-hidden border border-[#7dcfff]/20 shadow-2xl bg-gradient-to-br from-[#0a0a0c] to-[#050505] backdrop-blur-sm">
        
        {/* Header with Live Energy Bar */}
        <div className="bg-gradient-to-r from-[#1a1b26] via-[#1f2335] to-[#1a1b26] px-4 py-2.5 border-b border-[#7dcfff]/20">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              {/* Animated Terminal Dots */}
              <div className="flex gap-1.5">
                {[...Array(3)].map((_, i) => (
                  <motion.div
                    key={i}
                    animate={{ scale: [1, 1.2, 1] }}
                    transition={{ duration: 1.5, repeat: Infinity, delay: i * 0.2 }}
                    className={`w-2.5 h-2.5 rounded-full ${
                      i === 0 ? 'bg-[#f7768e]' : i === 1 ? 'bg-[#e0af68]' : 'bg-[#9ece6a]'
                    }`}
                  />
                ))}
              </div>
              
              <motion.div
                animate={{ rotate: [0, 5, 0, -5, 0] }}
                transition={{ duration: 3, repeat: Infinity }}
              >
                <Terminal className="w-3.5 h-3.5 text-[#7dcfff]" />
              </motion.div>
              
              <span className="text-[10px] font-mono text-[#7dcfff] uppercase tracking-wider flex items-center gap-2">
                {language}
                {executable && (
                  <span className="text-[7px] text-[#9ece6a] bg-[#9ece6a]/20 px-1.5 py-0.5 rounded-full flex items-center gap-1">
                    <Cpu className="w-2 h-2" />
                    executable
                  </span>
                )}
              </span>
              
              {driftLock && (
                <motion.div
                  initial={{ scale: 0 }}
                  animate={{ scale: 1 }}
                  className="flex items-center gap-1 px-2 py-0.5 rounded-full bg-[#9ece6a]/10 border border-[#9ece6a]/30"
                >
                  <ShieldCheck className="w-2.5 h-2.5 text-[#9ece6a]" />
                  <span className="text-[7px] font-mono text-[#9ece6a]">SCE</span>
                </motion.div>
              )}
            </div>
            
            <div className="flex items-center gap-2">
              <motion.div
                animate={{ opacity: [0.5, 1, 0.5] }}
                transition={{ duration: 2, repeat: Infinity }}
                className="text-[8px] font-mono text-[#565f89] flex items-center gap-1"
              >
                <Sparkles className="w-2.5 h-2.5" />
                {lines} lines
              </motion.div>
              
              <motion.button
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
                onClick={() => setExpanded(!expanded)}
                className="px-2 py-1 rounded-lg text-[8px] font-mono text-[#7dcfff] hover:bg-white/10 transition-all"
              >
                {expanded ? <Minimize2 className="w-3 h-3" /> : <Maximize2 className="w-3 h-3" />}
              </motion.button>
              
              {executable && (
                <motion.button
                  whileHover={{ scale: 1.05 }}
                  whileTap={{ scale: 0.95 }}
                  onClick={onExecute}
                  className="px-3 py-1.5 rounded-lg bg-gradient-to-r from-[#7dcfff]/20 to-[#9B72CB]/20 border border-[#7dcfff]/30 text-[#7dcfff] text-[9px] font-mono hover:shadow-lg transition-all flex items-center gap-1"
                >
                  <Play className="w-2.5 h-2.5" />
                  Run
                </motion.button>
              )}
              
              <motion.button
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
                onClick={handleCopy}
                className="p-1.5 rounded-lg bg-[#1a1b26] border border-[#7dcfff]/30 text-[#7dcfff] hover:bg-[#7dcfff]/10 transition-all"
              >
                {copied ? <Check className="w-3.5 h-3.5" /> : <Copy className="w-3.5 h-3.5" />}
              </motion.button>
            </div>
          </div>
          
          {/* Live Energy Bar */}
          <div className="absolute bottom-0 left-0 right-0 h-[1px] bg-gradient-to-r from-transparent via-[#7dcfff] to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-300" />
        </div>
        
        {/* Code with Live Highlight */}
        <motion.div 
          className={expanded ? 'max-h-[70vh]' : 'max-h-[500px]'}
          animate={{ height: 'auto' }}
          transition={{ duration: 0.3 }}
        >
          <SyntaxHighlighter
            language={language.toLowerCase()}
            style={oneDark}
            showLineNumbers={showLineNumbers && lines >= 3}
            wrapLines={true}
            customStyle={{
              margin: 0,
              padding: "1.5rem",
              background: "linear-gradient(135deg, #1a1b26 0%, #1f2335 100%)",
              fontSize: "13px",
              fontFamily: "'JetBrains Mono', 'Fira Code', monospace",
              lineHeight: "1.6",
            }}
            lineNumberStyle={{
              color: "#565f89",
              paddingRight: "1.2rem",
              borderRight: "1px solid rgba(125,207,255,0.2)",
              marginRight: "1.2rem",
            }}
          >
            {code}
          </SyntaxHighlighter>
        </motion.div>
        
        {/* Animated Gradient Border on Hover */}
        {hovered && (
          <motion.div
            className="absolute inset-0 rounded-xl pointer-events-none"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ duration: 0.3 }}
            style={{
              background: `radial-gradient(circle at ${springX.get() * 100}% ${springY.get() * 100}%, rgba(125,207,255,0.08), transparent)`,
            }}
          />
        )}
      </div>
    </motion.div>
  );
};

export default SovereignCodeBlock;
'@

$livingCodeBlock | Out-File -FilePath "D:\Rezonic_Agentic\apps\phoenix-frontend\components\SovereignCodeBlock.tsx" -Encoding utf8

Write-Host "✅ SovereignCodeBlock upgraded to 2026 Living Code Canvas!" -ForegroundColor Green