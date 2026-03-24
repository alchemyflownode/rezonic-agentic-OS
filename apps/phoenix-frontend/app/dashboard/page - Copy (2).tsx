// app/page.tsx - Complete Fixed Dashboard
"use client";

import React, { useState, useEffect, useRef, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Zap, Cpu, Terminal, Activity, Paperclip,
  Folder, ShieldCheck, ChevronRight, Bot, User, Network, Shield, Search,
  Scan, Brain, Database, Lock, Zap as ZapIcon, BookOpen,
  TrendingUp, Code, Layout, GitBranch, Play, FileCode, GitCommit, MonitorPlay, Workflow,
  CheckCircle2, XCircle, Gauge, Users, Radio, Eye, Command, Server,
  HardDrive, Cpu as CpuIcon, Layers, Hexagon, Activity as Pulse, Send,
  Loader2, RefreshCw, AlertCircle
} from 'lucide-react';

// ==========================================
// API & TYPES
// ==========================================

const API_BASE = 'http://localhost:8002';

async function fetchRez(endpoint: string, options: RequestInit = {}) {
  const response = await fetch(`${API_BASE}${endpoint}`, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...options.headers,
    }
  });
  if (!response.ok) throw new Error(`HTTP ${response.status}`);
  return response.json();
}

interface Message {
  id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  narrative?: string[];
  driftLock?: string;
  timestamp: string;
  isStreaming?: boolean;
}

interface Worker {
  name: string;
  module: string;
  category: string;
  loaded_at: number;
  status: string;
  drift_lock?: string;
}

