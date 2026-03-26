'use client';

import React, { useState, useEffect } from 'react';
import { Search, Database, Shield, Clock, ChevronRight } from 'lucide-react';

export default function SystemMemoryPage() {
  const [blueprints, setBlueprints] = useState<string[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [searchResults, setSearchResults] = useState<any[]>([]);

  useEffect(() => {
    fetchBlueprints();
  }, []);

  const fetchBlueprints = async () => {
    try {
      const response = await fetch('http://localhost:8002/memory/blueprints');
      if (response.ok) {
        const data = await response.json();
        setBlueprints(data.blueprints || []);
      }
    } catch (err) {
      console.error('Failed to fetch blueprints:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleSearch = async () => {
    if (!searchTerm.trim()) return;
    try {
      const response = await fetch('http://localhost:8002/memory/search', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query: searchTerm })
      });
      if (response.ok) {
        const data = await response.json();
        setSearchResults(data.results || []);
      }
    } catch (err) {
      console.error('Search failed:', err);
    }
  };

  return (
    <div className="min-h-screen bg-[#050505] p-8">
      <div className="max-w-7xl mx-auto">
        <div className="mb-8">
          <h1 className="text-2xl font-bold text-white flex items-center gap-3">
            <Database className="w-8 h-8 text-[#9B72CB]" />
            Sovereign Memory
          </h1>
          <p className="text-zinc-500 mt-2">{blueprints.length} blueprints stored</p>
        </div>

        <div className="mb-8">
          <div className="flex gap-2">
            <input
              type="text"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
              placeholder="Search memory..."
              className="flex-1 bg-black/50 border border-white/10 rounded-lg px-4 py-2 text-white placeholder:text-zinc-600 focus:outline-none focus:border-[#00E5FF]/50"
            />
            <button
              onClick={handleSearch}
              className="px-4 py-2 bg-[#00E5FF]/20 border border-[#00E5FF]/30 rounded-lg text-[#00E5FF] hover:bg-[#00E5FF]/30 transition"
            >
              <Search className="w-4 h-4" />
            </button>
          </div>
        </div>

        {searchResults.length > 0 && (
          <div className="mb-8">
            <h2 className="text-sm font-mono text-zinc-500 mb-4">Search Results</h2>
            <div className="space-y-2">
              {searchResults.map((result, i) => (
                <div key={i} className="bg-[#0a0a0c] border border-white/5 rounded-lg p-4">
                  <div className="flex items-center gap-2 mb-2">
                    <Shield className="w-4 h-4 text-[#00E676]" />
                    <code className="text-[#00E5FF] font-mono text-sm">{result.lock}</code>
                  </div>
                  <div className="text-xs text-zinc-500 flex items-center gap-2">
                    <Clock className="w-3 h-3" />
                    {new Date(result.timestamp * 1000).toLocaleString()}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        <div>
          <h2 className="text-sm font-mono text-zinc-500 mb-4">Recent Blueprints</h2>
          {loading ? (
            <div className="text-center py-8 text-zinc-500">Loading...</div>
          ) : (
            <div className="space-y-2">
              {blueprints.slice(0, 20).map((lock, i) => (
                <div key={i} className="bg-[#0a0a0c] border border-white/5 rounded-lg p-3 flex items-center justify-between">
                  <code className="text-[#00E5FF] font-mono text-sm">{lock}</code>
                  <ChevronRight className="w-4 h-4 text-zinc-600" />
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
