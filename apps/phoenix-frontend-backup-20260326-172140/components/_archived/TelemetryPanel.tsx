'use client';

import React, { useEffect, useState } from 'react';
import { motion } from 'framer-motion';
import { Cpu, HardDrive, Zap, Terminal } from 'lucide-react';

interface TelemetryData {
  cpu: number;
  ram: number;
  gpuTemp: number;
  networkDown: number;
  networkUp: number;
}

export const TelemetryPanel = React.memo(() => {
  const [stats, setStats] = useState<TelemetryData>({
    cpu: 0,
    ram: 0,
    gpuTemp: 45,
    networkDown: 0,
    networkUp: 0
  });
  const [gpuBars, setGpuBars] = useState<number[]>(Array(22).fill(20));

  // Separate SSE connection just for telemetry
  useEffect(() => {
    const eventSource = new EventSource('http://localhost:8001/kernel/telemetry');
    
    eventSource.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        setStats({
          cpu: data.cpu,
          ram: data.ram,
          gpuTemp: data.gpuTemp,
          networkDown: data.networkDown,
          networkUp: data.networkUp
        });
      } catch (e) {}
    };

    return () => eventSource.close();
  }, []);

  // GPU bars animation (isolated from main render cycle)
  useEffect(() => {
    const interval = setInterval(() => {
      setGpuBars(prev => prev.map(() => 
        Math.min(100, Math.max(20, stats.cpu) + Math.random() * 40)
      ));
    }, 800);
    return () => clearInterval(interval);
  }, [stats.cpu]);

  return (
    <motion.div 
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      className="bg-[#0E1015]/90 backdrop-blur-md border border-[#1F222A] rounded-xl p-5 shadow-[0_8px_30px_rgba(0,0,0,0.5)]"
    >
      <div className="flex items-center justify-between mb-5">
        <div className="flex items-center gap-2 text-xs font-bold tracking-[0.15em] uppercase text-white">
          <div className="text-[#B388FF] drop-shadow-[0_0_5px_#B388FF]"><Cpu size={14} /></div> System Telemetry
        </div>
      </div>

      <div className="grid grid-cols-2 gap-4 mb-4">
        <div>
          <div className="text-[9px] text-[#8A8F9B] font-mono mb-1">CPU</div>
          <div className={`text-sm font-mono ${stats.cpu > 80 ? 'text-[#FF4500]' : 'text-white'}`}>
            {stats.cpu}%
          </div>
        </div>
        <div>
          <div className="text-[9px] text-[#8A8F9B] font-mono mb-1">RAM</div>
          <div className={`text-sm font-mono ${stats.ram > 85 ? 'text-[#FF4500]' : 'text-white'}`}>
            {stats.ram}%
          </div>
        </div>
        <div>
          <div className="text-[9px] text-[#8A8F9B] font-mono mb-1">GPU</div>
          <div className="text-sm font-mono text-white">{stats.gpuTemp}°C</div>
        </div>
        <div>
          <div className="text-[9px] text-[#8A8F9B] font-mono mb-1">NET</div>
          <div className="text-xs font-mono text-white">
            ↓{stats.networkDown} ↑{stats.networkUp} MB/s
          </div>
        </div>
      </div>

      {/* GPU Bars */}
      <div className="h-20 flex items-end justify-between gap-1.5">
        {gpuBars.map((height, i) => (
          <motion.div
            key={i}
            className="w-full rounded-t-sm bg-gradient-to-t from-[#FF9800] to-[#FF4500]"
            animate={{ height: `${height}%` }}
            transition={{ duration: 0.5, ease: "easeInOut" }}
            style={{ opacity: 0.3 + (i / gpuBars.length) * 0.7 }}
          />
        ))}
      </div>
    </motion.div>
  );
});

TelemetryPanel.displayName = 'TelemetryPanel';