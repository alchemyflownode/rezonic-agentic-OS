# Create UI Audit page
$auditPage = @'
'use client';

import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { 
  Layout, Shield, Zap, AlertTriangle, CheckCircle, 
  Code, FileText, Package, Activity, Server 
} from 'lucide-react';

export default function UIAuditPage() {
  const [auditData, setAuditData] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Simulate audit data collection
    setTimeout(() => {
      setAuditData({
        pages: [
          { path: '/dashboard', component: 'SovereignMessage', status: 'active', size: '24KB' },
          { path: '/system/appbuilder', component: 'SovereignCanvas', status: 'active', size: '18KB' },
          { path: '/system/scanner', component: 'SovereignCanvas', status: 'active', size: '12KB' },
          { path: '/system/techdebt', component: 'SovereignCanvas', status: 'active', size: '14KB' }
        ],
        components: [
          { name: 'SovereignCanvas', purpose: 'Code display & execution', usedIn: 3 },
          { name: 'SovereignMessage', purpose: 'Chat & AI responses', usedIn: 1 },
          { name: 'SovereignCodeBlock', purpose: 'Static code snippets', usedIn: 0 },
          { name: 'SovereignCodeSurface', purpose: 'Full code editor', usedIn: 0 }
        ],
        issues: [
          { type: 'warning', message: 'SovereignCodeBlock component exists but not used anywhere' },
          { type: 'info', message: 'All system pages integrated with SovereignCanvas' }
        ],
        performance: {
          totalComponents: 4,
          totalPages: 4,
          buildTime: '2.5s',
          bundleSize: '245KB'
        }
      });
      setLoading(false);
    }, 1000);
  }, []);

  if (loading) {
    return (
      <div className="min-h-screen bg-black flex items-center justify-center">
        <div className="text-center">
          <div className="w-12 h-12 border-2 border-[#7dcfff] border-t-transparent rounded-full animate-spin mx-auto mb-4" />
          <p className="text-[#7dcfff]">Auditing UI components...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-[#0a0a0c] to-[#050505] p-8">
      <div className="max-w-6xl mx-auto">
        <motion.div
          initial={{ y: -20, opacity: 0 }}
          animate={{ y: 0, opacity: 1 }}
          className="mb-8"
        >
          <div className="flex items-center gap-4 mb-2">
            <div className="w-12 h-12 rounded-2xl bg-gradient-to-br from-[#7dcfff]/20 to-[#9B72CB]/20 border border-[#7dcfff]/30 flex items-center justify-center">
              <Layout className="w-6 h-6 text-[#7dcfff]" />
            </div>
            <div>
              <h1 className="text-3xl font-bold bg-gradient-to-r from-[#c0caf5] to-[#7dcfff] bg-clip-text text-transparent">
                UI Audit Dashboard
              </h1>
              <p className="text-[#565f89] mt-1">Comprehensive component inventory and health check</p>
            </div>
          </div>
        </motion.div>

        {/* Performance Metrics */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
          <div className="bg-black/30 backdrop-blur-xl border border-[#7dcfff]/10 rounded-2xl p-4">
            <div className="flex items-center gap-2 mb-2">
              <FileText className="w-4 h-4 text-[#7dcfff]" />
              <span className="text-xs text-[#565f89]">Total Pages</span>
            </div>
            <div className="text-2xl font-bold text-white">{auditData.performance.totalPages}</div>
          </div>
          <div className="bg-black/30 backdrop-blur-xl border border-[#7dcfff]/10 rounded-2xl p-4">
            <div className="flex items-center gap-2 mb-2">
              <Package className="w-4 h-4 text-[#7dcfff]" />
              <span className="text-xs text-[#565f89]">Components</span>
            </div>
            <div className="text-2xl font-bold text-white">{auditData.performance.totalComponents}</div>
          </div>
          <div className="bg-black/30 backdrop-blur-xl border border-[#7dcfff]/10 rounded-2xl p-4">
            <div className="flex items-center gap-2 mb-2">
              <Activity className="w-4 h-4 text-[#7dcfff]" />
              <span className="text-xs text-[#565f89]">Build Time</span>
            </div>
            <div className="text-2xl font-bold text-white">{auditData.performance.buildTime}</div>
          </div>
          <div className="bg-black/30 backdrop-blur-xl border border-[#7dcfff]/10 rounded-2xl p-4">
            <div className="flex items-center gap-2 mb-2">
              <Server className="w-4 h-4 text-[#7dcfff]" />
              <span className="text-xs text-[#565f89]">Bundle Size</span>
            </div>
            <div className="text-2xl font-bold text-white">{auditData.performance.bundleSize}</div>
          </div>
        </div>

        {/* Pages Grid */}
        <div className="bg-black/30 backdrop-blur-xl border border-[#7dcfff]/10 rounded-2xl p-6 mb-6">
          <h2 className="text-lg font-bold text-white mb-4 flex items-center gap-2">
            <Layout className="w-5 h-5 text-[#7dcfff]" />
            Active Pages
          </h2>
          <div className="grid gap-3">
            {auditData.pages.map((page: any, i: number) => (
              <div key={i} className="flex items-center justify-between p-3 bg-white/5 rounded-xl">
                <div className="flex items-center gap-3">
                  <div className="w-8 h-8 rounded-lg bg-[#7dcfff]/10 flex items-center justify-center">
                    <Code className="w-4 h-4 text-[#7dcfff]" />
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

        {/* Component Inventory */}
        <div className="bg-black/30 backdrop-blur-xl border border-[#7dcfff]/10 rounded-2xl p-6 mb-6">
          <h2 className="text-lg font-bold text-white mb-4 flex items-center gap-2">
            <Package className="w-5 h-5 text-[#7dcfff]" />
            Component Inventory
          </h2>
          <div className="grid gap-3">
            {auditData.components.map((comp: any, i: number) => (
              <div key={i} className="flex items-center justify-between p-3 bg-white/5 rounded-xl">
                <div>
                  <div className="font-mono text-sm text-white">{comp.name}</div>
                  <div className="text-xs text-[#565f89]">{comp.purpose}</div>
                </div>
                <div className="text-xs px-2 py-1 rounded-full bg-[#7dcfff]/20 text-[#7dcfff]">
                  Used in {comp.usedIn} {comp.usedIn === 1 ? 'page' : 'pages'}
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Issues */}
        {auditData.issues.length > 0 && (
          <div className="bg-black/30 backdrop-blur-xl border border-[#7dcfff]/10 rounded-2xl p-6">
            <h2 className="text-lg font-bold text-white mb-4 flex items-center gap-2">
              <AlertTriangle className="w-5 h-5 text-[#f7768e]" />
              Audit Findings
            </h2>
            <div className="space-y-2">
              {auditData.issues.map((issue: any, i: number) => (
                <div key={i} className={`p-3 rounded-xl flex items-start gap-2 ${
                  issue.type === 'warning' ? 'bg-yellow-500/10 border border-yellow-500/20' : 'bg-blue-500/10 border border-blue-500/20'
                }`}>
                  {issue.type === 'warning' ? 
                    <AlertTriangle className="w-4 h-4 text-yellow-500 mt-0.5" /> : 
                    <CheckCircle className="w-4 h-4 text-blue-500 mt-0.5" />
                  }
                  <span className="text-sm text-white/90">{issue.message}</span>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
'@

# Save the audit page
$auditPage | Out-File -FilePath "D:\Rezonic_Agentic\apps\phoenix-frontend\app\audit\page.tsx" -Encoding utf8
Write-Host "✅ Created UI Audit page at /audit" -ForegroundColor Green