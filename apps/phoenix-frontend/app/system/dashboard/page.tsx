// app/dashboard/page.tsx
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
// COMMAND DATABASE
// ==========================================
const commandGroups = {
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
};

const CommandCard = ({ name, description, example }: { name: string; description: string; example: string }) => (
  <div className="p-2 rounded-lg hover:bg-white/5 transition-colors">
    <div className="text-[9px] font-mono text-[#7dcfff]">{name}</div>
    <div className="text-[8px] text-[#565f89]">{description}</div>
    <div className="text-[7px] text-[#9B72CB] mt-1">`ex: {example}`</div>
  </div>
);

export default function SovereignDashboard() {
  const store = usePhoenix();
  
  const {
    connected = false,
    messages: storeMessages = [],
    isStreaming = false,
    workers = [],
    telemetry = { chain_valid: false, kernel_load: 0, workers: 0, memory: 0, gpu: { has_gpu: false } },
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
  
  // UI State
  const [mounted, setMounted] = useState(false);
  const [time, setTime] = useState('');
  const [prompt, setPrompt] = useState('');
  const [activeHash, setActiveHash] = useState('');
  const [activeTab, setActiveTab] = useState<'chat' | 'gallery'>('chat');
  const [showSidebar, setShowSidebar] = useState(true);
  const [viewMode, setViewMode] = useState<'dashboard' | 'terminal'>('dashboard');
  const [generatedImages, setGeneratedImages] = useState<Array<{ id: number; prompt: string; url: string; timestamp: string }>>([]);
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
    if (!prompt.trim() || isStreaming) return;
    const userText = prompt;
    setPrompt('');

    if (userText.startsWith('/generate')) {
      const imagePrompt = userText.replace('/generate', '').trim();
      if (imagePrompt && generateImage) {
        await generateImage(imagePrompt);
        setTimeout(() => {
          setGeneratedImages(prev => [{
            id: Date.now(),
            prompt: imagePrompt,
            url: `/api/comfyui/latest?t=${Date.now()}`,
            timestamp: new Date().toLocaleTimeString()
          }, ...prev].slice(0, 20));
        }, 3000);
        return;
      }
    } else if (userText.startsWith('/video')) {
      const videoPrompt = userText.replace('/video', '').trim();
      if (videoPrompt && generateVideo) {
        await generateVideo(videoPrompt);
        return;
      }
    }

    await executeCommand?.(userText);
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const workerCount = workers?.length || 0;
  const govScore = telemetry?.chain_valid ? 98 : 85;
  const comfyuiStatus = comfyui?.connected ? 'online' : 'offline';
  
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
      <header className="relative z-10 flex items-center justify-between px-6 py-3 border-b border-[#7dcfff]/10 bg-black/40 backdrop-blur-xl">
        <div className="flex items-center gap-8 text-[10px] font-mono">
          <div className="flex items-center gap-2">
            <div className={`w-2 h-2 rounded-full ${connected ? 'bg-[#9ece6a] animate-pulse' : 'bg-[#f7768e]'}`} />
            <span className={connected ? 'text-[#9ece6a]' : 'text-[#f7768e]'}>
              KERNEL: {connected ? 'ACTIVE' : 'OFFLINE'}
            </span>
          </div>
          <div className="flex items-center gap-2">
            <Shield className="w-3 h-3 text-[#9B72CB]" />
            <span>SCE: <span className="text-[#7dcfff]">ENFORCED</span></span>
          </div>
          <span className="text-[#565f89]">{time} UTC</span>
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
                      <span className="text-xs font-mono text-white">{workerCount} / 70</span>
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
                      />
                      <button
                        onClick={handleSend}
                        disabled={!prompt.trim() || isStreaming || !connected}
                        className="px-6 py-3 rounded-xl bg-gradient-to-r from-[#7dcfff]/20 to-[#9B72CB]/20 border border-[#7dcfff]/30 text-[#7dcfff] hover:shadow-lg transition-all disabled:opacity-50"
                      >
                        <Send className="w-4 h-4" />
                      </button>
                    </div>
                    <div className="flex justify-between mt-3 text-[8px] text-[#565f89] font-mono">
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
                      <p className="text-xs text-[#565f89] mt-2">
                        Generate with <code className="text-[#7dcfff]">/generate prompt</code>
                      </p>
                    </div>
                  ) : (
                    <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
                      {generatedImages.map((img) => (
                        <div key={img.id} className="bg-black/40 rounded-xl overflow-hidden border border-[#7dcfff]/10">
                          <img src={img.url} alt={img.prompt} className="w-full h-48 object-cover" />
                          <div className="p-3">
                            <p className="text-xs text-[#c0caf5] truncate">{img.prompt}</p>
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
                  {Object.entries(commandGroups).map(([group, commands]) => {
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
        <section id="protocol" className="scroll-mt-20 py-20 px-8 border-t border-[#7dcfff]/10">
          <div className="max-w-6xl mx-auto">
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-[#9ece6a]/10 border border-[#9ece6a]/20 mb-4">
              <Shield className="w-4 h-4 text-[#9ece6a]" />
              <span className="text-xs font-mono text-[#9ece6a]">SCE PROTOCOL</span>
            </div>
            <h2 className="text-3xl font-bold text-white mb-4">Constitutional Enforcement</h2>
            <p className="text-[#565f89] mb-8 max-w-2xl">Unbreakable laws enforced at the bytecode level. Every action cryptographically signed.</p>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              <div className="bg-[#0a0a0c] border border-white/[0.05] rounded-xl p-6 hover:border-[#7dcfff]/20 transition-all">
                <div className="text-2xl font-mono text-[#9ece6a] mb-2">DATA_SOVEREIGNTY</div>
                <div className="text-sm text-[#565f89]">No data leaves your node. Ever.</div>
              </div>
              <div className="bg-[#0a0a0c] border border-white/[0.05] rounded-xl p-6 hover:border-[#7dcfff]/20 transition-all">
                <div className="text-2xl font-mono text-[#9ece6a] mb-2">CREATIVE_FREEDOM</div>
                <div className="text-sm text-[#565f89]">No content restrictions beyond ethics.</div>
              </div>
              <div className="bg-[#0a0a0c] border border-white/[0.05] rounded-xl p-6 hover:border-[#7dcfff]/20 transition-all">
                <div className="text-2xl font-mono text-[#9ece6a] mb-2">TRANSPARENCY</div>
                <div className="text-sm text-[#565f89]">Every decision visible in drift chain.</div>
              </div>
            </div>
          </div>
        </section>

        <section id="workers" className="scroll-mt-20 py-20 px-8 border-t border-[#7dcfff]/10">
          <div className="max-w-6xl mx-auto">
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-[#9ece6a]/10 border border-[#9ece6a]/20 mb-4">
              <Users className="w-4 h-4 text-[#9ece6a]" />
              <span className="text-xs font-mono text-[#9ece6a]">SWARM INTELLIGENCE</span>
            </div>
            <h2 className="text-3xl font-bold text-white mb-4">{workerCount}+ Specialized Workers</h2>
            <p className="text-[#565f89] mb-8 max-w-2xl">One hive. Coordinated by SCE constitutional enforcement.</p>
          </div>
        </section>

        <section id="comfyui" className="scroll-mt-20 py-20 px-8 border-t border-[#7dcfff]/10">
          <div className="max-w-6xl mx-auto">
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-[#7dcfff]/10 border border-[#7dcfff]/20 mb-4">
              <Palette className="w-4 h-4 text-[#7dcfff]" />
              <span className="text-xs font-mono text-[#7dcfff]">COMFYUI STUDIO</span>
            </div>
            <h2 className="text-3xl font-bold text-white mb-4">AI Image & Video Studio</h2>
            <p className="text-[#565f89] mb-8 max-w-2xl">Generate stunning images and videos with ComfyUI. Full SCE constitutional oversight.</p>
            <div className="mt-6 text-center">
              <div className={`inline-flex items-center gap-2 px-4 py-2 rounded-full ${
                comfyuiStatus === 'online' 
                  ? 'bg-[#9ece6a]/10 border border-[#9ece6a]/20' 
                  : 'bg-[#f7768e]/10 border border-[#f7768e]/20'
              }`}>
                <div className={`w-2 h-2 rounded-full ${comfyuiStatus === 'online' ? 'bg-[#9ece6a]' : 'bg-[#f7768e]'}`} />
                <span className="text-xs font-mono">ComfyUI: {comfyuiStatus === 'online' ? 'Connected' : 'Not Running'}</span>
              </div>
            </div>
          </div>
        </section>

        <div className="h-20" />
      </div>

      {/* Mode Toggle Button */}
      <button
        onClick={() => setViewMode(viewMode === 'dashboard' ? 'terminal' : 'dashboard')}
        className="fixed bottom-6 right-6 z-50 p-3 rounded-full bg-[#0a0a0c] border border-[#7dcfff]/30 text-[#7dcfff] hover:bg-[#7dcfff]/10 transition-all shadow-lg"
      >
        {viewMode === 'dashboard' ? <Terminal className="w-5 h-5" /> : <Grid3x3 className="w-5 h-5" />}
      </button>

      <style jsx global>{`
        .custom-scrollbar::-webkit-scrollbar { width: 4px; }
        .custom-scrollbar::-webkit-scrollbar-track { background: rgba(125,207,255,0.05); border-radius: 10px; }
        .custom-scrollbar::-webkit-scrollbar-thumb { background: rgba(125,207,255,0.3); border-radius: 10px; }
        textarea::-webkit-scrollbar { display: none; }
      `}</style>
    </div>
  );
}