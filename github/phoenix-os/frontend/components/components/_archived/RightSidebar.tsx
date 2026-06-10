'use client';

import { Activity, Clock } from 'lucide-react';

export function RightSidebar() {
  const stats = [
    { label: 'CPU', value: '28%' },
    { label: 'RAM', value: '31%' },
    { label: 'GPU', value: '23%' },
    { label: 'NEURAL', value: '42%' }
  ];

  const activities = [
    { action: 'Check system health', time: '2m ago' },
    { action: 'Open Chrome', time: '5m ago' },
    { action: 'Deep search: AI news', time: '10m ago' },
    { action: 'System update', time: '15m ago' },
    { action: 'Code mutation', time: '22m ago' }
  ];

  return (
    <div className="h-full flex flex-col gap-4">
      {/* Stats Grid */}
      <div className="premium-panel p-4">
        <h2 className="text-sm font-semibold text-white mb-4 flex items-center gap-2">
          <Activity className="w-4 h-4 text-[#00FFC2]" />
          SYSTEM METRICS
        </h2>
        
        <div className="grid grid-cols-2 gap-3">
          {stats.map((stat, i) => (
            <div key={i} className="stat-card">
              <div className="stat-value">{stat.value}</div>
              <div className="stat-label">{stat.label}</div>
            </div>
          ))}
        </div>
      </div>
      
      {/* Activity Log */}
      <div className="premium-panel flex-1 p-4 overflow-y-auto">
        <h2 className="text-sm font-semibold text-white mb-4 flex items-center gap-2">
          <Clock className="w-4 h-4 text-[#00FFC2]" />
          ACTIVITY LOG
        </h2>
        
        <table className="activity-table">
          <thead>
            <tr>
              <th>Action</th>
              <th>Time</th>
            </tr>
          </thead>
          <tbody>
            {activities.map((activity, i) => (
              <tr key={i}>
                <td>{activity.action}</td>
                <td className="activity-time">{activity.time}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

