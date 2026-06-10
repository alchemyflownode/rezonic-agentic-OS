'use client';

import React, { useState, useEffect, useRef, useCallback, useMemo } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Zap, Shield, Sparkles, Send, Activity,
  Lock, PanelLeftClose, PanelLeftOpen,
  CheckCircle2, Terminal, User, Bot, BookOpen, Search,
  GalleryVertical, Flame, Code, Image, Video,
  TrendingUp, Grid3x3, ChevronRight, Users, Palette, Download,
  GitBranch
} from 'lucide-react';
import Link from 'next/link';
import { SovereignMessage } from '@/components/SovereignMessage';
import { usePhoenix, useAutoRefresh } from '@/hooks/usePhoenix';

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

type GeneratedImage = { id: string; prompt: string; url: string; timestamp: string; isLoading?: boolean };
type ViewMode = 'dashboard' | 'terminal';
type Tab = 'chat' | 'gallery';

interface ChatMessage {
  id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  timestamp: string;
  driftLock?: string;
  isStreaming?: boolean;
}

const CommandCard = ({ name, description, example }: { name: string; description: string; example: string }) => (
  <div className="p-2 rounded-lg hover:bg-white/5 transition-colors">
    <div className="text-[9px] font-mono text-[#7dcfff]">{name}</div>
    <div className="text-[8px] text-[#565f89]">{description}</div>
    <div className="text-[7px] text-[#9B72CB] mt-1">`ex: {example}`</div>
  </div>
);

// ✅ FIX: Unique ID generator for React keys
const generateUniqueId = () => `${Date.now()}-${Math.random().toString(36).substr(2, 8)}-${performance.now()}`;

