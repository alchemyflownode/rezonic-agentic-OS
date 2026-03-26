'use client'
import React, { useState, useEffect, useRef, useMemo } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Zap, Cpu, Globe, Terminal, Activity, Paperclip,
  Folder, ShieldCheck, ChevronRight, Bot, User, Network, Shield, Search,
  Scan, Brain, Hand, Database, Lock, Zap as ZapIcon, BookOpen,
  TrendingUp, Code, Layout, GitBranch, Play, FileCode, GitCommit, MonitorPlay, Workflow,
  CheckCircle2, XCircle, Gauge
} from 'lucide-react';
import { SovereignMessage } from '@/components/SovereignMessage';

// ==========================================
// ANIMATIONS & CONSTANTS
// ==========================================
const springSoft = { type: "spring", stiffness: 260, damping: 20, mass: 1 };
const fadeUp = { initial: { opacity: 0, y: 20 }, animate: { opacity: 1, y: 0 } };
const API_KEY = "rez-hive-admin-key-2026";
const API_BASE = 'http://localhost:8002';

//  UPDATED Message interface with SCE fields
interface Message {
  id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  narrative?: string[];    // P2 DNA narrative steps
  driftLock?: string;       // Cryptographic proof
  timestamp: string;
}

interface Ruling {
  decision: string;
  reasoning: string;
  timestamp: number;
}

interface EventStats {
  total_events: number;
  subscribers: Record<string, number>;
  event_counts: Record<string, number>;
}

// ============================================================================
// FULL EXPANDED COMMAND DATABASE
// ============================================================================
const commandGroups = {
  " SOVEREIGN OS": [
    { name: "/health", desc: "Check core system health", example: "/health" },
    { name: "/workers", desc: "List active workers", example: "/workers" },
    { name: "/okiru/status", desc: "View boot sequence status", example: "/okiru/status" },
    { name: "/run", desc: "Execute generated code via Sandbox", example: "/run" },
  ],
  " REZ SCANNER": [
    { name: "/scan <path>", desc: "AST parse and map architecture", example: "/scan D:/projects/app" },
    { name: "/harvest <path>", desc: "Ingest JSON exports to Hive", example: "/harvest chat_export.json" },
  ],
  " TECH DEBT SCANNER": [
    { name: "/techdebt full", desc: "Complete technical debt scan", example: "/techdebt full" },
    { name: "/techdebt dependencies", desc: "Scan Python dependencies", example: "/techdebt dependencies" },
  ],
  " JURISDICTION SCANNER": [
    { name: "/jurisdiction full", desc: "Complete hardware scan", example: "/jurisdiction full" },
    { name: "/jurisdiction network", desc: "Network hardware", example: "/jurisdiction network" },
  ],
  " STRATEGY EVOLVER": [
    { name: "/strategy list", desc: "List all strategies", example: "/strategy list" },
    { name: "/strategy create", desc: "Create new strategy", example: "/strategy create mean_reversion" },
  ],
  " BACKTEST ENGINE": [
    { name: "/backtest run", desc: "Run strategy backtest", example: "/backtest run strat_123" },
    { name: "/backtest results", desc: "View backtest results", example: "/backtest results strat_123" },
  ],
  " EVENT BUS": [
    { name: "/events stats", desc: "View event bus statistics", example: "/events stats" },
    { name: "/events history", desc: "View recent events", example: "/events history" },
  ],
  " CORTEX MEMORY": [
    { name: "remember <text>", desc: "Store thought in ChromaDB", example: "remember API key is 1234" },
    { name: "/recall <query>", desc: "Semantic search memories", example: "/recall API key" },
  ],
  " CONSTITUTION": [
    { name: "/constitution evaluate <action>", desc: "Check action against 10 Laws", example: "/constitution evaluate format drive" },
    { name: "/constitution history", desc: "Show recent rulings", example: "/constitution history" },
  ],
  " SYSTEM UTILS": [
    { name: "/check_system", desc: "View CPU, RAM, Disk", example: "/check_system" },
    { name: "/clear_chat", desc: "Clear local notebook", example: "/clear_chat" },
  ],
};

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
                <motion.div key={i} initial={{ x: -10, opacity: 0 }} animate={{ x: 0, opacity: 1 }} transition={{ delay: i * 0.03 }} className="p-2 rounded-lg hover:bg-white/5 transition-colors">
                  <div className="flex items-start gap-2">
                    <div className="w-4 h-4 rounded bg-[#00E5FF]/10 flex items-center justify-center shrink-0 border border-[#00E5FF]/20 mt-0.5"><span className="text-[8px] font-mono text-[#00E5FF]"></span></div>
                    <div className="flex-1 min-w-0">
                      <code className="text-[10px] font-mono font-bold text-white block">{cmd.name}</code>
                      <p className="text-[8px] font-mono text-[#64748B] mt-0.5 leading-relaxed">{cmd.desc}</p>
                      <div className="mt-1.5 text-[7px] font-mono bg-[#030406] p-1.5 rounded border border-white/5 text-[#8AB4F8]">
                        <span className="text-[#64748B]">ex: </span>{cmd.example}
                      </div>
                    </div>
                  </div>
                </motion.div>
              ))}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
};

