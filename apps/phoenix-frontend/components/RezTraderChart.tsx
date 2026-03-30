// components/RezTraderChart.tsx
'use client';

import React from 'react';
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, LineChart, Line } from 'recharts';

interface RezTraderChartProps {
  data: Array<{ time: string; price: number; volume?: number }>;
  title?: string;
  height?: number;
  showVolume?: boolean;
}

export function RezTraderChart({ data, title, height = 400, showVolume = false }: RezTraderChartProps) {
  if (!data || data.length === 0) {
    return (
      <div className="flex items-center justify-center h-full bg-[#0a0a0c] rounded-lg border border-white/5">
        <div className="text-center">
          <div className="w-12 h-12 mx-auto mb-3 rounded-full bg-[#00E5FF]/10 flex items-center justify-center">
            <svg className="w-6 h-6 text-[#00E5FF]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
            </svg>
          </div>
          <p className="text-zinc-500 text-sm font-mono">Waiting for market data...</p>
          <p className="text-zinc-600 text-xs font-mono mt-1">Connect to kernel to see real-time charts</p>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-[#0a0a0c] rounded-lg border border-white/5 p-4">
      {title && (
        <div className="mb-4">
          <h3 className="text-sm font-mono text-[#00E5FF] uppercase tracking-wider">{title}</h3>
        </div>
      )}
      <ResponsiveContainer width="100%" height={height}>
        <AreaChart data={data}>
          <defs>
            <linearGradient id="colorPrice" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="#00E5FF" stopOpacity={0.3} />
              <stop offset="95%" stopColor="#00E5FF" stopOpacity={0} />
            </linearGradient>
          </defs>
          <CartesianGrid strokeDasharray="3 3" stroke="#ffffff10" vertical={false} />
          <XAxis 
            dataKey="time" 
            stroke="#52525b" 
            fontSize={10} 
            tickLine={false} 
            axisLine={false}
          />
          <YAxis 
            stroke="#52525b" 
            fontSize={10} 
            tickLine={false} 
            axisLine={false}
            tickFormatter={(val) => `₱${(val / 1000).toFixed(0)}K`}
          />
          <Tooltip 
            contentStyle={{ 
              backgroundColor: '#0a0a0c', 
              border: '1px solid rgba(0,229,255,0.2)',
              borderRadius: '8px',
              fontSize: '10px'
            }}
            labelStyle={{ color: '#00E5FF' }}
          />
          <Area 
            type="monotone" 
            dataKey="price" 
            stroke="#00E5FF" 
            fillOpacity={1} 
            fill="url(#colorPrice)" 
            strokeWidth={2}
          />
        </AreaChart>
      </ResponsiveContainer>
      {showVolume && data[0]?.volume && (
        <div className="mt-4 pt-4 border-t border-white/5">
          <ResponsiveContainer width="100%" height={80}>
            <AreaChart data={data}>
              <Area 
                type="monotone" 
                dataKey="volume" 
                stroke="#9B72CB" 
                fill="#9B72CB20" 
                strokeWidth={1}
              />
            </AreaChart>
          </ResponsiveContainer>
        </div>
      )}
    </div>
  );
}
