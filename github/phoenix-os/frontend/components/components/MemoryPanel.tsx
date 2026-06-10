// components/MemoryPanel.tsx
import { useState } from 'react';
import { Database, Search, Clock, Lock, X } from 'lucide-react';
import { usePhoenixStore } from '@/store/phoenixStore';

export const MemoryPanel = () => {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState<any[]>([]);
  const [isSearching, setIsSearching] = useState(false);
  const [selectedMemory, setSelectedMemory] = useState<any>(null);
  const { memory, searchMemory, connected } = usePhoenixStore();

  const handleSearch = async () => {
    if (!query.trim()) return;
    setIsSearching(true);
    const searchResults = await searchMemory(query);
    setResults(searchResults);
    setIsSearching(false);
  };

  return (
    <div className="bg-black/30 backdrop-blur-xl border border-[#7dcfff]/10 rounded-2xl p-5">
      <div className="flex items-center gap-2 mb-4">
        <Database className="w-5 h-5 text-[#7dcfff]" />
        <h3 className="text-sm font-bold">Sovereign Memory</h3>
        <span className="text-xs text-[#565f89] ml-auto">
          {memory.total} blueprints
        </span>
      </div>

      {/* Search Bar */}
      <div className="flex gap-2 mb-4">
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
          placeholder="Search memory..."
          className="flex-1 bg-black/50 border border-[#7dcfff]/20 rounded-lg px-3 py-2 text-sm text-white placeholder:text-[#565f89] outline-none focus:border-[#7dcfff]/50"
        />
        <button
          onClick={handleSearch}
          disabled={isSearching || !connected}
          className="px-4 py-2 bg-[#7dcfff]/20 rounded-lg hover:bg-[#7dcfff]/30 transition disabled:opacity-50"
        >
          <Search className="w-4 h-4" />
        </button>
      </div>

      {/* Results List */}
      <div className="space-y-2 max-h-80 overflow-y-auto custom-scrollbar">
        {results.length > 0 ? (
          results.map((result) => (
            <div
              key={result.drift_lock}
              className="bg-white/5 rounded-lg p-3 hover:bg-white/10 transition cursor-pointer"
              onClick={() => setSelectedMemory(result)}
            >
              <p className="text-sm text-white line-clamp-2">{result.task}</p>
              <div className="flex items-center gap-3 mt-2 text-[10px] text-[#565f89]">
                <span className="flex items-center gap-1">
                  <Lock className="w-3 h-3" />
                  {result.drift_lock?.substring(0, 8)}...
                </span>
                <span className="flex items-center gap-1">
                  <Clock className="w-3 h-3" />
                  {new Date(result.timestamp * 1000).toLocaleString()}
                </span>
              </div>
            </div>
          ))
        ) : memory.searchResults.length > 0 ? (
          memory.searchResults.map((result) => (
            <div
              key={result.drift_lock}
              className="bg-white/5 rounded-lg p-3 hover:bg-white/10 transition cursor-pointer"
              onClick={() => setSelectedMemory(result)}
            >
              <p className="text-sm text-white line-clamp-2">{result.task}</p>
              <div className="flex items-center gap-3 mt-2 text-[10px] text-[#565f89]">
                <span className="flex items-center gap-1">
                  <Lock className="w-3 h-3" />
                  {result.drift_lock?.substring(0, 8)}...
                </span>
                <span className="flex items-center gap-1">
                  <Clock className="w-3 h-3" />
                  {new Date(result.timestamp * 1000).toLocaleString()}
                </span>
              </div>
            </div>
          ))
        ) : (
          <div className="text-center text-[#565f89] py-8">
            <Database className="w-8 h-8 mx-auto mb-2 opacity-50" />
            <p className="text-xs">
              {query ? 'No results found' : 'Search your sovereign memory'}
            </p>
          </div>
        )}
      </div>

      {/* Memory Detail Modal */}
      {selectedMemory && (
        <div className="fixed inset-0 bg-black/80 backdrop-blur-sm flex items-center justify-center z-50" onClick={() => setSelectedMemory(null)}>
          <div className="bg-[#0a0a0c] border border-[#7dcfff]/20 rounded-2xl p-6 max-w-2xl w-full mx-4" onClick={(e) => e.stopPropagation()}>
            <div className="flex justify-between items-center mb-4">
              <h3 className="text-lg font-bold text-[#7dcfff]">Memory Blueprint</h3>
              <button onClick={() => setSelectedMemory(null)} className="p-1 hover:bg-white/10 rounded-lg">
                <X className="w-4 h-4" />
              </button>
            </div>
            <div className="space-y-4">
              <div>
                <div className="text-xs text-[#565f89] mb-1">Drift Lock</div>
                <code className="text-sm font-mono text-[#9ece6a] bg-black/50 p-2 rounded block break-all">
                  {selectedMemory.drift_lock}
                </code>
              </div>
              <div>
                <div className="text-xs text-[#565f89] mb-1">Task</div>
                <p className="text-sm text-white">{selectedMemory.task}</p>
              </div>
              <div>
                <div className="text-xs text-[#565f89] mb-1">Timestamp</div>
                <p className="text-sm text-[#565f89]">{new Date(selectedMemory.timestamp * 1000).toLocaleString()}</p>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};