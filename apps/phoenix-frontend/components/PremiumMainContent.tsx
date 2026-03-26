'use client';

import { motion, AnimatePresence } from 'framer-motion';
import { useState } from 'react';
import { 
  Play, Save, Download, Upload,
  Plus, X, Check, AlertCircle
} from 'lucide-react';

export function PremiumMainContent() {
  const [activeTab, setActiveTab] = useState('design');
  const [items] = useState([
    { id: 1, name: 'Project Alpha', type: 'design', updated: '2m ago' },
    { id: 2, name: 'System Analysis', type: 'code', updated: '5m ago' },
    { id: 3, name: 'AI Workflow', type: 'design', updated: '10m ago' },
    { id: 4, name: 'Data Pipeline', type: 'code', updated: '15m ago' },
  ]);

  return (
    <div className="h-full flex flex-col">
      {/* Tab Bar */}
      <div className="flex items-center gap-1 p-1 bg-[#252525] rounded-t-lg border-b border-white/10">
        <div className="tabs">
          <button 
            className={`tab ${activeTab === 'design' ? 'active' : ''}`}
            onClick={() => setActiveTab('design')}
          >
            Design
          </button>
          <button 
            className={`tab ${activeTab === 'code' ? 'active' : ''}`}
            onClick={() => setActiveTab('code')}
          >
            Code
          </button>
          <button 
            className={`tab ${activeTab === 'review' ? 'active' : ''}`}
            onClick={() => setActiveTab('review')}
          >
            Review
          </button>
        </div>
        
        <div className="flex-1" />
        
        <button className="toolbar-button"><Save size={14} /> Save</button>
        <button className="toolbar-button primary"><Play size={14} /> Run</button>
      </div>
      
      {/* Content Area */}
      <div className="flex-1 p-4 overflow-y-auto">
        <div className="grid grid-cols-2 gap-4">
          <AnimatePresence>
            {items
              .filter(item => activeTab === 'all' || item.type === activeTab)
              .map((item, index) => (
                <motion.div
                  key={item.id}
                  className="card"
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, scale: 0.9 }}
                  transition={{ delay: index * 0.1 }}
                  whileHover={{ y: -2 }}
                >
                  <div className="flex items-start justify-between mb-2">
                    <h3 className="font-medium">{item.name}</h3>
                    <span className="badge blue text-[10px]">{item.type}</span>
                  </div>
                  <p className="text-xs text-white/50">Updated {item.updated}</p>
                  <div className="flex gap-2 mt-3">
                    <button className="text-xs px-2 py-1 bg-white/5 hover:bg-white/10 rounded">
                      Open
                    </button>
                    <button className="text-xs px-2 py-1 hover:bg-white/5 rounded">
                      Details
                    </button>
                  </div>
                </motion.div>
              ))}
          </AnimatePresence>
        </div>
      </div>
      
      {/* Status Bar */}
      <div className="flex items-center gap-4 p-2 bg-[#252525] border-t border-white/10 text-xs text-white/50">
        <span>CPU: 23%</span>
        <span>RAM: 4.2GB</span>
        <span>AI Model: Ready</span>
        <div className="flex-1" />
        <span className="flex items-center gap-1">
          <span className="w-1.5 h-1.5 bg-green-500 rounded-full animate-pulse" />
          Connected
        </span>
      </div>
    </div>
  );
}
