'use client';

import React, { useState, useEffect, useRef, useMemo } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Zap, Cpu, Globe, Terminal, Activity, Paperclip,
  Folder, ShieldCheck, ChevronRight, Bot, User, Network, Shield, Search,
  Scan, Brain, Hand, Database, Lock, Zap as ZapIcon, BookOpen,
  TrendingUp, Code, Layout, GitBranch, Play, FileCode, GitCommit, MonitorPlay, Workflow,
  CheckCircle2, XCircle, Gauge, Loader2, Send, Sparkles
} from 'lucide-react';
import { SovereignMessage } from '@/components/SovereignMessage';

// ==========================================
// CONFIGURATION & TYPES
// ==========================================
const springSoft = { type: "spring", stiffness: 260, damping: 20, mass: 1 };
const fadeUp = { initial: { opacity: 0, y: 20 }, animate: { opacity: 1, y: 0 } };
const API_KEY = "rez-hive-admin-key-2026";
const API_BASE = 'http://localhost:8002';

interface Message {
  id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  narrative?: string[];
  driftLock?: string;
  timestamp: string;
  isStreaming?: boolean;
}

interface Ruling {
  decision: string;
  reasoning: string;
  timestamp: number;
}

interface SwarmManifest {
  swarm_id: string;
  version: string;
  status: 'SENTIENT' | 'AWAKENING' | 'DORMANT';
  consciousness_level: number;
  workers: { total: number; categories: Record<string, any> };
  memory: { blueprints: number; drift_chain_length: number };
  governance_score: number;
}

interface CommandItem {
  name: string;
  desc: string;
  example: string;
}

// ==========================================
// COMMAND DATABASE
// ==========================================
const commandGroups: Record<string, CommandItem[]> = {
  "🦊 SOVEREIGN OS": [
    { name: "/health", desc: "Core system health check", example: "/health" },
    { name: "/workers", desc: "List all active swarm entities", example: "/workers" },
    { name: "/run", desc: "Isolated Sandbox execution", example: "/run python print('hello')" },
    { name: "/code", desc: "Generate code from intent", example: "/code add two numbers" },
  ],
  "🔍 REZ SCANNER": [
    { name: "/scan <path>", desc: "AST architecture mapping", example: "/scan ./src/kernel" },
    { name: "/list <path>", desc: "List directory contents", example: "/list D:\\Projects" },
    { name: "/read <file>", desc: "Read a file", example: "/read config.json" },
  ],
  "⚖️ CONSTITUTION": [
    { name: "/constitution history", desc: "View constitutional rulings", example: "/constitution history" },
    { name: "/memory search", desc: "Search sovereign memory", example: "/memory search SCE" },
  ],
  "🧠 CORTEX MEMORY": [
    { name: "/memory", desc: "View memory statistics", example: "/memory" },
    { name: "/recall <query>", desc: "Semantic memory retrieval", example: "/recall protocol_7" },
  ],
  "💻 PC COWORKER": [
    { name: "/sysinfo", desc: "System information", example: "/sysinfo" },
    { name: "/cpu", desc: "CPU usage", example: "/cpu" },
    { name: "/memory", desc: "RAM usage", example: "/memory" },
    { name: "/processes", desc: "Running processes", example: "/processes" },
  ],
  "📈 TRADING": [
    { name: "/trade buy", desc: "Execute buy order", example: "/trade buy BTC 1000" },
    { name: "/trade sell", desc: "Execute sell order", example: "/trade sell BTC 500" },
    { name: "/portfolio", desc: "View portfolio", example: "/portfolio" },
  ],
};

