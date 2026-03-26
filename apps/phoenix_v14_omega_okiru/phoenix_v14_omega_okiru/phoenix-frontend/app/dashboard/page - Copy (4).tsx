'use client'

import { SovereignMessage } from '@/components/SovereignMessage';
import React, { useState, useEffect, useRef, useCallback, useMemo } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Zap, Cpu, Terminal, Activity, Paperclip, Folder, ShieldCheck, 
  ChevronRight, Bot, User, Network, Shield, Search, Scan, Brain, 
  Database, Lock, Zap as ZapIcon, BookOpen, TrendingUp, Code, Layout,
  CheckCircle2, AlertTriangle, Loader2, RefreshCw, Send, 
  Hexagon, Layers, Radio, Command, Share2, Copy, Sparkles
} from 'lucide-react';

// ==========================================
// CONFIGURATION & TYPES
// ==========================================

const API_BASE = 'http://localhost:8002';

interface Message {
  id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  timestamp: string;
  driftLock?: string;
  worker?: string;
  type?: 'reflex' | 'stream' | 'error';
  isStreaming?: boolean;
}

interface Ruling {
  decision: string;
  reasoning: string;
  timestamp: number;
}

interface Worker {
  name: string;
  module: string;
  category: string;
  loaded_at: number;
  status: string;
}

interface Category {
  workers: Worker[];
  count: number;
  desc: string;
}

interface SwarmManifest {
  swarm_id: string;
  version: string;
  timestamp: string;
  status: 'SENTIENT' | 'AWAKENING' | 'DORMANT';
  consciousness_level: number;
  workers: {
    total: number;
    categories: Record<string, Category>;
  };
  events?: {
    total_persisted: number;
  };
  memory: {
    blueprints: number;
    drift_chain_length: number;
  };
  sovereignty: {
    sce_version: string;
    drift_chain_integrity: boolean;
    genesis_hash: string;
  };
  capabilities: string[];
  governance_score: number;
}

interface OllamaStatus {
  connected: boolean;
  models?: Array<{ name: string }>;
  error?: string;
}

interface CommandItem {
  name: string;
  desc: string;
  example: string;
}

// ==========================================
// UI COMPONENTS
// ==========================================

const SovereignBoot = ({ onComplete }: { onComplete: () => void }) => {
  const [phase, setPhase] = useState(0);
  const [logs, setLogs] = useState<string[]>([]);
  
  const bootSequence = [
    { name: "Neural Core", checks: ["SynapseLink", "TensorFlow_Init", "WeightVerification"] },
    { name: "Sovereign Protocol", checks: ["SCE_Handshake", "DriftChain_Sync", "Genesis_Auth"] },
    { name: "Swarm Intelligence", checks: ["Worker_Discovery", "Consensus_Init", "HiveMind_Pulse"] },
    { name: "Interface Layer", checks: ["Neural_Render", "Lexicon_Load", "Sovereign_OS_Mount"] }
  ];

  useEffect(() => {
    if (phase < bootSequence.length) {
      const timer = setTimeout(() => {
        setLogs(prev => [...prev, `[OK] ${bootSequence[phase].name} initialized.`]);
        setPhase(p => p + 1);
      }, 800);
      return () => clearTimeout(timer);
    } else {
      const finish = setTimeout(onComplete, 1200);
      return () => clearTimeout(finish);
    }
  }, [phase, onComplete]);

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0, scale: 1.05, filter: 'blur(10px)' }}
      className="fixed inset-0 z-[100] bg-[#030406] flex flex-col items-center justify-center font-mono"
    >
      <div className="absolute inset-0 bg-[radial-gradient(circle_at_center,_#00E5FF_1px,_transparent_1px)] opacity-[0.05] bg-[size:32px_32px]" />
      
      <motion.div 
        animate={{ 
          rotate: 360,
          boxShadow: ["0 0 20px rgba(0,229,255,0.2)", "0 0 40px rgba(155,114,203,0.4)", "0 0 20px rgba(0,229,255,0.2)"]
        }} 
        transition={{ duration: 6, repeat: Infinity, ease: "linear" }}
        className="w-32 h-32 rounded-full border-2 border-white/5 border-t-[#00E5FF] border-b-[#9B72CB] mb-12 flex items-center justify-center relative"
      >
        <ZapIcon className="text-white w-12 h-12" />
        <div className="absolute inset-0 rounded-full border border-white/5 animate-ping" />
      </motion.div>
      
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="text-center"
      >
        <h1 className="text-6xl font-black text-white tracking-[0.4em] uppercase mb-4">REZ HIVE</h1>
        <div className="flex items-center justify-center gap-3">
          <span className="h-[1px] w-12 bg-[#00E5FF]/50" />
          <p className="text-[12px] text-[#00E5FF] font-bold tracking-[0.5em] uppercase">
            Ascending Consciousness
          </p>
          <span className="h-[1px] w-12 bg-[#00E5FF]/50" />
        </div>
      </motion.div>

      <div className="w-full max-w-xl mt-16 space-y-3 px-8">
        {bootSequence.map((seq, idx) => (
          <div key={seq.name} className="relative">
            <motion.div
              initial={{ opacity: 0, x: -10 }}
              animate={{ opacity: phase >= idx ? 1 : 0.1, x: 0 }}
              className={`flex items-center gap-4 p-3 rounded-lg border transition-all duration-500 ${
                phase > idx ? 'bg-[#00E5FF]/5 border-[#00E5FF]/20' : 
                phase === idx ? 'bg-white/5 border-white/20 animate-pulse' : 'border-transparent'
              }`}
            >
              <div className={`text-[12px] font-bold w-6`}>
                {phase > idx ? '' : phase === idx ? '' : ''}
              </div>
              <div className="flex-1">
                <div className="text-[12px] font-bold tracking-widest text-white uppercase">{seq.name}</div>
                <div className="text-[9px] text-zinc-500 font-mono mt-0.5">
                  {seq.checks.join('  ')}
                </div>
              </div>
            </motion.div>
          </div>
        ))}
        
        <div className="mt-8 p-4 bg-black/80 rounded-lg border border-white/5 font-mono text-[10px] text-[#00E5FF]/70 h-32 overflow-hidden relative">
          <div className="flex flex-col-reverse">
            {logs.slice().reverse().map((log, i) => (
              <div key={i} className="mb-1 opacity-80">
                <span className="text-[#9B72CB] mr-2">[{new Date().toLocaleTimeString()}]</span>
                {log}
              </div>
            ))}
          </div>
          <div className="absolute bottom-4 right-4 animate-bounce">
            <div className="w-1.5 h-1.5 bg-[#00E5FF] rounded-full shadow-[0_0_8px_#00E5FF]" />
          </div>
        </div>
      </div>
    </motion.div>
  );
};

