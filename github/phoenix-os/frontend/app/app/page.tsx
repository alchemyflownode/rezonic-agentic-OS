// app/page.tsx
'use client';

import React, { useEffect, useCallback, useState, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import Link from 'next/link';
import {
  Shield, Zap, Users, GitBranch, FileCheck, ArrowRight,
  Palette, Brain, Lock, Terminal, TrendingUp, ChevronDown,
  Activity, Code, Image as ImageIcon, X,
} from 'lucide-react';
import { usePhoenix } from '@/hooks/usePhoenix';
import { useDriftStream, type DriftEntry } from '@/hooks/useDriftStream';

// ═══════════════════════════════════════════════════════════
// CONSTANTS
// ═══════════════════════════════════════════════════════════

const FEATURES = [
  {
    icon: Shield,
    title: 'Constitutional AI',
    subtitle: 'SCE Protocol v2.0',
    description: 'Every action validated against immutable constitutional articles before execution.',
    color: 'from-blue-500/20 to-blue-600/20',
    border: 'border-blue-500/30',
    details: {
      articles: ['No Deception', 'Sovereign Memory', 'Zero Leakage', 'Audit Trail'],
      endpoint: '/api/v1/constitution/check',
      example: '{ "action": "trade", "sce_pass": true, "article": "2.1", "hash": "0x7f3a..." }',
    },
  },
  {
    icon: Users,
    title: '70+ Specialized Workers',
    subtitle: 'Swarm Intelligence',
    description: 'Coordinated worker swarm: code gen, image synthesis, trading, analysis.',
    color: 'from-purple-500/20 to-purple-600/20',
    border: 'border-purple-500/30',
    details: {
      articles: ['ComfyUI', 'Codex', 'Meridian', 'Vision', 'Sentinel'],
      endpoint: '/api/v1/workers/status',
      example: '{ "active": 47, "queued": 12, "idle": 11, "uptime": "99.97%" }',
    },
  },
  {
    icon: Palette,
    title: 'ComfyUI Studio',
    subtitle: 'Visual Pipeline',
    description: 'SDXL, Flux, AnimateDiff — cinematic AI generation with full audit trail.',
    color: 'from-pink-500/20 to-pink-600/20',
    border: 'border-pink-500/30',
    details: {
      articles: ['SDXL 1.0', 'Flux Dev', 'AnimateDiff', 'ControlNet'],
      endpoint: '/api/v1/comfyui/generate',
      example: '{ "model": "sdxl", "steps": 30, "cfg": 7.5, "output": "1024x1024" }',
    },
  },
  {
    icon: Brain,
    title: 'Sovereign Memory',
    subtitle: '11,969+ Blueprints',
    description: 'Semantic search across all indexed knowledge. Context-aware retrieval.',
    color: 'from-green-500/20 to-green-600/20',
    border: 'border-green-500/30',
    details: {
      articles: ['Vector Store', 'Semantic Index', 'Blueprint Registry', 'Context Engine'],
      endpoint: '/api/v1/memory/search',
      example: '{ "query": "momentum strategy", "results": 47, "latency_ms": 12 }',
    },
  },
  {
    icon: GitBranch,
    title: 'Drift Chain Audit',
    subtitle: 'Immutable Ledger',
    description: 'Cryptographic proof of every decision, generation, and constitution check.',
    color: 'from-yellow-500/20 to-yellow-600/20',
    border: 'border-yellow-500/30',
    details: {
      articles: ['Block Sealing', 'Hash Verification', 'Tamper Detection', 'Export'],
      endpoint: '/api/v1/drift/latest',
      example: '{ "block": 48291, "entries": 1247, "integrity": "verified" }',
    },
  },
  {
    icon: TrendingUp,
    title: 'Real-time Trading',
    subtitle: 'Paper & Live',
    description: 'Backtest strategies, paper trade with real data, graduate to live execution.',
    color: 'from-cyan-500/20 to-cyan-600/20',
    border: 'border-cyan-500/30',
    details: {
      articles: ['Paper Trading', 'Backtesting', 'Risk Management', 'Market Data'],
      endpoint: '/api/v1/trading/execute',
      example: '{ "mode": "paper", "symbol": "SPY", "side": "LONG", "pnl": "+$420" }',
    },
  },
] as const;

const STATS = [
  { value: '70+', label: 'Workers',        icon: Users },
  { value: '11.9K', label: 'Blueprints',   icon: Brain },
  { value: '100%', label: 'On-chain Audit', icon: FileCheck },
  { value: '0',   label: 'Data Leakage',   icon: Lock },
] as const;

const PERSONAS = [
  {
    icon: TrendingUp,
    title: 'For Traders',
    points: [
      'Deterministic execution with full audit trail',
      'Paper trading → backtesting → live (graduated)',
      'NinjaTrader-grade interface, AI-native engine',
    ],
    cta: '/trading',
    ctaLabel: 'Open Trading Terminal',
    accent: 'phoenix-primary',
  },
  {
    icon: Code,
    title: 'For Developers',
    points: [
      'Programmable AI infrastructure via API',
      '70+ workers orchestrated through WebSocket',
      'Full source audit — no black boxes',
    ],
    cta: '/dashboard',
    ctaLabel: 'Launch Terminal',
    accent: 'phoenix-accent',
  },
  {
    icon: ImageIcon,
    title: 'For Creators',
    points: [
      'Cinematic AI pipelines (SDXL, Flux, AnimateDiff)',
      'ComfyUI studio with version-controlled workflows',
      'Every generation constitutionally verified',
    ],
    cta: '/dashboard',
    ctaLabel: 'Open Studio',
    accent: 'phoenix-success',
  },
] as const;

const DRIFT_TYPE_COLORS: Record<DriftEntry['type'], string> = {
  constitution: 'text-blue-400',
  worker:       'text-purple-400',
  memory:       'text-phoenix-success',
  trade:        'text-phoenix-primary',
  audit:        'text-phoenix-warning',
};

const DRIFT_TYPE_PREFIX: Record<DriftEntry['type'], string> = {
  constitution: 'SCE',
  worker:       'WRK',
  memory:       'MEM',
  trade:        'TRD',
  audit:        'AUD',
};

// ═══════════════════════════════════════════════════════════
// SUBCOMPONENTS
// ═══════════════════════════════════════════════════════════

function GridBackground() {
  return (
    <div className="fixed inset-0 pointer-events-none">
      <div className="absolute inset-0 bg-[radial-gradient(circle_at_50%_50%,_#7dcfff_0%,_transparent_50%)] opacity-[0.03]" />
      <div
        className="absolute inset-0 opacity-20"
        style={{
          backgroundImage:
            'linear-gradient(to right, rgba(125,207,255,0.04) 1px, transparent 1px), linear-gradient(to bottom, rgba(125,207,255,0.04) 1px, transparent 1px)',
          backgroundSize: '40px 40px',
        }}
      />
      {/* Scan line effect */}
      <div className="absolute inset-0 overflow-hidden">
        <div className="w-full h-px bg-phoenix-primary/10 animate-scan-line" />
      </div>
    </div>
  );
}

function StatusBadge({
  connected,
  workerCount,
}: {
  connected: boolean;
  workerCount: number;
}) {
  return (
    <div className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-white/5 border border-phoenix-border">
      <div
        className={`w-2 h-2 rounded-full ${
          connected ? 'bg-phoenix-success animate-pulse' : 'bg-phoenix-error'
        }`}
      />
      <span className="text-xs font-mono text-phoenix-muted">
        {connected ? `${workerCount} Workers` : 'Connecting…'}
      </span>
    </div>
  );
}

function SystemStatus({
  connected,
  workerCount,
  streamCount,
}: {
  connected: boolean;
  workerCount: number;
  streamCount: number;
}) {
  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ delay: 1 }}
      className="mt-10 mx-auto max-w-md font-mono text-xs border border-phoenix-border rounded-xl bg-black/50 backdrop-blur-xl overflow-hidden"
    >
      <div className="flex items-center gap-2 px-4 py-2 border-b border-phoenix-border bg-white/[0.02]">
        <div className="w-2 h-2 rounded-full bg-phoenix-error" />
        <div className="w-2 h-2 rounded-full bg-phoenix-warning" />
        <div className="w-2 h-2 rounded-full bg-phoenix-success" />
        <span className="ml-2 text-phoenix-muted">phoenix://system-status</span>
      </div>
      <div className="p-4 space-y-1.5">
        <StatusLine label="STATUS" value={connected ? 'ONLINE' : 'BOOTING'} color={connected ? 'text-phoenix-success' : 'text-phoenix-warning'} />
        <StatusLine label="WORKERS" value={`${workerCount} active`} color="text-phoenix-primary" />
        <StatusLine label="CHAIN" value={connected ? `SYNCED (${streamCount} blocks)` : 'PENDING'} color={connected ? 'text-phoenix-success' : 'text-phoenix-muted'} />
        <StatusLine label="SCE" value="ENFORCING" color="text-phoenix-success" />
        <StatusLine label="MEMORY" value="11,969 blueprints" color="text-phoenix-primary" />
        <div className="flex items-center gap-1 text-phoenix-muted pt-1">
          <span className="text-phoenix-success">❯</span>
          <span className="animate-cursor-blink">_</span>
        </div>
      </div>
    </motion.div>
  );
}

