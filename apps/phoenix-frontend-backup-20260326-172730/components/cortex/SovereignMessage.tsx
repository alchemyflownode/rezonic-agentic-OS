import React from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { InlineCode } from './InlineCode';
import { SovereignCodeBlock } from './SovereignCodeBlock';
import { StreamParser } from '../utils/streamParser';
import { LanguageDetector } from '../utils/languageDetector';

interface SovereignMessageProps {
  content: string;
  role: 'user' | 'assistant' | 'system';
  isStreaming?: boolean;
  onCopy?: () => void;
}

export const SovereignMessage: React.FC<SovereignMessageProps> = ({
  content,
  role,
  isStreaming,
  onCopy
}) => {
  const detector = new LanguageDetector();
  const parser = new StreamParser();
  
  // 1. STREAMING STATE (Handles chunks before Markdown is fully formed)
  if (isStreaming) {
    const segments = parser.parse(content);
    return (
      <div className="w-full">
        {segments.map((segment: any, i: number) => {
          if (segment.type === 'code') {
            return (
              <div key={i} className="my-3 shadow-lg rounded-lg border border-[#292e42] overflow-hidden">
                <SovereignCodeBlock
                  code={segment.content}
                  language={detector.detect(segment.content) || "text"}
                  isStreaming={true}
                />
              </div>
            );
          }
          return (
            <span key={i} className="whitespace-pre-wrap text-[#c0caf5] font-mono text-[11px] leading-relaxed">
              {segment.content}
            </span>
          );
        })}
      </div>
    );
  }
  
  // 2. COMPLETED STATE (Full Markdown Rendering in Tokyo Night)
  return (
    // 🔥 FIX: Wrapped ReactMarkdown in a styled div instead of using className on the component
    <div className="w-full text-[11px] leading-relaxed font-mono tracking-wide text-[#c0caf5]">
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        components={{
          
          // 🔥 FIX: Explicitly define paragraph spacing
          p({ children }) {
            return <p className="mb-3 last:mb-0">{children}</p>;
          },

          // Code blocks & Inline code
          code({ node, inline, className, children, ...props }) {
            const match = /language-(\w+)/.exec(className || '');
            let language = match ? match[1] : detector.detect(String(children));
            language = language || "text"; 
            
            if (inline) {
              return <InlineCode>{String(children)}</InlineCode>;
            }
            
            return (
              <div className="my-3 shadow-lg rounded-lg border border-[#292e42] overflow-hidden">
                <SovereignCodeBlock
                  code={String(children).replace(/\n$/, '')}
                  language={language}
                  onCopy={onCopy}
                />
              </div>
            );
          },
          
          // Tables (Tokyo Night styling)
          table({ children }) {
            return (
              <div className="overflow-x-auto my-4 rounded-lg border border-[#292e42]">
                <table className="min-w-full border-collapse bg-[#1a1b26]">
                  {children}
                </table>
              </div>
            );
          },
          th({ children }) {
            return (
              <th className="px-3 py-2 text-left text-[10px] font-mono border-b border-[#292e42] bg-[#24283b] text-[#bb9af7] uppercase tracking-widest">
                {children}
              </th>
            );
          },
          td({ children }) {
            return (
              <td className="px-3 py-2 text-[10px] border-b border-[#292e42] text-[#c0caf5]">
                {children}
              </td>
            );
          },
          
          // Headers (Cyan, Purple, White)
          h1({ children }) {
            return <h1 className="text-lg font-bold mt-4 mb-2 text-[#7dcfff]">{children}</h1>;
          },
          h2({ children }) {
            return <h2 className="text-base font-bold mt-4 mb-2 text-[#bb9af7]">{children}</h2>;
          },
          h3({ children }) {
            return <h3 className="text-sm font-bold mt-3 mb-2 text-[#c0caf5]">{children}</h3>;
          },
          
          // Lists
          ul({ children }) {
            return <ul className="list-disc list-inside my-2 space-y-1.5 text-[#c0caf5]">{children}</ul>;
          },
          ol({ children }) {
            return <ol className="list-decimal list-inside my-2 space-y-1.5 text-[#c0caf5]">{children}</ol>;
          },
          li({ children }) {
            return <li className="leading-relaxed">{children}</li>;
          },
          
          // Links
          a({ href, children }) {
            return (
              <a
                href={href}
                target="_blank"
                rel="noopener noreferrer"
                className="underline hover:no-underline transition-colors text-[#7dcfff]"
              >
                {children}
              </a>
            );
          },
          
          // Blockquotes (Purple accent)
          blockquote({ children }) {
            return (
              <blockquote className="pl-3 my-3 border-l-2 border-[#bb9af7] italic text-[#9aa5ce] bg-[#24283b]/50 py-1 pr-2 rounded-r">
                {children}
              </blockquote>
            );
          },
        }}
      >
        {content}
      </ReactMarkdown>
    </div>
  );
};