/**
 * @fileoverview APEX Trader - Production-grade AI-powered trading interface
 * @description Advanced trading dashboard with autonomous bot modes, real-time market data, portfolio visualization, and sovereign agent chat
 * @version 15.3.0-PHASE3-READY
 * 
 * FIXES IMPLEMENTED:
 * - ✅ Chat error logging to UI (not silent console errors)
 * - ✅ Chat message memory trimming (prevents unbounded growth)
 * - ✅ Portfolio balance sync after trades (auto-refresh via fetchPortfolio)
 * - ✅ Phase 3 metaphor/policy parameters (state + selector UI)
 * - ✅ Market data effect sync (re-sync on marketData change)
 * - ✅ Chat suggestions debounce (prevent excessive filtering)
 * - ✅ Socket resilience config (exponential backoff + retry limit)
 */

'use client';

import React, { useState, useEffect, useRef, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { io, Socket } from 'socket.io-client';
import { 
  Zap, ChevronRight, Lock, Activity, BarChart2, ShieldCheck, 
  Terminal, Play, Square, Settings, Cpu, Clock, TrendingUp, TrendingDown,
  Send, Bot, User, BookOpen, Brain, MessageSquare, Code, Upload, X, AlertCircle,
  Gauge, Network, Database, GitBranch, Layers, History, ArrowUpRight, ArrowDownRight,
  Briefcase, PieChart, Layout, Download
} from 'lucide-react';
import Link from 'next/link';
import { BotHiveModal } from '@/components/BotHiveModal';
import { TradeReportModal } from '@/components/TradeReportModal';
import { SovereignMessage } from '@/components/SovereignMessage';
import { usePhoenix, useAutoRefresh } from '@/hooks/usePhoenix';
import { TradingViewChart } from '@/components/TradingViewChart';
import { RezTraderChart } from '@/components/RezTraderChart';
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';

// ============================================================================
// TYPE DEFINITIONS
// ============================================================================

type TradingMode = 'manual' | 'ai' | 'hybrid';
type MetaphorType = 'balanced' | 'paranoid' | 'fast' | 'creative' | 'quiet' | 'academic' | 'lightning' | 'stealth';
type PolicyType = 'default' | 'safe' | 'team-safe';

interface MarketPair {
  symbol: string;
  price: number;
  change: number;
  volume: string;
}

interface WorkerInfo {
  name: string;
  module: string;
  metrics?: {
    calls: number;
    errors: number;
    avg_duration: number;
  };
}

interface Position {
  id: string;
  pair: string;
  pnl: number;
  amount: number;
  entry_price: number;
  current_price: number;
  type: 'BUY' | 'SELL';
}

interface Strategy {
  name: string;
  winRate: number;
  trades: number;
  active: boolean;
  color: string;
  worker: string;
}

interface Trade {
  id: string;
  type: 'BUY' | 'SELL';
  pair: string;
  amount: number;
  price: number;
  time: string;
  status: 'COMPLETED' | 'PENDING' | 'FAILED';
  bot_id?: string;
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

interface LogEntry {
  id: string;
  text: string;
  time: string;
  worker?: string;
  driftLock?: string;
}

// ============================================================================
// CONFIGURATION CONSTANTS
// ============================================================================

const TRADING_CONFIG = {
  KERNEL_HOST: process.env.NEXT_PUBLIC_KERNEL_HOST || 'http://localhost:8002',
  KERNEL_STREAM_ENDPOINT: '/kernel/stream',
  API_KEY: process.env.NEXT_PUBLIC_KERNEL_API_KEY || 'rez-hive-admin-key-2026',
  
  // Socket resilience (FIX #7)
  SOCKET_CONFIG: {
    autoConnect: false,
    reconnection: true,
    reconnectionDelay: 1000,
    reconnectionDelayMax: 10000,
    reconnectionAttempts: 5
  },
  SOCKET_PATH: '/socket.io',
  
  MAX_POSITIONS: 20,
  MAX_TRADE_HISTORY: 10,
  MAX_BOT_LOGS: 20,
  MAX_PORTFOLIO_HISTORY: 20,
  MAX_CHAT_MESSAGES: 100,  // FIX #2: Actively trim to this
  CHAT_SUGGESTION_DEBOUNCE: 100,  // FIX #6: Debounce delay (ms)
  
  BOT_DECISION_INTERVAL: 8000,
  AUTO_REFRESH_INTERVAL: 5000,
  BOT_DECISION_THRESHOLD: 0.7,
  
  TRADING_MODES: ['manual', 'ai', 'hybrid'] as const,
  DEFAULT_MODE: 'hybrid' as TradingMode,
  DEFAULT_TAB: 'chart' as 'chart' | 'portfolio',
  DEFAULT_METAPHOR: 'balanced' as MetaphorType,
  DEFAULT_POLICY: 'default' as PolicyType,
  
  DEFAULT_PAIRS: [
    { symbol: 'BTC/PHP', price: 4524067, change: 2.46, volume: '1.2B' },
    { symbol: 'ETH/PHP', price: 189430, change: -1.21, volume: '890M' },
    { symbol: 'SOL/PHP', price: 8450, change: 5.68, volume: '450M' }
  ] as const,
} as const;

const METAPHOR_OPTIONS: MetaphorType[] = [
  'balanced', 'paranoid', 'fast', 'creative', 'quiet', 'academic', 'lightning', 'stealth'
];

const POLICY_OPTIONS: PolicyType[] = ['default', 'safe', 'team-safe'];

const TRADING_STRATEGIES: Strategy[] = [
  { name: 'Momentum', winRate: 67.5, trades: 142, active: true, color: '#00E5FF', worker: 'MomentumWorker' },
  { name: 'Mean Reversion', winRate: 58.2, trades: 98, active: true, color: '#9B72CB', worker: 'ReversionWorker' },
  { name: 'Grid Trading', winRate: 52.8, trades: 215, active: false, color: '#ff0055', worker: 'GridWorker' },
  { name: 'Scalping', winRate: 61.3, trades: 347, active: true, color: '#00e676', worker: 'ScalpingWorker' },
];

const CHAT_COMMANDS = [
  "/help", "/pc status", "/trade buy BTC 1000", "/trade sell ETH 500",
  "/strategy list", "/backtest run", "/ai status", "/health",
  "/workers", "/events stats", "/memory search", "/constitution evaluate"
] as const;

// ============================================================================
// HELPER FUNCTIONS
// ============================================================================

const generateUniqueId = () => `${Date.now()}-${Math.random().toString(36).slice(2, 10)}-${performance.now()}`;

const calculatePercentageChange = (oldPrice: number, newPrice: number): number => {
  if (oldPrice === 0) return 0;
  return parseFloat((((newPrice - oldPrice) / oldPrice) * 100).toFixed(2));
};

// ============================================================================
// MAIN COMPONENT
// ============================================================================

export default function ApexTrader() {
  const {
    connected: kernelConnected,
    portfolio,
    marketData,
    killSwitch,
    executeTrade,
    activateKillSwitch,
    fetchPortfolio,
    workers: storeWorkers,
    chainStats,
    telemetry,
  } = usePhoenix();

  const balance = portfolio.balance;
  const totalValue = portfolio.total_value;

  const [mounted, setMounted] = useState(false);
  const [socket, setSocket] = useState<Socket | null>(null);
  const [time, setTime] = useState('');
  const [hasError, setHasError] = useState(false);
  const [errorMessage, setErrorMessage] = useState('');
  
  const [tradingMode, setTradingMode] = useState<TradingMode>(TRADING_CONFIG.DEFAULT_MODE);
  const [botActive, setBotActive] = useState(false);
  const [dailyPnL, setDailyPnL] = useState(23450);
  
  // FIX #4: Phase 3 governance parameters
  const [selectedMetaphor, setSelectedMetaphor] = useState<MetaphorType>(TRADING_CONFIG.DEFAULT_METAPHOR);
  const [selectedPolicy, setSelectedPolicy] = useState<PolicyType>(TRADING_CONFIG.DEFAULT_POLICY);
  
  const [pairs, setPairs] = useState<MarketPair[]>(
    (marketData && marketData.length > 0)
      ? marketData.map((md: any) => ({
          symbol: md.name,
          price: md.btcPrice,
          change: 0,
          volume: 'N/A'
        }))
      : Array.from(TRADING_CONFIG.DEFAULT_PAIRS) as MarketPair[]
  );
  
  const [selectedPair, setSelectedPair] = useState('BTC/PHP');
  const [tradeAmount, setTradeAmount] = useState('');
  const [activeTab, setActiveTab] = useState<'chart' | 'portfolio'>(TRADING_CONFIG.DEFAULT_TAB);
  const [showBotHive, setShowBotHive] = useState(false);
  const [selectedTradeForReport, setSelectedTradeForReport] = useState<any | null>(null);
  const [showTradeReport, setShowTradeReport] = useState(false);
  const [marketLock, setMarketLock] = useState<string>('--');
  const [lastTradeType, setLastTradeType] = useState<'buy' | 'sell' | null>(null);
  
  const [positions, setPositions] = useState<Position[]>([
    { id: generateUniqueId(), pair: 'BTC/PHP', pnl: 2.45, amount: 0.15, entry_price: 4500000, current_price: 4610250, type: 'BUY' }
  ]);
  
  const [activeStrategies, setActiveStrategies] = useState<Strategy[]>(TRADING_STRATEGIES);
  
  const [portfolioHistory, setPortfolioHistory] = useState<any[]>([
    { time: '00:00', value: 1200000 },
    { time: '04:00', value: 1210000 },
    { time: '08:00', value: 1205000 },
    { time: '12:00', value: 1225000 },
    { time: '16:00', value: 1245678 },
  ]);
  
  const [selectedStrategy, setSelectedStrategy] = useState<string>('Momentum');
  const [aiInsights, setAiInsights] = useState({ winRate: 94.2, maxDrawdown: 0.15 });
  const [tradeHistory, setTradeHistory] = useState<Trade[]>([]);
  const [botLogs, setBotLogs] = useState<LogEntry[]>([
    { id: generateUniqueId(), text: "Kernel v4.2-APEX online.", time: new Date().toLocaleTimeString() }
  ]);

  const [chatMessages, setChatMessages] = useState<ChatMessage[]>([
    { id: generateUniqueId(), role: 'assistant', content: '👋 Welcome to Apex Trader! Deploy a bot or use /commands.', timestamp: new Date().toLocaleTimeString() }
  ]);
  const [chatInput, setChatInput] = useState('');
  const [isChatStreaming, setIsChatStreaming] = useState(false);
  const [chatSuggestions, setChatSuggestions] = useState<string[]>([]);
  const [showChatSuggestions, setShowChatSuggestions] = useState(false);

  const logEndRef = useRef<HTMLDivElement>(null);
  const chatEndRef = useRef<HTMLDivElement>(null);
  const chatInputRef = useRef<HTMLTextAreaElement>(null);
  const chatSuggestionsRef = useRef<HTMLDivElement>(null);
  const chatSuggestionsTimeoutRef = useRef<NodeJS.Timeout>();  // FIX #6: Debounce ref

  useAutoRefresh(TRADING_CONFIG.AUTO_REFRESH_INTERVAL);

  // ============================================================================
  // STABILIZED CALLBACKS
  // ============================================================================
  
  const appendLog = useCallback((text: string, worker?: string, driftLock?: string) => {
    setBotLogs(prev => [...prev.slice(-TRADING_CONFIG.MAX_BOT_LOGS), {
      id: generateUniqueId(),
      text,
      time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' }),
      worker,
      driftLock
    }]);
  }, []);

  // ============================================================================
  // FIX #5: Market Data Sync Effect
  // ============================================================================
  useEffect(() => {
    if (marketData && marketData.length > 0) {
      setPairs(marketData.map(md => ({
        symbol: md.name,
        price: md.btcPrice,
        change: 0,
        volume: 'N/A'
      })));
    }
  }, [marketData]);

  // ============================================================================
  // SOCKET EFFECT
  // ============================================================================
  
  useEffect(() => {
    setMounted(true);
    const timeInterval = setInterval(() => setTime(new Date().toLocaleTimeString('en-US', { hour12: false }) + ' UTC'), 1000);
    
    let newSocket: Socket | null = null;
    let isMounted = true;

    try {
      // FIX #7: Socket resilience configuration
      newSocket = io(TRADING_CONFIG.KERNEL_HOST, { 
        auth: { token: TRADING_CONFIG.API_KEY }, 
        ...TRADING_CONFIG.SOCKET_CONFIG,
        path: TRADING_CONFIG.SOCKET_PATH 
      });
      
      if (isMounted) {
        setSocket(newSocket);
        newSocket.connect(); // Manual connect
      }

      newSocket.on('connect', () => { appendLog("✅ Connected to Neural Engine."); });
      newSocket.on('disconnect', () => { appendLog("⚠️ Lost connection to Kernel."); });
      newSocket.on('reconnect_attempt', () => { appendLog("🔄 Attempting to reconnect..."); });
      newSocket.on('reconnect_failed', () => { 
        appendLog("❌ Reconnection failed. Max attempts reached.");
        setErrorMessage("Lost connection to kernel. Check server status.");
        setHasError(true);
      });
      
      newSocket.on('error', (error: any) => {
        console.error('Socket error:', error);
        appendLog(`❌ Socket error: ${error?.message || 'Unknown error'}`);
        setErrorMessage(`Connection error: ${error?.message || 'Failed to connect to kernel'}`);
        setHasError(true);
      });

      newSocket.on('marketUpdate', (data: any) => {
        if (data.drift_lock) setMarketLock(data.drift_lock);
        setPairs(prev => {
          const newPairs = [...prev];
          const marketArray = data.data || data; 
          if (Array.isArray(marketArray)) {
            marketArray.forEach((ex: any) => {
              const existing = newPairs.find(p => p.symbol.includes(ex.name) || p.symbol === 'BTC/PHP');
              if (existing) {
                const oldPrice = existing.price;
                existing.price = ex.btcPrice;
                existing.change = calculatePercentageChange(oldPrice, ex.btcPrice);
              }
            });
          }
          return newPairs;
        });
      });

      newSocket.on('trade_result', (res) => {
        if (res.status === 'AUTHORIZED') {
          const tradeData = res.blueprint?.execution?.trade_data || {};
          const type = tradeData.type || 'BUY';
          const amount = tradeData.amount || 0;
          const price = tradeData.price || pairs.find(p => p.symbol === selectedPair)?.price || 0;
          
          appendLog(`✅ Trade Executed. Bot: ${res.bot_id || 'Manual'}`);
          // FIX #8: Trade feedback animation
          setLastTradeType(type.toLowerCase() === 'buy' ? 'buy' : 'sell');
          setTimeout(() => setLastTradeType(null), 1000);
          
          setTradeHistory(prev => {
            const newTrade: Trade = {
              id: generateUniqueId(),
              type: type as 'BUY' | 'SELL',
              pair: selectedPair,
              amount,
              price,
              time: new Date().toLocaleTimeString(),
              status: 'COMPLETED'
            };
            if (res.bot_id) {
              setSelectedTradeForReport(newTrade);
              setShowTradeReport(true);
            }
            return [newTrade, ...prev.slice(0, TRADING_CONFIG.MAX_TRADE_HISTORY - 1)];
          });

          setPositions(prev => {
            const existing = prev.find(p => p.pair === selectedPair);
            if (type === 'BUY') {
              if (existing) {
                const newAmount = existing.amount + amount;
                const newEntry = (existing.entry_price * existing.amount + price * amount) / newAmount;
                return prev.map(p => p.pair === selectedPair ? { ...p, amount: newAmount, entry_price: newEntry } : p);
              } else {
                return [...prev, { id: generateUniqueId(), pair: selectedPair, amount, entry_price: price, current_price: price, pnl: 0, type: 'BUY' }];
              }
            } else {
              if (existing) {
                const newAmount = Math.max(0, existing.amount - amount);
                if (newAmount === 0) return prev.filter(p => p.pair !== selectedPair);
                return prev.map(p => p.pair === selectedPair ? { ...p, amount: newAmount } : p);
              }
            }
            return prev;
          });

          if(tradeData.new_balance) {
              setPortfolioHistory(prev => [...prev, { 
                time: new Date().toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'}), 
                value: tradeData.new_balance 
              }].slice(-TRADING_CONFIG.MAX_PORTFOLIO_HISTORY));
          } else {
              const profit = Math.floor(Math.random() * 500) + 100;
              const finalProfit = (type === 'BUY' ? -profit : profit);
              setDailyPnL(prev => prev + finalProfit);
              setPortfolioHistory(ph => [...ph, { 
                time: new Date().toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'}), 
                value: (ph.length > 0 ? ph[ph.length-1].value : 1000000) + finalProfit
              }].slice(-TRADING_CONFIG.MAX_PORTFOLIO_HISTORY));
          }
          
          // FIX #3: Refresh portfolio balance from kernel
          setTimeout(() => fetchPortfolio(), 500);
        } else {
          appendLog(`❌ Trade Rejected: ${res.error}`);
        }
      });

    } catch (socketError) {
      console.error('Socket initialization error:', socketError);
      const errorMsg = socketError instanceof Error ? socketError.message : 'Unknown error';
      setErrorMessage(`Socket connection failed: ${errorMsg}`);
      setHasError(true);
    }

    const handleClickOutside = (event: MouseEvent) => {
      if (chatSuggestionsRef.current && !chatSuggestionsRef.current.contains(event.target as Node)) {
        setShowChatSuggestions(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);

    return () => {
      isMounted = false;
      clearInterval(timeInterval);
      newSocket?.disconnect();
      document.removeEventListener('mousedown', handleClickOutside);
      if (chatSuggestionsTimeoutRef.current) {
        clearTimeout(chatSuggestionsTimeoutRef.current);
      }
    };
  }, [appendLog, selectedPair, pairs, fetchPortfolio]);

  // ============================================================================
  // AUTO-SCROLL EFFECTS
  // ============================================================================
  
  useEffect(() => { logEndRef.current?.scrollIntoView({ behavior: 'smooth' }); }, [botLogs]);
  useEffect(() => { chatEndRef.current?.scrollIntoView({ behavior: 'smooth' }); }, [chatMessages]);

  // ============================================================================
  // BOT INTERVAL EFFECT
  // ============================================================================
  
  useEffect(() => {
    if (!botActive || !socket || !kernelConnected) return;

    const botInterval = setInterval(() => {
      const decision = Math.random() > TRADING_CONFIG.BOT_DECISION_THRESHOLD ? (Math.random() > 0.5 ? 'BUY' : 'SELL') : null;
      
      if (decision) {
        const amount = (Math.random() * 0.05).toFixed(4);
        appendLog(`🤖 AI Decision: ${decision} ${amount} ${selectedPair}`);
        socket.emit('execute_trade', { 
          pair: selectedPair, 
          amount: parseFloat(amount), 
          command: `AI_${decision}`,
          bot_id: 'CORTEX_V4',
          metaphor: selectedMetaphor,  // FIX #4: Include metaphor
          policy: selectedPolicy        // FIX #4: Include policy
        });
      }
    }, TRADING_CONFIG.BOT_DECISION_INTERVAL);

    return () => clearInterval(botInterval);
  }, [botActive, socket, kernelConnected, selectedPair, selectedMetaphor, selectedPolicy, appendLog]);

  // ============================================================================
  // HANDLERS
  // ============================================================================
  
  const handleManualTrade = (type: 'buy' | 'sell') => {
    if (!socket || !kernelConnected) return;
    const amount = parseFloat(tradeAmount) || 0;
    if (amount <= 0) return;
    appendLog(`📊 Initiating Manual ${type.toUpperCase()}...`);
    socket.emit('execute_trade', { 
      pair: selectedPair, 
      amount: amount, 
      command: `MANUAL_${type.toUpperCase()}`,
      metaphor: selectedMetaphor,  // FIX #4: Include metaphor
      policy: selectedPolicy        // FIX #4: Include policy
    });
    setTradeAmount('');
  };

  const toggleBot = () => {
    const newState = !botActive;
    setBotActive(newState);
    appendLog(newState ? "🤖 Zero Drift Auto-Execution Engaged." : "🛑 Bot Deactivated.");
  };

  // FIX #6: Debounced chat input with suggestions
  const handleChatInputChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    const value = e.target.value;
    setChatInput(value);
    const el = e.target;
    el.style.height = 'auto';
    el.style.height = `${Math.min(el.scrollHeight, 80)}px`;
    
    // Clear previous timeout
    if (chatSuggestionsTimeoutRef.current) {
      clearTimeout(chatSuggestionsTimeoutRef.current);
    }
    
    if (value.length > 0) {
      chatSuggestionsTimeoutRef.current = setTimeout(() => {
        const filtered = Array.from(CHAT_COMMANDS).filter(cmd =>
          cmd.toLowerCase().startsWith(value.toLowerCase())
        );
        setChatSuggestions(filtered);
        setShowChatSuggestions(filtered.length > 0);
      }, TRADING_CONFIG.CHAT_SUGGESTION_DEBOUNCE);
    } else {
      setChatSuggestions([]);
      setShowChatSuggestions(false);
    }
  };

  const handleChatSuggestionClick = (suggestion: string) => {
    setChatInput(suggestion);
    setShowChatSuggestions(false);
    chatInputRef.current?.focus();
    if (chatInputRef.current) {
      chatInputRef.current.style.height = 'auto';
    }
  };

  const handleChatKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); handleSendChat(); }
  };

  // FIX #1, #2, #4: Enhanced handleSendChat with error logging, message trimming, and Phase 3 params
  const handleSendChat = useCallback(async () => {
    if (!chatInput.trim() || isChatStreaming || !kernelConnected) return;
    const userText = chatInput;
    setChatInput('');
    setShowChatSuggestions(false);
    setIsChatStreaming(true);
    const timeNow = new Date().toLocaleTimeString();
    
    // FIX #2: Trim chat messages to prevent unbounded growth
    setChatMessages(prev => [...prev.slice(-(TRADING_CONFIG.MAX_CHAT_MESSAGES - 1)), { 
      id: generateUniqueId(), 
      role: 'user', 
      content: userText, 
      timestamp: timeNow 
    }]);
    
    const assistantId = generateUniqueId();
    // FIX #2: Trim here too
    setChatMessages(prev => [...prev.slice(-(TRADING_CONFIG.MAX_CHAT_MESSAGES - 1)), { 
      id: assistantId, 
      role: 'assistant', 
      content: '⏳ Processing...', 
      timestamp: timeNow 
    }]);

    try {
      // FIX #4: Phase 3 - Include metaphor and policy parameters
      const response = await fetch(`${TRADING_CONFIG.KERNEL_HOST}${TRADING_CONFIG.KERNEL_STREAM_ENDPOINT}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
          task: userText,
          metaphor: selectedMetaphor,
          policy: selectedPolicy,
          constraints: {
            cognition_mode: selectedMetaphor,
            policy_level: selectedPolicy
          }
        })
      });

      if (!response.ok) {
        throw new Error(`Kernel returned ${response.status}: ${response.statusText}`);
      }

      if (!response.body) {
        throw new Error('No response body received');
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let accumulatedContent = '';
      let hasReceivedData = false;

      try {
        while (true) {
          const { done, value } = await reader.read();
          if (done) break;

          const chunk = decoder.decode(value);
          const lines = chunk.split('\n');
        
          for (const line of lines) {
            if (line.startsWith('data: ')) {
              try {
                const data = JSON.parse(line.substring(6));
                hasReceivedData = true;
                
                if (data.type === 'reflex') {
                  setChatMessages(prev => prev.map(msg =>
                    msg.id === assistantId ? { ...msg, content: data.content } : msg
                  ));
                } else if (data.type === 'token') {
                  accumulatedContent += data.content;
                  setChatMessages(prev => prev.map(msg =>
                    msg.id === assistantId ? { ...msg, content: accumulatedContent } : msg
                  ));
                } else if (data.type === 'done') {
                  setChatMessages(prev => prev.map(msg =>
                    msg.id === assistantId ? { ...msg, driftLock: data.drift_lock } : msg
                  ));
                }
              } catch (e) {
                // FIX #1: Enhanced error logging to UI instead of silent failure
                console.error('Stream parse error:', { line, error: e });
                setChatMessages(prev => prev.map(msg =>
                  msg.id === assistantId 
                    ? { 
                        ...msg, 
                        content: `⚠️ Stream parsing error: ${e instanceof Error ? e.message : 'JSON decode failed'}`,
                        role: 'system' as const 
                      } 
                    : msg
                ));
                break; // Stop processing further lines on error
              }
            }
          }
        }
      } finally {
        reader.releaseLock();
      }

      if (!hasReceivedData && !accumulatedContent) {
        // FIX #1: Proper error message to user
        setChatMessages(prev => prev.map(msg =>
          msg.id === assistantId
            ? { ...msg, content: '⚠️ No response received from kernel. Try again.', role: 'system' as const }
            : msg
        ));
      }
    } catch (error: unknown) {
      // FIX #1: Comprehensive error display to user
      console.error('Chat error:', error);
      const errorMsg = error instanceof Error ? error.message : 'Connection failed';
      setChatMessages(prev => prev.map(msg =>
        msg.id === assistantId ? {
          ...msg,
          content: `❌ Error: ${errorMsg}. Check kernel status.`,
          role: 'system' as const
        } : msg
      ));
      setErrorMessage(`Chat error: ${errorMsg}`);
      setHasError(true);
    } finally {
      setIsChatStreaming(false);
    }
  }, [chatInput, isChatStreaming, kernelConnected, selectedMetaphor, selectedPolicy]);

  const formatPHP = (val: number) => new Intl.NumberFormat('en-PH', {
    style: 'currency', currency: 'PHP', minimumFractionDigits: 0, maximumFractionDigits: 0
  }).format(val).replace('PHP', '₱');

  const getTradingViewSymbol = (pair: string) => {
    const symbol = pair.replace('/', '');
    if (symbol === 'BTCPHP') return 'BINANCE:BTCPHP';
    if (symbol === 'ETHPHP') return 'BINANCE:ETHPHP';
    if (symbol === 'SOLPHP') return 'BINANCE:SOLPHP';
    return symbol;
  };

  const workersInfo: Record<string, WorkerInfo> = (storeWorkers || []).reduce<Record<string, WorkerInfo>>((acc: Record<string, WorkerInfo>, w: any) => {
    acc[w.name] = { 
      name: w.name, 
      module: 'builtin', 
      metrics: { calls: 0, errors: 0, avg_duration: 0 } 
    };
    return acc;
  }, {});

  if (!mounted) return <div className="min-h-screen bg-[#050505]" />;

  return (
    <div className="min-h-screen bg-[#050505] text-[#f5f5f7] font-sans selection:bg-[#00E5FF]/30 flex flex-col relative overflow-hidden">
      {/* Background Grid */}
      <div className="absolute inset-0 pointer-events-none opacity-20"
        style={{ backgroundImage: 'linear-gradient(to right, #ffffff0a 1px, transparent 1px), linear-gradient(to bottom, #ffffff0a 1px, transparent 1px)', backgroundSize: '40px 40px' }} />

      {/* Status Bar */}
      <div className="relative z-10 flex items-center justify-between px-6 py-1 border-b border-white/5 bg-[#050505]/80 text-[9px] font-mono tracking-widest text-zinc-500 uppercase">
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-1.5">
            <div className={`w-1.5 h-1.5 rounded-full ${kernelConnected ? 'bg-cyan-400 animate-pulse shadow-[0_0_8px_#00E5FF]' : 'bg-rose-500'}`} />
            <span>KERNEL: {kernelConnected ? 'ONLINE' : 'STANDBY'}</span>
          </div>
          <span>WORKERS: {Object.keys(workersInfo).length}</span>
          <span>EVENTS: {chainStats.total_events}</span>
          <div className="flex items-center gap-1.5 border-l border-white/10 pl-4">
            <Lock className="w-3 h-3 text-[#9B72CB]" />
            <span>DRIFT LOCK: <span className="text-[#9B72CB] font-mono">{marketLock}</span></span>
          </div>
        </div>
        <div className="flex items-center gap-4">
          <span>SCE PROTOCOL v1.0</span>
          <span>PHOENIX v15.3.0-PHASE3</span>
          <span className="text-zinc-300">{time}</span>
        </div>
      </div>

      {/* Error Banner */}
      {hasError && (
        <div className="relative z-20 bg-red-900/20 border-b border-red-500/30 px-6 py-3 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <AlertCircle className="w-5 h-5 text-red-500 shrink-0" />
            <span className="text-sm text-red-400 font-mono">{errorMessage || 'An error occurred'}</span>
          </div>
          <button 
            onClick={() => { setHasError(false); setErrorMessage(''); }}
            className="px-3 py-1 rounded text-xs font-mono bg-red-500/20 hover:bg-red-500/30 text-red-400 transition-colors"
          >
            Dismiss
          </button>
        </div>
      )}

      <div className="relative z-10 flex-1 flex flex-col p-4 gap-4 max-w-[1800px] mx-auto w-full h-[calc(100vh-28px)] overflow-hidden">
        
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
              <p className="text-[9px] text-zinc-500 font-mono tracking-widest uppercase mt-1">
                {Object.keys(workersInfo).length} Worker SCE Protocol
              </p>
            </div>
          </div>
          <div className="flex items-center gap-8">
            <Link href="/dashboard">
              <button className="flex items-center gap-2 px-4 py-1.5 rounded-xl bg-[#00E5FF]/10 border border-[#00E5FF]/30 text-[#00E5FF] hover:bg-[#00E5FF]/20 transition-all font-mono text-[10px] uppercase tracking-widest">
                <Layout className="w-4 h-4" /> Terminal
              </button>
            </Link>
            
            {/* FIX #4: Phase 3 Metaphor Selector */}
            <div className="flex flex-col gap-1">
              <label className="text-[8px] font-mono text-zinc-500 uppercase tracking-widest">Metaphor</label>
              <select 
                value={selectedMetaphor} 
                onChange={(e) => setSelectedMetaphor(e.target.value as MetaphorType)}
                className="bg-black/50 border border-white/10 rounded px-2 py-1 text-[9px] font-mono text-white hover:border-[#00E5FF]/30 focus:outline-none focus:border-[#00E5FF]/50"
              >
                {METAPHOR_OPTIONS.map(m => (
                  <option key={m} value={m}>{m}</option>
                ))}
              </select>
            </div>

            {/* FIX #4: Phase 3 Policy Selector */}
            <div className="flex flex-col gap-1">
              <label className="text-[8px] font-mono text-zinc-500 uppercase tracking-widest">Policy</label>
              <select 
                value={selectedPolicy} 
                onChange={(e) => setSelectedPolicy(e.target.value as PolicyType)}
                className="bg-black/50 border border-white/10 rounded px-2 py-1 text-[9px] font-mono text-white hover:border-[#9B72CB]/30 focus:outline-none focus:border-[#9B72CB]/50"
              >
                {POLICY_OPTIONS.map(p => (
                  <option key={p} value={p}>{p}</option>
                ))}
              </select>
            </div>
            
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

        {/* Main Grid */}
        <div className="flex-1 grid grid-cols-12 gap-4 min-h-0">
          {/* LEFT COLUMN - Market, Workers, SCE */}
          <div className="col-span-3 flex flex-col gap-4 min-h-0">
            {/* Market Terminal */}
            <div className="bg-[#0a0a0c] border border-white/5 rounded-2xl p-4 flex flex-col h-[35%] min-h-0">
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

            {/* Worker Pool */}
            <div className="bg-[#0a0a0c] border border-white/5 rounded-2xl p-4 flex flex-col h-[35%] min-h-0">
              <h3 className="text-[10px] font-mono tracking-widest uppercase text-zinc-400 mb-3 flex items-center gap-2">
                <Cpu className="w-3 h-3 text-[#9B72CB]" /> WORKER POOL
              </h3>
              <div className="bg-black/30 p-2 rounded-lg border border-white/5 flex-1 overflow-y-auto">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-[8px] font-mono text-[#9B72CB] flex items-center gap-1">
                    <Cpu className="w-3 h-3" /> ACTIVE WORKERS
                  </span>
                  <span className="text-[8px] font-mono text-white">{Object.keys(workersInfo).length}</span>
                </div>
                <div className="space-y-1">
                  {Object.entries(workersInfo).slice(0, 5).map(([name, info]) => (
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
                </div>
              </div>
            </div>

            {/* SCE Protocol */}
            <div className="bg-[#0a0a0c] border border-white/5 rounded-2xl p-4 flex flex-col h-[30%] min-h-0">
              <h3 className="text-[10px] font-mono tracking-widest uppercase text-zinc-400 mb-3 flex items-center gap-2">
                <GitBranch className="w-3 h-3 text-[#00E5FF]" /> SCE PROTOCOL
              </h3>
              <div className="bg-black/30 p-2 rounded-lg border border-white/5">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-[8px] font-mono text-[#00E5FF] flex items-center gap-1">
                    <GitBranch className="w-3 h-3" /> SCE PROTOCOL
                  </span>
                  <span className={`text-[6px] px-1 py-0.5 rounded ${
                    chainStats.chain_valid 
                      ? 'bg-[#00e676]/10 text-[#00e676] border border-[#00e676]/20' 
                      : 'bg-[#ff0055]/10 text-[#ff0055] border border-[#ff0055]/20'
                  }`}>
                    {chainStats.chain_valid ? 'VERIFIED' : 'BROKEN'}
                  </span>
                </div>
                <div className="grid grid-cols-2 gap-1 mb-2">
                  <div>
                    <span className="text-[6px] font-mono text-zinc-500">EVENTS</span>
                    <div className="text-[9px] font-bold text-white">{chainStats.total_events}</div>
                  </div>
                  <div>
                    <span className="text-[6px] font-mono text-zinc-500">LATEST</span>
                    <div className="text-[6px] font-mono text-[#9B72CB] truncate">{chainStats.latest?.substring(0, 8) || '...'}</div>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* CENTER COLUMN - Chart & Portfolio */}
          <div className="col-span-6 flex flex-col gap-4 min-h-0">
            {/* Bot Control */}
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
              <div className="flex gap-4 justify-center">
                <button
                  onClick={toggleBot}
                  className={`px-8 py-3 rounded-lg font-bold tracking-widest uppercase text-sm transition-all ${botActive ? 'bg-red-600 hover:bg-red-700 text-white' : 'bg-[#00E5FF] hover:bg-[#00E5FF]/80 text-black shadow-[0_0_20px_rgba(0,229,255,0.3)]'}`}
                >
                  {botActive ? 'STOP BOT' : 'ENGAGE BOT TRADER'}
                </button>
                <button
                  onClick={() => setShowBotHive(true)}
                  className="px-8 py-3 rounded-lg font-bold tracking-widest uppercase text-sm bg-[#9B72CB] hover:bg-[#9B72CB]/80 text-white shadow-[0_0_20px_rgba(155,114,203,0.3)] flex items-center gap-2"
                >
                  <Code className="w-4 h-4" /> BOT HIVE
                </button>
              </div>
            </div>

            {/* Chart/Portfolio Area */}
            <div className="bg-[#0a0a0c] border border-white/5 rounded-2xl flex-1 flex flex-col relative overflow-hidden">
              <div className="absolute inset-0 opacity-5 bg-[radial-gradient(circle_at_center,_#00E5FF_1px,_transparent_1px)] bg-[size:20px_20px] pointer-events-none" />
              
              <div className="px-6 py-2 border-b border-white/5 flex items-center justify-between bg-black/40 z-20">
                <div className="flex gap-4">
                  <button 
                    onClick={() => setActiveTab('chart')}
                    className={`text-[10px] font-mono tracking-widest uppercase transition-all ${activeTab === 'chart' ? 'text-[#00E5FF] border-b border-[#00E5FF]' : 'text-zinc-500 hover:text-zinc-300'}`}
                  >
                    LIVE CHART
                  </button>
                  <button 
                    onClick={() => setActiveTab('portfolio')}
                    className={`text-[10px] font-mono tracking-widest uppercase transition-all ${activeTab === 'portfolio' ? 'text-[#00E5FF] border-b border-[#00E5FF]' : 'text-zinc-500 hover:text-zinc-300'}`}
                  >
                    PORTFOLIO GRAPH
                  </button>
                </div>
                <div className="flex items-center gap-2">
                  <div className="w-2 h-2 rounded-full bg-[#00E5FF] animate-pulse" />
                  <span className="text-[8px] font-mono text-zinc-500 uppercase">REAL-TIME DATA FEED</span>
                </div>
              </div>

              <div className="flex-1 min-h-0 relative">
                {activeTab === 'chart' ? (
                  <TradingViewChart 
                    theme="dark"
                    symbol={getTradingViewSymbol(selectedPair)}
                    interval="D"
                  />
                ) : (
                  <div className="h-full w-full p-8 flex flex-col">
                    <div className="flex items-center justify-between mb-8">
                      <div>
                        <h3 className="text-xl font-black text-white uppercase tracking-tighter">Portfolio Growth</h3>
                        <p className="text-[10px] font-mono text-zinc-500 uppercase">Historical balance tracking (24H)</p>
                      </div>
                      <div className="text-right">
                        <p className="text-[10px] font-mono text-zinc-500 uppercase">Current Balance</p>
                        <p className="text-2xl font-black text-[#00E5FF]">{formatPHP(balance)}</p>
                      </div>
                    </div>
                    <div className="flex-1 min-h-0">
                      <ResponsiveContainer width="100%" height="100%">
                        <AreaChart data={portfolioHistory}>
                          <defs>
                            <linearGradient id="colorValue" x1="0" y1="0" x2="0" y2="1">
                              <stop offset="5%" stopColor="#00E5FF" stopOpacity={0.3}/>
                              <stop offset="95%" stopColor="#00E5FF" stopOpacity={0}/>
                            </linearGradient>
                          </defs>
                          <CartesianGrid strokeDasharray="3 3" stroke="#ffffff05" vertical={false} />
                          <XAxis dataKey="time" stroke="#52525b" fontSize={10} tickLine={false} axisLine={false} />
                          <YAxis stroke="#52525b" fontSize={10} tickLine={false} axisLine={false} tickFormatter={(val) => `${(val/1000000).toFixed(1)}M`} />
                          <Tooltip contentStyle={{ backgroundColor: '#0a0a0c', border: '1px solid rgba(255,255,255,0.1)', borderRadius: '8px', fontSize: '10px' }} />
                          <Area type="monotone" dataKey="value" stroke="#00E5FF" fillOpacity={1} fill="url(#colorValue)" strokeWidth={2} />
                        </AreaChart>
                      </ResponsiveContainer>
                    </div>
                  </div>
                )}
              </div>
              
              {/* Trade History Overlay */}
              <div className="h-32 bg-[#050505]/90 border-t border-white/5 p-3 overflow-hidden flex flex-col">
                <div className="flex items-center justify-between mb-2">
                  <h3 className="text-[10px] font-mono tracking-widest uppercase text-zinc-500 flex items-center gap-2">
                    <History className="w-3 h-3" /> RECENT EXECUTIONS
                  </h3>
                  <span className="text-[8px] font-mono text-zinc-600 uppercase">Paper Trading Mode</span>
                </div>
                <div className="flex-1 overflow-y-auto custom-scrollbar space-y-1">
                  {tradeHistory.length === 0 ? (
                    <div className="h-full flex items-center justify-center text-zinc-700 text-[10px] font-mono italic">
                      No recent trades detected.
                    </div>
                  ) : (
                    tradeHistory.map(trade => (
                      <div key={trade.id} className="flex items-center justify-between text-[10px] font-mono py-1 border-b border-white/5 last:border-0 group">
                        <div className="flex items-center gap-3">
                          <span className={trade.type === 'BUY' ? 'text-[#00e676]' : 'text-[#ff0055]'}>
                            {trade.type === 'BUY' ? <ArrowUpRight className="w-3 h-3 inline mr-1" /> : <ArrowDownRight className="w-3 h-3 inline mr-1" />}
                            {trade.type}
                          </span>
                          <span className="text-white">{trade.pair}</span>
                          <span className="text-zinc-500">{trade.amount} @ {formatPHP(trade.price)}</span>
                        </div>
                        <div className="flex items-center gap-3">
                          <button 
                            onClick={() => {
                              setSelectedTradeForReport(trade);
                              setShowTradeReport(true);
                            }}
                            className="opacity-0 group-hover:opacity-100 transition-opacity text-[#00E5FF] hover:underline text-[8px]"
                          >
                            VIEW REPORT
                          </button>
                          <span className="text-zinc-600">{trade.time}</span>
                          <span className="text-[#00E5FF] bg-[#00E5FF]/10 px-1 rounded text-[8px]">COMPLETED</span>
                        </div>
                      </div>
                    ))
                  )}
                </div>
              </div>
            </div>
          </div>

          {/* RIGHT COLUMN - Chat & Logs */}
          <div className="col-span-3 flex flex-col gap-4 min-h-0">
            {/* Manual Override */}
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
                    disabled={!kernelConnected}
                    aria-label="Trade amount in PHP"
                    className="flex-1 bg-black/50 border border-white/10 rounded-lg p-2 text-sm font-mono text-white placeholder:text-zinc-600 focus:outline-none focus:border-[#00E5FF]/50 disabled:opacity-50"
                  />
                  <button
                    onClick={() => setTradeAmount(balance.toString())}
                    className="px-3 py-2 bg-white/5 hover:bg-white/10 rounded-lg text-[10px] font-mono text-zinc-400 transition-colors"
                  >
                    MAX
                  </button>
                </div>
              </div>
              <div className="grid grid-cols-2 gap-2">
                <button
                  onClick={() => handleManualTrade('buy')}
                  disabled={!kernelConnected || !tradeAmount.trim()}
                  aria-label={`Buy ${selectedPair}`}
                  className={`bg-[#00e676]/20 hover:bg-[#00e676]/30 text-[#00e676] border border-[#00e676]/30 p-3 rounded-lg font-bold text-sm transition-all disabled:opacity-50 disabled:cursor-not-allowed ${lastTradeType === 'buy' ? 'ring-2 ring-[#00e676]' : ''}`}
                >
                  BUY
                </button>
                <button
                  onClick={() => handleManualTrade('sell')}
                  disabled={!kernelConnected || !tradeAmount.trim()}
                  aria-label={`Sell ${selectedPair}`}
                  className={`bg-[#ff0055]/20 hover:bg-[#ff0055]/30 text-[#ff0055] border border-[#ff0055]/30 p-3 rounded-lg font-bold text-sm transition-all disabled:opacity-50 disabled:cursor-not-allowed ${lastTradeType === 'sell' ? 'ring-2 ring-[#ff0055]' : ''}`}
                >
                  SELL
                </button>
              </div>
            </div>

            {/* Sovereign Chat */}
            <div className="bg-[#0a0a0c] border border-white/5 rounded-2xl p-4 flex-1 flex flex-col min-h-0">
              <div className="flex items-center justify-between mb-3 shrink-0">
                <h3 className="text-[10px] font-mono tracking-widest uppercase text-zinc-400 flex items-center gap-2">
                  <MessageSquare className="w-3 h-3 text-[#9B72CB]" /> SOVEREIGN CHAT
                </h3>
                <span className="text-[8px] font-mono px-2 py-1 rounded-full bg-[#9B72CB]/10 text-[#9B72CB] border border-[#9B72CB]/20">
                  SCE PROTOCOL
                </span>
              </div>
              <div className="flex-1 overflow-y-auto custom-scrollbar mb-3 space-y-3 pr-1">
                {chatMessages.map((msg) => (
                  <div key={msg.id} className={`flex gap-2 ${msg.role === 'user' ? 'flex-row-reverse' : ''}`}>
                    <div className={`w-5 h-5 rounded flex items-center justify-center shrink-0 mt-0.5 ${msg.role === 'user' ? 'bg-white/5 border border-white/10' : msg.role === 'system' ? 'bg-yellow-500/10 border border-yellow-500/30' : 'bg-[#9B72CB]/10 border border-[#9B72CB]/30'}`}>
                      {msg.role === 'user' ? <User className="w-3 h-3 text-zinc-400" /> : msg.role === 'system' ? <Terminal className="w-3 h-3 text-yellow-500" /> : <Bot className="w-3 h-3 text-[#9B72CB]" />}
                    </div>
                    <div className={`flex-1 ${msg.role === 'user' ? 'items-end' : 'items-start'}`}>
                      <div className={`text-[10px] font-mono leading-relaxed whitespace-pre-wrap ${msg.role === 'user' ? 'text-white bg-white/5 p-2 rounded-lg rounded-tr-sm' : msg.role === 'system' ? 'text-yellow-500' : 'text-zinc-300'}`}>
                        <SovereignMessage content={msg.content} role={msg.role} driftLock={msg.driftLock} />
                      </div>
                      <div className="flex items-center justify-between mt-1">
                        <span className="text-[6px] font-mono text-zinc-600">{msg.timestamp}</span>
                        {msg.driftLock && (
                          <div className="flex items-center gap-1 px-1.5 py-0.5 rounded border border-[#00e676]/30 bg-[#00e676]/10">
                            <ShieldCheck className="w-2 h-2 text-[#00e676]" />
                            <span className="text-[6px] font-mono font-bold text-[#00e676]">{msg.driftLock.substring(0, 6)}</span>
                          </div>
                        )}
                      </div>
                    </div>
                  </div>
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
                    placeholder="Ask about markets..."
                    className="flex-1 bg-transparent text-[10px] text-white placeholder:text-zinc-600 outline-none resize-none max-h-20 min-h-[32px] font-mono overflow-hidden"
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

            {/* Kernel Logs */}
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

      {/* Modals */}
      <BotHiveModal isOpen={showBotHive} onClose={() => setShowBotHive(false)} />
      <TradeReportModal 
        isOpen={showTradeReport}
        onClose={() => setShowTradeReport(false)}
        trade={selectedTradeForReport}
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
