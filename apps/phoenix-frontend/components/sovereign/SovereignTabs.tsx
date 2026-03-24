'use client';

import { Cpu, Rocket, Code, Search } from 'lucide-react';

interface Tab {
  id: string;
  label: string;
  icon: any;
}

interface SovereignTabsProps {
  tabs: Tab[];
  activeTab: string;
  onTabChange: (tabId: string) => void;
}

export function SovereignTabs({ tabs, activeTab, onTabChange }: SovereignTabsProps) {
  return (
    <div className="flex border-b border-white/10">
      {tabs.map(tab => {
        const Icon = tab.icon;
        return (
          <button
            key={tab.id}
            onClick={() => onTabChange(tab.id)}
            className={`flex-1 p-2 text-[10px] flex flex-col items-center gap-1 transition-colors ${
              activeTab === tab.id
                ? 'bg-purple-600/20 text-purple-300 border-b-2 border-purple-500'
                : 'text-white/50 hover:bg-white/5'
            }`}
            aria-selected={activeTab === tab.id}
            role="tab"
          >
            <Icon className="w-3 h-3" />
            {tab.label}
          </button>
        );
      })}
    </div>
  );
}

export const SOVEREIGN_TABS = [
  { id: 'SYSTEM', label: 'System', icon: Cpu },
  { id: 'APPS', label: 'Apps', icon: Rocket },
  { id: 'CODE', label: 'Dev', icon: Code },
  { id: 'RESEARCH', label: 'Research', icon: Search }
];
