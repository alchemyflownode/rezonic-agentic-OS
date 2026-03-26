'use client';

import { Shield, Users } from 'lucide-react';

export function LeftSidebar() {
  const constitution = [
    "Preserve user privacy",
    "Verify before code execution",
    "No unauthorized deletion",
    "System watches continuously"
  ];

  const workers = [
    "system_monitor",
    "deepsearch",
    "cortex",
    "mutation"
  ];

  return (
    <div className="h-full flex flex-col gap-4">
      {/* Constitution Panel */}
      <div className="premium-panel flex-1 p-4 overflow-y-auto">
        <h2 className="text-sm font-semibold text-white mb-4 flex items-center gap-2">
          <Shield className="w-4 h-4 text-[#00FFC2]" />
          CONSTITUTION
        </h2>
        
        <div className="space-y-1">
          {constitution.map((item, i) => (
            <div key={i} className="constitution-item">
              {item}
            </div>
          ))}
        </div>
        
        <div className="mt-4 flex flex-wrap gap-2">
          <span className="worker-badge">PRIVACY</span>
          <span className="worker-badge">LOCAL</span>
          <span className="worker-badge">SECURE</span>
        </div>
      </div>
      
      {/* Workers Panel */}
      <div className="premium-panel p-4">
        <h2 className="text-sm font-semibold text-white mb-4 flex items-center gap-2">
          <Users className="w-4 h-4 text-[#00FFC2]" />
          ACTIVE WORKERS
        </h2>
        
        <div className="space-y-2">
          {workers.map((worker, i) => (
            <div key={i} className="worker-badge active w-full justify-start">
              <span>{worker}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
