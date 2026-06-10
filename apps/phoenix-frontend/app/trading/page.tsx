// app/(terminal)/trading/page.tsx
'use client';

import React, { useState, useEffect, useRef, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Zap, Activity, TrendingUp, TrendingDown, Clock,
  Play, StopCircle, Brain, Send, Bot, User,
  Terminal, History, ArrowUpRight, ArrowDownRight,
  RefreshCw, MessageSquare,
} from 'lucide-react';
import { usePhoenix, useAutoRefresh } from '@/hooks/usePhoenix';
import { SovereignMessage } from '@/components/SovereignMessage';
import { TradingViewChart } from '@/components/TradingViewChart';
import {
  AreaChart, Area, XAxis, YAxis, CartesianGrid,
  Tooltip, ResponsiveContainer,
} from 'recharts';

// ── Types ────────────────────────────────────────────────
type TradingMode = 'paper' | 'live';
type ExecutionMode = 'manual' | 'auto';
type ChartTab = 'chart' | 'portfolio';

interface Trade {
  id: string;
  type: 'BUY' | 'SELL';
  symbol: string;
  amount: number;
  price: number;
  time: string;
  mode: TradingMode;
}

interface ChatMessage {
  id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  driftLock?: string;
  timestamp: string;
}

// ── Constants ────────────────────────────────────────────
const SYMBOLS = [
  { name: 'BTC/PHP', defaultPrice: 4524067 },
  { name: 'ETH/PHP', defaultPrice: 189430 },
  { name: 'SOL/PHP', defaultPrice: 8450 },
] as const;

const STRATEGIES = [
  { id: 'momentum',     name: 'Momentum',       winRate: 67.5, color: '#7dcfff' },
  { id: 'mean_revert',  name: 'Mean Reversion', winRate: 58.2, color: '#9B72CB' },
  { id: 'grid',         name: 'Grid Trading',   winRate: 52.8, color: '#f7768e' },
  { id: 'scalping',     name: 'Scalping',       winRate: 61.3, color: '#9ece6a' },
] as const;

const formatPHP = (val: number) =>
  '₱' + val.toLocaleString('en-PH', { maximumFractionDigits: 0 });

