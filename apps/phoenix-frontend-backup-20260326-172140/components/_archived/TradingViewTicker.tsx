import { useEffect, useRef } from 'react';

interface TradingViewTickerProps {
  symbols?: string[][];
  colorTheme?: 'light' | 'dark';
}

export default function TradingViewTicker({ 
  symbols = [
    ["BTC/USDT", "BINANCE"],
    ["ETH/USDT", "BINANCE"],
    ["SOL/USDT", "BINANCE"],
    ["BNB/USDT", "BINANCE"],
    ["EUR/USD", "FX_IDC"],
    ["GBP/USD", "FX_IDC"],
    ["USD/JPY", "FX_IDC"],
    ["AAPL", "NASDAQ"],
    ["MSFT", "NASDAQ"],
    ["GOOGL", "NASDAQ"]
  ],
  colorTheme = 'dark'
}: TradingViewTickerProps) {
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!containerRef.current) return;

    const script = document.createElement('script');
    script.src = 'https://s3.tradingview.com/external-embedding/embed-widget-ticker-tape.js';
    script.async = true;
    script.innerHTML = JSON.stringify({
      symbols: symbols,
      showSymbolLogo: true,
      colorTheme: colorTheme,
      isTransparent: true,
      displayMode: "adaptive",
      locale: "en"
    });

    containerRef.current.appendChild(script);

    return () => {
      if (containerRef.current) {
        containerRef.current.innerHTML = '';
      }
    };
  }, [symbols, colorTheme]);

  return <div ref={containerRef} className="tradingview-widget-container" />;
}