export default function SovereignDashboard() {
  const store = usePhoenix();
  const { 
    connected = false, 
    workers = [], 
    telemetry = { chain_valid: false, kernel_load: 0, workers: 0, memory: 0, gpu: { has_gpu: false } },
    error: storeError,
    killSwitch = { active: false },
    comfyui = { connected: false },
    portfolio = { balance: 1000000 },
    generateImage,
    generateVideo,
    connect,
  } = store;
  
  useAutoRefresh(DASHBOARD_CONFIG.AUTO_REFRESH_INTERVAL);
  
  // Local chat state
  const [chatMessages, setChatMessages] = useState<ChatMessage[]>([]);
  const [prompt, setPrompt] = useState('');
  const [isChatLoading, setIsChatLoading] = useState(false);
  const [mounted, setMounted] = useState(false);
  const [time, setTime] = useState('');
  const [activeHash, setActiveHash] = useState('');
  const [activeTab, setActiveTab] = useState<Tab>('chat');
  const [showSidebar, setShowSidebar] = useState(true);
  const [viewMode, setViewMode] = useState<ViewMode>('dashboard');
  const [generatedImages, setGeneratedImages] = useState<GeneratedImage[]>([]);
  const [searchTerm, setSearchTerm] = useState('');
  const [expandedGroup, setExpandedGroup] = useState<string | null>('🦊 SOVEREIGN OS');
  const [dashboardError, setDashboardError] = useState<string | null>(null);
  
  const chatEndRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  
  // Auto-scroll chat
  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [chatMessages]);
  
  // Clock Effect
  useEffect(() => {
    const clock = setInterval(() => {
      setTime(new Date().toLocaleTimeString('en-US', { hour12: false, hour: '2-digit', minute: '2-digit', second: '2-digit' }));
    }, 1000);
    return () => clearInterval(clock);
  }, []);
  
  // Mount
  useEffect(() => {
    setMounted(true);
    if (typeof window !== 'undefined') {
      setActiveHash(window.location.hash);
      const handleResize = () => {
        if (window.innerWidth < 1024) setShowSidebar(false);
      };
      handleResize();
      window.addEventListener('resize', handleResize);
      return () => window.removeEventListener('resize', handleResize);
    }
  }, []);
  
  // Auto-connect
  const stableConnect = useCallback(() => {
    if (!connected && connect) {
      console.log('🔌 Connecting to Phoenix Kernel...');
      connect().catch((err: Error) => setDashboardError(err.message));
    }
  }, [connect, connected]);
  
  useEffect(() => {
    stableConnect();
  }, [stableConnect]);
  
  // Auto-clear error
  useEffect(() => {
    if (dashboardError) {
      const timer = setTimeout(() => setDashboardError(null), 5000);
      return () => clearTimeout(timer);
    }
  }, [dashboardError]);
  
  // Handle hash change
  useEffect(() => {
    if (typeof window === 'undefined') return;
    const handleHashChange = () => setActiveHash(window.location.hash);
    window.addEventListener('hashchange', handleHashChange);
    return () => window.removeEventListener('hashchange', handleHashChange);
  }, []);
  
  const scrollToSection = (e: React.MouseEvent, hash: string) => {
    e.preventDefault();
    if (typeof window === 'undefined') return;
    const element = document.querySelector(hash);
    if (element) {
      element.scrollIntoView({ behavior: 'smooth' });
      window.history.pushState(null, '', hash);
      setActiveHash(hash);
    }
  };
  
  const handleSend = async () => {
    if (!prompt.trim() || isChatLoading) return;
    const userText = prompt.trim();
    setPrompt('');
    setIsChatLoading(true);
    
    // ✅ FIX: Use generateUniqueId() instead of Date.now()
    setChatMessages(prev => [...prev, {
      id: generateUniqueId(),
      role: 'user',
      content: userText,
      timestamp: new Date().toLocaleTimeString()
    }]);
    
    const assistantId = generateUniqueId();
    setChatMessages(prev => [...prev, {
      id: assistantId,
      role: 'assistant',
      content: '⏳ Processing...',
      timestamp: new Date().toLocaleTimeString()
    }]);
    
    try {
      const response = await fetch('http://localhost:8002/kernel/stream', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ task: userText })
      });
      
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      
      const reader = response.body?.getReader();
      const decoder = new TextDecoder();
      let fullContent = '';
      
      while (reader) {
        const { done, value } = await reader.read();
        if (done) break;
        const chunk = decoder.decode(value);
        const lines = chunk.split('\n');
        
        for (const line of lines) {
          if (line.startsWith('data: ')) {
            try {
              const data = JSON.parse(line.substring(6));
              if (data.type === 'reflex') {
                fullContent = data.content;
                setChatMessages(prev => prev.map(msg =>
                  msg.id === assistantId ? { ...msg, content: fullContent, driftLock: data.drift_lock } : msg
                ));
              } else if (data.type === 'token') {
                fullContent += data.content;
                setChatMessages(prev => prev.map(msg =>
                  msg.id === assistantId ? { ...msg, content: fullContent } : msg
                ));
              }
            } catch (e) {}
          }
        }
      }
      
      if (!fullContent) {
        setChatMessages(prev => prev.map(msg =>
          msg.id === assistantId ? { ...msg, content: '⚠️ No response from kernel', role: 'system' } : msg
        ));
      }
    } catch (error) {
      const errorMsg = error instanceof Error ? error.message : 'Connection failed';
      setDashboardError(errorMsg);
      setChatMessages(prev => prev.map(msg =>
        msg.id === assistantId ? { ...msg, content: `❌ Error: ${errorMsg}`, role: 'system' } : msg
      ));
    } finally {
      setIsChatLoading(false);
    }
  };
  
  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };
  
  const handleTextareaAutoResize = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setPrompt(e.target.value);
    const el = e.target;
    el.style.height = 'auto';
    el.style.height = `${Math.min(el.scrollHeight, 120)}px`;
  };
  
  const handleClearMessages = () => {
    setChatMessages([]);
  };
  
  const handleDownloadImage = (url: string, prompt: string) => {
    const link = document.createElement('a');
    link.href = url;
    link.download = `phoenix-${Date.now()}.png`;
    link.click();
  };
  
  // ✅ FIX: When adding images, use generateUniqueId()
  const addImage = (prompt: string, url: string) => {
    setGeneratedImages(prev => [{
      id: generateUniqueId(),
      prompt,
      url,
      timestamp: new Date().toLocaleTimeString(),
      isLoading: false
    }, ...prev.slice(0, DASHBOARD_CONFIG.MAX_IMAGES - 1)]);
  };
  
  const workerCount = workers?.length || 0;
  const govScore = telemetry?.chain_valid ? DASHBOARD_CONFIG.PERFECT_SCE_SCORE : DASHBOARD_CONFIG.INITIAL_SCE_SCORE;
  const comfyuiStatus = comfyui?.connected ? 'online' : 'offline';
  const displayError = dashboardError || storeError;
  const hasError = !!displayError;
  
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
      <AnimatePresence>
        {hasError && (
          <motion.div 
            initial={{ opacity: 0, y: -20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -20 }}
            className="fixed top-0 left-0 right-0 z-50 bg-red-500/20 border-b border-red-500/50 px-6 py-3 flex items-center justify-between"
            role="alert"
          >
            <span className="text-sm text-red-300 flex items-center gap-2">
              <span className="w-2 h-2 rounded-full bg-red-500 animate-pulse" />
              {displayError}
            </span>
            <button onClick={() => setDashboardError(null)} className="text-red-300 hover:text-red-200 transition text-xs">
              Dismiss
            </button>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Background Grid */}
      <div className="fixed inset-0 pointer-events-none opacity-20">
        <div className="absolute inset-0 bg-[radial-gradient(circle_at_50%_50%,_#7dcfff_0%,_transparent_50%)] opacity-5" />
        <div className="absolute inset-0" style={{ backgroundImage: 'linear-gradient(to right, #7dcfff0a 1px, transparent 1px), linear-gradient(to bottom, #7dcfff0a 1px, transparent 1px)', backgroundSize: '40px 40px' }} />
      </div>

      {/* Header */}
      <header className="relative z-10 flex items-center justify-between px-6 py-3 border-b border-[#7dcfff]/10 bg-black/40 backdrop-blur-xl">
        <div className="flex items-center gap-8 text-[10px] font-mono">
          <div className="flex items-center gap-2">
            <div className={`w-2 h-2 rounded-full ${connected ? 'bg-[#9ece6a] animate-pulse' : 'bg-[#f7768e]'}`} />
            <span className={connected ? 'text-[#9ece6a]' : 'text-[#f7768e]'}>KERNEL: {connected ? 'ACTIVE' : 'OFFLINE'}</span>
          </div>
          <div className="flex items-center gap-2">
            <Shield className="w-3 h-3 text-[#9B72CB]" />
            <span>SCE: <span className="text-[#7dcfff]">ENFORCED</span></span>
          </div>
          <span className="text-[#565f89]">{time} UTC</span>
        </div>
        
        <div className="flex items-center gap-2 bg-white/[0.02] rounded-full p-1 border border-white/[0.05]">
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = activeHash === item.href;
            return (
              <motion.a
                key={item.name}
                href={item.href}
                onClick={(e) => scrollToSection(e, item.href)}
                className={`relative px-4 py-1.5 rounded-full text-xs font-mono transition-all cursor-pointer flex items-center gap-2 ${isActive ? 'text-[#9ece6a]' : 'text-[#565f89] hover:text-[#c0caf5]'}`}
                whileHover={{ scale: 1.02 }}
                whileTap={{ scale: 0.98 }}
                title={item.description}
              >
                <Icon className="w-3.5 h-3.5" />
                {item.name}
                {item.badge && <span className="absolute -top-1 -right-2 text-[8px] bg-[#7dcfff]/20 text-[#7dcfff] px-1 rounded-full">{item.badge}</span>}
                {isActive && <motion.div layoutId="activeNav" className="absolute inset-0 bg-[#9ece6a]/10 rounded-full border border-[#9ece6a]/30" transition={{ type: "spring", bounce: 0.2, duration: 0.6 }} />}
              </motion.a>
            );
          })}
        </div>
        
        <div className="flex items-center gap-4">
          <Link href="/trading">
            <button className="px-3 py-1 rounded-lg bg-[#7dcfff]/10 border border-[#7dcfff]/20 text-[10px] text-[#7dcfff] hover:bg-[#7dcfff]/20 transition flex items-center gap-1">
              <TrendingUp className="w-3 h-3" /> Trade
            </button>
          </Link>
          <button onClick={() => setShowSidebar(!showSidebar)} className="p-1.5 rounded-lg bg-white/5 hover:bg-white/10 transition">
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
        {viewMode === 'dashboard' && (
          <div className="flex p-4 gap-4 min-h-[600px] flex-wrap lg:flex-nowrap">
            
            {/* LEFT SIDEBAR */}
            {showSidebar && (
              <aside className="hidden lg:flex w-80 bg-black/30 backdrop-blur-xl border border-[#7dcfff]/10 rounded-2xl p-5 flex-col gap-5 sticky top-4 h-[calc(100vh-100px)] shrink-0 overflow-y-auto custom-scrollbar">
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

            {/* CENTER: Chat */}
            <main className="flex-1 flex flex-col bg-black/30 backdrop-blur-xl border border-[#7dcfff]/10 rounded-2xl overflow-hidden">
              <div className="p-4 border-b border-[#7dcfff]/10 bg-gradient-to-r from-[#9B72CB]/10 to-transparent">
                <div className="flex items-center gap-4">
                  <button
                    onClick={() => setActiveTab('chat')}
                    className={`flex items-center gap-2 px-3 py-1.5 rounded-lg text-sm transition-all ${activeTab === 'chat' ? 'bg-[#7dcfff]/20 text-[#7dcfff]' : 'text-[#565f89] hover:text-white'}`}
                  >
                    <Sparkles className="w-4 h-4" /> Sovereign Chat
                  </button>
                  <button
                    onClick={() => setActiveTab('gallery')}
                    className={`flex items-center gap-2 px-3 py-1.5 rounded-lg text-sm transition-all ${activeTab === 'gallery' ? 'bg-[#7dcfff]/20 text-[#7dcfff]' : 'text-[#565f89] hover:text-white'}`}
                  >
                    <GalleryVertical className="w-4 h-4" /> Gallery ({generatedImages.length})
                  </button>
                  <button onClick={handleClearMessages} className="ml-auto text-xs text-[#565f89] hover:text-white transition">
                    Clear Chat
                  </button>
                </div>
              </div>

              {activeTab === 'chat' ? (
                <>
                  <div className="flex-1 overflow-y-auto p-6 space-y-4 custom-scrollbar">
                    {chatMessages.length === 0 ? (
                      <div className="h-full flex flex-col items-center justify-center text-center">
                        <div className="w-20 h-20 rounded-full border-2 border-[#7dcfff]/20 flex items-center justify-center mb-4">
                          <Flame className="w-8 h-8 text-[#7dcfff]" />
                        </div>
                        <h3 className="text-lg font-bold bg-gradient-to-r from-[#c0caf5] to-[#7dcfff] bg-clip-text text-transparent">
                          Sovereign AI Terminal
                        </h3>
                        <p className="text-xs text-[#565f89] mt-2 max-w-md">Execute commands, generate images, or ask questions.</p>
                        <div className="flex gap-2 mt-6 flex-wrap justify-center">
                          <button onClick={() => setPrompt('/generate cyberpunk cat')} className="px-3 py-1.5 bg-[#7dcfff]/10 rounded-lg text-xs text-[#7dcfff] hover:bg-[#7dcfff]/20 transition flex items-center gap-1">
                            <Image className="w-3 h-3" /> Generate Image
                          </button>
                          <button onClick={() => setPrompt('/video cat running')} className="px-3 py-1.5 bg-[#9B72CB]/10 rounded-lg text-xs text-[#9B72CB] hover:bg-[#9B72CB]/20 transition flex items-center gap-1">
                            <Video className="w-3 h-3" /> Generate Video
                          </button>
                          <button onClick={() => setPrompt('/code moving average strategy')} className="px-3 py-1.5 bg-[#9ece6a]/10 rounded-lg text-xs text-[#9ece6a] hover:bg-[#9ece6a]/20 transition flex items-center gap-1">
                            <Code className="w-3 h-3" /> Trading Bot
                          </button>
                        </div>
                      </div>
                    ) : (
                      chatMessages.map((msg) => (
                        <div key={msg.id} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                          <div className={`max-w-[85%] ${msg.role === 'user' ? 'bg-gradient-to-r from-[#7dcfff]/20 to-[#9B72CB]/20 border border-[#7dcfff]/30 rounded-br-sm' : ''}`}>
                            {msg.role === 'assistant' || msg.role === 'system' ? (
                              <SovereignMessage content={msg.content} role={msg.role} driftLock={msg.driftLock} timestamp={msg.timestamp} />
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
                        ref={textareaRef}
                        value={prompt}
                        onChange={handleTextareaAutoResize}
                        onKeyDown={handleKeyDown}
                        placeholder={connected ? "Execute command, ask a question, or /generate..." : "Awaiting kernel connection..."}
                        className="flex-1 bg-black/50 border border-[#7dcfff]/20 rounded-xl px-4 py-3 text-sm text-[#c0caf5] placeholder:text-[#565f89] outline-none resize-none focus:border-[#7dcfff]/50 transition-all overflow-hidden"
                        rows={1}
                        disabled={!connected || isChatLoading}
                      />
                      <button
                        onClick={handleSend}
                        disabled={!prompt.trim() || isChatLoading || !connected}
                        className="px-6 py-3 rounded-xl bg-gradient-to-r from-[#7dcfff]/20 to-[#9B72CB]/20 border border-[#7dcfff]/30 text-[#7dcfff] hover:shadow-lg transition-all disabled:opacity-50 disabled:cursor-not-allowed"
                      >
                        {isChatLoading ? (
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
                          <button key={cmd} onClick={() => setPrompt(cmd)} className="hover:text-[#7dcfff] transition-colors">{cmd}</button>
                        ))}
                      </div>
                    </div>
                  </div>
                </>
              ) : (
                <div className="flex-1 overflow-y-auto p-6 custom-scrollbar">
                  {generatedImages.length === 0 ? (
                    <div className="h-full flex flex-col items-center justify-center text-center">
                      <Image className="w-16 h-16 text-[#565f89] mb-4" />
                      <h3 className="text-lg font-bold text-white">No Images Yet</h3>
                      <p className="text-xs text-[#565f89] mt-2">Generate with <code className="text-[#7dcfff]">/generate prompt</code></p>
                    </div>
                  ) : (
                    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
                      {generatedImages.map((img) => (
                        <div key={img.id} className="bg-black/40 rounded-xl overflow-hidden border border-[#7dcfff]/10 group hover:border-[#7dcfff]/30 transition">
                          <div className="relative overflow-hidden bg-black/60 aspect-square">
                            {img.isLoading ? (
                              <div className="w-full h-full flex items-center justify-center">
                                <div className="w-8 h-8 border-2 border-[#7dcfff]/30 border-t-[#7dcfff] rounded-full animate-spin" />
                              </div>
                            ) : img.url ? (
                              <img src={img.url} alt={img.prompt} className="w-full h-full object-cover group-hover:scale-105 transition-transform" loading="lazy" />
                            ) : (
                              <div className="w-full h-full flex items-center justify-center text-[#565f89]"><Image className="w-8 h-8" /></div>
                            )}
                            {!img.isLoading && img.url && (
                              <button onClick={() => handleDownloadImage(img.url, img.prompt)} className="absolute top-2 right-2 p-2 bg-black/70 rounded-lg opacity-0 group-hover:opacity-100 transition-opacity">
                                <Download className="w-3 h-3 text-[#7dcfff]" />
                              </button>
                            )}
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
              <aside className="hidden lg:flex w-80 bg-black/30 backdrop-blur-xl border border-[#7dcfff]/10 rounded-2xl p-5 flex-col gap-4 sticky top-4 h-[calc(100vh-100px)] shrink-0 overflow-y-auto custom-scrollbar">
                <div className="flex items-center justify-between">
                  <h3 className="text-[10px] text-[#565f89] flex items-center gap-2 font-mono uppercase tracking-wider">
                    <BookOpen className="w-3 h-3 text-[#7dcfff]" /> COMMAND LEXICON
                  </h3>
                </div>
                <div className="relative">
                  <Search className="w-3 h-3 absolute left-3 top-2.5 text-[#565f89]" />
                  <input type="text" placeholder="Search commands..." value={searchTerm} onChange={(e) => setSearchTerm(e.target.value)} className="w-full bg-black/50 border border-[#7dcfff]/20 rounded-xl py-2 pl-8 pr-3 text-xs text-white placeholder:text-[#565f89] outline-none focus:border-[#7dcfff]/50" />
                </div>
                <div className="flex-1 overflow-y-auto space-y-2 custom-scrollbar">
                  {Object.entries(COMMAND_GROUPS).map(([group, commands]) => {
                    const filtered = commands.filter(cmd => cmd.name.toLowerCase().includes(searchTerm.toLowerCase()) || cmd.desc.toLowerCase().includes(searchTerm.toLowerCase()));
                    if (filtered.length === 0) return null;
                    const isExpanded = expandedGroup === group;
                    return (
                      <div key={group} className="border border-white/10 rounded-lg overflow-hidden">
                        <button onClick={() => setExpandedGroup(isExpanded ? null : group)} className="w-full flex items-center justify-between p-2.5 bg-black/20 hover:bg-white/5 transition-colors">
                          <span className="text-[9px] font-mono font-bold tracking-widest text-[#9B72CB] uppercase">{group} <span className="text-[#64748B]">({filtered.length})</span></span>
                          <ChevronRight className={`w-3 h-3 text-[#64748B] transition-transform ${isExpanded ? 'rotate-90' : ''}`} />
                        </button>
                        {isExpanded && (
                          <div className="p-2 space-y-2 border-t border-white/5 bg-black/20">
                            {filtered.map((cmd, i) => <CommandCard key={i} name={cmd.name} description={cmd.desc} example={cmd.example} />)}
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
                    <p className="text-[9px] text-[#565f89] leading-relaxed">All commands filtered through SCE Protocol. Images and videos generated via ComfyUI with constitutional oversight.</p>
                  </div>
                </div>
              </aside>
            )}
          </div>
        )}

        {/* Navigation Sections */}
        <section id="protocol" className="min-h-screen p-8 border-t border-[#7dcfff]/10">
          <div className="max-w-4xl mx-auto">
            <h2 className="text-2xl font-bold mb-4">SCE Protocol v2.0</h2>
            <p className="text-[#c0caf5] mb-4">Constitutional AI enforcement at bytecode level. Every action signed. Every decision auditable.</p>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mt-8">
              <div className="bg-black/40 p-4 rounded-xl border border-[#7dcfff]/20"><Shield className="w-8 h-8 text-[#7dcfff] mb-2" /><h3 className="font-bold mb-1">Constitutional</h3><p className="text-xs text-[#565f89]">5 unbreakable laws enforced</p></div>
              <div className="bg-black/40 p-4 rounded-xl border border-[#7dcfff]/20"><GitBranch className="w-8 h-8 text-[#7dcfff] mb-2" /><h3 className="font-bold mb-1">Drift Chain</h3><p className="text-xs text-[#565f89]">Cryptographic proof of actions</p></div>
              <div className="bg-black/40 p-4 rounded-xl border border-[#7dcfff]/20"><Lock className="w-8 h-8 text-[#7dcfff] mb-2" /><h3 className="font-bold mb-1">Sovereign</h3><p className="text-xs text-[#565f89]">Zero data leakage</p></div>
            </div>
          </div>
        </section>

        <section id="workers" className="min-h-screen p-8 border-t border-[#7dcfff]/10">
          <div className="max-w-4xl mx-auto">
            <h2 className="text-2xl font-bold mb-4">Worker Swarm</h2>
            <p className="text-[#c0caf5] mb-4">{workerCount} specialized workers for code generation, trading, image synthesis, and more.</p>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mt-8">
              {workers?.slice(0, 12).map((w: any, i: number) => (
                <div key={i} className="bg-black/40 p-2 rounded-lg text-xs text-center border border-[#7dcfff]/10">{typeof w === 'string' ? w : w.name || 'Worker'}</div>
              ))}
            </div>
          </div>
        </section>

        <section id="comfyui" className="min-h-screen p-8 border-t border-[#7dcfff]/10">
          <div className="max-w-4xl mx-auto">
            <h2 className="text-2xl font-bold mb-4">ComfyUI Studio</h2>
            <p className="text-[#c0caf5] mb-4">AI image and video generation with full audit trail.</p>
            <div className="bg-black/40 p-6 rounded-xl border border-[#7dcfff]/20 text-center">
              <Palette className="w-12 h-12 text-[#7dcfff] mx-auto mb-3" />
              <p className="text-sm">Status: {comfyuiStatus === 'online' ? '🟢 Online' : '🔴 Offline'}</p>
              <p className="text-xs text-[#565f89] mt-2">Use /generate prompt to create images</p>
            </div>
          </div>
        </section>

        <section id="audit" className="min-h-screen p-8 border-t border-[#7dcfff]/10">
          <div className="max-w-4xl mx-auto">
            <h2 className="text-2xl font-bold mb-4">Drift Chain Audit</h2>
            <p className="text-[#c0caf5] mb-4">Immutable ledger of all system actions.</p>
            <div className="bg-black/40 p-4 rounded-xl border border-[#7dcfff]/20 font-mono text-xs">
              <div className="flex justify-between items-center p-2 border-b border-[#7dcfff]/10"><span>Chain Valid:</span><span className={telemetry?.chain_valid ? 'text-[#9ece6a]' : 'text-[#f7768e]'}>{telemetry?.chain_valid ? '✓ VERIFIED' : '✗ INVALID'}</span></div>
              <div className="flex justify-between items-center p-2"><span>Integrity Score:</span><span className="text-[#7dcfff]">{govScore}%</span></div>
            </div>
          </div>
        </section>

        <section id="docs" className="min-h-screen p-8 border-t border-[#7dcfff]/10">
          <div className="max-w-4xl mx-auto">
            <h2 className="text-2xl font-bold mb-4">Documentation</h2>
            <p className="text-[#c0caf5] mb-4">Complete API reference and whitepaper.</p>
            <div className="flex gap-4">
              <Link href="/docs"><button className="px-4 py-2 bg-[#7dcfff]/10 rounded-lg text-[#7dcfff] hover:bg-[#7dcfff]/20 transition">API Reference</button></Link>
              <Link href="/whitepaper"><button className="px-4 py-2 bg-[#9B72CB]/10 rounded-lg text-[#9B72CB] hover:bg-[#9B72CB]/20 transition">Whitepaper</button></Link>
            </div>
          </div>
        </section>

        <div className="h-20" />
      </div>

      <style jsx global>{`
        .custom-scrollbar::-webkit-scrollbar { width: 4px; }
        .custom-scrollbar::-webkit-scrollbar-track { background: rgba(125,207,255,0.05); border-radius: 10px; }
        .custom-scrollbar::-webkit-scrollbar-thumb { background: rgba(125,207,255,0.3); border-radius: 10px; }
        .custom-scrollbar::-webkit-scrollbar-thumb:hover { background: rgba(125,207,255,0.5); }
        textarea { scrollbar-width: none; }
        textarea::-webkit-scrollbar { display: none; }
      `}</style>
    </div>
  );
}