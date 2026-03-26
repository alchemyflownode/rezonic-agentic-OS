'use client';

import React, { useState } from 'react';
import { Brain, Lightbulb } from 'lucide-react';

export const PrimordialUI = () => {
  const [insights] = useState([
    'I notice you check CPU often. Would you like a shortcut?',
    'Your RAM usage suggests closing Chrome tabs might help',
    "You're most active in the evening"
  ]);

  return (
    <div className="fixed right-6 bottom-24 w-80 z-40 space-y-3">
      <div className="bg-blue-500/10 backdrop-blur-xl border border-blue-500/30 rounded-2xl p-4">
        <div className="flex items-center gap-2 mb-3">
          <Brain className="text-blue-400" size={18} />
          <span className="text-xs font-mono text-blue-400">AGENT INSIGHTS</span>
        </div>
        <div className="space-y-2">
          {insights.map((insight, i) => (
            <div key={i} className="flex gap-2 text-xs text-white/60">
              <Lightbulb size={14} className="text-blue-400 shrink-0 mt-0.5" />
              <span>✨ {insight}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

export default PrimordialUI;