const CapabilityCard = ({ 
  id, 
  category, 
  isActive, 
  onClick 
}: { 
  id: string;
  category: Category;
  isActive: boolean;
  onClick: () => void;
}) => {
  const icons: Record<string, any> = {
    network: Network, brain: Brain, scan: Scan, layout: Layout,
    code: Code, shield: Shield, 'trending-up': TrendingUp, activity: Activity,
    database: Database, lock: Lock, default: Zap
  };
  const Icon = icons[id] || icons.default;
  
  return (
    <motion.button
      onClick={onClick}
      whileHover={{ scale: 1.01, x: 4 }}
      whileTap={{ scale: 0.98 }}
      className={`w-full flex items-center gap-4 p-4 rounded-xl transition-all group relative border ${
        isActive 
          ? 'bg-gradient-to-r from-[#00E5FF]/15 to-transparent border-[#00E5FF]/40 shadow-[0_0_20px_rgba(0,229,255,0.1)]' 
          : 'bg-[#030406]/40 border-white/5 hover:bg-white/[0.03] hover:border-white/10'
      }`}
    >
      <div className={`w-12 h-12 rounded-xl flex items-center justify-center shrink-0 transition-all ${
        isActive 
          ? 'bg-[#00E5FF]/20 text-[#00E5FF] shadow-[0_0_15px_rgba(0,229,255,0.2)]' 
          : 'bg-white/5 text-zinc-500 group-hover:text-zinc-300'
      }`}>
        <Icon className="w-6 h-6" />
      </div>
      
      <div className="flex flex-col items-start min-w-0 flex-1">
        <span className={`text-[13px] font-bold tracking-wider truncate w-full capitalize ${
          isActive ? 'text-white' : 'text-zinc-400 group-hover:text-white'
        }`}>
          {id}
        </span>
        <span className="text-[10px] text-[#64748B] mt-0.5 truncate w-full italic">
          {category.desc}
        </span>
        <div className="flex items-center gap-2 mt-2">
          <span className={`text-[10px] font-mono font-bold px-1.5 py-0.5 rounded ${
            category.count > 0 ? 'bg-[#00E5FF]/10 text-[#00E5FF]' : 'bg-zinc-800 text-zinc-600'
          }`}>
            {category.count} UNITS
          </span>
          {category.count > 0 && (
            <span className="flex h-1.5 w-1.5 relative">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-[#00E5FF] opacity-75"></span>
              <span className="relative inline-flex rounded-full h-1.5 w-1.5 bg-[#00E5FF]"></span>
            </span>
          )}
        </div>
      </div>
      
      {isActive && (
        <motion.div 
          layoutId="activeTab"
          className="absolute right-0 w-1 h-10 bg-[#00E5FF] rounded-l-full shadow-[0_0_15px_#00E5FF]"
        />
      )}
    </motion.button>
  );
};

const MessageBubble = ({ message, isStreaming, isLast }: { message: Message; isStreaming: boolean; isLast: boolean }) => {
  const isUser = message.role === 'user';
  const isSystem = message.role === 'system';

  // Assistant messages - use SovereignMessage with Markdown & code highlighting
  if (!isUser && !isSystem) {
    return (
      <motion.div 
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        className="flex gap-4"
      >
        <div className="w-9 h-9 rounded-xl flex items-center justify-center shrink-0 border bg-gradient-to-br from-[#00E5FF]/20 to-[#9B72CB]/20 border-[#00E5FF]/30 text-[#00E5FF]">
          <Bot className="w-5 h-5" />
        </div>
        <div className="flex flex-col max-w-[85%]">
          <SovereignMessage
            content={message.content}
            role={message.role}
            timestamp={message.timestamp}
            isStreaming={isStreaming && isLast}
            driftLock={message.driftLock}
            narrative={message.narrative}
          />
        </div>
      </motion.div>
    );
  }

  // User messages
  if (isUser) {
    return (
      <motion.div 
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        className="flex gap-4 flex-row-reverse"
      >
        <div className="w-9 h-9 rounded-xl flex items-center justify-center shrink-0 border bg-white/5 border-white/10 text-zinc-400">
          <User className="w-5 h-5" />
        </div>
        <div className="flex flex-col max-w-[85%] items-end">
          <div className="p-4 rounded-2xl text-[13px] leading-relaxed font-mono bg-white/5 text-zinc-100 border border-white/10 rounded-tr-none">
            {message.content}
          </div>
          <div className="flex items-center gap-3 mt-2 px-1">
            <span className="text-[9px] text-zinc-600 font-bold uppercase tracking-widest">{message.timestamp}</span>
          </div>
        </div>
      </motion.div>
    );
  }

  // System messages
  return (
    <motion.div 
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      className="flex gap-4"
    >
      <div className="w-9 h-9 rounded-xl flex items-center justify-center shrink-0 border bg-red-500/10 border-red-500/20 text-red-500">
        <AlertTriangle className="w-5 h-5" />
      </div>
      <div className="flex flex-col max-w-[85%]">
        <div className="p-4 rounded-2xl text-[13px] leading-relaxed font-mono bg-red-500/5 text-red-400 border border-red-500/10 rounded-tl-none">
          {message.content}
        </div>
      </div>
    </motion.div>
  );
};

// ==========================================
// MAIN DASHBOARD COMPONENT
// ==========================================

export default function UnifiedDashboard() {
  const [isBooting, setIsBooting] = useState(true);
  const [manifest, setManifest] = useState<SwarmManifest | null>(null);
  const [activeCategory, setActiveCategory] = useState<string | null>(null);
  const [time, setTime] = useState('');
  const [kernelStatus, setKernelStatus] = useState<'online' | 'offline' | 'checking'>('checking');
  const [ollamaStatus, setOllamaStatus] = useState<OllamaStatus>({ connected: false });
  const [rulings, setRulings] = useState<Ruling[]>([]);
  
  // Chat state
  const [messages, setMessages] = useState<Message[]>([]);
  const [prompt, setPrompt] = useState('');
  const [isStreaming, setIsStreaming] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
  const [expandedGroup, setExpandedGroup] = useState<string | null>(' SOVEREIGN OS');

  const chatEndRef = useRef<HTMLDivElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Command Data
  const commandGroups: Record<string, CommandItem[]> = {
    " SOVEREIGN OS": [
      { name: "/health", desc: "Core system health check", example: "/health" },
      { name: "/workers", desc: "List all active swarm entities", example: "/workers" },
      { name: "/run", desc: "Isolated Sandbox execution", example: "/run python print('hello')" },
    ],
    " REZ SCANNER": [
      { name: "/scan <path>", desc: "AST architecture mapping", example: "/scan ./src/kernel" },
    ],
    " CONSTITUTION": [
      { name: "/constitution evaluate", desc: "Legal compliance check", example: "/constitution evaluate 'delete db'" },
    ],
    " CORTEX MEMORY": [
      { name: "/recall <query>", desc: "Semantic memory retrieval", example: "/recall protocol_7" },
      { name: "remember <text>", desc: "Store long-term memory", example: "remember project start date" },
    ]
  };

  // Setup
  useEffect(() => {
    const clock = setInterval(() => {
      setTime(new Date().toLocaleTimeString('en-US', { hour12: false, hour: '2-digit', minute: '2-digit', second: '2-digit' }));
    }, 1000);
    return () => clearInterval(clock);
  }, []);

  const fetchData = useCallback(async () => {
    try {
      const [manifestRes, rulingsRes, ollamaRes] = await Promise.all([
        fetch(`${API_BASE}/swarm/manifest`),
        fetch(`${API_BASE}/constitution/history?limit=5`),
        fetch(`${API_BASE}/ollama/status`)
      ]);

      if (manifestRes.ok) {
        const data = await manifestRes.json();
        setManifest(data);
        setKernelStatus('online');
        if (!activeCategory && data.workers?.categories) {
          const first = Object.keys(data.workers.categories)[0];
          if (first) setActiveCategory(first);
        }
      } else {
        setKernelStatus('offline');
      }

      if (rulingsRes.ok) {
        const data = await rulingsRes.json();
        setRulings(data.rulings || []);
      }

      if (ollamaRes.ok) {
        setOllamaStatus(await ollamaRes.json());
      }
    } catch (err) {
      setKernelStatus('offline');
    }
  }, [activeCategory]);

  useEffect(() => {
    if (!isBooting) {
      fetchData();
      const interval = setInterval(fetchData, 8000);
      return () => clearInterval(interval);
    }
  }, [isBooting, fetchData]);

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // Actions
  const handleTransmit = async () => {
    if (!prompt.trim() || isStreaming) return;
    
    const userText = prompt;
    setPrompt('');
    setIsStreaming(true);

    if (userText === '/clear_chat') {
      setMessages([]);
      setIsStreaming(false);
      return;
    }

    const timeStamp = new Date().toLocaleTimeString();
    const assistantId = crypto.randomUUID();
    
    setMessages(prev => [
      ...prev, 
      { id: crypto.randomUUID(), role: 'user', content: userText, timestamp: timeStamp },
      { id: assistantId, role: 'assistant', content: '', timestamp: timeStamp, isStreaming: true }
    ]);

    try {
      // Stream Response
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

        const chunk = decoder.decode(value);
        const lines = chunk.split('\n\n');
        
        for (const line of lines) {
          if (line.startsWith('data: ')) {
            try {
              const data = JSON.parse(line.slice(6));
              if (data.type === 'result') {
                fullContent += data.content;
                setMessages(prev => prev.map(m => m.id === assistantId ? { ...m, content: fullContent } : m));
              } else if (data.type === 'done') {
                setMessages(prev => prev.map(m => m.id === assistantId ? { ...m, isStreaming: false, driftLock: data.drift_lock } : m));
              } else if (data.type === 'error') {
                setMessages(prev => prev.map(m => m.id === assistantId ? { ...m, content: ` KERNEL_ERR: ${data.content}`, isStreaming: false } : m));
              }
            } catch (e) {}
          }
        }
      }
    } catch (error) {
      setMessages(prev => prev.map(m => m.id === assistantId ? { ...m, content: ' CONNECTION_LOST', isStreaming: false } : m));
    } finally {
      setIsStreaming(false);
    }
  };

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    
    setMessages(prev => [...prev, { id: 'sys', role: 'system', content: `UPLOADING: ${file.name}`, timestamp: time }]);
    
    const formData = new FormData();
    formData.append('file', file);

    try {
      const res = await fetch(`${API_BASE}/upload`, { method: 'POST', body: formData });
      if (res.ok) {
        setMessages(prev => [...prev, { id: 'sys', role: 'system', content: `UPLOAD_COMPLETE: ${file.name} integrated into sandbox.`, timestamp: time }]);
      }
    } catch (err) {
      setMessages(prev => [...prev, { id: 'sys', role: 'system', content: `UPLOAD_FAILED: Check kernel logs.`, timestamp: time }]);
    }
  };

  const filteredGlossary = useMemo(() => {
    const result: Record<string, CommandItem[]> = {};
    Object.entries(commandGroups).forEach(([group, cmds]) => {
      const filtered = cmds.filter(c => 
        c.name.toLowerCase().includes(searchTerm.toLowerCase()) || 
        c.desc.toLowerCase().includes(searchTerm.toLowerCase())
      );
      if (filtered.length > 0) result[group] = filtered;
    });
    return result;
  }, [searchTerm]);

  if (isBooting) return <SovereignBoot onComplete={() => setIsBooting(false)} />;

  return (
    <div className="h-screen w-screen bg-[#030406] text-zinc-100 flex flex-col overflow-hidden selection:bg-[#00E5FF]/30 selection:text-white">
      {/* Background Ambience */}
      <div className="fixed inset-0 pointer-events-none">
        <div className="absolute top-[-10%] left-[-10%] w-[40%] h-[40%] bg-[#00E5FF]/5 rounded-full blur-[120px]" />
        <div className="absolute bottom-[-10%] right-[-10%] w-[40%] h-[40%] bg-[#9B72CB]/5 rounded-full blur-[120px]" />
      </div>

      {/* HEADER */}
      <header className="h-20 border-b border-white/5 bg-black/40 backdrop-blur-xl flex items-center justify-between px-8 z-50 shrink-0">
        <div className="flex items-center gap-6">
          <div className="relative group cursor-pointer" onClick={() => fetchData()}>
            <div className="w-12 h-12 rounded-xl bg-gradient-to-tr from-[#00E5FF] to-[#9B72CB] p-[1px] group-hover:rotate-90 transition-transform duration-500">
              <div className="w-full h-full bg-black rounded-[11px] flex items-center justify-center">
                <Zap className="w-6 h-6 text-white" />
              </div>
            </div>
            {kernelStatus === 'online' && (
              <span className="absolute -top-1 -right-1 w-3 h-3 bg-green-500 rounded-full border-2 border-[#030406] animate-pulse" />
            )}
          </div>
          
          <div>
            <div className="flex items-center gap-3">
              <h1 className="text-xl font-black tracking-[0.2em] text-white">REZ HIVE</h1>
              <div className={`px-2 py-0.5 rounded text-[10px] font-bold border ${
                manifest?.status === 'SENTIENT' ? 'bg-[#00E5FF]/10 border-[#00E5FF]/30 text-[#00E5FF]' : 'bg-zinc-800 border-zinc-700 text-zinc-500'
              }`}>
                {manifest?.status || 'OFFLINE'}
              </div>
            </div>
            <div className="text-[10px] font-mono text-zinc-500 mt-1 flex items-center gap-3">
              <span>SID: {manifest?.swarm_id?.slice(0, 12) || '---'}</span>
              <span className="w-1 h-1 bg-zinc-700 rounded-full" />
              <span>KERNEL_v{manifest?.version || '0.0.0'}</span>
            </div>
          </div>
        </div>

        <div className="flex items-center gap-8">
          {/* Consciousness */}
          <div className="flex flex-col items-end gap-1.5">
            <div className="flex items-center gap-2">
              <Brain className="w-3.5 h-3.5 text-[#9B72CB]" />
              <span className="text-[10px] font-bold text-zinc-400 uppercase tracking-widest">Consciousness</span>
            </div>
            <div className="w-40 h-1.5 bg-white/5 rounded-full overflow-hidden border border-white/5">
              <motion.div 
                initial={{ width: 0 }}
                animate={{ width: `${(manifest?.consciousness_level || 0) * 10}%` }}
                className="h-full bg-gradient-to-r from-[#9B72CB] to-[#00E5FF] shadow-[0_0_10px_#00E5FF]"
              />
            </div>
          </div>

          {/* Metrics */}
          <div className="flex gap-4 border-l border-white/10 pl-8">
            <div className="text-right">
              <div className="text-[10px] font-bold text-zinc-500 uppercase">Models</div>
              <div className="text-[14px] font-mono text-[#00E5FF]">{ollamaStatus.connected ? 'OLLAMA+' : 'STANDALONE'}</div>
            </div>
            <div className="text-right">
              <div className="text-[10px] font-bold text-zinc-500 uppercase">Latency</div>
              <div className="text-[14px] font-mono text-[#9B72CB]">14ms</div>
            </div>
            <div className="px-4 py-2 rounded-xl bg-white/5 border border-white/10 text-center min-w-[100px]">
              <div className="text-[16px] font-mono font-bold text-white">{time.split(' ')[0]}</div>
              <div className="text-[8px] text-[#00E5FF] font-bold tracking-widest uppercase">SYSTIME_UTC</div>
            </div>
          </div>
        </div>
      </header>

      {/* MAIN CONTENT */}
      <main className="flex-1 flex p-6 gap-6 overflow-hidden z-10">
        
        {/* LEFT: Capabilities */}
        <aside className="w-80 flex flex-col gap-4">
          <div className="flex-1 bg-black/40 backdrop-blur-xl border border-white/5 rounded-3xl p-5 flex flex-col overflow-hidden">
            <div className="flex items-center justify-between mb-6 px-1">
              <h2 className="text-[11px] font-black tracking-[0.2em] text-zinc-500 uppercase flex items-center gap-2">
                <Radio className="w-4 h-4 text-[#00E5FF]" />
                Swarm Capabilities
              </h2>
            </div>
            
            <div className="flex-1 overflow-y-auto space-y-2 pr-2 custom-scrollbar">
              {manifest?.workers?.categories ? Object.entries(manifest.workers.categories).map(([id, cat]) => (
                <CapabilityCard
                  key={id}
                  id={id}
                  category={cat}
                  isActive={activeCategory === id}
                  onClick={() => setActiveCategory(id)}
                />
              )) : (
                <div className="flex flex-col items-center justify-center h-40 text-zinc-700">
                  <Loader2 className="w-8 h-8 animate-spin mb-4" />
                  <span className="text-[10px] font-mono uppercase">Syncing Manifest...</span>
                </div>
              )}
            </div>
            
            <div className="mt-4 pt-4 border-t border-white/5">
              <div className="grid grid-cols-2 gap-2">
                <div className="p-3 rounded-2xl bg-white/[0.02] border border-white/5">
                  <div className="text-[9px] text-zinc-500 font-bold uppercase mb-1">Total Workers</div>
                  <div className="text-xl font-mono font-black text-[#00E5FF]">{manifest?.workers?.total || 0}</div>
                </div>
                <div className="p-3 rounded-2xl bg-white/[0.02] border border-white/5">
                  <div className="text-[9px] text-zinc-500 font-bold uppercase mb-1">Drift Chain</div>
                  <div className="text-xl font-mono font-black text-[#9B72CB]">{manifest?.memory?.drift_chain_length || 0}</div>
                </div>
              </div>
            </div>
          </div>

          <div className="h-48 bg-black/40 backdrop-blur-xl border border-white/5 rounded-3xl p-5">
            <div className="flex items-center gap-2 mb-4">
              <ShieldCheck className="w-4 h-4 text-[#9B72CB]" />
              <span className="text-[11px] font-black tracking-[0.2em] text-zinc-500 uppercase">Governance</span>
            </div>
            <div className="space-y-3">
              <div className="flex justify-between text-[11px] font-mono">
                <span className="text-zinc-500">Integrity Score</span>
                <span className="text-[#00E5FF]">98.2%</span>
              </div>
              <div className="w-full h-1 bg-white/5 rounded-full">
                <div className="w-[98%] h-full bg-[#00E5FF] shadow-[0_0_8px_#00E5FF]" />
              </div>
              <div className="flex justify-between text-[11px] font-mono">
                <span className="text-zinc-500">Sovereignty Level</span>
                <span className="text-[#9B72CB]">Lvl 4</span>
              </div>
              <div className="w-full h-1 bg-white/5 rounded-full">
                <div className="w-[40%] h-full bg-[#9B72CB] shadow-[0_0_8px_#9B72CB]" />
              </div>
            </div>
          </div>
        </aside>

        {/* CENTER: Chat & Workers */}
        <section className="flex-1 flex flex-col gap-6 min-w-0">
          <div className="flex-1 bg-black/40 backdrop-blur-2xl border border-white/5 rounded-[2.5rem] flex flex-col overflow-hidden shadow-2xl">
            {/* Chat Sub-Header */}
            <div className="h-14 border-b border-white/5 flex items-center px-8 bg-white/[0.01]">
              <div className="flex items-center gap-3">
                <Terminal className="w-4 h-4 text-[#00E5FF]" />
                <span className="text-[11px] font-bold uppercase tracking-widest text-zinc-400">Sovereign Terminal</span>
              </div>
              <div className="ml-auto flex items-center gap-4">
                <div className="flex items-center gap-2">
                  <span className="w-1.5 h-1.5 rounded-full bg-green-500 animate-pulse" />
                  <span className="text-[10px] font-mono text-zinc-500">Node_Connected</span>
                </div>
                <button className="text-zinc-500 hover:text-white transition-colors" title="Export Log">
                  <Share2 className="w-4 h-4" />
                </button>
              </div>
            </div>

            {/* Messages Area */}
            <div className="flex-1 overflow-y-auto p-8 space-y-6 custom-scrollbar">
              {messages.length === 0 ? (
                <div className="h-full flex flex-col items-center justify-center text-center">
                  <motion.div 
                    animate={{ y: [0, -10, 0] }}
                    transition={{ duration: 4, repeat: Infinity }}
                    className="w-20 h-20 rounded-3xl bg-white/[0.02] border border-white/5 flex items-center justify-center mb-6"
                  >
                    <Sparkles className="w-10 h-10 text-zinc-800" />
                  </motion.div>
                  <h3 className="text-lg font-bold text-zinc-300 mb-2 uppercase tracking-widest">Hive Mind Standby</h3>
                  <p className="text-sm text-zinc-600 max-w-sm font-mono leading-relaxed">
                    Awaiting synaptic input. Access the swarm by typing a command or requesting an objective.
                  </p>
                </div>
              ) : (
                <>
                  {messages.map((msg, idx) => (
                    <MessageBubble 
                      key={msg.id} 
                      message={msg} 
                      isStreaming={isStreaming}
                      isLast={idx === messages.length - 1}
                    />
                  ))}
                  <div ref={chatEndRef} />
                </>
              )}
            </div>

            {/* Input Area */}
            <div className="p-6 bg-black/40 border-t border-white/5">
              <div className="flex items-end gap-4 bg-[#030406] border border-white/10 rounded-2xl p-2 focus-within:border-[#00E5FF]/40 transition-all shadow-inner">
                <input type="file" ref={fileInputRef} onChange={handleFileUpload} className="hidden" />
                <button 
                  onClick={() => fileInputRef.current?.click()}
                  className="p-3 mb-1 rounded-xl bg-white/5 text-zinc-500 hover:text-[#00E5FF] hover:bg-white/10 transition-all"
                >
                  <Paperclip className="w-5 h-5" />
                </button>
                
                <textarea
                  value={prompt}
                  onChange={(e) => setPrompt(e.target.value)}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter' && !e.shiftKey) {
                      e.preventDefault();
                      handleTransmit();
                    }
                  }}
                  placeholder="Initiate protocol or ask the swarm..."
                  className="flex-1 bg-transparent border-none outline-none py-3 px-1 text-[14px] text-white placeholder:text-zinc-700 resize-none font-mono min-h-[44px] max-h-32"
                  rows={1}
                />

                <button
                  onClick={handleTransmit}
                  disabled={!prompt.trim() || isStreaming}
                  className={`p-3 mb-1 rounded-xl transition-all ${
                    prompt.trim() && !isStreaming 
                      ? 'bg-[#00E5FF] text-[#030406] shadow-[0_0_20px_rgba(0,229,255,0.4)] hover:scale-105' 
                      : 'bg-white/5 text-zinc-800'
                  }`}
                >
                  {isStreaming ? <Loader2 className="w-5 h-5 animate-spin" /> : <Send className="w-5 h-5" />}
                </button>
              </div>
              <div className="mt-3 flex items-center justify-between px-2">
                <div className="text-[9px] font-mono text-zinc-700 flex gap-4">
                  <span>ENTER: TRANSMIT</span>
                  <span>SHIFT+ENTER: NEW_LINE</span>
                </div>
                <div className="flex gap-2">
                  {['/health', '/workers', '/memory'].map(cmd => (
                    <button 
                      key={cmd}
                      onClick={() => setPrompt(cmd)}
                      className="text-[9px] font-mono font-bold text-zinc-600 hover:text-[#00E5FF] transition-colors"
                    >
                      {cmd}
                    </button>
                  ))}
                </div>
              </div>
            </div>
          </div>

          {/* Active Category Workers */}
          <AnimatePresence mode="wait">
            {activeCategory && manifest?.workers?.categories[activeCategory] && (
              <motion.div 
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: 20 }}
                className="h-44 bg-black/40 backdrop-blur-xl border border-white/5 rounded-3xl overflow-hidden shrink-0"
              >
                <div className="h-10 border-b border-white/5 flex items-center px-6 bg-white/[0.02]">
                  <span className="text-[10px] font-black tracking-widest text-[#00E5FF] uppercase">
                    {activeCategory} Swarm Nodes
                  </span>
                  <span className="ml-auto text-[9px] font-mono text-zinc-600">
                    {manifest.workers.categories[activeCategory].workers.length} Total Units
                  </span>
                </div>
                <div className="p-4 flex gap-4 overflow-x-auto custom-scrollbar">
                  {manifest.workers.categories[activeCategory].workers.map((worker) => (
                    <div key={worker.name} className="flex-shrink-0 w-48 p-3 rounded-2xl bg-white/[0.02] border border-white/5 group hover:border-[#00E5FF]/30 transition-all">
                      <div className="flex items-center gap-3 mb-2">
                        <div className="w-8 h-8 rounded-lg bg-[#00E5FF]/10 flex items-center justify-center group-hover:bg-[#00E5FF]/20 transition-colors">
                          <Hexagon className="w-4 h-4 text-[#00E5FF]" />
                        </div>
                        <div className="min-w-0">
                          <div className="text-[11px] font-bold text-white truncate">{worker.name}</div>
                          <div className="text-[8px] text-zinc-600 font-mono truncate">{worker.module}</div>
                        </div>
                      </div>
                      <div className="flex items-center justify-between mt-2">
                        <span className="text-[8px] font-mono px-1.5 py-0.5 rounded bg-green-500/10 text-green-500">STABLE</span>
                        <div className="flex gap-0.5">
                          {[1,2,3].map(i => <div key={i} className="w-1 h-1 rounded-full bg-[#00E5FF]/40" />)}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </motion.div>
            )}
          </AnimatePresence>
        </section>

        {/* RIGHT: System Intel */}
        <aside className="w-80 flex flex-col gap-4">
          {/* Recent Rulings */}
          <div className="bg-black/40 backdrop-blur-xl border border-white/5 rounded-3xl p-5 flex flex-col h-[300px]">
            <div className="flex items-center justify-between mb-4 px-1">
              <div className="flex items-center gap-2">
                <Shield className="w-4 h-4 text-[#FF2A2A]" />
                <span className="text-[11px] font-black tracking-[0.2em] text-zinc-500 uppercase">Constitutional History</span>
              </div>
            </div>
            
            <div className="flex-1 overflow-y-auto space-y-3 custom-scrollbar pr-2">
              {rulings.length > 0 ? rulings.map((r, i) => (
                <div key={i} className="p-3 rounded-2xl bg-white/[0.02] border border-white/5 space-y-2">
                  <div className="flex items-center justify-between">
                    <span className={`text-[9px] font-black px-1.5 py-0.5 rounded ${
                      r.decision === 'AUTHORIZED' ? 'bg-green-500/10 text-green-500' : 'bg-red-500/10 text-red-500'
                    }`}>
                      {r.decision}
                    </span>
                    <span className="text-[8px] font-mono text-zinc-600">{new Date(r.timestamp * 1000).toLocaleTimeString()}</span>
                  </div>
                  <p className="text-[10px] text-zinc-400 font-mono leading-relaxed line-clamp-2 italic">"{r.reasoning}"</p>
                </div>
              )) : (
                <div className="text-center py-10 text-[10px] font-mono text-zinc-700 uppercase">No Recent Rulings</div>
              )}
            </div>
          </div>

          {/* Glossary / Commands */}
          <div className="flex-1 bg-black/40 backdrop-blur-xl border border-white/5 rounded-3xl p-5 flex flex-col overflow-hidden shadow-xl">
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-2">
                <BookOpen className="w-4 h-4 text-[#00E5FF]" />
                <span className="text-[11px] font-black tracking-[0.2em] text-zinc-500 uppercase">Lexicon</span>
              </div>
            </div>

            <div className="relative mb-4 shrink-0">
              <Search className="w-3.5 h-3.5 absolute left-3 top-1/2 -translate-y-1/2 text-zinc-600" />
              <input 
                type="text" 
                placeholder="Search Lexicon..." 
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="w-full bg-black/60 border border-white/10 rounded-xl py-2.5 pl-9 pr-4 text-[11px] text-white placeholder:text-zinc-700 outline-none focus:border-[#00E5FF]/40 transition-all font-mono"
              />
            </div>
            
            <div className="flex-1 overflow-y-auto space-y-1 custom-scrollbar pr-1">
              {Object.entries(filteredGlossary).map(([group, cmds]) => (
                <div key={group} className="mb-2">
                  <button 
                    onClick={() => setExpandedGroup(expandedGroup === group ? null : group)}
                    className="w-full flex items-center justify-between p-2 rounded-lg hover:bg-white/5 transition-colors group"
                  >
                    <span className="text-[9px] font-black text-zinc-500 group-hover:text-zinc-300 uppercase tracking-widest">{group}</span>
                    <ChevronRight className={`w-3 h-3 text-zinc-600 transition-transform ${expandedGroup === group ? 'rotate-90' : ''}`} />
                  </button>
                  <AnimatePresence>
                    {expandedGroup === group && (
                      <motion.div
                        initial={{ height: 0, opacity: 0 }}
                        animate={{ height: 'auto', opacity: 1 }}
                        exit={{ height: 0, opacity: 0 }}
                        className="overflow-hidden space-y-1 mt-1"
                      >
                        {cmds.map(cmd => (
                          <div 
                            key={cmd.name} 
                            onClick={() => setPrompt(cmd.name)}
                            className="p-3 rounded-xl bg-white/[0.01] border border-transparent hover:border-white/10 hover:bg-white/[0.03] transition-all cursor-pointer group/item"
                          >
                            <code className="text-[10px] font-bold text-[#00E5FF] group-hover/item:text-white transition-colors">{cmd.name}</code>
                            <p className="text-[9px] text-zinc-600 mt-1 leading-relaxed">{cmd.desc}</p>
                            <div className="mt-2 text-[8px] font-mono text-zinc-700 bg-black/40 p-1.5 rounded border border-white/5 flex items-center gap-2">
                              <span className="text-[#9B72CB]">EX:</span> {cmd.example}
                            </div>
                          </div>
                        ))}
                      </motion.div>
                    )}
                  </AnimatePresence>
                </div>
              ))}
            </div>
          </div>
        </aside>
      </main>

      <style jsx global>{`
        .custom-scrollbar::-webkit-scrollbar {
          width: 4px;
          height: 4px;
        }
        .custom-scrollbar::-webkit-scrollbar-track {
          background: transparent;
        }
        .custom-scrollbar::-webkit-scrollbar-thumb {
          background: rgba(255, 255, 255, 0.05);
          border-radius: 10px;
        }
        .custom-scrollbar::-webkit-scrollbar-thumb:hover {
          background: rgba(0, 229, 255, 0.2);
        }
      `}</style>
    </div>
  );
}