// ==========================================
// SPECIAL SYSTEM OVERLAYS & VIEWS
// ==========================================
const TriangulationOverlay = () => {
  return (
    <motion.div
      initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
      className="absolute inset-0 z-50 bg-[#030406]/80 backdrop-blur-md flex items-center justify-center rounded-2xl overflow-hidden"
    >
      <div className="relative w-full h-full max-w-2xl max-h-96 flex items-center justify-center">
        {/* Nodes */}
        <motion.div initial={{ scale: 0 }} animate={{ scale: 1 }} transition={{ delay: 0.2 }} className="absolute top-10 left-20 w-12 h-12 bg-[#00E5FF]/20 rounded-full border border-[#00E5FF]/50 flex items-center justify-center shadow-[0_0_30px_rgba(0,229,255,0.4)] z-10">
          <Database className="w-5 h-5 text-[#00E5FF]" />
          <span className="absolute -bottom-6 text-[9px] font-mono text-[#00E5FF] tracking-widest">CORTEX</span>
        </motion.div>
        <motion.div initial={{ scale: 0 }} animate={{ scale: 1 }} transition={{ delay: 0.4 }} className="absolute bottom-10 left-20 w-12 h-12 bg-[#9B72CB]/20 rounded-full border border-[#9B72CB]/50 flex items-center justify-center shadow-[0_0_30px_rgba(155,114,203,0.4)] z-10">
          <Brain className="w-5 h-5 text-[#9B72CB]" />
          <span className="absolute -bottom-6 text-[9px] font-mono text-[#9B72CB] tracking-widest">BRAIN</span>
        </motion.div>
        <motion.div initial={{ scale: 0 }} animate={{ scale: 1 }} transition={{ delay: 0.6 }} className="absolute top-1/2 right-20 -translate-y-1/2 w-12 h-12 bg-[#8AB4F8]/20 rounded-full border border-[#8AB4F8]/50 flex items-center justify-center shadow-[0_0_30px_rgba(138,180,248,0.4)] z-10">
          <Shield className="w-5 h-5 text-[#8AB4F8]" />
          <span className="absolute -bottom-6 text-[9px] font-mono text-[#8AB4F8] tracking-widest">GOVERNOR</span>
        </motion.div>
        {/* Center Consensus */}
        <motion.div initial={{ scale: 0 }} animate={{ scale: 1 }} transition={{ delay: 0.8 }} className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-20 h-20 bg-white/10 rounded-full border-2 border-white/50 flex items-center justify-center shadow-[0_0_50px_rgba(255,255,255,0.2)] z-20 backdrop-blur-xl">
          <Network className="w-8 h-8 text-white animate-pulse" />
          <span className="absolute -bottom-8 text-[10px] font-mono font-bold text-white tracking-[0.2em]">CONSENSUS</span>
        </motion.div>
        {/* Connecting Lines */}
        <svg className="absolute inset-0 w-full h-full pointer-events-none z-0">
          <motion.line initial={{ pathLength: 0 }} animate={{ pathLength: 1 }} transition={{ delay: 0.3, duration: 0.5 }} x1="calc(50% - 180px)" y1="calc(50% - 80px)" x2="50%" y2="50%" stroke="#00E5FF" strokeWidth="2" strokeDasharray="4 4" className="opacity-50" />
          <motion.line initial={{ pathLength: 0 }} animate={{ pathLength: 1 }} transition={{ delay: 0.5, duration: 0.5 }} x1="calc(50% - 180px)" y1="calc(50% + 80px)" x2="50%" y2="50%" stroke="#9B72CB" strokeWidth="2" strokeDasharray="4 4" className="opacity-50" />
          <motion.line initial={{ pathLength: 0 }} animate={{ pathLength: 1 }} transition={{ delay: 0.7, duration: 0.5 }} x1="calc(50% + 180px)" y1="50%" x2="50%" y2="50%" stroke="#8AB4F8" strokeWidth="2" strokeDasharray="4 4" className="opacity-50" />
        </svg>
        <div className="absolute top-4 left-4 text-[10px] font-mono text-white/50 flex items-center gap-2 uppercase tracking-widest">
          <Activity className="w-3 h-3 text-[#A78BFA]" />
          Triangulation Engine Active
        </div>
      </div>
    </motion.div>
  );
};

const ScannerWorkspace = () => {
  return (
    <div className="flex-1 w-full h-full flex flex-col bg-[#030406]/50 p-6 relative overflow-hidden">
      <div className="mb-4 flex items-center justify-between shrink-0">
        <h3 className="text-[12px] font-mono font-bold tracking-[0.2em] text-[#00E5FF] flex items-center gap-2">
          <Workflow className="w-4 h-4" /> ARCHITECTURAL MAP
        </h3>
        <div className="px-2 py-1 bg-[#00E5FF]/10 border border-[#00E5FF]/30 rounded text-[9px] font-mono text-[#00E5FF] tracking-widest">
          AGAMOTO BRIDGE: CONNECTED
        </div>
      </div>
      <div className="flex-1 border border-white/10 rounded-xl bg-black/40 relative overflow-hidden flex items-center justify-center p-8">
        <div className="absolute inset-0 opacity-10 bg-[radial-gradient(circle_at_center,_#00E5FF_1px,_transparent_1px)] bg-[size:20px_20px]" />
        <div className="w-full max-w-3xl flex justify-between items-center relative z-10">
          {/* Files */}
          <div className="flex flex-col gap-4">
            {[1, 2, 3].map(i => (
              <motion.div key={`file-${i}`} initial={{ x: -20, opacity: 0 }} animate={{ x: 0, opacity: 1 }} transition={{ delay: i * 0.1 }} className="px-4 py-3 bg-[#030406]/80 border border-white/20 rounded-lg flex items-center gap-3 w-40 relative group">
                <FileCode className="w-4 h-4 text-[#8AB4F8]" />
                <span className="text-[10px] font-mono text-white">src/core_{i}.ts</span>
                <div className="absolute right-0 top-1/2 w-2 h-px bg-[#00E5FF] translate-x-full group-hover:w-8 transition-all" />
              </motion.div>
            ))}
          </div>
          {/* AST Processor */}
          <motion.div initial={{ scale: 0.8, opacity: 0 }} animate={{ scale: 1, opacity: 1 }} transition={{ delay: 0.4 }} className="w-32 h-32 rounded-full border-2 border-[#9B72CB]/50 bg-[#9B72CB]/10 flex flex-col items-center justify-center relative shadow-[0_0_40px_rgba(155,114,203,0.2)]">
            <Scan className="w-8 h-8 text-[#9B72CB] mb-2" />
            <span className="text-[8px] font-mono font-bold tracking-widest text-white">AST PARSER</span>
            {/* Connecting lines */}
            <svg className="absolute w-[400px] h-[200px] left-[-150px] top-[-34px] pointer-events-none -z-10">
              <path d="M0,50 C70,50 80,100 150,100" stroke="rgba(0,229,255,0.3)" strokeWidth="1" fill="none" strokeDasharray="4 4" />
              <path d="M0,100 C70,100 80,100 150,100" stroke="rgba(0,229,255,0.3)" strokeWidth="1" fill="none" strokeDasharray="4 4" />
              <path d="M0,150 C70,150 80,100 150,100" stroke="rgba(0,229,255,0.3)" strokeWidth="1" fill="none" strokeDasharray="4 4" />
            </svg>
          </motion.div>
          {/* Hive Memory */}
          <div className="flex flex-col gap-4">
            <motion.div initial={{ x: 20, opacity: 0 }} animate={{ x: 0, opacity: 1 }} transition={{ delay: 0.6 }} className="px-4 py-6 bg-gradient-to-br from-[#00E5FF]/10 to-[#00E5FF]/5 border border-[#00E5FF]/30 rounded-lg flex flex-col items-center gap-3 w-48 shadow-[0_0_20px_rgba(0,229,255,0.1)] relative">
              <div className="absolute left-0 top-1/2 w-16 h-px bg-[#00E5FF]/50 -translate-x-full" />
              <Database className="w-6 h-6 text-[#00E5FF]" />
              <div className="text-center">
                <span className="text-[11px] font-mono font-bold text-white block mb-1">HIVE MEMORY</span>
                <span className="text-[8px] font-mono text-[#00E5FF]">420 NODES / 1.2K EDGES</span>
              </div>
            </motion.div>
          </div>
        </div>
      </div>
    </div>
  );
};

