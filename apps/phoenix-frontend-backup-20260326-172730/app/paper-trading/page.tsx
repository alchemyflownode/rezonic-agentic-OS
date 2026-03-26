// app/paper-trading/page.tsx
'use client';

import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  Wallet, TrendingUp, TrendingDown, Activity, 
  RefreshCw, Clock, BarChart3, AlertCircle,
  CheckCircle2, XCircle, Zap, Shield, Brain,
  Calculator, LineChart, PieChart, Target, History,
  ArrowUpRight, ArrowDownRight, Play, StopCircle
} from 'lucide-react';
import Link from 'next/link';
import { usePhoenix, useAutoRefresh } from '@/hooks/usePhoenix';
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';

export default function PaperTradingPage() {
  const {
    connected,
    portfolio,
    executeTrade,
    fetchPortfolio,
    runBacktest,
    marketData,
    isLoading,
  } = usePhoenix();

  const [selectedStrategy, setSelectedStrategy] = useState('moving_average');
  const [backtestResult, setBacktestResult] = useState<any>(null);
  const [isBacktesting, setIsBacktesting] = useState(false);
  const [tradeAmount, setTradeAmount] = useState('1000');
  const [selectedSymbol, setSelectedSymbol] = useState('BTC/PHP');
  const [simulationMode, setSimulationMode] = useState<'manual' | 'auto'>('manual');
  const [simulationActive, setSimulationActive] = useState(false);
  const [simulationTrades, setSimulationTrades] = useState<any[]>([]);
  const [portfolioHistory, setPortfolioHistory] = useState<any[]>([
    { time: '00:00', value: 1000000 },
    { time: '04:00', value: 1012000 },
    { time: '08:00', value: 1008000 },
    { time: '12:00', value: 1025000 },
    { time: '16:00', value: 1045678 },
  ]);

  useAutoRefresh(5000);

  useEffect(() => {
    fetchPortfolio();
  }, []);

  // Update portfolio history when balance changes
  useEffect(() => {
    setPortfolioHistory(prev => [
      ...prev.slice(-19),
      { 
        time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }), 
        value: portfolio.balance 
      }
    ]);
  }, [portfolio.balance]);

  const symbols = [
    { name: 'BTC/PHP', price: marketData[0]?.btcPrice || 4524067, change: 2.46, volume: '1.2B' },
    { name: 'ETH/PHP', price: marketData[0]?.ethPrice || 189430, change: -1.21, volume: '890M' },
    { name: 'SOL/PHP', price: 8450, change: 5.68, volume: '450M' },
  ];

  const strategies = [
    { id: 'moving_average', name: 'Moving Average Crossover', description: 'Buy when MA50 crosses above MA200', winRate: 68.5, trades: 142 },
    { id: 'rsi', name: 'RSI Mean Reversion', description: 'Buy when RSI < 30, sell when RSI > 70', winRate: 58.2, trades: 98 },
    { id: 'bollinger', name: 'Bollinger Bands', description: 'Buy at lower band, sell at upper band', winRate: 62.3, trades: 215 },
    { id: 'momentum', name: 'Momentum Strategy', description: 'Follow the trend with 20-day momentum', winRate: 71.2, trades: 87 },
  ];

  const formatPHP = (val: number) => new Intl.NumberFormat('en-PH', {
    style: 'currency', currency: 'PHP', minimumFractionDigits: 0, maximumFractionDigits: 0
  }).format(val).replace('PHP', '₱');

  const handleRunBacktest = async () => {
    setIsBacktesting(true);
    const result = await runBacktest(selectedStrategy);
    setBacktestResult(result);
    setIsBacktesting(false);
  };

  const handlePaperTrade = async (action: 'buy' | 'sell') => {
    const amountNum = parseFloat(tradeAmount);
    if (isNaN(amountNum) || amountNum <= 0) return;
    
    const symbol = symbols.find(s => s.name === selectedSymbol);
    const quantity = amountNum / (symbol?.price || 1);
    
    const success = await executeTrade(action, selectedSymbol, quantity, symbol?.price);
    
    if (success && simulationMode === 'auto') {
      setSimulationTrades(prev => [{
        id: Date.now(),
        action,
        symbol: selectedSymbol,
        amount: quantity,
        price: symbol?.price,
        time: new Date().toLocaleTimeString(),
        reason: 'Manual override in auto mode'
      }, ...prev.slice(0, 9)]);
    }
  };

  const startSimulation = () => {
    setSimulationActive(true);
    setSimulationTrades([]);
  };

  const stopSimulation = () => {
    setSimulationActive(false);
  };

  const currentSymbol = symbols.find(s => s.name === selectedSymbol);
  const selectedStrategyData = strategies.find(s => s.id === selectedStrategy);

  return (
    <div className="min-h-screen bg-gradient-to-br from-[#0a0a0c] via-[#050505] to-[#0a0a0c] text-[#c0caf5]">
      {/* Animated Background */}
      <div className="fixed inset-0 pointer-events-none opacity-20">
        <div className="absolute inset-0 bg-[radial-gradient(circle_at_50%_50%,_#7dcfff_0%,_transparent_50%)] opacity-5" />
        <div className="absolute inset-0" style={{ backgroundImage: 'linear-gradient(to right, #7dcfff0a 1px, transparent 1px), linear-gradient(to bottom, #7dcfff0a 1px, transparent 1px)', backgroundSize: '40px 40px' }} />
      </div>

      {/* Header */}
      <header className="sticky top-0 z-10 bg-black/40 backdrop-blur-xl border-b border-[#7dcfff]/10">
        <div className="container mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-[#9ece6a]/20 to-[#7dcfff]/20 flex items-center justify-center">
                <Calculator className="w-5 h-5 text-[#9ece6a]" />
              </div>
              <div>
                <h1 className="text-xl font-bold">Paper Trading • Simulation Lab</h1>
                <p className="text-xs text-[#565f89]">Risk-free strategy testing with real-time market data</p>
              </div>
            </div>
            <div className="flex items-center gap-4">
              <Link href="/trading">
                <button className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-[#7dcfff]/10 border border-[#7dcfff]/20 text-[10px] text-[#7dcfff] hover:bg-[#7dcfff]/20 transition">
                  <TrendingUp className="w-3 h-3" />
                  Live Trading
                </button>
              </Link>
              <div className={`flex items-center gap-2 px-3 py-1.5 rounded-full ${connected ? 'bg-[#9ece6a]/10 border border-[#9ece6a]/20' : 'bg-[#f7768e]/10 border border-[#f7768e]/20'}`}>
                <div className={`w-2 h-2 rounded-full ${connected ? 'bg-[#9ece6a] animate-pulse' : 'bg-[#f7768e]'}`} />
                <span className={`text-xs font-mono ${connected ? 'text-[#9ece6a]' : 'text-[#f7768e]'}`}>
                  {connected ? 'SIMULATION MODE' : 'OFFLINE'}
                </span>
              </div>
            </div>
          </div>
        </div>
      </header>

      <main className="container mx-auto px-6 py-8">
        {/* Portfolio Summary */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
          <div className="bg-gradient-to-br from-[#9ece6a]/10 to-[#7dcfff]/10 rounded-2xl p-5 border border-[#9ece6a]/20">
            <div className="flex items-center gap-2 mb-2">
              <Wallet className="w-4 h-4 text-[#9ece6a]" />
              <span className="text-xs text-[#565f89]">Paper Balance</span>
            </div>
            <div className="text-2xl font-bold">{formatPHP(portfolio.balance)}</div>
            <div className="text-[10px] text-[#565f89] mt-1">Virtual funds</div>
          </div>
          <div className="bg-gradient-to-br from-[#7dcfff]/10 to-[#9B72CB]/10 rounded-2xl p-5 border border-[#7dcfff]/20">
            <div className="flex items-center gap-2 mb-2">
              <BarChart3 className="w-4 h-4 text-[#7dcfff]" />
              <span className="text-xs text-[#565f89]">Total Value</span>
            </div>
            <div className="text-2xl font-bold">{formatPHP(portfolio.total_value)}</div>
            <div className="text-[10px] text-[#565f89] mt-1">+ positions</div>
          </div>
          <div className="bg-gradient-to-br from-[#9B72CB]/10 to-[#7dcfff]/10 rounded-2xl p-5 border border-[#9B72CB]/20">
            <div className="flex items-center gap-2 mb-2">
              <Target className="w-4 h-4 text-[#9B72CB]" />
              <span className="text-xs text-[#565f89]">Open Positions</span>
            </div>
            <div className="text-2xl font-bold">{Object.keys(portfolio.positions).length}</div>
            <div className="text-[10px] text-[#565f89] mt-1">Active trades</div>
          </div>
          <div className="bg-gradient-to-br from-[#9ece6a]/10 to-[#9B72CB]/10 rounded-2xl p-5 border border-[#9ece6a]/20">
            <div className="flex items-center gap-2 mb-2">
              <History className="w-4 h-4 text-[#9ece6a]" />
              <span className="text-xs text-[#565f89]">Sim Trades</span>
            </div>
            <div className="text-2xl font-bold">{simulationTrades.length}</div>
            <div className="text-[10px] text-[#565f89] mt-1">This session</div>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Trading Panel - Left */}
          <div className="lg:col-span-2 space-y-6">
            {/* Portfolio Chart */}
            <div className="bg-black/30 backdrop-blur-xl border border-[#7dcfff]/10 rounded-2xl p-6">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-lg font-bold flex items-center gap-2">
                  <LineChart className="w-5 h-5 text-[#7dcfff]" />
                  Portfolio Growth (Simulated)
                </h2>
                <div className="flex items-center gap-2">
                  <div className={`w-2 h-2 rounded-full ${simulationActive ? 'bg-[#9ece6a] animate-pulse' : 'bg-[#565f89]'}`} />
                  <span className="text-[10px] font-mono text-[#565f89]">
                    {simulationActive ? 'SIMULATION ACTIVE' : 'SIMULATION IDLE'}
                  </span>
                </div>
              </div>
              <div className="h-64">
                <ResponsiveContainer width="100%" height="100%">
                  <AreaChart data={portfolioHistory}>
                    <defs>
                      <linearGradient id="paperValue" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%" stopColor="#9ece6a" stopOpacity={0.3}/>
                        <stop offset="95%" stopColor="#9ece6a" stopOpacity={0}/>
                      </linearGradient>
                    </defs>
                    <CartesianGrid strokeDasharray="3 3" stroke="#ffffff05" vertical={false} />
                    <XAxis dataKey="time" stroke="#52525b" fontSize={10} tickLine={false} axisLine={false} />
                    <YAxis stroke="#52525b" fontSize={10} tickLine={false} axisLine={false} tickFormatter={(val) => `${(val/1000000).toFixed(1)}M`} />
                    <Tooltip contentStyle={{ backgroundColor: '#0a0a0c', border: '1px solid rgba(255,255,255,0.1)', borderRadius: '8px' }} />
                    <Area type="monotone" dataKey="value" stroke="#9ece6a" fillOpacity={1} fill="url(#paperValue)" strokeWidth={2} />
                  </AreaChart>
                </ResponsiveContainer>
              </div>
            </div>

            {/* Quick Trade */}
            <div className="bg-black/30 backdrop-blur-xl border border-[#7dcfff]/10 rounded-2xl p-6">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-lg font-bold flex items-center gap-2">
                  <Zap className="w-5 h-5 text-[#7dcfff]" />
                  Paper Trade
                </h2>
                <div className="flex items-center gap-2 bg-black/30 rounded-lg p-1">
                  <button
                    onClick={() => setSimulationMode('manual')}
                    className={`px-3 py-1 rounded-md text-[10px] font-mono transition ${
                      simulationMode === 'manual' ? 'bg-[#7dcfff]/20 text-[#7dcfff]' : 'text-[#565f89] hover:text-white'
                    }`}
                  >
                    Manual
                  </button>
                  <button
                    onClick={() => setSimulationMode('auto')}
                    className={`px-3 py-1 rounded-md text-[10px] font-mono transition ${
                      simulationMode === 'auto' ? 'bg-[#9ece6a]/20 text-[#9ece6a]' : 'text-[#565f89] hover:text-white'
                    }`}
                  >
                    Auto Sim
                  </button>
                </div>
              </div>
              
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
                <div>
                  <label className="text-xs text-[#565f89] block mb-1">Symbol</label>
                  <select
                    value={selectedSymbol}
                    onChange={(e) => setSelectedSymbol(e.target.value)}
                    className="w-full bg-black/50 border border-[#7dcfff]/20 rounded-xl px-4 py-2 text-sm outline-none focus:border-[#7dcfff]/50"
                  >
                    {symbols.map(s => (
                      <option key={s.name} value={s.name}>{s.name}</option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="text-xs text-[#565f89] block mb-1">Amount (PHP)</label>
                  <input
                    type="number"
                    value={tradeAmount}
                    onChange={(e) => setTradeAmount(e.target.value)}
                    step="100"
                    min="100"
                    className="w-full bg-black/50 border border-[#7dcfff]/20 rounded-xl px-4 py-2 text-sm outline-none focus:border-[#7dcfff]/50"
                  />
                </div>
                <div>
                  <label className="text-xs text-[#565f89] block mb-1">Est. Quantity</label>
                  <div className="w-full bg-black/50 border border-[#7dcfff]/20 rounded-xl px-4 py-2 text-sm text-[#c0caf5]">
                    {currentSymbol ? (parseFloat(tradeAmount) / currentSymbol.price).toFixed(6) : '0'}
                  </div>
                </div>
              </div>

              <div className="flex gap-3">
                <button
                  onClick={() => handlePaperTrade('buy')}
                  disabled={!connected}
                  className="flex-1 py-3 rounded-xl bg-gradient-to-r from-[#9ece6a] to-[#7dcfff] text-black font-bold hover:opacity-90 transition disabled:opacity-50"
                >
                  BUY
                </button>
                <button
                  onClick={() => handlePaperTrade('sell')}
                  disabled={!connected}
                  className="flex-1 py-3 rounded-xl bg-gradient-to-r from-[#f7768e] to-[#ff9e64] text-black font-bold hover:opacity-90 transition disabled:opacity-50"
                >
                  SELL
                </button>
              </div>

              {simulationMode === 'auto' && (
                <div className="mt-4 pt-4 border-t border-[#7dcfff]/10">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <Brain className="w-4 h-4 text-[#9B72CB]" />
                      <span className="text-xs text-[#565f89]">Auto Simulation</span>
                    </div>
                    {!simulationActive ? (
                      <button
                        onClick={startSimulation}
                        className="px-4 py-1.5 rounded-lg bg-[#9ece6a]/20 text-[#9ece6a] text-xs font-mono hover:bg-[#9ece6a]/30 transition flex items-center gap-1"
                      >
                        <Play className="w-3 h-3" />
                        Start Auto Trading
                      </button>
                    ) : (
                      <button
                        onClick={stopSimulation}
                        className="px-4 py-1.5 rounded-lg bg-[#f7768e]/20 text-[#f7768e] text-xs font-mono hover:bg-[#f7768e]/30 transition flex items-center gap-1"
                      >
                        <StopCircle className="w-3 h-3" />
                        Stop Simulation
                      </button>
                    )}
                  </div>
                  {simulationActive && (
                    <p className="text-[8px] text-[#9ece6a] mt-2 animate-pulse">
                      AI bot executing {selectedStrategyData?.name} strategy...
                    </p>
                  )}
                </div>
              )}
            </div>

            {/* Market Data */}
            <div className="bg-black/30 backdrop-blur-xl border border-[#7dcfff]/10 rounded-2xl p-6">
              <h2 className="text-lg font-bold mb-4 flex items-center gap-2">
                <Activity className="w-5 h-5 text-[#7dcfff]" />
                Live Market Data
              </h2>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                {symbols.map(symbol => (
                  <div key={symbol.name} className="bg-white/5 rounded-lg p-3">
                    <div className="flex justify-between items-start mb-2">
                      <span className="font-mono text-sm">{symbol.name}</span>
                      <span className={`text-xs ${symbol.change >= 0 ? 'text-[#9ece6a]' : 'text-[#f7768e]'}`}>
                        {symbol.change >= 0 ? '+' : ''}{symbol.change}%
                      </span>
                    </div>
                    <div className="text-lg font-bold">{formatPHP(symbol.price)}</div>
                    <div className="text-[9px] text-[#565f89] mt-1">Vol: {symbol.volume}</div>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* Strategy Panel - Right */}
          <div className="space-y-6">
            {/* Backtest */}
            <div className="bg-black/30 backdrop-blur-xl border border-[#7dcfff]/10 rounded-2xl p-6">
              <h2 className="text-lg font-bold mb-4 flex items-center gap-2">
                <Clock className="w-5 h-5 text-[#9B72CB]" />
                Strategy Backtest
              </h2>
              
              <select
                value={selectedStrategy}
                onChange={(e) => setSelectedStrategy(e.target.value)}
                className="w-full bg-black/50 border border-[#7dcfff]/20 rounded-xl px-4 py-2 text-sm outline-none focus:border-[#7dcfff]/50 mb-3"
              >
                {strategies.map(s => (
                  <option key={s.id} value={s.id}>{s.name}</option>
                ))}
              </select>
              
              <div className="flex justify-between text-xs text-[#565f89] mb-3">
                <span>Win Rate: {selectedStrategyData?.winRate}%</span>
                <span>Trades: {selectedStrategyData?.trades}</span>
              </div>
              
              <p className="text-xs text-[#565f89] mb-4">
                {strategies.find(s => s.id === selectedStrategy)?.description}
              </p>
              
              <button
                onClick={handleRunBacktest}
                disabled={isBacktesting}
                className="w-full py-2 rounded-xl bg-[#7dcfff]/20 border border-[#7dcfff]/30 text-[#7dcfff] hover:bg-[#7dcfff]/30 transition disabled:opacity-50 flex items-center justify-center gap-2"
              >
                {isBacktesting ? (
                  <>
                    <RefreshCw className="w-4 h-4 animate-spin" />
                    Running Simulation...
                  </>
                ) : (
                  <>
                    <RefreshCw className="w-4 h-4" />
                    Run Backtest
                  </>
                )}
              </button>

              {backtestResult && (
                <motion.div
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  className="mt-4 p-4 bg-white/5 rounded-lg space-y-2"
                >
                  <div className="flex justify-between">
                    <span className="text-xs text-[#565f89]">Total Return:</span>
                    <span className={`text-sm font-mono ${backtestResult.total_return >= 0 ? 'text-[#9ece6a]' : 'text-[#f7768e]'}`}>
                      {(backtestResult.total_return * 100).toFixed(1)}%
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-xs text-[#565f89]">Sharpe Ratio:</span>
                    <span className="text-sm font-mono">{backtestResult.sharpe_ratio?.toFixed(2)}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-xs text-[#565f89]">Max Drawdown:</span>
                    <span className="text-sm font-mono text-[#f7768e]">{(backtestResult.max_drawdown * 100).toFixed(1)}%</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-xs text-[#565f89]">Win Rate:</span>
                    <span className="text-sm font-mono text-[#9ece6a]">{(backtestResult.win_rate * 100).toFixed(1)}%</span>
                  </div>
                  <div className="flex justify-between pt-2 border-t border-white/10">
                    <span className="text-xs text-[#565f89]">Projected Balance:</span>
                    <span className="text-sm font-mono text-[#7dcfff]">
                      {formatPHP(portfolio.balance * (1 + (backtestResult.total_return || 0)))}
                    </span>
                  </div>
                </motion.div>
              )}
            </div>

            {/* Open Positions */}
            <div className="bg-black/30 backdrop-blur-xl border border-[#7dcfff]/10 rounded-2xl p-6">
              <h2 className="text-lg font-bold mb-4 flex items-center gap-2">
                <TrendingUp className="w-5 h-5 text-[#9ece6a]" />
                Open Positions
              </h2>
              {Object.keys(portfolio.positions).length === 0 ? (
                <div className="text-center text-[#565f89] py-8">
                  <PieChart className="w-8 h-8 mx-auto mb-2 opacity-50" />
                  No open positions
                </div>
              ) : (
                <div className="space-y-3 max-h-64 overflow-y-auto custom-scrollbar">
                  {Object.entries(portfolio.positions).map(([symbol, amount]) => {
                    const price = symbols.find(s => s.name === symbol)?.price || 0;
                    const value = amount * price;
                    const pnl = value - (amount * 50000); // Simple PnL calc
                    return (
                      <div key={symbol} className="bg-white/5 rounded-lg p-3">
                        <div className="flex justify-between items-center">
                          <span className="font-mono text-sm">{symbol}</span>
                          <span className={`text-xs ${pnl >= 0 ? 'text-[#9ece6a]' : 'text-[#f7768e]'}`}>
                            {pnl >= 0 ? '+' : ''}{formatPHP(pnl)}
                          </span>
                        </div>
                        <div className="flex justify-between text-xs text-[#565f89] mt-1">
                          <span>{amount.toFixed(6)} units</span>
                          <span>{formatPHP(value)}</span>
                        </div>
                      </div>
                    );
                  })}
                </div>
              )}
            </div>

            {/* Simulation Trades */}
            {simulationTrades.length > 0 && (
              <div className="bg-black/30 backdrop-blur-xl border border-[#7dcfff]/10 rounded-2xl p-6">
                <h2 className="text-lg font-bold mb-4 flex items-center gap-2">
                  <History className="w-5 h-5 text-[#9B72CB]" />
                  Simulation Trades
                </h2>
                <div className="space-y-2 max-h-48 overflow-y-auto custom-scrollbar">
                  {simulationTrades.map(trade => (
                    <div key={trade.id} className="flex items-center justify-between text-xs py-2 border-b border-white/5">
                      <div className="flex items-center gap-2">
                        {trade.action === 'BUY' ? (
                          <ArrowUpRight className="w-3 h-3 text-[#9ece6a]" />
                        ) : (
                          <ArrowDownRight className="w-3 h-3 text-[#f7768e]" />
                        )}
                        <span className="font-mono">{trade.symbol}</span>
                        <span className="text-[#565f89]">{trade.amount.toFixed(4)} @ {formatPHP(trade.price)}</span>
                      </div>
                      <span className="text-[8px] text-[#565f89]">{trade.time}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      </main>

      <style jsx global>{`
        .custom-scrollbar::-webkit-scrollbar { width: 4px; }
        .custom-scrollbar::-webkit-scrollbar-track { background: rgba(125,207,255,0.05); border-radius: 10px; }
        .custom-scrollbar::-webkit-scrollbar-thumb { background: rgba(125,207,255,0.3); border-radius: 10px; }
      `}</style>
    </div>
  );
}