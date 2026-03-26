'use client';

import { useState, useEffect, useRef } from 'react';
import { Terminal, Send } from 'lucide-react';
import { phoenixStream } from '@/lib/phoenix-client';

const COMMANDS = [
  '/health', '/workers', '/code', '/generate', '/search',
  '/list', '/trade', '/portfolio', '/backtest', '/collaborate',
  '/kill', '/kill-status', '/okiru', '/symbiote'
];

interface CommandPaletteProps {
  onCommand?: (command: string, response: string) => void;
}

export default function CommandPalette({ onCommand }: CommandPaletteProps) {
  const [input, setInput] = useState('');
  const [suggestions, setSuggestions] = useState<string[]>([]);
  const [executing, setExecuting] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (input.length > 0) {
      const filtered = COMMANDS.filter(cmd => cmd.toLowerCase().startsWith(input.toLowerCase()));
      setSuggestions(filtered.slice(0, 5));
    } else {
      setSuggestions([]);
    }
  }, [input]);

  const executeCommand = async () => {
    if (!input.trim() || executing) return;
    
    setExecuting(true);
    let fullResponse = '';
    
    await phoenixStream(input, (data) => {
      if (data.content) {
        fullResponse += data.content;
        onCommand?.(input, fullResponse);
      }
    });
    
    setExecuting(false);
    setInput('');
    setSuggestions([]);
  };

  return (
    <div className="bg-black/30 backdrop-blur-xl border border-[#7dcfff]/10 rounded-xl p-4">
      <div className="flex items-center gap-2 mb-3">
        <Terminal className="w-4 h-4 text-[#7dcfff]" />
        <span className="text-sm font-mono text-gray-400">COMMAND PALETTE</span>
      </div>
      
      <div className="relative">
        <input
          ref={inputRef}
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && executeCommand()}
          placeholder="Type a command... /health, /trade, /code..."
          className="w-full bg-black/50 border border-[#7dcfff]/20 rounded-xl px-4 py-3 text-sm text-white placeholder:text-gray-500 outline-none focus:border-[#7dcfff]/50"
        />
        
        {suggestions.length > 0 && (
          <div className="absolute top-full left-0 right-0 mt-2 bg-black/90 border border-[#7dcfff]/20 rounded-xl overflow-hidden z-50">
            {suggestions.map((suggestion, i) => (
              <button
                key={i}
                onClick={() => {
                  setInput(suggestion);
                  setSuggestions([]);
                  inputRef.current?.focus();
                }}
                className="w-full text-left px-4 py-2 hover:bg-white/10 text-[#7dcfff] text-sm"
              >
                {suggestion}
              </button>
            ))}
          </div>
        )}
      </div>
      
      <button
        onClick={executeCommand}
        disabled={!input.trim() || executing}
        className="mt-3 w-full py-2 rounded-lg bg-gradient-to-r from-[#7dcfff]/20 to-[#9B72CB]/20 border border-[#7dcfff]/30 text-[#7dcfff] hover:shadow-lg disabled:opacity-50 flex items-center justify-center gap-2"
      >
        <Send className="w-4 h-4" />
        {executing ? 'Executing...' : 'Execute Command'}
      </button>
    </div>
  );
}