function StatusLine({
  label,
  value,
  color,
}: {
  label: string;
  value: string;
  color: string;
}) {
  return (
    <div className="flex items-center gap-2">
      <span className="text-phoenix-muted w-16 text-right">{label}:</span>
      <span className={color}>{value}</span>
    </div>
  );
}

function DriftChainPreview({ entries }: { entries: DriftEntry[] }) {
  const scrollRef = useRef<HTMLDivElement>(null);

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true }}
      className="border border-phoenix-border rounded-xl bg-black/50 backdrop-blur-xl overflow-hidden"
    >
      <div className="flex items-center justify-between px-4 py-2 border-b border-phoenix-border bg-white/[0.02]">
        <div className="flex items-center gap-2">
          <Activity className="w-3 h-3 text-phoenix-success animate-pulse" />
          <span className="text-xs font-mono text-phoenix-muted">
            DRIFT CHAIN — LIVE
          </span>
        </div>
        <span className="text-xs font-mono text-phoenix-muted">
          {entries.length} entries
        </span>
      </div>
      <div ref={scrollRef} className="h-48 overflow-hidden relative">
        {/* Fade masks */}
        <div className="absolute top-0 left-0 right-0 h-6 bg-gradient-to-b from-black/80 to-transparent z-10" />
        <div className="absolute bottom-0 left-0 right-0 h-6 bg-gradient-to-t from-black/80 to-transparent z-10" />
        <div className="p-3 space-y-1">
          <AnimatePresence mode="popLayout">
            {entries.slice(0, 12).map((entry) => (
              <motion.div
                key={entry.id}
                initial={{ opacity: 0, x: -20, height: 0 }}
                animate={{ opacity: 1, x: 0, height: 'auto' }}
                exit={{ opacity: 0 }}
                transition={{ duration: 0.3 }}
                className="flex items-start gap-2 font-mono text-xs"
              >
                <span className="text-phoenix-muted shrink-0">
                  {new Date(entry.timestamp).toLocaleTimeString('en-US', {
                    hour12: false,
                    hour: '2-digit',
                    minute: '2-digit',
                    second: '2-digit',
                  })}
                </span>
                <span className={`shrink-0 ${DRIFT_TYPE_COLORS[entry.type]}`}>
                  [{DRIFT_TYPE_PREFIX[entry.type]}]
                </span>
                <span className="text-phoenix-text/80 truncate">
                  {entry.message}
                </span>
                <span className="text-phoenix-muted/50 shrink-0 ml-auto">
                  {entry.hash}
                </span>
              </motion.div>
            ))}
          </AnimatePresence>
        </div>
      </div>
    </motion.div>
  );
}

