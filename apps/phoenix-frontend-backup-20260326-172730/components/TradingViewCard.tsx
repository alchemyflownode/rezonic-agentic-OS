import { useEffect, useRef } from 'react';

interface TradingViewCardProps {
  symbol: string;
  exchange?: string;
  width?: number | 'full';
  height?: number;
  colorTheme?: 'light' | 'dark';
  isTransparent?: boolean;
  locale?: string;
}

export default function TradingViewCard({ 
  symbol, 
  exchange = "BINANCE",
  width = 'full',
  height = 120,
  colorTheme = 'dark',
  isTransparent = true,
  locale = "en"
}: TradingViewCardProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const fullSymbol = exchange ? `${exchange}:${symbol}` : symbol;

  useEffect(() => {
    if (!containerRef.current) return;

    const script = document.createElement('script');
    script.src = 'https://s3.tradingview.com/external-embedding/embed-widget-single-quote.js';
    script.async = true;
    script.innerHTML = JSON.stringify({
      symbol: fullSymbol,
      width: width === 'full' ? '100%' : width,
      height: height,
      colorTheme: colorTheme,
      isTransparent: isTransparent,
      locale: locale
    });

    containerRef.current.appendChild(script);

    return () => {
      if (containerRef.current) {
        containerRef.current.innerHTML = '';
      }
    };
  }, [fullSymbol, width, height, colorTheme, isTransparent, locale]);

  return (
    <div className="bg-surface border border-elevated rounded-xl p-2">
      <div ref={containerRef} className="tradingview-widget-container" />
    </div>
  );
}
