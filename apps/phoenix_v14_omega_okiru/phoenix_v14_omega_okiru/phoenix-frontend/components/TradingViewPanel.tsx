import { useState } from 'react';
import TradingViewCard from './TradingViewCard';

export default function TradingViewPanel() {
  const [activeTab, setActiveTab] = useState<'crypto' | 'forex' | 'stocks'>('crypto');

  const cryptoPairs = [
    { symbol: 'BTCUSDT', exchange: 'BINANCE', name: 'Bitcoin' },
    { symbol: 'ETHUSDT', exchange: 'BINANCE', name: 'Ethereum' },
    { symbol: 'SOLUSDT', exchange: 'BINANCE', name: 'Solana' },
    { symbol: 'BNBUSDT', exchange: 'BINANCE', name: 'BNB' },
  ];

  const forexPairs = [
    { symbol: 'EURUSD', exchange: 'FX_IDC', name: 'EUR/USD' },
    { symbol: 'GBPUSD', exchange: 'FX_IDC', name: 'GBP/USD' },
    { symbol: 'USDJPY', exchange: 'FX_IDC', name: 'USD/JPY' },
    { symbol: 'USDCHF', exchange: 'FX_IDC', name: 'USD/CHF' },
  ];

  const stockPairs = [
    { symbol: 'AAPL', exchange: 'NASDAQ', name: 'Apple' },
    { symbol: 'MSFT', exchange: 'NASDAQ', name: 'Microsoft' },
    { symbol: 'GOOGL', exchange: 'NASDAQ', name: 'Google' },
    { symbol: 'TSLA', exchange: 'NASDAQ', name: 'Tesla' },
  ];

  const getPairs = () => {
    switch(activeTab) {
      case 'crypto': return cryptoPairs;
      case 'forex': return forexPairs;
      case 'stocks': return stocks;
    }
  };

  return (
    <div className="bg-surface border border-elevated rounded-xl p-4 mt-4">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-cyan font-mono text-sm tracking-wider">📈 MARKET WATCH</h3>
        <div className="flex gap-2">
          <button 
            onClick={() => setActiveTab('crypto')}
            className={`px-3 py-1 text-xs font-mono rounded transition-colors ${
              activeTab === 'crypto' 
                ? 'bg-cyan text-deep' 
                : 'bg-elevated text-white/60 hover:text-white'
            }`}
          >
            ₿ CRYPTO
          </button>
          <button 
            onClick={() => setActiveTab('forex')}
            className={`px-3 py-1 text-xs font-mono rounded transition-colors ${
              activeTab === 'forex' 
                ? 'bg-cyan text-deep' 
                : 'bg-elevated text-white/60 hover:text-white'
            }`}
          >
            💱 FOREX
          </button>
          <button 
            onClick={() => setActiveTab('stocks')}
            className={`px-3 py-1 text-xs font-mono rounded transition-colors ${
              activeTab === 'stocks' 
                ? 'bg-cyan text-deep' 
                : 'bg-elevated text-white/60 hover:text-white'
            }`}
          >
            📊 STOCKS
          </button>
        </div>
      </div>

      <div className="grid grid-cols-2 gap-3">
        {getPairs().map((pair) => (
          <TradingViewCard
            key={pair.symbol}
            symbol={pair.symbol}
            exchange={pair.exchange}
            height={100}
          />
        ))}
      </div>

      <div className="mt-3 text-[10px] text-white/30 text-right font-mono">
        POWERED BY TRADINGVIEW • REAL-TIME
      </div>
    </div>
  );
}
