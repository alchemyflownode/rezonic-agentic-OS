'use client';

import React, { useState, useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { io, Socket } from 'socket.io-client';
import {
  Zap, ChevronRight, Lock, Activity, BarChart2, ShieldCheck,
  Terminal, Play, Square, Settings, Cpu, Clock, TrendingUp, TrendingDown,
  Send, Bot, User, BookOpen, Brain, MessageSquare, Code, Upload, X, AlertCircle,
  Gauge, Network, Database, GitBranch, Layers, Cpu as CpuIcon
} from 'lucide-react';
import { BotHiveModal } from '@/components/BotHiveModal';

// --- Configuration ---
const API_KEY = "rez-hive-admin-key-2026";
const API_BASE = "http://localhost:8002";

type TradingMode = 'manual' | 'ai' | 'hybrid';

interface MarketPair {
  symbol: string;
  price: number;
  change: number;
  volume: string;
}

interface WorkerInfo {
  name: string;
  path: string;
  loaded: number;
  module: string;
  metrics?: {
    calls: number;
    errors: number;
    avg_duration: number;
  };
}

interface SCEStats {
  total_events: number;
  chain_integrity: boolean;
  genesis_hash: string;
  latest_hash: string;
  event_counts: Record<string, number>;
}

interface ChatMessage {
  id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  narrative?: string[];
  driftLock?: string;
  timestamp: string;
  worker?: string;
  confidence?: number;
}

// Default Bot Template
const DEFAULT_BOT_CODE = `class MeanReversionBot:
    def on_market_tick(self, market_data, context):
        btc_prices = [m['btcPrice'] for m in market_data if 'btcPrice' in m]
        if len(btc_prices) < 2:
            return None
        avg = sum(btc_prices) / len(btc_prices)
        current = btc_prices[-1]
        if current < avg * 0.99:
            return {'action': 'BUY', 'symbol': 'BTC/PHP', 'amount': 500}
        elif current > avg * 1.01:
            return {'action': 'SELL', 'symbol': 'BTC/PHP', 'amount': 500}
        return None
`;

// ==========================================
// WORKER METRICS COMPONENT
// ==========================================
const WorkerMetrics = ({ workers }: { workers: Record<string, WorkerInfo> }) => {
  const workerList = Object.entries(workers).slice(0, 5);
  const totalCalls = Object.values(workers).reduce((sum, w) => sum + (w.metrics?.calls || 0), 0);
  
  return (
    <div className="bg-black/30 p-2 rounded-lg border border-white/5">
      <div className="flex items-center justify-between mb-2">
        <span className="text-[8px] font-mono text-[#9B72CB] flex items-center gap-1">
          <CpuIcon className="w-3 h-3" /> ACTIVE WORKERS
        </span>
        <span className="text-[8px] font-mono text-white">{Object.keys(workers).length}</span>
      </div>
      <div className="space-y-1">
        {workerList.map(([name, info]) => (
          <div key={name} className="flex items-center justify-between text-[7px] font-mono">
            <div className="flex items-center gap-1">
              <div className="w-1 h-1 rounded-full bg-[#00E5FF]" />
              <span className="text-zinc-400 truncate max-w-[80px]">{name}</span>
            </div>
            <div className="flex items-center gap-2">
              <span className="text-[#00E5FF]">{info.metrics?.calls || 0}</span>
              <span className={info.metrics?.errors ? 'text-[#ff0055]' : 'text-zinc-600'}>
                {info.metrics?.errors || 0}
              </span>
            </div>
          </div>
        ))}
        {Object.keys(workers).length > 5 && (
          <div className="text-center text-[6px] font-mono text-zinc-600">
            +{Object.keys(workers).length - 5} more
          </div>
        )}
      </div>
      <div className="mt-2 pt-2 border-t border-white/5 flex justify-between text-[7px] font-mono">
        <span className="text-zinc-500">Total Calls</span>
        <span className="text-white">{totalCalls}</span>
      </div>
    </div>
  );
};

// ==========================================
// SCE METRICS COMPONENT
// ==========================================
const SCEMetrics = ({ stats, blueprints }: { stats: SCEStats; blueprints: string[] }) => {
  return (
    <div className="bg-black/30 p-2 rounded-lg border border-white/5">
      <div className="flex items-center justify-between mb-2">
        <span className="text-[8px] font-mono text-[#00E5FF] flex items-center gap-1">
          <GitBranch className="w-3 h-3" /> SCE PROTOCOL
        </span>
        <span className={`text-[6px] px-1 py-0.5 rounded ${
          stats.chain_integrity 
            ? 'bg-[#00e676]/10 text-[#00e676] border border-[#00e676]/20' 
            : 'bg-[#ff0055]/10 text-[#ff0055] border border-[#ff0055]/20'
        }`}>
          {stats.chain_integrity ? 'VERIFIED' : 'BROKEN'}
        </span>
      </div>
      <div className="grid grid-cols-2 gap-1 mb-2">
        <div>
          <span className="text-[6px] font-mono text-zinc-500">EVENTS</span>
          <div className="text-[9px] font-bold text-white">{stats.total_events}</div>
        </div>
        <div>
          <span className="text-[6px] font-mono text-zinc-500">LATEST</span>
          <div className="text-[6px] font-mono text-[#9B72CB] truncate">{stats.latest_hash?.substring(0, 8)}...</div>
        </div>
      </div>
      {blueprints.length > 0 && (
        <div className="mt-1">
          <span className="text-[6px] font-mono text-zinc-500">RECENT BLUEPRINTS</span>
          <div className="flex flex-wrap gap-1 mt-1">
            {blueprints.slice(0, 3).map((lock, i) => (
              <div key={i} className="text-[5px] font-mono bg-[#00E5FF]/10 px-1 py-0.5 rounded border border-[#00E5FF]/20 text-[#00E5FF]">
                {lock.substring(0, 4)}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

// ==========================================
// MAIN APEX TRADER COMPONENT
// ==========================================
export default function ApexSleekTrader() {
  const [mounted, setMounted] = useState(false);
  const [socket, setSocket] = useState<Socket | null>(null);
  const [kernelConnected, setKernelConnected] = useState(false);
  const [time, setTime] = useState('');
  
  // --- System State ---
  const [workers, setWorkers] = useState<Record<string, WorkerInfo>>({});
  const [sceStats, setSceStats] = useState<SCEStats>({
    total_events: 0,
    chain_integrity: true,
    genesis_hash: '',
    latest_hash: '',
    event_counts: {}
  });
  const [recentBlueprints, setRecentBlueprints] = useState<string[]>([]);
  
  // --- UI State ---
  const [tradingMode, setTradingMode] = useState<TradingMode>('hybrid');
  const [botActive, setBotActive] = useState(false);
  const [balance, setBalance] = useState(1245678);
  const [dailyPnL, setDailyPnL] = useState(23450);
  const [pairs, setPairs] = useState<MarketPair[]>([
    { symbol: 'BTC/PHP', price: 4524067, change: 2.46, volume: '1.2B' },
    { symbol: 'ETH/PHP', price: 189430, change: -1.21, volume: '890M' },
    { symbol: 'SOL/PHP', price: 8450, change: 5.68, volume: '450M' }
  ]);
  const [selectedPair, setSelectedPair] = useState('BTC/PHP');
  const [tradeAmount, setTradeAmount] = useState('');
  
  const [marketLock, setMarketLock] = useState<string>('--');
  
  const [positions, setPositions] = useState<any[]>([
    { id: '1', pair: 'BTC/PHP', pnl: 2.45, amount: 0.15, entry_price: 4500000, current_price: 4610250 }
  ]);
  
  const [activeStrategies, setActiveStrategies] = useState<any[]>([
    { name: 'Momentum', winRate: 67.5, trades: 142, active: true, color: '#00E5FF', worker: 'MomentumWorker' },
    { name: 'Mean Reversion', winRate: 58.2, trades: 98, active: true, color: '#9B72CB', worker: 'ReversionWorker' },
    { name: 'Grid Trading', winRate: 52.8, trades: 215, active: false, color: '#ff0055', worker: 'GridWorker' },
    { name: 'Scalping', winRate: 61.3, trades: 347, active: true, color: '#00e676', worker: 'ScalpingWorker' },
  ]);
  
  const [selectedStrategy, setSelectedStrategy] = useState<string>('Momentum');
  const [aiInsights, setAiInsights] = useState({ winRate: 94.2, maxDrawdown: 0.15 });
  const [botLogs, setBotLogs] = useState<{ id: string, text: string, time: string, worker?: string, driftLock?: string }[]>([
    { id: '1', text: "Phoenix Kernel v13.3.0 online. 56 workers loaded.", time: new Date().toLocaleTimeString() }
  ]);
  
  // Chat State
  const [chatMessages, setChatMessages] = useState<ChatMessage[]>([
    {
      id: 'welcome',
      role: 'assistant',
      content: '👋 Welcome to Apex Trader! 56 workers online. Ask me about markets, strategies, or use /commands.',
      timestamp: new Date().toLocaleTimeString()
    }
  ]);
  const [chatInput, setChatInput] = useState('');
  const [isChatStreaming, setIsChatStreaming] = useState(false);
  const [chatSuggestions, setChatSuggestions] = useState<string[]>([]);
  const [showChatSuggestions, setShowChatSuggestions] = useState(false);
  const [showBotHive, setShowBotHive] = useState(false);
  
  const logEndRef = useRef<HTMLDivElement>(null);
  const chatEndRef = useRef<HTMLDivElement>(null);
  const chatInputRef = useRef<HTMLTextAreaElement>(null);
  const chatSuggestionsRef = useRef<HTMLDivElement>(null);
  
  const chatCommands = [
    "/help", "/pc status", "/trade buy BTC 1000", "/trade sell ETH 500",
    "/strategy list", "/backtest run", "/ai status", "/health",
    "/workers", "/events stats", "/memory search", "/constitution evaluate"
  ];

  // Fetch system data
  const fetchSystemData = async () => {
    try {
      // Workers from /workers/list
      const workersRes = await fetch(`${API_BASE}/workers/list`, {
        headers: { 'X-Hive-API-Key': API_KEY }
      });
      if (workersRes.ok) {
        const data = await workersRes.json();
        setWorkers(data.loaded?.reduce((acc: any, name: string) => {
          acc[name] = { name, module: 'builtin', metrics: { calls: 0, errors: 0 } };
          return acc;
        }, {}) || {});
      }

      // SCE Stats from /events/stats
      const statsRes = await fetch(`${API_BASE}/events/stats`, {
        headers: { 'X-Hive-API-Key': API_KEY }
      });
      if (statsRes.ok) {
        const data = await statsRes.json();
        setSceStats(data);
      }

      // Blueprints from /memory/blueprints
      const blueprintsRes = await fetch(`${API_BASE}/memory/blueprints`, {
        headers: { 'X-Hive-API-Key': API_KEY }
      });
      if (blueprintsRes.ok) {
        const data = await blueprintsRes.json();
        setRecentBlueprints(data.blueprints || []);
      }
    } catch (err) {
      console.error('Failed to fetch system data:', err);
    }
  };

  useEffect(() => {
    setMounted(true);
    
    fetchSystemData();
    const refreshInterval = setInterval(fetchSystemData, 30000);

    const timeInterval = setInterval(() => {
      setTime(new Date().toLocaleTimeString('en-US', { hour12: false }) + ' UTC');
    }, 1000);

    // WebSocket with proper path for Phoenix Kernel
    const newSocket = io(API_BASE, {
      path: '/ws',
      transports: ['websocket'],
      auth: { token: API_KEY },
      reconnection: true,
      reconnectionAttempts: 5,
      reconnectionDelay: 1000,
    });

    setSocket(newSocket);

    newSocket.on('connect', () => {
      console.log('✅ Socket Connected:', newSocket.id);
      setKernelConnected(true);
      appendLog("Connected to Phoenix Neural Engine.");
    });

    newSocket.on('connect_error', (err) => {
      console.error('❌ Socket Connection Error:', err.message);
      setKernelConnected(false);
      appendLog(`Connection Failed: ${err.message}`);
    });

    newSocket.on('disconnect', (reason) => {
      console.log('🔌 Socket Disconnected:', reason);
      setKernelConnected(false);
      appendLog(`Lost connection: ${reason}`);
    });

    newSocket.on('marketUpdate', (data: any) => {
      if (data.drift_lock) setMarketLock(data.drift_lock);
    });

    newSocket.on('trade_result', (res) => {
      if (res.status === 'AUTHORIZED') {
        appendLog(`✅ Trade Executed. Lock: ${res.drift_lock?.substring(0, 8)}`);
        const profit = Math.floor(Math.random() * 500) + 100;
        setDailyPnL(prev => prev + profit);
        setBalance(prev => prev + profit);
      } else {
        appendLog(`❌ Trade Rejected: ${res.error}`);
      }
    });

    const handleClickOutside = (event: MouseEvent) => {
      if (chatSuggestionsRef.current && !chatSuggestionsRef.current.contains(event.target as Node)) {
        setShowChatSuggestions(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);

    return () => {
      clearInterval(timeInterval);
      clearInterval(refreshInterval);
      newSocket.disconnect();
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, []);

  useEffect(() => {
    logEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [botLogs]);

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [chatMessages, isChatStreaming]);

  const appendLog = (text: string, worker?: string, driftLock?: string) => {
    setBotLogs(prev => [...prev.slice(-20), {
      id: Date.now().toString() + Math.random(),
      text,
      time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' }),
      worker,
      driftLock
    }]);
  };

  const handleManualTrade = (type: 'buy' | 'sell') => {
    if (!socket || !kernelConnected) {
      appendLog("Cannot execute: Kernel Offline.");
      return;
    }
    const amount = parseFloat(tradeAmount) || 0;
    if (amount <= 0) return;
    appendLog(`Initiating Manual ${type.toUpperCase()}...`);
    socket.emit('execute_trade', {
      pair: selectedPair,
      amount: amount,
      command: `MANUAL_${type.toUpperCase()}`
    });
    setTradeAmount('');
  };

  const toggleBot = () => {
    const newState = !botActive;
    setBotActive(newState);
    appendLog(newState ? "Zero Drift Auto-Execution Engaged." : "Bot Deactivated. Returning to Manual.");
  };

  const handleChatInputChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    const value = e.target.value;
    setChatInput(value);
    if (value.length > 0) {
      const filtered = chatCommands.filter(cmd =>
        cmd.toLowerCase().startsWith(value.toLowerCase())
      );
      setChatSuggestions(filtered);
      setShowChatSuggestions(filtered.length > 0);
    } else {
      setChatSuggestions([]);
      setShowChatSuggestions(false);
    }
  };

  const handleChatSuggestionClick = (suggestion: string) => {
    setChatInput(suggestion);
    setShowChatSuggestions(false);
    chatInputRef.current?.focus();
  };

  const handleChatKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendChat();
    }
  };

  const handleSendChat = async () => {
    if (!chatInput.trim() || isChatStreaming || !kernelConnected) return;
    const userText = chatInput;
    setChatInput('');
    setShowChatSuggestions(false);
    setIsChatStreaming(true);
    const timeNow = new Date().toLocaleTimeString('en-US', { hour12: false });

    setChatMessages(prev => [...prev, {
      id: Date.now().toString(),
      role: 'user',
      content: userText,
      timestamp: timeNow
    }]);

    const assistantId = (Date.now() + 1).toString();
    setChatMessages(prev => [...prev, {
      id: assistantId,
      role: 'assistant',
      content: '',
      timestamp: timeNow
    }]);

    try {
      const response = await fetch(`${API_BASE}/kernel/stream`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-Hive-API-Key': API_KEY
        },
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
                setChatMessages(prev => prev.map(msg =>
                  msg.id === assistantId ? { ...msg, content: accumulatedContent } : msg
                ));
              } else if (data.type === 'done') {
                setChatMessages(prev => prev.map(msg =>
                  msg.id === assistantId ? { ...msg, driftLock: data.drift_lock } : msg
                ));
                appendLog(`💬 Response complete`, undefined, data.drift_lock);
              } else if (data.type === 'error') {
                setChatMessages(prev => [...prev, { 
                  id: Date.now().toString(), 
                  role: 'system', 
                  content: `🚨 ${data.content}`, 
                  timestamp: new Date().toLocaleTimeString() 
                }]);
              }
            } catch (e) {}
          }
        }
      }
    } catch (error) {
      console.error('Chat error:', error);
      setChatMessages(prev => prev.map(msg =>
        msg.id === assistantId ? {
          ...msg,
          content: `⚠️ Error: ${error instanceof Error ? error.message : 'Connection failed'}`,
          role: 'system'
        } : msg
      ));
    } finally {
      setIsChatStreaming(false);
    }
  };

  const formatPHP = (val: number) => new Intl.NumberFormat('en-PH', {
    style: 'currency', currency: 'PHP', minimumFractionDigits: 0, maximumFractionDigits: 0
  }).format(val).replace('PHP', '₱');

  const handleBotDeployed = () => {
    appendLog("🤖 Bot deployed successfully! It will start trading on next market tick.");
    fetchSystemData();
  };

  if (!mounted) return <div className="min-h-screen bg-[#050505]" />;

  return (
    <div className="min-h-screen bg-[#050505] text-[#f5f5f7] font-sans selection:bg-[#00E5FF]/30 flex flex-col relative overflow-hidden">
      <div className="absolute inset-0 pointer-events-none opacity-20"
        style={{ backgroundImage: 'linear-gradient(to right, #ffffff0a 1px, transparent 1px), linear-gradient(to bottom, #ffffff0a 1px, transparent 1px)', backgroundSize: '40px 40px' }} />

      <div className="relative z-10 flex items-center justify-between px-6 py-1 border-b border-white/5 bg-[#050505]/80 text-[9px] font-mono tracking-widest text-zinc-500 uppercase">
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-1.5">
            <div className={`w-1.5 h-1.5 rounded-full ${kernelConnected ? 'bg-cyan-400 animate-pulse shadow-[0_0_8px_#00E5FF]' : 'bg-rose-500'}`} />
            <span>KERNEL: {kernelConnected ? 'ONLINE' : 'STANDBY'}</span>
          </div>
          <span>WORKERS: {Object.keys(workers).length}</span>
          <span>EVENTS: {sceStats.total_events}</span>
          <div className="flex items-center gap-1.5 border-l border-white/10 pl-4">
            <Lock className="w-3 h-3 text-[#9B72CB]" />
            <span>DRIFT LOCK: <span className="text-[#9B72CB] font-mono">{marketLock}</span></span>
          </div>
        </div>
        <div className="flex items-center gap-4">
          <span>SCE PROTOCOL v1.0</span>
          <span>PHOENIX v13.3.0</span>
          <span className="text-zinc-300">{time}</span>
        </div>
      </div>

      <div className="relative z-10 flex-1 flex flex-col p-4 gap-4 max-w-[1800px] mx-auto w-full h-[calc(100vh-28px)]">
        <header className="flex items-center justify-between shrink-0">
          <div className="flex items-center gap-3">
            <div className="w-12 h-12 bg-transparent border border-white/10 rounded-xl flex items-center justify-center">
              <Zap className="w-6 h-6 text-[#00E5FF]" />
            </div>
            <div>
              <h1 className="text-xl font-black tracking-tighter uppercase leading-none">
                REZTRADER <span className="text-[#00E5FF]">APEX</span>
              </h1>
              <p className="text-[9px] text-zinc-500 font-mono tracking-widest uppercase mt-1">{Object.keys(workers).length} Worker SCE Protocol</p>
            </div>
          </div>
          <div className="flex items-center gap-8">
            <div className="text-right">
              <p className="text-[9px] text-zinc-500 uppercase font-bold tracking-widest mb-0.5">Portfolio Value</p>
              <p className="text-xl font-black text-white">{formatPHP(balance)}</p>
            </div>
            <div className="text-right">
              <p className="text-[9px] text-zinc-500 uppercase font-bold tracking-widest mb-0.5">24H Performance</p>
              <p className={`text-xl font-black flex items-center justify-end gap-1 ${dailyPnL >= 0 ? 'text-[#00e676]' : 'text-[#ff0055]'}`}>
                {dailyPnL >= 0 ? '+' : ''}{formatPHP(dailyPnL)}
                {dailyPnL >= 0 ? <TrendingUp className="w-4 h-4" /> : <TrendingDown className="w-4 h-4" />}
              </p>
            </div>
            <button
              onClick={() => setShowBotHive(true)}
              className="flex items-center gap-2 px-4 py-2 bg-[#9B72CB]/20 text-[#9B72CB] border border-[#9B72CB]/50 rounded-lg hover:bg-[#9B72CB]/30 transition-all font-mono text-xs uppercase tracking-widest"
            >
              <Code className="w-4 h-4" /> Bot Hive
            </button>
            <div className="flex items-center bg-[#0a0a0c] border border-white/10 rounded-lg p-1">
              {(['manual', 'ai', 'hybrid'] as TradingMode[]).map((mode) => (
                <button
                  key={mode}
                  onClick={() => setTradingMode(mode)}
                  className={`px-4 py-1.5 rounded-md text-[10px] font-bold tracking-widest uppercase transition-all ${tradingMode === mode ? 'bg-white/10 text-white' : 'text-zinc-500 hover:text-zinc-300'}`}
                >
                  {mode}
                </button>
              ))}
            </div>
          </div>
        </header>

        <div className="flex-1 grid grid-cols-12 gap-4 min-h-0">
          {/* LEFT COLUMN */}
          <div className="col-span-3 flex flex-col gap-4 min-h-0">
            <div className="bg-[#0a0a0c] border border-white/5 rounded-2xl p-4 flex flex-col h-[40%]">
              <h3 className="text-[10px] font-mono tracking-widest uppercase text-zinc-400 mb-3 flex items-center gap-2">
                <Activity className="w-3 h-3 text-[#00E5FF]" /> MARKET TERMINAL
              </h3>
              <div className="flex-1 overflow-y-auto custom-scrollbar">
                {pairs.map(pair => (
                  <button
                    key={pair.symbol}
                    onClick={() => setSelectedPair(pair.symbol)}
                    className={`w-full p-3 rounded-lg mb-2 transition-all ${selectedPair === pair.symbol ? 'bg-[#00E5FF]/10 border border-[#00E5FF]/30' : 'hover:bg-white/5 border border-transparent'}`}
                  >
                    <div className="flex justify-between items-center">
                      <span className="font-mono text-sm">{pair.symbol}</span>
                      <span className="font-mono text-sm text-white">{formatPHP(pair.price)}</span>
                    </div>
                    <div className="flex justify-between mt-1 text-[9px] font-mono">
                      <span className={pair.change >= 0 ? 'text-[#00e676]' : 'text-[#ff0055]'}>
                        {pair.change >= 0 ? '+' : ''}{pair.change}%
                      </span>
                      <span className="text-zinc-500">Vol: {pair.volume}</span>
                    </div>
                  </button>
                ))}
              </div>
            </div>

            <div className="bg-[#0a0a0c] border border-white/5 rounded-2xl p-4 flex flex-col h-[30%]">
              <h3 className="text-[10px] font-mono tracking-widest uppercase text-zinc-400 mb-2 flex items-center gap-2">
                <Cpu className="w-3 h-3 text-[#9B72CB]" /> WORKER POOL
              </h3>
              <WorkerMetrics workers={workers} />
            </div>

            <div className="bg-[#0a0a0c] border border-white/5 rounded-2xl p-4 flex flex-col h-[30%]">
              <h3 className="text-[10px] font-mono tracking-widest uppercase text-zinc-400 mb-2 flex items-center gap-2">
                <GitBranch className="w-3 h-3 text-[#00E5FF]" /> SCE PROTOCOL
              </h3>
              <SCEMetrics stats={sceStats} blueprints={recentBlueprints} />
            </div>
          </div>

          {/* CENTER COLUMN */}
          <div className="col-span-6 flex flex-col gap-4 min-h-0">
            <div className="bg-[#0a0a0c] border border-white/5 rounded-2xl p-6 text-center shrink-0">
              <h2 className="text-2xl font-bold mb-4 flex items-center justify-center gap-3">
                {botActive ? (
                  <>
                    <div className="w-2 h-2 rounded-full bg-[#00e676] animate-pulse shadow-[0_0_10px_#00e676]" />
                    AUTONOMOUS MODE
                  </>
                ) : (
                  <>
                    <div className="w-2 h-2 rounded-full bg-zinc-500" />
                    MANUAL MODE
                  </>
                )}
              </h2>
              <button
                onClick={toggleBot}
                className={`px-8 py-3 rounded-lg font-bold tracking-widest uppercase text-sm transition-all ${botActive ? 'bg-red-600 hover:bg-red-700 text-white' : 'bg-[#00E5FF] hover:bg-[#00E5FF]/80 text-black shadow-[0_0_20px_rgba(0,229,255,0.3)]'}`}
              >
                {botActive ? 'STOP BOT' : 'ENGAGE BOT TRADER'}
              </button>
            </div>

            <div className="bg-[#0a0a0c] border border-white/5 rounded-2xl p-4 flex-1">
              <h3 className="text-[10px] font-mono tracking-widest uppercase text-zinc-400 mb-3 flex items-center gap-2">
                <BarChart2 className="w-3 h-3 text-[#9B72CB]" /> ACTIVE STRATEGIES
              </h3>
              <div className="grid grid-cols-2 gap-2 overflow-y-auto max-h-[200px] custom-scrollbar">
                {activeStrategies.filter(s => s.active).map(strategy => (
                  <div
                    key={strategy.name}
                    className={`p-3 rounded-lg cursor-pointer transition-all ${selectedStrategy === strategy.name ? 'bg-[#9B72CB]/10 border border-[#9B72CB]/30' : 'bg-black/30 hover:bg-black/50 border border-transparent'}`}
                    onClick={() => setSelectedStrategy(strategy.name)}
                  >
                    <div className="flex justify-between items-center">
                      <span className="text-white text-xs" style={{ color: strategy.color }}>{strategy.name}</span>
                      <span className="text-[#00E5FF] font-mono text-xs">{strategy.winRate}%</span>
                    </div>
                    <div className="flex justify-between mt-1 text-[8px] font-mono">
                      <span className="text-zinc-500">Trades: {strategy.trades}</span>
                      <span className="text-zinc-500">Worker: {strategy.worker}</span>
                    </div>
                    <div className="w-full h-1 bg-white/5 rounded-full mt-2 overflow-hidden">
                      <div className="h-full rounded-full transition-all" style={{ width: `${strategy.winRate}%`, backgroundColor: strategy.color }} />
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* RIGHT COLUMN */}
          <div className="col-span-3 flex flex-col gap-4 min-h-0">
            <div className="bg-[#0a0a0c] border border-white/5 rounded-2xl p-4 shrink-0">
              <h3 className="text-[10px] font-mono tracking-widest uppercase text-zinc-400 mb-3 flex items-center gap-2">
                <Terminal className="w-3 h-3 text-[#00E5FF]" /> MANUAL OVERRIDE
              </h3>
              <div className="mb-3">
                <div className="flex items-center gap-2 mb-2">
                  <input
                    type="number"
                    value={tradeAmount}
                    onChange={(e) => setTradeAmount(e.target.value)}
                    placeholder="Amount (PHP)"
                    className="flex-1 bg-black/50 border border-white/10 rounded-lg p-2 text-sm font-mono text-white placeholder:text-zinc-600 focus:outline-none focus:border-[#00E5FF]/50"
                  />
                  <button
                    onClick={() => setTradeAmount(balance.toString())}
                    className="px-3 py-2 bg-white/5 hover:bg-white/10 rounded-lg text-[10px] font-mono text-zinc-400"
                  >
                    MAX
                  </button>
                </div>
                <div className="text-[9px] font-mono text-zinc-600 mb-3">
                  Selected: <span className="text-[#00E5FF]">{selectedPair}</span>
                </div>
              </div>
              <div className="grid grid-cols-2 gap-2">
                <button
                  onClick={() => handleManualTrade('buy')}
                  disabled={!kernelConnected}
                  className="bg-[#00e676]/20 hover:bg-[#00e676]/30 text-[#00e676] border border-[#00e676]/30 p-3 rounded-lg font-bold text-sm transition-all disabled:opacity-50"
                >
                  BUY
                </button>
                <button
                  onClick={() => handleManualTrade('sell')}
                  disabled={!kernelConnected}
                  className="bg-[#ff0055]/20 hover:bg-[#ff0055]/30 text-[#ff0055] border border-[#ff0055]/30 p-3 rounded-lg font-bold text-sm transition-all disabled:opacity-50"
                >
                  SELL
                </button>
              </div>
            </div>

            <div className="bg-[#0a0a0c] border border-white/5 rounded-2xl p-4 shrink-0">
              <h3 className="text-[10px] font-mono tracking-widest uppercase text-zinc-400 mb-3 flex items-center gap-2">
                <BarChart2 className="w-3 h-3 text-[#9B72CB]" /> OPEN POSITIONS
              </h3>
              <div className="space-y-2 max-h-32 overflow-y-auto custom-scrollbar">
                {positions.map(pos => (
                  <div key={pos.id} className="p-2 bg-black/30 rounded-lg">
                    <div className="flex justify-between items-center">
                      <span className="font-mono text-sm">{pos.pair}</span>
                      <span className={pos.pnl >= 0 ? 'text-[#00e676]' : 'text-[#ff0055]'}>
                        {pos.pnl > 0 ? '+' : ''}{pos.pnl}%
                      </span>
                    </div>
                    <div className="flex justify-between text-[9px] font-mono text-zinc-500 mt-1">
                      <span>{pos.amount} @ {formatPHP(pos.entry_price)}</span>
                      <span>{formatPHP(pos.current_price)}</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            <div className="bg-[#0a0a0c] border border-white/5 rounded-2xl p-4 flex-1 flex flex-col min-h-0">
              <div className="flex items-center justify-between mb-3 shrink-0">
                <h3 className="text-[10px] font-mono tracking-widest uppercase text-zinc-400 flex items-center gap-2">
                  <MessageSquare className="w-3 h-3 text-[#9B72CB]" /> SOVEREIGN CHAT
                </h3>
                <span className="text-[8px] font-mono px-2 py-1 rounded-full bg-[#9B72CB]/10 text-[#9B72CB] border border-[#9B72CB]/20">
                  {Object.keys(workers).length} WORKERS
                </span>
              </div>
              <div className="flex-1 overflow-y-auto custom-scrollbar mb-3 space-y-3 pr-1">
                {chatMessages.map((msg) => (
                  <motion.div
                    key={msg.id}
                    initial={{ opacity: 0, y: 5 }}
                    animate={{ opacity: 1, y: 0 }}
                    className={`flex gap-2 ${msg.role === 'user' ? 'flex-row-reverse' : ''}`}
                  >
                    <div className={`w-5 h-5 rounded flex items-center justify-center shrink-0 mt-0.5 ${msg.role === 'user' ? 'bg-white/5 border border-white/10' : msg.role === 'system' ? 'bg-yellow-500/10 border border-yellow-500/30' : 'bg-[#9B72CB]/10 border border-[#9B72CB]/30'}`}>
                      {msg.role === 'user' ? <User className="w-3 h-3 text-zinc-400" /> : msg.role === 'system' ? <Terminal className="w-3 h-3 text-yellow-500" /> : <Bot className="w-3 h-3 text-[#9B72CB]" />}
                    </div>
                    <div className={`flex-1 ${msg.role === 'user' ? 'items-end' : 'items-start'}`}>
                      {msg.narrative && msg.narrative.length > 0 && (
                        <div className="mb-1 p-1.5 bg-purple-500/5 border border-purple-500/20 rounded">
                          <div className="text-[7px] font-mono text-purple-400 mb-0.5">🧠 REASONING</div>
                          {msg.narrative.map((step, i) => (
                            <div key={i} className="text-[8px] font-mono text-zinc-500 italic">"{step}"</div>
                          ))}
                        </div>
                      )}
                      <div className={`text-[10px] font-mono leading-relaxed whitespace-pre-wrap ${msg.role === 'user' ? 'text-white bg-white/5 p-2 rounded-lg rounded-tr-sm' : msg.role === 'system' ? 'text-yellow-500' : 'text-zinc-300'}`}>
                        {msg.content}
                      </div>
                      <div className="flex items-center justify-between mt-1">
                        <div className="flex items-center gap-2">
                          <span className="text-[6px] font-mono text-zinc-600">{msg.timestamp}</span>
                          {msg.worker && (
                            <span className="text-[6px] font-mono px-1 py-0.5 rounded bg-[#00E5FF]/10 text-[#00E5FF] border border-[#00E5FF]/20">
                              {msg.worker}
                            </span>
                          )}
                        </div>
                        {msg.driftLock && (
                          <div className="flex items-center gap-1 px-1.5 py-0.5 rounded border border-[#00e676]/30 bg-[#00e676]/10">
                            <ShieldCheck className="w-2 h-2 text-[#00e676]" />
                            <span className="text-[6px] font-mono font-bold text-[#00e676]">
                              {msg.driftLock.substring(0, 6)}
                            </span>
                          </div>
                        )}
                      </div>
                    </div>
                  </motion.div>
                ))}
                <div ref={chatEndRef} />
              </div>
              <div className="relative shrink-0">
                <div className="flex items-end gap-2 bg-black/50 border border-white/10 rounded-lg p-2 focus-within:border-[#9B72CB]/50 transition-colors">
                  <textarea
                    ref={chatInputRef}
                    value={chatInput}
                    onChange={handleChatInputChange}
                    onKeyDown={handleChatKeyDown}
                    placeholder="Ask about markets or use /commands..."
                    className="flex-1 bg-transparent text-[10px] text-white placeholder:text-zinc-600 outline-none resize-none max-h-20 min-h-[32px] font-mono"
                    rows={1}
                    disabled={!kernelConnected || isChatStreaming}
                  />
                  <button
                    onClick={handleSendChat}
                    disabled={!chatInput.trim() || isChatStreaming || !kernelConnected}
                    className="shrink-0 w-7 h-7 rounded bg-[#9B72CB]/20 hover:bg-[#9B72CB]/30 flex items-center justify-center transition-colors disabled:opacity-50"
                  >
                    <Send className="w-3 h-3 text-[#9B72CB]" />
                  </button>
                </div>
                {showChatSuggestions && chatSuggestions.length > 0 && (
                  <div
                    ref={chatSuggestionsRef}
                    className="absolute bottom-full left-0 right-0 mb-2 bg-black/90 border border-white/10 rounded-lg p-1 shadow-2xl"
                  >
                    {chatSuggestions.map((suggestion, i) => (
                      <div
                        key={i}
                        onClick={() => handleChatSuggestionClick(suggestion)}
                        className="px-3 py-1.5 hover:bg-white/10 cursor-pointer text-[9px] font-mono text-[#9B72CB] rounded transition-colors"
                      >
                        {suggestion}
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>

            <div className="bg-[#0a0a0c] border border-white/5 rounded-2xl p-4 h-24 overflow-y-auto custom-scrollbar shrink-0">
              <div className="flex items-center gap-2 mb-2">
                <Terminal className="w-3 h-3 text-zinc-500" />
                <span className="text-[8px] font-mono tracking-widest text-zinc-500">KERNEL LOGS</span>
              </div>
              <div className="space-y-1">
                {botLogs.map(log => (
                  <div key={log.id} className="text-[8px] font-mono flex items-center gap-1">
                    <span className="text-zinc-500">[{log.time}]</span>
                    {log.worker && (
                      <span className="text-[#00E5FF] bg-[#00E5FF]/10 px-1 rounded text-[6px]">
                        {log.worker}
                      </span>
                    )}
                    <span className={log.text.includes('❌') ? 'text-[#ff0055]' : 'text-zinc-400'}>
                      {log.text}
                    </span>
                    {log.driftLock && (
                      <span className="text-[6px] font-mono text-[#00e676] ml-auto">
                        {log.driftLock.substring(0, 4)}
                      </span>
                    )}
                  </div>
                ))}
                <div ref={logEndRef} />
              </div>
            </div>
          </div>
        </div>
      </div>

      <BotHiveModal
        isOpen={showBotHive}
        onClose={() => setShowBotHive(false)}
        onBotDeployed={handleBotDeployed}
      />

      <style jsx global>{`
        .custom-scrollbar::-webkit-scrollbar { width: 4px; }
        .custom-scrollbar::-webkit-scrollbar-track { background: transparent; }
        .custom-scrollbar::-webkit-scrollbar-thumb { background: rgba(255, 255, 255, 0.1); border-radius: 10px; }
        .custom-scrollbar::-webkit-scrollbar-thumb:hover { background: rgba(255, 255, 255, 0.2); }
      `}</style>
    </div>
  );
}