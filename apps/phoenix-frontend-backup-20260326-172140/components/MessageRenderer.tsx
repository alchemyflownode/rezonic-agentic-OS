'use client';

import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { ShieldCheck, Copy, Check, Terminal, User, Bot } from 'lucide-react';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { oneDark } from 'react-syntax-highlighter/dist/esm/styles/prism';

interface MessageRendererProps {
  content: string;
  role: 'user' | 'assistant' | 'system';
  timestamp?: string;
  driftLock?: string;
  isStreaming?: boolean;
}

interface ContentPart {
  type: 'text' | 'code';
  content?: string;
  language?: string;
  code?: string;
}

// Parse content into text and code blocks
const parseContent = (content: string): ContentPart[] => {
  if (!content) return [{ type: 'text', content: '' }];
  
  const parts: ContentPart[] = [];
  const codeBlockRegex = /```(\w+)?\n([\s\S]*?)```/g;
  let lastIndex = 0;
  let match;
  
  while ((match = codeBlockRegex.exec(content)) !== null) {
    // Add text before code block
    if (match.index > lastIndex) {
      const text = content.slice(lastIndex, match.index);
      if (text.trim()) {
        parts.push({ type: 'text', content: text });
      }
    }
    
    // Add code block
    parts.push({
      type: 'code',
      language: match[1] || 'python',
      code: match[2].trim()
    });
    
    lastIndex = match.index + match[0].length;
  }
  
  // Add remaining text
  if (lastIndex < content.length) {
    const text = content.slice(lastIndex);
    if (text.trim()) {
      parts.push({ type: 'text', content: text });
    }
  }
  
  return parts.length > 0 ? parts : [{ type: 'text', content }];
};

// Code Block Component
const CodeBlock = ({ code, language }: { code: string; language: string }) => {
  const [copied, setCopied] = useState(false);

  const handleCopy = async () => {
    await navigator.clipboard.writeText(code);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="relative group my-3">
      <div className="absolute right-2 top-2 z-10 opacity-0 group-hover:opacity-100 transition-opacity">
        <button
          onClick={handleCopy}
          className="p-1.5 rounded-lg bg-[#1a1b26] border border-[#7dcfff]/30 text-[#7dcfff] hover:bg-[#7dcfff]/10 transition-all"
          title="Copy code"
        >
          {copied ? <Check className="w-3.5 h-3.5" /> : <Copy className="w-3.5 h-3.5" />}
        </button>
      </div>
      <div className="rounded-xl overflow-hidden border border-[#7dcfff]/20">
        <div className="bg-[#1f2335] px-4 py-2 border-b border-[#7dcfff]/20 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="w-2 h-2 rounded-full bg-[#f7768e]" />
            <div className="w-2 h-2 rounded-full bg-[#e0af68]" />
            <div className="w-2 h-2 rounded-full bg-[#9ece6a]" />
            <Terminal className="w-3 h-3 text-[#7dcfff] ml-2" />
            <span className="text-[9px] font-mono text-[#7dcfff] uppercase tracking-wider">
              {language}
            </span>
          </div>
          <span className="text-[8px] font-mono text-[#565f89]">
            {code.split('\n').length} lines
          </span>
        </div>
        <SyntaxHighlighter
          language={language.toLowerCase()}
          style={oneDark}
          showLineNumbers={true}
          wrapLines={true}
          customStyle={{
            margin: 0,
            padding: "1rem",
            background: "#1a1b26",
            fontSize: "12px",
            fontFamily: "'JetBrains Mono', 'Fira Code', monospace",
          }}
          lineNumberStyle={{
            color: "#565f89",
            paddingRight: "1rem",
            borderRight: "1px solid rgba(125,207,255,0.2)",
            marginRight: "1rem",
          }}
        >
          {code}
        </SyntaxHighlighter>
      </div>
    </div>
  );
};

// Main MessageRenderer Component
export const MessageRenderer: React.FC<MessageRendererProps> = ({
  content,
  role,
  timestamp,
  driftLock,
  isStreaming = false,
}) => {
  const parts = parseContent(content);
  
  const getContainerClass = () => {
    if (role === 'user') {
      return 'bg-gradient-to-r from-[#7dcfff]/20 to-[#9B72CB]/20 border border-[#7dcfff]/30 rounded-br-sm';
    }
    if (role === 'system') {
      return 'bg-[#565f89]/10 border border-[#565f89]/30 rounded-bl-sm';
    }
    return 'bg-white/5 border border-white/10 rounded-bl-sm';
  };
  
  const getIcon = () => {
    if (role === 'user') return <User className="w-3 h-3" />;
    if (role === 'system') return <ShieldCheck className="w-3 h-3" />;
    return <Bot className="w-3 h-3" />;
  };

  return (
    <div className={`p-4 rounded-2xl ${getContainerClass()}`}>
      <div className="flex items-center gap-2 mb-2">
        <div className={`w-5 h-5 rounded-full flex items-center justify-center ${
          role === 'user' ? 'bg-[#7dcfff]/20' : 'bg-[#9B72CB]/20'
        }`}>
          {getIcon()}
        </div>
        <span className="text-[9px] font-mono text-[#565f89] uppercase tracking-wider">
          {role === 'user' ? 'You' : role === 'system' ? 'System' : 'Sovereign AI'}
        </span>
        {timestamp && (
          <span className="text-[8px] font-mono text-[#565f89] ml-auto">{timestamp}</span>
        )}
      </div>
      
      <div className="text-sm leading-relaxed">
        {parts.map((part, idx) => {
          if (part.type === 'code' && part.code && part.language) {
            return (
              <CodeBlock
                key={idx}
                code={part.code}
                language={part.language}
              />
            );
          }
          return (
            <p key={idx} className="whitespace-pre-wrap mb-2 last:mb-0 text-[#c0caf5]">
              {part.content}
            </p>
          );
        })}
        {isStreaming && (
          <span className="inline-block w-2 h-4 ml-1 bg-[#7dcfff] animate-pulse" />
        )}
      </div>
      
      {driftLock && (
        <div className="flex items-center gap-1 mt-2 pt-1 border-t border-[#7dcfff]/10">
          <ShieldCheck className="w-3 h-3 text-[#9ece6a]" />
          <span className="text-[8px] font-mono text-[#9ece6a]">
            SCE: {driftLock.substring(0, 8)}...
          </span>
        </div>
      )}
    </div>
  );
};

export default MessageRenderer;
