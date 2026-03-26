'use client';
import React, { useState, useEffect } from 'react';

export default function V8Dashboard() {
  const [kernelStatus, setKernelStatus] = useState('OFFLINE');
  const [uptime, setUptime] = useState(0);

  useEffect(() => {
    // Check kernel status
    const checkKernel = async () => {
      try {
        const res = await fetch('http://localhost:8003/health');
        if (res.ok) {
          setKernelStatus('ONLINE');
        } else {
          setKernelStatus('OFFLINE');
        }
      } catch {
        setKernelStatus('OFFLINE');
      }
    };

    checkKernel();
    const interval = setInterval(checkKernel, 5000);
    const timer = setInterval(() => setUptime(prev => prev + 1), 1000);

    return () => {
      clearInterval(interval);
      clearInterval(timer);
    };
  }, []);

  const workers = [
    { id: 'auto', name: 'Orchestrator', description: 'Auto-Routing Intent Detection' },
    { id: 'brain', name: 'Brain Worker', description: 'Cognitive Reasoning' },
    { id: 'search', name: 'Web Research', description: 'Live data analysis' },
    { id: 'code', name: 'Automation Tools', description: 'Execute workflows' },
    { id: 'files', name: 'Company Knowledge', description: 'Search internal files' },
    { id: 'vision', name: 'Vision Worker', description: 'Screen Analysis' },
    { id: 'voice', name: 'Voice Worker', description: 'Speech Recognition' },
    { id: 'cloud', name: 'Cloud Worker', description: 'Gemini Overdrive' },
    { id: 'apps', name: 'Apps Worker', description: 'Gemini App Integration' },
  ];

  return (
    <div className="min-h-screen bg-[#050505] text-white">
      {/* Header */}
      <header className="border-b border-gray-800 p-4">
        <div className="container mx-auto flex justify-between items-center">
          <h1 className="text-2xl font-bold text-cyan-400">REZ HIVE</h1>
          <div className="flex items-center gap-4">
            <div className={px-3 py-1 rounded }>
              KERNEL {kernelStatus}
            </div>
            <div className="text-sm text-gray-400">{uptime}s</div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <div className="container mx-auto p-4">
        <div className="grid grid-cols-12 gap-4">
          {/* Left Sidebar - Workers */}
          <div className="col-span-3 bg-gray-900 rounded-lg p-4">
            <h2 className="text-xs text-gray-500 uppercase mb-4">Capabilities</h2>
            <div className="space-y-2">
              {workers.map(worker => (
                <div key={worker.id} className="p-3 bg-gray-800 rounded-lg hover:bg-gray-700 cursor-pointer">
                  <div className="font-medium">{worker.name}</div>
                  <div className="text-xs text-gray-400">{worker.description}</div>
                </div>
              ))}
            </div>
          </div>

          {/* Center - Chat Area */}
          <div className="col-span-6 bg-gray-900 rounded-lg p-4">
            <div className="h-96 flex items-center justify-center text-gray-500">
              <div className="text-center">
                <div className="text-6xl mb-4">??</div>
                <h3 className="text-xl mb-2">What can Rez Hive do for you today?</h3>
                <p className="text-sm text-gray-400">Select a capability or type below</p>
              </div>
            </div>
            
            {/* Input Area */}
            <div className="mt-4">
              <input 
                type="text"
                placeholder="Ask Rez Hive anything..."
                className="w-full bg-gray-800 border border-gray-700 rounded-lg p-3 text-white placeholder-gray-500"
              />
            </div>
          </div>

          {/* Right Sidebar - Market Watch */}
          <div className="col-span-3 bg-gray-900 rounded-lg p-4">
            <h2 className="text-xs text-gray-500 uppercase mb-4">Market Watch</h2>
            <div className="space-y-3">
              <div className="bg-gray-800 p-3 rounded-lg">
                <div className="flex justify-between text-sm">
                  <span>BTC/USDT</span>
                  <span className="text-green-400">,341</span>
                </div>
                <div className="text-xs text-gray-400 mt-1">BINANCE ? 12ms</div>
              </div>
              <div className="bg-gray-800 p-3 rounded-lg">
                <div className="flex justify-between text-sm">
                  <span>ETH/USDT</span>
                  <span className="text-green-400">,124</span>
                </div>
                <div className="text-xs text-gray-400 mt-1">BINANCE ? 12ms</div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
