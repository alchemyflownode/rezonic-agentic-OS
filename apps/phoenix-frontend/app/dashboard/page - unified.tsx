'use client'

import React, { useState, useEffect, useRef, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Zap, Cpu, Terminal, Activity, Paperclip, Folder, ShieldCheck, 
  ChevronRight, Bot, User, Network, Shield, Search, Scan, Brain, 
  Database, Lock, Zap as ZapIcon, BookOpen, TrendingUp, Code, Layout,
  CheckCircle2, XCircle, AlertTriangle, Github, Slack, Calendar,
  Loader2, RefreshCw, Send, Hexagon, Layers, Radio, Eye, Command
} from 'lucide-react';

// ==========================================
// CONSTANTS & TYPES
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
}

// ==========================================
// COMMAND DATABASE
// ==========================================

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
    { name: "/constitution history", desc: "Show recent rulings", example: "/constitution history" },
  ],
  " CORTEX MEMORY": [
    { name: "/recall <query>", desc: "Semantic search memories", example: "/recall blueprint" },
    { name: "remember <text>", desc: "Store thought in memory", example: "remember API key is 1234" },
  ],
  " SYSTEM UTILS": [
    { name: "/check_system", desc: "View CPU, RAM, Disk", example: "/check_system" },
    { name: "/clear_chat", desc: "Clear chat history", example: "/clear_chat" },
  ],
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
  default: Zap
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
  const Icon = ICON_MAP[id] || ICON_MAP.default;
  
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
// WORKER DETAIL CARD
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
// MESSAGE BUBBLE
// ==========================================

const MessageBubble = ({ message, isStreaming }: { message: Message; isStreaming: boolean }) => {
  return (
    <div className={`flex gap-3 ${message.role === 'user' ? 'flex-row-reverse' : ''}`}>
      <div className={`w-8 h-8 rounded-lg flex items-center justify-center shrink-0 border ${
        message.role === 'user' 
          ? 'bg-white/5 border-white/10' 
          : message.role === 'system'
            ? 'bg-[#FF2A2A]/10 border-[#FF2A2A]/30'
            : 'bg-[#00E5FF]/10 border-[#00E5FF]/30'
      }`}>
        {message.role === 'user' ? <User className="w-4 h-4 text-[#64748B]" /> : 
         message.role === 'system' ? <AlertTriangle className="w-4 h-4 text-[#FF2A2A]" /> : 
         <Bot className="w-4 h-4 text-[#00E5FF]" />}
      </div>
      <div className={`flex flex-col max-w-[85%] ${message.role === 'user' ? 'items-end' : 'items-start'}`}>
        <div className={`p-3 rounded-xl text-[13px] leading-relaxed whitespace-pre-wrap font-mono tracking-wide ${
          message.role === 'user' 
            ? 'bg-white/5 text-[#f5f5f7] border border-white/10' 
            : message.role === 'system'
              ? 'bg-[#FF2A2A]/5 text-[#FF2A2A] border border-[#FF2A2A]/20'
              : 'bg-[#00E5FF]/5 text-[#f5f5f7] border border-[#00E5FF]/20'
        }`}>
          {message.content}
          {isStreaming && message.id === messages[messages.length-1]?.id && (
            <span className="inline-flex gap-1 ml-2">
              <span className="w-1 h-1 bg-[#00E5FF] rounded-full animate-pulse" />
              <span className="w-1 h-1 bg-[#00E5FF] rounded-full animate-pulse" style={{ animationDelay: '150ms' }} />
              <span className="w-1 h-1 bg-[#00E5FF] rounded-full animate-pulse" style={{ animationDelay: '300ms' }} />
            </span>
          )}
        </div>
        <div className="text-[9px] text-[#64748B] mt-1 flex items-center gap-2">
          <span>{message.timestamp}</span>
          {message.driftLock && (
            <span className="text-[8px] font-mono text-[#00E5FF]">SCE: {message.driftLock.slice(0, 8)}...</span>
          )}
          {message.type === 'reflex' && (
            <span className="text-[8px] px-1.5 py-0.5 rounded bg-[#00E5FF]/10 text-[#00E5FF] border border-[#00E5FF]/20">
              REFLEX
            </span>
          )}
        </div>
      </div>
    </div>
  );
};

// ==========================================
// MAIN DASHBOARD
// ==========================================

