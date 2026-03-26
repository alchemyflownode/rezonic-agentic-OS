// app/comfyui/page.tsx
'use client';

import React, { useState, useEffect } from 'react';
import { Palette, Video, Image, Zap } from 'lucide-react';

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8002';

export default function ComfyUIPage() {
  const [comfyuiStatus, setComfyuiStatus] = useState<'online' | 'offline' | 'checking'>('checking');
  const [prompt, setPrompt] = useState('');
  const [generating, setGenerating] = useState(false);

  const checkComfyUI = async () => {
    try {
      const res = await fetch('http://127.0.0.1:8188/system_stats');
      setComfyuiStatus(res.ok ? 'online' : 'offline');
    } catch {
      setComfyuiStatus('offline');
    }
  };

  useEffect(() => {
    checkComfyUI();
  }, []);

  const handleGenerate = async () => {
    if (!prompt.trim()) return;
    setGenerating(true);
    try {
      const res = await fetch(`${API_BASE}/kernel/stream`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ task: `/generate ${prompt}` })
      });
      const data = await res.json();
      console.log('Generation queued:', data);
    } catch (error) {
      console.error('Generation failed:', error);
    }
    setGenerating(false);
  };

  return (
    <div className="h-screen bg-gradient-to-br from-[#0a0a0c] via-[#050505] to-[#0a0a0c] text-[#c0caf5] p-6 overflow-y-auto">
      <div className="max-w-7xl mx-auto">
        <div className="mb-8">
          <h1 className="text-3xl font-bold bg-gradient-to-r from-[#7dcfff] to-[#bb9af7] bg-clip-text text-transparent">
            ComfyUI Studio
          </h1>
          <p className="text-[#565f89] mt-2">AI image & video generation with constitutional oversight</p>
        </div>

        {/* Status */}
        <div className={`inline-flex items-center gap-2 px-4 py-2 rounded-full mb-6 ${
          comfyuiStatus === 'online' ? 'bg-[#9ece6a]/10 border border-[#9ece6a]/20' : 'bg-[#f7768e]/10 border border-[#f7768e]/20'
        }`}>
          <div className={`w-2 h-2 rounded-full ${comfyuiStatus === 'online' ? 'bg-[#9ece6a]' : 'bg-[#f7768e]'}`} />
          <span className="text-xs font-mono">ComfyUI: {comfyuiStatus === 'online' ? 'Connected' : 'Not Running'}</span>
        </div>

        {/* Generation Form */}
        <div className="bg-black/30 backdrop-blur-xl border border-[#7dcfff]/10 rounded-xl p-6 mb-6">
          <h2 className="text-xl font-bold mb-4 flex items-center gap-2">
            <Palette className="w-5 h-5 text-[#7dcfff]" />
            Generate Image
          </h2>
          <div className="flex gap-2">
            <input
              type="text"
              value={prompt}
              onChange={(e) => setPrompt(e.target.value)}
              placeholder="Describe what you want to generate..."
              className="flex-1 bg-black/50 border border-[#7dcfff]/20 rounded-xl px-4 py-3 text-sm text-[#c0caf5] placeholder:text-[#565f89] outline-none focus:border-[#7dcfff]/50"
            />
            <button
              onClick={handleGenerate}
              disabled={generating || comfyuiStatus !== 'online'}
              className="px-6 py-3 rounded-xl bg-gradient-to-r from-[#7dcfff]/20 to-[#bb9af7]/20 border border-[#7dcfff]/30 text-[#7dcfff] hover:shadow-lg transition-all disabled:opacity-50"
            >
              {generating ? 'Generating...' : 'Generate'}
            </button>
          </div>
        </div>

        {/* Module Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="bg-black/30 backdrop-blur-xl border border-[#7dcfff]/10 rounded-xl p-5">
            <Image className="w-8 h-8 text-[#7dcfff] mb-3" />
            <h3 className="text-lg font-bold text-white mb-2">Image Generation</h3>
            <p className="text-sm text-[#565f89] mb-4">SDXL, Flux, Z-Image models</p>
            <code className="text-xs text-[#7dcfff] block bg-black/40 p-2 rounded">/generate cyberpunk cat</code>
          </div>
          <div className="bg-black/30 backdrop-blur-xl border border-[#7dcfff]/10 rounded-xl p-5">
            <Video className="w-8 h-8 text-[#bb9af7] mb-3" />
            <h3 className="text-lg font-bold text-white mb-2">Video Generation</h3>
            <p className="text-sm text-[#565f89] mb-4">AnimateDiff, SVD models</p>
            <code className="text-xs text-[#bb9af7] block bg-black/40 p-2 rounded">/video cat running</code>
          </div>
        </div>
      </div>
    </div>
  );
}