'use client';

import React, { useState } from 'react';
import { SovereignMessage } from '@/components/SovereignMessage';

export default function TestMessagePage() {
  const [testContent, setTestContent] = useState(`**Generated Code**

\`\`\`python
def add(a: int, b: int) -> int:
    """Add two numbers."""
    return a + b
\`\`\`

Verified: False
Drift Score: 0.00`);

  return (
    <div className="min-h-screen bg-gradient-to-br from-[#0a0a0c] to-[#050505] p-8">
      <div className="max-w-4xl mx-auto">
        <h1 className="text-2xl font-bold text-white mb-6">SovereignMessage Test</h1>
        
        <div className="mb-6">
          <h2 className="text-sm font-mono text-[#7dcfff] mb-2">Test Content:</h2>
          <textarea
            value={testContent}
            onChange={(e) => setTestContent(e.target.value)}
            className="w-full h-64 bg-black/50 border border-[#7dcfff]/20 rounded-xl p-4 text-white font-mono text-sm"
          />
        </div>
        
        <div className="space-y-4">
          <h2 className="text-sm font-mono text-[#9ece6a] mb-2">Rendered Output:</h2>
          <SovereignMessage
            content={testContent}
            role="assistant"
            driftLock="229c4af7d8faba26"
          />
        </div>
        
        <div className="mt-8 p-4 bg-yellow-500/10 border border-yellow-500/20 rounded-xl">
          <p className="text-xs text-yellow-500">Check the browser console (F12) to see the parseContent logs!</p>
        </div>
      </div>
    </div>
  );
}
