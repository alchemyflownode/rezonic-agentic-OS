'use client';

import React, { useState, useRef, useEffect } from 'react';
import { motion, AnimatePresence, useMotionValue, useSpring } from 'framer-motion';
import { ShieldCheck, Copy, Check, Terminal, User, Bot, Sparkles, Zap } from 'lucide-react';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { oneDark } from 'react-syntax-highlighter/dist/esm/styles/prism';

// ==========================================
// 2026 LIVING COMPONENTS
// ==========================================

interface ContentPart {
  type: 'text' | 'code';
  content?: string;
  language?: string;
  code?: string;
}

// Enhanced parse with drift-aware highlighting
const parseContent = (content: string, driftLock?: string): ContentPart[] => {
  if (!content) return [{ type: 'text', content: '' }];
  
  const parts: ContentPart[] = [];
  const codeBlockRegex = /```(\w+)?\n([\s\S]*?)```/g;
  let lastIndex = 0;
  let match;
  
  while ((match = codeBlockRegex.exec(content)) !== null) {
    if (match.index > lastIndex) {
      const text = content.slice(lastIndex, match.index);
      if (text.trim()) {
        parts.push({ type: 'text', content: text });
      }
    }
    
    parts.push({
      type: 'code',
      language: match[1] || 'python',
      code: match[2].trim()
    });
    
    lastIndex = match.index + match[0].length;
  }
  
  if (lastIndex < content.length) {
    const text = content.slice(lastIndex);
    if (text.trim()) {
      parts.push({ type: 'text', content: text });
    }
  }
  
  return parts.length > 0 ? parts : [{ type: 'text', content }];
};

// 2026 Code Block with Live Effects
const CodeBlock = ({ code, language, driftLock }: { code: string; language: string; driftLock?: string }) => {
  const [copied, setCopied] = useState(false);
  const [expanded, setExpanded] = useState(false);
  const [hovered, setHovered] = useState(false);
  const lines = code.split('\n').length;
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
      initial={{ opacity: 0, y: 20, scale: 0.98 }}
      animate={{ opacity: 1, y: 0, scale: 1 }}
      transition={{ type: "spring", stiffness: 500, damping: 30 }}
      className="relative group my-4"
      onMouseMove={handleMouseMove}
      onMouseEnter={() => setHovered(true)}
      onMouseLeave={() => setHovered(false)}
    >
      {/* Animated Glow Effect */}
      <motion.div
        className="absolute -inset-0.5 rounded-xl blur-xl opacity-0 group-hover:opacity-100 transition-opacity duration-300"
        style={{
          background: `radial-gradient(circle at ${springX.get() * 100}% ${springY.get() * 100}%, rgba(125,207,255,0.3), rgba(155,114,203,0.1), transparent)`,
        }}
      />
      
      <div className="relative rounded-xl overflow-hidden border border-[#7dcfff]/20 shadow-2xl bg-[#0a0a0c]/90 backdrop-blur-sm">
        {/* Header with Live Indicator */}
        <div className="bg-gradient-to-r from-[#1a1b26] to-[#1f2335] px-4 py-2 border-b border-[#7dcfff]/20 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="flex gap-1.5">
              <motion.div 
                animate={{ scale: [1, 1.1, 1] }}
                transition={{ duration: 2, repeat: Infinity }}
                className="w-2.5 h-2.5 rounded-full bg-[#f7768e]" 
              />
              <div className="w-2.5 h-2.5 rounded-full bg-[#e0af68]" />
              <div className="w-2.5 h-2.5 rounded-full bg-[#9ece6a]" />
            </div>
            <Terminal className="w-3.5 h-3.5 text-[#7dcfff] animate-pulse" />
            <span className="text-[10px] font-mono text-[#7dcfff] uppercase tracking-wider">
              {language}
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
          <div className="flex items-center gap-3">
            <span className="text-[8px] font-mono text-[#565f89] flex items-center gap-1">
              <Zap className="w-2.5 h-2.5" />
              {lines} lines
            </span>
            <button
              onClick={() => setExpanded(!expanded)}
              className="text-[8px] font-mono text-[#7dcfff] hover:text-white transition px-2 py-1 rounded hover:bg-white/10"
            >
              {expanded ? 'Collapse' : 'Expand'}
            </button>
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
        
        {/* Code with Live Highlight */}
        <motion.div 
          className={expanded ? 'max-h-[600px]' : 'max-h-[400px]'}
          animate={{ opacity: 1 }}
          transition={{ duration: 0.2 }}
        >
          <SyntaxHighlighter
            language={language.toLowerCase()}
            style={oneDark}
            showLineNumbers={lines >= 3}
            wrapLines={true}
            customStyle={{
              margin: 0,
              padding: "1.2rem",
              background: "linear-gradient(135deg, #1a1b26 0%, #1f2335 100%)",
              fontSize: "13px",
              fontFamily: "'JetBrains Mono', 'Fira Code', monospace",
              lineHeight: "1.6",
            }}
            lineNumberStyle={{
              color: "#565f89",
              paddingRight: "1.2rem",
              borderRight: "1px solid rgba(125,207,255,0.15)",
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
            transition={{ duration: 0.2 }}
            style={{
              background: `radial-gradient(circle at ${springX.get() * 100}% ${springY.get() * 100}%, rgba(125,207,255,0.1), transparent)`,
            }}
          />
        )}
      </div>
    </motion.div>
  );
};

