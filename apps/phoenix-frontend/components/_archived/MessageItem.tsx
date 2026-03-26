'use client';

import React from 'react';
import { motion } from 'framer-motion';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { CodeBlock } from './CodeBlock';
import { Shield, Zap } from 'lucide-react';

interface Message {
  id: string;
  role: 'user' | 'ai' | 'system';
  content: string;
  timestamp: string;
  worker?: string;
  proof_hash?: string;
  isStreaming?: boolean;
}

const Icons = {
  Shield: () => <Shield className="w-3 h-3" />,
  Zap: () => <Zap className="w-3 h-3" />
};

const MessageContent = React.memo(({ content }: { content: string }) => (
  <div className="prose prose-invert max-w-none 
    prose-p:text-[#D1D5DB] prose-p:leading-relaxed prose-p:mb-4 
    prose-headings:text-white prose-headings:font-semibold prose-headings:mb-4 prose-headings:mt-6
    prose-a:text-[#00E5FF] prose-a:no-underline hover:prose-a:underline
    prose-ul:list-disc prose-ul:pl-5 prose-ul:mb-5 prose-ul:space-y-1.5
    prose-ol:list-decimal prose-ol:pl-5 prose-ol:mb-5 prose-ol:space-y-1.5
    prose-li:text-[#D1D5DB] prose-li:leading-relaxed
    prose-strong:text-[#00E5FF] prose-strong:font-semibold">
    <ReactMarkdown
      remarkPlugins={[remarkGfm]}
      components={{
        p: ({ children }) => <div className="mb-4 last:mb-0">{children}</div>,
        pre: ({ children }) => <div className="my-4">{children}</div>,
        code({ node, inline, className, children, ...props }) {
          const match = /language-(\w+)/.exec(className || '');
          const language = match ? match[1] : 'text';
          const codeString = String(children).replace(/\n$/, '');
          if (!inline) return <CodeBlock language={language} code={codeString} />;
          return <code className="bg-[#2A2E38]/50 text-[#10b981] px-1.5 py-0.5 rounded text-[13px] font-mono border border-[#10b981]/30" {...props}>{children}</code>;
        }
      }}
    >
      {content}
    </ReactMarkdown>
  </div>
));

MessageContent.displayName = 'MessageContent';

export const MessageItem = React.memo(({ 
  message, 
  activeWorkerInfo,
  isLast,
  isAtBottom,
  onStreamingComplete 
}: { 
  message: Message; 
  activeWorkerInfo: any;
  isLast: boolean;
  isAtBottom: boolean;
  onStreamingComplete?: () => void;
}) => {
  return (
    <motion.div
      layout
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
    >
      <div className={`max-w-[80%] ${
        message.role === 'user' 
          ? 'bg-[#1A1D24] border border-[#2A2E38] rounded-2xl rounded-tr-sm p-4' 
          : message.role === 'system'
            ? 'border-l-2 border-[#FF9800] bg-gradient-to-r from-[#FF9800]/10 to-transparent p-4'
            : 'border-l-2 border-[#00E5FF] bg-gradient-to-r from-[#00E5FF]/5 to-transparent p-4'
      }`}>
        <div className="text-xs text-white/40 mb-2 font-mono flex items-center gap-2">
          <span>{message.timestamp}</span>
          {message.proof_hash && (
            <span className="text-[#00E5FF] flex items-center gap-1">
              <Icons.Zap /> {message.proof_hash.substring(0, 6)}
            </span>
          )}
          {message.isStreaming && (
            <span className="flex gap-1">
              <span className="w-1 h-1 bg-[#00E5FF] rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
              <span className="w-1 h-1 bg-[#00E5FF] rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
              <span className="w-1 h-1 bg-[#00E5FF] rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
            </span>
          )}
        </div>
        <MessageContent content={message.content} />
      </div>
    </motion.div>
  );
});

MessageItem.displayName = 'MessageItem';