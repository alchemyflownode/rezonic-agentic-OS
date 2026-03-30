// components/TradingViewChart.tsx
'use client';

import React, { useEffect, useRef } from 'react';

interface TradingViewChartProps {
  symbol: string;
  theme?: 'dark' | 'light';
  interval?: string;
}

declare global {
  interface Window {
    TradingView: any;
  }
}

export function TradingViewChart({ symbol, theme = 'dark', interval = 'D' }: TradingViewChartProps) {
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    // Load TradingView widget script
    const script = document.createElement('script');
    script.src = 'https://s3.tradingview.com/tv.js';
    script.async = true;
    script.onload = () => {
      if (containerRef.current && window.TradingView) {
        new window.TradingView.widget({
          container_id: containerRef.current.id,
          symbol: symbol,
          interval: interval,
          timezone: 'Etc/UTC',
          theme: theme,
          style: '1',
          locale: 'en',
          toolbar_bg: '#050505',
          enable_publishing: false,
          hide_side_toolbar: false,
          allow_symbol_change: true,
          save_image: false,
          studies: ['MASimple@tv-basicstudies', 'RSI@tv-basicstudies'],
          width: '100%',
          height: '100%',
        });
      }
    };
    document.head.appendChild(script);

    return () => {
      if (script.parentNode) {
        script.parentNode.removeChild(script);
      }
    };
  }, [symbol, theme, interval]);

  return <div id="tradingview_chart" ref={containerRef} style={{ width: '100%', height: '100%' }} />;
}
