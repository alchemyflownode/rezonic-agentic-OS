// app/dashboard/page.tsx
'use client';

import React, { useState, useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Zap, Cpu, Globe, Terminal, Activity, ShieldCheck,
  ChevronRight, Bot, User, Network, Shield, Search,
  Scan, Brain, Database, Lock, BookOpen,
  TrendingUp, Code, Layout, GitBranch, Play, FileCode,
  Workflow, CheckCircle2, XCircle, Gauge, Send, Sparkles, Menu
} from 'lucide-react';
import { SovereignMessage } from '@/components/SovereignMessage';

// ==========================================
// CONFIGURATION
// ==========================================
const API_BASE = 'http://localhost:8002';
const fadeUp = { initial: { opacity: 0, y: 20 }, animate: { opacity: 1, y: 0 } };

interface Message {
  id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  narrative?: string[];
  driftLock?: string;
  timestamp: string;
  isStreaming?: boolean;
}

// ==========================================
// COMMAND DATABASE
// ==========================================
const commandGroups: Record<string, any[]> = {
  "🦊 SOVEREIGN OS": [
    { name: "/health", desc: "Core system health check", example: "/health" },
    { name: "/workers", desc: "List all active swarm entities", example: "/workers" },
    { name: "/code", desc: "Generate code from intent", example: "/code add two numbers" },
  ],
  "🔍 REZ SCANNER": [
    { name: "/scan <path>", desc: "AST architecture mapping", example: "/scan ./src/kernel" },
    { name: "/list <path>", desc: "List directory contents", example: "/list D:\\Projects" },
  ],
  "⚖️ CONSTITUTION": [
    { name: "/constitution history", desc: "View constitutional rulings", example: "/constitution history" },
    { name: "/memory search", desc: "Search sovereign memory", example: "/memory search SCE" },
  ],
  "📈 TRADING": [
    { name: "/trade buy", desc: "Execute buy order", example: "/trade buy BTC 1000" },
    { name: "/trade sell", desc: "Execute sell order", example: "/trade sell BTC 500" },
  ],
};

