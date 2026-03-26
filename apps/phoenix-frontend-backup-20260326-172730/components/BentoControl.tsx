'use client';

import { useState } from 'react';
import { cn } from '@/lib/utils';
import { 
  Lock, Globe, Cpu, Shield, Wifi, Battery,
  Zap, Cloud, Key, Bell, Volume2, Sun
} from 'lucide-react';
import { SovereignCard } from './ui/SovereignCard';

interface BentoTileProps {
  icon: any;
  title: string;
  value?: string;
  active?: boolean;
  onClick?: () => void;
  size?: 'sm' | 'md' | 'lg';
  glowColor?: 'purple' | 'green' | 'amber' | 'blue';
}

function BentoTile({ icon: Icon, title, value, active, onClick, size = 'md', glowColor = 'purple' }: BentoTileProps) {
  const [isHovered, setIsHovered] = useState(false);
  
  const sizeClasses = {
    sm: 'col-span-1 row-span-1 p-3',
    md: 'col-span-1 row-span-1 p-4',
    lg: 'col-span-2 row-span-1 p-4'
  };

  return (
    <button
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
      onClick={onClick}
      className={cn(
        'relative group bg-black/40 backdrop-blur-xl rounded-2xl border transition-all duration-300',
        active ? 'border-purple-500/50 bg-purple-500/10' : 'border-white/10 hover:border-white/20',
        isHovered && 'scale-[1.02]',
        sizeClasses[size]
      )}
      style={{
        boxShadow: isHovered ? `0 0 30px rgba(139,92,246,0.2)` : undefined
      }}
    >
      <div className="flex flex-col items-start justify-between h-full">
        <div className="flex items-center justify-between w-full">
          <Icon className={cn(
            'w-4 h-4 transition-colors',
            active ? 'text-purple-400' : 'text-white/50'
          )} />
          {value && (
            <span className="text-[10px] font-mono text-white/40">{value}</span>
          )}
        </div>
        <span className={cn(
          'text-xs font-medium',
          active ? 'text-white' : 'text-white/70'
        )}>
          {title}
        </span>
      </div>

      {/* Hover glow */}
      {isHovered && (
        <div className="absolute inset-0 rounded-2xl bg-gradient-to-r from-purple-500/0 via-purple-500/5 to-transparent pointer-events-none" />
      )}
    </button>
  );
}

interface BentoControlProps {
  onTogglePrivacy?: (enabled: boolean) => void;
  onSelectModel?: (model: string) => void;
  className?: string;
}

export function BentoControl({ onTogglePrivacy, onSelectModel, className }: BentoControlProps) {
  const [privacyMode, setPrivacyMode] = useState(true);
  const [selectedModel, setSelectedModel] = useState('qwen2.5:3b');
  const [activeTiles, setActiveTiles] = useState<string[]>(['privacy', 'local']);

  const models = [
    { id: 'qwen2.5:3b', name: 'Fast', speed: 120, quality: 70 },
    { id: 'deepseek-coder:6.7b', name: 'Code', speed: 60, quality: 85 },
    { id: 'gemma2:9b', name: 'Balanced', speed: 45, quality: 90 }
  ];

  const togglePrivacy = () => {
    const newState = !privacyMode;
    setPrivacyMode(newState);
    setActiveTiles(prev => 
      newState ? [...prev, 'privacy'] : prev.filter(t => t !== 'privacy')
    );
    onTogglePrivacy?.(newState);
  };

  return (
    <SovereignCard 
      variant="ultra-thin" 
      glowColor="purple"
      animate={false}
      className={cn(
        'fixed top-20 right-6 w-80',
        className
      )}
    >
      <div className="p-4">
        <h3 className="text-xs font-mono text-white/50 mb-3 tracking-wider">CONTROL CENTER</h3>
        
        {/* Privacy Toggle - Physical-looking switch */}
        <div className="mb-4 p-3 bg-white/5 rounded-xl">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Shield className={cn(
                'w-4 h-4',
                privacyMode ? 'text-green-400' : 'text-white/30'
              )} />
              <span className="text-xs text-white/80">Local-Only Mode</span>
            </div>
            <button
              onClick={togglePrivacy}
              className={cn(
                'relative w-10 h-5 rounded-full transition-colors duration-300',
                privacyMode ? 'bg-green-500' : 'bg-white/20'
              )}
            >
              <div className={cn(
                'absolute top-0.5 left-0.5 w-4 h-4 bg-white rounded-full transition-transform duration-300',
                privacyMode && 'transform translate-x-5'
              )} />
            </button>
          </div>
          {privacyMode && (
            <div className="mt-2 text-[10px] text-amber-400 flex items-center gap-1">
              <Lock className="w-3 h-3" />
              <span>All processing stays local. No cloud data.</span>
            </div>
          )}
        </div>

        {/* Model Selector */}
        <div className="mb-4">
          <label className="text-[10px] text-white/40 mb-2 block">ACTIVE MODEL</label>
          <div className="grid grid-cols-3 gap-2">
            {models.map((model) => (
              <button
                key={model.id}
                onClick={() => {
                  setSelectedModel(model.id);
                  onSelectModel?.(model.id);
                }}
                className={cn(
                  'p-2 rounded-lg border transition-all text-center',
                  selectedModel === model.id 
                    ? 'border-purple-500 bg-purple-500/20' 
                    : 'border-white/10 hover:border-white/20'
                )}
              >
                <div className="text-[10px] font-mono text-white/90">{model.name}</div>
                <div className="text-[8px] text-white/40">{model.speed} tok/s</div>
              </button>
            ))}
          </div>
        </div>

        {/* Bento Grid */}
        <div className="grid grid-cols-2 gap-2 auto-rows-fr">
          <BentoTile
            icon={Cpu}
            title="Neural Core"
            value="45%"
            active={activeTiles.includes('neural')}
            size="md"
          />
          <BentoTile
            icon={Wifi}
            title="Network"
            value="Online"
            active={activeTiles.includes('network')}
            size="md"
            glowColor="blue"
          />
          <BentoTile
            icon={Battery}
            title="Power"
            value="87%"
            active={activeTiles.includes('power')}
            size="sm"
            glowColor="green"
          />
          <BentoTile
            icon={Volume2}
            title="Audio"
            value="75%"
            active={activeTiles.includes('audio')}
            size="sm"
            glowColor="blue"
          />
          <BentoTile
            icon={Sun}
            title="Display"
            value="Auto"
            active={activeTiles.includes('display')}
            size="sm"
            glowColor="amber"
          />
          <BentoTile
            icon={Bell}
            title="Focus"
            value="On"
            active={activeTiles.includes('focus')}
            size="sm"
            glowColor="purple"
          />
        </div>

        {/* System Status */}
        <div className="mt-4 pt-3 border-t border-white/10">
          <div className="flex items-center justify-between text-[10px]">
            <span className="text-white/40">NPU Load</span>
            <span className="text-white/80">23%</span>
          </div>
          <div className="w-full h-1 bg-white/10 rounded-full mt-1">
            <div className="w-[23%] h-full bg-gradient-to-r from-purple-500 to-blue-500 rounded-full" />
          </div>
        </div>
      </div>
    </SovereignCard>
  );
}
