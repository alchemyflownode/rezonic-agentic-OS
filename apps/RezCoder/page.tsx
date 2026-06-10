/**
 * SovereignDashboard Component
 * ============================
 * Main dashboard interface for Phoenix Kernel frontend.
 * Provides unified control center with:
 * - Real-time kernel status monitoring
 * - Chat interface with streaming responses
 * - Image/video generation gallery (ComfyUI integration)
 * - Command lexicon with search
 * - System metrics and telemetry
 * - Constitutional AI enforcement display
 * 
 * @version 15.3.0-UNIFIED
 * @author Phoenix Team
 */

'use client';
import React, { useState, useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Zap, Shield, Sparkles, Send, Activity,
  Lock, PanelLeftClose, PanelLeftOpen,
  CheckCircle2, Terminal, User, Bot, BookOpen, Search,
  GalleryVertical, Flame, Code, Image, Video,
  TrendingUp, Grid3x3, ChevronRight, Users, Palette
} from 'lucide-react';
import Link from 'next/link';
import { SovereignMessage } from '@/components/SovereignMessage';
import { usePhoenix, useCommandParser, useAutoRefresh } from '@/hooks/usePhoenix';

// ==========================================
// CONSTANTS & CONFIG
// ==========================================
const DASHBOARD_CONFIG = {
  MAX_MESSAGES: 200,
  MAX_IMAGES: 20,
  AUTO_REFRESH_INTERVAL: 5000,
  SCROLL_BEHAVIOR: 'smooth' as const,
  MAX_WORKERS: 70,
  INITIAL_SCE_SCORE: 85,
  PERFECT_SCE_SCORE: 98,
} as const;

const COMMAND_GROUPS = {
  "🦊 SOVEREIGN OS": [
    { name: "/health", desc: "Check core system health", example: "/health" },
    { name: "/workers", desc: "List active workers", example: "/workers" },
    { name: "/portfolio", desc: "View trading portfolio", example: "/portfolio" },
  ],
  "🎨 AI STUDIO": [
    { name: "/generate", desc: "Generate image via ComfyUI", example: "/generate cyberpunk cat" },
    { name: "/video", desc: "Generate video", example: "/video cat running" },
    { name: "/code", desc: "Generate Python code", example: "/code moving average strategy" },
  ],
  "💰 TRADING": [
    { name: "/trade buy", desc: "Execute paper trade", example: "/trade buy BTC 0.01" },
    { name: "/trade sell", desc: "Sell position", example: "/trade sell ETH 0.5" },
    { name: "/backtest", desc: "Run strategy backtest", example: "/backtest moving_average" },
  ],
  "🔍 SYSTEM": [
    { name: "/resource/stats", desc: "CPU, RAM, GPU usage", example: "/resource/stats" },
    { name: "/audit/stats", desc: "Event chain statistics", example: "/audit/stats" },
    { name: "/pulse", desc: "Market sentiment score", example: "/pulse" },
  ],
} as const;

type CommandGroup = typeof COMMAND_GROUPS;
type GeneratedImage = { id: number; prompt: string; url: string; timestamp: string };
type ViewMode = 'dashboard' | 'terminal';
type Tab = 'chat' | 'gallery';

// ==========================================
// COMMAND DATABASE
// ==========================================

/**
 * CommandCard: Renders a single command with description and example.
 * @param name - Command name (e.g., "/health")
 * @param description - Human-readable description
 * @param example - Example usage
 */
const CommandCard = ({ 
  name, 
  description, 
  example 
}: { 
  name: string
  description: string
  example: string 
}) => (
  <div className="p-2 rounded-lg hover:bg-white/5 transition-colors">
    <div className="text-[9px] font-mono text-[#7dcfff]">{name}</div>
    <div className="text-[8px] text-[#565f89]">{description}</div>
    <div className="text-[7px] text-[#9B72CB] mt-1">`ex: {example}`</div>
  </div>
);

