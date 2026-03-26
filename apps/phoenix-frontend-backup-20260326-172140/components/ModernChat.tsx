'use client';

import { useState, useRef, useEffect } from 'react';
import { Send, Bot, User, Sparkles } from 'lucide-react';

export function ModernChat() {
  const [messages, setMessages] = useState([
    { id: 1, role: 'assistant', content: 'Hello! How can I help you today?' }
  ]);
  const [input, setInput] = useState('');
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSend = () => {
    if (!input.trim()) return;
    
    setMessages([...messages, { id: Date.now(), role: 'user', content: input }]);
    setInput('');
    
    // Simulate response
    setTimeout(() => {
      setMessages(prev => [...prev, { 
        id: Date.now() + 1, 
        role: 'assistant', 
        content: 'Processing your request...' 
      }]);
    }, 1000);
  };

  return (
    <div className="chat-container h-full flex flex-col">
      {/* Header */}
      <div className="chat-header">
        <div className="flex items-center gap-2">
          <Bot size={18} className="text-accent-primary" />
          <span className="font-medium">Sovereign AI</span>
          <span className="text-xs text-text-tertiary ml-2">• 28 workers active</span>
        </div>
      </div>
      
      {/* Messages */}
      <div className="chat-messages flex-1 overflow-y-auto">
        {messages.map((msg) => (
          <div
            key={msg.id}
            className={`chat-bubble ${msg.role}`}
          >
            {msg.content}
          </div>
        ))}
        <div ref={messagesEndRef} />
      </div>
      
      {/* Input */}
      <div className="chat-input-container">
        <div className="flex gap-2">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleSend()}
            placeholder="Ask Sovereign AI..."
            className="chat-input flex-1"
          />
          <button
            onClick={handleSend}
            className="modern-button primary px-4 flex items-center gap-2"
          >
            <Send size={16} />
            <span>Send</span>
          </button>
        </div>
      </div>
    </div>
  );
}
