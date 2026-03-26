'use client';

import { Brain, Settings } from 'lucide-react';
import { SovereignBadge } from '@/components/ui/SovereignBadge';

interface SovereignHeaderProps {
  onSettingsClick: () => void;
  isEditing: boolean;
}

export function SovereignHeader({ onSettingsClick, isEditing }: SovereignHeaderProps) {
  return (
    <div className="p-3 border-b border-white/10 flex justify-between items-center">
      <div className="flex items-center gap-2">
        <Brain className="w-4 h-4 text-purple-400" />
        <span className="text-xs font-bold text-white/80">SOVEREIGN CONTROL</span>
      </div>
      <div className="flex items-center gap-2">
        <button
          onClick={onSettingsClick}
          className="p-1 hover:bg-white/10 rounded text-white/50 hover:text-white transition-colors"
          aria-label={isEditing ? "Exit edit mode" : "Enter edit mode"}
        >
          <Settings className="w-3 h-3" />
        </button>
        <SovereignBadge variant="online">ONLINE</SovereignBadge>
      </div>
    </div>
  );
}
