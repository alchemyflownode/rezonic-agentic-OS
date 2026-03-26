'use client';

import { useState, useEffect } from 'react';
import { SovereignCard } from '@/components/ui';
import { Brain, Zap, Shield, Clock } from 'lucide-react';

interface AgentThoughtProps {
  thought?: string;
  processing?: boolean;
  intent?: any;
}

export function AgentThought({ thought, processing, intent }: AgentThoughtProps) {
  const [expanded, setExpanded] = useState(false);
  const [currentThought, setCurrentThought] = useState(thought);
  
  useEffect(() => {
    if (thought) {
      setCurrentThought(thought);
    }
  }, [thought]);
  
  if (!processing && !currentThought && !intent) return null;
  
  return (
    <SovereignCard variant="glass" className="mb-4 p-3 text-xs border-l-4 border-l-[var(--sovereign-primary)]">
      <div className="flex items-center justify-between mb-2">
        <div className="flex items-center gap-2">
          <Brain className="w-3 h-3 text-[var(--sovereign-primary)]" />
          <span className="font-mono text-[10px] text-[var(--sovereign-text-secondary)]">
            AGENT THOUGHT PROCESS
          </span>
        </div>
        <button 
          onClick={() => setExpanded(!expanded)}
          className="text-[var(--sovereign-text-tertiary)] hover:text-[var(--sovereign-text-primary)]"
        >
          {expanded ? '−' : '+'}
        </button>
      </div>
      
      {processing && (
        <div className="flex items-center gap-2 text-[10px] text-[var(--sovereign-text-tertiary)]">
          <Zap className="w-2 h-2 animate-pulse" />
          <span>Analyzing intent...</span>
        </div>
      )}
      
      {intent && expanded && (
        <div className="mt-2 space-y-1 font-mono text-[9px] border-t border-[var(--sovereign-border-light)] pt-2">
          <div className="flex items-center gap-1">
            <Shield className="w-2 h-2 text-[var(--sovereign-secondary)]" />
            <span className="text-[var(--sovereign-text-tertiary)]">Intent Type:</span>
            <span className="text-[var(--sovereign-text-primary)]">{intent.type}</span>
          </div>
          <div className="flex items-center gap-1">
            <Clock className="w-2 h-2 text-[var(--sovereign-secondary)]" />
            <span className="text-[var(--sovereign-text-tertiary)]">Confidence:</span>
            <span className="text-[var(--sovereign-text-primary)]">{intent.confidence * 100}%</span>
          </div>
          {intent.suggested_worker && (
            <div className="flex items-center gap-1">
              <Zap className="w-2 h-2 text-[var(--sovereign-secondary)]" />
              <span className="text-[var(--sovereign-text-tertiary)]">Selected Worker:</span>
              <span className="text-[var(--sovereign-primary)]">{intent.suggested_worker}</span>
            </div>
          )}
        </div>
      )}
      
      {currentThought && expanded && (
        <div className="mt-2 text-[9px] text-[var(--sovereign-text-secondary)] italic border-t border-[var(--sovereign-border-light)] pt-2">
          {currentThought}
        </div>
      )}
    </SovereignCard>
  );
}