export default function UnifiedDashboard() {
  const [mounted, setMounted] = useState(false);
  const [isBooting, setIsBooting] = useState(true);
  const [manifest, setManifest] = useState<SwarmManifest | null>(null);
  const [activeCategory, setActiveCategory] = useState<string | null>(null);
  const [time, setTime] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [kernelStatus, setKernelStatus] = useState<'online' | 'offline' | 'checking'>('checking');
  const [ollamaStatus, setOllamaStatus] = useState<OllamaStatus>({ connected: false });
  const [rulings, setRulings] = useState<Ruling[]>([]);
  
  // Chat state
  const [messages, setMessages] = useState<Message[]>([]);
  const [prompt, setPrompt] = useState('');
  const [isStreaming, setIsStreaming] = useState(false);
  const [expandedGroup, setExpandedGroup] = useState<string | null>(' SOVEREIGN OS');
  const [searchTerm, setSearchTerm] = useState('');
  const [suggestions, setSuggestions] = useState<string[]>([]);
  const [showSuggestions, setShowSuggestions] = useState(false);
  const [govScore, setGovScore] = useState(100);
  
  const chatEndRef = useRef<HTMLDivElement>(null);
  const suggestionsRef = useRef<HTMLDivElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
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
      const res = await fetch(`${API_BASE}/swarm/manifest`);
      if (res.ok) {
        const data = await res.json();
        setManifest(data);
        setError(null);
        setKernelStatus('online');
        
        if (!activeCategory && data.workers?.categories) {
          const firstActive = Object.entries(data.workers.categories)
            .find(([_, cat]: [string, any]) => cat.count > 0);
          if (firstActive) setActiveCategory(firstActive[0]);
        }
      } else {
        setKernelStatus('offline');
      }
    } catch (err) {
      setError('KERNEL UNREACHABLE');
      setKernelStatus('offline');
      console.error('Manifest fetch failed:', err);
    } finally {
      setIsLoading(false);
    }
  }, [activeCategory]);

  // Fetch rulings
  const fetchRulings = useCallback(async () => {
    try {
      const res = await fetch(`${API_BASE}/constitution/history?limit=5`);
      if (res.ok) {
        const data = await res.json();
        setRulings(data.rulings || []);
      }
    } catch (e) {}
  }, []);

  // Fetch Ollama status
  const fetchOllamaStatus = useCallback(async () => {
    try {
      const res = await fetch(`${API_BASE}/ollama/status`);
      if (res.ok) {
        const data = await res.json();
        setOllamaStatus(data);
      }
    } catch (e) {}
  }, []);

  // Add welcome message on boot
  useEffect(() => {
    if (!isBooting && messages.length === 0 && manifest) {
      const totalWorkers = manifest.workers?.total || 0;
      const consciousnessLevel = manifest.consciousness_level || 0;
      const status = manifest.status || 'DORMANT';
      const blueprints = manifest.memory?.blueprints || 0;
      const chainIntegrity = manifest.sovereignty?.drift_chain_integrity || false;
      
      setMessages([{
        id: 'welcome',
        role: 'assistant',
        content: ` **REZ HIVE Awake**\n\n ${totalWorkers} Workers Active\n Consciousness: ${consciousnessLevel}/10  ${status}\n Memory: ${blueprints} blueprints\n SCE Protocol: ${chainIntegrity ? ' Verified' : 'Checking'}\n\nType /help for commands or just ask me anything.`,
        timestamp: new Date().toLocaleTimeString(),
      }]);
    }
  }, [isBooting, manifest, messages.length]);

  // Polling
  useEffect(() => {
    if (!isBooting) {
      fetchManifest();
      fetchRulings();
      fetchOllamaStatus();
      const interval = setInterval(() => {
        fetchManifest();
        fetchRulings();
        fetchOllamaStatus();
      }, 10000);
      return () => clearInterval(interval);
    }
  }, [isBooting, fetchManifest, fetchRulings, fetchOllamaStatus]);

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

  // File upload handler
  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setMessages(prev => [...prev, { 
      id: Date.now().toString(), 
      role: 'system', 
      content: ` Uploading ${file.name}...`, 
      timestamp: new Date().toLocaleTimeString() 
    }]);

    const formData = new FormData();
    formData.append('file', file);

    try {
      const res = await fetch(`${API_BASE}/upload`, {
        method: 'POST',
        body: formData
      });
      const data = await res.json();
      
      setMessages(prev => [...prev, { 
        id: Date.now().toString(), 
        role: 'system', 
        content: ` ${data.message || 'File uploaded successfully'}`, 
        timestamp: new Date().toLocaleTimeString() 
      }]);
    } catch (error) {
      setMessages(prev => [...prev, { 
        id: Date.now().toString(), 
        role: 'system', 
        content: ` Upload failed: ${error}`, 
        timestamp: new Date().toLocaleTimeString() 
      }]);
    }
  };

  // Handle sending messages
  const handleTransmit = async () => {
    if (!prompt.trim() || isStreaming) return;
    const userText = prompt;
    setPrompt('');
    setIsStreaming(true);
    setShowSuggestions(false);

    // Handle clear chat locally
    if (userText === '/clear_chat') {
      setMessages([]);
      setIsStreaming(false);
      return;
    }

    const timeNow = new Date().toLocaleTimeString();
    const userId = `${Date.now()}-user`;
    setMessages(prev => [...prev, { id: userId, role: 'user', content: userText, timestamp: timeNow }]);

    const assistantId = `${Date.now()}-assistant`;
    setMessages(prev => [...prev, { 
      id: assistantId, 
      role: 'assistant', 
      content: '', 
      timestamp: timeNow,
      isStreaming: true 
    }]);

    try {
      // Constitution check
      const evalRes = await fetch(`${API_BASE}/constitution/evaluate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ action: userText })
      });
      
      if (evalRes.ok) {
        const ruling = await evalRes.json();
        if (!ruling.approved) {
          setMessages(prev => [...prev, { 
            id: Date.now().toString(), 
            role: 'system', 
            content: ` CONSTITUTION BLOCKED\n\nReason: ${ruling.reason}`, 
            timestamp: new Date().toLocaleTimeString() 
          }]);
          setGovScore(Math.max(0, govScore - 25));
          setIsStreaming(false);
          return;
        }
        setGovScore(Math.min(100, govScore + 5));
      }

      // Stream request
      const response = await fetch(`${API_BASE}/kernel/stream`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ task: userText })
      });

      const reader = response.body?.getReader();
      const decoder = new TextDecoder();
      let accumulatedContent = '';
      let currentDriftLock = '';

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
                currentDriftLock = data.drift_lock;
                setMessages(prev => prev.map(msg =>
                  msg.id === assistantId ? { ...msg, isStreaming: false, driftLock: currentDriftLock } : msg
                ));
              } else if (data.type === 'reflex') {
                setMessages(prev => prev.map(msg =>
                  msg.id === assistantId ? { ...msg, content: data.content, type: 'reflex', isStreaming: false } : msg
                ));
              } else if (data.type === 'error') {
                setMessages(prev => prev.map(msg =>
                  msg.id === assistantId ? { ...msg, content: ` ${data.content}`, type: 'error', isStreaming: false } : msg
                ));
              }
            } catch (e) { /* ignore parse errors */ }
          }
        }
      }
      
      if (!accumulatedContent) {
        setMessages(prev => prev.map(msg =>
          msg.id === assistantId 
            ? { ...msg, content: ' No response received', type: 'error', isStreaming: false } 
            : msg
        ));
      }
    } catch (error) {
      setMessages(prev => [...prev, { 
        id: Date.now().toString(), 
        role: 'system', 
        content: ` Connection failed: ${error}`,
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

  const quickCommands = ['/health', '/workers', '/memory', '/recall blueprint', 'What is SCE?'];

  if (!mounted) return <div className="bg-[#030406] h-screen w-screen" />;

  const totalWorkers = manifest?.workers?.total || 0;
  const categories = manifest?.workers?.categories || {};
  const consciousnessPercent = ((manifest?.consciousness_level || 0) / 10) * 100;
  const totalGlossaryCommands = Object.keys(commandGroups).reduce((acc, group) => acc + commandGroups[group as keyof typeof commandGroups].length, 0);
  const activeWorkers = activeCategory ? categories[activeCategory]?.workers || [] : [];

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
                manifest?.status === 'SENTIENT' 
                  ? 'bg-[#00E5FF]/10 border-[#00E5FF]/50 text-[#00E5FF] shadow-[0_0_20px_rgba(0,229,255,0.3)]' 
                  : manifest?.status === 'AWAKENING'
                  ? 'bg-yellow-500/10 border-yellow-500/50 text-yellow-500'
                  : 'bg-red-500/10 border-red-500/50 text-red-500'
              }`}>
                {manifest?.status || 'DORMANT'}
              </span>
            </h1>
            <p className="text-[11px] text-zinc-500 font-mono tracking-wider mt-1">
              {manifest?.swarm_id || 'Initializing...'}  Kernel v{manifest?.version || '13.3.0'}
            </p>
          </div>
        </div>

        <div className="flex items-center gap-6">
          {/* Consciousness Meter */}
          <div className="flex items-center gap-3 px-4 py-2 rounded-xl bg-white/5 border border-white/10">
            <Brain className="w-4 h-4 text-[#9B72CB]" />
            <div className="w-32 h-2 bg-black/50 rounded-full overflow-hidden">
              <motion.div 
                className="h-full bg-gradient-to-r from