const AppBuilderWorkspace = () => {
  return (
    <div className="flex-1 w-full h-full flex bg-[#030406]">
      {/* File Tree */}
      <div className="w-48 border-r border-white/5 bg-black/40 p-4 flex flex-col gap-2 overflow-y-auto">
        <span className="text-[9px] font-mono font-bold tracking-widest text-[#64748B] uppercase mb-2">EXPLORER</span>
        <div className="flex items-center gap-2 text-[10px] font-mono text-zinc-300 hover:text-white cursor-pointer"><Folder className="w-3 h-3 text-[#8AB4F8]" /> src</div>
        <div className="flex items-center gap-2 text-[10px] font-mono text-zinc-500 hover:text-white cursor-pointer ml-4"><Folder className="w-3 h-3 text-[#8AB4F8]" /> components</div>
        <div className="flex items-center gap-2 text-[10px] font-mono text-zinc-300 hover:text-white cursor-pointer ml-8 bg-white/5 px-2 py-1 rounded"><FileCode className="w-3 h-3 text-[#00E5FF]" /> Button.tsx</div>
        <div className="flex items-center gap-2 text-[10px] font-mono text-zinc-500 hover:text-white cursor-pointer ml-8"><FileCode className="w-3 h-3 text-zinc-500" /> Header.tsx</div>
        <div className="flex items-center gap-2 text-[10px] font-mono text-zinc-500 hover:text-white cursor-pointer ml-4"><FileCode className="w-3 h-3 text-zinc-500" /> index.ts</div>
      </div>
      {/* Editor */}
      <div className="flex-1 flex flex-col min-w-0">
        <div className="h-10 border-b border-white/5 bg-white/[0.02] flex items-center px-4 gap-4">
          <div className="flex items-center gap-2 text-[10px] font-mono text-white border-b-2 border-[#00E5FF] h-full pt-1 px-2">Button.tsx</div>
          <div className="flex items-center gap-2 text-[10px] font-mono text-zinc-500 h-full pt-1 px-2">style.css</div>
        </div>
        <div className="flex-1 p-4 overflow-y-auto font-mono text-[11px] leading-relaxed text-zinc-300 bg-[#030406]/80">
          <div className="text-[#9B72CB]">import</div> React <div className="text-[#9B72CB]">from</div> <span className="text-[#6AAB73]">'react'</span>;<br /><br />
          <div className="text-[#9B72CB]">export const</div> <span className="text-[#8AB4F8]">Button</span> = () {'=>'} {'{'}<br />
          &nbsp;&nbsp;<div className="text-[#9B72CB]">return</div> (<br />
          &nbsp;&nbsp;&nbsp;&nbsp;{'<'}<span className="text-[#00E5FF]">button</span> className=<span className="text-[#6AAB73]">"px-4 py-2 bg-blue-500 text-white rounded"</span>{'>'}<br />
          &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Click Me<br />
          &nbsp;&nbsp;&nbsp;&nbsp;{'</'}<span className="text-[#00E5FF]">button</span>{'>'}<br />
          &nbsp;&nbsp;);<br />
          {'}'};
        </div>
      </div>
      {/* Preview */}
      <div className="w-1/3 border-l border-white/5 bg-black/40 flex flex-col min-w-[250px]">
        <div className="h-10 border-b border-white/5 bg-white/[0.02] flex items-center px-4 justify-between">
          <span className="text-[9px] font-mono font-bold tracking-widest text-[#64748B] uppercase flex items-center gap-2"><MonitorPlay className="w-3 h-3" /> PREVIEW</span>
          <div className="flex gap-1">
            <div className="w-2 h-2 rounded-full bg-red-500/50" />
            <div className="w-2 h-2 rounded-full bg-yellow-500/50" />
            <div className="w-2 h-2 rounded-full bg-green-500/50" />
          </div>
        </div>
        <div className="flex-1 p-4 flex items-center justify-center bg-white/5">
          <button className="px-6 py-2 bg-blue-600 hover:bg-blue-500 text-white rounded-md shadow-lg transition-colors text-sm font-medium">
            Click Me
          </button>
        </div>
      </div>
    </div>
  );
};

