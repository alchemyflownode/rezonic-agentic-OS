"use client";
import { Home, Cpu, Search, Code, Settings, Zap } from 'lucide-react';

const navItems = [
  { icon: Home, label: 'Home', active: false },
  { icon: Cpu, label: 'System', active: true },
  { icon: Search, label: 'Search', active: false },
  { icon: Code, label: 'Code', active: false },
  { icon: Zap, label: 'Workers', active: false },
  { icon: Settings, label: 'Config', active: false }
];

export function SovereignSidebar() {
  return (
    <aside className="sidebar">
      {navItems.map((item, i) => (
        <div key={i} className={`sidebar-icon ${item.active ? 'active' : ''}`} title={item.label}>
          <item.icon size={22} strokeWidth={1.5} />
        </div>
      ))}
    </aside>
  );
}
