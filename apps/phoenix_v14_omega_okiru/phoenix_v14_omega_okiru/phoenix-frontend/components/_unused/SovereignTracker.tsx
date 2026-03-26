'use client';

import { useState, useEffect } from 'react';

export function SovereignTracker() {
  const [status, setStatus] = useState({
    ollama: false,
    chroma: false,
    kernel: true
  });

  useEffect(() => {
    const checkStatus = async () => {
      try {
        const res = await fetch('/api/status');
        const data = await res.json();
        setStatus(data);
      } catch (e) {
        console.log('Status check failed');
      }
    };
    checkStatus();
    const interval = setInterval(checkStatus, 10000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="fixed bottom-4 left-4 z-50 bg-black/50 backdrop-blur-md border border-white/10 rounded-lg p-2 text-xs">
      <div className="flex gap-3">
        <div className="flex items-center gap-1">
          <span className={`w-2 h-2 rounded-full ${status.ollama ? 'bg-green-400' : 'bg-red-400'}`} />
          <span>Brain</span>
        </div>
        <div className="flex items-center gap-1">
          <span className={`w-2 h-2 rounded-full ${status.chroma ? 'bg-green-400' : 'bg-red-400'}`} />
          <span>Memory</span>
        </div>
        <div className="flex items-center gap-1">
          <span className={`w-2 h-2 rounded-full ${status.kernel ? 'bg-green-400' : 'bg-red-400'}`} />
          <span>Kernel</span>
        </div>
      </div>
    </div>
  );
}