function FeatureCard({
  feature,
  isActive,
  onToggle,
}: {
  feature: (typeof FEATURES)[number];
  isActive: boolean;
  onToggle: () => void;
}) {
  const Icon = feature.icon;
  return (
    <motion.div
      layout
      initial={{ opacity: 0, y: 20 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true }}
      whileHover={!isActive ? { y: -8, scale: 1.02 } : undefined}
      onClick={onToggle}
      className={`bg-gradient-to-br ${feature.color} rounded-2xl border ${feature.border} backdrop-blur-sm cursor-pointer transition-all overflow-hidden`}
    >
      <div className="p-6">
        <div className="flex items-start justify-between">
          <Icon className="w-10 h-10 text-white mb-4" />
          <motion.div
            animate={{ rotate: isActive ? 180 : 0 }}
            className="text-phoenix-muted"
          >
            <ChevronDown className="w-4 h-4" />
          </motion.div>
        </div>
        <h3 className="text-xl font-bold text-white mb-1">{feature.title}</h3>
        <p className="text-xs font-mono text-phoenix-primary mb-2">
          {feature.subtitle}
        </p>
        <p className="text-sm text-phoenix-text/80">{feature.description}</p>
      </div>

      <AnimatePresence>
        {isActive && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.3 }}
            className="border-t border-white/10"
          >
            <div className="p-6 space-y-4">
              {/* Capabilities */}
              <div>
                <p className="text-xs font-mono text-phoenix-muted mb-2">
                  CAPABILITIES
                </p>
                <div className="flex flex-wrap gap-2">
                  {feature.details.articles.map((article) => (
                    <span
                      key={article}
                      className="px-2 py-1 text-xs font-mono bg-white/5 border border-white/10 rounded text-phoenix-text"
                    >
                      {article}
                    </span>
                  ))}
                </div>
              </div>

              {/* Endpoint */}
              <div>
                <p className="text-xs font-mono text-phoenix-muted mb-1">
                  ENDPOINT
                </p>
                <code className="text-xs font-mono text-phoenix-primary">
                  {feature.details.endpoint}
                </code>
              </div>

              {/* Example Response */}
              <div>
                <p className="text-xs font-mono text-phoenix-muted mb-1">
                  EXAMPLE RESPONSE
                </p>
                <pre className="text-xs font-mono text-phoenix-success bg-black/30 rounded-lg p-3 overflow-x-auto">
                  {feature.details.example}
                </pre>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  );
}

