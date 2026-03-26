'use client';

import React, { useState } from 'react';
import { Scan, FolderOpen, FileText, AlertTriangle, CheckCircle } from 'lucide-react';

export default function SystemScannerPage() {
  const [path, setPath] = useState('');
  const [scanning, setScanning] = useState(false);
  const [results, setResults] = useState<any>(null);
  const [error, setError] = useState('');

  const handleScan = async () => {
    if (!path.trim()) return;
    setScanning(true);
    setError('');
    setResults(null);

    try {
      const response = await fetch('http://localhost:8002/kernel/stream', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ task: `/scan ${path}` })
      });
      
      const reader = response.body?.getReader();
      const decoder = new TextDecoder();
      let content = '';
      
      while (reader) {
        const { done, value } = await reader.read();
        if (done) break;
        content += decoder.decode(value);
      }
      
      setResults({ content, path });
    } catch (err) {
      setError('Scan failed. Is the kernel running?');
    } finally {
      setScanning(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#050505] p-8">
      <div className="max-w-4xl mx-auto">
        <div className="mb-8">
          <h1 className="text-2xl font-bold text-white flex items-center gap-3">
            <Scan className="w-8 h-8 text-[#00E5FF]" />
            RezScanner
          </h1>
          <p className="text-zinc-500 mt-2">AST Architecture Mapping</p>
        </div>

        <div className="bg-[#0a0a0c] border border-white/5 rounded-xl p-6 mb-6">
          <div className="flex gap-3">
            <input
              type="text"
              value={path}
              onChange={(e) => setPath(e.target.value)}
              placeholder="Enter path to scan (e.g., D:\\Projects)"
              className="flex-1 bg-black/50 border border-white/10 rounded-lg px-4 py-3 text-white placeholder:text-zinc-600 focus:outline-none focus:border-[#00E5FF]/50 font-mono text-sm"
            />
            <button
              onClick={handleScan}
              disabled={scanning}
              className="px-6 py-3 bg-[#00E5FF]/20 border border-[#00E5FF]/30 rounded-lg text-[#00E5FF] hover:bg-[#00E5FF]/30 transition disabled:opacity-50"
            >
              {scanning ? 'Scanning...' : 'Scan'}
            </button>
          </div>
          <p className="text-xs text-zinc-600 mt-3">Example: D:\Rezonic_Agentic\apps\phoenix-kernel</p>
        </div>

        {error && (
          <div className="bg-red-500/10 border border-red-500/30 rounded-xl p-4 mb-6 flex items-center gap-3">
            <AlertTriangle className="w-5 h-5 text-red-500" />
            <span className="text-red-400">{error}</span>
          </div>
        )}

        {results && (
          <div className="bg-[#0a0a0c] border border-white/5 rounded-xl overflow-hidden">
            <div className="px-4 py-3 bg-[#1A1D23]/80 border-b border-white/10 flex items-center gap-2">
              <FolderOpen className="w-4 h-4 text-[#00E5FF]" />
              <span className="text-xs font-mono text-zinc-400">{results.path}</span>
            </div>
            <pre className="p-4 text-xs font-mono text-zinc-300 whitespace-pre-wrap overflow-x-auto max-h-96">
              {results.content}
            </pre>
          </div>
        )}
      </div>
    </div>
  );
}