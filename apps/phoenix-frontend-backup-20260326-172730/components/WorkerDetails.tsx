'use client';

import { useState } from 'react';
import { motion } from 'framer-motion';
import { Play, Clock, BarChart2, AlertCircle } from 'lucide-react';

interface WorkerDetailsProps {
  worker: any;
  onExecute: (task: string) => void;
  isLoading: boolean;
  result: any;
  stats: any;
}

export function WorkerDetails({ worker, onExecute, isLoading, result, stats }: WorkerDetailsProps) {
  const [task, setTask] = useState('');

  if (!worker) {
    return (
      <div className="h-full flex items-center justify-center text-white/30">
        <p className="text-sm">Select a worker from the grid</p>
      </div>
    );
  }

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      className="space-y-4"
    >
      {/* Worker Header */}
      <div>
        <h3 className="text-base font-medium text-white/90">{worker.name}</h3>
        <p className="text-xs text-white/40 mt-1">{worker.description}</p>
        <div className="flex items-center gap-2 mt-2">
          <span className="text-[10px] px-2 py-0.5 bg-white/10 rounded-full">
            {worker.category}
          </span>
          <span className="text-[10px] px-2 py-0.5 bg-white/10 rounded-full font-mono">
            {worker.endpoint}
          </span>
        </div>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 gap-2">
        <div className="bg-white/5 rounded-lg p-3">
          <div className="flex items-center gap-1 text-[10px] text-white/30 mb-1">
            <Clock className="w-3 h-3" /> Last Used
          </div>
          <div className="text-xs">
            {stats?.lastUsed ? new Date(stats.lastUsed).toLocaleTimeString() : 'Never'}
          </div>
        </div>
        <div className="bg-white/5 rounded-lg p-3">
          <div className="flex items-center gap-1 text-[10px] text-white/30 mb-1">
            <BarChart2 className="w-3 h-3" /> Usage
          </div>
          <div className="text-xs">{stats?.usageCount || 0} times</div>
        </div>
      </div>

      {/* Task Input */}
      <div>
        <label className="text-xs text-white/50 mb-2 block">Execute Task</label>
        <textarea
          value={task}
          onChange={(e) => setTask(e.target.value)}
          placeholder={`Enter command for ${worker.name}...`}
          rows={4}
          className="obsidian-input w-full resize-none"
        />
        
        <button
          onClick={() => onExecute(task)}
          disabled={!task.trim() || isLoading}
          className="obsidian-button primary w-full mt-3 flex items-center justify-center gap-2"
        >
          {isLoading ? (
            <>
              <div className="w-4 h-4 border-2 border-black border-t-transparent rounded-full animate-spin" />
              <span>Executing...</span>
            </>
          ) : (
            <>
              <Play className="w-4 h-4" />
              <span>Execute</span>
            </>
          )}
        </button>
      </div>

      {/* Result */}
      {result && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          className="p-3 bg-white/5 rounded-lg border border-cyan-500/30"
        >
          <div className="flex items-center gap-2 mb-2">
            <AlertCircle className="w-4 h-4 text-cyan-400" />
            <span className="text-xs font-medium text-white/80">Result</span>
          </div>
          <pre className="text-[10px] text-white/60 whitespace-pre-wrap font-mono max-h-40 overflow-y-auto">
            {JSON.stringify(result, null, 2)}
          </pre>
        </motion.div>
      )}
    </motion.div>
  );
}