function PersonaCard({ persona }: { persona: (typeof PERSONAS)[number] }) {
  const Icon = persona.icon;
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true }}
      whileHover={{ y: -5 }}
      className="bg-black/30 backdrop-blur-xl border border-phoenix-border rounded-2xl p-6 flex flex-col"
    >
      <Icon className={`w-8 h-8 text-${persona.accent} mb-4`} />
      <h3 className="text-xl font-bold text-white mb-4">{persona.title}</h3>
      <ul className="space-y-3 flex-1">
        {persona.points.map((point) => (
          <li
            key={point}
            className="flex items-start gap-2 text-sm text-phoenix-text/80"
          >
            <span className="text-phoenix-success mt-0.5 shrink-0">✓</span>
            {point}
          </li>
        ))}
      </ul>
      <Link href={persona.cta}>
        <motion.button
          whileHover={{ scale: 1.03 }}
          whileTap={{ scale: 0.97 }}
          className="mt-6 w-full py-2.5 rounded-lg bg-white/5 border border-white/10 text-sm font-medium text-white hover:bg-white/10 transition flex items-center justify-center gap-2"
        >
          {persona.ctaLabel}
          <ArrowRight className="w-3.5 h-3.5" />
        </motion.button>
      </Link>
    </motion.div>
  );
}

// ═══════════════════════════════════════════════════════════
// MAIN PAGE
// ═══════════════════════════════════════════════════════════

