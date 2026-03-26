'use client';

import { useState, useRef, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Send, Bot, User, Sparkles, Zap, Loader } from 'lucide-react';

interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
  worker?: string;
}

export function ObsidianChat() {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: '1',
      role: 'assistant',
      content: 'Welcome to Sovereign IDE. Type a command or select a worker.',
      timestamp: new Date()
    }
  ]);
  const [input, setInput] = useState('');
  const [isProcessing, setIsProcessing] = useState(false);
  const [mounted, setMounted] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    setMounted(true);
  }, []);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const executeCommand = async (command: string) => {
    try {
      const response = await fetch('/api/kernel', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ task: command })
      });
      return await response.json();
    } catch (error) {
      return { error: String(error) };
    }
  };

  const handleSend = async () => {
    if (!input.trim() || isProcessing) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      role: 'user',
      content: input,
      timestamp: new Date()
    };
    setMessages(prev => [...prev, userMessage]);
    const command = input;
    setInput('');
    setIsProcessing(true);

    const result = await executeCommand(command);
    
    let responseContent = '';
    if (result.error) {
      responseContent = `❌ ${result.error}`;
    } else if (result.stats) {
      responseContent = `📊 CPU: ${result.stats.cpu?.percent}% | RAM: ${result.stats.memory?.percent}%`;
    } else if (result.message) {
      responseContent = result.message;
    } else if (result.content) {
      responseContent = result.content;
    } else {
      responseContent = 'Command executed';
    }

    const assistantMessage: Message = {
      id: (Date.now() + 1).toString(),
      role: 'assistant',
      content: responseContent,
      timestamp: new Date(),
      worker: result.worker
    };
    
    setMessages(prev => [...prev, assistantMessage]);
    setIsProcessing(false);
  };

  const formatTime = (date: Date) => {
    if (!mounted) return '';
    return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
  };

  return (
    <div className="h-full flex flex-col bg-charcoal-surface">
      {/* Chat Header */}
      <div className="flex items-center justify-between px-3 py-2 border-b border-charcoal-border">
        <div className="flex items-center gap-2">
          <Bot size={14} className="text-accent-cyan" />
          <span className="text-xs font-mono text-text-secondary">SOVEREIGN CHAT</span>
        </div>
        <div className="flex items-center gap-2">
          <span className="status-dot active" />
          <span className="text-[10px] text-text-tertiary">connected</span>
        </div>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-3 space-y-3 font-mono text-xs">
        <AnimatePresence>
          {messages.map((message) => (
            <motion.div
              key={message.id}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
            >
              <div className={`max-w-[80%] px-2 py-1.5 rounded ${
                message.role === 'user' 
                  ? 'bg-accent-cyan/10 text-accent-cyan' 
                  : 'bg-charcoal-surface-light text-text-secondary'
              }`}>
                <p className="whitespace-pre-wrap">{message.content}</p>
                <div className="flex justify-between items-center mt-1 text-[8px] text-text-tertiary">
                  <span>{message.worker && `@${message.worker}`}</span>
                  <span>{formatTime(message.timestamp)}</span>
                </div>
              </div>
            </motion.div>
          ))}
        </AnimatePresence>
        
        {isProcessing && (
          <div className="flex items-center gap-2 text-text-tertiary">
            <Loader size={12} className="animate-spin" />
            <span className="text-xs">processing...</span>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <div className="p-2 border-t border-charcoal-border">
        <div className="flex gap-1">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleSend()}
            placeholder="Type a command..."
            className="flex-1 bg-charcoal-foundation border border-charcoal-border rounded px-2 py-1 text-xs font-mono text-text-primary placeholder-text-tertiary focus:outline-none focus:border-accent-cyan"
          />
          <button
            onClick={handleSend}
            disabled={!input.trim() || isProcessing}
            className="px-3 py-1 bg-accent-cyan/10 hover:bg-accent-cyan/20 border border-accent-cyan/30 rounded text-accent-cyan text-xs disabled:opacity-50"
          >
            Send
          </button>
        </div>
      </div>
    </div>
  );
}
