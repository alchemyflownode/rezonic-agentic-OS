'use client';

import { useState, useEffect } from 'react';
import { TrendingUp, Wallet, RefreshCw } from 'lucide-react';
import { phoenixFetch } from '@/lib/phoenix-client';

interface Portfolio {
  balance: number;
  positions: Record<string, number>;
  total_value: number;
  trade_count: number;
}

export default function PortfolioView() {
  const [portfolio, setPortfolio] = useState<Portfolio | null>(null);
  const [loading, setLoading] = useState(true);

  const fetchPortfolio = async () => {
    const result = await phoenixFetch('/portfolio');
    if (result?.content) {
      try {
        const data = JSON.parse(result.content.replace(/\\/g, ''));
        setPortfolio(data);
      } catch (e) {}
    }
    setLoading(false);
  };

  useEffect(() => {
    fetchPortfolio();
    const interval = setInterval(fetchPortfolio, 5000);
    return () => clearInterval(interval);
  }, []);

  if (loading) {
    return (
      <div className="bg-black/30 backdrop-blur-xl border border-[#7dcfff]/10 rounded-xl p-5 animate-pulse">
        Loading portfolio...
      </div>
    );
  }

  return (
    <div className="bg-black/30 backdrop-blur-xl border border-[#7dcfff]/10 rounded-xl p-5">
      <div className="flex items-center justify-between mb-4">
        <h3 className="font-bold flex items-center gap-2">
          <Wallet className="w-4 h-4 text-[#7dcfff]" />
          Portfolio
        </h3>
        <span className="text-xs text-gray-400">{portfolio?.trade_count || 0} trades</span>
      </div>
      
      <div className="grid grid-cols-2 gap-4 mb-4">
        <div>
          <div className="text-xs text-gray-400">Balance</div>
          <div className="text-xl font-bold text-[#7dcfff]">${portfolio?.balance?.toLocaleString() || '0'}</div>
        </div>
        <div>
          <div className="text-xs text-gray-400">Total Value</div>
          <div className="text-xl font-bold text-white">${portfolio?.total_value?.toLocaleString() || '0'}</div>
        </div>
      </div>
      
      {portfolio?.positions && Object.keys(portfolio.positions).length > 0 ? (
        <div className="space-y-2">
          <div className="text-xs text-gray-400">Open Positions</div>
          {Object.entries(portfolio.positions).map(([symbol, amount]) => (
            <div key={symbol} className="flex justify-between items-center p-2 bg-white/5 rounded-lg">
              <span className="font-mono text-[#9ece6a]">{symbol}</span>
              <span className="text-white">{amount.toFixed(4)} units</span>
            </div>
          ))}
        </div>
      ) : (
        <div className="text-center text-gray-500 py-4 text-sm">No open positions</div>
      )}
      
      <button
        onClick={fetchPortfolio}
        className="mt-4 w-full py-2 bg-white/5 rounded-lg hover:bg-white/10 transition flex items-center justify-center gap-2 text-sm"
      >
        <RefreshCw className="w-3 h-3" />
        Refresh
      </button>
    </div>
  );
}
