'use client'

"use client";

import { useState, useEffect } from 'react';
import { io } from 'socket.io-client';
import { 
  Users, Cpu, Database, Activity, Zap, Shield, Brain, Code, 
  FileText, Mic, Eye, Folder, GitBranch, TestTube, RefreshCw,
  ChevronDown, ChevronRight, Search
} from 'lucide-react';

export default function WorkersPage() {
  const [workers, setWorkers] = useState<any[]>([]);
  const [workerCount, setWorkerCount] = useState(0);
  const [coworkerCount, setCoworkerCount] = useState(0);
  const [connected, setConnected] = useState(false);
  const [expandedCategories, setExpandedCategories] = useState<Set<string>>(new Set(['core', 'skills', 'agents']));
  const [searchTerm, setSearchTerm] = useState('');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const socket = io('http://localhost:8002', {
      transports: ['websocket'],
      reconnection: true,
    });

    socket.on('connect', () => {
      console.log(' WebSocket connected');
      setConnected(true);
      socket.emit('get_workers');
    });

    socket.on('workers_update', (data: any) => {
      console.log('Workers update:', data);
      if (data.workers) {
        const allWorkers = data.workers;
        setWorkers(allWorkers);
        setWorkerCount(allWorkers.length);
        
        // Count coworker workers
        const coworkerWorkers = allWorkers.filter((w: any) => 
          w.name?.toLowerCase().includes('coworker') || 
          w.category === 'coworker' ||
          (w.path && w.path.includes('coworker'))
        );
        setCoworkerCount(coworkerWorkers.length);
        setLoading(false);
      }
    });

    return () => {
      socket.disconnect();
    };
  }, []);

  const toggleCategory = (category: string) => {
    const newSet = new Set(expandedCategories);
    if (newSet.has(category)) {
      newSet.delete(category);
    } else {
      newSet.add(category);
    }
    setExpandedCategories(newSet);
  };

  const getCategoryIcon = (category: string) => {
    switch(category) {
      case 'core': return <Cpu className="w-4 h-4" />;
      case 'skills': return <Activity className="w-4 h-4" />;
      case 'agents': return <Brain className="w-4 h-4" />;
      case 'tools': return <Code className="w-4 h-4" />;
      default: return <Zap className="w-4 h-4" />;
    }
  };

  const getWorkerIcon = (workerName: string) => {
    const name = workerName.toLowerCase();
    if (name.includes('brain')) return <Brain className="w-4 h-4 text-[#bb9af7]" />;
    if (name.includes('code') || name.includes('execution')) return <Code className="w-4 h-4 text-[#7dcfff]" />;
    if (name.includes('vision')) return <Eye className="w-4 h-4 text-[#9ece6a]" />;
    if (name.includes('voice')) return <Mic className="w-4 h-4 text-[#ff9e64]" />;
    if (name.includes('file') || name.includes('fs')) return <Folder className="w-4 h-4 text-[#f7768e]" />;
    if (name.includes('test')) return <TestTube className="w-4 h-4 text-[#bb9af7]" />;
    if (name.includes('git')) return <GitBranch className="w-4 h-4 text-[#7dcfff]" />;
    return <Zap className="w-4 h-4 text-[#565f89]" />;
  };

  // Group workers by category
  const groupedWorkers = workers.reduce((acc: any, worker: any) => {
    let category = worker.category || 'general';
    if (worker.name?.toLowerCase().includes('coworker')) category = 'coworker';
    if (!acc[category]) acc[category] = [];
    acc[category].push(worker);
    return acc;
  }, {});

  const categories = [
    { id: 'coworker', name: ' Coworker AI Agents', icon: Users, count: coworkerCount, color: '#bb9af7' },
    { id: 'core', name: ' Core Workers', icon: Cpu, count: 0, color: '#7dcfff' },
    { id: 'agents', name: ' AI Agents', icon: Brain, count: 0, color: '#9ece6a' },
    { id: 'skills', name: ' Skills & Capabilities', icon: Activity, count: 0, color: '#ff9e64' },
    { id: 'tools', name: ' Tools & Utilities', icon: Code, count: 0, color: '#f7768e' },
  ];

  // Update counts
  categories.forEach(cat => {
    cat.count = groupedWorkers[cat.id]?.length || 0;
  });

  const filteredWorkers = (workers: any[]) => {
    if (!searchTerm) return workers;
    return workers.filter(w => 
      w.name?.toLowerCase().includes(searchTerm.toLowerCase()) ||
      w.category?.toLowerCase().includes(searchTerm.toLowerCase()) ||
      (w.path && w.path.toLowerCase().includes(searchTerm.toLowerCase()))
    );
  };

  return (
    <div className="min-h-screen bg-[#1a1b26]">
      {/* Header */}
      <div className="border-b border-[#292e42] bg-[#24283b]/30 backdrop-blur-sm sticky top-0 z-10">
        <div className="max-w-7xl mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-[#7dcfff] to-[#bb9af7] flex items-center justify-center">
                <Users className="w-5 h-5 text-[#1a1b26]" />
              </div>
              <div>
                <h1 className="text-xl font-bold text-[#c0caf5]">Worker Pool</h1>
                <p className="text-xs text-[#565f89]">{workerCount} active workers  {coworkerCount} coworker agents</p>
              </div>
            </div>
            <div className={`px-3 py-1 rounded-full text-xs ${connected ? 'bg-green-500/20 text-green-400' : 'bg-red-500/20 text-red-400'}`}>
              {connected ? ' WEBSOCKET CONNECTED' : ' OFFLINE'}
            </div>
          </div>
        </div>
      </div>

      {/* Search Bar */}
      <div className="max-w-7xl mx-auto px-6 py-4">
        <div className="relative">
          <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-[#565f89]" />
          <input
            type="text"
            placeholder="Search workers by name, category, or path..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full bg-[#24283b] border border-[#292e42] rounded-lg py-2 pl-9 pr-4 text-sm text-[#c0caf5] placeholder:text-[#565f89] focus:outline-none focus:border-[#7dcfff] transition-colors"
          />
        </div>
      </div>

      {/* Worker Categories */}
      <div className="max-w-7xl mx-auto px-6 pb-8">
        {loading ? (
          <div className="flex items-center justify-center py-20">
            <div className="text-center">
              <div className="w-12 h-12 border-2 border-[#7dcfff]/20 border-t-[#7dcfff] rounded-full animate-spin mx-auto mb-4"></div>
              <p className="text-[#c0caf5]">Loading workers...</p>
            </div>
          </div>
        ) : (
          <div className="space-y-4">
            {categories.filter(cat => cat.count > 0).map((category) => {
              const workersInCat = groupedWorkers[category.id] || [];
              const filtered = filteredWorkers(workersInCat);
              const isExpanded = expandedCategories.has(category.id);
              
              return (
                <div key={category.id} className="bg-[#24283b]/50 rounded-xl border border-[#292e42] overflow-hidden">
                  <button
                    onClick={() => toggleCategory(category.id)}
                    className="w-full flex items-center justify-between p-4 hover:bg-white/5 transition-colors"
                  >
                    <div className="flex items-center gap-3">
                      <category.icon className="w-5 h-5" style={{ color: category.color }} />
                      <span className="font-semibold text-[#c0caf5]">{category.name}</span>
                      <span className="text-xs text-[#565f89]">({filtered.length}/{category.count})</span>
                    </div>
                    {isExpanded ? <ChevronDown className="w-4 h-4 text-[#565f89]" /> : <ChevronRight className="w-4 h-4 text-[#565f89]" />}
                  </button>
                  
                  {isExpanded && (
                    <div className="border-t border-[#292e42] p-4">
                      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
                        {filtered.map((worker: any, idx: number) => (
                          <div key={idx} className="bg-[#1a1b26] rounded-lg p-3 border border-[#292e42] hover:border-[#7dcfff]/40 transition-all group">
                            <div className="flex items-start gap-3">
                              <div className="w-8 h-8 rounded-lg bg-[#24283b] flex items-center justify-center">
                                {getWorkerIcon(worker.name || '')}
                              </div>
                              <div className="flex-1 min-w-0">
                                <div className="flex items-center gap-2">
                                  <h3 className="text-sm font-medium text-[#c0caf5] truncate">
                                    {worker.name || worker.key || 'Unknown'}
                                  </h3>
                                  {worker.category === 'coworker' && (
                                    <span className="text-[8px] px-1 py-0.5 rounded bg-[#bb9af7]/20 text-[#bb9af7]">COWORKER</span>
                                  )}
                                </div>
                                <p className="text-xs text-[#565f89] mt-1 truncate">
                                  {worker.module || worker.path?.split('\\').pop() || 'Built-in worker'}
                                </p>
                                <div className="flex items-center gap-2 mt-2">
                                  <div className="w-1.5 h-1.5 rounded-full bg-[#9ece6a]"></div>
                                  <span className="text-[10px] text-[#9ece6a]">Active</span>
                                </div>
                              </div>
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              );
            })}
            
            {searchTerm && filteredWorkers(workers).length === 0 && (
              <div className="text-center py-12">
                <p className="text-[#565f89]">No workers found matching "{searchTerm}"</p>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

