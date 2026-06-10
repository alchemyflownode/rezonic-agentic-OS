'use client';

import { motion } from 'framer-motion';
import { useSovereignStore } from '@/lib/store/useSovereignStore';

export default function WorkerHeatMap() {
  const { workers } = useSovereignStore();
  
  const workerTypes = {
    'GPU': { icon: '🎨', label: 'Vision/ComfyUI', color: '#7dcfff' },
    'CPU': { icon: '⚙️', label: 'Code/Execution', color: '#9ece6a' },
    'Memory': { icon: '🧠', label: 'Memory/Cortex', color: '#bb9af7' },
    'Network': { icon: '🌐', label: 'Search/API', color: '#7aa2f7' },
    'Trading': { icon: '💰', label: 'Trading/Backtest', color: '#ff9e64' },
  };
  
  const workersByType = workers.reduce((acc, w) => {
    const type = w.name.includes('GPU') ? 'GPU' :
                 w.name.includes('Code') ? 'CPU' :
                 w.name.includes('Memory') ? 'Memory' :
                 w.name.includes('Search') ? 'Network' : 'Trading';
    acc[type] = (acc[type] || 0) + 1;
    return acc;
  }, {} as Record<string, number>);
  
  return (
    <div className="bg-black/30 backdrop-blur-xl border border-[#7dcfff]/10 rounded-2xl p-5">
      <h3 className="text-[10px] text-[#565f89] font-mono tracking-wider mb-4">
        WORKER SWARM HEATMAP
      </h3>
      
      <div className="grid grid-cols-5 gap-2">
        {Object.entries(workerTypes).map(([type, { icon, label, color }]) => {
          const count = workersByType[type] || 0;
          const intensity = Math.min(1, count / 30);
          
          return (
            <motion.div
              key={type}
              whileHover={{ scale: 1.05 }}
              className="relative cursor-pointer"
            >
              <div
                className="aspect-square rounded-lg flex items-center justify-center text-xl transition-all"
                style={{
                  backgroundColor: `${color}${Math.floor(20 + intensity * 60).toString(16)}`,
                  boxShadow: intensity > 0.3 ? `0 0 10px ${color}` : 'none',
                }}
              >
                {icon}
              </div>
              <div className="absolute -bottom-1 -right-1 w-3 h-3 rounded-full bg-black/80 border border-[#7dcfff]/30 flex items-center justify-center text-[8px] font-mono text-white">
                {count}
              </div>
            </motion.div>
          );
        })}
      </div>
      
      <div className="flex justify-between mt-3 text-[8px] font-mono text-[#565f89]">
        <span>Idle</span>
        <div className="w-24 h-1 bg-white/10 rounded-full overflow-hidden">
          <div className="h-full w-1/3 bg-gradient-to-r from-[#9ece6a] to-[#ff9e64] rounded-full" />
        </div>
        <span>Saturated</span>
      </div>
    </div>
  );
}