export default function TradingPage() {
  const {
    connected,
    portfolio,
    marketData,
    executeTrade,
    runBacktest,
    workers,
  } = usePhoenix();

  // ── State ──────────────────────────────────────────────
  const [tradingMode, setTradingMode] = useState<TradingMode>('paper');
  const [executionMode, setExecutionMode] = useState<ExecutionMode>('manual');
  const [chartTab, setChartTab] = useState<ChartTab>('chart');
  const [selectedSymbol, setSelectedSymbol] = useState('BTC/PHP');
  const [tradeAmount, setTradeAmount] = useState('');
  const [selectedStrategy, setSelectedStrategy] = useState('momentum');
  const [botActive, setBotActive] = useState(false);
  const [trades, setTrades] = useState<Trade[]>([]);
  const [backtestResult, setBacktestResult] = useState<any>(null);
  const [isBacktesting, setIsBacktesting] = useState(false);

  // Chat
  const [chatMessages, setChatMessages] = useState<ChatMessage[]>([
    {
      id: 'welcome',
      role: 'assistant',
      content: 'Trading terminal ready. Use /help for commands.',
      timestamp: new Date().toLocaleTimeString(),
    },
  ]);
  const [chatInput, setChatInput] = useState('');
  const [isChatStreaming, setIsChatStreaming] = useState(false);
  const chatEndRef = useRef<HTMLDivElement>(null);

  // Portfolio history
  const [portfolioHistory, setPortfolioHistory] = useState([
    { time: '00:00', value: 1000000 },
    { time: '04:00', value: 1012000 },
    { time: '08:00', value: 1008000 },
    { time: '12:00', value: 1025000 },
    { time: '16:00', value: portfolio?.balance || 1045678 },
  ]);

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [chatMessages]);

  // Update portfolio history on balance change
  useEffect(() => {
    if (!portfolio?.balance) return;
    setPortfolioHistory((prev) => [
      ...prev.slice(-19),
      {
        time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        value: portfolio.balance,
      },
    ]);
  }, [portfolio?.balance]);

  // ── Symbol prices (from market data or defaults) ───────
  const getPrice = useCallback(
    (symbol: string) => {
      const sym = SYMBOLS.find((s) => s.name === symbol);
      // Try real market data first
      if (marketData?.length > 0) {
        const md = marketData.find((m: any) =>
          symbol.toLowerCase().includes(m.name?.toLowerCase())
        );
        if (md?.btcPrice) return md.btcPrice;
      }
      return sym?.defaultPrice || 0;
    },
    [marketData]
  );

  // ── Handlers ───────────────────────────────────────────
  const handleTrade = useCallback(
    async (side: 'buy' | 'sell') => {
      const amount = parseFloat(tradeAmount);
      if (!amount || amount <= 0 || !connected) return;

      const price = getPrice(selectedSymbol);
      const quantity = amount / price;

      const success = await executeTrade(side, selectedSymbol, quantity, price);

      if (success) {
        setTrades((prev) => [
          {
            id: Date.now().toString(),
            type: side.toUpperCase() as 'BUY' | 'SELL',
            symbol: selectedSymbol,
            amount: quantity,
            price,
            time: new Date().toLocaleTimeString(),
            mode: tradingMode,
          },
          ...prev.slice(0, 19),
        ]);
        setTradeAmount('');
      }
    },
    [tradeAmount, connected, selectedSymbol, tradingMode, getPrice, executeTrade]
  );

  const handleBacktest = useCallback(async () => {
    setIsBacktesting(true);
    const result = await runBacktest(selectedStrategy);
    setBacktestResult(result);
    setIsBacktesting(false);
  }, [selectedStrategy, runBacktest]);

  const handleSendChat = useCallback(async () => {
    if (!chatInput.trim() || isChatStreaming || !connected) return;
    const text = chatInput;
    setChatInput('');
    setIsChatStreaming(true);
    const now = new Date().toLocaleTimeString();

    setChatMessages((prev) => [
      ...prev,
      { id: Date.now().toString(), role: 'user', content: text, timestamp: now },
    ]);

    const assistantId = (Date.now() + 1).toString();
    setChatMessages((prev) => [
      ...prev,
      { id: assistantId, role: 'assistant', content: '🧠 Processing...', timestamp: now },
    ]);

    try {
      const response = await fetch('http://127.0.0.1:8002/kernel/stream', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-Hive-API-Key': 'rez-hive-admin-key-2026',
        },
        body: JSON.stringify({ task: text }),
      });

      const reader = response.body?.getReader();
      const decoder = new TextDecoder();
      let accumulated = '';

      while (reader) {
        const { done, value } = await reader.read();
        if (done) break;
        const chunk = decoder.decode(value);

        for (const line of chunk.split('\n\n')) {
          if (!line.startsWith('data: ')) continue;
          try {
            const data = JSON.parse(line.slice(6));
            if (data.type === 'token') {
              accumulated += data.content;
              setChatMessages((prev) =>
                prev.map((m) =>
                  m.id === assistantId ? { ...m, content: accumulated } : m
                )
              );
            } else if (data.type === 'done') {
              setChatMessages((prev) =>
                prev.map((m) =>
                  m.id === assistantId ? { ...m, driftLock: data.drift_lock } : m
                )
              );
            }
          } catch {}
        }
      }
    } catch (err) {
      setChatMessages((prev) =>
        prev.map((m) =>
          m.id === assistantId
            ? { ...m, content: `⚠️ ${err instanceof Error ? err.message : 'Error'}`, role: 'system' }
            : m
        )
      );
    } finally {
      setIsChatStreaming(false);
    }
  }, [chatInput, isChatStreaming, connected]);

  const currentPrice = getPrice(selectedSymbol);

  return (
    <div className="flex-1 flex flex-col p-4 gap-4 min-h-0">
      {/* ── Header Controls ──────────────────────── */}
      <div className="flex items-center justify-between shrink-0">
        <div className="flex items-center gap-4">
          {/* Trading Mode */}
          <div className="flex items-center bg-black/30 rounded-lg p-1 border border-white/5">
            {(['paper', 'live'] as TradingMode[]).map((mode) => (
              <button
                key={mode}
                onClick={() => setTradingMode(mode)}
                className={`px-4 py-1.5 rounded-md text-[10px] font-mono uppercase tracking-wider transition ${
                  tradingMode === mode
                    ? mode === 'live'
                      ? 'bg-phoenix-error/20 text-phoenix-error'
                      : 'bg-phoenix-success/20 text-phoenix-success'
                    : 'text-phoenix-muted hover:text-white'
                }`}
              >
                {mode}
              </button>
            ))}
          </div>

          {/* Execution Mode */}
          <div className="flex items-center bg-black/30 rounded-lg p-1 border border-white/5">
            {(['manual', 'auto'] as ExecutionMode[]).map((mode) => (
              <button
                key={mode}
                onClick={() => setExecutionMode(mode)}
                className={`px-4 py-1.5 rounded-md text-[10px] font-mono uppercase tracking-wider transition ${
                  executionMode === mode
                    ? 'bg-phoenix-primary/20 text-phoenix-primary'
                    : 'text-phoenix-muted hover:text-white'
                }`}
              >
                {mode}
              </button>
            ))}
          </div>

          {tradingMode === 'paper' && (
            <span className="text-[10px] font-mono text-phoenix-success bg-phoenix-success/10 border border-phoenix-success/20 px-2 py-1 rounded">
              SIMULATION
            </span>
          )}
        </div>

        <div className="flex items-center gap-6">
          <div className="text-right">
            <div className="text-[9px] text-phoenix-muted font-mono">BALANCE</div>
            <div className="text-lg font-bold font-mono">{formatPHP(portfolio?.balance || 1000000)}</div>
          </div>
          <div className="text-right">
            <div className="text-[9px] text-phoenix-muted font-mono">TOTAL VALUE</div>
            <div className="text-lg font-bold font-mono text-phoenix-primary">
              {formatPHP(portfolio?.total_value || 1000000)}
            </div>
          </div>
        </div>
      </div>

      {/* ── Main Grid ────────────────────────────── */}
      <div className="flex-1 grid grid-cols-12 gap-4 min-h-0">
        {/* LEFT — Market + Strategies */}
        <div className="col-span-3 flex flex-col gap-4 min-h-0">
          {/* Market Pairs */}
          <div className="bg-black/30 border border-white/5 rounded-2xl p-4 flex flex-col">
            <h3 className="text-[10px] font-mono uppercase tracking-wider text-phoenix-muted mb-3 flex items-center gap-2">
              <Activity className="w-3 h-3 text-phoenix-primary" />
              MARKETS
            </h3>
            <div className="space-y-2">
              {SYMBOLS.map((sym) => {
                const price = getPrice(sym.name);
                const isSelected = selectedSymbol === sym.name;
                return (
                  <button
                    key={sym.name}
                    onClick={() => setSelectedSymbol(sym.name)}
                    className={`w-full p-3 rounded-lg transition ${
                      isSelected
                        ? 'bg-phoenix-primary/10 border border-phoenix-primary/30'
                        : 'hover:bg-white/5 border border-transparent'
                    }`}
                  >
                    <div className="flex justify-between">
                      <span className="font-mono text-sm">{sym.name}</span>
                      <span className="font-mono text-sm">{formatPHP(price)}</span>
                    </div>
                  </button>
                );
              })}
            </div>
          </div>

          {/* Trade Execution */}
          <div className="bg-black/30 border border-white/5 rounded-2xl p-4">
            <h3 className="text-[10px] font-mono uppercase tracking-wider text-phoenix-muted mb-3 flex items-center gap-2">
              <Zap className="w-3 h-3 text-phoenix-primary" />
              {tradingMode === 'paper' ? 'PAPER TRADE' : 'LIVE TRADE'}
            </h3>

            <div className="space-y-3">
              <div>
                <label className="text-[10px] text-phoenix-muted block mb-1">Amount (PHP)</label>
                <input
                  type="number"
                  value={tradeAmount}
                  onChange={(e) => setTradeAmount(e.target.value)}
                  placeholder="1000"
                  className="w-full bg-black/50 border border-white/10 rounded-lg px-3 py-2 text-sm font-mono outline-none focus:border-phoenix-primary/50"
                  disabled={!connected}
                />
              </div>

              {tradeAmount && currentPrice > 0 && (
                <div className="text-[10px] text-phoenix-muted font-mono">
                  ≈ {(parseFloat(tradeAmount) / currentPrice).toFixed(6)} units
                </div>
              )}

              <div className="grid grid-cols-2 gap-2">
                <button
                  onClick={() => handleTrade('buy')}
                  disabled={!connected || !tradeAmount}
                  className="py-2.5 rounded-lg bg-phoenix-success/20 border border-phoenix-success/30 text-phoenix-success font-bold text-sm transition hover:bg-phoenix-success/30 disabled:opacity-50"
                >
                  BUY
                </button>
                <button
                  onClick={() => handleTrade('sell')}
                  disabled={!connected || !tradeAmount}
                  className="py-2.5 rounded-lg bg-phoenix-error/20 border border-phoenix-error/30 text-phoenix-error font-bold text-sm transition hover:bg-phoenix-error/30 disabled:opacity-50"
                >
                  SELL
                </button>
              </div>
            </div>

            {/* Auto Mode Controls */}
            {executionMode === 'auto' && (
              <div className="mt-4 pt-4 border-t border-white/5">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <Brain className="w-4 h-4 text-phoenix-accent" />
                    <span className="text-xs text-phoenix-muted">Auto Trading</span>
                  </div>
                  <button
                    onClick={() => setBotActive(!botActive)}
                    className={`px-3 py-1.5 rounded-lg text-xs font-mono flex items-center gap-1 transition ${
                      botActive
                        ? 'bg-phoenix-error/20 text-phoenix-error'
                        : 'bg-phoenix-success/20 text-phoenix-success'
                    }`}
                  >
                    {botActive ? <StopCircle className="w-3 h-3" /> : <Play className="w-3 h-3" />}
                    {botActive ? 'Stop' : 'Start'}
                  </button>
                </div>
              </div>
            )}
          </div>

          {/* Backtest */}
          <div className="bg-black/30 border border-white/5 rounded-2xl p-4 flex-1">
            <h3 className="text-[10px] font-mono uppercase tracking-wider text-phoenix-muted mb-3 flex items-center gap-2">
              <Clock className="w-3 h-3 text-phoenix-accent" />
              BACKTEST
            </h3>

            <select
              value={selectedStrategy}
              onChange={(e) => setSelectedStrategy(e.target.value)}
              className="w-full bg-black/50 border border-white/10 rounded-lg px-3 py-2 text-sm outline-none mb-3"
            >
              {STRATEGIES.map((s) => (
                <option key={s.id} value={s.id}>{s.name} ({s.winRate}%)</option>
              ))}
            </select>

            <button
              onClick={handleBacktest}
              disabled={isBacktesting}
              className="w-full py-2 rounded-lg bg-phoenix-primary/20 border border-phoenix-primary/30 text-phoenix-primary text-sm font-mono hover:bg-phoenix-primary/30 transition disabled:opacity-50 flex items-center justify-center gap-2"
            >
              {isBacktesting ? (
                <RefreshCw className="w-4 h-4 animate-spin" />
              ) : (
                <RefreshCw className="w-4 h-4" />
              )}
              Run Backtest
            </button>

            {backtestResult && (
              <div className="mt-3 p-3 bg-white/[0.02] rounded-lg space-y-1.5 text-xs font-mono">
                <Row label="Return" value={`${(backtestResult.total_return * 100).toFixed(1)}%`} color={backtestResult.total_return >= 0 ? 'text-phoenix-success' : 'text-phoenix-error'} />
                <Row label="Sharpe" value={backtestResult.sharpe_ratio?.toFixed(2)} />
                <Row label="Drawdown" value={`${(backtestResult.max_drawdown * 100).toFixed(1)}%`} color="text-phoenix-error" />
                <Row label="Win Rate" value={`${(backtestResult.win_rate * 100).toFixed(1)}%`} color="text-phoenix-success" />
              </div>
            )}
          </div>
        </div>

        {/* CENTER — Chart */}
        <div className="col-span-6 flex flex-col gap-4 min-h-0">
          <div className="bg-black/30 border border-white/5 rounded-2xl flex-1 flex flex-col overflow-hidden">
            {/* Chart Tabs */}
            <div className="px-4 py-2 border-b border-white/5 flex items-center justify-between">
              <div className="flex gap-3">
                {(['chart', 'portfolio'] as ChartTab[]).map((tab) => (
                  <button
                    key={tab}
                    onClick={() => setChartTab(tab)}
                    className={`text-[10px] font-mono uppercase tracking-wider transition ${
                      chartTab === tab
                        ? 'text-phoenix-primary border-b border-phoenix-primary pb-1'
                        : 'text-phoenix-muted hover:text-white'
                    }`}
                  >
                    {tab === 'chart' ? 'LIVE CHART' : 'PORTFOLIO'}
                  </button>
                ))}
              </div>
              <div className="flex items-center gap-2">
                <div className="w-2 h-2 rounded-full bg-phoenix-success animate-pulse" />
                <span className="text-[9px] font-mono text-phoenix-muted">LIVE</span>
              </div>
            </div>

            {/* Chart Content */}
            <div className="flex-1 min-h-0">
              {chartTab === 'chart' ? (
                <TradingViewChart
                  theme="dark"
                  symbol={`BINANCE:${selectedSymbol.replace('/', '')}`}
                  interval="D"
                />
              ) : (
                <div className="h-full 