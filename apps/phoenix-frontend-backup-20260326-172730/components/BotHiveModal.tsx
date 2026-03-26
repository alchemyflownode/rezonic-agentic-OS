'use client';

import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Code, Upload, X, Play } from 'lucide-react';

const API_BASE = "http://localhost:8002";

const JS_BOT_TEMPLATE = `// APEX JS WORKER v1.0
class TradingBot {
    async onTick(marketData) {
        const btc = marketData.find(m => m.symbol === 'BTC/PHP');
        if (btc.price < 4500000) {
            return { action: 'BUY', amount: 1000, reason: 'Constitutional Floor Reached' };
        }
        return null;
    }
}
export default TradingBot;`;

export const BotHiveModal = ({ isOpen, onClose }: { isOpen: boolean, onClose: () => void }) => {
  const [code, setCode] = useState(JS_BOT_TEMPLATE);
  const [status, setStatus] = useState('idle');

  const handleDeploy = async () => {
    setStatus('deploying');
    try {
      await fetch(`${API_BASE}/workers/deploy`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name: "CustomWorker", code: code })
      });
      setStatus('success');
      setTimeout(() => { setStatus('idle'); onClose(); }, 1500);
    } catch (e) { 
      setStatus('error');
      console.error('Deploy failed:', e);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-[100] flex items-center justify-center bg-black/90 backdrop-blur-md p-8">
      <div className="w-full max-w-4xl bg-[#0a0a0c] border border-white/10 rounded-2xl flex flex-col h-[80vh] overflow-hidden shadow-2xl">
        <div className="p-4 border-b border-white/10 flex justify-between items-center">
          <div className="flex items-center gap-3">
            <Code className="text-cyan-400 w-5 h-5" />
            <h2 className="text-sm font-bold tracking-widest uppercase">Worker Deployment Engine</h2>
          </div>
          <button onClick={onClose}><X className="text-zinc-500" /></button>
        </div>
        
        <textarea 
          value={code} 
          onChange={(e) => setCode(e.target.value)}
          className="flex-1 bg-black text-cyan-400 font-mono text-[11px] p-6 outline-none resize-none"
        />

        <div className="p-4 border-t border-white/10 bg-black/40 flex justify-end">
          <button 
            onClick={handleDeploy}
            className={`px-8 py-2 rounded text-[10px] font-bold uppercase tracking-widest transition-all ${
              status === 'success' 
                ? 'bg-green-500 text-black' 
                : status === 'error'
                ? 'bg-red-500 text-white'
                : 'bg-cyan-500 text-black'
            }`}
          >
            {status === 'deploying' ? 'Injecting Worker...' : 
             status === 'success' ? 'Injection Complete' : 
             status === 'error' ? 'Deploy Failed' : 
             'Deploy to Kernel'}
          </button>
        </div>
      </div>
    </div>
  );
};