'use client';

import React, { useState } from 'react';
import { Code, Play, Save, Download, Sparkles } from 'lucide-react';

const DEFAULT_CODE = `// Sovereign App Builder
// Create your own AI-powered applications

from rezonic.workers import Worker
from rezonic.sce import invariant

class MySovereignApp(Worker):
    @invariant("SAFETY_FIRST")
    async def execute(self, task: str):
        return {
            "result": f"Processing: {task}",
            "drift_lock": "0x7f3e..."
        }
`;

export default function AppBuilderPage() {
  const [code, setCode] = useState(DEFAULT_CODE);
  const [output, setOutput] = useState('');
  const [running, setRunning] = useState(false);

  const handleRun = async () => {
    setRunning(true);
    setOutput('Executing...');

    try {
      const response = await fetch('http://localhost:8002/kernel/stream', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ task: '/code ' + code.substring(0, 200) })
      });

      const reader = response.body?.getReader();
      const decoder = new TextDecoder();
      let content = '';

      while (reader) {
        const { done, value } = await reader.read();
        if (done) break;
        content += decoder.decode(value);
      }

      setOutput(content || 'Execution complete');
    } catch (err) {
      setOutput('Error: Kernel not reachable');
    } finally {
      setRunning(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#050505] p-8">
      <div className="max-w-6xl mx-auto">
        <div className="mb-8">
          <h1 className="text-2xl font-bold text-white flex items-center gap-3">
            <Sparkles className="w-8 h-8 text-[#9B72CB]" />
            App Builder
          </h1>
          <p className="text-zinc-500 mt-2">Create sovereign AI applications with RezCode</p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div className="bg-[#0a0a0c] border border-white/5 rounded-xl overflow-hidden">
            <div className="px-4 py-3 bg-[#1A1D23]/80 border-b border-white/10 flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Code className="w-4 h-4 text-[#00E5FF]" />
                <span className="text-xs font-mono text-zinc-400">app.py</span>
              </div>
              <div className="flex gap-2">
                <button className="p-1.5 rounded hover:bg-white/10 text-zinc-500 hover:text-white transition">
                  <Save className="w-4 h-4" />
                </button>
                <button className="p-1.5 rounded hover:bg-white/10 text-zinc-500 hover:text-white transition">
                  <Download className="w-4 h-4" />
                </button>
              </div>
            </div>
            <textarea
              value={code}
              onChange={(e) => setCode(e.target.value)}
              className="w-full h-[500px] bg-[#050505] text-[#00E5FF] font-mono text-sm p-4 resize-none focus:outline-none"
              spellCheck={false}
            />
          </div>

          <div className="bg-[#0a0a0c] border border-white/5 rounded-xl overflow-hidden flex flex-col">
            <div className="px-4 py-3 bg-[#1A1D23]/80 border-b border-white/10 flex items-center justify-between">
              <span className="text-xs font-mono text-zinc-400">Output</span>
              <button
                onClick={handleRun}
                disabled={running}
                className="flex items-center gap-2 px-3 py-1.5 bg-[#00E5FF]/20 border border-[#00E5FF]/30 rounded-lg text-[#00E5FF] text-xs hover:bg-[#00E5FF]/30 transition disabled:opacity-50"
              >
                <Play className="w-3 h-3" />
                {running ? 'Running...' : 'Run'}
              </button>
            </div>
            <div className="flex-1 p-4 overflow-auto">
              <pre className="text-sm font-mono text-zinc-300 whitespace-pre-wrap">
                {output || 'Click Run to execute your sovereign app'}
              </pre>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
