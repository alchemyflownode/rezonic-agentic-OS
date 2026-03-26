'use client';

import { 
  Brain, Cpu, Search, Code, Eye, Mic, FileText,
  Sparkles, Zap, Shield, Activity, GitBranch,
  Layers, Box, Globe, HardDrive, Terminal, Wifi
} from 'lucide-react';

const iconMap: Record<string, any> = {
  'system-monitor': Cpu, 'deep-search': Search, 'mutation': Code,
  'vision': Eye, 'app-launcher': Box, 'code-worker': Code,
  'voice': Mic, 'canvas': Layers, 'file-worker': FileText,
  'rezstack': GitBranch, 'mcp': Globe, 'director': Brain,
  'sce': Sparkles, 'harvester': Activity, 'guardian': Shield,
  'architect': Brain, 'discover': Search, 'domains': Layers,
  'generate': Code, 'heal': Activity, 'learn': Brain,
  'autonomous': Zap, 'heartbeat': Activity, 'governor': Shield,
  'compute-hw': Cpu, 'compute-exec': Terminal,
  'frontend-workers': Wifi, 'system-snapshot': HardDrive,
};

interface PremiumWorkerGridProps {
  workers: any[];
  onSelect: (worker: any) => void;
  selectedId?: string;
}

export function PremiumWorkerGrid({ workers, onSelect, selectedId }: PremiumWorkerGridProps) {
  return (
    <div className="worker-grid-premium">
      {workers.map((worker) => {
        const Icon = iconMap[worker.id] || Brain;
        const isSelected = selectedId === worker.id;
        
        return (
          <button
            key={worker.id}
            onClick={() => onSelect(worker)}
            className={`worker-item-premium ${isSelected ? 'active' : ''}`}
            title={worker.name}
          >
            <Icon size={16} />
            <span>{worker.name.split(' ')[0]}</span>
          </button>
        );
      })}
    </div>
  );
}
