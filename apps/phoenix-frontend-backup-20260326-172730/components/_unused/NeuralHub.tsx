// src/components/NeuralHub.tsx
'use client';

import { motion, AnimatePresence } from 'framer-motion';
import { useEffect, useState } from 'react';
import { VantaGlass } from './ui/VantaGlass';
import { neuralBus, WorkerType } from '@/lib/kernel/event-bus';
import { Brain, Activity, Cpu, Eye, Search, Code, Zap, Shield } from 'lucide-react';

const rezSpring = { type: "spring", stiffness: 300, damping: 30 };

const workerIcons: Record<WorkerType, any> = {
  vision: Eye,
  deepsearch: Search,
  mutation: Code,
  code: Code,
  app: Activity,
  file: Activity,
  voice: Activity,
  system_monitor: Cpu,
  architect: Brain,
  discover: Search,
  heal: Shield,
  learn: Brain,
  autonomous: Zap,
  director: Brain,
  sce: Brain,
  canvas: Activity,
  mcp: Activity,
  rezstack: Brain,
  governor: Shield,
  heartbeat: Activity
};

interface WorkerTileProps {
  worker: WorkerType;
  active: boolean;
  lastEvent?: any;
}

function WorkerTile({ worker, active, lastEvent }: WorkerTileProps) {
  const Icon = workerIcons[worker] || Activity;
  
  return (
    <motion.div
      layout
      transition={rezSpring}
      className={`
        relative p-4 rounded-2xl backdrop-blur-md border transition-all
        ${active 
          ? 'bg-purple-500/10 border-purple-500/30 shadow-[0_0_30px_rgba(168,85,247,0.2)]' 
          : 'bg-white/5 border-white/10 hover:border-white/20'
        }
      `}
    >
      <div className="flex items-center gap-3">
        <div className="relative">
          <Icon className={`w-4 h-4 ${active ? 'text-purple-400' : 'text-white/40'}`} />
          {active && (
            <span className="absolute -top-1 -right-1 flex h-2 w-2">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-green-400 opacity-75" />
              <span className="relative inline-flex rounded-full h-2 w-2 bg-green-500" />
            </span>
          )}
        </div>
        <span className="text-xs font-mono capitalize text-white/70">{worker}</span>
      </div>
      
      {lastEvent && (
        <div className="mt-2 text-[8px] font-mono text-white/30 truncate">
          {lastEvent.type}: {JSON.stringify(lastEvent.data).slice(0, 30)}
        </div>
      )}
    </motion.div>
  );
}

export function NeuralHub() {
  const [activeWorkers, setActiveWorkers] = useState<WorkerType[]>([]);
  const [workerEvents, setWorkerEvents] = useState<Map<WorkerType, any>>(new Map());
  const [neuralLoad, setNeuralLoad] = useState([40, 70, 45, 90, 65]);

  useEffect(() => {
    // Subscribe to all events
    const id = neuralBus.subscribe((event) => {
      setActiveWorkers(neuralBus.getActiveWorkers());
      setWorkerEvents(prev => new Map(prev).set(event.worker, event));
      
      // Animate neural load based on active workers
      setNeuralLoad(prev => 
        prev.map(() => Math.floor(Math.random() * 60) + 20)
      );
    });

    return () => neuralBus.unsubscribe(id);
  }, []);

  return (
    <div className="grid grid-cols-12 grid-rows-6 gap-4 p-6 h-screen w-full bg-[var(--bg-deep)] overflow-hidden">
      {/* Main Orchestrator - REZ HIVE Core */}
      <VantaGlass layer="mantle" className="col-span-8 row-span-4">
        <div className="absolute top-6 left-8 flex items-center gap-3">
          <motion.div 
            animate={{ scale: [1, 1.2, 1] }}
            transition={{ duration: 2, repeat: Infinity }}
            className="h-3 w-3 rounded-full bg-purple-500"
          />
          <span className="text-xs font-mono tracking-[0.3em] text-white/40 uppercase">
            Neural Core • {activeWorkers.length} Active
          </span>
        </div>
        
        {/* Neural Activity Visualization */}
        <div className="absolute bottom-8 left-8 right-8">
          <div className="flex items-end gap-1 h-24">
            {neuralLoad.map((h, i) => (
              <motion.div 
                key={i}
                animate={{ height: `${h}%` }}
                transition={{ duration: 0.5 }}
                className="flex-1 bg-gradient-to-t from-purple-600 to-blue-400 rounded-full"
                style={{ opacity: 0.3 + (h / 100) * 0.7 }}
              />
            ))}
          </div>
        </div>
      </VantaGlass>

      {/* Hardware Vitals */}
      <VantaGlass layer="mantle" className="col-span-4 row-span-2 p-6">
        <h4 className="text-white/30 text-[10px] uppercase tracking-tighter mb-4">
          NPU Neural Load
        </h4>
        <div className="flex items-end gap-1 h-16">
          {neuralLoad.map((h, i) => (
            <motion.div 
              key={i}
              animate={{ height: `${h}%` }}
              transition={{ duration: 0.5 }}
              className="flex-1 bg-gradient-to-t from-purple-600 to-blue-400 rounded-full"
            />
          ))}
        </div>
      </VantaGlass>

      {/* Autonomous Worker Feed */}
      <VantaGlass layer="crust" className="col-span-4 row-span-4 p-4 overflow-y-auto">
        <span className="text-[10px] text-white/20 uppercase tracking-widest px-2 mb-4 block">
          Active Protocols • {activeWorkers.length}
        </span>
        <div className="space-y-2">
          <AnimatePresence>
            {activeWorkers.map(worker => (
              <motion.div
                key={worker}
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: 20 }}
                className="flex items-center gap-4 p-3 hover:bg-white/5 rounded-xl transition-colors"
              >
                <div className="h-2 w-2 rounded-full bg-blue-500 shadow-[0_0_10px_var(--accent-blue)]" />
                <span className="text-sm text-white/70 font-light capitalize">{worker}</span>
                <span className="ml-auto text-[8px] text-white/30 font-mono">
                  active
                </span>
              </motion.div>
            ))}
          </AnimatePresence>
        </div>
      </VantaGlass>

      {/* Worker Grid */}
      <VantaGlass layer="crust" className="col-span-8 row-span-2 p-4">
        <div className="grid grid-cols-6 gap-2">
          {Object.keys(workerIcons).slice(0, 12).map((worker) => (
            <WorkerTile 
              key={worker}
              worker={worker as WorkerType}
              active={activeWorkers.includes(worker as WorkerType)}
              lastEvent={workerEvents.get(worker as WorkerType)}
            />
          ))}
        </div>
      </VantaGlass>
    </div>
  );
}