// 2026 Living Message Bubble
export const SovereignMessage: React.FC<{
  content: string;
  role: 'user' | 'assistant' | 'system';
  isStreaming?: boolean;
  driftLock?: string;
  timestamp?: string;
}> = ({ content, role, isStreaming = false, driftLock, timestamp }) => {
  const parts = parseContent(content, driftLock);
  const [isTyping, setIsTyping] = useState(false);
  
  // Simulate typing effect for streaming
  useEffect(() => {
    if (isStreaming) {
      setIsTyping(true);
      const timer = setTimeout(() => setIsTyping(false), 500);
      return () => clearTimeout(timer);
    }
  }, [isStreaming, content]);

  const getContainerClass = () => {
    if (role === 'user') {
      return 'bg-gradient-to-r from-[#7dcfff]/15 to-[#9B72CB]/15 border border-[#7dcfff]/30 rounded-2xl rounded-br-sm backdrop-blur-sm';
    }
    if (role === 'system') {
      return 'bg-[#565f89]/10 border border-[#565f89]/30 rounded-2xl rounded-bl-sm backdrop-blur-sm';
    }
    return 'bg-gradient-to-r from-white/5 to-white/3 border border-white/10 rounded-2xl rounded-bl-sm backdrop-blur-sm';
  };

  const getIcon = () => {
    if (role === 'user') return <User className="w-3.5 h-3.5" />;
    if (role === 'system') return <ShieldCheck className="w-3.5 h-3.5" />;
    return <Bot className="w-3.5 h-3.5" />;
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 20, scale: 0.95 }}
      animate={{ opacity: 1, y: 0, scale: 1 }}
      exit={{ opacity: 0, scale: 0.95 }}
      transition={{ type: "spring", stiffness: 500, damping: 30 }}
      className={`p-5 ${getContainerClass()} relative overflow-hidden group`}
    >
      {/* Live Particle Effect */}
      {isStreaming && (
        <div className="absolute inset-0 pointer-events-none">
          {[...Array(8)].map((_, i) => (
            <motion.div
              key={i}
              className="absolute w-1 h-1 rounded-full bg-[#7dcfff]/30"
              initial={{ x: -20, y: Math.random() * 100 }}
              animate={{ x: '100%', y: Math.random() * 100 }}
              transition={{ duration: Math.random() * 2 + 1, repeat: Infinity, delay: i * 0.2 }}
            />
          ))}
        </div>
      )}
      
      {/* Header */}
      <div className="flex items-center gap-2 mb-3">
        <motion.div 
          whileHover={{ scale: 1.1, rotate: 5 }}
          className={`w-6 h-6 rounded-full flex items-center justify-center ${
            role === 'user' ? 'bg-[#7dcfff]/20' : 'bg-[#9B72CB]/20'
          }`}
        >
          {getIcon()}
        </motion.div>
        <span className="text-[9px] font-mono text-[#565f89] uppercase tracking-wider">
          {role === 'user' ? 'You' : role === 'system' ? 'System' : 'Sovereign AI'}
        </span>
        {timestamp && (
          <span className="text-[8px] font-mono text-[#565f89] ml-auto flex items-center gap-1">
            <motion.div 
              animate={{ scale: [1, 1.2, 1] }}
              transition={{ duration: 2, repeat: Infinity }}
              className="w-1 h-1 rounded-full bg-[#7dcfff]" 
            />
            {timestamp}
          </span>
        )}
      </div>
      
      {/* Content */}
      <div className="text-sm leading-relaxed">
        {parts.map((part, idx) => {
          if (part.type === 'code' && part.code && part.language) {
            return <CodeBlock key={idx} code={part.code} language={part.language} driftLock={driftLock} />;
          }
          return (
            <motion.p 
              key={idx} 
              initial={{ opacity: 0, x: -5 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: idx * 0.05 }}
              className="whitespace-pre-wrap mb-2 last:mb-0 text-[#c0caf5] leading-relaxed"
            >
              {part.content}
            </motion.p>
          );
        })}
        {isStreaming && (
          <span className="inline-flex items-center gap-1 ml-1">
            <motion.span
              animate={{ opacity: [0, 1, 0] }}
              transition={{ duration: 0.8, repeat: Infinity }}
              className="w-2 h-2 bg-[#7dcfff] rounded-full"
            />
            <span className="text-[10px] text-[#565f89] animate-pulse">thinking</span>
          </span>
        )}
      </div>
      
      {/* Drift Lock Badge */}
      {driftLock && (
        <motion.div 
          initial={{ opacity: 0, y: 5 }}
          animate={{ opacity: 1, y: 0 }}
          className="flex items-center gap-1 mt-3 pt-2 border-t border-[#7dcfff]/10"
        >
          <ShieldCheck className="w-3 h-3 text-[#9ece6a]" />
          <span className="text-[8px] font-mono text-[#9ece6a]">
            SCE: {driftLock.substring(0, 8)}...
          </span>
          <motion.div 
            animate={{ x: [0, 3, 0] }}
            transition={{ duration: 3, repeat: Infinity }}
            className="text-[8px] font-mono text-[#7dcfff] ml-auto"
          >
            zero-drift
          </motion.div>
        </motion.div>
      )}
      
      {/* Hover Glow Effect */}
      <div className="absolute inset-0 rounded-2xl pointer-events-none opacity-0 group-hover:opacity-100 transition-opacity duration-500">
        <div className="absolute inset-0 bg-gradient-to-r from-[#7dcfff]/5 via-[#9B72CB]/5 to-transparent rounded-2xl" />
      </div>
    </motion.div>
  );
};