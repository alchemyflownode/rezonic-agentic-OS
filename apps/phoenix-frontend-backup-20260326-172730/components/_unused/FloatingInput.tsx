'use client';

import { useState } from 'react';
import { cn } from '@/lib/utils';
import { Send, Mic, Paperclip } from 'lucide-react';
import { GlassCard } from './ui/GlassCard';

interface FloatingInputProps {
  onSend?: (message: string) => void;
  placeholder?: string;
  className?: string;
}

export function FloatingInput({ onSend, placeholder = "Message Sovereign...", className }: FloatingInputProps) {
  const [input, setInput] = useState('');
  const [isFocused, setIsFocused] = useState(false);

  const handleSend = () => {
    if (input.trim()) {
      onSend?.(input);
      setInput('');
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <GlassCard 
      variant="medium" 
      radius="full"
      hover={false}
      glow={isFocused}
      className={cn(
        'fixed bottom-8 left-1/2 transform -translate-x-1/2',
        'w-[600px] max-w-[90vw] p-1',
        'transition-all duration-300',
        isFocused && 'shadow-[0_0_40px_rgba(139,92,246,0.3)]',
        className
      )}
    >
      <div className="flex items-center gap-2">
        {/* Attachment button */}
        <button className="p-2 text-white/40 hover:text-white/60 transition-colors rounded-full hover:bg-white/5">
          <Paperclip className="w-4 h-4" />
        </button>

        {/* Input field */}
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onFocus={() => setIsFocused(true)}
          onBlur={() => setIsFocused(false)}
          onKeyDown={handleKeyDown}
          placeholder={placeholder}
          className="flex-1 bg-transparent border-none outline-none text-sm text-white/90 placeholder:text-white/30 py-3"
        />

        {/* Mic button */}
        <button className="p-2 text-white/40 hover:text-white/60 transition-colors rounded-full hover:bg-white/5">
          <Mic className="w-4 h-4" />
        </button>

        {/* Send button */}
        <button
          onClick={handleSend}
          disabled={!input.trim()}
          className={cn(
            'p-2 rounded-full transition-all',
            input.trim() 
              ? 'bg-primary text-white hover:bg-primary-hover shadow-[0_0_20px_rgba(139,92,246,0.5)]' 
              : 'bg-white/10 text-white/30 cursor-not-allowed'
          )}
        >
          <Send className="w-4 h-4" />
        </button>
      </div>
    </GlassCard>
  );
}
