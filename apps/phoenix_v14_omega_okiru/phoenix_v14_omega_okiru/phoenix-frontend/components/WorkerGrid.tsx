'use client';

import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
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

export function WorkerGrid({ workers, onSelect, selectedId }: WorkerGridProps) {
  const [filter, setFilter] = useState('all');

  const categories = ['all', 'python', 'api'];
  const filteredWorkers = filter === 'all' 
    ? workers 
    : workers.filter(w => w.category === filter);

  return (
    <div className="space-y-4">
      {/* Category Filter */}
      <div className="flex gap-2 p-1 bg-white/5 rounded-lg">
        {categories.map(cat => (
          <button
            key={cat}
            onClick={() => setFilter(cat)}
            className={`flex-1 px-3 py-1.5 rounded text-xs font-medium transition-all ${
              filter === cat 
                ? 'bg-[#00FFC2] text-black' 
                : 'text-white/50 hover:text-white/80'
            }`}
          >
            {cat.toUpperCase()}
          </button>
        ))}
      </div>

      {/* Worker Grid */}
      <div className="grid grid-cols-3 gap-2">
        <AnimatePresence>
          {filteredWorkers.map((worker, index) => {
            const Icon = iconMap[worker.id] || Brain;
            const isSelected = selectedId === worker.id;
            
            return (
              <motion.button
                key={worker.id}
                initial={{ opacity: 0, scale: 0.9 }}
                animate={{ opacity: 1, scale: 1 }}
                exit={{ opacity: 0, scale: 0.9 }}
                transition={{ delay: index * 0.02 }}
                onClick={() => onSelect(worker)}
                className={`relative p-3 rounded-xl border transition-all ${
                  isSelected
                    ? 'bg-[#00FFC2]/10 border-[#00FFC2]'
                    : 'bg-white/5 border-white/10 hover:bg-white/10'
                }`}
              >
                <Icon className={`w-5 h-5 mb-2 ${
                  isSelected ? 'text-[#00FFC2]' : 'text-white/60'
                }`} />
                <div className="text-[10px] font-medium truncate">
                  {worker.name}
                </div>
                <div className="text-[8px] text-white/30 mt-1">
                  {worker.category}
                </div>
                
                {/* Status Indicator */}
                <div className={`absolute top-2 right-2 w-1.5 h-1.5 rounded-full ${
                  worker.status === 'active' ? 'bg-green-400 animate-pulse' : 'bg-yellow-400'
                }`} />
              </motion.button>
            );
          })}
        </AnimatePresence>
      </div>
    </div>
  );
}
