'use client';

import { motion } from 'framer-motion';
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

interface WorkerGridProps {
  workers: any[];
  onSelect: (worker: any) => void;
  selectedId?: string;
}

export function ObsidianWorkerGrid({ workers, onSelect, selectedId }: WorkerGridProps) {
  return (
    <div className="obsidian-worker-grid">
      {workers.map((worker, index) => {
        const Icon = iconMap[worker.id] || Brain;
        const isSelected = selectedId === worker.id;
        
        return (
          <motion.button
            key={worker.id}
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ delay: index * 0.02 }}
            onClick={() => onSelect(worker)}
            className={`obsidian-worker-item ${isSelected ? 'selected' : ''}`}
          >
            <Icon className="obsidian-worker-icon" />
            <div className="obsidian-worker-name">{worker.name}</div>
            <div className="obsidian-worker-category">{worker.category}</div>
            <div className="flex justify-center mt-2">
              <span className={`obsidian-status-dot ${worker.status}`} />
            </div>
          </motion.button>
        );
      })}
    </div>
  );
}
