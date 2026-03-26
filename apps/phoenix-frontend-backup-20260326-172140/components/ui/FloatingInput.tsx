'use client';
import { useState } from 'react';
import { cn } from '@/lib/utils';
import { Send, Zap } from 'lucide-react';
import { Glass } from './Glass';

interface FloatingInputProps {
  onSend?: (message: string) => void;
  placeholder?: string;
  className?: string;
}

export const FloatingInput: React.FC<FloatingInputProps> = ({
  onSend,
  placeholder = "Ask Sovereign anything...",
  className
}) => {
  const [input, setInput] = useState('');
  const [isFocused, setIsFocused] = useState(false);

  const handleSend = () => {
    if (input.trim()) {
      onSend?.(input);
      setInput('');
    }
  };

  return (
    <div className={cn('fixed bottom-8 left-1/2 -translate-x-1/2 w-[600px] max-w-[90vw]', className)}>
      <Glass
        intensity="medium"
        glow={isFocused}
        radius="full"
        className={cn(
          'transition-all duration-300',
          isFocused && 'shadow-[0_0_40px_rgba(0,255,194,0.3)]'
        )}
      >
        <div className="flex items-center px-2">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onFocus={() => setIsFocused(true)}
            onBlur={() => setIsFocused(false)}
            onKeyDown={(e) => e.key === 'Enter' && handleSend()}
            placeholder={placeholder}
            className="flex-1 bg-transparent border-none outline-none px-4 py-3 text-sm text-white/90 placeholder:text-white/30"
          />
          <button
            onClick={handleSend}
            disabled={!input.trim()}
            className={cn(
              'p-2 rounded-full transition-all flex items-center gap-1',
              input.trim()
                ? 'text-[var(--accent-cyan)] hover:bg-white/5'
                : 'text-white/20 cursor-not-allowed'
            )}
          >
            <Zap size={16} />
            <span className="text-xs font-mono hidden sm:inline">SEND</span>
          </button>
        </div>
      </Glass>
    </div>
  );
};

