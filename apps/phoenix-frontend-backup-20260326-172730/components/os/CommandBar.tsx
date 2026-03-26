'use client'

import { useState, useRef, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { Terminal } from 'lucide-react'

const commands = [
  { cmd: '/workers', path: '/system/workers' },
  { cmd: '/memory', path: '/system/memory' },
  { cmd: '/constitution', path: '/system/constitution' },
  { cmd: '/scanner', path: '/system/scanner' },
  { cmd: '/trading', path: '/trading/dashboard' },
  { cmd: '/strategies', path: '/trading/strategies' },
]

export const CommandBar = () => {
  const [input, setInput] = useState('')
  const [suggestions, setSuggestions] = useState<typeof commands>([])
  const inputRef = useRef<HTMLInputElement>(null)
  const router = useRouter()

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') inputRef.current?.blur()
    }
    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [])

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = e.target.value
    setInput(value)
    
    if (value.startsWith('/')) {
      setSuggestions(commands.filter(c => c.cmd.startsWith(value)))
    } else {
      setSuggestions([])
    }
  }

  const handleSubmit = () => {
    const cmd = commands.find(c => c.cmd === input)
    if (cmd?.path) {
      router.push(cmd.path)
      setInput('')
      setSuggestions([])
    }
  }

  return (
    <div className="relative border-t border-zinc-800">
      <div className="flex items-center px-4 py-2">
        <Terminal className="w-4 h-4 text-zinc-500 mr-2" />
        <input
          ref={inputRef}
          type="text"
          value={input}
          onChange={handleChange}
          onKeyDown={(e) => e.key === 'Enter' && handleSubmit()}
          placeholder="Type / for commands..."
          className="flex-1 bg-transparent text-sm text-white outline-none placeholder:text-zinc-600"
        />
      </div>
      
      {suggestions.length > 0 && (
        <div className="absolute bottom-full left-0 right-0 mb-1 bg-zinc-900 border border-zinc-800 rounded p-1">
          {suggestions.map((s) => (
            <button
              key={s.cmd}
              onClick={() => {
                setInput(s.cmd)
                setSuggestions([])
              }}
              className="w-full text-left px-3 py-2 text-sm hover:bg-zinc-800 rounded"
            >
              <span className="text-purple-400">{s.cmd}</span>
              <span className="text-zinc-500 text-xs ml-2">→ {s.path}</span>
            </button>
          ))}
        </div>
      )}
    </div>
  )
}