'use client';

import { useState, useEffect, useCallback } from 'react';
import { paperTrading } from '@/app/lib/paperTrading';

export interface PaperTrade {
  id: string;
  symbol: string;
  type: 'BUY' | 'SELL';
  amount: number;
  price: number;
  timestamp: number;
}

export interface PaperPortfolio {
  balance: number;
  totalValue: number;
  totalPnL: number;
  totalPnLPercent: number;
  positions: Array<{
    symbol: string;
    quantity: number;
    avgPrice: number;
    currentPrice: number;
    pnl: number;
  }>;
}

export function usePaperTrading() {
  const [portfolio, setPortfolio] = useState<PaperPortfolio>(paperTrading.getPortfolio());
  const [trades, setTrades] = useState<PaperTrade[]>(paperTrading.getTrades());
  const [mode, setMode] = useState(paperTrading.getBotStatus().mode);
  const [botActive, setBotActive] = useState(paperTrading.getBotStatus().active);

  useEffect(() => {
    const interval = setInterval(() => {
      setPortfolio(paperTrading.getPortfolio());
      setTrades(paperTrading.getTrades());
      const status = paperTrading.getBotStatus();
      setMode(status.mode);
      setBotActive(status.active);
    }, 1000);
    
    return () => clearInterval(interval);
  }, []);

  const executeTrade = useCallback((symbol: string, type: 'BUY' | 'SELL', amount: number) => {
    return paperTrading.executeTrade({ symbol, type, amount, orderType: 'market' });
  }, []);

  const setTradingMode = useCallback((newMode: 'manual' | 'ai' | 'hybrid') => {
    paperTrading.setMode(newMode);
    setMode(newMode);
  }, []);

  const resetPortfolio = useCallback(() => {
    paperTrading.resetPortfolio();
  }, []);

  return {
    portfolio,
    trades,
    mode,
    botActive,
    executeTrade,
    setTradingMode,
    resetPortfolio
  };
}