// ==========================================
// SOVEREIGN BOOT SEQUENCER
// ==========================================
const SovereignBoot = ({ phase, onComplete }: { phase: number, onComplete: () => void }) => {
  const workers = ['orchestrator', 'filesystem', 'hands', 'sandbox', 'brain', 'pc_hive', 'rez_scanner', 'agamato', 'rezstack', 'appbuilder', 'cortex_mem', 'gov_layer'];
  return (
    <motion.div
      initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
      className="fixed inset-0 z-[100] bg-[#030406] flex flex-col items-center justify-center font-mono selection:bg-[#00E5FF]/30 p-8"
    >
      <div className="absolute inset-0 bg-[radial-gradient(circle_at_center,_#00E5FF_1px,_transparent_1px)] opacity-[0.03] bg-[size:24px_24px] pointer-events-none" />
      <div className="max-w-6xl w-full flex flex-col gap-12 relative z-10">
        <div className="text-center mb-8">
          <motion.div animate={{ rotate: 360 }} transition={{ duration: 10, repeat: Infinity, ease: "linear" }} className="w-16 h-16 rounded-full border border-white/10 border-t-[#00E5FF] border-b-[#9B72CB] mx-auto mb-6 flex items-center justify-center shadow-[0_0_30px_rgba(0,229,255,0.2)]">
            <ZapIcon className="text-white w-6 h-6 animate-pulse" />
          </motion.div>
          <h1 className="text-3xl font-bold text-white tracking-[0.3em] uppercase mb-2">REZHIVE OS</h1>
          <p className="text-[10px] text-[#00E5FF] tracking-widest uppercase">Boot Sequence Initiated  ULTIMATE EDITION v10.7</p>
        </div>
        <div className="grid grid-cols-5 gap-6 h-[300px]">
          {/* Phase 0 */}
          <div className={`border-l border-white/10 pl-4 flex flex-col gap-4 transition-opacity duration-500 ${phase >= 0 ? 'opacity-100' : 'opacity-20'}`}>
            <h2 className="text-[10px] font-bold tracking-widest text-[#64748B] uppercase mb-2">PHASE 0</h2>
            <div className="text-[12px] text-white tracking-widest">Core Memory</div>
            <div className="flex-1 flex flex-col justify-end">
              <div className="flex items-center gap-2 text-[10px] mb-2">
                {phase > 0 ? <CheckCircle2 className="w-3 h-3 text-[#00E5FF]" /> : <Activity className="w-3 h-3 text-zinc-500 animate-pulse" />}
                <span className={phase > 0 ? "text-[#00E5FF]" : "text-zinc-500"}>HiveMemoryBus</span>
              </div>
              <div className="flex items-center gap-2 text-[10px]">
                {phase > 0 ? <CheckCircle2 className="w-3 h-3 text-[#00E5FF]" /> : <Activity className="w-3 h-3 text-zinc-500 animate-pulse" />}
                <span className={phase > 0 ? "text-[#00E5FF]" : "text-zinc-500"}>MetricsCollector</span>
              </div>
            </div>
          </div>
          {/* Phase 1 */}
          <div className={`border-l border-white/10 pl-4 flex flex-col gap-4 transition-opacity duration-500 ${phase >= 1 ? 'opacity-100' : 'opacity-20'}`}>
            <h2 className="text-[10px] font-bold tracking-widest text-[#64748B] uppercase mb-2">PHASE 1</h2>
            <div className="text-[12px] text-white tracking-widest">Constitutional</div>
            <div className="flex-1 flex flex-col justify-end">
              <div className="flex items-center gap-2 text-[10px] mb-2">
                {phase > 1 ? <CheckCircle2 className="w-3 h-3 text-[#9B72CB]" /> : phase === 1 ? <Activity className="w-3 h-3 text-[#9B72CB] animate-pulse" /> : <div className="w-3 h-3 rounded-full border border-zinc-700" />}
                <span className={phase > 1 ? "text-[#9B72CB]" : phase === 1 ? "text-white" : "text-zinc-600"}>Governor</span>
              </div>
              <div className="flex items-center gap-2 text-[10px]">
                {phase > 1 ? <CheckCircle2 className="w-3 h-3 text-[#9B72CB]" /> : phase === 1 ? <Activity className="w-3 h-3 text-[#9B72CB] animate-pulse" /> : <div className="w-3 h-3 rounded-full border border-zinc-700" />}
                <span className={phase > 1 ? "text-[#9B72CB]" : phase === 1 ? "text-white" : "text-zinc-600"}>AgentMemory</span>
              </div>
            </div>
          </div>
          {/* Phase 2 */}
          <div className={`border-l border-white/10 pl-4 flex flex-col gap-4 transition-opacity duration-500 ${phase >= 2 ? 'opacity-100' : 'opacity-20'}`}>
            <h2 className="text-[10px] font-bold tracking-widest text-[#64748B] uppercase mb-2">PHASE 2</h2>
            <div className="text-[12px] text-white tracking-widest">Consensus Engine</div>
            <div className="flex-1 flex flex-col justify-end">
              <div className="flex items-center gap-2 text-[10px]">
                {phase > 2 ? <CheckCircle2 className="w-3 h-3 text-[#8AB4F8]" /> : phase === 2 ? <Network className="w-3 h-3 text-[#8AB4F8] animate-spin" /> : <div className="w-3 h-3 rounded-full border border-zinc-700" />}
                <span className={phase > 2 ? "text-[#8AB4F8]" : phase === 2 ? "text-white" : "text-zinc-600"}>Triangulation</span>
              </div>
            </div>
          </div>
          {/* Phase 3 */}
          <div className={`border-l border-white/10 pl-4 flex flex-col gap-4 transition-opacity duration-500 ${phase >= 3 ? 'opacity-100' : 'opacity-20'}`}>
            <h2 className="text-[10px] font-bold tracking-widest text-[#64748B] uppercase mb-2">PHASE 3</h2>
            <div className="text-[12px] text-white tracking-widest">Workers Init</div>
            <div className="flex-1">
              <div className="grid grid-cols-3 gap-2 mt-4">
                {workers.map((w, i) => (
                  <div key={w} className={`h-6 rounded border flex items-center justify-center text-[7px] font-bold tracking-widest transition-all duration-300 ${phase > 3 ? 'bg-[#00E5FF]/20 border-[#00E5FF]/50 text-[#00E5FF] shadow-[0_0_10px_rgba(0,229,255,0.2)]' : phase === 3 ? 'bg-white/5 border-white/20 text-white animate-pulse delay-[' + (i * 100) + 'ms]' : 'bg-transparent border-white/5 text-zinc-700'}`}>
                    {w.substring(0, 4).toUpperCase()}
                  </div>
                ))}
              </div>
            </div>
          </div>
          {/* Phase 4 */}
          <div className={`border-l border-white/10 pl-4 flex flex-col gap-4 transition-opacity duration-500 ${phase >= 4 ? 'opacity-100' : 'opacity-20'}`}>
            <h2 className="text-[10px] font-bold tracking-widest text-[#64748B] uppercase mb-2">PHASE 4</h2>
            <div className="text-[12px] text-white tracking-widest">Verification</div>
            <div className="flex-1 flex flex-col justify-end">
              <div className="flex flex-col gap-2 bg-black/50 p-3 rounded border border-white/10">
                <div className="flex justify-between items-center text-[9px]">
                  <span className="text-zinc-400">STATUS</span>
                  <span className={phase >= 5 ? "text-[#00E5FF]" : "text-yellow-500 animate-pulse"}>{phase >= 5 ? 'SENTIENT' : 'AWAKENING...'}</span>
                </div>
                <div className="w-full bg-white/5 h-1 rounded overflow-hidden">
                  <div className="h-full bg-[#00E5FF] transition-all duration-1000 ease-out" style={{ width: phase >= 5 ? '100%' : phase === 4 ? '60%' : '0%' }} />
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </motion.div>
  );
};

