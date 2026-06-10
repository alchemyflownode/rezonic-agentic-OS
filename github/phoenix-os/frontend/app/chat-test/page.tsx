'use client';

import { useState, useRef, useEffect } from 'react';

export default function ChatTest() {
  const [messages, setMessages] = useState<{role: string, content: string, id: string}[]>([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const endRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const sendMessage = async () => {
    if (!input.trim() || loading) return;
    const userText = input.trim();
    setInput('');
    setLoading(true);
    
    // Add user message
    setMessages(prev => [...prev, {
      id: Date.now().toString(),
      role: 'user',
      content: userText
    }]);
    
    // Add loading message
    const assistantId = (Date.now() + 1).toString();
    setMessages(prev => [...prev, {
      id: assistantId,
      role: 'assistant',
      content: '⏳ Processing...'
    }]);
    
    try {
      const response = await fetch('http://localhost:8002/kernel/stream', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ task: userText })
      });
      
      const reader = response.body?.getReader();
      const decoder = new TextDecoder();
      let fullContent = '';
      
      while (reader) {
        const { done, value } = await reader.read();
        if (done) break;
        const chunk = decoder.decode(value);
        const lines = chunk.split('\n');
        
        for (const line of lines) {
          if (line.startsWith('data: ')) {
            try {
              const data = JSON.parse(line.substring(6));
              if (data.type === 'reflex') {
                fullContent = data.content;
                setMessages(prev => prev.map(msg =>
                  msg.id === assistantId ? { ...msg, content: fullContent } : msg
                ));
              } else if (data.type === 'token') {
                fullContent += data.content;
                setMessages(prev => prev.map(msg =>
                  msg.id === assistantId ? { ...msg, content: fullContent } : msg
                ));
              }
            } catch (e) {}
          }
        }
      }
      
      if (!fullContent) {
        setMessages(prev => prev.map(msg =>
          msg.id === assistantId ? { ...msg, content: '⚠️ No response' } : msg
        ));
      }
    } catch (error) {
      setMessages(prev => prev.map(msg =>
        msg.id === assistantId ? { ...msg, content: `❌ Error: ${error}` } : msg
      ));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-900 text-white p-6">
      <div className="max-w-2xl mx-auto">
        <h1 className="text-2xl font-bold mb-4">Phoenix Chat Test</h1>
        <div className="bg-gray-800 rounded-lg p-4 h-96 overflow-y-auto mb-4">
          {messages.length === 0 && (
            <div className="text-gray-500 text-center">Send a command like /portfolio</div>
          )}
          {messages.map(msg => (
            <div key={msg.id} className={`mb-2 ${msg.role === 'user' ? 'text-right' : 'text-left'}`}>
              <div className={`inline-block p-2 rounded-lg ${msg.role === 'user' ? 'bg-blue-600' : 'bg-gray-700'}`}>
                {msg.content}
              </div>
            </div>
          ))}
          <div ref={endRef} />
        </div>
        <div className="flex gap-2">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && sendMessage()}
            placeholder="Type /portfolio or /health..."
            className="flex-1 p-2 rounded bg-gray-800 border border-gray-700 text-white"
            disabled={loading}
          />
          <button
            onClick={sendMessage}
            disabled={loading}
            className="px-4 py-2 bg-blue-600 rounded hover:bg-blue-700 disabled:opacity-50"
          >
            Send
          </button>
        </div>
      </div>
    </div>
  );
}
