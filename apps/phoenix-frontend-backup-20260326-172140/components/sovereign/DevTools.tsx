'use client';

interface DevToolsProps {
  onAction: (command: string) => void;
}

export function DevTools({ onAction }: DevToolsProps) {
  return (
    <div className="space-y-2">
      <div className="text-[10px] text-white/40 mb-1">Development Tools</div>
      <div className="grid grid-cols-2 gap-2">
        <button
          onClick={() => onAction('Clean code')}
          className="p-2 bg-red-500/10 hover:bg-red-500/20 border border-red-500/30 rounded text-[10px] text-red-300 flex items-center gap-1 justify-center"
          aria-label="Clean code"
        >
          Clean Code
        </button>
        <button
          onClick={() => onAction('Write a python hello world')}
          className="p-2 bg-white/5 hover:bg-white/10 border border-white/10 rounded text-[10px] text-white/80 flex items-center gap-1 justify-center"
          aria-label="Generate script"
        >
          Gen Script
        </button>
      </div>
    </div>
  );
}
