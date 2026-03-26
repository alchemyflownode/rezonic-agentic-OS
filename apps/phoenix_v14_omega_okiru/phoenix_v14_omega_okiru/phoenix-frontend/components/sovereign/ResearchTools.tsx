'use client';

import { Search } from 'lucide-react';

interface ResearchToolsProps {
  onAction: (command: string) => void;
}

export function ResearchTools({ onAction }: ResearchToolsProps) {
  return (
    <div className="space-y-2">
      <div className="grid grid-cols-2 gap-2">
        <button
          onClick={() => onAction('Deep search: Latest AI news')}
          className="p-2 bg-purple-500/10 hover:bg-purple-500/20 border border-purple-500/30 rounded text-[10px] text-purple-300 flex items-center gap-1 justify-center"
          aria-label="Search AI news"
        >
          <Search className="w-3 h-3" /> AI News
        </button>
        <button
          onClick={() => onAction('Deep search: Cyberpunk art')}
          className="p-2 bg-purple-500/10 hover:bg-purple-500/20 border border-purple-500/30 rounded text-[10px] text-purple-300 flex items-center gap-1 justify-center"
          aria-label="Search cyberpunk art"
        >
          <Search className="w-3 h-3" /> Art Ref
        </button>
      </div>
    </div>
  );
}