// ==========================================
// MAIN DASHBOARD COMPONENT - FIXED VERSION
// ==========================================
export default function SovereignDashboard() {
  const [mounted, setMounted] = useState(false);
  const [time, setTime] = useState('');
  const [uptime, setUptime] = useState(0);
  // Boot & System State
  const [bootPhase, setBootPhase] = useState(0);
  const [isBooting, setIsBooting] = useState(true);
  const [kernelStatus, setKernelStatus] = useState<'checking' | 'online' | 'offline'>('checking');
  const [consciousnessLevel, setConsciousnessLevel] = useState<'FORMING' | 'AWAKENING' | 'SENTIENT'>('FORMING');
  const [workerCount, setWorkerCount] = useState(0);
  // Visual Overlays State
  const [showTriangulation, setShowTriangulation] = useState(false);
  const [govScore, setGovScore] = useState(100);
  const [activeCapability, setActiveCapability] = useState('orchestrator');
  const [messages, setMessages] = useState<Message[]>([]);
  const [prompt, setPrompt] = useState('');
  const [isStreaming, setIsStreaming] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
  const [expandedGroup, setExpandedGroup] = useState<string | null>(' SOVEREIGN OS');
  const [suggestions, setSuggestions] = useState<string[]>([]);
  const [showSuggestions, setShowSuggestions] = useState(false);
  const chatEndRef = useRef<HTMLDivElement>(null);
  const suggestionsRef = useRef<HTMLDivElement>(null);
  // Expanded capabilities
  const capabilities = [
    { id: 'orchestrator', name: 'Orchestrator', desc: 'Intent Detection', icon: Network },
    { id: 'brain', name: 'Brain', desc: 'Reasoning', icon: Brain },
    { id: 'scanner', name: 'Scanner', desc: 'Architecture Flow', icon: Scan },
    { id: 'appbuilder', name: 'AppBuilder', desc: 'Integrated IDE', icon: Layout },
    { id: 'techdebt', name: 'TechDebt', desc: 'Code Analysis', icon: Code },
    { id: 'jurisdiction', name: 'Jurisdiction', desc: 'Hardware Trust', icon: Shield },
    { id: 'strategy', name: 'Strategy', desc: 'Evolution', icon: TrendingUp },
    { id: 'backtest', name: 'Backtest', desc: 'Simulation', icon: Activity },
    { id: 'cortex', name: 'Cortex', desc: 'Memory', icon: Database },
    { id: 'constitution', name: 'Constitution', desc: 'Governance', icon: Lock },
  ];
  const allCommands = Object.values(commandGroups).flat().map(cmd => cmd.name);
  // Boot Sequencer Effect
  useEffect(() => {
    if (isBooting) {
      if (bootPhase < 5) {
        const timer = setTimeout(() => setBootPhase(p => p + 1), 1200);
        return () => clearTimeout(timer);
      } else {
        const finishTimer = setTimeout(() => setIsBooting(false), 2000);
        setConsciousnessLevel('SENTIENT');
        return () => clearTimeout(finishTimer);
      }
    }
  }, [bootPhase, isBooting]);
  useEffect(() => {
    setMounted(true);
    const updateTime = () => setTime(new Date().toLocaleTimeString('en-US', { hour12: false }));
    updateTime();
    const clockInterval = setInterval(updateTime, 1000);
    const upInterval = setInterval(() => setUptime(prev => prev + 1), 1000);
    //  SIMPLIFIED fetchSystemState - only uses WORKING endpoints
    const fetchSystemState = async () => {
      try {
        const headers = { 'X-Hive-API-Key': API_KEY };
        //  /health - WORKING
        const healthRes = await fetch(`${API_BASE}/health`, { headers });
        if (healthRes.ok) {
          const healthData = await healthRes.json();
          setKernelStatus('online');
          setWorkerCount(healthData.workers || 32);
                  } else {
          setKernelStatus('offline');
        }
        //  /sce/status - WORKING (optional)
        const sceRes = await fetch(`${API_BASE}/sce/status`, { headers });
        if (sceRes.ok) {
          const sceData = await sceRes.json();
          console.log('SCE Protocol:', sceData.protocol_version);
        }
      } catch (err) {
        setKernelStatus('offline');
      }
    };
    if (!isBooting) {
      fetchSystemState();
      const pollInterval = setInterval(fetchSystemState, 10000); // Poll every 10 seconds
      return () => clearInterval(pollInterval);
    }
    const handleClickOutside = (event: MouseEvent) => {
      if (suggestionsRef.current && !suggestionsRef.current.contains(event.target as Node)) {
        setShowSuggestions(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => {
      clearInterval(clockInterval);
      clearInterval(upInterval);
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, [isBooting]);
  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isStreaming, activeCapability]);
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
  //  UPDATED handleTransmit with ONLY /sce/process endpoint
  const handleTransmit = async () => {
    if (!prompt.trim() || isStreaming) return;
    const userText = prompt;
    setPrompt('');
    setIsStreaming(true);
    setShowSuggestions(false);
    if (userText.includes('backtest') || userText.includes('strategy')) {
      setShowTriangulation(true);
      setTimeout(() => setShowTriangulation(false), 4000);
    }
    const timeNow = new Date().toLocaleTimeString('en-US', { hour12: false });
    setMessages(prev => [...prev, {
      id: Date.now().toString(),
      role: 'user',
      content: userText,
      timestamp: timeNow
    }]);
    try {
      //  REMOVED constitution check - endpoint doesn't exist
      // Just proceed directly to worker
      const assistantId = Date.now().toString();
      setMessages(prev => [...prev, {
        id: assistantId,
        role: 'assistant',
        content: '',
        timestamp: new Date().toLocaleTimeString('en-US', { hour12: false })
      }]);
      let worker = activeCapability === 'orchestrator' ? 'auto' : activeCapability;
      if (userText.startsWith('/techdebt')) worker = 'techdebt';
      else if (userText.startsWith('/jurisdiction')) worker = 'jurisdiction';
      else if (userText.startsWith('/strategy')) worker = 'strategy';
      else if (userText.startsWith('/backtest')) worker = 'backtest';
      else if (userText.startsWith('/trade') || userText.includes('buy') || userText.includes('sell')) worker = 'reztrader';
      else if (userText.startsWith('/pc') || userText.includes('cpu') || userText.includes('ram')) worker = 'pc_monitor';
      //  Use /sce/process
      const processRes = await fetch(`${API_BASE}/sce/process`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-Hive-API-Key': API_KEY
        },
        body: JSON.stringify({
          task: userText,
          worker: worker === 'auto' ? 'brain' : worker
        })
      });
      if (!processRes.ok) {
        throw new Error(`HTTP ${processRes.status}`);
      }
      const blueprint = await processRes.json();
      // Extract content from blueprint
      const result = blueprint.execution?.result || JSON.stringify(blueprint, null, 2);
      const driftLock = blueprint.master_drift_lock;
      const narrative = blueprint.dna?.narrative || [];
      // Update message with result and drift lock
      setMessages(prev => prev.map(msg =>
        msg.id === assistantId ? {
          ...msg,
          content: result,
          narrative: narrative,
          driftLock: driftLock
        } : msg
      ));
    } catch (error) {
      console.error('Transmit error:', error);
      setMessages(prev => [...prev, {
        id: Date.now().toString(),
        role: 'system',
        content: ` Connection Failed: ${error instanceof Error ? error.message : 'Unknown error'}`,
        timestamp: new Date().toLocaleTimeString('en-US', { hour12: false })
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
  if (!mounted) return <div className="bg-[#030406] h-screen w-screen" />;
  const totalGlossaryCommands = Object.keys(commandGroups).reduce((acc, group) => acc + commandGroups[group as keyof typeof commandGroups].length, 0);
  return (
    <div className="h-screen w-screen bg-[#030406] text-[#f5f5f7] font-sans overflow-hidden flex flex-col selection:bg-[#00E5FF]/30 selection:text-white relative p-4 gap-4 z-0">
      <AnimatePresence>
        {isBooting && <SovereignBoot phase={bootPhase} onComplete={() => setIsBooting(false)} />}
      </AnimatePresence>
      <div className="absolute inset-0 opacity-20 pointer-events-none mix-blend-screen" style={{ backgroundImage: 'radial-gradient(circle at 20% 50%, #00E5FF 0%, transparent 40%), radial-gradient(circle at 80% 30%, #9B72CB 0%, transparent 40%)', filter: 'blur(80px)' }} />
      <div className="absolute inset-0 bg-[url('https://grainy-gradients.vercel.app/noise.svg')] opacity-[0.03] pointer-events-none mix-blend-overlay" />
      <motion.header initial={{ y: -50, opacity: 0 }} animate={{ y: 0, opacity: 1 }} transition={springSoft} className="relative z-10 h-14 bg-black/40 backdrop-blur-xl border border-white/10 rounded-2xl flex items-center justify-between px-4 shadow-lg shrink-0">
        <div className="flex items-center gap-6">
          <div className="flex items-center gap-3">
            <div className="relative w-8 h-8 rounded-lg bg-gradient-to-br from-[#00E5FF] to-[#9B72CB] p-[1px] shadow-[0_0_20px_rgba(0,229,255,0.3)]">
              <div className="w-full h-full bg-black/80 rounded-md flex items-center justify-center backdrop-blur-md"><Zap className="w-4 h-4 text-white" /></div>
            </div>
            <div className="flex flex-col">
              <span className="text-[13px] font-bold tracking-widest text-white uppercase flex items-center gap-2">
                SOVEREIGN OS
                <span className={`px-1.5 py-0.5 rounded-sm border text-[8px] font-mono tracking-widest ${consciousnessLevel === 'SENTIENT' ? 'bg-gradient-to-r from-[#9B72CB]/20 to-[#00E5FF]/20 border-white/10 text-[#00E5FF] drop-shadow-[0_0_5px_#00E5FF]' : 'bg-yellow-500/10 border-yellow-500/30 text-yellow-500'}`}>
                  {consciousnessLevel}
                </span>
              </span>
              <span className="text-[9px] text-[#8AB4F8] font-mono tracking-wider">THE SYMBIOTE CONSCIOUSNESS</span>
            </div>
          </div>
        </div>
        <div className="flex items-center gap-4">
          <div className={`hidden md:flex items-center gap-2 px-3 py-1 rounded-md border backdrop-blur-md transition-colors ${kernelStatus === 'online' ? 'bg-[#00E5FF]/10 border-[#00E5FF]/30' : 'bg-[#FF2A2A]/10 border-[#FF2A2A]/30'}`}>
            <div className={`w-1.5 h-1.5 rounded-full ${kernelStatus === 'online' ? 'bg-[#00E5FF] animate-pulse shadow-[0_0_8px_#00E5FF]' : 'bg-[#FF2A2A] shadow-[0_0_8px_#FF2A2A]'}`} />
            <span className={`text-[9px] font-mono tracking-widest uppercase ${kernelStatus === 'online' ? 'text-[#00E5FF]' : 'text-[#FF2A2A]'}`}>KERNEL {kernelStatus.toUpperCase()}</span>
          </div>
          <div className="px-3 py-1 rounded-md bg-black/50 border border-white/5 text-[#00E5FF] text-[10px] font-mono drop-shadow-[0_0_8px_#00E5FF] hidden lg:block">{time} <span className="text-[#64748B]">MNL</span></div>
          {/*  Added worker count */}
          <div className="px-3 py-1 rounded-md bg-[#9B72CB]/10 border border-[#9B72CB]/30 text-[#9B72CB] text-[9px] font-mono">
            {workerCount} WORKERS
          </div>
        </div>
      </motion.header>
      <main className="relative z-10 flex-1 flex gap-4 min-h-0">
        <motion.div {...fadeUp} transition={{ ...springSoft, delay: 0.1 }} className="w-[280px] flex flex-col gap-4 shrink-0 min-h-0">
          <div className="flex-1 bg-black/40 backdrop-blur-xl border border-white/10 rounded-2xl p-4 flex flex-col shadow-lg min-h-0">
            <h2 className="text-[10px] font-mono tracking-[0.2em] font-bold text-[#64748B] uppercase flex items-center gap-2 mb-4"><Cpu className="w-3 h-3 text-[#00E5FF]" /> CAPABILITIES</h2>
            <div className="flex-1 overflow-y-auto custom-scrollbar pr-1 flex flex-col gap-2">
              {capabilities.map((cap) => {
                const isActive = activeCapability === cap.id;
                return (
                  <button key={cap.id} onClick={() => setActiveCapability(cap.id)} className={`w-full flex items-center gap-3 p-3 rounded-xl transition-all group relative text-left border shrink-0 ${isActive ? 'bg-[#00E5FF]/10 border-[#00E5FF]/30 shadow-[0_0_15px_rgba(0,229,255,0.1)]' : 'bg-[#030406]/80 border-white/5 hover:bg-white/[0.02] hover:border-white/10'}`}>
                    <div className={`w-8 h-8 rounded-lg flex items-center justify-center shrink-0 ${isActive ? 'bg-[#00E5FF]/20 text-[#00E5FF]' : 'text-zinc-500 group-hover:text-zinc-300'}`}><cap.icon className="w-4 h-4" /></div>
                    <div className="flex flex-col items-start min-w-0">
                      <span className={`text-[11px] font-bold tracking-wider truncate w-full ${isActive ? 'text-white' : 'text-zinc-400 group-hover:text-white'}`}>{cap.name}</span>
                      <span className="text-[9px] font-mono text-[#64748B] mt-0.5 truncate w-full">{cap.desc}</span>
                    </div>
                    {isActive && <div className="absolute right-3 w-1.5 h-1.5 rounded-full bg-[#00E5FF] shadow-[0_0_8px_#00E5FF]" />}
                  </button>
                );
              })}
            </div>
          </div>
        </motion.div>
        <motion.div {...fadeUp} transition={{ ...springSoft, delay: 0.2 }} className="flex-1 bg-black/40 backdrop-blur-xl border border-white/10 rounded-2xl flex flex-col relative overflow-hidden shadow-lg min-w-0 min-h-0">
          <AnimatePresence>
            {showTriangulation && <TriangulationOverlay />}
          </AnimatePresence>
          <div className="h-12 border-b border-white/5 flex items-center justify-between px-4 shrink-0 bg-white/[0.01]">
            <div className="flex items-center gap-2">
              <Terminal className="w-3.5 h-3.5 text-[#00E5FF]" />
              <span className="text-[10px] font-mono tracking-[0.2em] font-bold text-white uppercase">{capabilities.find(c => c.id === activeCapability)?.name || 'Terminal'}</span>
            </div>
            <div className="flex items-center gap-4">
              <span className="text-[9px] font-mono text-zinc-500 tracking-wider">ENGINE: <span className="text-[#A78BFA]">SCE v1.0.0</span></span>
            </div>
          </div>
          <div className="flex-1 overflow-hidden flex flex-col relative bg-[#030406]/50">
            {activeCapability === 'scanner' ? (
              <ScannerWorkspace />
            ) : activeCapability === 'appbuilder' ? (
              <AppBuilderWorkspace />
            ) : (
              <div className="flex-1 overflow-y-auto custom-scrollbar p-6 flex flex-col">
                {messages.length === 0 ? (
                  <div className="flex-1 flex flex-col items-center justify-center relative">
                    <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="flex flex-col items-center w-full max-w-2xl">
                      <div className="relative w-24 h-24 mb-8 flex items-center justify-center">
                        <div className="absolute w-32 h-32 bg-[#00E5FF]/10 blur-2xl rounded-full" />
                        <motion.div animate={{ rotate: 360 }} transition={{ duration: 20, repeat: Infinity, ease: "linear" }} className="absolute w-28 h-28 rounded-full border border-white/10 border-t-[#00E5FF] border-b-[#9B72CB] opacity-50" />
                        <div className="absolute w-14 h-14 rounded-full bg-gradient-to-br from-[#00E5FF]/20 to-[#9B72CB]/20 shadow-[0_0_30px_rgba(0,229,255,0.3)] flex items-center justify-center backdrop-blur-md border border-white/10"><ZapIcon className="text-white w-6 h-6" /></div>
                      </div>
                      <h1 className="text-2xl font-bold text-white mb-3 tracking-wide">The Hive Awaits</h1>
                      <p className="text-[11px] font-mono text-[#64748B] mb-12 text-center uppercase tracking-widest leading-relaxed">
                        /pc status  /trade buy BTC 1000  /scan /app /strategy
                      </p>
                    </motion.div>
                  </div>
                ) : (
                  <div className="w-full max-w-4xl mx-auto space-y-6 pb-4">
                    {messages.map((msg) => (
                      <motion.div key={msg.id} initial={{ opacity: 0, y: 5 }} animate={{ opacity: 1, y: 0 }} className={`flex gap-3 ${msg.role === 'user' ? 'flex-row-reverse' : ''}`}>
                        <div className={`w-6 h-6 rounded flex items-center justify-center shrink-0 border mt-1 ${msg.role === 'user' ? 'bg-white/5 border-white/10' : 'bg-[#00E5FF]/10 border-[#00E5FF]/30'}`}>
                          {msg.role === 'user' ? <User className="w-3 h-3 text-[#64748B]" /> : <Bot className="w-3 h-3 text-[#00E5FF]" />}
                        </div>
                        <div className={`flex flex-col max-w-[85%] w-full ${msg.role === 'user' ? 'items-end' : 'items-start'}`}>
                          {msg.role === 'user' ? (
                            <div className="p-3 rounded-xl text-[11px] leading-relaxed whitespace-pre-wrap font-mono tracking-wide bg-white/5 text-[#f5f5f7] border border-white/10 rounded-tr-sm">
                              {msg.content}
                              <div className="text-[7px] text-[#64748B] mt-2 text-right">{msg.timestamp}</div>
                            </div>
                          ) : (
                            <div className="w-full">
                              {/* P2 DNA Narrative Steps */}
                              {msg.narrative && msg.narrative.length > 0 && (
                                <div className="mb-2 p-2 bg-purple-500/5 border border-purple-500/20 rounded-lg">
                                  <div className="text-[8px] font-mono text-purple-400 mb-1"> REASONING</div>
                                  {msg.narrative.map((step, i) => (
                                    <div key={i} className="text-[9px] font-mono text-zinc-400 italic">"{step}"</div>
                                  ))}
                                </div>
                              )}
                              <SovereignMessage
                                content={msg.content}
                                role={msg.role}
                                isStreaming={isStreaming && msg.id === messages[messages.length - 1]?.id}
                              />
                              <div className="flex items-center justify-between mt-2">
                                <div className="text-[7px] font-mono text-[#64748B]">{msg.timestamp}</div>
                                {/* CRYPTOGRAPHIC PROOF BADGE */}
                                {msg.driftLock && (
                                  <div className="flex items-center gap-1.5 px-2 py-0.5 rounded border border-[#00e676]/30 bg-[#00e676]/10">
                                    <ShieldCheck className="w-3 h-3 text-[#00e676]" />
                                    <span className="text-[8px] font-mono font-bold text-[#00e676]">
                                      SCE: {msg.driftLock.substring(0, 8)}...
                                    </span>
                                  </div>
                                )}
                              </div>
                            </div>
                          )}
                        </div>
                      </motion.div>
                    ))}
                    <div ref={chatEndRef} />
                  </div>
                )}
              </div>
            )}
          </div>
          <div className="p-4 bg-black/40 border-t border-white/5 shrink-0 z-10 relative">
            <div className="w-full max-w-4xl mx-auto flex items-center gap-4">
              <div className="flex flex-col items-center justify-center shrink-0 w-12 group relative">
                <svg viewBox="0 0 36 36" className="w-10 h-10 transform -rotate-90">
                  <path d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831" fill="none" stroke="rgba(255,255,255,0.1)" strokeWidth="3" />
                  <path d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831" fill="none" stroke={govScore > 80 ? '#00E5FF' : govScore > 50 ? '#9B72CB' : '#FF2A2A'} strokeWidth="3" strokeDasharray={`${govScore}, 100`} className="transition-all duration-1000" />
                </svg>
                <div className="absolute inset-0 flex items-center justify-center text-[8px] font-mono font-bold text-white">{govScore}</div>
                <div className="absolute bottom-full mb-2 bg-black/90 text-[9px] text-[#64748B] px-2 py-1 rounded border border-white/10 opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap">Gov Score</div>
              </div>
              <div className="flex-1 bg-[#030406]/80 border border-white/10 rounded-xl flex flex-col overflow-hidden focus-within:border-[#00E5FF]/50 transition-colors relative">
                <textarea
                  value={prompt}
                  onChange={handleInputChange}
                  onKeyDown={handleKeyDown}
                  disabled={kernelStatus !== 'online'}
                  placeholder={kernelStatus === 'online' ? "Execute command or send intent..." : "Awaiting Kernel..."}
                  className="w-full bg-transparent p-4 text-[11px] text-white placeholder:text-[#64748B] outline-none resize-none min-h-[60px] font-mono disabled:opacity-50"
                />
                {showSuggestions && suggestions.length > 0 && (
                  <div ref={suggestionsRef} className="absolute bottom-full left-0 right-0 mb-2 bg-black/90 border border-white/10 rounded-lg p-2 shadow-2xl">
                    {suggestions.map((suggestion, i) => (
                      <div
                        key={i}
                        onClick={() => handleSuggestionClick(suggestion)}
                        className="px-3 py-2 hover:bg-white/10 cursor-pointer text-[10px] font-mono text-[#00E5FF] rounded transition-colors"
                      >
                        {suggestion}
                      </div>
                    ))}
                  </div>
                )}
                <div className="flex items-center justify-between p-2 border-t border-white/5 bg-white/[0.02]">
                  <div className="flex items-center gap-3 px-2">
                    <button className="flex items-center gap-1.5 text-[9px] font-mono tracking-widest text-[#64748B] uppercase hover:text-[#00E5FF] transition-colors"><Paperclip className="w-3 h-3" /> Attach</button>
                    <div className="w-px h-3 bg-white/10" /><span className="text-[8px] font-mono tracking-widest text-zinc-600 uppercase">Shift + Enter</span>
                  </div>
                  <button onClick={handleTransmit} disabled={!prompt.trim() || isStreaming || kernelStatus !== 'online'} className={`px-4 py-1.5 rounded text-[9px] font-mono font-bold tracking-widest uppercase transition-all ${prompt.trim() && kernelStatus === 'online' && !isStreaming ? 'bg-[#00E5FF]/10 text-[#00E5FF] border border-[#00E5FF]/30 shadow-[0_0_10px_rgba(0,229,255,0.2)] hover:bg-[#00E5FF]/20' : 'bg-white/5 text-zinc-500 cursor-not-allowed border border-transparent'}`}>
                    {isStreaming ? '...' : 'EXECUTE'}
                  </button>
                </div>
              </div>
            </div>
          </div>
        </motion.div>
        <motion.div {...fadeUp} transition={{ ...springSoft, delay: 0.3 }} className="w-[320px] flex flex-col gap-4 shrink-0 min-h-0">
          <div className="flex-1 bg-black/40 backdrop-blur-xl border border-white/10 rounded-2xl p-4 flex flex-col shadow-lg min-h-0">
            <div className="flex justify-between items-center mb-3 shrink-0 border-b border-white/5 pb-2">
              <div className="flex items-center gap-2">
                <BookOpen className="w-3.5 h-3.5 text-[#00E5FF]" />
                <span className="text-[10px] font-mono font-bold tracking-[0.2em] text-[#00E5FF] uppercase">GLOSSARY</span>
              </div>
              <span className="text-[8px] font-mono tracking-widest px-2 py-0.5 rounded bg-white/5 text-zinc-400 border border-white/10">{totalGlossaryCommands} CMDS</span>
            </div>
            <div className="relative mb-3 shrink-0">
              <Search className="w-3 h-3 absolute left-2.5 top-2.5 text-[#64748B]" />
              <input type="text" placeholder="Search commands..." value={searchTerm} onChange={(e) => setSearchTerm(e.target.value)} className="w-full bg-[#030406]/80 border border-white/10 rounded-lg py-2 pl-8 pr-3 text-[10px] text-white placeholder:text-[#64748B] outline-none focus:border-[#00E5FF]/50 transition-all font-mono" />
            </div>
            <div className="flex-1 overflow-y-auto custom-scrollbar pr-1 flex flex-col">
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
        </motion.div>
      </main>
      <style dangerouslySetInnerHTML={{ __html: `
        .custom-scrollbar::-webkit-scrollbar { width: 4px; }
        .custom-scrollbar::-webkit-scrollbar-track { background: transparent; }
        .custom-scrollbar::-webkit-scrollbar-thumb { background: rgba(255,255,255,0.1); border-radius: 4px; }
        .custom-scrollbar::-webkit-scrollbar-thumb:hover { background: rgba(255,255,255,0.2); }
      `}} />
    </div>
  );
}