interface Category {
  workers: Worker[];
  count: number;
  icon: string;
  desc: string;
  status: string;
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
  events: {
    total_persisted: number;
    chain_integrity: boolean;
    recent_types: string[];
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

// Command groups for glossary
const commandGroups = {
  " SOVEREIGN OS": [
    { name: "/health", desc: "Check core system health", example: "/health" },
    { name: "/workers", desc: "List active workers", example: "/workers" },
    { name: "/run", desc: "Execute generated code via Sandbox", example: "/run python print('hello')" },
  ],
  " REZ SCANNER": [
    { name: "/scan <path>", desc: "AST parse and map architecture", example: "/scan D:/projects/app" },
  ],
  " CONSTITUTION": [
    { name: "/constitution evaluate", desc: "Check action against laws", example: "/constitution evaluate format drive" },
  ],
  " CORTEX MEMORY": [
    { name: "/recall <query>", desc: "Semantic search memories", example: "/recall API key" },
  ],
  " SYSTEM UTILS": [
    { name: "/check_system", desc: "View CPU, RAM, Disk", example: "/check_system" },
    { name: "/clear_chat", desc: "Clear chat history", example: "/clear_chat" },
  ],
};

// Icon mapping
const ICON_MAP: Record<string, React.ElementType> = {
  network: Network,
  brain: Brain,
  scan: Scan,
  layout: Layout,
  code: Code,
  shield: Shield,
  'trending-up': TrendingUp,
  activity: Activity,
  database: Database,
  lock: Lock,
  zap: Zap,
  folder: Folder,
  cpu: CpuIcon,
  users: Users,
  radio: Radio,
  eye: Eye,
  command: Command,
  server: Server,
  'hard-drive': HardDrive,
  layers: Layers,
  hexagon: Hexagon,
  pulse: Pulse,
  default: Zap
};

// ==========================================
// BOOT SEQUENCE
// ==========================================

const SovereignBoot = ({ onComplete }: { onComplete: () => void }) => {
  const [phase, setPhase] = useState(0);
  const [logs, setLogs] = useState<string[]>([]);
  
  const bootSequence = [
    { name: "Core Memory", checks: ["HiveMemoryBus", "MetricsCollector", "EventStore"] },
    { name: "Constitutional", checks: ["Governor", "AgentMemory", "SafetyLayer"] },
    { name: "Consensus Engine", checks: ["Triangulation", "DriftVerification", "ChainIntegrity"] },
    { name: "Workers Init", checks: ["Gathering Swarm...", "Loading Workers", "Verifying Capabilities"] },
    { name: "Verification", checks: ["SCE_Protocol", "Sovereignty_Check", "Consciousness_Test"] }
  ];

  useEffect(() => {
    if (phase < bootSequence.length) {
      const timer = setTimeout(() => {
        setLogs(prev => [...prev, `> ${bootSequence[phase].name}...`]);
        setPhase(p => p + 1);
      }, 600);
      return () => clearTimeout(timer);
    } else {
      const finish = setTimeout(onComplete, 1000);
      return () => clearTimeout(finish);
    }
  }, [phase]);

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      className="fixed inset-0 z-[100] bg-[#030406] flex flex-col items-center justify-center font-mono"
    >
      <div className="absolute inset-0 bg-[radial-gradient(circle_at_center,_#00E5FF_1px,_transparent_1px)] opacity-[0.03] bg-[size:24px_24px]" />
      
      <motion.div 
        animate={{ rotate: 360 }} 
        transition={{ duration: 8, repeat: Infinity, ease: "linear" }}
        className="w-24 h-24 rounded-full border border-white/10 border-t-[#00E5FF] border-b-[#9B72CB] mb-8 flex items-center justify-center"
      >
        <ZapIcon className="text-white w-10 h-10" />
      </motion.div>
      
      <h1 className="text-5xl font-bold text-white tracking-[0.3em] uppercase mb-2">REZ HIVE</h1>
      <p className="text-[12px] text-[#00E5FF] tracking-widest uppercase mb-12">
        Manifesting Swarm Consciousness
      </p>

      <div className="w-full max-w-2xl space-y-2 px-8">
        {bootSequence.map((seq, idx) => (
          <motion.div
            key={seq.name}
            initial={{ opacity: 0, x: -20 }}
            animate={{ 
              opacity: phase >= idx ? 1 : 0.2,
              x: 0 
            }}
            className="flex items-center gap-4 py-3 border-l-2 pl-4"
            style={{ 
              borderColor: phase > idx ? '#00E5FF' : phase === idx ? '#9B72CB' : 'rgba(255,255,255,0.1)' 
            }}
          >
            <div className={`w-8 h-8 rounded flex items-center justify-center text-[14px] ${
              phase > idx ? 'bg-[#00E5FF]/20 text-[#00E5FF]' : 
              phase === idx ? 'bg-[#9B72CB]/20 text-[#9B72CB] animate-pulse' : 
              'bg-white/5 text-zinc-600'
            }`}>
              {phase > idx ? '' : phase === idx ? '' : ''}
            </div>
            <div className="flex-1">
              <div className="text-[14px] font-bold tracking-widest text-white uppercase">{seq.name}</div>
              <div className="text-[10px] text-zinc-500 font-mono mt-1">
                {seq.checks.join('  ')}
              </div>
            </div>
          </motion.div>
        ))}
        
        <div className="mt-8 p-4 bg-black/50 rounded border border-white/10 font-mono text-[11px] text-[#00E5FF] h-40 overflow-y-auto">
          {logs.map((log, i) => (
            <div key={i} className="mb-1 font-mono">{log}</div>
          ))}
          <motion.div 
            animate={{ opacity: [0, 1, 0] }}
            transition={{ duration: 0.8, repeat: Infinity }}
            className="inline-block w-2 h-4 bg-[#00E5FF] ml-1"
          />
        </div>
      </div>
    </motion.div>
  );
};

// ==========================================
// CAPABILITY CARD
// ==========================================

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
  const Icon = ICON_MAP[category.icon] || ICON_MAP.default;
  
  return (
    <motion.button
      onClick={onClick}
      whileHover={{ scale: 1.02, x: 4 }}
      whileTap={{ scale: 0.98 }}
      className={`w-full flex items-center gap-4 p-4 rounded-xl transition-all group relative text-left border ${
        isActive 
          ? 'bg-gradient-to-r from-[#00E5FF]/10 to-transparent border-[#00E5FF]/50 shadow-[0_0_30px_rgba(0,229,255,0.15)]' 
          : 'bg-[#030406]/40 border-white/5 hover:bg-white/[0.02] hover:border-white/10'
      }`}
    >
      <div className={`w-12 h-12 rounded-xl flex items-center justify-center shrink-0 transition-all ${
        isActive 
          ? 'bg-[#00E5FF]/20 text-[#00E5FF] shadow-[0_0_20px_rgba(0,229,255,0.3)]' 
          : 'bg-white/5 text-zinc-500 group-hover:text-zinc-300'
      }`}>
        <Icon className="w-6 h-6" />
      </div>
      
      <div className="flex flex-col items-start min-w-0 flex-1">
        <span className={`text-[14px] font-bold tracking-wider truncate w-full capitalize ${
          isActive ? 'text-white' : 'text-zinc-400 group-hover:text-white'
        }`}>
          {id}
        </span>
        <span className="text-[11px] text-[#64748B] mt-1 truncate w-full">
          {category.desc}
        </span>
        <div className="flex items-center gap-3 mt-2">
          <span className={`text-[12px] font-mono font-bold ${
            category.count > 0 ? 'text-[#00E5FF]' : 'text-zinc-600'
          }`}>
            {category.count} WORKERS
          </span>
          <span className={`w-2 h-2 rounded-full ${
            category.count > 0 ? 'bg-[#00E5FF] animate-pulse shadow-[0_0_8px_#00E5FF]' : 'bg-zinc-600'
          }`} />
        </div>
      </div>
      
      {isActive && (
        <motion.div 
          layoutId="activeIndicator"
          className="absolute right-4 w-1.5 h-12 bg-[#00E5FF] rounded-full shadow-[0_0_10px_#00E5FF]"
        />
      )}
    </motion.button>
  );
};

