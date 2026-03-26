// components/TradingViewChart.tsx
'use client';

import React, { useEffect, useRef } from 'react';

interface TradingViewChartProps {
  symbol: string;
  interval?: string;
  theme?: 'dark' | 'light';
  height?: number;
}

declare global {
  interface Window {
    TradingView: any;
  }
}

export const TradingViewChart: React.FC<TradingViewChartProps> = ({ 
  symbol, 
  interval = "15", 
  theme = "dark",
  height = 400
}) => {
  const container = useRef<HTMLDivElement>(null);
  const widgetRef = useRef<any>(null);

  useEffect(() => {
    if (!container.current) return;
    
    // Clear previous content
    if (widgetRef.current) {
      container.current.innerHTML = '';
      widgetRef.current = null;
    }
    
    // Map symbol to TradingView format
    let tvSymbol = symbol;
    if (symbol === 'BTC/PHP') tvSymbol = 'BINANCE:BTCUSDT';
    else if (symbol === 'ETH/PHP') tvSymbol = 'BINANCE:ETHUSDT';
    else if (symbol === 'SOL/PHP') tvSymbol = 'BINANCE:SOLUSDT';
    else if (symbol === 'BTCUSDT') tvSymbol = 'BINANCE:BTCUSDT';
    else if (symbol === 'ETHUSDT') tvSymbol = 'BINANCE:ETHUSDT';
    else if (symbol === 'SOLUSDT') tvSymbol = 'BINANCE:SOLUSDT';

    const script = document.createElement("script");
    script.src = "https://s3.tradingview.com/tv.js";
    script.async = true;
    script.onload = () => {
      if (window.TradingView && container.current) {
        try {
          widgetRef.current = new window.TradingView.widget({
            autosize: true,
            symbol: tvSymbol,
            interval: interval,
            timezone: "Etc/UTC",
            theme: theme,
            style: "1",
            locale: "en",
            enable_publishing: false,
            hide_side_toolbar: false,
            allow_symbol_change: true,
            container_id: container.current.id,
            studies: ["MASimple@tv-basicstudies"],
          });
        } catch (error) {
          console.error('TradingView widget error:', error);
        }
      }
    };
    
    document.head.appendChild(script);
    
    return () => {
      if (widgetRef.current) {
        widgetRef.current = null;
      }
    };
  }, [symbol, interval, theme]);

  return (
    <div 
      id={`tv-chart-${symbol.replace('/', '-')}`}
      ref={container} 
      style={{ width: '100%', height: `${height}px` }}
      className="rounded-lg overflow-hidden"
    />
  );
};

export default TradingViewChart;