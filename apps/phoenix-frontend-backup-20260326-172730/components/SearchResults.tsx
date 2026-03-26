'use client';

import { useState } from 'react';
import { Search, Image as ImageIcon, ExternalLink, Clock } from 'lucide-react';

interface SearchResult {
  title: string;
  url: string;
  snippet: string;
}

interface SearchImage {
  title: string;
  url: string;
  thumbnail: string;
}

export function SearchResults() {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState<SearchResult[]>([]);
  const [images, setImages] = useState<SearchImage[]>([]);
  const [loading, setLoading] = useState(false);
  const [time, setTime] = useState(0);

  const handleSearch = async () => {
    if (!query.trim()) return;
    
    setLoading(true);
    const start = Date.now();
    
    try {
      const res = await fetch('/api/workers/deepsearch', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ task: query })
      });
      
      const data = await res.json();
      
      if (data.results) {
        setResults(data.results);
      }
      if (data.images) {
        setImages(data.images);
      }
      
      setTime(Date.now() - start);
    } catch (error) {
      console.error('Search failed:', error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="panel p-4">
      {/* Search Input */}
      <div className="flex gap-2 mb-4">
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
          placeholder="Search the web..."
          className="flex-1 bg-bg-elevated border border-border-subtle rounded px-3 py-2 text-sm"
        />
        <button
          onClick={handleSearch}
          disabled={loading}
          className="px-4 py-2 bg-accent-primary text-black rounded text-sm font-medium hover:bg-accent-hover disabled:opacity-50"
        >
          {loading ? 'Searching...' : 'Search'}
        </button>
      </div>
      
      {/* Results */}
      {results.length > 0 && (
        <div className="space-y-3">
          <div className="flex items-center justify-between text-xs text-text-tertiary">
            <span>Found {results.length} results</span>
            <span className="flex items-center gap-1">
              <Clock size={12} /> {time}ms
            </span>
          </div>
          
          {results.map((result, i) => (
            <div key={i} className="panel-elevated p-3 hover:border-accent-soft transition-colors">
              <a 
                href={result.url} 
                target="_blank" 
                rel="noopener noreferrer"
                className="block"
              >
                <h4 className="text-sm font-medium text-accent-primary mb-1 hover:underline flex items-center gap-1">
                  {result.title}
                  <ExternalLink size={12} className="opacity-50" />
                </h4>
                <p className="text-xs text-text-secondary line-clamp-2">{result.snippet}</p>
                <p className="text-[10px] text-text-tertiary mt-1 truncate">{result.url}</p>
              </a>
            </div>
          ))}
        </div>
      )}
      
      {/* Images */}
      {images.length > 0 && (
        <div className="mt-4">
          <h4 className="text-xs font-medium text-text-secondary mb-2 flex items-center gap-1">
            <ImageIcon size={12} /> Images
          </h4>
          <div className="grid grid-cols-3 gap-2">
            {images.map((img, i) => (
              <a
                key={i}
                href={img.url}
                target="_blank"
                rel="noopener noreferrer"
                className="aspect-square bg-bg-elevated rounded overflow-hidden border border-border-subtle hover:border-accent-primary transition-colors"
              >
                <img 
                  src={img.thumbnail} 
                  alt={img.title}
                  className="w-full h-full object-cover"
                  onError={(e) => {
                    (e.target as HTMLImageElement).style.display = 'none';
                  }}
                />
              </a>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
