'use client';

import { PulseIndicator } from './PulseIndicator';

interface WorkerActivityProps {
  name: string;
  active: boolean;
  lastActive?: string;
}

export function WorkerActivity({ name, active, lastActive }: WorkerActivityProps) {
  return (
    <div className="flex items-center justify-between p-2 bg-obsidian-surface rounded border border-border-subtle hover:border-cyan-primary transition-colors">
      <div className="flex items-center gap-2">
        <PulseIndicator status={active ? 'processing' : 'idle'} size="sm" />
        <span className="text-sm text-text-secondary">{name}</span>
      </div>
      {lastActive && (
        <span className="text-xs text-text-tertiary">{lastActive}</span>
      )}
    </div>
  );
}
