'use client';

import { useState, useRef, useEffect } from 'react';
import { Send, Bot, User } from 'lucide-react';
import { ThinkingIndicator } from './ThinkingIndicator';

interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  worker?: string;
  timestamp: Date;
}

export function AIChat() {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: '1',
      role: 'assistant',
      content: 'Hello! I\'m your Sovereign AI. How can I help?',
      timestamp: new Date()
    }
  ]);
  const [input, setInput] = useState('');
  const [isThinking, setIsThinking] = useState(false);
  const [activeWorker, setActiveWorker] = useState<string | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSend = async () => {
    if (!input.trim() || isThinking) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      role: 'user',
      content: input,
      timestamp: new Date()
    };
    setMessages(prev => [...prev, userMessage]);
    
    const query = input;
    setInput('');
    setIsThinking(true);
    
    // Simulate worker detection
    if (query.toLowerCase().includes('search')) {
      setActiveWorker('deepsearch');
    } else if (query.toLowerCase().includes('cpu') || query.toLowerCase().includes('ram')) {
      setActiveWorker('system_monitor');
    } else if (query.toLowerCase().includes('open') || query.toLowerCase().includes('launch')) {
      setActiveWorker('app_launcher');
    } else if (query.toLowerCase().includes('code')) {
      setActiveWorker('code_worker');
    } else {
      setActiveWorker('cortex');
    }

    try {
      const response = await fetch('/api/kernel', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ task: query })
      });
      
      const data = await response.json();
      
      let content = '';
      if (data.stats) {
        content = `📊 CPU: ${data.stats.cpu?.percent}% | RAM: ${data.stats.memory?.percent}%`;
      } else if (data.message) {
        content = data.message;
      } else if (data.content) {
        content = data.content;
      } else if (data.results) {
        content = `Found ${data.results.length} results`;
      } else {
        content = 'Command executed successfully';
      }

      const assistantMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content,
        worker: data.worker || activeWorker,
        timestamp: new Date()
      };
      setMessages(prev => [...prev, assistantMessage]);
    } catch (error) {
      const errorMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: '❌ Error processing request',
        timestamp: new Date()
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsThinking(false);
      setActiveWorker(null);
    }
  };

  return (
    <div className="flex flex-col h-full bg-bg-surface rounded-lg border border-border-subtle overflow-hidden">
      {/* Chat Header */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-border-subtle">
        <div className="flex items-center gap-2">
          <Bot size={18} className="text-accent-primary" />
          <span className="font-medium">Sovereign AI</span>
          {isThinking && <ThinkingIndicator variant="minimal" isThinking={true} />}
        </div>
        <div className="flex items-center gap-2">
          <span className="status-dot active" />
          <span className="text-xs text-text-tertiary">online</span>
        </div>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.map((msg) => (
          <div
            key={msg.id}
            className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
          >
            <div className={`max-w-[80%] ${msg.role === 'user' ? 'order-2' : ''}`}>
              <div className="flex items-start gap-2">
                {msg.role === 'assistant' && (
                  <div className="w-6 h-6 rounded-full bg-accent-soft flex items-center justify-center flex-shrink-0">
                    <Bot size={12} className="text-accent-primary" />
                  </div>
                )}
                <div
                  className={`px-3 py-2 rounded-lg text-sm ${
                    msg.role === 'user'
                      ? 'bg-accent-primary text-black'
                      : 'bg-bg-elevated text-text-primary border border-border-soft'
                  }`}
                >
                  <p>{msg.content}</p>
                  {msg.worker && msg.role === 'assistant' && (
                    <div className="flex items-center gap-2 mt-1">
                      <span className="worker-activity">
                        <span className="worker-status" />
                        <span className="worker-name">{msg.worker}</span>
                      </span>
                      <span className="text-[10px] text-text-tertiary">
                        {msg.timestamp.toLocaleTimeString()}
                      </span>
                    </div>
                  )}
                </div>
                {msg.role === 'user' && (
                  <div className="w-6 h-6 rounded-full bg-bg-elevated border border-border-soft flex items-center justify-center flex-shrink-0">
                    <User size={12} className="text-text-secondary" />
                  </div>
                )}
              </div>
            </div>
          </div>
        ))}
        
        {/* Thinking Indicator */}
        {isThinking && (
          <div className="flex justify-start">
            <div className="flex items-start gap-2">
              <div className="w-6 h-6 rounded-full bg-accent-soft flex items-center justify-center">
                <Bot size={12} className="text-accent-primary" />
              </div>
              <ThinkingIndicator 
                variant="neural" 
                isThinking={true} 
                worker={activeWorker || undefined}
                message="Processing"
              />
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <div className="p-4 border-t border-border-subtle">
        <div className="flex gap-2">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleSend()}
            placeholder="Ask Sovereign AI..."
            className="flex-1 bg-bg-elevated border border-border-soft rounded-lg px-4 py-2 text-sm focus:outline-none focus:border-accent-primary"
            disabled={isThinking}
          />
          <button
            onClick={handleSend}
            disabled={!input.trim() || isThinking}
            className="px-4 py-2 bg-accent-primary text-black rounded-lg text-sm font-medium hover:bg-accent-hover disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
          >
            <Send size={16} />
            <span>Send</span>
          </button>
        </div>
      </div>
    </div>
  );
}
