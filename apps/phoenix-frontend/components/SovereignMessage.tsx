// components/SovereignMessage.tsx
import React from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { vscDarkPlus } from 'react-syntax-highlighter/dist/esm/styles/prism';

interface SovereignMessageProps {
  content: string;
  role: 'user' | 'assistant' | 'system';
  timestamp?: string;
  isStreaming?: boolean;
  driftLock?: string;
  narrative?: string[];
  className?: string;
}

export const SovereignMessage: React.FC<SovereignMessageProps> = ({
  content,
  role,
  timestamp,
  isStreaming = false,
  driftLock,
  narrative,
  className = ''
}) => {
  return (
    <div className={`message ${role} ${isStreaming ? 'streaming' : ''} ${className}`}>
      <div className="message-content prose prose-invert max-w-none">
        <ReactMarkdown
          remarkPlugins={[remarkGfm]}
          components={{
            code({ inline, className, children, ...props }) {
              const match = /language-(\w+)/.exec(className || '');
              const codeString = String(children).replace(/\n$/, '');
              
              if (!inline && match) {
                return (
                  <div className="relative my-4 rounded-lg overflow-hidden border border-white/10">
                    <div className="flex items-center justify-between px-4 py-2 bg-white/5 border-b border-white/10">
                      <span className="text-[10px] font-mono text-[#9B72CB] uppercase tracking-wider">
                        {match[1]}
                      </span>
                      <button
                        onClick={() => navigator.clipboard.writeText(codeString)}
                        className="text-[10px] text-zinc-500 hover:text-[#00E5FF] transition-colors"
                      >
                        Copy
                      </button>
                    </div>
                    <SyntaxHighlighter
                      language={match[1]}
                      style={vscDarkPlus}
                      customStyle={{
                        margin: 0,
                        background: '#030406',
                        fontSize: '11px',
                        padding: '1rem',
                        borderRadius: 0
                      }}
                    >
                      {codeString}
                    </SyntaxHighlighter>
                  </div>
                );
              }
              
              return (
                <code className="bg-white/10 px-1.5 py-0.5 rounded text-[#00E5FF] text-[11px] font-mono" {...props}>
                  {children}
                </code>
              );
            },
            p({ children }) {
              return <div className="mb-4 last:mb-0 text-[13px] leading-relaxed font-mono">{children}</div>;
            },
          }}
        >
          {content}
        </ReactMarkdown>
        
        {isStreaming && (
          <span className="inline-block w-1.5 h-4 bg-[#00E5FF] animate-pulse ml-1 align-middle" />
        )}
      </div>

      {narrative && narrative.length > 0 && (
        <div className="mt-3 p-3 bg-purple-500/5 border border-purple-500/20 rounded-lg">
          <div className="text-[8px] font-mono text-purple-400 mb-1 uppercase tracking-wider">🧠 Reasoning</div>
          {narrative.map((step, index) => (
            <div key={index} className="text-[9px] font-mono text-zinc-400 italic leading-relaxed mb-1">
              "{step}"
            </div>
          ))}
        </div>
      )}

      {driftLock && (
        <div className="mt-2 flex items-center gap-2">
          <div className="flex items-center gap-1.5">
            <span className="w-1.5 h-1.5 rounded-full bg-[#00E5FF]" />
            <span className="text-[8px] font-mono text-[#00E5FF]/70 uppercase tracking-wider">SCE_LOCKED</span>
          </div>
          <code className="text-[8px] font-mono text-[#00E5FF]/50 bg-white/5 px-1.5 py-0.5 rounded">
            {driftLock.slice(0, 12)}...
          </code>
        </div>
      )}
    </div>
  );
};

export default SovereignMessage;