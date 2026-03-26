'use client';

import React, { useState, useMemo } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Brain, Search, GitBranch, Clock, Lock, Star, Sparkles, Shield, Code } from 'lucide-react';

interface MemorySnapshot {
  id: string;
  content: string;
  fullContent?: string;
  timestamp: number;
  driftLock: string;
  importance: number;
  tags?: string[];
  codeBlock?: string | null;
}

interface ZeroDriftMemoryMapProps {
  memories: MemorySnapshot[];
  onMemorySelect?: (content: string) => void;
  className?: string;
}

export default function ZeroDriftMemoryMap({ memories, onMemorySelect, className = '' }: ZeroDriftMemoryMapProps) {
  const [searchTerm, setSearchTerm] = useState('');
  const [filterType, setFilterType] = useState<'all' | 'sce' | 'code'>('all');
  const [selectedId, setSelectedId] = useState<string | null>(null);

  const filteredMemories = useMemo(() => {
    let filtered = [...memories];
    
    if (filterType === 'sce') {
      filtered = filtered.filter(m => m.tags?.includes('SCE') || m.content.includes('SCE'));
    } else if (filterType === 'code') {
      filtered = filtered.filter(m => m.tags?.includes('code') || m.codeBlock);
    }
    
    if (searchTerm) {
      const term = searchTerm.toLowerCase();
      filtered = filtered.filter(m => 
        m.content.toLowerCase().includes(term) ||
        m.tags?.some(t => t.toLowerCase().includes(term))
      );
    }
    
    return filtered.sort((a, b) => b.importance - a.importance);
  }, [memories, searchTerm, filterType]);

  const getTimeAgo = (timestamp: number) => {
    const seconds = Math.floor((Date.now() - timestamp) / 1000);
    if (seconds < 60) return `${seconds}s`;
    const minutes = Math.floor(seconds / 60);
    if (minutes < 60) return `${minutes}m`;
    const hours = Math.floor(minutes / 60);
    if (hours < 24) return `${hours}h`;
    return `${Math.floor(hours / 24)}d`;
  };

  return (
    <div className={`bg-black/30 backdrop-blur-xl border border-[#7dcfff]/10 rounded-2xl flex flex-col h-full ${className}`}>
      <div className="p-4 border-b border-[#7dcfff]/10">
        <div className="flex items-center gap-2 mb-3">
          <Brain className="w-4 h-4 text-[#7dcfff]" />
          <h3 className="text-[11px] font-mono font-bold text-[#7dcfff]">Zero-Drift Memory</h3>
          <span className="text-[8px] text-[#9ece6a] bg-[#9ece6a]/20 px-2 py-0.5 rounded-full">{memories.length}</span>
        </div>
        
        <div className="relative mb-3">
          <Search className="w-3 h-3 absolute left-3 top-2.5 text-[#565f89]" />
          <input
            type="text"
            placeholder="Search memories..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full bg-black/50 border border-[#7dcfff]/20 rounded-xl py-2 pl-8 pr-3 text-xs text-white outline-none focus:border-[#7dcfff]/50"
          />
        </div>
        
        <div className="flex gap-1">
          <button onClick={() => setFilterType('all')} className={`px-3 py-1.5 rounded-lg text-[9px] font-mono ${filterType === 'all' ? 'bg-[#7dcfff]/20 border border-[#7dcfff]/50' : 'bg-white/5'}`}>ALL</button>
          <button onClick={() => setFilterType('sce')} className={`px-3 py-1.5 rounded-lg text-[9px] font-mono ${filterType === 'sce' ? 'bg-[#7dcfff]/20 border border-[#7dcfff]/50' : 'bg-white/5'}`}>SCE</button>
          <button onClick={() => setFilterType('code')} className={`px-3 py-1.5 rounded-lg text-[9px] font-mono ${filterType === 'code' ? 'bg-[#7dcfff]/20 border border-[#7dcfff]/50' : 'bg-white/5'}`}>CODE</button>
        </div>
      </div>
      
      <div className="flex-1 overflow-y-auto p-3 space-y-2">
        {filteredMemories.length === 0 ? (
          <div className="text-center py-12">
            <Brain className="w-12 h-12 text-[#565f89] opacity-30 mx-auto mb-3" />
            <p className="text-[10px] text-[#565f89]">No memories yet</p>
          </div>
        ) : (
          filteredMemories.map(memory => (
            <div key={memory.id} onClick={() => onMemorySelect?.(memory.fullContent || memory.content)} className="p-2 bg-black/20 rounded-lg border-l-2 border-[#7dcfff] cursor-pointer hover:bg-white/5">
              <div className="flex justify-between text-[8px] text-[#565f89] mb-1">
                <span>🔒 {memory.driftLock?.slice(0, 8)}</span>
                <span>{getTimeAgo(memory.timestamp)} ago</span>
              </div>
              <p className="text-[9px] text-[#c0caf5] line-clamp-2">{memory.content.slice(0, 100)}</p>
            </div>
          ))
        )}
      </div>
    </div>
  );
}