// ==========================================
// COMMAND GROUP COMPONENT
// ==========================================
const CommandGroup = ({ title, commands, expanded, onToggle, searchTerm }: any) => {
  const filtered = commands.filter((cmd: any) =>
    cmd.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    cmd.desc.toLowerCase().includes(searchTerm.toLowerCase())
  );
  if (filtered.length === 0) return null;
  
  return (
    <div className="border border-white/10 rounded-xl overflow-hidden mb-2 shrink-0 bg-black/20">
      <button onClick={onToggle} className="w-full flex items-center justify-between p-3 hover:bg-white/5 transition-colors">
        <span className="text-[10px] font-mono font-bold tracking-widest text-[#7dcfff] uppercase">
          {title} <span className="text-[#565f89]">({filtered.length})</span>
        </span>
        <ChevronRight className={`w-3 h-3 text-[#565f89] transition-transform ${expanded ? 'rotate-90' : ''}`} />
      </button>
      <AnimatePresence>
        {expanded && (
          <motion.div initial={{ height: 0 }} animate={{ height: 'auto' }} exit={{ height: 0 }} className="overflow-hidden">
            <div className="p-3 space-y-2 border-t border-white/5">
              {filtered.map((cmd: any, i: number) => (
                <div key={i} className="p-2 rounded-lg hover:bg-white/5 transition-colors">
                  <div className="flex items-start gap-2">
                    <div className="w-1.5 h-1.5 rounded-full bg-[#7dcfff] mt-1.5" />
                    <div className="flex-1">
                      <code className="text-[10px] font-mono font-bold text-white">{cmd.name}</code>
                      <p className="text-[9px] text-[#565f89] mt-0.5">{cmd.desc}</p>
                      <div className="mt-1 text-[8px] font-mono text-[#7dcfff]/70">ex: {cmd.example}</div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
};

// ==========================================
// MAIN DASHBOARD
// ==========================================
export default function SovereignDashboard() {
  const [mounted, setMounted] = useState(false);
  const [time, setTime] = useState('');
  const [kernelStatus, setKernelStatus] = useState<'online' | 'offline' | 'checking'>('checking');
  const [workerCount, setWorkerCount] = useState(0);
  const [consciousnessLevel] = useState('SENTIENT');
  const [govScore, setGovScore] = useState(98);
  const [messages, setMessages] = useState<Message[]>([]);
  const [prompt, setPrompt] = useState('');
  const [isStreaming, setIsStreaming] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
  const [expandedGroup, setExpandedGroup] = useState<string | null>('🦊 SOVEREIGN OS');
  const [suggestions, setSuggestions] = useState<string[]>([]);
  const [showSuggestions, setShowSuggestions] = useState(false);
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  
  const chatEndRef = useRef<HTMLDivElement>(null);
  const suggestionsRef = useRef<HTMLDivElement>(null);

  const allCommands = Object.values(commandGroups).flat().map(cmd => cmd.name);

  // Clock Effect
  useEffect(() => {
    const clock = setInterval(() => {
      setTime(new Date().toLocaleTimeString('en-US', { hour12: false, hour: '2-digit', minute: '2-digit', second: '2-digit' }));
    }, 1000);
    return () => clearInterval(clock);
  }, []);

  // Fetch System Data
  const fetchData = async () => {
    try {
      const healthRes = await fetch(`${API_BASE}/health`);
      if (healthRes.ok) {
        const data = await healthRes.json();
        setKernelStatus('online');
        setWorkerCount(data.workers || 0);
        setGovScore(Math.floor(data.integrity_score || 98.2));
      } else {
        setKernelStatus('offline');
      }
    } catch (err) {
      setKernelStatus('offline');
    }
  };

  useEffect(() => {
    setMounted(true);
    fetchData();
    const interval = setInterval(fetchData, 10000);
    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleInputChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    const value = e.target.value;
    setPrompt(value);
    if (value.length > 0) {
      const filtered = allCommands.filter(cmd => cmd.toLowerCase().startsWith(value.toLowerCase())).slice(0, 5);
      setSuggestions(filtered);
      setShowSuggestions(filtered.length > 0);
    } else {
      setSuggestions([]);
      setShowSuggestions(false);
    }
  };

  const handleSuggestionClick = (suggestion: string) => {
    setPrompt(suggestion);
    setShowSuggestions(false);
  };

  const handleTransmit = async () => {
    if (!prompt.trim() || isStreaming) return;
    
    const userText = prompt;
    setPrompt('');
    setIsStreaming(true);
    setShowSuggestions(false);

    const timeStamp = new Date().toLocaleTimeString();
    const assistantId = crypto.randomUUID();
    
    setMessages(prev => [
      ...prev, 
      { id: crypto.randomUUID(), role: 'user', content: userText, timestamp: timeStamp },
      { id: assistantId, role: 'assistant', content: '', timestamp: timeStamp, isStreaming: true }
    ]);

    try {
      const response = await fetch(`${API_BASE}/kernel/stream`, {
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
        fullContent += decoder.decode(value);
        setMessages(prev => prev.map(m => m.id === assistantId ? { ...m, content: fullContent } : m));
      }
      setMessages(prev => prev.map(m => m.id === assistantId ? { ...m, isStreaming: false } : m));
    } catch (error) {
      setMessages(prev => prev.map(m => m.id === assistantId ? { ...m, content: '❌ Connection lost', isStreaming: false } : m));
    } finally {
      setIsStreaming(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleTransmit();
    }
  };

  const totalGlossaryCommands = Object.values(commandGroups).reduce((acc, cmds) => acc + cmds.length, 0);

  if (!mounted) return null;

  return (
    <div className="h-screen bg-gradient-to-br from-[#0a0a0c] via-[#050505] to-[#0a0a0c] text-[#c0caf5] overflow-hidden">
      
      {/* Animated Grid Background */}
      <div className="fixed inset-0 pointer-events-none opacity-20">
        <div className="absolute inset-0 bg-[radial-gradient(circle_at_50%_50%,_#7dcfff_0%,_transparent_50%)] opacity-5" />
        <div className="absolute inset-0" style={{ backgroundImage: 'linear-gradient(to right, #7dcfff0a 1px, transparent 1px), linear-gradient(to bottom, #7dcfff0a 1px, transparent 1px)', backgroundSize: '40px 40px' }} />
      </div>

      {/* Glass Header */}
      <motion.header 
        initial={{ y: -20, opacity: 0 }}
        animate={{ y: 0, opacity: 1 }}
        className="relative z-10 flex items-center justify-between px-6 py-3 border-b border-[#7dcfff]/10 bg-black/40 backdrop-blur-xl"
      >
        <div className="flex items-center gap-8 text-[10px] font-mono">
          <div className="flex items-center gap-2">
            <motion.div 
              animate={{ scale: [1, 1.2, 1] }}
              transition={{ duration: 2, repeat: Infinity }}
              className={`w-2 h-2 rounded-full ${kernelStatus === 'online' ? 'bg-[#9ece6a]' : 'bg-[#f7768e]'} shadow-[0_0_8px_${kernelStatus === 'online' ? '#9ece6a' : '#f7768e'}]`} 
            />
            <span className={kernelStatus === 'online' ? 'text-[#9ece6a]' : 'text-[#f7768e]'}>
              KERNEL: {kernelStatus === 'online' ? 'ACTIVE' : 'OFFLINE'}
            </span>
          </div>
          <div className="flex items-center gap-2">
            <Shield className="w-3 h-3 text-[#9B72CB]" />
            <span>SCE: <span className="text-[#7dcfff]">ENFORCED</span></span>
          </div>
          <span className="text-[#565f89]">{time} UTC</span>
        </div>
        
        <div className="flex items-center gap-4">
          <div className="text-right">
            <div className="text-[8px] text-[#565f89] uppercase tracking-wider">Consciousness</div>
            <div className="text-xs font-bold text-[#7dcfff]">{consciousnessLevel}</div>
          </div>
          <div className="text-right">
            <div className="text-[8px] text-[#565f89] uppercase tracking-wider">Workers</div>
            <div className="text-xs font-bold text-white">{workerCount}</div>
          </div>
        </div>
      </motion.header>

      {/* Main Content - 3 Column Layout */}
      <div className="relative z-10 h-[calc(100vh-60px)] flex p-4 gap-4 overflow-hidden">
        
        {/* LEFT: System Status */}
        <motion.aside 
          initial={{ x: -20, opacity: 0 }}
          animate={{ x: 0, opacity: 1 }}
          className="w-80 bg-black/30 backdrop-blur-xl border border-[#7dcfff]/10 rounded-2xl p-5 flex flex-col gap-5 shadow-[0_8px_32px_rgba(0,0,0,0.4)]"
        >
          <div>
            <h3 className="text-[10px] text-[#565f89] mb-4 flex items-center gap-2 font-mono uppercase tracking-wider">
              <Activity className="w-3 h-3 text-[#7dcfff]" /> SYSTEM STATUS
            </h3>
            <div className="space-y-3">
              <div className="flex justify-between items-center p-3 bg-white/5 rounded-xl">
                <span className="text-xs">Kernel Load</span>
                <div className="w-32 h-1.5 bg-white/10 rounded-full overflow-hidden">
                  <div className="h-full w-[34%] bg-gradient-to-r from-[#7dcfff] to-[#9B72CB] rounded-full" />
                </div>
                <span className="text-xs font-mono text-[#7dcfff]">34%</span>
              </div>
              <div className="flex justify-between items-center p-3 bg-white/5 rounded-xl">
                <span className="text-xs">Worker Pool</span>
                <span className="text-xs font-mono text-white">{workerCount} / 64</span>
              </div>
              <div className="flex justify-between items-center p-3 bg-white/5 rounded-xl">
                <span className="text-xs">SCE Integrity</span>
                <span className="text-xs font-mono text-[#9ece6a]">{govScore}%</span>
              </div>
            </div>
          </div>

          <div>
            <h3 className="text-[10px] text-[#565f89] mb-3 flex items-center gap-2 font-mono uppercase tracking-wider">
              <Shield className="w-3 h-3 text-[#9B72CB]" /> CONSTITUTION
            </h3>
            <div className="space-y-2">
              {['Data Sovereignty', 'No Financial Advice', 'Risk Disclosure', 'Transparency', 'Objectivity'].map((principle, i) => (
                <div key={i} className="flex items-center gap-2 text-[10px] text-[#c0caf5] p-2 bg-white/5 rounded-lg">
                  <CheckCircle2 className="w-3 h-3 text-[#9ece6a]" />
                  <span className="truncate">{principle}</span>
                </div>
              ))}
            </div>
          </div>

          <div className="mt-auto pt-4 border-t border-[#7dcfff]/10">
            <div className="flex items-center gap-2 text-[9px] text-[#565f89]">
              <div className="w-1.5 h-1.5 rounded-full bg-[#9ece6a] animate-pulse" />
              <span>Constitutional AI • Active</span>
            </div>
          </div>
        </motion.aside>

        {/* CENTER: Sovereign Chat */}
        <motion.main 
          initial={{ y: 20, opacity: 0 }}
          animate={{ y: 0, opacity: 1 }}
          transition={{ delay: 0.1 }}
          className="flex-1 flex flex-col bg-black/30 backdrop-blur-xl border border-[#7dcfff]/10 rounded-2xl overflow-hidden shadow-[0_8px_32px_rgba(0,0,0,0.4)]"
        >
          <div className="p-4 border-b border-[#7dcfff]/10 bg-gradient-to-r from-[#9B72CB]/10 to-transparent">
            <div className="flex items-center gap-2">
              <Sparkles className="w-4 h-4 text-[#9B72CB]" />
              <h2 className="text-sm font-bold tracking-wide">Sovereign Intelligence</h2>
              <div className="ml-auto flex items-center gap-2">
                <div className="w-1.5 h-1.5 rounded-full bg-[#9ece6a] animate-pulse" />
                <span className="text-[8px] font-mono text-[#565f89]">SCE v1.0</span>
              </div>
            </div>
          </div>

          {/* Chat Messages */}
          <div className="flex-1 overflow-y-auto p-6 space-y-4 custom-scrollbar">
            {messages.length === 0 ? (
              <div className="h-full flex flex-col items-center justify-center text-center">
                <div className="w-20 h-20 rounded-full border-2 border-[#7dcfff]/20 flex items-center justify-center mb-4">
                  <Zap className="w-8 h-8 text-[#7dcfff]" />
                </div>
                <h3 className="text-lg font-bold bg-gradient-to-r from-[#c0caf5] to-[#7dcfff] bg-clip-text text-transparent">Sovereign AI Terminal</h3>
                <p className="text-xs text-[#565f89] mt-2 max-w-md">Execute commands or ask questions. Constitutional AI ensures ethical responses.</p>
              </div>
            ) : (
              messages.map((msg, idx) => (
                <motion.div
                  key={msg.id}
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
                >
                  <div className={`max-w-[80%] p-4 rounded-2xl ${msg.role === 'user' ? 'bg-gradient-to-r from-[#7dcfff]/20 to-[#9B72CB]/20 border border-[#7dcfff]/30 rounded-br-sm' : 'bg-white/5 border border-white/10 rounded-bl-sm'}`}>
                    <p className="text-sm leading-relaxed whitespace-pre-wrap">{msg.content}</p>
                    <div className="flex items-center gap-2 mt-2">
                      <span className="text-[8px] text-[#565f89]">{msg.timestamp}</span>
                      {msg.driftLock && (
                        <span className="text-[7px] font-mono text-[#9ece6a]">🔒 {msg.driftLock.substring(0, 8)}</span>
                      )}
                    </div>
                  </div>
                </motion.div>
              ))
            )}
            <div ref={chatEndRef} />
          </div>

          {/* Input Area */}
          <div className="p-4 border-t border-[#7dcfff]/10 bg-black/20">
            <div className="flex gap-2">
              <div className="flex-1 relative">
                <textarea
                  value={prompt}
                  onChange={handleInputChange}
                  onKeyDown={handleKeyDown}
                  placeholder={kernelStatus === 'online' ? "Execute command or ask a question..." : "Awaiting kernel connection..."}
                  className="w-full bg-black/50 border border-[#7dcfff]/20 rounded-xl px-4 py-3 text-sm text-[#c0caf5] placeholder:text-[#565f89] outline-none resize-none focus:border-[#7dcfff]/50 transition-all"
                  rows={1}
                />
                {showSuggestions && suggestions.length > 0 && (
                  <div ref={suggestionsRef} className="absolute bottom-full left-0 right-0 mb-2 bg-black/90 border border-[#7dcfff]/20 rounded-xl p-2">
                    {suggestions.map((suggestion, i) => (
                      <div key={i} onClick={() => handleSuggestionClick(suggestion)} className="px-3 py-2 hover:bg-white/10 cursor-pointer text-xs text-[#7dcfff] rounded-lg transition-colors">
                        {suggestion}
                      </div>
                    ))}
                  </div>
                )}
              </div>
              <button
                onClick={handleTransmit}
                disabled={!prompt.trim() || isStreaming || kernelStatus !== 'online'}
                className="px-6 py-3 rounded-xl bg-gradient-to-r from-[#7dcfff]/20 to-[#9B72CB]/20 border border-[#7dcfff]/30 text-[#7dcfff] hover:shadow-[0_0_20px_rgba(125,207,255,0.2)] transition-all disabled:opacity-50"
              >
                <Send className="w-4 h-4" />
              </button>
            </div>
            <div className="flex justify-between mt-3 text-[8px] text-[#565f89] font-mono">
              <div className="flex gap-3">
                <span>ENTER • Send</span>
                <span>SHIFT+ENTER • New line</span>
              </div>
              <div className="flex gap-2">
                {['/health', '/workers', '/code'].map(cmd => (
                  <button key={cmd} onClick={() => setPrompt(cmd)} className="hover:text-[#7dcfff] transition-colors">{cmd}</button>
                ))}
              </div>
            </div>
          </div>
        </motion.main>

        {/* RIGHT: Command Lexicon */}
        <motion.aside 
          initial={{ x: 20, opacity: 0 }}
          animate={{ x: 0, opacity: 1 }}
          transition={{ delay: 0.2 }}
          className="w-80 bg-black/30 backdrop-blur-xl border border-[#7dcfff]/10 rounded-2xl p-5 flex flex-col gap-4 shadow-[0_8px_32px_rgba(0,0,0,0.4)]"
        >
          <div className="flex items-center justify-between">
            <h3 className="text-[10px] text-[#565f89] flex items-center gap-2 font-mono uppercase tracking-wider">
              <BookOpen className="w-3 h-3 text-[#7dcfff]" /> COMMAND LEXICON
            </h3>
            <span className="text-[8px] text-[#565f89]">{totalGlossaryCommands} commands</span>
          </div>
          
          <div className="relative">
            <Search className="w-3 h-3 absolute left-3 top-2.5 text-[#565f89]" />
            <input
              type="text"
              placeholder="Search commands..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full bg-black/50 border border-[#7dcfff]/20 rounded-xl py-2 pl-8 pr-3 text-xs text-white placeholder:text-[#565f89] outline-none focus:border-[#7dcfff]/50"
            />
          </div>

          <div className="flex-1 overflow-y-auto custom-scrollbar space-y-2">
            {Object.entries(commandGroups).map(([group, commands]) => (
              <CommandGroup
                key={group}
                title={group}
                commands={commands}
                expanded={expandedGroup === group}
                onToggle={() => setExpandedGroup(expandedGroup === group ? null : group)}
                searchTerm={searchTerm}
              />
            ))}
          </div>

          <div className="pt-4 border-t border-[#7dcfff]/10">
            <div className="bg-gradient-to-r from-[#7dcfff]/5 to-[#9B72CB]/5 rounded-xl p-3">
              <div className="flex items-center gap-2 mb-2">
                <Shield className="w-3 h-3 text-[#9B72CB]" />
                <span className="text-[8px] font-mono text-[#7dcfff] uppercase tracking-wider">Constitutional AI</span>
              </div>
              <p className="text-[9px] text-[#565f89] leading-relaxed">
                All commands filtered through SCE Protocol. Responses are constitutionally verified.
              </p>
            </div>
          </div>
        </motion.aside>
      </div>

      <style jsx global>{`
        .custom-scrollbar::-webkit-scrollbar { width: 4px; }
        .custom-scrollbar::-webkit-scrollbar-track { background: rgba(125,207,255,0.05); border-radius: 10px; }
        .custom-scrollbar::-webkit-scrollbar-thumb { background: rgba(125,207,255,0.3); border-radius: 10px; }
        .custom-scrollbar::-webkit-scrollbar-thumb:hover { background: rgba(125,207,255,0.5); }
        textarea::-webkit-scrollbar { display: none; }
      `}</style>
    </div>
  );
}