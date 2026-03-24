'use client';

import React, { useState, useEffect, useRef, memo } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { io, Socket } from 'socket.io-client';
import {
  Zap, ChevronRight, Lock, Activity, BarChart2, ShieldCheck,
  Terminal, Play, Square, Settings, Cpu, Clock, TrendingUp, TrendingDown,
  Send, Bot, User, Brain, MessageSquare, Code, Shield, GitBranch, Search, Sparkles
} from 'lucide-react';
import { BotHiveModal } from '@/components/BotHiveModal';

// --- Configuration (AUTH REMOVED) ---
const API_BASE = "http://localhost:8002";

type TradingMode = 'manual' | 'ai' | 'hybrid';

// --- Native TradingView Component (No library needed) ---
const TradingViewChart = memo(({ symbol }: { symbol: string }) => {
  const container = useRef<HTMLDivElement>(null);
  useEffect(() => {
    if (!container.current) return;
    container.current.innerHTML = '';
    const script = document.createElement("script");
    script.src = "https://s3.tradingview.com/tv.js";
    script.async = true;
    script.onload = () => {
      if (window.TradingView) {
        let tvSymbol = symbol;
        if (symbol === 'BTC/PHP') tvSymbol = 'BINANCE:BTCUSDT';
        else if (symbol === 'ETH/PHP') tvSymbol = 'BINANCE:ETHUSDT';
        else if (symbol === 'SOL/PHP') tvSymbol = 'BINANCE:SOLUSDT';
        else if (symbol === 'BTCUSDT') tvSymbol = 'BINANCE:BTCUSDT';
        else if (symbol === 'ETHUSDT') tvSymbol = 'BINANCE:ETHUSDT';
        else if (symbol === 'SOLUSDT') tvSymbol = 'BINANCE:SOLUSDT';
        
        new window.TradingView.widget({
          autosize: true,
          symbol: tvSymbol,
          interval: "1",
          timezone: "Etc/UTC",
          theme: "dark",
          style: "1",
          locale: "en",
          enable_publishing: false,
          hide_side_toolbar: false,
          allow_symbol_change: true,
          container_id: "tv_chart_container",
        });
      }
    };
    document.head.appendChild(script);
  }, [symbol]);
  return <div id="tv_chart_container" className="w-full h-full" ref={container} />;
});

