'use client';

import React, { useState, useEffect } from 'react';
import { ShieldCheck, Lock, CheckCircle, XCircle, Scale } from 'lucide-react';

interface Ruling {
  action: string;
  ruling: { approved: boolean; reason: string };
  timestamp: number;
}

export default function SystemConstitutionPage() {
  const [rulings, setRulings] = useState<Ruling[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchRulings();
  }, []);

  const fetchRulings = async () => {
    try {
      const response = await fetch('http://localhost:8002/constitution/history?limit=20');
      if (response.ok) {
        const data = await response.json();
        setRulings(data.rulings || []);
      }
    } catch (err) {
      console.error('Failed to fetch rulings:', err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#050505] p-8">
      <div className="max-w-4xl mx-auto">
        <div className="mb-8">
          <h1 className="text-2xl font-bold text-white flex items-center gap-3">
            <Scale className="w-8 h-8 text-[#9B72CB]" />
            Constitutional History
          </h1>
          <p className="text-zinc-500 mt-2">SCE Protocol Enforcement Records</p>
        </div>

        <div className="bg-[#0a0a0c] border border-white/5 rounded-xl p-6 mb-6">
          <div className="flex items-center gap-2 mb-4">
            <ShieldCheck className="w-5 h-5 text-[#00E5FF]" />
            <h2 className="text-white font-bold">The 9 Laws of Sovereignty</h2>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-sm">
            <div className="text-zinc-400">1. SOVEREIGNTY</div>
            <div className="text-zinc-400">2. TRANSPARENCY</div>
            <div className="text-zinc-400">3. ACCOUNTABILITY</div>
            <div className="text-zinc-400">4. DETERMINISM</div>
            <div className="text-zinc-400">5. SAFETY</div>
            <div className="text-zinc-400">6. PRIVACY</div>
            <div className="text-zinc-400">7. AUDITABILITY</div>
            <div className="text-zinc-400">8. RECOVERABILITY</div>
            <div className="text-zinc-400">9. BOUNDEDNESS</div>
          </div>
        </div>

        <h2 className="text-sm font-mono text-zinc-500 mb-4">Recent Rulings</h2>
        {loading ? (
          <div className="text-center py-8 text-zinc-500">Loading...</div>
        ) : rulings.length === 0 ? (
          <div className="text-center py-8 text-zinc-500">No rulings recorded yet</div>
        ) : (
          <div className="space-y-3">
            {rulings.map((ruling, i) => (
              <div key={i} className="bg-[#0a0a0c] border border-white/5 rounded-lg p-4">
                <div className="flex items-center gap-2 mb-2">
                  {ruling.ruling.approved ? (
                    <CheckCircle className="w-4 h-4 text-green-500" />
                  ) : (
                    <XCircle className="w-4 h-4 text-red-500" />
                  )}
                  <span className="text-white font-mono text-sm truncate flex-1">{ruling.action}</span>
                  <span className="text-xs text-zinc-500">{new Date(ruling.timestamp * 1000).toLocaleString()}</span>
                </div>
                <div className={	ext-xs }>
                  {ruling.ruling.reason}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
