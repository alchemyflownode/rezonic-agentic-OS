'use client';

import { useState } from 'react';
import { 
  Brain, Cpu, Search, Code, Eye, Mic, FileText,
  Sparkles, Zap, Shield, Activity, GitBranch,
  Layers, Box, Globe, HardDrive, Terminal, Wifi
} from 'lucide-react';

const iconMap: Record<string, any> = {
  'system-monitor': Cpu,
  'deep-search': Search,
  'mutation': Code,
  'vision': Eye,
  'app-launcher': Box,
  'code-worker': Code,
  'voice': Mic,
  'canvas': Layers,
  'file-worker': FileText,
  'rezstack': GitBranch,
  'mcp': Globe,
  'director': Brain,
  'sce': Sparkles,
  'harvester': Activity,
  'guardian': Shield,
  'architect': Brain,
  'discover': Search,
  'domains': Layers,
  'generate': Code,
  'heal': Activity,
  'learn': Brain,
  'autonomous': Zap,
  'heartbeat': Activity,
  'governor': Shield,
  'compute-hw': Cpu,
  'compute-exec': Terminal,
  'frontend-workers': Wifi,
  'system-snapshot': HardDrive,
};

interface HighDensityWorkerGridProps {
  workers: any[];
  onSelect: (worker: any) => void;
  selectedId?: string;
}

export function HighDensityWorkerGrid({ workers, onSelect, selectedId }: HighDensityWorkerGridProps) {
  return (
    <div className="ide-worker-grid">
      {workers.map((worker, index) => {
        const Icon = iconMap[worker.id] || Brain;
        const isSelected = selectedId === worker.id;
        
        return (
          <button
            key={worker.id}
            onClick={() => onSelect(worker)}
            className={`ide-worker-item ${isSelected ? 'active' : ''}`}
            title={worker.name}
          >
            <Icon className="icon" />
            <span className="label">{worker.name.split(' ')[0]}</span>
            {isSelected && <div className="ide-active-pulse" />}
          </button>
        );
      })}
    </div>
  );
}
