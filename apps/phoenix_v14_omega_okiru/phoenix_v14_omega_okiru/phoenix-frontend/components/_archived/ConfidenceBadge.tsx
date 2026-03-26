"use client";
export function ConfidenceBadge({ confidence, worker }: { confidence: number, worker: string }) {
  const color = confidence > 0.8 ? 'text-green-400' : confidence > 0.5 ? 'text-yellow-400' : 'text-red-400';
  return (<div className={`text-xs ${color} font-mono flex items-center gap-1`}><span>→ {worker}</span><span className="opacity-70">({(confidence * 100).toFixed(0)}%)</span></div>);
}
