'use client';

import React, { useState, useEffect, useRef, memo } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  Zap, TrendingUp, TrendingDown, RotateCcw, Bot, User, Brain, 
  Shield, Activity, BarChart2, Terminal, Send, Sparkles, DollarSign
} from 'lucide-react';

// --- Native TradingView Component ---
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
        if (symbol === 'BTCUSDT') tvSymbol = 'BINANCE:BTCUSDT';
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
          container_id: "paper_tv_chart",
        });
      }
    };
    document.head.appendChild(script);
  }, [symbol]);
  return <div id="paper_tv_chart" className="w-full h-full" ref={container} />;
});

interface Position {
  symbol: string;
  quantity: number;
  avgPrice: number;
  currentPrice: number;
  pnl: number;
}

export default function PaperTradingPage() {
  const [balance, setBalance] = useState(1000000);
  const [positions, setPositions] = useState<Position[]>([]);
  const [selectedSymbol, setSelectedSymbol] = useState('BTCUSDT');
  const [amount, setAmount] = useState('');
  const [mode, setMode] = useState<'manual' | 'ai' | 'hybrid'>('manual');
  const [logs, setLogs] = useState<string[]>([]);
  const [time, setTime] = useState('');
  
  const [prices, setPrices] = useState({
    'BTCUSDT': 45240.67,
    'ETHUSDT': 1894.30,
    'SOLUSDT': 84.50
  });

  // Clock effect
  useEffect(() => {
    const interval = setInterval(() => {
      setTime(new Date().toLocaleTimeString('en-US', { hour12: false }) + ' UTC');
    }, 1000);
    return () => clearInterval(interval);
  }, []);

  // Price simulation
  useEffect(() => {
    const interval = setInterval(() => {
      setPrices(prev => ({
        'BTCUSDT': prev['BTCUSDT'] + (Math.random() - 0.5) * 50,
        'ETHUSDT': prev['ETHUSDT'] + (Math.random() - 0.5) * 2,
        'SOLUSDT': prev['SOLUSDT'] + (Math.random() - 0.5) * 0.5
      }));
    }, 3000);
    return () => clearInterval(interval);
  }, []);

  // Update positions with current prices
  useEffect(() => {
    setPositions(prev => prev.map(pos => ({
      ...pos,
      currentPrice: prices[pos.symbol as keyof typeof prices],
      pnl: (prices[pos.symbol as keyof typeof prices] - pos.avgPrice) * pos.quantity
    })));
  }, [prices]);

  // AI Bot logic
  useEffect(() => {
    if (mode !== 'ai') return;
    
    const interval = setInterval(() => {
      const symbols = ['BTCUSDT', 'ETHUSDT', 'SOLUSDT'];
      symbols.forEach(symbol => {
        const price = prices[symbol as keyof typeof prices];
        const position = positions.find(p => p.symbol === symbol);
        const random = Math.random();
        
        if (!position && random > 0.7 && balance > price * 0.01) {
          const tradeAmount = Math.min(0.01, balance / price);
          executeTrade(symbol, 'BUY', tradeAmount);
        } else if (position && random > 0.8 && position.quantity > 0) {
          const tradeAmount = Math.min(position.quantity, 0.01);
          executeTrade(symbol, 'SELL', tradeAmount);
        }
      });
    }, 10000);
    
    return () => clearInterval(interval);
  }, [mode, prices, positions, balance]);

  const executeTrade = (symbol: string, type: 'BUY' | 'SELL', tradeAmount: number) => {
    const price = prices[symbol as keyof typeof prices];
    const totalCost = tradeAmount * price;
    
    if (type === 'BUY') {
      if (balance < totalCost) {
        addLog('❌ Insufficient balance to buy ' + tradeAmount + ' ' + symbol);
        return false;
      }
      setBalance(prev => prev - totalCost);
      
      setPositions(prev => {
        const existing = prev.find(p => p.symbol === symbol);
        if (existing) {
          const newQuantity = existing.quantity + tradeAmount;
          const newAvgPrice = ((existing.avgPrice * existing.quantity) + (price * tradeAmount)) / newQuantity;
          return prev.map(p => p.symbol === symbol ? { ...p, quantity: newQuantity, avgPrice: newAvgPrice } : p);
        } else {
          return [...prev, {
            symbol,
            quantity: tradeAmount,
            avgPrice: price,
            currentPrice: price,
            pnl: 0
          }];
        }
      });
      
      addLog('✅ BOUGHT ' + tradeAmount + ' ' + symbol + ' at $' + price.toLocaleString());
    } else {
      const position = positions.find(p => p.symbol === symbol);
      if (!position || position.quantity < tradeAmount) {
        addLog('❌ Insufficient ' + symbol + ' to sell');
        return false;
      }
      
      setBalance(prev => prev + totalCost);
      setPositions(prev => {
        const updated = prev.map(p => p.symbol === symbol ? { ...p, quantity: p.quantity - tradeAmount } : p);
        return updated.filter(p => p.quantity > 0);
      });
      
      addLog('✅ SOLD ' + tradeAmount + ' ' + symbol + ' at $' + price.toLocaleString());
    }
    return true;
  };

  const handleTrade = (type: 'BUY' | 'SELL') => {
    const numAmount = parseFloat(amount);
    if (isNaN(numAmount) || numAmount <= 0) {
      addLog('❌ Please enter a valid amount');
      return;
    }
    executeTrade(selectedSymbol, type, numAmount);
    setAmount('');
  };

  const addLog = (message: string) => {
    const timestamp = new Date().toLocaleTimeString();
    setLogs(prev => ['[' + timestamp + '] ' + message, ...prev.slice(0, 19)]);
  };

  const resetPortfolio = () => {
    setBalance(1000000);
    setPositions([]);
    setLogs([]);
    addLog('🔄 Portfolio reset to $1,000,000');
  };

  const formatUSD = (val: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 0,
      maximumFractionDigits: 2
    }).format(val);
  };

  const totalValue = balance + positions.reduce((sum, pos) => sum + (pos.currentPrice * pos.quantity), 0);
  const totalPnL = totalValue - 1000000;
  const totalPnLPercent = (totalPnL / 1000000) * 100;

  return (
    <div className="min-h-screen bg-gradient-to-br from-[#0a0a0c] via-[#050505] to-[#0a0a0c] text-[#c0caf5] overflow-hidden">
      
      {/* Animated Grid Background */}
      <div className="fixed inset-0 pointer-events-none opacity-20">
        <div className="absolute inset-0 bg-[radial-gradient(circle_at_50%_50%,_#7dcfff_0%,_transparent_50%)] opacity-5" />
        <div className="absolute inset-0" style={{ backgroundImage: 'linear-gradient(to right, #7dcfff0a 1px, transparent 1px), linear-gradient(to bottom, #7dcfff0a 1px, transparent 1px)', backgroundSize: '40px 40px' }} />
      </div>

      <div className="relative z-10 p-6">
        <div className="max-w-7xl mx-auto">
          {/* Header */}
          <motion.div 
            initial={{ y: -20, opacity: 0 }}
            animate={{ y: 0, opacity: 1 }}
            className="mb-8"
          >
            <h1 className="text-3xl font-bold bg-gradient-to-r from-[#c0caf5] to-[#7dcfff] bg-clip-text text-transparent flex items-center gap-3">
              <div className="w-12 h-12 rounded-2xl bg-gradient-to-br from-[#7dcfff]/20 to-[#9B72CB]/20 border border-[#7dcfff]/30 flex items-center justify-center shadow-[0_0_20px_rgba(125,207,255,0.2)]">
                <Zap className="w-6 h-6 text-[#7dcfff]" />
              </div>
              Paper Trading Simulator
            </h1>
            <p className="text-[#565f89] mt-2 font-mono text-sm">Practice trading with virtual funds • Start with $1,000,000</p>
          </motion.div>

          {/* Portfolio Stats - Glass Cards */}
          <motion.div 
            initial={{ y: 20, opacity: 0 }}
            animate={{ y: 0, opacity: 1 }}
            transition={{ delay: 0.1 }}
            className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8"
          >
            {[
              { label: 'Balance', value: formatUSD(balance), color: '#7dcfff' },
              { label: 'Total Value', value: formatUSD(totalValue), color: '#c0caf5' },
              { label: 'PnL', value: (totalPnL >= 0 ? '+' : '') + formatUSD(totalPnL), color: totalPnL >= 0 ? '#9ece6a' : '#f7768e' },
              { label: 'PnL %', value: (totalPnLPercent >= 0 ? '+' : '') + totalPnLPercent.toFixed(2) + '%', color: totalPnLPercent >= 0 ? '#9ece6a' : '#f7768e' }
            ].map((stat, i) => (
              <motion.div
                key={i}
                whileHover={{ scale: 1.02, y: -2 }}
                className="bg-black/30 backdrop-blur-xl border border-[#7dcfff]/10 rounded-2xl p-5 shadow-[0_8px_32px_rgba(0,0,0,0.4)]"
              >
                <div className="text-xs text-[#565f89] font-mono uppercase tracking-wider mb-2">{stat.label}</div>
                <div className="text-2xl font-bold" style={{ color: stat.color }}>{stat.value}</div>
              </motion.div>
            ))}
          </motion.div>

          {/* Trading Mode - Glass Card */}
          <motion.div 
            initial={{ y: 20, opacity: 0 }}
            animate={{ y: 0, opacity: 1 }}
            transition={{ delay: 0.2 }}
            className="bg-black/30 backdrop-blur-xl border border-[#7dcfff]/10 rounded-2xl p-5 mb-8"
          >
            <h3 className="text-[#c0caf5] font-bold mb-4 flex items-center gap-2">
              <Sparkles className="w-4 h-4 text-[#7dcfff]" />
              Trading Mode
            </h3>
            <div className="flex gap-3">
              {(['manual', 'ai', 'hybrid'] as const).map(m => (
                <motion.button
                  key={m}
                  whileHover={{ scale: 1.02 }}
                  whileTap={{ scale: 0.98 }}
                  onClick={() => setMode(m)}
                  className={`flex-1 py-3 rounded-xl transition-all flex items-center justify-center gap-2 text-sm font-mono uppercase tracking-wider ${
                    mode === m 
                      ? 'bg-gradient-to-r from-[#7dcfff]/20 to-[#9B72CB]/20 border border-[#7dcfff]/30 text-[#7dcfff] shadow-[0_0_15px_rgba(125,207,255,0.1)]' 
                      : 'bg-white/5 text-[#565f89] hover:bg-white/10'
                  }`}
                >
                  {m === 'manual' && <User className="w-4 h-4" />}
                  {m === 'ai' && <Bot className="w-4 h-4" />}
                  {m === 'hybrid' && <Brain className="w-4 h-4" />}
                  {m.toUpperCase()}
                </motion.button>
              ))}
            </div>
            <div className="mt-3 text-xs text-[#565f89] font-mono">
              {mode === 'manual' && '🔹 Manual mode: You control all trades'}
              {mode === 'ai' && '🤖 AI mode: Bot trades automatically every 10 seconds'}
              {mode === 'hybrid' && '🧠 Hybrid mode: AI suggests trades, you approve'}
            </div>
          </motion.div>

          {/* Chart Section */}
          <motion.div 
            initial={{ y: 20, opacity: 0 }}
            animate={{ y: 0, opacity: 1 }}
            transition={{ delay: 0.3 }}
            className="bg-black/30 backdrop-blur-xl border border-[#7dcfff]/10 rounded-2xl p-5 mb-8 shadow-[0_8px_32px_rgba(0,0,0,0.4)]"
          >
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-bold bg-gradient-to-r from-[#c0caf5] to-[#7dcfff] bg-clip-text text-transparent">Advanced Chart - {selectedSymbol}</h2>
              <div className="flex gap-2">
                {Object.keys(prices).map(symbol => (
                  <motion.button
                    key={symbol}
                    whileHover={{ scale: 1.05 }}
                    whileTap={{ scale: 0.95 }}
                    onClick={() => setSelectedSymbol(symbol)}
                    className={`px-3 py-1.5 rounded-lg text-xs font-mono transition-all ${
                      selectedSymbol === symbol 
                        ? 'bg-gradient-to-r from-[#7dcfff]/20 to-[#9B72CB]/20 border border-[#7dcfff]/30 text-[#7dcfff]' 
                        : 'bg-white/5 text-[#565f89] hover:bg-white/10'
                    }`}
                  >
                    {symbol}
                  </motion.button>
                ))}
              </div>
            </div>
            
            {/* Price Display */}
            <div className="mb-4">
              <div className="text-3xl font-bold text-[#c0caf5]">
                ${prices[selectedSymbol as keyof typeof prices].toLocaleString()}
              </div>
              <div className="text-xs text-[#565f89] font-mono mt-1">Real-time price • Updated every 3s</div>
            </div>
            
            {/* TradingView Chart */}
            <div className="h-[450px] w-full rounded-xl overflow-hidden">
              <TradingViewChart symbol={selectedSymbol} />
            </div>
          </motion.div>

          {/* Trading Controls & Positions */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
            {/* Place Order */}
            <motion.div 
              initial={{ x: -20, opacity: 0 }}
              animate={{ x: 0, opacity: 1 }}
              transition={{ delay: 0.4 }}
              className="bg-black/30 backdrop-blur-xl border border-[#7dcfff]/10 rounded-2xl p-6"
            >
              <h3 className="text-[#c0caf5] font-bold mb-4 flex items-center gap-2">
                <Terminal className="w-4 h-4 text-[#7dcfff]" />
                Place Order - {selectedSymbol}
              </h3>
              <div className="space-y-4">
                <input
                  type="number"
                  value={amount}
                  onChange={(e) => setAmount(e.target.value)}
                  placeholder="Amount (units)"
                  className="w-full bg-black/50 border border-[#7dcfff]/20 rounded-xl px-4 py-3 text-[#c0caf5] focus:outline-none focus:border-[#7dcfff]/50 transition-all"
                  step="0.001"
                />
                <div className="flex gap-3">
                  <motion.button 
                    whileHover={{ scale: 1.02 }}
                    whileTap={{ scale: 0.98 }}
                    onClick={() => handleTrade('BUY')} 
                    className="flex-1 py-3 bg-gradient-to-r from-[#9ece6a]/20 to-[#9ece6a]/10 border border-[#9ece6a]/30 rounded-xl text-[#9ece6a] hover:shadow-[0_0_20px_rgba(158,206,106,0.2)] transition-all font-bold"
                  >
                    BUY
                  </motion.button>
                  <motion.button 
                    whileHover={{ scale: 1.02 }}
                    whileTap={{ scale: 0.98 }}
                    onClick={() => handleTrade('SELL')} 
                    className="flex-1 py-3 bg-gradient-to-r from-[#f7768e]/20 to-[#f7768e]/10 border border-[#f7768e]/30 rounded-xl text-[#f7768e] hover:shadow-[0_0_20px_rgba(247,118,142,0.2)] transition-all font-bold"
                  >
                    SELL
                  </motion.button>
                  <motion.button 
                    whileHover={{ scale: 1.02 }}
                    whileTap={{ scale: 0.98 }}
                    onClick={resetPortfolio} 
                    className="px-4 py-3 bg-gradient-to-r from-[#ff9e64]/20 to-[#ff9e64]/10 border border-[#ff9e64]/30 rounded-xl text-[#ff9e64] hover:shadow-[0_0_20px_rgba(255,158,100,0.2)] transition-all"
                  >
                    <RotateCcw className="w-4 h-4" />
                  </motion.button>
                </div>
              </div>
            </motion.div>

            {/* Open Positions */}
            <motion.div 
              initial={{ x: 20, opacity: 0 }}
              animate={{ x: 0, opacity: 1 }}
              transition={{ delay: 0.4 }}
              className="bg-black/30 backdrop-blur-xl border border-[#7dcfff]/10 rounded-2xl p-6"
            >
              <h3 className="text-[#c0caf5] font-bold mb-4 flex items-center gap-2">
                <BarChart2 className="w-4 h-4 text-[#9B72CB]" />
                Open Positions
              </h3>
              {positions.length === 0 ? (
                <div className="text-center text-[#565f89] py-8 font-mono text-sm">No open positions</div>
              ) : (
                <div className="space-y-3 max-h-64 overflow-y-auto custom-scrollbar">
                  {positions.map((pos, i) => (
                    <motion.div 
                      key={i}
                      initial={{ opacity: 0, y: 10 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ delay: i * 0.1 }}
                      className="border border-[#7dcfff]/10 rounded-xl p-3 hover:border-[#7dcfff]/30 transition-all"
                    >
                      <div className="flex justify-between mb-2">
                        <span className="text-[#c0caf5] font-bold">{pos.symbol}</span>
                        <span className={pos.pnl >= 0 ? 'text-[#9ece6a]' : 'text-[#f7768e]'}>
                          {pos.pnl >= 0 ? '+' : ''}{formatUSD(pos.pnl)}
                        </span>
                      </div>
                      <div className="text-xs text-[#565f89] font-mono">
                        Qty: {pos.quantity.toFixed(4)} | Avg: {formatUSD(pos.avgPrice)} | Current: {formatUSD(pos.currentPrice)}
                      </div>
                    </motion.div>
                  ))}
                </div>
              )}
            </motion.div>
          </div>

          {/* Activity Log */}
          <motion.div 
            initial={{ y: 20, opacity: 0 }}
            animate={{ y: 0, opacity: 1 }}
            transition={{ delay: 0.5 }}
            className="bg-black/30 backdrop-blur-xl border border-[#7dcfff]/10 rounded-2xl p-6"
          >
            <h3 className="text-[#c0caf5] font-bold mb-3 flex items-center gap-2">
              <Activity className="w-4 h-4 text-[#7dcfff]" />
              Activity Log
            </h3>
            <div className="space-y-1 max-h-48 overflow-y-auto font-mono text-xs custom-scrollbar">
              {logs.length === 0 ? (
                <div className="text-[#565f89] text-center py-4">No activity yet. Start trading!</div>
              ) : (
                logs.map((log, i) => (
                  <motion.div 
                    key={i}
                    initial={{ opacity: 0, x: -10 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: i * 0.02 }}
                    className="text-[#565f89] border-l-2 border-[#7dcfff]/30 pl-3 py-1 hover:border-[#7dcfff] transition-all"
                  >
                    {log}
                  </motion.div>
                ))
              )}
            </div>
          </motion.div>
        </div>
      </div>

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