export default function ApexSleekTrader() {
  const [mounted, setMounted] = useState(false);
  const [socket, setSocket] = useState<Socket | null>(null);
  const [kernelConnected, setKernelConnected] = useState(false);
  const [time, setTime] = useState('');
  
  const [selectedPair, setSelectedPair] = useState('BTC/PHP');
  const [botActive, setBotActive] = useState(false);
  const [balance, setBalance] = useState(1245678);
  const [dailyPnL, setDailyPnL] = useState(23450);
  const [marketLock, setMarketLock] = useState<string>('LOCAL_DEV_BYPASS');
  const [showBotHive, setShowBotHive] = useState(false);
  
  const [workers, setWorkers] = useState<any[]>([]);
  const [chatMessages, setChatMessages] = useState<any[]>([]);
  const [chatInput, setChatInput] = useState('');
  const [isChatStreaming, setIsChatStreaming] = useState(false);
  const [pairs] = useState([
    { symbol: 'BTC/PHP', price: 4524067, change: 2.46, volume: '1.2B' },
    { symbol: 'ETH/PHP', price: 189430, change: -1.21, volume: '890M' },
    { symbol: 'SOL/PHP', price: 8450, change: 5.68, volume: '450M' }
  ]);

  useEffect(() => {
    setMounted(true);
    const ticker = setInterval(() => setTime(new Date().toLocaleTimeString()), 1000);

    const newSocket = io(API_BASE, { path: '/ws', transports: ['websocket'] });
    newSocket.on('connect', () => setKernelConnected(true));
    newSocket.on('disconnect', () => setKernelConnected(false));
    newSocket.on('marketUpdate', (data) => data.drift_lock && setMarketLock(data.drift_lock));
    
    setSocket(newSocket);
    return () => { clearInterval(ticker); newSocket.disconnect(); };
  }, []);

  const handleSendChat = async () => {
    if (!chatInput.trim() || isChatStreaming) return;
    const text = chatInput;
    setChatInput('');
    setIsChatStreaming(true);
    
    setChatMessages(prev => [...prev, { role: 'user', content: text, timestamp: new Date().toLocaleTimeString() }]);

    try {
      const response = await fetch(`${API_BASE}/kernel/stream`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ task: text })
      });
      
      const reader = response.body?.getReader();
      const decoder = new TextDecoder();
      let accumulatedContent = '';
      const assistantId = Date.now().toString();
      
      setChatMessages(prev => [...prev, { role: 'assistant', content: '', id: assistantId, timestamp: new Date().toLocaleTimeString() }]);
      
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
              }
            } catch (e) {}
          }
        }
      }
    } catch (e) { 
      console.error(e); 
      setChatMessages(prev => [...prev, { role: 'system', content: 'Error connecting to kernel', timestamp: new Date().toLocaleTimeString() }]);
    } finally { 
      setIsChatStreaming(false); 
    }
  };

  const formatPHP = (val: number) => new Intl.NumberFormat('en-PH', {
    style: 'currency', currency: 'PHP', minimumFractionDigits: 0, maximumFractionDigits: 0
  }).format(val).replace('PHP', '₱');

  if (!mounted) return null;

  return (
    <div className="h-screen bg-gradient-to-br from-[#0a0a0c] via-[#050505] to-[#0a0a0c] text-[#c0caf5] font-sans flex flex-col overflow-hidden relative">
      
      {/* Animated Grid Background */}
      <div className="absolute inset-0 pointer-events-none opacity-20">
        <div className="absolute inset-0 bg-[radial-gradient(circle_at_50%_50%,_#7dcfff_0%,_transparent_50%)] opacity-5" />
        <div className="absolute inset-0" style={{ backgroundImage: 'linear-gradient(to right, #7dcfff0a 1px, transparent 1px), linear-gradient(to bottom, #7dcfff0a 1px, transparent 1px)', backgroundSize: '40px 40px' }} />
      </div>

      {/* 1. GLASS HEADER */}
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
              className={`w-2 h-2 rounded-full ${kernelConnected ? 'bg-[#9ece6a]' : 'bg-[#f7768e]'} shadow-[0_0_8px_${kernelConnected ? '#9ece6a' : '#f7768e'}]`} 
            />
            <span className={kernelConnected ? 'text-[#9ece6a]' : 'text-[#f7768e]'}>
              KERNEL: {kernelConnected ? 'ACTIVE' : 'OFFLINE'}
            </span>
          </div>
          <div className="flex items-center gap-2">
            <Shield className="w-3 h-3 text-[#9B72CB]" />
            <span>SCE LOCK: <span className="text-[#7dcfff]">{marketLock.substring(0, 12)}</span></span>
          </div>
          <span className="text-[#565f89]">{time}</span>
        </div>
        
        <div className="flex items-center gap-6">
          <div className="text-right">
            <div className="text-[8px] text-[#565f89] uppercase tracking-wider">Vault Balance</div>
            <motion.div 
              animate={{ scale: [1, 1.02, 1] }}
              transition={{ duration: 3, repeat: Infinity }}
              className="text-sm font-bold bg-gradient-to-r from-[#c0caf5] to-[#7dcfff] bg-clip-text text-transparent"
            >
              {formatPHP(balance)}
            </motion.div>
          </div>
          <div className="text-right">
            <div className="text-[8px] text-[#565f89] uppercase tracking-wider">24H PnL</div>
            <div className={`text-sm font-bold ${dailyPnL >= 0 ? 'text-[#9ece6a]' : 'text-[#f7768e]'}`}>
              {dailyPnL >= 0 ? '+' : ''}{formatPHP(dailyPnL)}
            </div>
          </div>
          <motion.button 
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
            onClick={() => setShowBotHive(true)} 
            className="flex items-center gap-2 px-4 py-1.5 bg-gradient-to-r from-[#9B72CB]/20 to-[#7dcfff]/20 border border-[#7dcfff]/30 rounded-lg text-[10px] text-[#7dcfff] hover:shadow-[0_0_15px_rgba(125,207,255,0.2)] transition-all uppercase tracking-wider"
          >
            <Code className="w-3 h-3" /> Bot Hive
          </motion.button>
        </div>
      </motion.header>

      {/* 2. MAIN WORKSPACE - GLASS PANELS */}
      <div className="relative z-10 flex-1 grid grid-cols-12 gap-4 p-4 overflow-hidden">
        
        {/* LEFT: TELEMETRY - GLASS CARD */}
        <motion.aside 
          initial={{ x: -20, opacity: 0 }}
          animate={{ x: 0, opacity: 1 }}
          transition={{ delay: 0.1 }}
          className="col-span-2 bg-black/30 backdrop-blur-xl border border-[#7dcfff]/10 rounded-2xl p-4 flex flex-col gap-6 shadow-[0_8px_32px_rgba(0,0,0,0.4)]"
        >
          <div>
            <h3 className="text-[10px] text-[#565f89] mb-4 flex items-center gap-2 font-mono uppercase tracking-wider">
              <Activity className="w-3 h-3 text-[#7dcfff]" /> ASSET PAIRS
            </h3>
            {pairs.map(p => (
              <motion.button 
                key={p.symbol} 
                whileHover={{ x: 4 }}
                onClick={() => setSelectedPair(p.symbol)} 
                className={`w-full text-left p-3 rounded-xl text-xs mb-2 transition-all ${selectedPair === p.symbol ? 'bg-gradient-to-r from-[#7dcfff]/20 to-transparent border-l-2 border-[#7dcfff] text-[#c0caf5]' : 'text-[#565f89] hover:bg-white/5'}`}
              >
                <span className="font-bold">{p.symbol}</span>
                <span className="float-right font-mono">{formatPHP(p.price)}</span>
                <div className={`text-[8px] mt-1 ${p.change >= 0 ? 'text-[#9ece6a]' : 'text-[#f7768e]'}`}>
                  {p.change >= 0 ? '+' : ''}{p.change}%
                </div>
              </motion.button>
            ))}
          </div>
          <div className="mt-auto">
            <div className="p-3 rounded-xl bg-gradient-to-br from-white/5 to-transparent border border-[#7dcfff]/10">
              <h4 className="text-[8px] text-[#7dcfff] uppercase mb-2 tracking-wider">Kernel Load</h4>
              <div className="w-full h-1 bg-white/10 rounded-full overflow-hidden">
                <motion.div 
                  initial={{ width: 0 }}
                  animate={{ width: '34%' }}
                  transition={{ duration: 1 }}
                  className="h-full bg-gradient-to-r from-[#7dcfff] to-[#9B72CB] rounded-full"
                />
              </div>
              <div className="flex justify-between mt-2 text-[7px] text-[#565f89]">
                <span>Workers: 56</span>
                <span>Latency: 12ms</span>
              </div>
            </div>
          </div>
        </motion.aside>

        {/* CENTER: CHART & CONTROL - GLASS CARD */}
        <motion.main 
          initial={{ y: 20, opacity: 0 }}
          animate={{ y: 0, opacity: 1 }}
          transition={{ delay: 0.2 }}
          className="col-span-7 flex flex-col bg-black/30 backdrop-blur-xl border border-[#7dcfff]/10 rounded-2xl overflow-hidden shadow-[0_8px_32px_rgba(0,0,0,0.4)]"
        >
          <div className="flex-1 p-2">
             <TradingViewChart symbol={selectedPair} />
          </div>
          
          <div className="p-4 border-t border-[#7dcfff]/10 bg-black/20">
            <div className="flex items-center justify-between">
              <motion.button 
                whileHover={{ scale: 1.02 }}
                whileTap={{ scale: 0.98 }}
                onClick={() => setBotActive(!botActive)} 
                className={`px-8 py-2.5 rounded-xl font-bold text-xs uppercase tracking-wider transition-all ${botActive ? 'bg-gradient-to-r from-[#f7768e] to-[#ff9e64] text-black shadow-[0_0_20px_rgba(247,118,142,0.3)]' : 'bg-gradient-to-r from-[#7dcfff] to-[#9B72CB] text-black shadow-[0_0_20px_rgba(125,207,255,0.3)]'}`}
              >
                {botActive ? 'KILL AUTONOMOUS' : 'ENGAGE AUTONOMOUS'}
              </motion.button>
              <div className="flex items-center gap-2">
                <div className="w-1.5 h-1.5 rounded-full bg-[#9ece6a] animate-pulse" />
                <span className="text-[9px] font-mono text-[#565f89]">SC-ENVIRONMENT: <span className="text-[#9ece6a]">ENFORCED</span></span>
              </div>
            </div>
          </div>
        </motion.main>

        {/* RIGHT: CONSTITUTIONAL CHAT - GLASS CARD */}
        <motion.aside 
          initial={{ x: 20, opacity: 0 }}
          animate={{ x: 0, opacity: 1 }}
          transition={{ delay: 0.3 }}
          className="col-span-3 bg-black/30 backdrop-blur-xl border border-[#7dcfff]/10 rounded-2xl flex flex-col overflow-hidden shadow-[0_8px_32px_rgba(0,0,0,0.4)]"
        >
          <div className="p-4 border-b border-[#7dcfff]/10 flex justify-between items-center bg-gradient-to-r from-[#9B72CB]/10 to-transparent">
            <div className="flex items-center gap-2">
              <Sparkles className="w-3 h-3 text-[#9B72CB]" />
              <span className="text-[10px] text-[#9B72CB] font-bold tracking-wider">SOVEREIGN AI</span>
            </div>
            <motion.div 
              animate={{ scale: [1, 1.2, 1] }}
              transition={{ duration: 2, repeat: Infinity }}
              className="w-2 h-2 rounded-full bg-[#9B72CB] shadow-[0_0_8px_#9B72CB]" 
            />
          </div>

          <div className="flex-1 overflow-y-auto p-4 space-y-4 custom-scrollbar">
            {chatMessages.map((m, i) => (
              <motion.div 
                key={i} 
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                className={`flex flex-col ${m.role === 'user' ? 'items-end' : 'items-start'}`}
              >
                <div className={`p-3 rounded-2xl text-xs max-w-[90%] ${m.role === 'user' ? 'bg-gradient-to-r from-[#7dcfff]/20 to-[#9B72CB]/20 border border-[#7dcfff]/30 text-[#c0caf5] rounded-br-sm' : 'bg-white/5 border border-white/10 text-[#c0caf5] rounded-bl-sm'}`}>
                  {m.content}
                </div>
                <span className="text-[7px] text-[#565f89] mt-1">{m.timestamp}</span>
              </motion.div>
            ))}
          </div>

          <div className="p-4 bg-black/20 border-t border-[#7dcfff]/10">
            <div className="flex items-center gap-2 bg-black/40 border border-[#7dcfff]/20 rounded-xl p-2 focus-within:border-[#7dcfff]/50 transition-all">
              <textarea 
                value={chatInput} 
                onChange={(e) => setChatInput(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && !e.shiftKey && handleSendChat()}
                placeholder="Query Kernel..." 
                className="flex-1 bg-transparent text-xs outline-none h-8 pt-1.5 resize-none text-[#c0caf5] placeholder:text-[#565f89]" 
              />
              <motion.button 
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
                onClick={handleSendChat} 
                disabled={isChatStreaming} 
                className="p-1.5 rounded-lg bg-gradient-to-r from-[#7dcfff]/20 to-[#9B72CB]/20 text-[#7dcfff] disabled:opacity-50"
              >
                <Send className="w-3.5 h-3.5" />
              </motion.button>
            </div>
          </div>
        </motion.aside>

      </div>

      <BotHiveModal isOpen={showBotHive} onClose={() => setShowBotHive(false)} />
      
      <style jsx global>{`
        .custom-scrollbar::-webkit-scrollbar { width: 4px; }
        .custom-scrollbar::-webkit-scrollbar-track { background: rgba(125,207,255,0.05); border-radius: 10px; }
        .custom-scrollbar::-webkit-scrollbar-thumb { background: rgba(125,207,255,0.3); border-radius: 10px; }
        .custom-scrollbar::-webkit-scrollbar-thumb:hover { background: rgba(125,207,255,0.5); }
        input::-webkit-outer-spin-button, input::-webkit-inner-spin-button { -webkit-appearance: none; margin: 0; }
      `}</style>
    </div>
  );
}