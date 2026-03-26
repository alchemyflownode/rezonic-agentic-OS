'use client';

import { useState, useEffect } from 'react';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { vscDarkPlus } from 'react-syntax-highlighter/dist/esm/styles/prism';
import { Check, Copy, Download, Maximize2, X } from 'lucide-react';

interface CodeBlockProps {
  language: string;
  code: string;
}

export const CodeBlock = ({ language, code }: CodeBlockProps) => {
  const [copied, setCopied] = useState(false);
  const [isExpanded, setIsExpanded] = useState(false);
  const lineCount = code.split('\n').length;

  // Escape key to close fullscreen
  useEffect(() => {
    if (!isExpanded) return;
    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === 'Escape') setIsExpanded(false);
    };
    window.addEventListener('keydown', handleEscape);
    return () => window.removeEventListener('keydown', handleEscape);
  },[isExpanded]);

  const copyToClipboard = async () => {
    try {
      await navigator.clipboard.writeText(code);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch (err) {
      console.error('Failed to copy:', err);
    }
  };

  // Map common language aliases (MOVED UP to fix the scope bug)
  const languageMap: Record<string, string> = {
    js: 'javascript', ts: 'typescript', tsx: 'typescript', jsx: 'javascript',
    py: 'python', rb: 'ruby', sh: 'bash', bash: 'bash', ps1: 'powershell',
    json: 'json', yaml: 'yaml', yml: 'yaml', html: 'html', css: 'css',
    scss: 'scss', sql: 'sql', go: 'go', rs: 'rust', rust: 'rust',
    java: 'java', c: 'c', cpp: 'cpp', 'c++': 'cpp', php: 'php',
    md: 'markdown', markdown: 'markdown',
  };

  const normalizedLang = languageMap[language?.toLowerCase()] || language || 'text';

  const downloadCode = () => {
    const extensions: Record<string, string> = {
      javascript: 'js', typescript: 'ts', python: 'py', bash: 'sh',
      powershell: 'ps1', json: 'json', yaml: 'yml', html: 'html',
      css: 'css', scss: 'scss', rust: 'rs', go: 'go', java: 'java',
      cpp: 'cpp', c: 'c', php: 'php', sql: 'sql', markdown: 'md',
    };

    const ext = extensions[normalizedLang] || 'txt';
    const filename = `script_${new Date().getTime()}.${ext}`;

    const element = document.createElement('a');
    const file = new Blob([code], { type: 'text/plain' });
    element.href = URL.createObjectURL(file);
    element.download = filename;
    document.body.appendChild(element);
    element.click();
    document.body.removeChild(element);
    URL.revokeObjectURL(element.href);
  };

  const langColors: Record<string, string> = {
    javascript: 'from-yellow-500 to-yellow-600', typescript: 'from-blue-500 to-blue-600',
    python: 'from-blue-400 to-cyan-500', bash: 'from-green-500 to-green-600',
    powershell: 'from-purple-500 to-purple-600', json: 'from-orange-500 to-orange-600',
    html: 'from-red-500 to-red-600', css: 'from-pink-500 to-pink-600',
    rust: 'from-orange-600 to-red-600', go: 'from-cyan-400 to-blue-500',
    java: 'from-red-600 to-orange-500', sql: 'from-blue-600 to-indigo-600',
    markdown: 'from-gray-500 to-gray-600', scss: 'from-pink-600 to-purple-600',
    php: 'from-indigo-500 to-purple-500', c: 'from-blue-700 to-blue-800',
    cpp: 'from-blue-600 to-purple-600', text: 'from-gray-600 to-gray-700'
  };

  const bgGradient = langColors[normalizedLang] || 'from-cyan-500 to-blue-500';

  return (
    <>
      {/* Backdrop for fullscreen */}
      {isExpanded && (
        <div
          className="fixed inset-0 bg-[#050505]/90 backdrop-blur-md z-[100] transition-opacity"
          onClick={() => setIsExpanded(false)}
        />
      )}

      {/* Code Block Container */}
      <div
        className={`group my-6 rounded-xl overflow-hidden border border-[#2A2E38] bg-[#0A0C10] shadow-2xl transition-all ${
          isExpanded 
            ? 'fixed inset-4 md:inset-10 z-[101] flex flex-col shadow-[0_0_50px_rgba(0,229,255,0.1)]' 
            : 'relative'
        }`}
      >
        {/* Header Bar */}
        <div className="flex items-center justify-between px-4 py-2 bg-[#12141A] border-b border-[#2A2E38]">
          <div className="flex items-center gap-3">
            <span className={`text-[10px] font-bold uppercase tracking-widest px-2.5 py-1 rounded bg-gradient-to-r ${bgGradient} text-white shadow-sm`}>
              {normalizedLang}
            </span>
            <span className="text-[10px] text-[#8A8F9B] font-mono tracking-wider hidden sm:inline-block">
              {lineCount} {lineCount === 1 ? 'LINE' : 'LINES'}
            </span>
          </div>

          {/* Action Buttons */}
          <div className="flex items-center gap-2">
            <button
              onClick={downloadCode}
              className="p-1.5 rounded bg-white/5 hover:bg-white/10 text-[#8A8F9B] hover:text-white transition-colors border border-transparent hover:border-[#2A2E38]"
              title="Download code"
            >
              <Download size={14} />
            </button>

            {!isExpanded && (
              <button
                onClick={() => setIsExpanded(true)}
                className="p-1.5 rounded bg-white/5 hover:bg-white/10 text-[#8A8F9B] hover:text-white transition-colors border border-transparent hover:border-[#2A2E38]"
                title="Expand fullscreen"
              >
                <Maximize2 size={14} />
              </button>
            )}

            <button
              onClick={copyToClipboard}
              className={`flex items-center gap-1.5 px-3 py-1 rounded text-[10px] font-mono font-bold uppercase tracking-widest transition-all border ${
                copied
                  ? 'bg-[#00E676]/10 border-[#00E676]/30 text-[#00E676]'
                  : 'bg-[#00E5FF]/10 border-[#00E5FF]/30 text-[#00E5FF] hover:bg-[#00E5FF]/20'
              }`}
            >
              {copied ? <><Check size={12} /> COPIED</> : <><Copy size={12} /> COPY</>}
            </button>

            {isExpanded && (
              <button
                onClick={() => setIsExpanded(false)}
                className="p-1.5 ml-2 rounded bg-red-500/10 hover:bg-red-500/20 text-red-400 hover:text-red-300 transition-colors border border-red-500/20"
                title="Close fullscreen"
              >
                <X size={14} />
              </button>
            )}
          </div>
        </div>

        {/* Syntax Highlighter */}
        <div className={`flex-1 overflow-auto custom-scrollbar ${isExpanded ? '' : 'max-h-[400px]'}`}>
          <SyntaxHighlighter
            language={normalizedLang}
            style={vscDarkPlus}
            customStyle={{
              margin: 0,
              padding: '1.25rem',
              background: 'transparent',
              fontSize: '13px',
              lineHeight: '1.6',
              fontFamily: 'ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace',
            }}
            wrapLines={true}
            wrapLongLines={true}
            showLineNumbers={lineCount >= 3}
            lineNumberStyle={{
              color: '#4B5563',
              paddingRight: '1.5rem',
              userSelect: 'none',
              minWidth: '3em',
              textAlign: 'right'
            }}
          >
            {code}
          </SyntaxHighlighter>
        </div>
      </div>
    </>
  );
};