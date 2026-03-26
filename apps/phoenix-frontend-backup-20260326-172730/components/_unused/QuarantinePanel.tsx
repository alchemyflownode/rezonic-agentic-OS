'use client';

import React, { useState, useEffect } from 'react';
import { AlertTriangle, Shield, RotateCcw, Eye, Download, XCircle } from 'lucide-react';

interface QuarantinedItem {
  id: string;
  worker_name?: string;
  file_name?: string;
  reason: string;
  severity: string;
  timestamp: number;
  flagged_by: string;
}

export const QuarantinePanel = () => {
  const [quarantined, setQuarantined] = useState<QuarantinedItem[]>([]);
  const [reviewQueue, setReviewQueue] = useState<any[]>([]);
  const [selected, setSelected] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    fetchQuarantine();
    fetchReviewQueue();
  }, []);

  const fetchQuarantine = async () => {
    try {
      const res = await fetch('http://localhost:8001/quarantine/workers');
      const data = await res.json();
      setQuarantined(data.quarantined || []);
    } catch (error) {
      console.error('Failed to fetch quarantine:', error);
    }
  };

  const fetchReviewQueue = async () => {
    try {
      const res = await fetch('http://localhost:8001/quarantine/review');
      const data = await res.json();
      setReviewQueue(data.review_queue || []);
    } catch (error) {
      console.error('Failed to fetch review queue:', error);
    }
  };

  const restoreWorker = async (id: string) => {
    setLoading(true);
    try {
      await fetch(`http://localhost:8001/quarantine/restore/${id}`, {
        method: 'POST'
      });
      await fetchQuarantine();
      alert('Worker restored successfully');
    } catch (error) {
      alert('Failed to restore worker');
    }
    setLoading(false);
  };

  const getSeverityColor = (severity: string) => {
    switch(severity) {
      case 'critical': return 'text-red-400 border-red-500/30 bg-red-500/10';
      case 'high': return 'text-orange-400 border-orange-500/30 bg-orange-500/10';
      case 'medium': return 'text-yellow-400 border-yellow-500/30 bg-yellow-500/10';
      default: return 'text-blue-400 border-blue-500/30 bg-blue-500/10';
    }
  };

  return (
    <div className="bg-[#070708] border border-cyan-500/20 rounded-lg overflow-hidden">
      {/* Header */}
      <div className="p-4 border-b border-cyan-500/20 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Shield className="w-5 h-5 text-cyan-400" />
          <h2 className="text-sm font-mono text-white">QUARANTINE ZONE</h2>
        </div>
        <span className="text-xs text-zinc-500">
          {quarantined.length} items
        </span>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-3 gap-2 p-4 border-b border-cyan-500/20">
        <div className="text-center">
          <div className="text-xl font-bold text-red-400">
            {quarantined.filter(q => q.severity === 'critical').length}
          </div>
          <div className="text-[8px] text-zinc-500">CRITICAL</div>
        </div>
        <div className="text-center">
          <div className="text-xl font-bold text-orange-400">
            {quarantined.filter(q => q.severity === 'high').length}
          </div>
          <div className="text-[8px] text-zinc-500">HIGH</div>
        </div>
        <div className="text-center">
          <div className="text-xl font-bold text-yellow-400">
            {reviewQueue.length}
          </div>
          <div className="text-[8px] text-zinc-500">REVIEW</div>
        </div>
      </div>

      {/* Quarantined List */}
      <div className="max-h-96 overflow-y-auto custom-scrollbar p-2 space-y-2">
        {quarantined.length === 0 ? (
          <div className="text-center py-8 text-zinc-600">
            <Shield className="w-8 h-8 mx-auto mb-2 opacity-20" />
            <p className="text-xs">No quarantined items</p>
          </div>
        ) : (
          quarantined.map(item => (
            <div
              key={item.id}
              className={`p-3 rounded-lg border ${getSeverityColor(item.severity)}`}
            >
              <div className="flex items-center justify-between mb-2">
                <div className="flex items-center gap-2">
                  <AlertTriangle className="w-4 h-4" />
                  <span className="text-xs font-mono">
                    {item.worker_name || item.file_name}
                  </span>
                </div>
                <span className="text-[8px] uppercase px-1.5 py-0.5 rounded bg-black/40">
                  {item.severity}
                </span>
              </div>
              
              <p className="text-[9px] text-zinc-400 mb-2 line-clamp-2">
                {item.reason}
              </p>
              
              <div className="flex items-center justify-between text-[8px] text-zinc-500">
                <span>by {item.flagged_by}</span>
                <span>{new Date(item.timestamp * 1000).toLocaleString()}</span>
              </div>
              
              <div className="flex gap-2 mt-3">
                <button
                  onClick={() => setSelected(item.id)}
                  className="flex-1 py-1.5 text-[8px] bg-black/40 border border-cyan-500/20 rounded flex items-center justify-center gap-1 hover:border-cyan-500/40"
                >
                  <Eye className="w-3 h-3" /> View
                </button>
                <button
                  onClick={() => restoreWorker(item.id)}
                  disabled={loading}
                  className="flex-1 py-1.5 text-[8px] bg-green-500/10 border border-green-500/30 rounded flex items-center justify-center gap-1 hover:bg-green-500/20"
                >
                  <RotateCcw className="w-3 h-3" /> Restore
                </button>
              </div>
            </div>
          ))
        )}
      </div>

      {/* Review Queue Section */}
      {reviewQueue.length > 0 && (
        <div className="border-t border-cyan-500/20 p-3">
          <h3 className="text-[9px] font-mono text-yellow-400 mb-2 flex items-center gap-1">
            <AlertTriangle className="w-3 h-3" /> REVIEW QUEUE
          </h3>
          <div className="space-y-2">
            {reviewQueue.map((item, i) => (
              <div key={i} className="p-2 bg-yellow-500/5 border border-yellow-500/20 rounded text-[8px]">
                <div className="flex justify-between">
                  <span className="text-white">{item.item_name}</span>
                  <span className="text-yellow-400">{item.severity}</span>
                </div>
                <p className="text-zinc-500 mt-1">{item.reason}</p>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};