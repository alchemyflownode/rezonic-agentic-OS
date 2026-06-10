'use client';

import { useState, useEffect } from 'react';
import { cn } from '@/lib/utils';
import { 
  Chrome, Terminal, Code, Music, MessageCircle, 
  Settings, HardDrive, Cpu, Brain, Activity 
} from 'lucide-react';
import { SovereignCard } from './SovereignCard';

interface DockItem {
  id: string;
  icon: any;
  label: string;
  action: () => void;
  glowColor?: 'purple' | 'green' | 'amber' | 'blue';
}

interface AeroDockProps {
  onItemClick?: (id: string) => void;
  npuActive?: boolean;
  className?: string;
}

export function AeroDock({ onItemClick, npuActive = false, className }: AeroDockProps) {
  const [hoveredItem, setHoveredItem] = useState<string | null>(null);
  const [dockItems, setDockItems] = useState<DockItem[]>([
    { id: 'chrome', icon: Chrome, label: 'Chrome', action: () => {}, glowColor: 'blue' },
    { id: 'terminal', icon: Terminal, label: 'Terminal', action: () => {}, glowColor: 'green' },
    { id: 'code', icon: Code, label: 'VS Code', action: () => {}, glowColor: 'purple' },
    { id: 'spotify', icon: Music, label: 'Spotify', action: () => {}, glowColor: 'green' },
    { id: 'discord', icon: MessageCircle, label: 'Discord', action: () => {}, glowColor: 'purple' },
    { id: 'settings', icon: Settings, label: 'Settings', action: () => {}, glowColor: 'amber' }
  ]);

  // Neural Core (Central NPU indicator)
  const NeuralCore = () => (
    <div className="relative mx-2">
      <div className={cn(
        'w-14 h-14 rounded-2xl bg-gradient-to-br from-purple-600 to-blue-600 flex items-center justify-center cursor-pointer transition-all duration-300',
        'border-2 border-white/20 shadow-[0_0_30px_rgba(139,92,246,0.5)]',
        npuActive && 'animate-pulse'
      )}>
        <Brain className="w-6 h-6 text-white" />
      </div>
      {npuActive && (
        <div className="absolute -top-1 -right-1 w-3 h-3">
          <span className="absolute inline-flex w-full h-full bg-green-400 rounded-full opacity-75 animate-ping" />
          <span className="relative inline-flex w-3 h-3 bg-green-500 rounded-full" />
        </div>
      )}
    </div>
  );

  return (
    <SovereignCard 
      variant="ultra-thin" 
      glowColor="purple"
      animate={false}
      className={cn(
        'fixed bottom-8 left-1/2 transform -translate-x-1/2',
        'px-4 py-2 flex items-center gap-1',
        'backdrop-blur-[40px] bg-black/30',
        className
      )}
    >
      {/* Dock Items */}
      <div className="flex items-center gap-1">
        {dockItems.map((item) => {
          const Icon = item.icon;
          const isHovered = hoveredItem === item.id;
          
          return (
            <button
              key={item.id}
              onMouseEnter={() => setHoveredItem(item.id)}
              onMouseLeave={() => setHoveredItem(null)}
              onClick={() => {
                item.action();
                onItemClick?.(item.id);
              }}
              className="relative group"
            >
              <div className={cn(
                'w-12 h-12 rounded-xl flex items-center justify-center transition-all duration-200',
                'hover:bg-white/10',
                isHovered && 'scale-110 -translate-y-1'
              )}>
                <Icon className={cn(
                  'w-5 h-5 transition-all duration-200',
                  isHovered ? 'text-white scale-110' : 'text-white/70'
                )} />
              </div>
              
              {/* Label Tooltip */}
              {isHovered && (
                <div className="absolute -top-8 left-1/2 transform -translate-x-1/2 px-2 py-1 bg-black/80 backdrop-blur rounded text-[10px] text-white/90 whitespace-nowrap border border-white/10">
                  {item.label}
                </div>
              )}
              
              {/* Active Glow */}
              {isHovered && (
                <div className={cn(
                  'absolute inset-0 rounded-xl opacity-20 blur-lg transition-opacity',
                  `bg-${item.glowColor}-500`
                )} />
              )}
            </button>
          );
        })}
      </div>

      {/* Neural Core */}
      <NeuralCore />

      {/* Divider */}
      <div className="w-px h-8 bg-white/10 mx-1" />

      {/* System Tray */}
      <button className="w-10 h-10 rounded-xl flex items-center justify-center hover:bg-white/10 transition-all">
        <Activity className="w-4 h-4 text-white/70" />
      </button>
    </SovereignCard>
  );
}
