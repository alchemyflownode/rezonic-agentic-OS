"use client";

interface DeepSearchResultsProps {
  data?: {
    answer?: string;
    results?: any[];
    images?: any[];
  };
}

export default function DeepSearchResults({ data }: DeepSearchResultsProps) {
  if (!data) return null;

  return (
    <div className="space-y-3">
      {/* Answer */}
      {data.answer && (
        <div className="text-sm text-white/80 whitespace-pre-wrap">{data.answer}</div>
      )}
      
      {/* Images Grid */}
      {data.images && data.images.length > 0 && (
        <div className="grid grid-cols-2 gap-2 my-2">
          {data.images.map((img, i) => (
            <img 
              key={i} 
              src={img.image || img.thumbnail} 
              alt={img.title || 'Result'} 
              className="w-full h-24 object-cover rounded border border-white/10"
            />
          ))}
        </div>
      )}

      {/* Sources */}
      {data.results && data.results.length > 0 && (
        <div className="text-[10px] text-white/50">
          <strong>Sources:</strong> {data.results.length} results found.
        </div>
      )}
    </div>
  );
}
