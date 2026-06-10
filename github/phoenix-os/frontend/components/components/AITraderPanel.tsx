'use client';

import React, { useState, useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { io, Socket } from 'socket.io-client';
import { 
  Zap, ChevronRight, Lock, Activity, BarChart2, ShieldCheck, 
  Terminal, Play, Square, Settings, Cpu, Clock, TrendingUp, TrendingDown
} from 'lucide-react';
import { AITraderPanel } from './AITraderPanel'; // Adjust path if needed!

// --- Configuration ---
const API_KEY = "rez-hive-admin-key-2026";
const API_BASE = "http://localhost:8001";

type TradingMode = 'manual' | 'ai' | 'hybrid';

interface MarketPair {
  symbol: string;
  price: number;
  change: number;
  volume: string;
}

export default function ApexSleekTrader() {
  const [mounted, setMounted] = useState(false);
  const[socket, setSocket] = useState<Socket | null>(null);
  const [kernelConnected, setKernelConnected] = useState(false);
  const [time, setTime] = useState('');

  // --- UI State ---
  const[tradingMode, setTradingMode] = useState<TradingMode>('hybrid');
  const [botActive, setBotActive] = useState(false);
  const [balance, setBalance] = useState(1245678);
  const[dailyPnL, setDailyPnL] = useState(23450);
  const [pairs, setPairs] = useState<MarketPair[]>([
    { symbol: 'BTC/PHP', price: 4524067, change: 2.46, volume: '1.2B' },
    { symbol: 'ETH/PHP', price: 189430, change: -1.21, volume: '890M' },
    { symbol: 'SOL/PHP', price: 8450, change: 5.68, volume: '450M' }
  ]);
  const[selectedPair, setSelectedPair] = useState('BTC/PHP');
  const [tradeAmount, setTradeAmount] = useState('');

  // 🔥 NEW: Live drift lock
  const [marketLock, setMarketLock] = useState<string>('--');

  // Akashic Vault States
  const [positions, setPositions] = useState<any[]>([
    { id: '1', pair: 'BTC/PHP', pnl: 2.45, amount: 0.15, entry_price: 4500000, current_price: 4610250 }
  ]);
  const [activeStrategies, setActiveStrategies] = useState<any[]>([
    { name: 'Momentum', winRate: 67.5, trades: 142, active: true, color: '#00E5FF' },
    { name: 'Mean Reversion', winRate: 58.2, trades: 98, active: true, color: '#9B72CB' },
    { name: 'Grid Trading', winRate: 52.8, trades: 215, active: false, color: '#ff0055' },
    { name: 'Scalping', winRate: 61.3, trades: 347, active: true, color: '#00e676' },
  ]);
  const [portfolioHistory, setPortfolioHistory] = useState<number[]>([
    1200000, 1205000, 1202000, 1210000, 1208000, 1215000, 1220000, 1218000, 1225000, 1230000, 1228000, 1235000, 1240000, 1238000, 1245678
  ]);
  const [selectedStrategy, setSelectedStrategy] = useState<string>('Momentum');

  // Backend Data State
  const [aiInsights, setAiInsights] = useState({ winRate: 94.2, maxDrawdown: 0.15 });
  const [botLogs, setBotLogs] = useState<{id: string, text: string, time: string}[]>([
    { id: '1', text: "Kernel v4.2-APEX online.", time: new Date().toLocaleTimeString() }
  ]);

  const logEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    setMounted(true);
    
    const timeInterval = setInterval(() => {
      setTime(new Date().toLocaleTimeString('en-US', { hour12: false }) + ' UTC');
    }, 1000);

    const newSocket = io(API_BASE, { 
      auth: { token: API_KEY }, 
      reconnectionDelayMax: 10000 
    });
    setSocket(newSocket);

    newSocket.on('connect', () => {
      setKernelConnected(true);
      appendLog("Connected to Neural Engine.");
    });

    newSocket.on('disconnect', () => {
      setKernelConnected(false);
      appendLog("Lost connection to Kernel.");
    });

    newSocket.on('marketUpdate', (data: any) => {
      // Capture the drift lock from the broadcast wrapper
      if (data.drift_lock) setMarketLock(data.drift_lock);
      
      setPairs(prev => {
        const newPairs = [...prev];
        const marketArray = data.data || data; 
        
        marketArray.forEach((ex: any) => {
          const existing = newPairs.find(p => p.symbol.includes(ex.name) || p.symbol === 'BTC/PHP');
          if (existing) {
            existing.price = ex.btcPrice;
            existing.change = (Math.random() * 0.4) - 0.2; 
            existing.volume = `${(ex.latency * 12.4).toFixed(1)}M`;
          }
        });
        return newPairs;
      });
    });

    newSocket.on('agentUpdate', (data) => setAiInsights(prev => ({ ...prev, winRate: data.winRate })));
    newSocket.on('riskUpdate', (data) => setAiInsights(prev => ({ ...prev, maxDrawdown: data.maxDrawdown })));
    newSocket.on('agentLog', (log) => appendLog(`${log.message}`));
    
    newSocket.on('trade_result', (res) => {
      if (res.status === 'AUTHORIZED') {
        appendLog(`Trade Executed. Cert: ${res.certificate}`);
        const profit = Math.floor(Math.random() * 500) + 100;
        setDailyPnL(prev => prev + profit);
        setBalance(prev => prev + profit);
      } else {
        appendLog(`Trade Rejected: ${res.error}`);
      }
    });

    newSocket.on('position_update', (data) => {
      setPositions(prev => {
        const existing = prev.findIndex(p => p.id === data.id);
        if (existing >= 0) {
          const updated = [...prev];
          updated[existing] = { ...updated[existing], ...data };
          return updated;
        }
        return [...prev, data];
      });
    });

    newSocket.on('portfolio_update', (data) => {
      setPositions(data.positions || []);
      setPortfolioHistory(prev => [...prev.slice(-20), data.total_value]);
    });

    newSocket.on('strategy_update', (data) => {
      setActiveStrategies(prev => 
        prev.map(s => s.name === data.name ? { ...s, ...data } : s)
      );
    });

    newSocket.emit('get_positions');
    newSocket.emit('get_strategies');

    return () => { 
      clearInterval(timeInterval);
      newSocket.disconnect(); 
    };
  },[]);

  useEffect(() => {
    logEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [botLogs]);

  const appendLog = (text: string) => {
    setBotLogs(prev =>[...prev.slice(-20), { 
      id: Date.now().toString() + Math.random(), 
      text, 
      time: new Date().toLocaleTimeString([], {hour: '2-digit', minute:'2-digit', second:'2-digit'})
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
    socket.emit('execute_trade', { pair: selectedPair, amount: amount, command: `MANUAL_${type.toUpperCase()}` });
    setTradeAmount('');
  };

  const toggleBot = () => {
    const newState = !botActive;
    setBotActive(newState);
    appendLog(newState ? "Zero Drift Auto-Execution Engaged." : "Bot Deactivated. Returning to Manual.");
  };

  const formatPHP = (val: number) => new Intl.NumberFormat('en-PH', { 
    style: 'currency', currency: 'PHP', minimumFractionDigits: 0, maximumFractionDigits: 0
  }).format(val).replace('PHP', '₱');

  if (!mounted) return <div className="min-h-screen bg-[#050505]" />;

  return (
    <div className="min-h-screen bg-[#050505] text-[#f5f5f7] font-sans selection:bg-[#00E5FF]/30 flex flex-col relative overflow-hidden">
      
      {/* Grid Background */}
      <div className="absolute inset-0 pointer-events-none opacity-20" 
           style={{ backgroundImage: 'linear-gradient(to right, #ffffff0a 1px, transparent 1px), linear-gradient(to bottom, #ffffff0a 1px, transparent 1px)', backgroundSize: '40px 40px' }} />

      {/* --- TOP SYSTEM BAR with Drift Lock --- */}
      <div className="relative z-10 flex items-center justify-between px-6 py-1 border-b border-white/5 bg-[#050505]/80 text-[9px] font-mono tracking-widest text-zinc-500 uppercase">
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-1.5">
            <div className={`w-1.5 h-1.5 rounded-full ${kernelConnected ? 'bg-cyan-400 animate-pulse shadow-[0_0_8px_#00E5FF]' : 'bg-rose-500'}`} />
            <span>SYSTEM: {kernelConnected ? 'ONLINE' : 'STANDBY'}</span>
          </div>
          <span>LATENCY: {kernelConnected ? '12MS' : '--'}</span>
          
          <div className="flex items-center gap-1.5 border-l border-white/10 pl-4">
            <Lock className="w-3 h-3 text-[#9B72CB]" />
            <span>DRIFT LOCK: <span className="text-[#9B72CB] font-mono">{marketLock}</span></span>
          </div>
        </div>
        <div className="flex items-center gap-4">
          <span>SCE PROTOCOL v1.0</span>
          <span>KERNEL V4.2.0-APEX</span>
          <span className="text-zinc-300">{time}</span>
        </div>
      </div>

      <div className="relative z-10 flex-1 flex flex-col p-4 gap-4 max-w-[1800px] mx-auto w-full h-[calc(100vh-28px)]">
        
        {/* Header */}
        <header className="flex items-center justify-between shrink-0">
          <div className="flex items-center gap-3">
            <div className="w-12 h-12 bg-transparent border border-white/10 rounded-xl flex items-center justify-center">
              <Zap className="w-6 h-6 text-[#00E5FF]" />
            </div>
            <div>
              <h1 className="text-xl font-black tracking-tighter uppercase leading-none">
                REZTRADER <span className="text-[#00E5FF]">APEX</span>
              </h1>
              <p className="text-[9px] text-zinc-500 font-mono tracking-widest uppercase mt-1">Zero Drift Neural Engine</p>
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
            
            <div className="flex items-center bg-[#0a0a0c] border border-white/10 rounded-lg p-1">
              {(['manual', 'ai', 'hybrid'] as TradingMode[]).map((mode) => (
                <button
                  key={mode}
                  onClick={() => setTradingMode(mode)}
                  className={`px-4 py-1.5 rounded-md text-[10px] font-bold tracking-widest uppercase transition-all ${
                    tradingMode === mode ? 'bg-white/10 text-white' : 'text-zinc-500 hover:text-zinc-300'
                  }`}
                >
                  {mode}
                </button>
              ))}
            </div>
          </div>
        </header>

        {/* MAIN GRID */}
        <div className="flex-1 grid grid-cols-12 gap-4 min-h-0">
          
          {/* LEFT COLUMN */}
          <div className="col-span-3 flex flex-col gap-4 min-h-0 overflow-y-auto custom-scrollbar pr-1">
            <div className="bg-[#0a0a0c] border border-white/5 rounded-2xl p-5 shrink-0 flex flex-col max-h-[40%]">
              <div className="flex items-center justify-between mb-4 shrink-0">
                <h3 className="text-[10px] font-mono tracking-widest uppercase text-zinc-400 flex items-center gap-2">
                  <Terminal className="w-3.5 h-3.5 text-[#00E5FF]" /> Market Terminal
                </h3>
                <div className="flex gap-1"><div className="w-1.5 h-1.5 rounded-full bg-[#00e676]"/><div className="w-1.5 h-1.5 rounded-full bg-[#00e676]"/><div className="w-1.5 h-1.5 rounded-full bg-[#00e676]"/></div>
              </div>
              
              <div className="flex-1 overflow-y-auto space-y-2 custom-scrollbar pr-2">
                {pairs.map(pair => (
                  <button key={pair.symbol} onClick={() => setSelectedPair(pair.symbol)} className={`w-full p-4 rounded-xl border transition-all text-left ${selectedPair === pair.symbol ? 'bg-white/5 border-white/10' : 'bg-transparent border-transparent hover:bg-white/5'}`}>
                    <div className="flex justify-between items-start mb-1">
                      <span className={`text-sm font-bold ${selectedPair === pair.symbol ? 'text-[#00E5FF]' : 'text-white'}`}>{pair.symbol}</span>
                      <span className="text-sm font-bold text-white">{formatPHP(pair.price)}</span>
                    </div>
                    <div className="flex justify-between items-center">
                      <span className="text-[9px] font-mono text-zinc-500">VOL: {pair.volume}</span>
                      <span className={`text-[10px] font-mono font-bold flex items-center gap-0.5 ${pair.change >= 0 ? 'text-[#00e676]' : 'text-[#ff0055]'}`}>
                        {pair.change >= 0 ? '▲' : '▼'} {Math.abs(pair.change).toFixed(2)}%
                      </span>
                    </div>
                  </button>
                ))}
              </div>
            </div>

            <div className="bg-[#0a0a0c] border border-white/5 rounded-2xl p-5 shrink-0">
              <h3 className="text-[10px] font-mono tracking-widest uppercase text-zinc-400 mb-4 flex items-center gap-2">
                <Cpu className="w-3.5 h-3.5 text-[#9B72CB]" /> Active Strategies
              </h3>

              <div className="space-y-3">
                {activeStrategies.map((strategy) => (
                  <button
                    key={strategy.name}
                    onClick={() => setSelectedStrategy(strategy.name)}
                    className={`w-full p-3 rounded-xl border transition-all ${
                      selectedStrategy === strategy.name 
                        ? 'bg-white/5 border-[#00E5FF]/30 shadow-[0_0_10px_rgba(0,229,255,0.1)]' 
                        : 'bg-transparent border-transparent hover:bg-white/5'
                    }`}
                  >
                    <div className="flex justify-between items-center mb-2">
                      <div className="flex items-center gap-2">
                        <div className="w-2 h-2 rounded-full" style={{ backgroundColor: strategy.color }} />
                        <span className="text-xs font-bold text-white">{strategy.name}</span>
                      </div>
                      <span className={`text-[8px] font-mono px-1.5 py-0.5 rounded border ${strategy.active ? 'text-[#00e676] bg-[#00e676]/10 border-[#00e676]/30' : 'text-zinc-500 border-zinc-500/30'}`}>
                        {strategy.active ? 'ACTIVE' : 'PAUSED'}
                      </span>
                    </div>
                    
                    <div className="grid grid-cols-2 gap-2 mt-2 text-left">
                      <div className="bg-black/30 rounded p-2">
                        <p className="text-[7px] font-mono text-zinc-500">WIN RATE</p>
                        <p className="text-[10px] font-bold text-[#00E5FF]">{strategy.winRate}%</p>
                      </div>
                      <div className="bg-black/30 rounded p-2">
                        <p className="text-[7px] font-mono text-zinc-500">TRADES</p>
                        <p className="text-[10px] font-bold text-white">{strategy.trades}</p>
                      </div>
                    </div>

                    <div className="mt-3 w-full h-1 bg-white/5 rounded-full overflow-hidden">
                      <div 
                        className="h-full bg-gradient-to-r from-[#00E5FF] to-[#9B72CB]"
                        style={{ width: `${strategy.winRate}%` }}
                      />
                    </div>
                  </button>
                ))}
              </div>
            </div>

            <div className="bg-[#0a0a0c] border border-white/5 rounded-2xl p-5 shrink-0">
              <h3 className="text-[10px] font-mono tracking-widest uppercase text-zinc-400 mb-4 flex items-center gap-2">
                <BarChart2 className="w-3.5 h-3.5 text-[#00E5FF]" /> Portfolio Performance
              </h3>

              <div className="h-16 flex items-end gap-[2px]">
                {portfolioHistory.slice(-30).map((value, i) => {
                  const min = Math.min(...portfolioHistory) * 0.98;
                  const max = Math.max(...portfolioHistory);
                  const height = Math.max(5, ((value - min) / (max - min)) * 100);
                  
                  return (
                    <div
                      key={i}
                      className="flex-1 bg-gradient-to-t from-[#00E5FF]/60 to-[#00E5FF]/10 rounded-t hover:from-cyan-300 transition-colors"
                      style={{ height: `${height}%` }}
                    />
                  )
                })}
              </div>
            </div>
          </div>

          {/* CENTER COLUMN */}
          <div className="col-span-6 flex flex-col gap-4 min-h-0">
            <div className="bg-[#0a0a0c] border border-white/5 rounded-2xl p-6 relative overflow-hidden shrink-0 flex flex-col items-center justify-center text-center">
              <div className="absolute inset-0 opacity-20 pointer-events-none flex items-center justify-center">
                <div className="w-full h-[1px] bg-gradient-to-r from-transparent via-[#00E5FF] to-transparent transform rotate-3" />
                <div className="w-full h-[1px] bg-gradient-to-r from-transparent via-[#9B72CB] to-transparent transform -rotate-2 absolute mt-10" />
              </div>

              <div className="relative z-10 w-full max-w-sm mx-auto">
                <div className="mx-auto w-max px-3 py-1 bg-white/5 rounded-full border border-white/10 text-[9px] font-mono tracking-widest text-zinc-400 mb-6">
                  KERNEL {kernelConnected ? 'ONLINE' : 'OFFLINE'}
                </div>

                <h2 className={`text-3xl font-black italic tracking-tight mb-2 uppercase ${botActive ? 'text-[#00E5FF]' : 'text-white'}`}>
                  {botActive ? 'Autonomous Mode' : 'Manual Mode'}
                </h2>
                
                <p className="text-xs text-zinc-400 mb-8 font-mono">
                  {botActive ? 'Zero Drift algorithms engaged...' : 'Monitoring arbitrage spreads...'}
                </p>

                <button 
                  onClick={toggleBot}
                  className={`w-full py-4 rounded-xl font-black text-sm tracking-widest uppercase transition-all flex items-center justify-center gap-2 ${
                    botActive 
                      ? 'bg-[#ff0055] text-white hover:bg-[#ff0055]/90 shadow-[0_0_20px_rgba(255,0,85,0.4)]' 
                      : 'bg-[#00E5FF] text-black hover:bg-[#00E5FF]/90 shadow-[0_0_20px_rgba(0,229,255,0.4)]'
                  }`}
                >
                  {botActive ? <Square className="w-5 h-5 fill-white" /> : <Play className="w-5 h-5 fill-black" />}
                  {botActive ? 'STOP BOT TRADER' : 'ENGAGE BOT TRADER'}
                </button>

                <p className="text-[8px] font-mono tracking-widest text-zinc-500 mt-4 uppercase">
                  ZERO DRIFT PROTECTION: ENABLED
                </p>
              </div>
            </div>

            <div className="bg-[#0a0a0c] border border-white/5 rounded-2xl overflow-hidden flex-1 relative min-h-0">
               <div className="absolute top-4 left-4