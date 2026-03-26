// app/page.tsx
'use client';

import React, { useEffect } from 'react';
import { motion } from 'framer-motion';
import Link from 'next/link';
import { 
  Shield, Sparkles, Cpu, Zap, Users, GitBranch, 
  FileCheck, BookOpen, ArrowRight, CheckCircle2, 
  Palette, Video, Brain, Globe, Lock, Terminal, 
  Activity, Database, TrendingUp, Code, Image, Layers
} from 'lucide-react';
import { usePhoenix } from '@/hooks/usePhoenix';

export default function LandingPage() {
  const { connected, telemetry, workers, connect } = usePhoenix();

  useEffect(() => {
    connect();
  }, []);

  const features = [
    {
      icon: Shield,
      title: 'Constitutional AI',
      description: 'SCE Protocol enforced at bytecode level. Every action cryptographically signed.',
      color: 'from-blue-500/20 to-blue-600/20',
      borderColor: 'border-blue-500/30'
    },
    {
      icon: Users,
      title: '70+ Specialized Workers',
      description: 'Swarm intelligence with ComfyUI, trading bots, code generation, and more.',
      color: 'from-purple-500/20 to-purple-600/20',
      borderColor: 'border-purple-500/30'
    },
    {
      icon: Palette,
      title: 'ComfyUI Studio',
      description: 'Generate stunning images and videos with SDXL, Flux, and AnimateDiff.',
      color: 'from-pink-500/20 to-pink-600/20',
      borderColor: 'border-pink-500/30'
    },
    {
      icon: Brain,
      title: 'Sovereign Memory',
      description: '11,969+ blueprints indexed with semantic search. Never forgets.',
      color: 'from-green-500/20 to-green-600/20',
      borderColor: 'border-green-500/30'
    },
    {
      icon: GitBranch,
      title: 'Drift Chain Audit',
      description: 'Immutable proof of every decision, generation, and constitution check.',
      color: 'from-yellow-500/20 to-yellow-600/20',
      borderColor: 'border-yellow-500/30'
    },
    {
      icon: TrendingUp,
      title: 'Real-time Trading',
      description: 'Paper trading with real market data. Backtest strategies before going live.',
      color: 'from-cyan-500/20 to-cyan-600/20',
      borderColor: 'border-cyan-500/30'
    }
  ];

  const stats = [
    { value: '70+', label: 'Workers', icon: Users },
    { value: '11.9K', label: 'Blueprints', icon: Brain },
    { value: '100%', label: 'On-chain Audit', icon: FileCheck },
    { value: '0', label: 'Data Leakage', icon: Lock },
  ];

  return (
    <div className="min-h-screen bg-gradient-to-br from-[#0a0a0c] via-[#050505] to-[#0a0a0c]">
      {/* Animated Grid Background */}
      <div className="fixed inset-0 pointer-events-none opacity-20">
        <div className="absolute inset-0 bg-[radial-gradient(circle_at_50%_50%,_#7dcfff_0%,_transparent_50%)] opacity-5" />
        <div className="absolute inset-0" style={{ backgroundImage: 'linear-gradient(to right, #7dcfff0a 1px, transparent 1px), linear-gradient(to bottom, #7dcfff0a 1px, transparent 1px)', backgroundSize: '40px 40px' }} />
      </div>

      {/* Navigation */}
      <nav className="sticky top-0 z-50 bg-black/40 backdrop-blur-xl border-b border-[#7dcfff]/10">
        <div className="container mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <motion.div 
                whileHover={{ rotate: 360 }}
                transition={{ duration: 0.5 }}
                className="w-10 h-10 rounded-xl bg-gradient-to-br from-[#7dcfff]/20 to-[#9B72CB]/20 flex items-center justify-center"
              >
                <Zap className="w-5 h-5 text-[#7dcfff]" />
              </motion.div>
              <div>
                <h1 className="text-xl font-bold bg-gradient-to-r from-[#c0caf5] to-[#7dcfff] bg-clip-text text-transparent">
                  Phoenix OS
                </h1>
                <p className="text-[8px] text-[#565f89]">Sovereign AI Operating System</p>
              </div>
            </div>
            <div className="flex items-center gap-4">
              <div className="flex items-center gap-2 px-3 py-1 rounded-full bg-white/5 border border-white/10">
                <div className={`w-2 h-2 rounded-full ${connected ? 'bg-[#9ece6a] animate-pulse' : 'bg-[#f7768e]'}`} />
                <span className="text-[8px] font-mono text-[#565f89]">
                  {connected ? `${workers.length} Workers` : 'Connecting...'}
                </span>
              </div>
              <Link href="/dashboard">
                <motion.button 
                  whileHover={{ scale: 1.05 }}
                  whileTap={{ scale: 0.95 }}
                  className="px-4 py-2 rounded-lg bg-gradient-to-r from-[#7dcfff]/20 to-[#9B72CB]/20 border border-[#7dcfff]/30 text-[#7dcfff] text-sm font-medium hover:shadow-lg transition-all flex items-center gap-2"
                >
                  <Terminal className="w-4 h-4" />
                  Launch Terminal
                </motion.button>
              </Link>
            </div>
          </div>
        </div>
      </nav>

      {/* Hero Section */}
      <section className="relative py-20 px-6">
        <div className="container mx-auto text-center">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8 }}
          >
            <motion.div 
              animate={{ scale: [1, 1.05, 1] }}
              transition={{ duration: 2, repeat: Infinity }}
              className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-[#7dcfff]/10 border border-[#7dcfff]/20 mb-6"
            >
              <Shield className="w-3 h-3 text-[#7dcfff]" />
              <span className="text-xs font-mono text-[#7dcfff]">SCE PROTOCOL v2.0</span>
            </motion.div>
            <h1 className="text-5xl md:text-7xl font-bold mb-6">
              <span className="bg-gradient-to-r from-[#c0caf5] via-[#7dcfff] to-[#9B72CB] bg-clip-text text-transparent">
                Sovereign AI
              </span>
              <br />
              Operating System
            </h1>
            <p className="text-xl text-[#565f89] max-w-2xl mx-auto mb-8">
              The first AI system with constitutional enforcement. Every action cryptographically signed. 
              Every decision auditable. Complete sovereignty.
            </p>
            <div className="flex gap-4 justify-center">
              <Link href="/dashboard">
                <motion.button 
                  whileHover={{ scale: 1.05 }}
                  whileTap={{ scale: 0.95 }}
                  className="px-8 py-3 rounded-xl bg-gradient-to-r from-[#7dcfff] to-[#9B72CB] text-black font-bold hover:opacity-90 transition flex items-center gap-2"
                >
                  Launch Terminal
                  <ArrowRight className="w-4 h-4" />
                </motion.button>
              </Link>
              <Link href="#features">
                <motion.button 
                  whileHover={{ scale: 1.05 }}
                  whileTap={{ scale: 0.95 }}
                  className="px-8 py-3 rounded-xl bg-white/5 border border-white/10 text-white hover:bg-white/10 transition"
                >
                  Learn More
                </motion.button>
              </Link>
            </div>
          </motion.div>

          {/* Stats */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-6 mt-20">
            {stats.map((stat, idx) => {
              const Icon = stat.icon;
              return (
                <motion.div
                  key={idx}
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: idx * 0.1 }}
                  whileHover={{ y: -5 }}
                  className="bg-black/30 backdrop-blur-xl border border-[#7dcfff]/10 rounded-2xl p-6 text-center"
                >
                  <Icon className="w-8 h-8 text-[#7dcfff] mx-auto mb-3" />
                  <motion.div 
                    initial={{ scale: 0 }}
                    animate={{ scale: 1 }}
                    transition={{ delay: idx * 0.1 + 0.3 }}
                    className="text-3xl font-bold text-white"
                  >
                    {stat.value}
                  </motion.div>
                  <div className="text-xs text-[#565f89] mt-1">{stat.label}</div>
                </motion.div>
              );
            })}
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section id="features" className="py-20 px-6 border-t border-[#7dcfff]/10">
        <div className="container mx-auto">
          <motion.div 
            initial={{ opacity: 0 }}
            whileInView={{ opacity: 1 }}
            viewport={{ once: true }}
            className="text-center mb-12"
          >
            <h2 className="text-3xl md:text-4xl font-bold text-white mb-4">
              Built for <span className="text-[#7dcfff]">Sovereignty</span>
            </h2>
            <p className="text-[#565f89] max-w-2xl mx-auto">
              Every feature designed with constitutional enforcement at its core.
              No black boxes. No hidden training. Complete transparency.
            </p>
          </motion.div>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {features.map((feature, idx) => {
              const Icon = feature.icon;
              return (
                <motion.div
                  key={idx}
                  initial={{ opacity: 0, y: 20 }}
                  whileInView={{ opacity: 1, y: 0 }}
                  transition={{ delay: idx * 0.1 }}
                  viewport={{ once: true }}
                  whileHover={{ y: -8, scale: 1.02 }}
                  className={`bg-gradient-to-br ${feature.color} rounded-2xl p-6 border ${feature.borderColor} backdrop-blur-sm transition-all cursor-pointer`}
                >
                  <Icon className="w-10 h-10 text-white mb-4" />
                  <h3 className="text-xl font-bold text-white mb-2">{feature.title}</h3>
                  <p className="text-sm text-[#c0caf5]/80">{feature.description}</p>
                </motion.div>
              );
            })}
          </div>
        </div>
      </section>

      {/* How It Works Section */}
      <section className="py-20 px-6 border-t border-[#7dcfff]/10">
        <div className="container mx-auto">
          <motion.div 
            initial={{ opacity: 0 }}
            whileInView={{ opacity: 1 }}
            viewport={{ once: true }}
            className="text-center mb-12"
          >
            <h2 className="text-3xl md:text-4xl font-bold text-white mb-4">
              How It <span className="text-[#9B72CB]">Works</span>
            </h2>
            <p className="text-[#565f89] max-w-2xl mx-auto">
              Three layers of sovereignty ensuring your AI remains truly yours.
            </p>
          </motion.div>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            <motion.div 
              initial={{ opacity: 0, x: -20 }}
              whileInView={{ opacity: 1, x: 0 }}
              viewport={{ once: true }}
              className="text-center"
            >
              <div className="w-20 h-20 rounded-full bg-gradient-to-br from-[#7dcfff]/20 to-[#9B72CB]/20 flex items-center justify-center mx-auto mb-4 border border-[#7dcfff]/30">
                <Shield className="w-10 h-10 text-[#7dcfff]" />
              </div>
              <h3 className="text-xl font-bold text-white mb-2">1. Constitutional AI</h3>
              <p className="text-sm text-[#565f89]">SCE Protocol enforces unbreakable laws at bytecode level</p>
            </motion.div>
            <motion.div 
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ delay: 0.1 }}
              className="text-center"
            >
              <div className="w-20 h-20 rounded-full bg-gradient-to-br from-[#7dcfff]/20 to-[#9B72CB]/20 flex items-center justify-center mx-auto mb-4 border border-[#7dcfff]/30">
                <GitBranch className="w-10 h-10 text-[#7dcfff]" />
              </div>
              <h3 className="text-xl font-bold text-white mb-2">2. Drift Chain Audit</h3>
              <p className="text-sm text-[#565f89]">Every action cryptographically signed and immutable</p>
            </motion.div>
            <motion.div 
              initial={{ opacity: 0, x: 20 }}
              whileInView={{ opacity: 1, x: 0 }}
              viewport={{ once: true }}
              transition={{ delay: 0.2 }}
              className="text-center"
            >
              <div className="w-20 h-20 rounded-full bg-gradient-to-br from-[#7dcfff]/20 to-[#9B72CB]/20 flex items-center justify-center mx-auto mb-4 border border-[#7dcfff]/30">
                <Lock className="w-10 h-10 text-[#7dcfff]" />
              </div>
              <h3 className="text-xl font-bold text-white mb-2">3. Data Sovereignty</h3>
              <p className="text-sm text-[#565f89]">Zero data leakage. Your intelligence stays yours.</p>
            </motion.div>
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-20 px-6 border-t border-[#7dcfff]/10">
        <div className="container mx-auto">
          <motion.div 
            initial={{ opacity: 0, scale: 0.95 }}
            whileInView={{ opacity: 1, scale: 1 }}
            viewport={{ once: true }}
            className="bg-gradient-to-r from-[#7dcfff]/10 to-[#9B72CB]/10 rounded-3xl p-12 border border-[#7dcfff]/20 text-center"
          >
            <h2 className="text-3xl md:text-4xl font-bold text-white mb-4">
              Ready to take control?
            </h2>
            <p className="text-[#565f89] max-w-2xl mx-auto mb-8">
              Join the sovereign AI revolution. Your data, your rules, your intelligence.
            </p>
            <Link href="/dashboard">
              <motion.button 
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
                className="px-8 py-3 rounded-xl bg-gradient-to-r from-[#7dcfff] to-[#9B72CB] text-black font-bold hover:opacity-90 transition flex items-center gap-2 mx-auto"
              >
                Launch Terminal
                <Terminal className="w-4 h-4" />
              </motion.button>
            </Link>
          </motion.div>
        </div>
      </section>

      {/* Footer */}
      <footer className="py-8 px-6 border-t border-[#7dcfff]/10">
        <div className="container mx-auto text-center text-[10px] text-[#565f89]">
          <p>Phoenix OS • Constitutional AI • SCE Protocol v2.0</p>
          <p className="mt-2">All actions cryptographically signed and auditable on the drift chain.</p>
          <div className="flex justify-center gap-6 mt-4">
            <Link href="/dashboard" className="hover:text-[#7dcfff] transition">Terminal</Link>
            <Link href="/trading" className="hover:text-[#7dcfff] transition">Trading</Link>
            <Link href="/paper-trading" className="hover:text-[#7dcfff] transition">Paper Trading</Link>
          </div>
        </div>
      </footer>
    </div>
  );
}