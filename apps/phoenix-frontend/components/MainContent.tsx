'use client';

import { useState } from 'react';
import { Send, Bot, User } from 'lucide-react';

export function MainContent() {
  const [input, setInput] = useState('');
  const [messages, setMessages] = useState([
    { role: 'assistant', content: 'Sovereign AI v2026 is active. How can I help you today?' }
  ]);

  const handleSend = () => {
    if (!input.trim()) return;
    
    setMessages([...messages, { role: 'user', content: input }]);
    setInput('');
    
    // Simulate response
    setTimeout(() => {
      setMessages(prev => [...prev, { 
        role: 'assistant', 
        content: 'Processing your request... System nominal.' 
      }]);
    }, 1000);
  };

  return (
    <div className="h-full flex flex-col">
      {/* Messages Area */}
      <div className="premium-panel flex-1 p-4 overflow-y-auto mb-4">
        <div className="space-y-4">
          {messages.map((msg, i) => (
            <div key={i} className={`flex gap-3 ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
              {msg.role === 'assistant' && (
                <div className="w-8 h-8 rounded-full bg-[#00FFC2]/10 flex items-center justify-center">
                  <Bot className="w-4 h-4 text-[#00FFC2]" />
                </div>
              )}
              
              <div className={`max-w-[70%] ${msg.role === 'user' ? 'bg-[#00FFC2]/10' : 'bg-white/5'} rounded-lg px-4 py-2`}>
                <p className="text-sm text-white/90">{msg.content}</p>
              </div>
              
              {msg.role === 'user' && (
                <div className="w-8 h-8 rounded-full bg-white/10 flex items-center justify-center">
                  <User className="w-4 h-4 text-white/70" />
                </div>
              )}
            </div>
          ))}
        </div>
      </div>
      
      {/* Command Input */}
      <div className="command-input-container">
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && handleSend()}
          placeholder="Ask Sovereign anything..."
          className="command-input"
        />
        <button onClick={handleSend} className="command-button">
          Send
        </button>
      </div>
    </div>
  );
}
