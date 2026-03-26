'use client'

import { useState, useRef, useEffect } from 'react'
import { Send } from 'lucide-react'
import { SovereignMessage } from './SovereignMessage'

interface Message {
  id: string
  role: 'user' | 'assistant' | 'system'
  content: string
  narrative?: string[]
  driftLock?: string
  timestamp: string
}

export const ChatConsole = () => {
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState('')
  const [isStreaming, setIsStreaming] = useState(false)
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const API_BASE = 'http://localhost:8001' // Your Phoenix backend

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const sendMessage = async () => {
    if (!input.trim() || isStreaming) return

    const userText = input
    setInput('')
    setIsStreaming(true)

    const timeNow = new Date().toLocaleTimeString()
    
    // Add user message
    setMessages(prev => [...prev, {
      id: Date.now().toString(),
      role: 'user',
      content: userText,
      timestamp: timeNow
    }])

    // Add placeholder for assistant
    const assistantId = (Date.now() + 1).toString()
    setMessages(prev => [...prev, {
      id: assistantId,
      role: 'assistant',
      content: '',
      timestamp: timeNow
    }])

    try {
      // Call your Phoenix backend
      const res = await fetch(`${API_BASE}/kernel/stream`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ task: userText })
      })
      
      const data = await res.json()
      
      // Update with response
      setMessages(prev => prev.map(msg => 
        msg.id === assistantId ? {
          ...msg,
          content: data.content || 'No response',
          narrative: data.narrative,
          driftLock: data.drift_lock
        } : msg
      ))

    } catch (error) {
      setMessages(prev => prev.map(msg => 
        msg.id === assistantId ? {
          ...msg,
          content: '⚠️ Connection error',
          role: 'system'
        } : msg
      ))
    } finally {
      setIsStreaming(false)
    }
  }

  return (
    <div className="flex flex-col h-full bg-[#1a1b26] rounded-lg border border-[#292e42]">
      {/* Messages Area */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.length === 0 ? (
          <div className="h-full flex items-center justify-center text-[#565f89]">
            <div className="text-center">
              <div className="w-12 h-12 mx-auto mb-4 rounded-full bg-[#24283b] border border-[#292e42] flex items-center justify-center">
                <span className="text-2xl">🤖</span>
              </div>
              <p className="text-sm">Send a message to start</p>
            </div>
          </div>
        ) : (
          messages.map((msg) => (
            <SovereignMessage
              key={msg.id}
              content={msg.content}
              role={msg.role}
              narrative={msg.narrative}
              driftLock={msg.driftLock}
              timestamp={msg.timestamp}
              isStreaming={isStreaming && msg.id === messages[messages.length-1]?.id}
            />
          ))
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Input Area */}
      <div className="p-3 border-t border-[#292e42]">
        <div className="flex gap-2">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && sendMessage()}
            placeholder="Type a message or command..."
            className="flex-1 bg-[#24283b] text-[#c0caf5] p-2 rounded outline-none border border-[#292e42] focus:border-[#7dcfff] placeholder:text-[#565f89]"
            disabled={isStreaming}
          />
          <button
            onClick={sendMessage}
            disabled={isStreaming || !input.trim()}
            className="px-4 bg-[#7dcfff] text-[#1a1b26] rounded hover:bg-[#bb9af7] transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <Send className="w-4 h-4" />
          </button>
        </div>
      </div>
    </div>
  )
}