export default function LandingPage() {
  const { connected, workers, connect } = usePhoenix();
  const { entries, start: startDrift } = useDriftStream();
  const [activeFeature, setActiveFeature] = useState<string | null>(null);

  const stableConnect = useCallback(() => {
    connect();
  }, [connect]);

  useEffect(() => {
    stableConnect();
    startDrift();
  }, [stableConnect, startDrift]);

  const toggleFeature = useCallback((title: string) => {
    setActiveFeature((prev) => (prev === title ? null : title));
  }, []);

  return (
    <div className="min-h-screen bg-gradient-to-br from-phoenix-bg via-phoenix-bgSoft to-phoenix-bg text-white">
      <GridBackground />

      {/* ── Nav ──────────────────────────────────────── */}
      <nav className="sticky top-0 z-50 bg-black/60 backdrop-blur-xl border-b border-phoenix-border">
        <div className="container mx-auto px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <motion.div
              whileHover={{ rotate: 360 }}
              transition={{ duration: 0.5 }}
              className="w-10 h-10 rounded-xl bg-gradient-to-br from-phoenix-primary/20 to-phoenix-accent/20 flex items-center justify-center border border-phoenix-border"
            >
              <Zap className="w-5 h-5 text-phoenix-primary" />
            </motion.div>
            <div>
              <h1 className="text-xl font-bold bg-gradient-to-r from-phoenix-text to-phoenix-primary bg-clip-text text-transparent">
                Phoenix OS
              </h1>
              <p className="text-xs text-phoenix-muted font-mono">
                v2.0 • sovereign runtime
              </p>
            </div>
          </div>
          <div className="flex items-center gap-4">
            <StatusBadge
              connected={connected}
              workerCount={workers.length}
            />
            <Link href="/dashboard" className="hidden sm:block">
              <motion.button
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
                className="px-4 py-2 rounded-lg bg-gradient-to-r from-phoenix-primary/20 to-phoenix-accent/20 border border-phoenix-primary/30 text-phoenix-primary text-sm font-medium transition-all flex items-center gap-2"
              >
                <Terminal className="w-4 h-4" />
                Launch Terminal
              </motion.button>
            </Link>
          </div>
        </div>
      </nav>

      {/* ── Hero ─────────────────────────────────────── */}
      <section className="relative py-20 md:py-28 px-6">
        <div className="container mx-auto text-center">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8 }}
          >
            <motion.div
              animate={{ scale: [1, 1.05, 1] }}
              transition={{ duration: 2, repeat: Infinity }}
              className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-phoenix-primary/10 border border-phoenix-primary/20 mb-8"
            >
              <Shield className="w-3.5 h-3.5 text-phoenix-primary" />
              <span className="text-xs font-mono text-phoenix-primary tracking-wider">
                SCE PROTOCOL v2.0 — ACTIVE
              </span>
            </motion.div>

            <h2 className="text-5xl md:text-7xl font-bold mb-6 leading-tight">
              <span className="bg-gradient-to-r from-phoenix-text via-phoenix-primary to-phoenix-accent bg-clip-text text-transparent">
                Sovereign AI
              </span>
              <br />
              <span className="text-white">Operating System</span>
            </h2>

            <p className="text-lg md:text-xl text-phoenix-muted max-w-2xl mx-auto mb-10">
              Constitutional enforcement at bytecode level. Every action signed.
              Every decision auditable. Zero data leakage. Complete sovereignty.
            </p>

            <div className="flex flex-wrap gap-4 justify-center">
              <Link href="/dashboard">
                <motion.button
                  whileHover={{ scale: 1.05 }}
                  whileTap={{ scale: 0.95 }}
                  className="px-8 py-3 rounded-xl bg-gradient-to-r from-phoenix-primary to-phoenix-accent text-black font-bold transition flex items-center gap-2"
                >
                  Launch Terminal
                  <ArrowRight className="w-4 h-4" />
                </motion.button>
              </Link>
              <Link href="#drift-chain">
                <motion.button
                  whileHover={{ scale: 1.05 }}
                  whileTap={{ scale: 0.95 }}
                  className="px-8 py-3 rounded-xl bg-white/5 border border-white/10 hover:bg-white/10 transition"
                >
                  View Live Chain
                </motion.button>
              </Link>
            </div>
          </motion.div>

          {/* Live System Status */}
          <SystemStatus
            connected={connected}
            workerCount={workers.length}
            streamCount={entries.length}
          />

          {/* Stats Row */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-6 mt-16">
            {STATS.map((stat, i) => {
              const Icon = stat.icon;
              return (
                <motion.div
                  key={stat.label}
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: 1.2 + i * 0.1 }}
                  whileHover={{ y: -5 }}
                  className="bg-black/30 backdrop-blur-xl border border-phoenix-border rounded-2xl p-6"
                >
                  <Icon className="w-8 h-8 text-phoenix-primary mx-auto mb-3" />
                  <div className="text-3xl font-bold font-mono">
                    {stat.value}
                  </div>
                  <div className="text-xs text-phoenix-muted mt-1">
                    {stat.label}
                  </div>
                </motion.div>
              );
            })}
          </div>
        </div>
      </section>

      {/* ── Live Drift Chain ─────────────────────────── */}
      <section
        id="drift-chain"
        className="py-20 px-6 border-t border-phoenix-border"
      >
        <div className="container mx-auto max-w-4xl">
          <motion.div
            initial={{ opacity: 0 }}
            whileInView={{ opacity: 1 }}
            viewport={{ once: true }}
            className="text-center mb-12"
          >
            <h2 className="text-3xl md:text-4xl font-bold mb-4">
              Live <span className="text-phoenix-primary">Drift Chain</span>
            </h2>
            <p className="text-phoenix-muted max-w-2xl mx-auto">
              Real-time cryptographic audit trail. Every worker action,
              constitution check, and trade execution — immutably recorded.
            </p>
          </motion.div>

          <DriftChainPreview entries={entries} />

          <motion.p
            initial={{ opacity: 0 }}
            whileInView={{ opacity: 1 }}
            viewport={{ once: true }}
            className="text-center text-xs font-mono text-phoenix-muted mt-4"
          >
            ↑ This is not a demo. This stream reflects live system activity.
          </motion.p>
        </div>
      </section>

      {/* ── Features ─────────────────────────────────── */}
      <section
        id="features"
        className="py-20 px-6 border-t border-phoenix-border"
      >
        <div className="container mx-auto">
          <motion.div
            initial={{ opacity: 0 }}
            whileInView={{ opacity: 1 }}
            viewport={{ once: true }}
            className="text-center mb-16"
          >
            <h2 className="text-3xl md:text-4xl font-bold mb-4">
              Built for{' '}
              <span className="text-phoenix-primary">Sovereignty</span>
            </h2>
            <p className="text-phoenix-muted max-w-2xl mx-auto">
              Click any feature to inspect its API surface. No black boxes.
            </p>
          </motion.div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {FEATURES.map((feature) => (
              <FeatureCard
                key={feature.title}
                feature={feature}
                isActive={activeFeature === feature.title}
                onToggle={() => toggleFeature(feature.title)}
              />
            ))}
          </div>
        </div>
      </section>

      {/* ── Who This Is For ──────────────────────────── */}
      <section className="py-20 px-6 border-t border-phoenix-border">
        <div className="container mx-auto">
          <motion.div
            initial={{ opacity: 0 }}
            whileInView={{ opacity: 1 }}
            viewport={{ once: true }}
            className="text-center mb-16"
          >
            <h2 className="text-3xl md:text-4xl font-bold mb-4">
              Built for <span className="text-phoenix-accent">You</span>
            </h2>
            <p className="text-phoenix-muted max-w-2xl mx-auto">
              Three audiences. One sovereign platform.
            </p>
          </motion.div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {PERSONAS.map((persona) => (
              <PersonaCard key={persona.title} persona={persona} />
            ))}
          </div>
        </div>
      </section>

      {/* ── How It Works ─────────────────────────────── */}
      <section className="py-20 px-6 border-t border-phoenix-border">
        <div className="container mx-auto">
          <motion.div
            initial={{ opacity: 0 }}
            whileInView={{ opacity: 1 }}
            viewport={{ once: true }}
            className="text-center mb-16"
          >
            <h2 className="text-3xl md:text-4xl font-bold mb-4">
              How It <span className="text-phoenix-accent">Works</span>
            </h2>
            <p className="text-phoenix-muted max-w-2xl mx-auto">
              Three layers of sovereignty. No exceptions.
            </p>
          </motion.div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-8 relative">
            {/* Connection line */}
            <div className="hidden md:block absolute top-10 left-1/6 right-1/6 h-px bg-gradient-to-r from-transparent via-phoenix-primary/30 to-transparent" />

            {[
              {
                icon: Shield,
                title: '1. Constitution',
                desc: 'SCE Protocol validates every action against immutable articles before execution',
              },
              {
                icon: GitBranch,
                title: '2. Drift Chain',
                desc: 'Every validated action is cryptographically signed and sealed into the audit ledger',
              },
              {
                icon: Lock,
                title: '3. Sovereignty',
                desc: 'Zero data leaves the system. Your intelligence, your infrastructure, your rules',
              },
            ].map((step, i) => {
              const Icon = step.icon;
              return (
                <motion.div
                  key={step.title}
                  initial={{ opacity: 0, y: 20 }}
                  whileInView={{ opacity: 1, y: 0 }}
                  viewport={{ once: true }}
                  transition={{ delay: i * 0.15 }}
                  className="text-center relative"
                >
                  <div className="w-20 h-20 rounded-full bg-gradient-to-br from-phoenix-primary/20 to-phoenix-accent/20 flex items-center justify-center mx-auto mb-4 border border-phoenix-primary/30">
                    <Icon className="w-10 h-10 text-phoenix-primary" />
                  </div>
                  <h3 className="text-xl font-bold mb-2">{step.title}</h3>
                  <p className="text-sm text-phoenix-muted max-w-xs mx-auto">
                    {step.desc}
                  </p>
                </motion.div>
              );
            })}
          </div>
        </div>
      </section>

      {/* ── CTA ──────────────────────────────────────── */}
      <section className="py-20 px-6 border-t border-phoenix-border">
        <div className="container mx-auto">
          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            whileInView={{ opacity: 1, scale: 1 }}
            viewport={{ once: true }}
            className="bg-gradient-to-r from-phoenix-primary/10 to-phoenix-accent/10 rounded-3xl p-12 border border-phoenix-primary/20 text-center relative overflow-hidden"
          >
            {/* Ambient glow */}
            <div className="absolute inset-0 bg-[radial-gradient(circle_at_50%_50%,_rgba(125,207,255,0.08)_0%,_transparent_60%)]" />

            <div className="relative z-10">
              <h2 className="text-3xl md:text-4xl font-bold mb-4">
                Ready to take control?
              </h2>
              <p className="text-phoenix-muted max-w-2xl mx-auto mb-8">
                Your data. Your rules. Your intelligence. No exceptions.
              </p>
              <Link href="/dashboard">
                <motion.button
                  whileHover={{ scale: 1.05 }}
                  whileTap={{ scale: 0.95 }}
                  className="px-8 py-3 rounded-xl bg-gradient-to-r from-phoenix-primary to-phoenix-accent text-black font-bold transition flex items-center gap-2 mx-auto"
                >
                  <Terminal className="w-4 h-4" />
                  Launch Terminal
                </motion.button>
              </Link>
            </div>
          </motion.div>
        </div>
      </section>

      {/* ── Footer ───────────────────────────────────── */}
      <footer className="py-8 px-6 border-t border-phoenix-border">
        <div className="container mx-auto text-center text-xs text-phoenix-muted font-mono">
          <p>
            PHOENIX OS · SCE PROTOCOL v2.0 · CONSTITUTIONAL AI
          </p>
          <p className="mt-1">
            All actions cryptographically signed and auditable on the drift
            chain.
          </p>
          <nav className="flex justify-center gap-6 mt-4">
            {[
              { href: '/dashboard', label: 'Terminal' },
              { href: '/trading', label: 'Trading' },
              { href: '/paper-trading', label: 'Paper Trading' },
              { href: '#drift-chain', label: 'Drift Chain' },
            ].map((link) => (
              <Link
                key={link.href}
                href={link.href}
                className="hover:text-phoenix-primary transition"
              >
                {link.label}
              </Link>
            ))}
          </nav>
        </div>
      </footer>
    </div>
  );
}