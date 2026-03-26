'use client';

import { useState } from 'react';
import { 
  LayoutGrid, MessageSquare, Activity, Settings,
  Users, Cpu, HardDrive, Wifi, Shield, LogOut
} from 'lucide-react';

export function PremiumSidebar() {
  const [active, setActive] = useState('workers');
  
  const items = [
    { id: 'workers', icon: LayoutGrid, label: 'Workers' },
    { id: 'chat', icon: MessageSquare, label: 'Chat' },
    { id: 'monitor', icon: Activity, label: 'Monitor' },
    { id: 'system', icon: Cpu, label: 'System' },
    { id: 'network', icon: Wifi, label: 'Network' },
    { id: 'users', icon: Users, label: 'Users' },
    { id: 'security', icon: Shield, label: 'Security' },
    { id: 'settings', icon: Settings, label: 'Settings' },
  ];

  return (
    <div className="sidebar-premium">
      {/* Top Icons */}
      <div className="flex flex-col gap-1 w-full items-center">
        {items.map((item) => (
          <button
            key={item.id}
            onClick={() => setActive(item.id)}
            className={`sidebar-icon ${active === item.id ? 'active' : ''}`}
            title={item.label}
          >
            <item.icon size={20} />
          </button>
        ))}
      </div>
      
      {/* Spacer */}
      <div className="flex-1" />
      
      {/* Bottom Icons */}
      <div className="flex flex-col gap-1 w-full items-center">
        <button className="sidebar-icon" title="Logout">
          <LogOut size={20} />
        </button>
      </div>
    </div>
  );
}
