'use client';

import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { Sparkles, Code, Play, Save } from 'lucide-react';

const DEFAULT_CODE = `# Sovereign App Builder
# Create your own AI-powered applications

class MySovereignApp:
    def __init__(self):
        self.name = "MySovereignApp"
    
    async def execute(self, task: str):
        return {
            "result": f"Processing: {task}",
            "drift_lock": "0x7f3e..."
        }
`;

export default function AppBuilderPage() {
  const [code, setCode] = useState(DEFAULT_CODE);
  const [output, setOutput] = useState('');
  const [isRunning, setIsRunning] = useState(false);

  const handleExecute = async () => {
    setIsRunning(true);
    setOutput('Executing...\n');
    
    try {
      const response = await fetch('/api/kernel/execute', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ code })
      });
      const result = await response.json();
      setOutput(prev => prev + JSON.stringify(result, null, 2));
    } catch (error) {
      setOutput(prev => prev + `\nError: ${error}`);
    } finally {
      setIsRunning(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-[#0a0a0c] via-[#050505] to-[#0a0a0c] p-8">
      <div className="max-w-7xl mx-auto">
        <div className="flex items-center gap-4 mb-8">
          <div className="w-12 h-12 rounded-2xl bg-gradient-to-br from-[#7dcfff]/20 to-[#9B72CB]/20 border border-[#7dcfff]/30 flex items-center justify-center">
            <Sparkles className="w-6 h-6 text-[#7dcfff]" />
          </div>
          <div>
            <h1 className="text-3xl font-bold bg-gradient-to-r from-[#c0caf5] to-[#7dcfff] bg-clip-text text-transparent">
              App Builder
            </h1>
            <p className="text-[#565f89] mt-1">Create sovereign AI applications</p>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Code Editor */}
          <div className="bg-black/30 backdrop-blur-xl border border-[#7dcfff]/10 rounded-2xl overflow-hidden">
            <div className="px-4 py-3 border-b border-[#7dcfff]/10 bg-black/30 flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Code className="w-4 h-4 text-[#7dcfff]" />
                <span className="text-xs font-mono text-white">app.py</span>
              </div>
              <div className="flex gap-2">
                <button className="p-1.5 rounded-lg hover:bg-white/10 transition">
                  <Save className="w-4 h-4 text-[#7dcfff]" />
                </button>
                <button
                  onClick={handleExecute}
                  disabled={isRunning}
                  className="p-1.5 rounded-lg bg-[#7dcfff]/20 hover:bg-[#7dcfff]/30 transition disabled:opacity-50"
                >
                  <Play className="w-4 h-4 text-[#7dcfff]" />
                </button>
              </div>
            </div>
            <textarea
              value={code}
              onChange={(e) => setCode(e.target.value)}
              className="w-full h-[500px] bg-[#030406] text-[#7dcfff] font-mono text-sm p-4 resize-none focus:outline-none"
              spellCheck={false}
            />
          </div>

          {/* Output */}
          <div className="bg-black/30 backdrop-blur-xl border border-[#7dcfff]/10 rounded-2xl overflow-hidden">
            <div className="px-4 py-3 border-b border-[#7dcfff]/10 bg-black/30">
              <span className="text-xs font-mono text-white">Execution Output</span>
            </div>
            <pre className="h-[500px] overflow-y-auto p-4 text-sm text-[#c0caf5] font-mono">
              {output || '# Output will appear here...\n\n# Click Run to execute your sovereign app'}
            </pre>
          </div>
        </div>
      </div>
    </div>
  );
}
