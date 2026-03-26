'use client';

import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  ShieldCheck, Lock, CheckCircle, XCircle, Scale, 
  GitBranch, Clock, Zap, Brain, Eye, EyeOff, 
  ChevronDown, ChevronRight, AlertTriangle, BookOpen 
} from 'lucide-react';

interface Ruling {
  action: string;
  ruling: { approved: boolean; reason: string };
  timestamp: number;
  driftLock?: string;
  narrative?: string[];
  worker?: string;
  confidence?: number;
}

export default function SystemConstitutionPage() {
  const [rulings, setRulings] = useState<Ruling[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedRuling, setSelectedRuling] = useState<Ruling | null>(null);
  const [showDetails, setShowDetails] = useState(false);
  const [time, setTime] = useState('');
  const [kernelStatus, setKernelStatus] = useState<'online' | 'offline'>('checking');

  // Clock Effect
  useEffect(() => {
    const interval = setInterval(() => {
      setTime(new Date().toLocaleTimeString('en-US', { hour12: false }) + ' UTC');
    }, 1000);
    return () => clearInterval(interval);
  }, []);

  const fetchRulings = async () => {
    try {
      const response = await fetch('http://localhost:8002/constitution/history?limit=50');
      if (response.ok) {
        const data = await response.json();
        setRulings(data.rulings || []);
        setKernelStatus('online');
      } else {
        setKernelStatus('offline');
      }
    } catch (err) {
      console.error('Failed to fetch rulings:', err);
      setKernelStatus('offline');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchRulings();
    const interval = setInterval(fetchRulings, 30000);
    return () => clearInterval(interval);
  }, []);

  const formatTimestamp = (timestamp: number) => {
    const date = new Date(timestamp * 1000);
    return date.toLocaleDateString() + ' at ' + date.toLocaleTimeString();
  };

  const getApprovalColor = (approved: boolean) => {
    return approved ? 'text-[#9ece6a]' : 'text-[#f7768e]';
  };

  const getApprovalIcon = (approved: boolean) => {
    return approved ? <CheckCircle className="w-4 h-4" /> : <XCircle className="w-4 h-4" />;
  };

  // Constitutional Principles
  const principles = [
    { id: 1, name: 'SOVEREIGNTY', desc: 'User owns their data and decisions', color: '#7dcfff' },
    { id: 2, name: 'TRANSPARENCY', desc: 'All decisions are auditable', color: '#9B72CB' },
    { id: 3, name: 'ACCOUNTABILITY', desc: 'Actions are traceable to source', color: '#9ece6a' },
    { id: 4, name: 'DETERMINISM', desc: 'Same input → same output', color: '#ff9e64' },
    { id: 5, name: 'SAFETY', desc: 'No harmful operations', color: '#f7768e' },
    { id: 6, name: 'PRIVACY', desc: 'Data stays local', color: '#7dcfff' },
    { id: 7, name: 'AUDITABILITY', desc: 'Complete execution logs', color: '#9B72CB' },
    { id: 8, name: 'RECOVERABILITY', desc: 'Can revert to previous states', color: '#9ece6a' },
    { id: 9, name: 'BOUNDEDNESS', desc: 'Resource limits enforced', color: '#ff9e64' }
  ];

  // Statistics
  const approvedCount = rulings.filter(r => r.ruling.approved).length;
  const rejectedCount = rulings.filter(r => !r.ruling.approved).length;
  const approvalRate = rulings.length > 0 ? (approvedCount / rulings.length * 100).toFixed(1) : '0';

  return (
    <div className="min-h-screen bg-gradient-to-br from-[#0a0a0c] via-[#050505] to-[#0a0a0c] overflow-hidden">
      
      {/* Animated Grid Background */}
      <div className="fixed inset-0 pointer-events-none opacity-20">
        <div className="absolute inset-0 bg-[radial-gradient(circle_at_50%_50%,_#7dcfff_0%,_transparent_50%)] opacity-5" />
        <div className="absolute inset-0" style={{ backgroundImage: 'linear-gradient(to right, #7dcfff0a 1px, transparent 1px), linear-gradient(to bottom, #7dcfff0a 1px, transparent 1px)', backgroundSize: '40px 40px' }} />
      </div>

      {/* Status Bar */}
      <div className="relative z-10 flex items-center justify-between px-6 py-2 border-b border-[#7dcfff]/10 bg-black/40 backdrop-blur-xl text-[9px] font-mono text-zinc-500 uppercase">
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2">
            <div className={`w-1.5 h-1.5 rounded-full ${kernelStatus === 'online' ? 'bg-[#9ece6a] animate-pulse' : 'bg-[#f7768e]'}`} />
            <span className={kernelStatus === 'online' ? 'text-[#9ece6a]' : 'text-[#f7768e]'}>
              KERNEL: {kernelStatus === 'online' ? 'ACTIVE' : 'OFFLINE'}
            </span>
          </div>
          <div className="flex items-center gap-2">
            <ShieldCheck className="w-3 h-3 text-[#7dcfff]" />
            <span>SCE PROTOCOL: <span className="text-[#9ece6a]">ENFORCING</span></span>
          </div>
          <span>DRIFT CHAIN: {rulings.length} EVENTS</span>
        </div>
        <div className="flex items-center gap-4">
          <span>CONSTITUTION v1.0</span>
          <span>PHOENIX v13.3.0</span>
          <span className="text-zinc-300">{time}</span>
        </div>
      </div>

      <div className="relative z-10 p-8">
        <div className="max-w-7xl mx-auto">
          
          {/* Header */}
          <motion.div 
            initial={{ y: -20, opacity: 0 }}
            animate={{ y: 0, opacity: 1 }}
            className="mb-8"
          >
            <div className="flex items-center gap-4 mb-4">
              <div className="w-12 h-12 rounded-2xl bg-gradient-to-br from-[#7dcfff]/20 to-[#9B72CB]/20 border border-[#7dcfff]/30 flex items-center justify-center">
                <Scale className="w-6 h-6 text-[#7dcfff]" />
              </div>
              <div>
                <h1 className="text-3xl font-bold bg-gradient-to-r from-[#c0caf5] to-[#7dcfff] bg-clip-text text-transparent">
                  Constitutional History
                </h1>
                <p className="text-[#565f89] mt-1">SCE Protocol Enforcement Records • Drift Chain Audit</p>
              </div>
            </div>

            {/* Stats Cards */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mt-6">
              <div className="bg-black/30 backdrop-blur-xl border border-[#7dcfff]/10 rounded-xl p-4">
                <div className="text-[10px] text-[#565f89] mb-1">Total Rulings</div>
                <div className="text-2xl font-bold text-white">{rulings.length}</div>
              </div>
              <div className="bg-black/30 backdrop-blur-xl border border-[#7dcfff]/10 rounded-xl p-4">
                <div className="text-[10px] text-[#565f89] mb-1">Approved</div>
                <div className="text-2xl font-bold text-[#9ece6a]">{approvedCount}</div>
              </div>
              <div className="bg-black/30 backdrop-blur-xl border border-[#7dcfff]/10 rounded-xl p-4">
                <div className="text-[10px] text-[#565f89] mb-1">Rejected</div>
                <div className="text-2xl font-bold text-[#f7768e]">{rejectedCount}</div>
              </div>
              <div className="bg-black/30 backdrop-blur-xl border border-[#7dcfff]/10 rounded-xl p-4">
                <div className="text-[10px] text-[#565f89] mb-1">Approval Rate</div>
                <div className="text-2xl font-bold text-[#7dcfff]">{approvalRate}%</div>
              </div>
            </div>
          </motion.div>

          {/* Constitution Principles Section */}
          <motion.div 
            initial={{ y: 20, opacity: 0 }}
            animate={{ y: 0, opacity: 1 }}
            transition={{ delay: 0.1 }}
            className="bg-black/30 backdrop-blur-xl border border-[#7dcfff]/10 rounded-2xl p-6 mb-8"
          >
            <div className="flex items-center gap-3 mb-6">
              <div className="w-8 h-8 rounded-xl bg-[#7dcfff]/10 border border-[#7dcfff]/30 flex items-center justify-center">
                <BookOpen className="w-4 h-4 text-[#7dcfff]" />
              </div>
              <h2 className="text-lg font-bold text-white">The 9 Laws of Sovereignty</h2>
              <div className="ml-auto flex items-center gap-2">
                <div className="w-1.5 h-1.5 rounded-full bg-[#9ece6a] animate-pulse" />
                <span className="text-[8px] text-[#565f89] font-mono">SCE ACTIVE</span>
              </div>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
              {principles.map((principle) => (
                <div key={principle.id} className="group p-3 rounded-xl bg-white/5 border border-white/10 hover:border-[#7dcfff]/30 transition-all">
                  <div className="flex items-center gap-2 mb-1">
                    <span className="text-[10px] font-mono" style={{ color: principle.color }}>0{principle.id}</span>
                    <span className="text-[11px] font-bold text-white">{principle.name}</span>
                  </div>
                  <p className="text-[9px] text-[#565f89]">{principle.desc}</p>
                </div>
              ))}
            </div>
          </motion.div>

          {/* Rulings Section */}
          <motion.div 
            initial={{ y: 20, opacity: 0 }}
            animate={{ y: 0, opacity: 1 }}
            transition={{ delay: 0.2 }}
          >
            <div className="flex items-center justify-between mb-6">
              <div className="flex items-center gap-2">
                <GitBranch className="w-4 h-4 text-[#7dcfff]" />
                <h2 className="text-lg font-bold text-white">Drift Chain History</h2>
                <span className="text-[10px] text-[#565f89] font-mono">({rulings.length} events)</span>
              </div>
              <button 
                onClick={fetchRulings}
                className="text-[9px] font-mono text-[#7dcfff] hover:text-white transition-colors flex items-center gap-1"
              >
                <Zap className="w-3 h-3" />
                Refresh
              </button>
            </div>

            {loading ? (
              <div className="flex items-center justify-center py-20">
                <div className="w-8 h-8 border-2 border-[#7dcfff] border-t-transparent rounded-full animate-spin" />
              </div>
            ) : rulings.length === 0 ? (
              <div className="bg-black/30 backdrop-blur-xl border border-[#7dcfff]/10 rounded-2xl p-12 text-center">
                <ShieldCheck className="w-12 h-12 text-[#565f89] mx-auto mb-4" />
                <p className="text-[#565f89]">No rulings recorded yet. The constitution awaits its first case.</p>
              </div>
            ) : (
              <div className="space-y-3">
                {rulings.map((ruling, i) => (
                  <motion.div
                    key={i}
                    initial={{ opacity: 0, x: -10 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: i * 0.02 }}
                    className="group bg-black/30 backdrop-blur-xl border border-[#7dcfff]/10 rounded-xl overflow-hidden hover:border-[#7dcfff]/30 transition-all"
                  >
                    <div 
                      className="p-4 cursor-pointer hover:bg-white/5 transition-colors"
                      onClick={() => {
                        setSelectedRuling(selectedRuling === ruling ? null : ruling);
                        setShowDetails(true);
                      }}
                    >
                      <div className="flex items-center gap-3">
                        <div className={`flex-shrink-0 ${getApprovalColor(ruling.ruling.approved)}`}>
                          {getApprovalIcon(ruling.ruling.approved)}
                        </div>
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center gap-2 flex-wrap">
                            <code className="text-[11px] font-mono text-white truncate">{ruling.action}</code>
                            {ruling.worker && (
                              <span className="text-[7px] font-mono text-[#7dcfff] bg-[#7dcfff]/10 px-1.5 py-0.5 rounded">
                                {ruling.worker}
                              </span>
                            )}
                          </div>
                          <div className="text-[9px] text-[#565f89] mt-1 line-clamp-1">
                            {ruling.ruling.reason}
                          </div>
                        </div>
                        <div className="flex items-center gap-3">
                          <div className="flex items-center gap-1">
                            <Clock className="w-3 h-3 text-[#565f89]" />
                            <span className="text-[9px] text-[#565f89]">{formatTimestamp(ruling.timestamp)}</span>
                          </div>
                          {ruling.driftLock && (
                            <code className="text-[7px] font-mono text-[#9ece6a] bg-[#9ece6a]/10 px-1.5 py-0.5 rounded">
                              🔒 {ruling.driftLock.slice(0, 6)}
                            </code>
                          )}
                          <ChevronRight className={`w-4 h-4 text-[#565f89] transition-transform ${selectedRuling === ruling ? 'rotate-90' : ''}`} />
                        </div>
                      </div>
                    </div>

                    {/* Expanded Details */}
                    <AnimatePresence>
                      {selectedRuling === ruling && showDetails && (
                        <motion.div
                          initial={{ height: 0, opacity: 0 }}
                          animate={{ height: 'auto', opacity: 1 }}
                          exit={{ height: 0, opacity: 0 }}
                          className="border-t border-[#7dcfff]/10 bg-black/20"
                        >
                          <div className="p-4 space-y-3">
                            {/* Reason */}
                            <div>
                              <div className="text-[9px] font-mono text-[#565f89] mb-1">REASONING</div>
                              <div className="text-[11px] text-[#c0caf5] bg-black/40 rounded-lg p-3 border border-white/5">
                                {ruling.ruling.reason}
                              </div>
                            </div>

                            {/* Narrative */}
                            {ruling.narrative && ruling.narrative.length > 0 && (
                              <div>
                                <div className="text-[9px] font-mono text-[#9B72CB] mb-1 flex items-center gap-1">
                                  <Brain className="w-3 h-3" />
                                  NARRATIVE
                                </div>
                                <div className="space-y-1">
                                  {ruling.narrative.map((step, idx) => (
                                    <div key={idx} className="text-[9px] text-[#565f89] italic border-l-2 border-[#9B72CB]/30 pl-2 py-1">
                                      "{step}"
                                    </div>
                                  ))}
                                </div>
                              </div>
                            )}

                            {/* Drift Lock */}
                            {ruling.driftLock && (
                              <div>
                                <div className="text-[9px] font-mono text-[#9ece6a] mb-1 flex items-center gap-1">
                                  <Lock className="w-3 h-3" />
                                  DRIFT LOCK
                                </div>
                                <code className="text-[9px] font-mono text-[#9ece6a] bg-black/40 rounded-lg p-2 block border border-[#9ece6a]/20">
                                  {ruling.driftLock}
                                </code>
                              </div>
                            )}

                            {/* Confidence */}
                            {ruling.confidence && (
                              <div>
                                <div className="text-[9px] font-mono text-[#565f89] mb-1">CONFIDENCE</div>
                                <div className="flex items-center gap-2">
                                  <div className="flex-1 h-1 bg-white/10 rounded-full overflow-hidden">
                                    <div 
                                      className="h-full rounded-full bg-gradient-to-r from-[#7dcfff] to-[#9ece6a]"
                                      style={{ width: `${ruling.confidence}%` }}
                                    />
                                  </div>
                                  <span className="text-[9px] text-[#7dcfff]">{ruling.confidence}%</span>
                                </div>
                              </div>
                            )}
                          </div>
                        </motion.div>
                      )}
                    </AnimatePresence>
                  </motion.div>
                ))}
              </div>
            )}
          </motion.div>
        </div>
      </div>

      <style jsx global>{`
        .custom-scrollbar::-webkit-scrollbar { width: 4px; }
        .custom-scrollbar::-webkit-scrollbar-track { background: rgba(125,207,255,0.05); border-radius: 10px; }
        .custom-scrollbar::-webkit-scrollbar-thumb { background: rgba(125,207,255,0.3); border-radius: 10px; }
        .custom-scrollbar::-webkit-scrollbar-thumb:hover { background: rgba(125,207,255,0.5); }
        .line-clamp-1 {
          display: -webkit-box;
          -webkit-line-clamp: 1;
          -webkit-box-orient: vertical;
          overflow: hidden;
        }
      `}</style>
    </div>
  );
}