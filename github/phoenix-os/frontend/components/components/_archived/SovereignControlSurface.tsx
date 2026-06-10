"use client";
import { useState } from 'react';
import { SovereignCard } from '@/components/ui/SovereignCard';
import {
  SovereignHeader,
  SovereignTabs,
  SOVEREIGN_TABS,
  SystemMetrics,
  AppGrid,
  DevTools,
  ResearchTools
} from '@/components/sovereign';
import { useApps } from '@/hooks/useApps';
import { Chrome, FileEdit, Calculator, Code, Music, MessageCircle, Terminal } from 'lucide-react';

const IconMap: Record<string, any> = {
  Chrome, FileEdit, Calculator, Code, Music, MessageCircle, Terminal
};

interface ControlSurfaceProps {
  onAction: (cmd: string) => void;
  stats: any;
}

export default function SovereignControlSurface({ onAction, stats }: ControlSurfaceProps) {
  const [activeTab, setActiveTab] = useState('SYSTEM');
  const { apps, removeApp } = useApps();
  const [editing, setEditing] = useState(false);

  const handleSettingsClick = () => setEditing(!editing);

  const renderTabContent = () => {
    switch (activeTab) {
      case 'SYSTEM':
        return (
          <div className="space-y-2">
            <SystemMetrics stats={stats} />
            <div className="grid grid-cols-2 gap-2 pt-2 border-t border-white/5">
              <button
                onClick={() => onAction('Check system health')}
                className="p-2 bg-white/5 hover:bg-white/10 rounded text-[10px] text-white/80 flex items-center gap-1 justify-center"
              >
                Vitals
              </button>
              <button
                onClick={() => onAction('List top processes')}
                className="p-2 bg-white/5 hover:bg-white/10 rounded text-[10px] text-white/80 flex items-center gap-1 justify-center"
              >
                Processes
              </button>
            </div>
          </div>
        );

      case 'APPS':
        return (
          <AppGrid
            apps={apps}
            onAction={onAction}
            onRemove={removeApp}
            editing={editing}
            iconMap={IconMap}
          />
        );

      case 'CODE':
        return <DevTools onAction={onAction} />;

      case 'RESEARCH':
        return <ResearchTools onAction={onAction} />;

      default:
        return null;
    }
  };

  return (
    <SovereignCard variant="glass" className="overflow-hidden">
      <SovereignHeader onSettingsClick={handleSettingsClick} isEditing={editing} />
      <SovereignTabs
        tabs={SOVEREIGN_TABS}
        activeTab={activeTab}
        onTabChange={setActiveTab}
      />
      <div className="p-3 space-y-3 max-h-[400px] overflow-y-auto">
        {renderTabContent()}
      </div>
    </SovereignCard>
  );
}
