'use client';

import { useState, useRef, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Send, Bot, User, Sparkles, Lock, Zap } from 'lucide-react';

interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
}

export function ChatInterface() {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: '1',
      role: 'assistant',
      content: 'Hello! I\'m your Sovereign AI. How can I help you today?',
      timestamp: new Date()
    }
  ]);
  const [input, setInput] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSend = async () => {
    if (!input.trim()) return;

    // Add user message
    const userMessage: Message = {
      id: Date.now().toString(),
      role: 'user',
      content: input,
      timestamp: new Date()
    };
    setMessages(prev => [...prev, userMessage]);
    setInput('');
    setIsTyping(true);

    // Simulate AI response
    setTimeout(() => {
      const assistantMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: `Processing: "${input}"\n\nI'll help you with that. (This is a simulated response - actual AI integration coming soon)`,
        timestamp: new Date()
      };
      setMessages(prev => [...prev, assistantMessage]);
      setIsTyping(false);
    }, 1500);
  };

  return (
    <div className="flex flex-col h-full bg-[#1E1E1E] rounded-lg overflow-hidden border border-white/10">
      {/* Chat Header */}
      <div className="flex items-center justify-between p-3 border-b border-white/10 bg-[#252525]">
        <div className="flex items-center gap-2">
          <div className="w-6 h-6 rounded bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center">
            <Bot className="w-3 h-3 text-white" />
          </div>
          <span className="font-medium text-sm">Sovereign AI Assistant</span>
          <span className="badge blue text-[10px]">v2026</span>
        </div>
        <div className="flex items-center gap-2">
          <Lock className="w-3 h-3 text-white/30" />
          <span className="text-[10px] text-white/30">2800 DEEP - Full compliance</span>
        </div>
      </div>

      {/* Messages Area */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        <AnimatePresence>
          {messages.map((message) => (
            <motion.div
              key={message.id}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0 }}
              className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
            >
              <div className={`flex gap-2 max-w-[80%] ${message.role === 'user' ? 'flex-row-reverse' : ''}`}>
                {/* Avatar */}
                <div className={`w-6 h-6 rounded-full flex items-center justify-center flex-shrink-0 ${
                  message.role === 'user' 
                    ? 'bg-blue-500' 
                    : 'bg-gradient-to-br from-purple-500 to-blue-500'
                }`}>
                  {message.role === 'user' 
                    ? <User className="w-3 h-3 text-white" />
                    : <Bot className="w-3 h-3 text-white" />
                  }
                </div>
                
                {/* Message Bubble */}
                <div className={`px-3 py-2 rounded-lg text-sm ${
                  message.role === 'user'
                    ? 'bg-blue-500 text-white'
                    : 'bg-[#2D2D2D] text-white/90 border border-white/10'
                }`}>
                  <p className="whitespace-pre-wrap">{message.content}</p>
                  <div className="text-[8px] text-white/30 mt-1">
                    {message.timestamp.toLocaleTimeString()}
                  </div>
                </div>
              </div>
            </motion.div>
          ))}
        </AnimatePresence>
        
        {/* Typing Indicator */}
        {isTyping && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="flex gap-2"
          >
            <div className="w-6 h-6 rounded-full bg-gradient-to-br from-purple-500 to-blue-500 flex items-center justify-center">
              <Bot className="w-3 h-3 text-white" />
            </div>
            <div className="px-3 py-2 rounded-lg bg-[#2D2D2D] border border-white/10">
              <div className="flex gap-1">
                <span className="w-1.5 h-1.5 bg-white/50 rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
                <span className="w-1.5 h-1.5 bg-white/50 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
                <span className="w-1.5 h-1.5 bg-white/50 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
              </div>
            </div>
          </motion.div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Input Area */}
      <div className="p-3 border-t border-white/10 bg-[#252525]">
        <div className="flex gap-2">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleSend()}
            placeholder="Describe what you want to generate..."
            className="flex-1 bg-[#1E1E1E] border border-white/10 rounded px-3 py-2 text-sm focus:outline-none focus:border-blue-500"
          />
          <button
            onClick={handleSend}
            disabled={!input.trim() || isTyping}
            className="px-4 bg-blue-500 hover:bg-blue-600 disabled:opacity-50 disabled:cursor-not-allowed rounded flex items-center gap-2 text-sm font-medium transition-colors"
          >
            <Send className="w-3 h-3" />
            <span className="hidden sm:inline">Generate with Zero Click</span>
          </button>
        </div>
        
        {/* Quick Actions */}
        <div className="flex gap-2 mt-2">
          <button className="text-xs px-2 py-1 bg-white/5 hover:bg-white/10 rounded flex items-center gap-1">
            <Sparkles className="w-3 h-3" /> Generate
          </button>
          <button className="text-xs px-2 py-1 bg-white/5 hover:bg-white/10 rounded flex items-center gap-1">
            <Zap className="w-3 h-3" /> Quick
          </button>
          <span className="text-xs text-white/30 ml-auto">Lock Foundation • 2800 DEEP</span>
        </div>
      </div>
    </div>
  );
}
