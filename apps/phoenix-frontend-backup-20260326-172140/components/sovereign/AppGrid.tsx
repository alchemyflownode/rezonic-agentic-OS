'use client';

import { Terminal, X } from 'lucide-react';

interface App {
  id: string;
  name: string;
  icon: string;
  command: string;
}

interface AppGridProps {
  apps: App[];
  onAction: (command: string) => void;
  onRemove: (id: string) => void;
  editing: boolean;
  iconMap: Record<string, any>;
}

export function AppGrid({ apps, onAction, onRemove, editing, iconMap }: AppGridProps) {
  return (
    <div className="grid grid-cols-3 gap-2">
      {apps.map(app => {
        const IconComponent = iconMap[app.icon] || Terminal;
        return (
          <div key={app.id} className="relative group">
            <button
              onClick={() => onAction(app.command)}
              className="w-full p-3 bg-white/5 hover:bg-blue-500/20 border border-white/10 hover:border-blue-500/50 rounded-lg flex flex-col items-center gap-1 transition-all"
              aria-label={`Launch ${app.name}`}
            >
              <IconComponent className="w-4 h-4 text-blue-400" />
              <span className="text-[9px] text-white/80">{app.name}</span>
            </button>

            {editing && (
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  onRemove(app.id);
                }}
                className="absolute -top-1 -right-1 bg-red-500 rounded-full p-0.5 opacity-0 group-hover:opacity-100 transition-opacity"
                aria-label={`Remove ${app.name}`}
              >
                <X className="w-2 h-2 text-white" />
              </button>
            )}
          </div>
        );
      })}
    </div>
  );
}
