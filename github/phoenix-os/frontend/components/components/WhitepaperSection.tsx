// components/WhitepaperSection.tsx
'use client';

import { motion } from 'framer-motion';
import { BookOpen, FileText, Download, ExternalLink, Shield, Users, FileCheck, Cpu, GitBranch } from 'lucide-react';

export const WhitepaperSection = () => {
  return (
    <section id="docs" className="scroll-mt-20 py-20 px-8 border-b border-white/[0.05]">
      <div className="max-w-6xl mx-auto">
        {/* Header */}
        <motion.div 
          className="text-center mb-12"
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
        >
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-[#9ece6a]/10 border border-[#9ece6a]/20 mb-4">
            <BookOpen className="w-4 h-4 text-[#9ece6a]" />
            <span className="text-xs font-mono text-[#9ece6a]">SOVEREIGN AI WHITEPAPER</span>
          </div>
          <h2 className="text-4xl font-bold text-white mb-4">The Sovereign Constitution</h2>
          <p className="text-[#565f89] max-w-2xl mx-auto">
            From root seed to sovereign OS. The complete architectural specification of RezHive.
          </p>
        </motion.div>

        {/* Document Cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-12">
          {/* Whitepaper */}
          <motion.a
            href="/whitepaper.pdf"
            target="_blank"
            className="group bg-[#0a0a0c] border border-white/[0.05] rounded-2xl p-6 hover:border-[#9ece6a]/30 transition-all"
            whileHover={{ y: -4 }}
          >
            <div className="w-12 h-12 rounded-xl bg-[#9ece6a]/10 flex items-center justify-center mb-4 group-hover:bg-[#9ece6a]/20 transition-all">
              <FileText className="w-6 h-6 text-[#9ece6a]" />
            </div>
            <h3 className="text-lg font-bold text-white mb-2">Technical Whitepaper</h3>
            <p className="text-sm text-[#565f89] mb-4">
              Complete architecture specification: SCE Protocol, Swarm Intelligence, Constitutional Enforcement.
            </p>
            <div className="flex items-center gap-2 text-xs text-[#9ece6a]">
              <span>Download PDF</span>
              <Download className="w-3 h-3" />
            </div>
          </motion.a>

          {/* Quick Start */}
          <motion.a
            href="/docs/quickstart"
            className="group bg-[#0a0a0c] border border-white/[0.05] rounded-2xl p-6 hover:border-[#9ece6a]/30 transition-all"
            whileHover={{ y: -4 }}
          >
            <div className="w-12 h-12 rounded-xl bg-[#9ece6a]/10 flex items-center justify-center mb-4 group-hover:bg-[#9ece6a]/20 transition-all">
              <Cpu className="w-6 h-6 text-[#9ece6a]" />
            </div>
            <h3 className="text-lg font-bold text-white mb-2">Quick Start Guide</h3>
            <p className="text-sm text-[#565f89] mb-4">
              Get your sovereign AI trading in 10 minutes. Install, configure, deploy.
            </p>
            <div className="flex items-center gap-2 text-xs text-[#9ece6a]">
              <span>Read Guide</span>
              <ExternalLink className="w-3 h-3" />
            </div>
          </motion.a>

          {/* API Reference */}
          <motion.a
            href="/docs/api"
            className="group bg-[#0a0a0c] border border-white/[0.05] rounded-2xl p-6 hover:border-[#9ece6a]/30 transition-all"
            whileHover={{ y: -4 }}
          >
            <div className="w-12 h-12 rounded-xl bg-[#9ece6a]/10 flex items-center justify-center mb-4 group-hover:bg-[#9ece6a]/20 transition-all">
              <GitBranch className="w-6 h-6 text-[#9ece6a]" />
            </div>
            <h3 className="text-lg font-bold text-white mb-2">API Reference</h3>
            <p className="text-sm text-[#565f89] mb-4">
              Complete API documentation for SCE Protocol, Workers, and Drift Chain.
            </p>
            <div className="flex items-center gap-2 text-xs text-[#9ece6a]">
              <span>View API</span>
              <ExternalLink className="w-3 h-3" />
            </div>
          </motion.a>
        </div>

        {/* Whitepaper Preview */}
        <motion.div 
          className="bg-[#0a0a0c] border border-white/[0.05] rounded-2xl p-8"
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ delay: 0.2 }}
        >
          <div className="flex items-center gap-3 mb-6">
            <Shield className="w-5 h-5 text-[#9ece6a]" />
            <h3 className="text-lg font-bold text-white">Executive Summary</h3>
          </div>
          
          <div className="prose prose-invert max-w-none">
            <p className="text-[#c0caf5] leading-relaxed">
              RezHive is the first sovereign AI operating system with constitutional enforcement. 
              Built on 53 specialized workers, enforced by SCE Protocol, and audited by an immutable drift chain, 
              RezHive enables truly autonomous AI agents that cannot violate their own constitutional laws.
            </p>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mt-6">
              <div className="bg-white/[0.02] rounded-xl p-4">
                <div className="flex items-center gap-2 mb-2">
                  <Shield className="w-4 h-4 text-[#9ece6a]" />
                  <span className="text-sm font-mono text-white">Constitutional Enforcement</span>
                </div>
                <p className="text-xs text-[#565f89]">
                  Invariants enforced at bytecode level. Cannot be bypassed. Every action cryptographically signed.
                </p>
              </div>
              
              <div className="bg-white/[0.02] rounded-xl p-4">
                <div className="flex items-center gap-2 mb-2">
                  <Users className="w-4 h-4 text-[#9ece6a]" />
                  <span className="text-sm font-mono text-white">Swarm Intelligence</span>
                </div>
                <p className="text-xs text-[#565f89]">
                  53 specialized workers, coordinated by L10 Unified Engine, operating in parallel.
                </p>
              </div>
              
              <div className="bg-white/[0.02] rounded-xl p-4">
                <div className="flex items-center gap-2 mb-2">
                  <FileCheck className="w-4 h-4 text-[#9ece6a]" />
                  <span className="text-sm font-mono text-white">Drift Chain Audit</span>
                </div>
                <p className="text-xs text-[#565f89]">
                  Immutable cryptographic record of every action. 98.2% integrity score.
                </p>
              </div>
              
              <div className="bg-white/[0.02] rounded-xl p-4">
                <div className="flex items-center gap-2 mb-2">
                  <Cpu className="w-4 h-4 text-[#9ece6a]" />
                  <span className="text-sm font-mono text-white">Local-First Architecture</span>
                </div>
                <p className="text-xs text-[#565f89]">
                  Runs on RTX 3060. 32K/16K context. No cloud dependency. Your data stays yours.
                </p>
              </div>
            </div>
          </div>
          
          <div className="mt-8 pt-6 border-t border-white/[0.05] flex justify-between items-center">
            <div className="text-xs text-[#565f89]">
              <span className="text-[#9ece6a]">Version 13.3.0</span> • Last updated March 2026
            </div>
            <motion.a
              href="/whitepaper.pdf"
              className="px-4 py-2 bg-[#9ece6a]/10 border border-[#9ece6a]/20 rounded-lg text-xs text-[#9ece6a] hover:bg-[#9ece6a]/20 transition-all flex items-center gap-2"
              whileHover={{ scale: 1.02 }}
            >
              <Download className="w-3 h-3" />
              Download Full Whitepaper
            </motion.a>
          </div>
        </motion.div>
      </div>
    </section>
  );
};