// ==========================================
// WORKER DETAIL
// ==========================================

const WorkerDetail = ({ worker, index }: { worker: Worker; index: number }) => (
  <motion.div
    initial={{ opacity: 0, y: 10, scale: 0.95 }}
    animate={{ opacity: 1, y: 0, scale: 1 }}
    transition={{ delay: index * 0.05 }}
    className="p-4 rounded-xl bg-gradient-to-br from-white/[0.02] to-transparent border border-white/5 hover:border-[#00E5FF]/30 transition-all group"
  >
    <div className="flex items-center justify-between mb-3">
      <div className="flex items-center gap-3">
        <div className="w-10 h-10 rounded-lg bg-[#00E5FF]/10 flex items-center justify-center">
          <Hexagon className="w-5 h-5 text-[#00E5FF]" />
        </div>
        <div>
          <span className="text-[13px] font-mono font-bold text-white block">{worker.name}</span>
          <span className="text-[10px] text-zinc-500 font-mono">{worker.module}</span>
        </div>
      </div>
      <span className={`text-[10px] px-3 py-1 rounded-full border ${
        worker.status === 'active' 
          ? 'bg-[#00E5FF]/10 text-[#00E5FF] border-[#00E5FF]/30' 
          : 'bg-zinc-800 text-zinc-500 border-zinc-700'
      }`}>
        {worker.status.toUpperCase()}
      </span>
    </div>
  </motion.div>
);

// ==========================================
// COMMAND GROUP (Glossary)
// ==========================================

