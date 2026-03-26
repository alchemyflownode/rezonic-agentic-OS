'use client';

import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { 
  Layout, Shield, Zap, AlertTriangle, CheckCircle, 
  Code, FileText, Package, Activity, Server, RefreshCw,
  Search, Folder, FileCode, Terminal, GitBranch, Clock
} from 'lucide-react';

interface PageInfo {
  path: string;
  component: string;
  size: string;
  status: 'active' | 'inactive';
  lastModified: string;
}

interface ComponentInfo {
  name: string;
  purpose: string;
  usedIn: number;
  status: 'active' | 'available' | 'deprecated';
  filePath: string;
  imports: string[];
  usedBy: string[];
}

interface AuditData {
  pages: PageInfo[];
  components: ComponentInfo[];
  issues: Array<{ type: string; message: string; component?: string }>;
  performance: {
    totalComponents: number;
    totalPages: number;
    buildTime: string;
    bundleSize: string;
  };
  timestamp: string;
}

export default function RealUIAuditPage() {
  const [auditData, setAuditData] = useState<AuditData | null>(null);
  const [loading, setLoading] = useState(true);
  const [scanning, setScanning] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const performAudit = async () => {
    setScanning(true);
    setLoading(true);
    setError(null);
    
    try {
      const response = await fetch('/api/audit');
      if (!response.ok) throw new Error('Failed to scan');
      const data = await response.json();
      setAuditData(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Scan failed');
    } finally {
      setLoading(false);
      setScanning(false);
    }
  };

  useEffect(() => {
    performAudit();
  }, []);

  if (loading) {
    return (
      <div className="min-h-screen bg-black flex items-center justify-center">
        <div className="text-center">
          <div className="w-12 h-12 border-2 border-[#7dcfff] border-t-transparent rounded-full animate-spin mx-auto mb-4" />
          <p className="text-[#7dcfff] font-mono text-sm">
            {scanning ? 'Scanning filesystem...' : 'Loading audit data...'}
          </p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-black flex items-center justify-center p-8">
        <div className="text-center max-w-md">
          <AlertTriangle className="w-12 h-12 text-[#f7768e] mx-auto mb-4" />
          <h2 className="text-xl font-bold text-white mb-2">Scan Failed</h2>
          <p className="text-[#565f89] mb-4">{error}</p>
          <button
            onClick={performAudit}
            className="px-4 py-2 rounded-xl bg-[#7dcfff]/10 border border-[#7dcfff]/30 text-[#7dcfff] hover:bg-[#7dcfff]/20 transition-all"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-[#0a0a0c] to-[#050505] p-8">
      <div className="max-w-6xl mx-auto">
        
        {/* Header */}
        <motion.div initial={{ y: -20, opacity: 0 }} animate={{ y: 0, opacity: 1 }} className="mb-8">
          <div className="flex items-center justify-between flex-wrap gap-4">
            <div className="flex items-center gap-4">
              <div className="w-12 h-12 rounded-2xl bg-gradient-to-br from-[#7dcfff]/20 to-[#9B72CB]/20 border border-[#7dcfff]/30 flex items-center justify-center">
                <Search className="w-6 h-6 text-[#7dcfff]" />
              </div>
              <div>
                <h1 className="text-3xl font-bold bg-gradient-to-r from-[#c0caf5] to-[#7dcfff] bg-clip-text text-transparent">
                  UI Audit Dashboard
                </h1>
                <p className="text-[#565f89] mt-1 text-sm flex items-center gap-2">
                  <Clock className="w-3 h-3" />
                  Last scan: {new Date(auditData.timestamp).toLocaleString()}
                </p>
              </div>
            </div>
            
            <button
              onClick={performAudit}
              disabled={scanning}
              className="flex items-center gap-2 px-4 py-2 rounded-xl bg-[#7dcfff]/10 border border-[#7dcfff]/30 text-[#7dcfff] hover:bg-[#7dcfff]/20 transition-all"
            >
              <RefreshCw className={`w-4 h-4 ${scanning ? 'animate-spin' : ''}`} />
              <span className="text-xs font-mono">Rescan</span>
            </button>
          </div>
        </motion.div>

        {/* Metrics */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
          <div className="bg-black/30 backdrop-blur-xl border border-[#7dcfff]/10 rounded-2xl p-4">
            <div className="flex items-center gap-2 mb-2 text-[#7dcfff]">
              <FileText className="w-4 h-4" />
              <span className="text-xs text-[#565f89]">Total Pages</span>
            </div>
            <div className="text-2xl font-bold text-white font-mono">{auditData.performance.totalPages}</div>
          </div>
          <div className="bg-black/30 backdrop-blur-xl border border-[#7dcfff]/10 rounded-2xl p-4">
            <div className="flex items-center gap-2 mb-2 text-[#9B72CB]">
              <Package className="w-4 h-4" />
              <span className="text-xs text-[#565f89]">Components</span>
            </div>
            <div className="text-2xl font-bold text-white font-mono">{auditData.performance.totalComponents}</div>
          </div>
          <div className="bg-black/30 backdrop-blur-xl border border-[#7dcfff]/10 rounded-2xl p-4">
            <div className="flex items-center gap-2 mb-2 text-[#9ece6a]">
              <Activity className="w-4 h-4" />
              <span className="text-xs text-[#565f89]">Active Workers</span>
            </div>
            <div className="text-2xl font-bold text-white font-mono">56</div>
          </div>
          <div className="bg-black/30 backdrop-blur-xl border border-[#7dcfff]/10 rounded-2xl p-4">
            <div className="flex items-center gap-2 mb-2 text-[#ff9e64]">
              <Server className="w-4 h-4" />
              <span className="text-xs text-[#565f89]">Bundle Size</span>
            </div>
            <div className="text-2xl font-bold text-white font-mono">{auditData.performance.bundleSize}</div>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          
          {/* Pages */}
          <div className="bg-black/30 backdrop-blur-xl border border-[#7dcfff]/10 rounded-2xl p-6">
            <h2 className="text-lg font-bold text-white mb-4 flex items-center gap-2">
              <Folder className="w-5 h-5 text-[#7dcfff]" />
              Active Pages ({auditData.pages.length})
            </h2>
            <div className="space-y-3 max-h-[400px] overflow-y-auto custom-scrollbar">
              {auditData.pages.map((page, i) => (
                <div key={page.path} className="flex items-center justify-between p-3 bg-white/5 rounded-xl">
                  <div className="flex items-center gap-3">
                    <div className="w-8 h-8 rounded-lg bg-[#7dcfff]/10 flex items-center justify-center">
                      <FileCode className="w-4 h-4 text-[#7dcfff]" />
                    </div>
                    <div>
                      <div className="font-mono text-sm text-white">{page.path}</div>
                      <div className="text-xs text-[#565f89]">{page.component}</div>
                    </div>
                  </div>
                  <div className="flex items-center gap-3">
                    <span className="text-xs text-[#565f89]">{page.size}</span>
                    <span className="text-xs px-2 py-1 rounded-full bg-[#9ece6a]/20 text-[#9ece6a]">
                      {page.status}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Components */}
          <div className="bg-black/30 backdrop-blur-xl border border-[#7dcfff]/10 rounded-2xl p-6">
            <h2 className="text-lg font-bold text-white mb-4 flex items-center gap-2">
              <Package className="w-5 h-5 text-[#9B72CB]" />
              Component Inventory ({auditData.components.length})
            </h2>
            <div className="space-y-3 max-h-[400px] overflow-y-auto custom-scrollbar">
              {auditData.components.map((comp) => (
                <div key={comp.name} className="flex items-center justify-between p-3 bg-white/5 rounded-xl group">
                  <div className="flex-1">
                    <div className="flex items-center gap-2 flex-wrap">
                      <span className="font-mono text-sm text-white">{comp.name}</span>
                      <span className={`text-[8px] px-1.5 py-0.5 rounded font-mono ${
                        comp.status === 'active' 
                          ? 'bg-[#9ece6a]/20 text-[#9ece6a]' 
                          : 'bg-[#565f89]/20 text-[#565f89]'
                      }`}>
                        {comp.status}
                      </span>
                    </div>
                    <div className="text-xs text-[#565f89] mt-0.5">{comp.purpose}</div>
                    <div className="text-[9px] font-mono text-[#7dcfff]/50 mt-1">{comp.filePath}</div>
                    {comp.usedBy.length > 0 && (
                      <div className="text-[8px] font-mono text-[#9ece6a]/70 mt-1">
                        Used in: {comp.usedBy.map(p => path.basename(p)).join(', ')}
                      </div>
                    )}
                  </div>
                  <div className="text-xs font-mono text-[#565f89] bg-black/30 px-2 py-1 rounded">
                    {comp.usedIn} usage{comp.usedIn !== 1 ? 's' : ''}
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Issues */}
        <div className="mt-6 bg-black/30 backdrop-blur-xl border border-[#7dcfff]/10 rounded-2xl p-6">
          <h2 className="text-lg font-bold text-white mb-4 flex items-center gap-2">
            <Terminal className="w-5 h-5 text-[#f7768e]" />
            Audit Findings
          </h2>
          <div className="space-y-2 max-h-[300px] overflow-y-auto">
            {auditData.issues.map((issue, i) => (
              <div key={i} className={`p-3 rounded-xl flex items-start gap-3 ${
                issue.type === 'error' ? 'bg-[#f7768e]/10 border border-[#f7768e]/30' :
                issue.type === 'warning' ? 'bg-[#e0af68]/10 border border-[#e0af68]/30' :
                'bg-[#9ece6a]/10 border border-[#9ece6a]/30'
              }`}>
                {issue.type === 'error' && <AlertTriangle className="w-4 h-4 text-[#f7768e] mt-0.5" />}
                {issue.type === 'warning' && <AlertTriangle className="w-4 h-4 text-[#e0af68] mt-0.5" />}
                {issue.type === 'success' && <CheckCircle className="w-4 h-4 text-[#9ece6a] mt-0.5" />}
                
                <div className="flex-1">
                  <span className="text-sm text-white/90">{issue.message}</span>
                  {issue.component && (
                    <span className="ml-2 text-xs font-mono text-[#565f89]">[{issue.component}]</span>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      <style jsx global>{`
        .custom-scrollbar::-webkit-scrollbar { width: 4px; }
        .custom-scrollbar::-webkit-scrollbar-track { background: rgba(125,207,255,0.05); border-radius: 4px; }
        .custom-scrollbar::-webkit-scrollbar-thumb { background: rgba(125,207,255,0.3); border-radius: 4px; }
      `}</style>
    </div>
  );
}

// Helper for path
const path = {
  basename: (p: string) => p.split(/[\\/]/).pop() || p
};
