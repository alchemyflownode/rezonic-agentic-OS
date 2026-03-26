'use client';

import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { Sparkles, Code } from 'lucide-react';
import { SovereignCanvas } from '@/components/SovereignCanvas';

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
  const [sce, setSce] = useState({
    verified: true,
    driftLock: '0x7f3e8a2c1b9d4f5e',
    narrative: [
      'Analyzing code intent...',
      'Compiling with RezCode...',
      'SCE verification passed'
    ]
  });

  const handleExecute = async (codeToRun: string) => {
    try {
      const response = await fetch('http://localhost:8002/kernel/stream', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ task: `/code ${codeToRun.substring(0, 200)}` })
      });
      
      const reader = response.body?.getReader();
      const decoder = new TextDecoder();
      let content = '';
      
      while (reader) {
        const { done, value } = await reader.read();
        if (done) break;
        content += decoder.decode(value);
      }
      
      setOutput(content);
      return { message: 'Execution complete', driftLock: '0x7f3e...' };
    } catch (err) {
      setOutput('Error: Kernel not reachable');
      throw err;
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-[#0a0a0c] via-[#050505] to-[#0a0a0c] p-8">
      <div className="fixed inset-0 pointer-events-none opacity-20">
        <div className="absolute inset-0 bg-[radial-gradient(circle_at_50%_50%,_#7dcfff_0%,_transparent_50%)] opacity-5" />
        <div className="absolute inset-0" style={{ backgroundImage: 'linear-gradient(to right, #7dcfff0a 1px, transparent 1px), linear-gradient(to bottom, #7dcfff0a 1px, transparent 1px)', backgroundSize: '40px 40px' }} />
      </div>

      <div className="relative z-10 max-w-7xl mx-auto">
        <motion.div
          initial={{ y: -20, opacity: 0 }}
          animate={{ y: 0, opacity: 1 }}
          className="mb-8"
        >
          <div className="flex items-center gap-4">
            <div className="w-12 h-12 rounded-2xl bg-gradient-to-br from-[#7dcfff]/20 to-[#9B72CB]/20 border border-[#7dcfff]/30 flex items-center justify-center">
              <Sparkles className="w-6 h-6 text-[#7dcfff]" />
            </div>
            <div>
              <h1 className="text-3xl font-bold bg-gradient-to-r from-[#c0caf5] to-[#7dcfff] bg-clip-text text-transparent">
                App Builder
              </h1>
              <p className="text-[#565f89] mt-1">Create sovereign AI applications with RezCode</p>
            </div>
          </div>
        </motion.div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Code Editor */}
          <div className="bg-black/30 backdrop-blur-xl border border-[#7dcfff]/10 rounded-2xl overflow-hidden">
            <div className="px-4 py-3 border-b border-[#7dcfff]/10 bg-black/30 flex items-center gap-2">
              <Code className="w-4 h-4 text-[#7dcfff]" />
              <span className="text-xs font-mono text-white">app.py</span>
            </div>
            <textarea
              value={code}
              onChange={(e) => setCode(e.target.value)}
              className="w-full h-[500px] bg-[#030406] text-[#7dcfff] font-mono text-sm p-4 resize-none focus:outline-none"
              spellCheck={false}
            />
          </div>

          {/* SovereignCanvas Output */}
          <SovereignCanvas
            code={output || '# Output will appear here...\n\n# Click Run to execute your sovereign app'}
            language="python"
            title="Execution Output"
            executable={true}
            sce={sce}
            onExecute={handleExecute}
            metadata={{
              author: 'Rezonic Labs',
              version: '1.0.0',
              created: new Date().toLocaleDateString()
            }}
          />
        </div>
      </div>
    </div>
  );
}