// ==========================================
// COMMAND GROUP COMPONENT
// ==========================================
const CommandGroup = ({ title, commands, expanded, onToggle, searchTerm }: any) => {
  const filtered = commands.filter((cmd: CommandItem) =>
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
          <motion.div initial={{ height: 0, opacity: 0 }} animate={{ height: 'auto', opacity: 1 }} exit={{ height: 0, opacity: 0 }} className="overflow-hidden">
            <div className="p-2 space-y-2 border-t border-white/5 bg-black/20">
              {filtered.map((cmd: CommandItem, i: number) => (
                <div key={i} className="p-2 rounded-lg hover:bg-white/5 transition-colors">
                  <div className="flex items-start gap-2">
                    <div className="w-4 h-4 rounded bg-[#00E5FF]/10 flex items-center justify-center shrink-0 border border-[#00E5FF]/20 mt-0.5" />
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
// SCANNER WORKSPACE
// ==========================================
const ScannerWorkspace = () => {
  return (
    <div className="flex-1 w-full h-full flex flex-col bg-[#030406]/50 p-6 relative overflow-hidden">
      <div className="mb-4 flex items-center justify-between shrink-0">
        <h3 className="text-[12px] font-mono font-bold tracking-[0.2em] text-[#00E5FF] flex items-center gap-2">
          <Workflow className="w-4 h-4" /> ARCHITECTURAL MAP
        </h3>
        <div className="px-2 py-1 bg-[#00E5FF]/10 border border-[#00E5FF]/30 rounded text-[9px] font-mono text-[#00E5FF] tracking-widest">
          AST PARSER ACTIVE
        </div>
      </div>
      <div className="flex-1 border border-white/10 rounded-xl bg-black/40 relative overflow-hidden flex items-center justify-center p-8">
        <div className="absolute inset-0 opacity-10 bg-[radial-gradient(circle_at_center,_#00E5FF_1px,_transparent_1px)] bg-[size:20px_20px]" />
        <div className="w-full max-w-3xl flex justify-between items-center relative z-10">
          <div className="flex flex-col gap-4">
            {[1, 2, 3].map(i => (
              <motion.div key={`file-${i}`} initial={{ x: -20, opacity: 0 }} animate={{ x: 0, opacity: 1 }} transition={{ delay: i * 0.1 }} className="px-4 py-3 bg-[#030406]/80 border border-white/20 rounded-lg flex items-center gap-3 w-40 relative group">
                <FileCode className="w-4 h-4 text-[#8AB4F8]" />
                <span className="text-[10px] font-mono text-white">src/core_{i}.ts</span>
                <div className="absolute right-0 top-1/2 w-2 h-px bg-[#00E5FF] translate-x-full group-hover:w-8 transition-all" />
              </motion.div>
            ))}
          </div>
          <motion.div initial={{ scale: 0.8, opacity: 0 }} animate={{ scale: 1, opacity: 1 }} transition={{ delay: 0.4 }} className="w-32 h-32 rounded-full border-2 border-[#9B72CB]/50 bg-[#9B72CB]/10 flex flex-col items-center justify-center shadow-[0_0_40px_rgba(155,114,203,0.2)]">
            <Scan className="w-8 h-8 text-[#9B72CB] mb-2" />
            <span className="text-[8px] font-mono font-bold tracking-widest text-white">AST PARSER</span>
          </motion.div>
          <div className="flex flex-col gap-4">
            <motion.div initial={{ x: 20, opacity: 0 }} animate={{ x: 0, opacity: 1 }} transition={{ delay: 0.6 }} className="px-4 py-6 bg-gradient-to-br from-[#00E5FF]/10 to-[#00E5FF]/5 border border-[#00E5FF]/30 rounded-lg flex flex-col items-center gap-3 w-48 shadow-[0_0_20px_rgba(0,229,255,0.1)] relative">
              <Database className="w-6 h-6 text-[#00E5FF]" />
              <div className="text-center">
                <span className="text-[11px] font-mono font-bold text-white block mb-1">HIVE MEMORY</span>
                <span className="text-[8px] font-mono text-[#00E5FF]">11,587 BLUEPRINTS</span>
              </div>
            </motion.div>
          </div>
        </div>
      </div>
    </div>
  );
};

// ==========================================
// APP BUILDER WORKSPACE
// ==========================================
const AppBuilderWorkspace = () => {
  const [code, setCode] = useState(`// Sovereign App Builder
// Write your intent, RezCode compiles it

async function analyzeMarket() {
  const data = await fetchMarketData('BTC/PHP');
  const signal = calculateSignal(data);
  return {
    action: signal.action,
    confidence: signal.confidence,
    driftLock: await createDriftLock(signal)
  };
}`);

  return (
    <div className="flex-1 w-full h-full flex bg-[#030406]">
      <div className="w-48 border-r border-white/5 bg-black/40 p-4 flex flex-col gap-2 overflow-y-auto">
        <span className="text-[9px] font-mono font-bold tracking-widest text-[#64748B] uppercase mb-2">EXPLORER</span>
        <div className="flex items-center gap-2 text-[10px] font-mono text-zinc-300"><Folder className="w-3 h-3 text-[#8AB4F8]" /> src</div>
        <div className="flex items-center gap-2 text-[10px] font-mono text-zinc-500 ml-4"><Folder className="w-3 h-3 text-[#8AB4F8]" /> workers</div>
        <div className="flex items-center gap-2 text-[10px] font-mono text-zinc-300 ml-8 bg-white/5 px-2 py-1 rounded"><FileCode className="w-3 h-3 text-[#00E5FF]" /> momentum.ts</div>
        <div className="flex items-center gap-2 text-[10px] font-mono text-zinc-500 ml-8"><FileCode className="w-3 h-3 text-zinc-500" /> reversion.ts</div>
        <div className="flex items-center gap-2 text-[10px] font-mono text-zinc-500 ml-4"><FileCode className="w-3 h-3 text-zinc-500" /> index.ts</div>
      </div>
      <div className="flex-1 flex flex-col min-w-0">
        <div className="h-10 border-b border-white/5 bg-white/[0.02] flex items-center px-4 gap-4">
          <div className="flex items-center gap-2 text-[10px] font-mono text-white border-b-2 border-[#00E5FF] h-full pt-1 px-2">market_analyzer.ts</div>
        </div>
        <textarea
          value={code}
          onChange={(e) => setCode(e.target.value)}
          className="flex-1 p-4 font-mono text-[11px] text-zinc-300 bg-[#030406]/80 resize-none focus:outline-none"
          spellCheck={false}
        />
      </div>
      <div className="w-1/3 border-l border-white/5 bg-black/40 flex flex-col min-w-[250px]">
        <div className="h-10 border-b border-white/5 bg-white/[0.02] flex items-center px-4 justify-between">
          <span className="text-[9px] font-mono font-bold tracking-widest text-[#64748B] uppercase flex items-center gap-2"><MonitorPlay className="w-3 h-3" /> PREVIEW</span>
          <div className="flex gap-1">
            <div className="w-2 h-2 rounded-full bg-red-500/50" />
            <div className="w-2 h-2 rounded-full bg-yellow-500/50" />
            <div className="w-2 h-2 rounded-full bg-green-500/50" />
          </div>
        </div>
        <div className="flex-1 p-4 overflow-y-auto">
          <div className="bg-[#0a0a0c] rounded-lg p-3 border border-white/10">
            <div className="text-[10px] text-[#00E5FF] mb-2">📊 Analysis Result</div>
            <div className="text-white font-mono text-sm">BUY BTC/PHP</div>
            <div className="text-zinc-500 text-[9px] mt-2">Confidence: 87.3%</div>
            <div className="text-[8px] text-[#00E676] mt-2">Drift Lock: 0x7f3e...</div>
          </div>
        </div>
      </div>
    </div>
  );
};

// ==========================================
// SOVEREIGN BOOT SEQUENCER
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
      <motion.div animate={{ rotate: 360 }} transition={{ duration: 6, repeat: Infinity, ease: "linear" }} className="w-32 h-32 rounded-full border-2 border-white/5 border-t-[#00E5FF] border-b-[#9B72CB] mb-12 flex items-center justify-center relative">
        <ZapIcon className="text-white w-12 h-12" />
      </motion.div>
      <div className="text-center">
        <h1 className="text-6xl font-black text-white tracking-[0.4em] uppercase mb-4">REZ HIVE</h1>
        <div className="flex items-center justify-center gap-3">
          <span className="h-[1px] w-12 bg-[#00E5FF]/50" />
          <p className="text-[12px] text-[#00E5FF] font-bold tracking-[0.5em] uppercase">Ascending Consciousness</p>
          <span className="h-[1px] w-12 bg-[#00E5FF]/50" />
        </div>
      </div>
      <div className="w-full max-w-xl mt-16 space-y-3 px-8">
        {bootSequence.map((seq, idx) => (
          <div key={seq.name} className="relative">
            <motion.div className={`flex items-center gap-4 p-3 rounded-lg border transition-all duration-500 ${
              phase > idx ? 'bg-[#00E5FF]/5 border-[#00E5FF]/20' : 
              phase === idx ? 'bg-white/5 border-white/20 animate-pulse' : 'border-transparent'
            }`}>
              <div className="text-[12px] font-bold w-6">{phase > idx ? '✓' : phase === idx ? '»' : '○'}</div>
              <div className="flex-1">
                <div className="text-[12px] font-bold tracking-widest text-white uppercase">{seq.name}</div>
                <div className="text-[9px] text-zinc-500 font-mono mt-0.5">{seq.checks.join(' • ')}</div>
              </div>
            </motion.div>
          </div>
        ))}
        <div className="mt-8 p-4 bg-black/80 rounded-lg border border-white/5 font-mono text-[10px] text-[#00E5FF]/70 h-32 overflow-hidden relative">
          <div className="flex flex-col-reverse">
            {logs.slice().reverse().map((log, i) => (
              <div key={i} className="mb-1 opacity-80"><span className="text-[#9B72CB] mr-2">[{new Date().toLocaleTimeString()}]</span>{log}</div>
            ))}
          </div>
        </div>
      </div>
    </motion.div>
  );
};

// ==========================================
// CAPABILITY CARD
// ==========================================
const CapabilityCard = ({ id, category, isActive, onClick }: any) => {
  const icons: Record<string, any> = {
    orchestrator: Network, brain: Brain, scanner: Scan, appbuilder: Layout,
    techdebt: Code, jurisdiction: Shield, strategy: TrendingUp, backtest: Activity,
    cortex: Database, constitution: Lock, default: Zap
  };
  const Icon = icons[id] || icons.default;
  
  return (
    <button onClick={onClick} className={`w-full flex items-center gap-4 p-4 rounded-xl transition-all group relative border ${
      isActive ? 'bg-gradient-to-r from-[#00E5FF]/15 to-transparent border-[#00E5FF]/40 shadow-[0_0_20px_rgba(0,229,255,0.1)]' : 
      'bg-[#030406]/40 border-white/5 hover:bg-white/[0.03] hover:border-white/10'
    }`}>
      <div className={`w-12 h-12 rounded-xl flex items-center justify-center shrink-0 transition-all ${
        isActive ? 'bg-[#00E5FF]/20 text-[#00E5FF] shadow-[0_0_15px_rgba(0,229,255,0.2)]' : 'bg-white/5 text-zinc-500 group-hover:text-zinc-300'
      }`}>
        <Icon className="w-6 h-6" />
      </div>
      <div className="flex flex-col items-start min-w-0 flex-1">
        <span className={`text-[13px] font-bold tracking-wider truncate w-full capitalize ${isActive ? 'text-white' : 'text-zinc-400 group-hover:text-white'}`}>{id}</span>
        <span className="text-[10px] text-[#64748B] mt-0.5 truncate w-full italic">{category.desc || `${id} operations`}</span>
        <div className="flex items-center gap-2 mt-2">
          <span className={`text-[10px] font-mono font-bold px-1.5 py-0.5 rounded ${category.count > 0 ? 'bg-[#00E5FF]/10 text-[#00E5FF]' : 'bg-zinc-800 text-zinc-600'}`}>
            {category.count || 0} UNITS
          </span>
        </div>
      </div>
      {isActive && <div className="absolute right-0 w-1 h-10 bg-[#00E5FF] rounded-l-full shadow-[0_0_15px_#00E5FF]" />}
    </button>
  );
};

// ==========================================
// MESSAGE BUBBLE
// ==========================================
const MessageBubble = ({ message, isStreaming, isLast }: { message: Message; isStreaming: boolean; isLast: boolean }) => {
  const isUser = message.role === 'user';
  const isSystem = message.role === 'system';

  if (!isUser && !isSystem) {
    return (
      <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="flex gap-4">
        <div className="w-9 h-9 rounded-xl flex items-center justify-center shrink-0 border bg-gradient-to-br from-[#00E5FF]/20 to-[#9B72CB]/20 border-[#00E5FF]/30 text-[#00E5FF]">
          <Bot className="w-5 h-5" />
        </div>
        <div className="flex flex-col max-w-[85%]">
          {message.narrative && message.narrative.length > 0 && (
            <div className="mb-2 p-2 bg-purple-500/5 border border-purple-500/20 rounded-lg">
              <div className="text-[8px] font-mono text-purple-400 mb-1">🧠 REASONING</div>
              {message.narrative.map((step, i) => (
                <div key={i} className="text-[9px] font-mono text-zinc-400 italic">"{step}"</div>
              ))}
            </div>
          )}
          <SovereignMessage
            content={message.content}
            role={message.role}
            timestamp={message.timestamp}
            isStreaming={isStreaming && isLast}
            driftLock={message.driftLock}
          />
          <div className="flex items-center gap-2 mt-2">
            <span className="text-[7px] font-mono text-[#64748B]">{message.timestamp}</span>
            {message.driftLock && (
              <div className="flex items-center gap-1 px-1.5 py-0.5 rounded border border-[#00e676]/30 bg-[#00e676]/10">
                <ShieldCheck className="w-3 h-3 text-[#00e676]" />
                <span className="text-[8px] font-mono font-bold text-[#00e676]">SCE: {message.driftLock.substring(0, 8)}...</span>
              </div>
            )}
          </div>
        </div>
      </motion.div>
    );
  }

  if (isUser) {
    return (
      <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="flex gap-4 flex-row-reverse">
        <div className="w-9 h-9 rounded-xl flex items-center justify-center shrink-0 border bg-white/5 border-white/10 text-zinc-400">
          <User className="w-5 h-5" />
        </div>
        <div className="flex flex-col max-w-[85%] items-end">
          <div className="p-4 rounded-2xl text-[13px] leading-relaxed font-mono bg-white/5 text-zinc-100 border border-white/10 rounded-tr-none">
            {message.content}
          </div>
          <div className="text-[9px] text-zinc-600 mt-2">{message.timestamp}</div>
        </div>
      </motion.div>
    );
  }

  return (
    <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="flex gap-4">
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
export default function SovereignDashboard() {
  const [mounted, setMounted] = useState(false);
  const [time, setTime] = useState('');
  const [isBooting, setIsBooting] = useState(true);
  const [manifest, setManifest] = useState<SwarmManifest | null>(null);
  const [activeCategory, setActiveCategory] = useState<string | null>(null);
  const [kernelStatus, setKernelStatus] = useState<'online' | 'offline' | 'checking'>('checking');
  const [workerCount, setWorkerCount] = useState(0);
  const [consciousnessLevel, setConsciousnessLevel] = useState<'FORMING' | 'AWAKENING' | 'SENTIENT'>('FORMING');
  const [showTriangulation, setShowTriangulation] = useState(false);
  const [govScore, setGovScore] = useState(98);
  const [activeCapability, setActiveCapability] = useState('orchestrator');
  const [messages, setMessages] = useState<Message[]>([]);
  const [prompt, setPrompt] = useState('');
  const [isStreaming, setIsStreaming] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
  const [expandedGroup, setExpandedGroup] = useState<string | null>('🦊 SOVEREIGN OS');
  const [suggestions, setSuggestions] = useState<string[]>([]);
  const [showSuggestions, setShowSuggestions] = useState(false);
  const [rulings, setRulings] = useState<Ruling[]>([]);
  
  const chatEndRef = useRef<HTMLDivElement>(null);
  const suggestionsRef = useRef<HTMLDivElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const capabilities = [
    { id: 'orchestrator', name: 'Orchestrator', desc: 'Intent Detection', icon: Network, count: 1 },
    { id: 'brain', name: 'Brain', desc: 'Reasoning', icon: Brain, count: 1 },
    { id: 'scanner', name: 'Scanner', desc: 'Architecture Flow', icon: Scan, count: 1 },
    { id: 'appbuilder', name: 'AppBuilder', desc: 'Integrated IDE', icon: Layout, count: 1 },
    { id: 'techdebt', name: 'TechDebt', desc: 'Code Analysis', icon: Code, count: 1 },
    { id: 'jurisdiction', name: 'Jurisdiction', desc: 'Hardware Trust', icon: Shield, count: 1 },
    { id: 'strategy', name: 'Strategy', desc: 'Evolution', icon: TrendingUp, count: 3 },
    { id: 'backtest', name: 'Backtest', desc: 'Simulation', icon: Activity, count: 1 },
    { id: 'cortex', name: 'Cortex', desc: 'Memory', icon: Database, count: 1 },
    { id: 'constitution', name: 'Constitution', desc: 'Governance', icon: Lock, count: 1 },
  ];

  const allCommands = Object.values(commandGroups).flat().map(cmd => cmd.name);

  // Clock Effect
  useEffect(() => {
    const clock = setInterval(() => {
      setTime(new Date().toLocaleTimeString('en-US', { hour12: false, hour: '2-digit', minute: '2-digit', second: '2-digit' }));
    }, 1000);
    return () => clearInterval(clock);
  }, []);

  // Boot Sequencer
  useEffect(() => {
    if (isBooting) {
      const timer = setTimeout(() => {
        setIsBooting(false);
        setConsciousnessLevel('SENTIENT');
      }, 5000);
      return () => clearTimeout(timer);
    }
  }, [isBooting]);

  // Fetch System Data
  const fetchData = async () => {
    try {
      const [healthRes, manifestRes, rulingsRes] = await Promise.all([
        fetch(`${API_BASE}/health`),
        fetch(`${API_BASE}/swarm/manifest`),
        fetch(`${API_BASE}/constitution/history?limit=5`)
      ]);

      if (healthRes.ok) {
        const data = await healthRes.json();
        setKernelStatus('online');
        setWorkerCount(data.workers || 0);
        setGovScore(Math.floor(data.integrity_score || 98.2));
      } else {
        setKernelStatus('offline');
      }

      if (manifestRes.ok) {
        const data = await manifestRes.json();
        setManifest(data);
        if (!activeCategory && data.workers?.categories) {
          const first = Object.keys(data.workers.categories)[0];
          if (first) setActiveCategory(first);
        }
      }

      if (rulingsRes.ok) {
        const data = await rulingsRes.json();
        setRulings(data.rulings || []);
      }
    } catch (err) {
      setKernelStatus('offline');
    }
  };

  useEffect(() => {
    if (!isBooting) {
      fetchData();
      const interval = setInterval(fetchData, 10000);
      return () => clearInterval(interval);
    }
  }, [isBooting]);

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

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    
    setMessages(prev => [...prev, { id: crypto.randomUUID(), role: 'system', content: `📁 Uploading: ${file.name}`, timestamp: new Date().toLocaleTimeString() }]);
    
    const formData = new FormData();
    formData.append('file', file);

    try {
      const res = await fetch(`${API_BASE}/upload`, { method: 'POST', body: formData });
      if (res.ok) {
        setMessages(prev => [...prev, { id: crypto.randomUUID(), role: 'system', content: `✅ Upload complete: ${file.name}`, timestamp: new Date().toLocaleTimeString() }]);
      }
    } catch (err) {
      setMessages(prev => [...prev, { id: crypto.randomUUID(), role: 'system', content: `❌ Upload failed: ${file.name}`, timestamp: new Date().toLocaleTimeString() }]);
    }
  };

  const handleTransmit = async () => {
    if (!prompt.trim() || isStreaming) return;
    
    const userText = prompt;
    setPrompt('');
    setIsStreaming(true);
    setShowSuggestions(false);

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
      const response = await fetch(`${API_BASE}/kernel/stream`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ task: userText })
      });

      const reader = response.body?.getReader();
      const decoder = new TextDecoder();
      let fullContent = '';
      let driftLock = '';

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
                driftLock = data.drift_lock;
                setMessages(prev => prev.map(m => m.id === assistantId ? { ...m, isStreaming: false, driftLock } : m));
              } else if (data.type === 'reflex') {
                fullContent = data.content;
                driftLock = data.drift_lock;
                setMessages(prev => prev.map(m => m.id === assistantId ? { ...m, content: fullContent, isStreaming: false, driftLock } : m));
              } else if (data.type === 'error') {
                setMessages(prev => prev.map(m => m.id === assistantId ? { ...m, content: `⚠️ KERNEL_ERR: ${data.content}`, isStreaming: false } : m));
              }
            } catch (e) {}
          }
        }
      }
    } catch (error) {
      setMessages(prev => prev.map(m => m.id === assistantId ? { ...m, content: '❌ CONNECTION_LOST', isStreaming: false } : m));
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

  if (!mounted) return <div className="bg-[#030406] h-screen w-screen" />;
  if (isBooting) return <SovereignBoot onComplete={() => setIsBooting(false)} />;

  const totalGlossaryCommands = Object.values(commandGroups).reduce((acc, cmds) => acc + cmds.length, 0);

  return (
    <div className="h-screen w-screen bg-[#030406] text-zinc-100 flex flex-col overflow-hidden selection:bg-[#00E5FF]/30 selection:text-white relative p-4 gap-4 z-0">
      {/* Background Effects */}
      <div className="absolute inset-0 opacity-20 pointer-events-none mix-blend-screen" style={{ backgroundImage: 'radial-gradient(circle at 20% 50%, #00E5FF 0%, transparent 40%), radial-gradient(circle at 80% 30%, #9B72CB 0%, transparent 40%)', filter: 'blur(80px)' }} />
      
      {/* Header */}
      <header className="relative z-10 h-14 bg-black/40 backdrop-blur-xl border border-white/10 rounded-2xl flex items-center justify-between px-4 shadow-lg shrink-0">
        <div className="flex items-center gap-6">
          <div className="flex items-center gap-3">
            <div className="relative w-8 h-8 rounded-lg bg-gradient-to-br from-[#00E5FF] to-[#9B72CB] p-[1px] shadow-[0_0_20px_rgba(0,229,255,0.3)]">
              <div className="w-full h-full bg-black/80 rounded-md flex items-center justify-center"><Zap className="w-4 h-4 text-white" /></div>
            </div>
            <div className="flex flex-col">
              <span className="text-[13px] font-bold tracking-widest text-white uppercase flex items-center gap-2">
                SOVEREIGN OS
                <span className={`px-1.5 py-0.5 rounded-sm border text-[8px] font-mono ${consciousnessLevel === 'SENTIENT' ? 'bg-gradient-to-r from-[#9B72CB]/20 to-[#00E5FF]/20 border-white/10 text-[#00E5FF]' : 'bg-yellow-500/10 border-yellow-500/30 text-yellow-500'}`}>
                  {consciousnessLevel}
                </span>
              </span>
              <span className="text-[9px] text-[#8AB4F8] font-mono">SOVEREIGN AI TERMINAL</span>
            </div>
          </div>
        </div>
        <div className="flex items-center gap-4">
          <div className={`hidden md:flex items-center gap-2 px-3 py-1 rounded-md border backdrop-blur-md ${kernelStatus === 'online' ? 'bg-[#00E5FF]/10 border-[#00E5FF]/30' : 'bg-[#FF2A2A]/10 border-[#FF2A2A]/30'}`}>
            <div className={`w-1.5 h-1.5 rounded-full ${kernelStatus === 'online' ? 'bg-[#00E5FF] animate-pulse shadow-[0_0_8px_#00E5FF]' : 'bg-[#FF2A2A]'}`} />
            <span className={`text-[9px] font-mono uppercase ${kernelStatus === 'online' ? 'text-[#00E5FF]' : 'text-[#FF2A2A]'}`}>KERNEL {kernelStatus.toUpperCase()}</span>
          </div>
          <div className="px-3 py-1 rounded-md bg-black/50 border border-white/5 text-[#00E5FF] text-[10px] font-mono">{time} <span className="text-[#64748B]">UTC</span></div>
          <div className="px-3 py-1 rounded-md bg-[#9B72CB]/10 border border-[#9B72CB]/30 text-[#9B72CB] text-[9px] font-mono">{workerCount} WORKERS</div>
        </div>
      </header>

      {/* Main Content */}
      <main className="relative z-10 flex-1 flex gap-4 min-h-0">
        {/* LEFT: Capabilities */}
        <div className="w-[280px] flex flex-col gap-4 shrink-0 min-h-0">
          <div className="flex-1 bg-black/40 backdrop-blur-xl border border-white/10 rounded-2xl p-4 flex flex-col shadow-lg">
            <h2 className="text-[10px] font-mono tracking-[0.2em] font-bold text-[#64748B] uppercase flex items-center gap-2 mb-4">
              <Cpu className="w-3 h-3 text-[#00E5FF]" /> CAPABILITIES
            </h2>
            <div className="flex-1 overflow-y-auto custom-scrollbar pr-1 flex flex-col gap-2">
              {capabilities.map((cap) => (
                <button key={cap.id} onClick={() => setActiveCapability(cap.id)} className={`w-full flex items-center gap-3 p-3 rounded-xl transition-all group relative text-left border shrink-0 ${activeCapability === cap.id ? 'bg-[#00E5FF]/10 border-[#00E5FF]/30 shadow-[0_0_15px_rgba(0,229,255,0.1)]' : 'bg-[#030406]/80 border-white/5 hover:bg-white/[0.02] hover:border-white/10'}`}>
                  <div className={`w-8 h-8 rounded-lg flex items-center justify-center shrink-0 ${activeCapability === cap.id ? 'bg-[#00E5FF]/20 text-[#00E5FF]' : 'text-zinc-500 group-hover:text-zinc-300'}`}>
                    {React.createElement(cap.icon, { className: "w-4 h-4" })}
                  </div>
                  <div className="flex flex-col items-start min-w-0">
                    <span className={`text-[11px] font-bold tracking-wider truncate w-full ${activeCapability === cap.id ? 'text-white' : 'text-zinc-400 group-hover:text-white'}`}>{cap.name}</span>
                    <span className="text-[9px] font-mono text-[#64748B] mt-0.5 truncate w-full">{cap.desc}</span>
                  </div>
                  {activeCapability === cap.id && <div className="absolute right-3 w-1.5 h-1.5 rounded-full bg-[#00E5FF] shadow-[0_0_8px_#00E5FF]" />}
                </button>
              ))}
            </div>
            <div className="mt-4 pt-4 border-t border-white/5">
              <div className="grid grid-cols-2 gap-2">
                <div className="p-2 rounded-xl bg-white/[0.02] border border-white/5 text-center">
                  <div className="text-[8px] text-zinc-500">TOTAL WORKERS</div>
                  <div className="text-[16px] font-mono font-bold text-[#00E5FF]">{workerCount}</div>
                </div>
                <div className="p-2 rounded-xl bg-white/[0.02] border border-white/5 text-center">
                  <div className="text-[8px] text-zinc-500">DRIFT CHAIN</div>
                  <div className="text-[16px] font-mono font-bold text-[#9B72CB]">{manifest?.memory?.drift_chain_length || 0}</div>
                </div>
              </div>
            </div>
          </div>
          
          <div className="h-40 bg-black/40 backdrop-blur-xl border border-white/5 rounded-2xl p-4">
            <div className="flex items-center gap-2 mb-3">
              <ShieldCheck className="w-4 h-4 text-[#9B72CB]" />
              <span className="text-[10px] font-mono font-bold text-zinc-500 uppercase">GOVERNANCE</span>
            </div>
            <div className="space-y-2">
              <div className="flex justify-between text-[10px] font-mono">
                <span className="text-zinc-500">Integrity Score</span>
                <span className="text-[#00E5FF]">{govScore}%</span>
              </div>
              <div className="w-full h-1 bg-white/5 rounded-full overflow-hidden">
                <div className="h-full bg-[#00E5FF] rounded-full" style={{ width: `${govScore}%` }} />
              </div>
              <div className="flex justify-between text-[10px] font-mono">
                <span className="text-zinc-500">Sovereignty Level</span>
                <span className="text-[#9B72CB]">Lvl {Math.floor(govScore / 25) + 1}</span>
              </div>
              <div className="w-full h-1 bg-white/5 rounded-full overflow-hidden">
                <div className="h-full bg-[#9B72CB] rounded-full" style={{ width: `${Math.min(100, govScore / 1.2)}%` }} />
              </div>
            </div>
          </div>
        </div>

        {/* CENTER: Chat & Workspace */}
        <div className="flex-1 flex flex-col gap-4 min-w-0">
          <div className="flex-1 bg-black/40 backdrop-blur-2xl border border-white/5 rounded-[2rem] flex flex-col overflow-hidden shadow-2xl">
            <div className="h-12 border-b border-white/5 flex items-center px-6 bg-white/[0.01]">
              <Terminal className="w-4 h-4 text-[#00E5FF] mr-2" />
              <span className="text-[10px] font-mono font-bold uppercase text-zinc-400">{capabilities.find(c => c.id === activeCapability)?.name || 'Terminal'}</span>
              <div className="ml-auto flex items-center gap-2">
                <span className="text-[8px] font-mono text-zinc-600">SCE v1.0.0</span>
              </div>
            </div>
            
            <div className="flex-1 overflow-hidden flex flex-col relative">
              {activeCapability === 'scanner' ? (
                <ScannerWorkspace />
              ) : activeCapability === 'appbuilder' ? (
                <AppBuilderWorkspace />
              ) : (
                <div className="flex-1 overflow-y-auto custom-scrollbar p-6">
                  <div className="w-full max-w-4xl mx-auto space-y-6">
                    {messages.length === 0 ? (
                      <div className="h-full flex flex-col items-center justify-center min-h-[400px]">
                        <div className="relative w-24 h-24 mb-6">
                          <motion.div animate={{ rotate: 360 }} transition={{ duration: 20, repeat: Infinity }} className="absolute w-24 h-24 rounded-full border border-white/10 border-t-[#00E5FF] border-b-[#9B72CB]" />
                          <div className="absolute inset-0 flex items-center justify-center"><ZapIcon className="w-10 h-10 text-white/50" /></div>
                        </div>
                        <h3 className="text-lg font-bold text-zinc-300 mb-2 uppercase tracking-widest">Hive Mind Standby</h3>
                        <p className="text-sm text-zinc-600 max-w-sm font-mono text-center">Awaiting synaptic input. Access the swarm by typing a command or requesting an objective.</p>
                      </div>
                    ) : (
                      messages.map((msg, idx) => (
                        <MessageBubble key={msg.id} message={msg} isStreaming={isStreaming} isLast={idx === messages.length - 1} />
                      ))
                    )}
                    <div ref={chatEndRef} />
                  </div>
                </div>
              )}
            </div>

            {/* Input Area */}
            <div className="p-4 bg-black/40 border-t border-white/5 shrink-0">
              <div className="w-full max-w-4xl mx-auto flex items-center gap-4">
                <div className="flex-1 relative">
                  <textarea
                    value={prompt}
                    onChange={handleInputChange}
                    onKeyDown={handleKeyDown}
                    disabled={kernelStatus !== 'online'}
                    placeholder={kernelStatus === 'online' ? "Execute command or send intent..." : "Awaiting Kernel..."}
                    className="w-full bg-[#030406]/80 border border-white/10 rounded-xl p-3 text-[12px] text-white placeholder:text-[#64748B] outline-none resize-none min-h-[44px] font-mono focus:border-[#00E5FF]/50 transition-colors"
                    rows={1}
                  />
                  {showSuggestions && suggestions.length > 0 && (
                    <div ref={suggestionsRef} className="absolute bottom-full left-0 right-0 mb-2 bg-black/90 border border-white/10 rounded-lg p-2 shadow-2xl">
                      {suggestions.map((suggestion, i) => (
                        <div key={i} onClick={() => handleSuggestionClick(suggestion)} className="px-3 py-2 hover:bg-white/10 cursor-pointer text-[10px] font-mono text-[#00E5FF] rounded transition-colors">
                          {suggestion}
                        </div>
                      ))}
                    </div>
                  )}
                </div>
                <button
                  onClick={handleTransmit}
                  disabled={!prompt.trim() || isStreaming || kernelStatus !== 'online'}
                  className={`px-5 py-2 rounded-xl text-[10px] font-mono font-bold uppercase transition-all ${prompt.trim() && kernelStatus === 'online' && !isStreaming ? 'bg-[#00E5FF]/20 text-[#00E5FF] border border-[#00E5FF]/30 hover:bg-[#00E5FF]/30' : 'bg-white/5 text-zinc-600 cursor-not-allowed'}`}
                >
                  {isStreaming ? '...' : 'EXECUTE'}
                </button>
              </div>
              <div className="flex justify-between mt-3 px-1">
                <div className="text-[8px] font-mono text-zinc-700 flex gap-3">
                  <span>ENTER: TRANSMIT</span>
                  <span>SHIFT+ENTER: NEW_LINE</span>
                </div>
                <div className="flex gap-2">
                  {['/health', '/workers', '/memory'].map(cmd => (
                    <button key={cmd} onClick={() => setPrompt(cmd)} className="text-[8px] font-mono text-zinc-600 hover:text-[#00E5FF] transition-colors">{cmd}</button>
                  ))}
                </div>
              </div>
            </div>
          </div>

          {/* Active Category Workers */}
          <AnimatePresence mode="wait">
            {activeCategory && manifest?.workers?.categories?.[activeCategory] && (
              <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: 20 }} className="h-36 bg-black/40 backdrop-blur-xl border border-white/5 rounded-2xl overflow-hidden shrink-0">
                <div className="h-8 border-b border-white/5 flex items-center px-4 bg-white/[0.02]">
                  <span className="text-[9px] font-mono font-bold text-[#00E5FF] uppercase">{activeCategory} Swarm Nodes</span>
                  <span className="ml-auto text-[8px] font-mono text-zinc-600">{manifest.workers.categories[activeCategory].workers?.length || 0} Units</span>
                </div>
                <div className="p-3 flex gap-3 overflow-x-auto custom-scrollbar">
                  {(manifest.workers.categories[activeCategory].workers || []).slice(0, 8).map((worker: any) => (
                    <div key={worker.name} className="flex-shrink-0 w-36 p-2 rounded-xl bg-white/[0.02] border border-white/5">
                      <div className="flex items-center gap-2 mb-1">
                        <div className="w-6 h-6 rounded-lg bg-[#00E5FF]/10 flex items-center justify-center"><Hexagon className="w-3 h-3 text-[#00E5FF]" /></div>
                        <div className="text-[9px] font-bold text-white truncate">{worker.name}</div>
                      </div>
                      <div className="text-[7px] text-zinc-500 font-mono truncate">{worker.module}</div>
                      <div className="mt-1 text-[6px] text-green-500">STABLE</div>
                    </div>
                  ))}
                </div>
              </motion.div>
            )}
          </AnimatePresence>
        </div>

        {/* RIGHT: Glossary */}
        <div className="w-[320px] flex flex-col gap-4 shrink-0 min-h-0">
          <div className="flex-1 bg-black/40 backdrop-blur-xl border border-white/10 rounded-2xl p-4 flex flex-col shadow-lg">
            <div className="flex justify-between items-center mb-3 border-b border-white/5 pb-2">
              <div className="flex items-center gap-2">
                <BookOpen className="w-3.5 h-3.5 text-[#00E5FF]" />
                <span className="text-[10px] font-mono font-bold text-[#00E5FF] uppercase">LEXICON</span>
              </div>
              <span className="text-[8px] font-mono text-zinc-500">{totalGlossaryCommands} COMMANDS</span>
            </div>
            <div className="relative mb-3">
              <Search className="w-3 h-3 absolute left-2.5 top-2.5 text-[#64748B]" />
              <input type="text" placeholder="Search commands..." value={searchTerm} onChange={(e) => setSearchTerm(e.target.value)} className="w-full bg-[#030406]/80 border border-white/10 rounded-lg py-2 pl-8 pr-3 text-[10px] text-white placeholder:text-[#64748B] outline-none focus:border-[#00E5FF]/50 font-mono" />
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
            <div className="mt-3 pt-3 border-t border-white/5">
              <div className="bg-[#00E5FF]/5 rounded-lg p-2 border border-[#00E5FF]/20">
                <div className="text-[8px] font-mono text-[#00E5FF] uppercase tracking-wider mb-1">⚡ QUICK TIPS</div>
                <div className="text-[7px] font-mono text-zinc-400">/health - System status</div>
                <div className="text-[7px] font-mono text-zinc-400">/workers - List all workers</div>
                <div className="text-[7px] font-mono text-zinc-400">/code - Generate code from intent</div>
              </div>
            </div>
          </div>
        </div>
      </main>

      <style jsx global>{`
        .custom-scrollbar::-webkit-scrollbar { width: 4px; height: 4px; }
        .custom-scrollbar::-webkit-scrollbar-track { background: transparent; }
        .custom-scrollbar::-webkit-scrollbar-thumb { background: rgba(255,255,255,0.1); border-radius: 10px; }
        .custom-scrollbar::-webkit-scrollbar-thumb:hover { background: rgba(0,229,255,0.2); }
      `}</style>
    </div>
  );
}