const CommandGroup = ({ title, commands, expanded, onToggle, searchTerm }: any) => {
  const filtered = commands.filter((cmd: any) =>
    cmd.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    cmd.desc.toLowerCase().includes(searchTerm.toLowerCase())
  );
  if (filtered.length === 0) return null;
  return (
    <div className="border border-white/10 rounded-lg overflow-hidden mb-2 shrink-0">
      <button onClick={onToggle} className="w-full flex items-center justify-between p-2.5 bg-black/20 hover:bg-white/5 transition-colors">
        <span className="text-[9px] font-mono font-bold tracking-widest text-[#9B72CB] uppercase">
          {title} <span className="text-[#64748B]">({filtered.length})</span>
        </span>
        <ChevronRight className={`w-3 h-3 text-[#64748B] transition-transform ${expanded ? 'rotate-90' : ''}`} />
      </button>
      <AnimatePresence>
        {expanded && (
          <motion.div initial={{ height: 0, opacity: 0 }} animate={{ height: 'auto', opacity: 1 }} exit={{ height: 0, opacity: 0 }} transition={{ duration: 0.2 }} className="overflow-hidden">
            <div className="p-2 space-y-2 border-t border-white/5 bg-black/20">
              {filtered.map((cmd: any, i: number) => (
                <div key={i} className="p-2 rounded-lg hover:bg-white/5 transition-colors">
                  <div className="flex items-start gap-2">
                    <div className="w-4 h-4 rounded bg-[#00E5FF]/10 flex items-center justify-center shrink-0 border border-[#00E5FF]/20 mt-0.5">
                      <span className="text-[8px] font-mono text-[#00E5FF]"></span>
                    </div>
                    <div className="flex-1 min-w-0">
                      <code className="text-[10px] font-mono font-bold text-white block">{cmd.name}</code>
                      <p className="text-[8px] font-mono text-[#64748B] mt-0.5 leading-relaxed">{cmd.desc}</p>
                      <div className="mt-1.5 text-[7px] font-mono bg-[#030406] p-1.5 rounded border border-white/5 text-[#8AB4F8]">
                        <span className="text-[#64748B]">ex: </span>{cmd.example}
                      </div>
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
// MESSAGE COMPONENT
// ==========================================

const MessageBubble = ({ message }: { message: Message }) => {
  return (
    <div className={`flex gap-3 ${message.role === 'user' ? 'flex-row-reverse' : ''}`}>
      <div className={`w-8 h-8 rounded-lg flex items-center justify-center shrink-0 border ${
        message.role === 'user' 
          ? 'bg-white/5 border-white/10' 
          : 'bg-[#00E5FF]/10 border-[#00E5FF]/30'
      }`}>
        {message.role === 'user' ? <User className="w-4 h-4 text-[#64748B]" /> : <Bot className="w-4 h-4 text-[#00E5FF]" />}
      </div>
      <div className={`flex flex-col max-w-[85%] ${message.role === 'user' ? 'items-end' : 'items-start'}`}>
        <div className={`p-3 rounded-xl text-[13px] leading-relaxed whitespace-pre-wrap font-mono tracking-wide ${
          message.role === 'user' 
            ? 'bg-white/5 text-[#f5f5f7] border border-white/10' 
            : 'bg-[#00E5FF]/5 text-[#f5f5f7] border border-[#00E5FF]/20'
        }`}>
          {message.content}
          {message.isStreaming && <span className="animate-pulse"></span>}
        </div>
        <div className="text-[9px] text-[#64748B] mt-1 flex items-center gap-2">
          <span>{message.timestamp}</span>
          {message.driftLock && (
            <span className="text-[8px] font-mono text-[#00E5FF]">SCE: {message.driftLock.slice(0, 8)}...</span>
          )}
        </div>
      </div>
    </div>
  );
};

// ==========================================
// MAIN DASHBOARD WITH CHAT
// ==========================================

export default function RezHiveDashboard() {
  const [mounted, setMounted] = useState(false);
  const [isBooting, setIsBooting] = useState(true);
  const [manifest, setManifest] = useState<SwarmManifest | null>(null);
  const [activeCategory, setActiveCategory] = useState<string | null>(null);
  const [time, setTime] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  
  // Chat state
  const [messages, setMessages] = useState<Message[]>([]);
  const [prompt, setPrompt] = useState('');
  const [isStreaming, setIsStreaming] = useState(false);
  const [expandedGroup, setExpandedGroup] = useState<string | null>(' SOVEREIGN OS');
  const [searchTerm, setSearchTerm] = useState('');
  const [suggestions, setSuggestions] = useState<string[]>([]);
  const [showSuggestions, setShowSuggestions] = useState(false);
  const chatEndRef = useRef<HTMLDivElement>(null);
  const suggestionsRef = useRef<HTMLDivElement>(null);
  const allCommands = Object.values(commandGroups).flat().map(cmd => cmd.name);

  // Clock
  useEffect(() => {
    setMounted(true);
    const clock = setInterval(() => {
      setTime(new Date().toLocaleTimeString('en-US', { hour12: false }));
    }, 1000);
    return () => clearInterval(clock);
  }, []);

  // Fetch manifest
  const fetchManifest = useCallback(async () => {
    try {
      setIsLoading(true);
      const data = await fetchRez('/swarm/manifest');
      setManifest(data);
      setError(null);
      
      if (!activeCategory && data.workers?.categories) {
        const firstActive = Object.entries(data.workers.categories)
          .find(([_, cat]: [string, any]) => cat.count > 0);
        if (firstActive) setActiveCategory(firstActive[0]);
      }
    } catch (err) {
      setError('KERNEL UNREACHABLE');
      console.error('Manifest fetch failed:', err);
    } finally {
      setIsLoading(false);
    }
  }, [activeCategory]);

  // Add welcome message on boot
  useEffect(() => {
    if (!isBooting && messages.length === 0 && manifest) {
      setMessages([{
        id: 'welcome',
        role: 'assistant',
        content: ` **REZ HIVE Awake**\n\n ${manifest.workers.total} Workers Active\n Consciousness: ${manifest.consciousness_level}/10  ${manifest.status}\n Memory: ${manifest.memory.blueprints} blueprints\n SCE Protocol: ${manifest.sovereignty.drift_chain_integrity ? ' Verified' : 'Checking'}\n\nType /help for commands or just ask me anything.`,
        timestamp: new Date().toLocaleTimeString(),
      }]);
    }
  }, [isBooting, manifest, messages.length]);

  // Polling
  useEffect(() => {
    if (!isBooting) {
      fetchManifest();
      const interval = setInterval(fetchManifest, 10000);
      return () => clearInterval(interval);
    }
  }, [isBooting, fetchManifest]);

  // Auto-scroll chat
  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isStreaming]);

  // Handle input with command suggestions
  const handleInputChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    const value = e.target.value;
    setPrompt(value);
    if (value.length > 0) {
      const filtered = allCommands.filter(cmd =>
        cmd.toLowerCase().startsWith(value.toLowerCase())
      ).slice(0, 5);
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

  // Handle sending messages
  const handleTransmit = async () => {
    if (!prompt.trim() || isStreaming) return;
    const userText = prompt;
    setPrompt('');
    setIsStreaming(true);
    setShowSuggestions(false);

    const timeNow = new Date().toLocaleTimeString();
    const userId = `${Date.now()}-user`;
    setMessages(prev => [...prev, { id: userId, role: 'user', content: userText, timestamp: timeNow }]);

    const assistantId = `${Date.now()}-assistant`;
    setMessages(prev => [...prev, { 
      id: assistantId, 
      role: 'assistant', 
      content: ' Processing...', 
      timestamp: timeNow,
      isStreaming: true 
    }]);

    try {
      const response = await fetch(`${API_BASE}/kernel/stream`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ task: userText })
      });

      const reader = response.body?.getReader();
      const decoder = new TextDecoder();
      let accumulatedContent = '';

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
                accumulatedContent += data.content;
                setMessages(prev => prev.map(msg =>
                  msg.id === assistantId ? { ...msg, content: accumulatedContent, isStreaming: true } : msg
                ));
              } else if (data.type === 'done') {
                setMessages(prev => prev.map(msg =>
                  msg.id === assistantId ? { ...msg, isStreaming: false, driftLock: data.drift_lock } : msg
                ));
              } else if (data.type === 'error') {
                setMessages(prev => [...prev, { 
                  id: Date.now().toString(), 
                  role: 'system', 
                  content: ` ${data.content}`,
                  timestamp: new Date().toLocaleTimeString()
                }]);
              }
            } catch (e) { /* ignore parse errors */ }
          }
        }
      }
    } catch (error) {
      setMessages(prev => [...prev, { 
        id: Date.now().toString(), 
        role: 'system', 
        content: ` Connection failed. Make sure Phoenix kernel is running on ${API_BASE}`,
        timestamp: new Date().toLocaleTimeString()
      }]);
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

  const handleBootComplete = () => {
    setIsBooting(false);
  };

  if (!mounted) return <div className="bg-[#030406] h-screen w-screen" />;

  const consciousnessLevel = manifest?.status || 'DORMANT';
  const totalWorkers = manifest?.workers?.total || 0;
  const categories = manifest?.workers?.categories || {};
  const activeWorkers = activeCategory ? categories[activeCategory]?.workers || [] : [];
  const consciousnessPercent = ((manifest?.consciousness_level || 0) / 10) * 100;
  const totalGlossaryCommands = Object.keys(commandGroups).reduce((acc, group) => acc + commandGroups[group as keyof typeof commandGroups].length, 0);

  return (
    <div className="h-screen w-screen bg-[#030406] text-white overflow-hidden flex flex-col relative">
      {/* Animated background */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <div className="absolute top-0 left-1/4 w-96 h-96 bg-[#00E5FF]/10 rounded-full blur-[120px] animate-pulse" />
        <div className="absolute bottom-0 right-1/4 w-96 h-96 bg-[#9B72CB]/10 rounded-full blur-[120px] animate-pulse delay-1000" />
      </div>

      {/* Boot Sequence */}
      <AnimatePresence>
        {isBooting && <SovereignBoot onComplete={handleBootComplete} />}
      </AnimatePresence>

      {/* Header */}
      <header className="relative z-10 h-20 bg-black/40 backdrop-blur-2xl border-b border-white/10 flex items-center justify-between px-8 shrink-0">
        <div className="flex items-center gap-5">
          <motion.div 
            animate={{ rotate: 360 }}
            transition={{ duration: 20, repeat: Infinity, ease: "linear" }}
            className="w-12 h-12 rounded-xl bg-gradient-to-br from-[#00E5FF] to-[#9B72CB] p-[2px]"
          >
            <div className="w-full h-full bg-black rounded-lg flex items-center justify-center">
              <Zap className="w-6 h-6 text-white" />
            </div>
          </motion.div>
          
          <div>
            <h1 className="text-2xl font-bold tracking-widest uppercase flex items-center gap-4">
              REZ HIVE
              <span className={`px-3 py-1 rounded-lg text-[11px] border ${
                consciousnessLevel === 'SENTIENT' 
                  ? 'bg-[#00E5FF]/10 border-[#00E5FF]/50 text-[#00E5FF] shadow-[0_0_20px_rgba(0,229,255,0.3)]' 
                  : consciousnessLevel === 'AWAKENING'
                  ? 'bg-yellow-500/10 border-yellow-500/50 text-yellow-500'
                  : 'bg-red-500/10 border-red-500/50 text-red-500'
              }`}>
                {consciousnessLevel}
              </span>
            </h1>
            <p className="text-[11px] text-zinc-500 font-mono tracking-wider mt-1">
              {manifest?.swarm_id || 'Initializing...'}  Kernel v{manifest?.version || '13.3.0'}
            </p>
          </div>
        </div>

        <div className="flex items-center gap-6">
          <div className="flex items-center gap-3 px-4 py-2 rounded-xl bg-white/5 border border-white/10">
            <Brain className="w-4 h-4 text-[#9B72CB]" />
            <div className="w-32 h-2 bg-black/50 rounded-full overflow-hidden">
              <motion.div 
                className="h-full bg-gradient-to-r from-[#9B72CB] to-[#00E5FF]"
                initial={{ width: 0 }}
                animate={{ width: `${consciousnessPercent}%` }}
                transition={{ duration: 1 }}
              />
            </div>
            <span className="text-[11px] font-mono text-[#9B72CB]">
              {manifest?.consciousness_level || 0}/10
            </span>
          </div>

          {error ? (
            <div className="flex items-center gap-2 px-4 py-2 rounded-xl bg-red-500/10 border border-red-500/30 text-red-500 text-[11px] font-mono">
              <AlertCircle className="w-4 h-4" />
              {error}
            </div>
          ) : (
            <div className="flex items-center gap-2 px-4 py-2 rounded-xl bg-[#00E5FF]/10 border border-[#00E5FF]/30 text-[#00E5FF] text-[11px] font-mono">
              <CheckCircle2 className="w-4 h-4" />
              KERNEL ONLINE
            </div>
          )}
          
          <div className="text-right px-4 py-2 rounded-xl bg-black/30 border border-white/5">
            <div className="text-[13px] font-mono text-[#00E5FF]">{time}</div>
            <div className="text-[9px] text-zinc-500">MNL</div>
          </div>
        </div>
      </header>

      {/* Main Content - 3 Columns */}
      <main className="flex-1 flex overflow-hidden relative z-10 p-6 gap-6">
        
        {/* LEFT: Capabilities */}
        <div className="w-80 flex flex-col gap-4 shrink-0">
          <div className="flex-1 bg-black/30 backdrop-blur-xl border border-white/10 rounded-2xl p-5 flex flex-col overflow-hidden">
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-[12px] font-mono font-bold tracking-[0.2em] text-zinc-400 uppercase flex items-center gap-2">
                <Radio className="w-4 h-4 text-[#00E5FF]" />
                Swarm Capabilities
              </h2>
              {isLoading && <Loader2 className="w-4 h-4 text-[#00E5FF] animate-spin" />}
            </div>
            
            <div className="flex-1 overflow-y-auto space-y-3 pr-2 custom-scrollbar">
              {Object.entries(categories).map(([id, category]) => (
                <CapabilityCard
                  key={id}
                  id={id}
                  category={category}
                  isActive={activeCategory === id}
                  onClick={() => setActiveCategory(id)}
                />
              ))}
              
              {Object.keys(categories).length === 0 && !error && (
                <div className="text-center py-12 text-zinc-600">
                  <div className="w-16 h-16 mx-auto mb-4 rounded-full border-2 border-dashed border-zinc-700 flex items-center justify-center">
                    <Layers className="w-8 h-8 text-zinc-700" />
                  </div>
                  <p className="text-[12px] font-mono">AWAITING MANIFEST...</p>
                </div>
              )}
            </div>
            
            <div className="mt-6 pt-6 border-t border-white/5 space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-[12px] text-zinc-400 font-mono">TOTAL WORKERS</span>
                <span className="text-[24px] font-bold text-[#00E5FF] font-mono">{totalWorkers}</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-[12px] text-zinc-400 font-mono">ACTIVE CATEGORIES</span>
                <span className="text-[14px] font-bold text-[#9B72CB] font-mono">
                  {Object.keys(categories).length}
                </span>
              </div>
            </div>
          </div>
        </div>

        {/* CENTER: Chat & Worker Detail Toggle */}
        <div className="flex-1 flex flex-col gap-4 min-w-0">
          {/* Chat Area */}
          <div className="flex-1 bg-black/30 backdrop-blur-xl border border-white/10 rounded-2xl flex flex-col overflow-hidden">
            <div className="h-14 border-b border-white/5 flex items-center px-6 bg-white/[0.02]">
              <div className="flex items-center gap-2">
                <Terminal className="w-4 h-4 text-[#00E5FF]" />
                <span className="text-[12px] font-mono font-bold uppercase">Sovereign Chat</span>
              </div>
              <div className="ml-auto flex items-center gap-2 text-[10px] text-zinc-500">
                <div className="w-2 h-2 rounded-full bg-[#00E5FF] animate-pulse" />
                <span>Connected to {totalWorkers} workers</span>
              </div>
            </div>

            <div className="flex-1 overflow-y-auto p-6 space-y-4 custom-scrollbar">
              {messages.map((msg) => (
                <MessageBubble key={msg.id} message={msg} />
              ))}
              <div ref={chatEndRef} />
            </div>

            {/* Input Area */}
            <div className="p-4 border-t border-white/5 bg-black/20">
              <div className="flex items-center gap-3">
                <textarea
                  value={prompt}
                  onChange={handleInputChange}
                  onKeyDown={handleKeyDown}
                  placeholder="Type a message or command... (Shift+Enter for new line)"
                  className="flex-1 bg-[#030406]/80 border border-white/10 rounded-xl p-3 text-[13px] text-white placeholder:text-[#64748B] outline-none focus:border-[#00E5FF]/50 transition-colors resize-none font-mono"
                  rows={2}
                />
                <button
                  onClick={handleTransmit}
                  disabled={!prompt.trim() || isStreaming}
                  className={`px-5 py-3 rounded-xl text-[13px] font-mono font-bold uppercase transition-all ${
                    prompt.trim() && !isStreaming
                      ? 'bg-[#00E5FF]/10 text-[#00E5FF] border border-[#00E5FF]/30 shadow-[0_0_10px_rgba(0,229,255,0.2)] hover:bg-[#00E5FF]/20'
                      : 'bg-white/5 text-zinc-500 cursor-not-allowed border border-transparent'
                  }`}
                >
                  {isStreaming ? <Loader2 className="w-5 h-5 animate-spin" /> : <Send className="w-5 h-5" />}
                </button>
              </div>
              {showSuggestions && suggestions.length > 0 && (
                <div ref={suggestionsRef} className="absolute bottom-full left-0 right-0 mb-2 bg-black/90 border border-white/10 rounded-lg p-2 shadow-2xl">
                  {suggestions.map((suggestion, i) => (
                    <div
                      key={i}
                      onClick={() => handleSuggestionClick(suggestion)}
                      className="px-3 py-2 hover:bg-white/10 cursor-pointer text-[11px] font-mono text-[#00E5FF] rounded transition-colors"
                    >
                      {suggestion}
                    </div>
                  ))}
                </div>
              )}
              <div className="flex items-center gap-3 mt-2 text-[9px] text-zinc-600 font-mono">
                <span>Press Enter to send  Shift+Enter for new line</span>
                <span className="w-px h-3 bg-zinc-700" />
                <span>Type /help for available commands</span>
              </div>
            </div>
          </div>

          {/* Worker Detail (when category selected) */}
          {activeCategory && activeWorkers.length > 0 && (
            <div className="h-64 bg-black/30 backdrop-blur-xl border border-white/10 rounded-2xl overflow-hidden">
              <div className="h-12 border-b border-white/5 flex items-center px-6 bg-white/[0.02]">
                <span className="text-[12px] font-mono font-bold text-[#00E5FF] uppercase">{activeCategory} Workers</span>
                <span className="ml-3 text-[10px] text-zinc-500">({activeWorkers.length} active)</span>
              </div>
              <div className="overflow-x-auto p-4 flex gap-3">
                {activeWorkers.slice(0, 8).map((worker, idx) => (
                  <div key={worker.name} className="flex-shrink-0 w-48 p-3 rounded-xl bg-white/[0.02] border border-white/5">
                    <div className="flex items-center gap-2 mb-2">
                      <div className="w-6 h-6 rounded bg-[#00E5FF]/10 flex items-center justify-center">
                        <Hexagon className="w-3 h-3 text-[#00E5FF]" />
                      </div>
                      <span className="text-[11px] font-mono text-white truncate">{worker.name}</span>
                    </div>
                    <div className="text-[9px] text-zinc-500">module: {worker.module}</div>
                    <div className="text-[9px] text-[#00E5FF] mt-1"> active</div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* RIGHT: System Status & Glossary */}
        <div className="w-80 flex flex-col gap-4 shrink-0">
          {/* Event Chain */}
          <div className="bg-black/30 backdrop-blur-xl border border-white/10 rounded-2xl p-5">
            <h3 className="text-[12px] font-mono font-bold tracking-[0.2em] text-zinc-400 uppercase mb-4 flex items-center gap-2">
              <Activity className="w-4 h-4 text-[#00E5FF]" />
              Event Chain
            </h3>
            
            <div className="space-y-3">
              <div className="flex items-center justify-between p-3 rounded-xl bg-white/[0.02]">
                <span className="text-[12px] text-zinc-400">Total Events</span>
                <span className="text-[18px] font-bold text-[#00E5FF] font-mono">
                  {manifest?.events?.total_persisted || 0}
                </span>
              </div>
              
              <div className="flex items-center justify-between p-3 rounded-xl bg-white/[0.02]">
                <span className="text-[12px] text-zinc-400">Integrity</span>
                <span className={`text-[12px] font-bold font-mono ${
                  manifest?.events?.chain_integrity ? 'text-[#00E5FF]' : 'text-yellow-500'
                }`}>
                  {manifest?.events?.chain_integrity ? 'VERIFIED' : 'CHECKING'}
                </span>
              </div>
              
              <div className="flex items-center justify-between p-3 rounded-xl bg-white/[0.02]">
                <span className="text-[12px] text-zinc-400">Drift Locks</span>
                <span className="text-[14px] font-bold text-[#9B72CB] font-mono">
                  {manifest?.memory?.drift_chain_length || 0}
                </span>
              </div>
            </div>
          </div>

          {/* Glossary */}
          <div className="flex-1 bg-black/30 backdrop-blur-xl border border-white/10 rounded-2xl p-5 flex flex-col overflow-hidden">
            <div className="flex justify-between items-center mb-3 shrink-0">
              <div className="flex items-center gap-2">
                <BookOpen className="w-4 h-4 text-[#00E5FF]" />
                <span className="text-[11px] font-mono font-bold tracking-[0.2em] text-[#00E5FF] uppercase">GLOSSARY</span>
              </div>
              <span className="text-[9px] font-mono tracking-widest px-2 py-0.5 rounded bg-white/5 text-zinc-400 border border-white/10">
                {totalGlossaryCommands} CMDS
              </span>
            </div>
            
            <div className="relative mb-3 shrink-0">
              <Search className="w-3 h-3 absolute left-2.5 top-2.5 text-[#64748B]" />
              <input 
                type="text" 
                placeholder="Search commands..." 
                value={searchTerm} 
                onChange={(e) => setSearchTerm(e.target.value)} 
                className="w-full bg-[#030406]/80 border border-white/10 rounded-lg py-2 pl-8 pr-3 text-[10px] text-white placeholder:text-[#64748B] outline-none focus:border-[#00E5FF]/50 transition-all font-mono" 
              />
            </div>
            
            <div className="flex-1 overflow-y-auto custom-scrollbar pr-1">
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
          </div>

          {/* Quick Actions */}
          <div className="bg-black/30 backdrop-blur-xl border border-white/10 rounded-2xl p-4">
            <div className="grid grid-cols-2 gap-2">
              <button 
                onClick={fetchManifest}
                className="p-2 rounded-xl bg-[#00E5FF]/10 border border-[#00E5FF]/30 text-[#00E5FF] text-[10px] font-mono hover:bg-[#00E5FF]/20 transition-colors"
              >
                <RefreshCw className="w-4 h-4 inline mr-1" />
                REFRESH
              </button>
              <button 
                onClick={() => setMessages([])}
                className="p-2 rounded-xl bg-white/5 border border-white/10 text-zinc-400 text-[10px] font-mono hover:bg-white/10 transition-colors"
              >
                CLEAR CHAT
              </button>
            </div>
          </div>
        </div>
      </main>

      <style jsx global>{`
        .custom-scrollbar::-webkit-scrollbar {
          width: 6px;
        }
        .custom-scrollbar::-webkit-scrollbar-track {
          background: transparent;
        }
        .custom-scrollbar::-webkit-scrollbar-thumb {
          background: rgba(0, 229, 255, 0.2);
          border-radius: 3px;
        }
        .custom-scrollbar::-webkit-scrollbar-thumb:hover {
          background: rgba(0, 229, 255, 0.4);
        }
      `}</style>
    </div>
  );
}