export default function SovereignDashboard() {
  // ================== STORE HOOKS ==================
  const store = usePhoenix();
  
  const {
    connected = false,
    messages: storeMessages = [],
    isStreaming = false,
    isLoading = false,
    workers = [],
    telemetry = { 
      chain_valid: false, 
      kernel_load: 0, 
      workers: 0, 
      memory: 0, 
      gpu: { has_gpu: false } 
    },
    error: storeError,
    killSwitch = { active: false, triggered_at: null, triggered_by: null, reason: null },
    comfyui = { connected: false, workflows: [], last_generation: null },
    portfolio = { balance: 1000000, positions: {}, total_value: 1000000, trades: [] },
    sendMessage,
    generateImage,
    generateVideo,
    clearMessages,
    connect,
  } = store || {};

  const { executeCommand } = useCommandParser?.() || { executeCommand: async () => {} };
  
  // ================== UI STATE ==================
  const [mounted, setMounted] = useState(false);
  const [dashboardError, setDashboardError] = useState<string | null>(null);
  const [time, setTime] = useState('');
  const [prompt, setPrompt] = useState('');
  const [activeHash, setActiveHash] = useState('');
  const [activeTab, setActiveTab] = useState<Tab>('chat');
  const [showSidebar, setShowSidebar] = useState(true);
  const [viewMode, setViewMode] = useState<ViewMode>('dashboard');
  const [generatedImages, setGeneratedImages] = useState<GeneratedImage[]>([]);
  const [searchTerm, setSearchTerm] = useState('');
  const [expandedGroup, setExpandedGroup] = useState<string | null>('🦊 SOVEREIGN OS');
  
  const chatEndRef = useRef<HTMLDivElement>(null);
  const terminalEndRef = useRef<HTMLDivElement>(null);
  const terminalInputRef = useRef<HTMLInputElement>(null);

  // 🔥 AUTO-CONNECT
  useEffect(() => {
    if (!connected) {
      console.log('🔌 Connecting to Phoenix Kernel at http://127.0.0.1:8002...');
      connect?.();
    }
  }, [connect, connected]);

  // Auto-refresh every 5 seconds
  useAutoRefresh?.(5000);

  // Clock Effect
  useEffect(() => {
    const clock = setInterval(() => {
      setTime(new Date().toLocaleTimeString('en-US', { 
        hour12: false, 
        hour: '2-digit', 
        minute: '2-digit', 
        second: '2-digit' 
      }));
    }, 1000);
    return () => clearInterval(clock);
  }, []);

  // Handle hash change
  useEffect(() => {
    const handleHashChange = () => setActiveHash(window.location.hash);
    handleHashChange();
    window.addEventListener('hashchange', handleHashChange);
    return () => window.removeEventListener('hashchange', handleHashChange);
  }, []);

  // Scroll to section
  const scrollToSection = (e: React.MouseEvent, hash: string) => {
    e.preventDefault();
    const element = document.querySelector(hash);
    if (element) {
      element.scrollIntoView({ behavior: 'smooth' });
      window.history.pushState(null, '', hash);
      setActiveHash(hash);
    }
  };

  // Mount check
  useEffect(() => {
    setMounted(true);
  }, []);

  // Auto-scroll chat
  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [storeMessages]);

  // Auto-scroll terminal
  useEffect(() => {
    if (viewMode === 'terminal') {
      terminalEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }
  }, [viewMode]);

  // Focus terminal input when mode changes
  useEffect(() => {
    if (viewMode === 'terminal') {
      setTimeout(() => terminalInputRef.current?.focus(), 100);
    }
  }, [viewMode]);

  const handleSend = async () => {
    if (!prompt.trim() || isStreaming || isLoading) return;
    const userText = prompt;
    setPrompt('');

    try {
      if (userText.startsWith('/generate')) {
        const imagePrompt = userText.replace('/generate', '').trim();
        if (!imagePrompt) {
          setDashboardError('Please provide a prompt for image generation');
          return;
        }
        if (generateImage) {
          await generateImage(imagePrompt);
          setTimeout(() => {
            setGeneratedImages(prev => [{
              id: Date.now(),
              prompt: imagePrompt,
              url: `/api/comfyui/latest?t=${Date.now()}`,
              timestamp: new Date().toLocaleTimeString()
            }, ...prev].slice(0, DASHBOARD_CONFIG.MAX_IMAGES));
          }, 3000);
        }
        return;
      } 
      
      if (userText.startsWith('/video')) {
        const videoPrompt = userText.replace('/video', '').trim();
        if (!videoPrompt) {
          setDashboardError('Please provide a prompt for video generation');
          return;
        }
        if (generateVideo) {
          await generateVideo(videoPrompt);
        }
        return;
      }

      await executeCommand?.(userText);
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Command execution failed';
      setDashboardError(errorMessage);
      console.error('Command error:', error);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const workerCount = workers?.length || 0;
  const govScore = telemetry?.chain_valid ? DASHBOARD_CONFIG.PERFECT_SCE_SCORE : DASHBOARD_CONFIG.INITIAL_SCE_SCORE;
  const comfyuiStatus = comfyui?.connected ? 'online' : 'offline';
  const displayError = dashboardError || storeError;
  const hasError = !!displayError;
  
  const messages = (storeMessages || []).map(msg => ({
    ...msg,
    timestamp: new Date(msg.timestamp).toLocaleTimeString()
  }));

  const navItems = [
    { name: 'Protocol', href: '#protocol', icon: Shield, description: 'SCE Constitutional Enforcement' },
    { name: 'Workers', href: '#workers', icon: Users, description: `${workerCount} Specialized Agents` },
    { name: 'ComfyUI', href: '#comfyui', icon: Palette, description: 'AI Image & Video Studio', badge: 'NEW' },
    { name: 'Audit', href: '#audit', icon: Shield, description: 'Drift Chain Audit Trail' },
    { name: 'Docs', href: '#docs', icon: BookOpen, description: 'Whitepaper & Documentation' },
  ];

  if (!mounted) return null;

  return (
    <div className="min-h-screen bg-[#0a0a0c] text-white">
      {/* Error Banner */}
      {hasError && (
        <div 
          className="fixed top-0 left-0 right-0 z-50 bg-red-500/20 border-b border-red-500/50 px-6 py-3 flex items-center justify-between animate-in slide-in-from-top"
          role="alert"
          aria-live="assertive"
        >
          <span className="text-sm text-red-300 flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-red-500 animate-pulse" />
            {displayError}
          </span>
          <button
            onClick={() => setDashboardError(null)}
            className="text-red-300 hover:text-red-200 transition text-xs"
            aria-label="Close error message"
          >
            Dismiss
          </button>
        </div>
      )}

      {/* Animated Grid Background */}
      <div className="fixed inset-0 pointer-events-none opacity-20">
        <div className="absolute inset-0 bg-[radial-gradient(circle_at_50%_50%,_#7dcfff_0%,_transparent_50%)] opacity-5" />
        <div 
          className="absolute inset-0" 
          style={{ 
            backgroundImage: 'linear-gradient(to right, #7dcfff0a 1px, transparent 1px), linear-gradient(to bottom, #7dcfff0a 1px, transparent 1px)', 
            backgroundSize: '40px 40px' 
          }} 
        />
      </div>

      {/* Glass Header */}
      <header 
        className="relative z-10 flex items-center justify-between px-6 py-3 border-b border-[#7dcfff]/10 bg-black/40 backdrop-blur-xl"
        role="banner"
      >
        <div className="flex items-center gap-8 text-[10px] font-mono">
          <div className="flex items-center gap-2" title={connected ? 'Kernel connected' : 'Kernel offline'}>
            <div className={`w-2 h-2 rounded-full ${connected ? 'bg-[#9ece6a] animate-pulse' : 'bg-[#f7768e]'}`} 
              aria-hidden="true"
            />
            <span className={connected ? 'text-[#9ece6a]' : 'text-[#f7768e]'}>
              KERNEL: {connected ? 'ACTIVE' : 'OFFLINE'}
            </span>
          </div>
          <div className="flex items-center gap-2">
            <Shield className="w-3 h-3 text-[#9B72CB]" aria-hidden="true" />
            <span>SCE: <span className="text-[#7dcfff]">ENFORCED</span></span>
          </div>
          <span className="text-[#565f89]">{time} UTC</span>
          {isLoading && (
            <span className="flex items-center gap-1 text-[#7dcfff]">
              <span className="w-1 h-1 rounded-full bg-[#7dcfff] animate-pulse" />
              Loading...
            </span>
          )}
        </div>
        
        {/* Center Navigation */}
        <div className="flex items-center gap-2 bg-white/[0.02] rounded-full p-1 border border-white/[0.05]">
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = activeHash === item.href;
            return (
              <motion.a
                key={item.name}
                href={item.href}
                onClick={(e) => scrollToSection(e, item.href)}
                className={`relative px-4 py-1.5 rounded-full text-xs font-mono transition-all cursor-pointer flex items-center gap-2 ${
                  isActive ? 'text-[#9ece6a]' : 'text-[#565f89] hover:text-[#c0caf5]'
                }`}
                whileHover={{ scale: 1.02 }}
                whileTap={{ scale: 0.98 }}
                title={item.description}
              >
                <Icon className="w-3.5 h-3.5" />
                {item.name}
                {item.badge && (
                  <span className="absolute -top-1 -right-2 text-[8px] bg-[#7dcfff]/20 text-[#7dcfff] px-1 rounded-full">
                    {item.badge}
                  </span>
                )}
                {isActive && (
                  <motion.div
                    layoutId="activeNav"
                    className="absolute inset-0 bg-[#9ece6a]/10 rounded-full border border-[#9ece6a]/30"
                    transition={{ type: "spring", bounce: 0.2, duration: 0.6 }}
                  />
                )}
              </motion.a>
            );
          })}
        </div>
        
        <div className="flex items-center gap-4">
          <Link href="/trading">
            <button className="px-3 py-1 rounded-lg bg-[#7dcfff]/10 border border-[#7dcfff]/20 text-[10px] text-[#7dcfff] hover:bg-[#7dcfff]/20 transition flex items-center gap-1">
              <TrendingUp className="w-3 h-3" />
              Trade
            </button>
          </Link>
          <button
            onClick={() => setShowSidebar(!showSidebar)}
            className="p-1.5 rounded-lg bg-white/5 hover:bg-white/10 transition"
          >
            {showSidebar ? <PanelLeftClose className="w-4 h-4" /> : <PanelLeftOpen className="w-4 h-4" />}
          </button>
          <div className="text-right">
            <div className="text-[8px] text-[#565f89] uppercase tracking-wider">Workers</div>
            <div className="text-xs font-bold text-white">{workerCount}</div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <div className="relative z-10 h-[calc(100vh-60px)] overflow-y-auto custom-scrollbar">
        
        {/* Dashboard View */}
        {viewMode === 'dashboard' && (
          <div className="flex p-4 gap-4 min-h-[600px]">
            
            {/* LEFT SIDEBAR */}
            {showSidebar && (
              <aside className="w-80 bg-black/30 backdrop-blur-xl border border-[#7dcfff]/10 rounded-2xl p-5 flex flex-col gap-5 sticky top-4 h-[calc(100vh-100px)] shrink-0 overflow-y-auto custom-scrollbar">
                <div>
                  <h3 className="text-[10px] text-[#565f89] mb-4 flex items-center gap-2 font-mono uppercase tracking-wider">
                    <Activity className="w-3 h-3 text-[#7dcfff]" /> SYSTEM STATUS
                  </h3>
                  <div className="space-y-3">
                    <div className="flex justify-between items-center p-3 bg-white/5 rounded-xl">
                      <span className="text-xs">Worker Pool</span>
                      <span className="text-xs font-mono text-white">{workerCount} / {DASHBOARD_CONFIG.MAX_WORKERS}</span>
                    </div>
                    <div className="flex justify-between items-center p-3 bg-white/5 rounded-xl">
                      <span className="text-xs">Portfolio</span>
                      <span className="text-xs font-mono text-[#9ece6a]">₱{portfolio?.balance?.toLocaleString() || '1,000,000'}</span>
                    </div>
                    <div className="flex justify-between items-center p-3 bg-white/5 rounded-xl">
                      <span className="text-xs">SCE Integrity</span>
                      <span className="text-xs font-mono text-[#9ece6a]">{govScore}%</span>
                    </div>
                    <div className="flex justify-between items-center p-3 bg-gradient-to-r from-[#7dcfff]/10 to-[#9B72CB]/10 rounded-xl">
                      <span className="text-xs flex items-center gap-1"><Image className="w-3 h-3" /> ComfyUI</span>
                      <span className={`text-xs font-mono ${comfyuiStatus === 'online' ? 'text-[#9ece6a]' : 'text-[#f7768e]'}`}>
                        {comfyuiStatus === 'online' ? 'ACTIVE' : 'OFFLINE'}
                      </span>
                    </div>
                    {killSwitch?.active && (
                      <div className="flex justify-between items-center p-3 bg-red-500/20 rounded-xl">
                        <span className="text-xs flex items-center gap-1"><Lock className="w-3 h-3" /> Kill Switch</span>
                        <span className="text-xs font-mono text-red-400">ACTIVE</span>
                      </div>
                    )}
                  </div>
                </div>

                <div>
                  <h3 className="text-[10px] text-[#565f89] mb-3 flex items-center gap-2 font-mono uppercase tracking-wider">
                    <Shield className="w-3 h-3 text-[#9B72CB]" /> CONSTITUTION
                  </h3>
                  <div className="space-y-2">
                    {['Data Sovereignty', 'Creative Freedom', 'No Hidden Training', 'Transparency', 'Objectivity'].map((principle, i) => (
                      <div key={i} className="flex items-center gap-2 text-[10px] text-[#c0caf5] p-2 bg-white/5 rounded-lg">
                        <CheckCircle2 className="w-3 h-3 text-[#9ece6a]" />
                        <span className="truncate">{principle}</span>
                      </div>
                    ))}
                  </div>
                </div>

                <div className="mt-auto pt-4 border-t border-[#7dcfff]/10">
                  <div className="flex items-center gap-2 text-[9px] text-[#565f89]">
                    <div className="w-1.5 h-1.5 rounded-full bg-[#9ece6a] animate-pulse" />
                    <span>Constitutional AI • Active</span>
                  </div>
                </div>
              </aside>
            )}

            {/* CENTER: Chat/Gallery */}
            <main className="flex-1 flex flex-col bg-black/30 backdrop-blur-xl border border-[#7dcfff]/10 rounded-2xl overflow-hidden">
              <div className="p-4 border-b border-[#7dcfff]/10 bg-gradient-to-r from-[#9B72CB]/10 to-transparent">
                <div className="flex items-center gap-4">
                  <button
                    onClick={() => setActiveTab('chat')}
                    className={`flex items-center gap-2 px-3 py-1.5 rounded-lg text-sm transition-all ${
                      activeTab === 'chat' ? 'bg-[#7dcfff]/20 text-[#7dcfff]' : 'text-[#565f89] hover:text-white'
                    }`}
                  >
                    <Sparkles className="w-4 h-4" />
                    Sovereign Chat
                  </button>
                  <button
                    onClick={() => setActiveTab('gallery')}
                    className={`flex items-center gap-2 px-3 py-1.5 rounded-lg text-sm transition-all ${
                      activeTab === 'gallery' ? 'bg-[#7dcfff]/20 text-[#7dcfff]' : 'text-[#565f89] hover:text-white'
                    }`}
                  >
                    <GalleryVertical className="w-4 h-4" />
                    Gallery ({generatedImages.length})
                  </button>
                  <button
                    onClick={clearMessages}
                    className="ml-auto text-xs text-[#565f89] hover:text-white transition"
                  >
                    Clear Chat
                  </button>
                </div>
              </div>

              {activeTab === 'chat' ? (
                <>
                  <div className="flex-1 overflow-y-auto p-6 space-y-4 custom-scrollbar">
                    {messages.length === 0 ? (
                      <div className="h-full flex flex-col items-center justify-center text-center">
                        <div className="w-20 h-20 rounded-full border-2 border-[#7dcfff]/20 flex items-center justify-center mb-4">
                          <Flame className="w-8 h-8 text-[#7dcfff]" />
                        </div>
                        <h3 className="text-lg font-bold bg-gradient-to-r from-[#c0caf5] to-[#7dcfff] bg-clip-text text-transparent">
                          Sovereign AI Terminal
                        </h3>
                        <p className="text-xs text-[#565f89] mt-2 max-w-md">
                          Execute commands, generate images, or ask questions.
                        </p>
                        <div className="flex gap-2 mt-6">
                          <button 
                            onClick={() => setPrompt('/generate cyberpunk cat')} 
                            className="px-3 py-1.5 bg-[#7dcfff]/10 rounded-lg text-xs text-[#7dcfff] hover:bg-[#7dcfff]/20 transition flex items-center gap-1"
                          >
                            <Image className="w-3 h-3" /> Generate Image
                          </button>
                          <button 
                            onClick={() => setPrompt('/video cat running')} 
                            className="px-3 py-1.5 bg-[#9B72CB]/10 rounded-lg text-xs text-[#9B72CB] hover:bg-[#9B72CB]/20 transition flex items-center gap-1"
                          >
                            <Video className="w-3 h-3" /> Generate Video
                          </button>
                          <button 
                            onClick={() => setPrompt('/code moving average strategy')} 
                            className="px-3 py-1.5 bg-[#9ece6a]/10 rounded-lg text-xs text-[#9ece6a] hover:bg-[#9ece6a]/20 transition flex items-center gap-1"
                          >
                            <Code className="w-3 h-3" /> Trading Bot
                          </button>
                        </div>
                      </div>
                    ) : (
                      messages.map((msg) => (
                        <div key={msg.id} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                          <div className={`max-w-[85%] ${
                            msg.role === 'user' 
                              ? 'bg-gradient-to-r from-[#7dcfff]/20 to-[#9B72CB]/20 border border-[#7dcfff]/30 rounded-br-sm' 
                              : ''
                          }`}>
                            {msg.role === 'assistant' || msg.role === 'system' ? (
                              <SovereignMessage
                                content={msg.content}
                                role={msg.role}
                                isStreaming={msg.isStreaming}
                                driftLock={msg.drift_lock}
                                timestamp={msg.timestamp}
                              />
                            ) : (
                              <div className="p-4 rounded-2xl bg-white/5 border border-white/10 rounded-bl-sm">
                                <p className="text-sm leading-relaxed whitespace-pre-wrap text-[#c0caf5]">{msg.content}</p>
                                <div className="flex items-center gap-2 mt-2">
                                  <span className="text-[8px] text-[#565f89]">{msg.timestamp}</span>
                                </div>
                              </div>
                            )}
                          </div>
                        </div>
                      ))
                    )}
                    <div ref={chatEndRef} />
                  </div>

                  <div className="p-4 border-t border-[#7dcfff]/10 bg-black/20">
                    <div className="flex gap-2">
                      <textarea
                        value={prompt}
                        onChange={(e) => setPrompt(e.target.value)}
                        onKeyDown={handleKeyDown}
                        placeholder={connected ? "Execute command, ask a question, or /generate..." : "Awaiting kernel connection..."}
                        className="flex-1 bg-black/50 border border-[#7dcfff]/20 rounded-xl px-4 py-3 text-sm text-[#c0caf5] placeholder:text-[#565f89] outline-none resize-none focus:border-[#7dcfff]/50 transition-all"
                        rows={1}
                        disabled={!connected || isLoading}
                        aria-label="Command or message input"
                        aria-describedby="input-help"
                      />
                      <button
                        onClick={handleSend}
                        disabled={!prompt.trim() || isStreaming || !connected || isLoading}
                        className="px-6 py-3 rounded-xl bg-gradient-to-r from-[#7dcfff]/20 to-[#9B72CB]/20 border border-[#7dcfff]/30 text-[#7dcfff] hover:shadow-lg transition-all disabled:opacity-50 disabled:cursor-not-allowed"
                        title={isLoading ? 'Loading...' : isStreaming ? 'Streaming response...' : 'Send message'}
                        aria-label="Send message"
                      >
                        {isLoading || isStreaming ? (
                          <div className="w-4 h-4 border-2 border-[#7dcfff]/30 border-t-[#7dcfff] rounded-full animate-spin" />
                        ) : (
                          <Send className="w-4 h-4" />
                        )}
                      </button>
                    </div>
                    <div className="flex justify-between mt-3 text-[8px] text-[#565f89] font-mono" id="input-help">
                      <div className="flex gap-3">
                        <span>ENTER • Send</span>
                        <span>SHIFT+ENTER • New line</span>
                        <span className="text-[#7dcfff]">🎨 /generate prompt</span>
                      </div>
                      <div className="flex gap-2">
                        {['/health', '/workers', '/generate', '/code'].map(cmd => (
                          <button 
                            key={cmd} 
                            onClick={() => setPrompt(cmd)} 
                            className="hover:text-[#7dcfff] transition-colors"
                            aria-label={`Insert ${cmd} command`}
                          >
                            {cmd}
                          </button>
                        ))}
                      </div>
                    </div>
                  </div>
                </>
              ) : (
                <div className="flex-1 overflow-y-auto p-6 custom-scrollbar">
                  {generatedImages.length === 0 ? (
                    <div className="h-full flex flex-col items-center justify-center text-center">
                      <Image className="w-16 h-16 text-[#565f89] mb-4" aria-hidden="true" />
                      <h3 className="text-lg font-bold text-white">No Images Yet</h3>
                      <p className="text-xs text-[#565f89] mt-2">
                        Generate with <code className="text-[#7dcfff]">/generate prompt</code>
                      </p>
                    </div>
                  ) : (
                    <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
                      {generatedImages.map((img) => (
                        <div 
                          key={img.id} 
                          className="bg-black/40 rounded-xl overflow-hidden border border-[#7dcfff]/10 group hover:border-[#7dcfff]/30 transition"
                          role="listitem"
                        >
                          <div className="relative overflow-hidden bg-black/60 aspect-square">
                            <img 
                              src={img.url} 
                              alt={img.prompt} 
                              className="w-full h-full object-cover group-hover:scale-105 transition-transform" 
                              loading="lazy"
                            />
                            <button
                              onClick={() => {
                                const link = document.createElement('a');
                                link.href = img.url;
                                link.download = `phoenix-${img.id}.png`;
                                link.click();
                              }}
                              className="absolute top-2 right-2 p-2 bg-black/70 rounded-lg opacity-0 group-hover:opacity-100 transition-opacity"
                              title="Download image"
                              aria-label="Download image"
                            >
                              <Send className="w-3 h-3 text-[#7dcfff]" />
                            </button>
                          </div>
                          <div className="p-3">
                            <p className="text-xs text-[#c0caf5] truncate" title={img.prompt}>{img.prompt}</p>
                            <p className="text-[8px] text-[#565f89] mt-1">{img.timestamp}</p>
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              )}
            </main>

            {/* RIGHT: Command Lexicon */}
            {showSidebar && (
              <aside className="w-80 bg-black/30 backdrop-blur-xl border border-[#7dcfff]/10 rounded-2xl p-5 flex flex-col gap-4 sticky top-4 h-[calc(100vh-100px)] shrink-0 overflow-y-auto custom-scrollbar">
                <div className="flex items-center justify-between">
                  <h3 className="text-[10px] text-[#565f89] flex items-center gap-2 font-mono uppercase tracking-wider">
                    <BookOpen className="w-3 h-3 text-[#7dcfff]" /> COMMAND LEXICON
                  </h3>
                </div>
                
                <div className="relative">
                  <Search className="w-3 h-3 absolute left-3 top-2.5 text-[#565f89]" />
                  <input
                    type="text"
                    placeholder="Search commands..."
                    value={searchTerm}
                    onChange={(e) => setSearchTerm(e.target.value)}
                    className="w-full bg-black/50 border border-[#7dcfff]/20 rounded-xl py-2 pl-8 pr-3 text-xs text-white placeholder:text-[#565f89] outline-none focus:border-[#7dcfff]/50"
                  />
                </div>

                <div className="flex-1 overflow-y-auto space-y-2 custom-scrollbar">
                  {Object.entries(COMMAND_GROUPS).map(([group, commands]) => {
                    const filtered = commands.filter(cmd => 
                      cmd.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
                      cmd.desc.toLowerCase().includes(searchTerm.toLowerCase())
                    );
                    if (filtered.length === 0) return null;
                    
                    const isExpanded = expandedGroup === group;
                    return (
                      <div key={group} className="border border-white/10 rounded-lg overflow-hidden">
                        <button
                          onClick={() => setExpandedGroup(isExpanded ? null : group)}
                          className="w-full flex items-center justify-between p-2.5 bg-black/20 hover:bg-white/5 transition-colors"
                        >
                          <span className="text-[9px] font-mono font-bold tracking-widest text-[#9B72CB] uppercase">
                            {group} <span className="text-[#64748B]">({filtered.length})</span>
                          </span>
                          <ChevronRight className={`w-3 h-3 text-[#64748B] transition-transform ${isExpanded ? 'rotate-90' : ''}`} />
                        </button>
                        {isExpanded && (
                          <div className="p-2 space-y-2 border-t border-white/5 bg-black/20">
                            {filtered.map((cmd, i) => (
                              <CommandCard key={i} name={cmd.name} description={cmd.desc} example={cmd.example} />
                            ))}
                          </div>
                        )}
                      </div>
                    );
                  })}
                </div>

                <div className="pt-4 border-t border-[#7dcfff]/10">
                  <div className="bg-gradient-to-r from-[#7dcfff]/5 to-[#9B72CB]/5 rounded-xl p-3">
                    <div className="flex items-center gap-2 mb-2">
                      <Shield className="w-3 h-3 text-[#9B72CB]" />
                      <span className="text-[8px] font-mono text-[#7dcfff] uppercase tracking-wider">Constitutional AI</span>
                    </div>
                    <p className="text-[9px] text-[#565f89] leading-relaxed">
                      All commands filtered through SCE Protocol. Images and videos generated via ComfyUI with constitutional oversight.
                    </p>
                  </div>
                </div>
              </aside>
            )}
          </div>
        )}

        {/* Sections for navigation */}
        

        

        

        <div className="h-20" />
      </div>

      {/* Mode Toggle Button */}
      <button
        onClick={() => setViewMode(viewMode === 'dashboard' ? 'terminal' : 'dashboard')}
        className="fixed bottom-6 right-6 z-50 p-3 rounded-full bg-[#0a0a0c] border border-[#7dcfff]/30 text-[#7dcfff] hover:bg-[#7dcfff]/10 transition-all shadow-lg hover:shadow-[0_0_20px_rgba(125,207,255,0.3)]"
        title={`Switch to ${viewMode === 'dashboard' ? 'terminal' : 'dashboard'} view`}
        aria-label={`Switch to ${viewMode === 'dashboard' ? 'terminal' : 'dashboard'} view`}
      >
        {viewMode === 'dashboard' ? <Terminal className="w-5 h-5" /> : <Grid3x3 className="w-5 h-5" />}
      </button>

      <style jsx global>{`
        .custom-scrollbar::-webkit-scrollbar { width: 4px; }
        .custom-scrollbar::-webkit-scrollbar-track { background: rgba(125,207,255,0.05); border-radius: 10px; }
        .custom-scrollbar::-webkit-scrollbar-thumb { background: rgba(125,207,255,0.3); border-radius: 10px; }
        .custom-scrollbar::-webkit-scrollbar-thumb:hover { background: rgba(125,207,255,0.5); }
        textarea::-webkit-scrollbar { display: none; }
        @media (prefers-reduced-motion: reduce) {
          * {
            animation-duration: 0.01ms !important;
            animation-iteration-count: 1 !important;
            transition-duration: 0.01ms !important;
          }
        }
      `}</style>
    </div>
  );
}