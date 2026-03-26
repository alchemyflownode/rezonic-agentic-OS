'use client';

import React, { useState, useEffect, useRef, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  Zap, Shield, Sparkles, Send, Network, Brain, 
  GitBranch, Activity, Cpu, Eye, EyeOff, 
  Radar, Lock, Unlock, Menu, PanelLeftClose, PanelLeftOpen,
  CheckCircle2, XCircle, Terminal, User, Bot, BookOpen, Search,
  ChevronRight, Home, FileText, Users, FileCheck, Image, Video,
  Palette, Camera, Film, Layers, GalleryVertical, Wand2, Flame
} from 'lucide-react';
import Link from 'next/link';
import { SovereignMessage } from '@/components/SovereignMessage';
import { phoenixStream } from '@/lib/phoenix-client';

const API_BASE = 'http://localhost:8002';

interface Message {
  id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  driftLock?: string;
  timestamp: string;
  isStreaming?: boolean;
  imageUrl?: string;
  videoUrl?: string;
}

// Enhanced Navigation with ComfyUI section
const navItems = [
  { name: 'Protocol', href: '#protocol', icon: Shield, description: 'SCE Constitutional Enforcement' },
  { name: 'Workers', href: '#workers', icon: Users, description: '70+ Specialized Agents' },
  { name: 'ComfyUI', href: '#comfyui', icon: Palette, description: 'AI Image & Video Studio', badge: 'NEW' },
  { name: 'Audit', href: '#audit', icon: FileCheck, description: 'Drift Chain Audit Trail' },
  { name: 'Docs', href: '#docs', icon: BookOpen, description: 'Whitepaper & Documentation' },
];

// Gallery images (placeholder - will be populated from ComfyUI)
const galleryImages = [
  { id: 1, prompt: "cyberpunk cat", url: "/api/placeholder/400/400", timestamp: "12:34:56" },
  { id: 2, prompt: "neon cityscape", url: "/api/placeholder/400/400", timestamp: "12:35:23" },
  { id: 3, prompt: "ethereal landscape", url: "/api/placeholder/400/400", timestamp: "12:36:01" },
];

export default function SovereignDashboard() {
  const [mounted, setMounted] = useState(false);
  const [time, setTime] = useState('');
  const [kernelStatus, setKernelStatus] = useState<'online' | 'offline' | 'checking'>('checking');
  const [workerCount, setWorkerCount] = useState(0);
  const [govScore, setGovScore] = useState(98);
  const [messages, setMessages] = useState<Message[]>([]);
  const [prompt, setPrompt] = useState('');
  const [isStreaming, setIsStreaming] = useState(false);
  const [driftLock, setDriftLock] = useState('');
  const [activeHash, setActiveHash] = useState('');
  const [activeTab, setActiveTab] = useState<'chat' | 'gallery'>('chat');
  const [generatedImages, setGeneratedImages] = useState(galleryImages);
  const [comfyuiStatus, setComfyuiStatus] = useState<'checking' | 'online' | 'offline'>('checking');
  const [showSidebar, setShowSidebar] = useState(true);
  
  const chatEndRef = useRef<HTMLDivElement>(null);

  // Check ComfyUI status
  const checkComfyUI = async () => {
    try {
      const res = await fetch('http://127.0.0.1:8188/system_stats');
      if (res.ok) {
        setComfyuiStatus('online');
      } else {
        setComfyuiStatus('offline');
      }
    } catch {
      setComfyuiStatus('offline');
    }
  };

  useEffect(() => {
    checkComfyUI();
    const interval = setInterval(checkComfyUI, 30000);
    return () => clearInterval(interval);
  }, []);

  // Handle hash change for active nav state
  useEffect(() => {
    const handleHashChange = () => {
      setActiveHash(window.location.hash);
    };
    handleHashChange();
    window.addEventListener('hashchange', handleHashChange);
    return () => window.removeEventListener('hashchange', handleHashChange);
  }, []);

  // Scroll to section
  const scrollToSection = (e: React.MouseEvent<HTMLAnchorElement>, hash: string) => {
    e.preventDefault();
    const element = document.querySelector(hash);
    if (element) {
      element.scrollIntoView({ behavior: 'smooth' });
      window.history.pushState(null, '', hash);
      setActiveHash(hash);
    }
  };

  // Clock Effect
  useEffect(() => {
    const clock = setInterval(() => {
      setTime(new Date().toLocaleTimeString('en-US', { hour12: false, hour: '2-digit', minute: '2-digit', second: '2-digit' }));
    }, 1000);
    return () => clearInterval(clock);
  }, []);

  // Fetch System Data
  const fetchData = async () => {
    try {
      const healthRes = await fetch(`${API_BASE}/health`);
      if (healthRes.ok) {
        const data = await healthRes.json();
        setKernelStatus('online');
        setWorkerCount(data.workers || 70);
        setGovScore(Math.floor(data.integrity_score || 98.2));
      } else {
        setKernelStatus('offline');
      }
    } catch (err) {
      setKernelStatus('offline');
    }
  };

  useEffect(() => {
    setMounted(true);
    fetchData();
    const interval = setInterval(fetchData, 10000);
    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleTransmit = async () => {
    if (!prompt.trim() || isStreaming) return;
    
    const userText = prompt;
    setPrompt('');
    setIsStreaming(true);

    const timeStamp = new Date().toLocaleTimeString();
    const assistantId = crypto.randomUUID();
    
    setMessages(prev => [
      ...prev, 
      { id: crypto.randomUUID(), role: 'user', content: userText, timestamp: timeStamp },
      { id: assistantId, role: 'assistant', content: '', timestamp: timeStamp, isStreaming: true }
    ]);

    try {
      const response = await fetch(`${API_BASE}/kernel/stream`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'Authorization': Bearer  },
        body: JSON.stringify({ task: userText })
      });

      const reader = response.body?.getReader();
      const decoder = new TextDecoder();
      let fullContent = '';
      let currentDriftLock = '';
      let buffer = '';
      let imageUrl: string | undefined;
      let videoUrl: string | undefined;

      while (reader) {
        const { done, value } = await reader.read();
        if (done) break;
        
        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        buffer = lines.pop() || '';
        
        for (const line of lines) {
          if (line.startsWith('data: ')) {
            try {
              const data = JSON.parse(line.slice(6));
              if (data.content) fullContent += data.content;
              if (data.drift_lock) currentDriftLock = data.drift_lock;
              
              // Check for generation result
              if (data.type === 'reflex' && data.content?.includes('Generation Queued')) {
                const promptMatch = userText.match(/\/generate (.+?)(?:\s|$)/);
                if (promptMatch) {
                  setTimeout(() => {
                    const newImage = {
                      id: Date.now(),
                      prompt: promptMatch[1],
                      url: `/api/comfyui/latest?t=${Date.now()}`,
                      timestamp: new Date().toLocaleTimeString()
                    };
                    setGeneratedImages(prev => [newImage, ...prev].slice(0, 20));
                  }, 3000);
                }
              }
              
              setMessages(prev => prev.map(m => 
                m.id === assistantId ? { ...m, content: fullContent, driftLock: currentDriftLock, imageUrl, videoUrl } : m
              ));
            } catch (e) {
              if (line.length > 6) fullContent += line.slice(6);
            }
          }
        }
      }
      
      setMessages(prev => prev.map(m => 
        m.id === assistantId ? { ...m, isStreaming: false } : m
      ));
      setDriftLock(currentDriftLock);
      
    } catch (error) {
      setMessages(prev => prev.map(m => 
        m.id === assistantId ? { ...m, content: 'âŒ Connection lost', isStreaming: false } : m
      ));
    } finally {
      setIsStreaming(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleTransmit();
    }
  };

  if (!mounted) return null;

  return (
    <div className="h-screen bg-gradient-to-br from-[#0a0a0c] via-[#050505] to-[#0a0a0c] text-[#c0caf5] overflow-hidden">
      
      {/* Animated Grid Background */}
      <div className="fixed inset-0 pointer-events-none opacity-20">
        <div className="absolute inset-0 bg-[radial-gradient(circle_at_50%_50%,_#7dcfff_0%,_transparent_50%)] opacity-5" />
        <div className="absolute inset-0" style={{ backgroundImage: 'linear-gradient(to right, #7dcfff0a 1px, transparent 1px), linear-gradient(to bottom, #7dcfff0a 1px, transparent 1px)', backgroundSize: '40px 40px' }} />
      </div>

      {/* Glass Header with Navigation */}
      <header className="relative z-10 flex items-center justify-between px-6 py-3 border-b border-[#7dcfff]/10 bg-black/40 backdrop-blur-xl">
        <div className="flex items-center gap-8 text-[10px] font-mono">
          <div className="flex items-center gap-2">
            <div className={`w-2 h-2 rounded-full ${kernelStatus === 'online' ? 'bg-[#9ece6a] animate-pulse' : 'bg-[#f7768e]'}`} />
            <span className={kernelStatus === 'online' ? 'text-[#9ece6a]' : 'text-[#f7768e]'}>
              KERNEL: {kernelStatus === 'online' ? 'ACTIVE' : 'OFFLINE'}
            </span>
          </div>
          <div className="flex items-center gap-2">
            <Shield className="w-3 h-3 text-[#9B72CB]" />
            <span>SCE: <span className="text-[#7dcfff]">ENFORCED</span></span>
          </div>
          <span className="text-[#565f89]">{time} UTC</span>
        </div>
        
        {/* CENTER NAVIGATION */}
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
                  isActive 
                    ? 'text-[#9ece6a]' 
                    : 'text-[#565f89] hover:text-[#c0caf5]'
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
        
        <div className="flex items-center gap-4"><Link href="/"><button className="px-3 py-1 rounded-lg bg-[#7dcfff]/10 border border-[#7dcfff]/20 text-[10px] text-[#7dcfff] hover:bg-[#7dcfff]/20 transition flex items-center gap-1"><Home className="w-3 h-3" /> Home</button></Link>
          <button
            onClick={() => setShowSidebar(!showSidebar)}
            className="p-1.5 rounded-lg bg-white/5 hover:bg-white/10 transition"
          >
            {showSidebar ? <PanelLeftClose className="w-4 h-4" /> : <PanelLeftOpen className="w-4 h-4" />}
          </button>
          <Link href="/">
            <button className="px-3 py-1 rounded-lg bg-[#7dcfff]/10 border border-[#7dcfff]/20 text-[10px] text-[#7dcfff] hover:bg-[#7dcfff]/20 transition flex items-center gap-1">
              <Home className="w-3 h-3" />
              Home
            </button>
          </Link>
          <div className="text-right">
            <div className="text-[8px] text-[#565f89] uppercase tracking-wider">Workers</div>
            <div className="text-xs font-bold text-white">{workerCount}</div>
          </div>
        </div>
      </header>

      {/* Main Content - Scrollable */}
      <div className="relative z-10 h-[calc(100vh-60px)] overflow-y-auto custom-scrollbar">
        
        {/* Chat/Gallery Section */}
        <div className="flex p-4 gap-4 min-h-[600px]">
          
          {/* LEFT: System Status - Conditional Sidebar */}
          {showSidebar && (
            <aside className="w-80 bg-black/30 backdrop-blur-xl border border-[#7dcfff]/10 rounded-2xl p-5 flex flex-col gap-5 sticky top-4 h-[calc(100vh-100px)] shrink-0">
              <div>
                <h3 className="text-[10px] text-[#565f89] mb-4 flex items-center gap-2 font-mono uppercase tracking-wider">
                  <Activity className="w-3 h-3 text-[#7dcfff]" /> SYSTEM STATUS
                </h3>
                <div className="space-y-3">
                  <div className="flex justify-between items-center p-3 bg-white/5 rounded-xl">
                    <span className="text-xs">Kernel Load</span>
                    <div className="w-32 h-1.5 bg-white/10 rounded-full overflow-hidden">
                      <div className="h-full w-[34%] bg-gradient-to-r from-[#7dcfff] to-[#9B72CB] rounded-full" />
                    </div>
                    <span className="text-xs font-mono text-[#7dcfff]">34%</span>
                  </div>
                  <div className="flex justify-between items-center p-3 bg-white/5 rounded-xl">
                    <span className="text-xs">Worker Pool</span>
                    <span className="text-xs font-mono text-white">{workerCount} / 70</span>
                  </div>
                  <div className="flex justify-between items-center p-3 bg-white/5 rounded-xl">
                    <span className="text-xs">SCE Integrity</span>
                    <span className="text-xs font-mono text-[#9ece6a]">{govScore}%</span>
                  </div>
                  <div className="flex justify-between items-center p-3 bg-gradient-to-r from-[#7dcfff]/10 to-[#9B72CB]/10 rounded-xl">
                    <span className="text-xs flex items-center gap-1"><Palette className="w-3 h-3" /> ComfyUI</span>
                    <span className={`text-xs font-mono ${comfyuiStatus === 'online' ? 'text-[#9ece6a]' : 'text-[#f7768e]'}`}>
                      {comfyuiStatus === 'online' ? 'ACTIVE' : 'OFFLINE'}
                    </span>
                  </div>
                  {driftLock && (
                    <div className="flex justify-between items-center p-3 bg-white/5 rounded-xl">
                      <span className="text-xs">Drift Lock</span>
                      <span className="text-xs font-mono text-[#7dcfff]">{driftLock.slice(0, 8)}...</span>
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
                  <span>Constitutional AI â€¢ Active</span>
                </div>
              </div>
            </aside>
          )}

          {/* CENTER: Chat or Gallery */}
          <main className="flex-1 flex flex-col bg-black/30 backdrop-blur-xl border border-[#7dcfff]/10 rounded-2xl overflow-hidden">
            {/* Tab Header */}
            <div className="p-4 border-b border-[#7dcfff]/10 bg-gradient-to-r from-[#9B72CB]/10 to-transparent">
              <div className="flex items-center gap-4"><Link href="/"><button className="px-3 py-1 rounded-lg bg-[#7dcfff]/10 border border-[#7dcfff]/20 text-[10px] text-[#7dcfff] hover:bg-[#7dcfff]/20 transition flex items-center gap-1"><Home className="w-3 h-3" /> Home</button></Link>
                <button
                  onClick={() => setActiveTab('chat')}
                  className={`flex items-center gap-2 px-3 py-1.5 rounded-lg text-sm transition-all ${activeTab === 'chat' ? 'bg-[#7dcfff]/20 text-[#7dcfff]' : 'text-[#565f89] hover:text-white'}`}
                >
                  <Sparkles className="w-4 h-4" />
                  Sovereign Chat
                </button>
                <button
                  onClick={() => setActiveTab('gallery')}
                  className={`flex items-center gap-2 px-3 py-1.5 rounded-lg text-sm transition-all ${activeTab === 'gallery' ? 'bg-[#7dcfff]/20 text-[#7dcfff]' : 'text-[#565f89] hover:text-white'}`}
                >
                  <GalleryVertical className="w-4 h-4" />
                  Gallery ({generatedImages.length})
                </button>
                <div className="ml-auto flex items-center gap-2">
                  <div className="w-1.5 h-1.5 rounded-full bg-[#9ece6a] animate-pulse" />
                  <span className="text-[8px] font-mono text-[#565f89]">SCE v1.0</span>
                </div>
              </div>
            </div>

            {activeTab === 'chat' ? (
              <>
                {/* Chat Messages */}
                <div className="flex-1 overflow-y-auto" aria-live="polite" aria-atomic="false" p-6 space-y-4 custom-scrollbar">
                  {messages.length === 0 ? (
                    <div className="h-full flex flex-col items-center justify-center text-center">
                      <div className="w-20 h-20 rounded-full border-2 border-[#7dcfff]/20 flex items-center justify-center mb-4">
                        <Flame className="w-8 h-8 text-[#7dcfff]" />
                      </div>
                      <h3 className="text-lg font-bold bg-gradient-to-r from-[#c0caf5] to-[#7dcfff] bg-clip-text text-transparent">Sovereign AI Terminal</h3>
                      <p className="text-xs text-[#565f89] mt-2 max-w-md">Execute commands, generate images, or ask questions. Constitutional AI ensures ethical responses.</p>
                      <div className="flex gap-2 mt-6">
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
                    messages.map((msg) => (
                      <motion.div
                        key={msg.id}
                        initial={{ opacity: 0, y: 10 }}
                        animate={{ opacity: 1, y: 0 }}
                        className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
                      >
                        <div className={`max-w-[85%] ${msg.role === 'user' ? 'bg-gradient-to-r from-[#7dcfff]/20 to-[#9B72CB]/20 border border-[#7dcfff]/30 rounded-br-sm' : ''}`}>
                          {msg.role === 'assistant' ? (
                            <div>
                              <SovereignMessage
                                content={msg.content}
                                role={msg.role}
                                isStreaming={msg.isStreaming}
                                driftLock={msg.driftLock}
                              />
                              {msg.imageUrl && (
                                <div className="mt-3 rounded-xl overflow-hidden border border-[#7dcfff]/20">
                                  <img src={msg.imageUrl} alt="Generated" className="w-full h-auto max-h-96 object-contain" />
                                </div>
                              )}
                              {msg.videoUrl && (
                                <div className="mt-3 rounded-xl overflow-hidden border border-[#7dcfff]/20">
                                  <video controls className="w-full max-h-96">
                                    <source src={msg.videoUrl} type="video/mp4" />
                                  </video>
                                </div>
                              )}
                            </div>
                          ) : (
                            <div className="p-4 rounded-2xl bg-white/5 border border-white/10 rounded-bl-sm">
                              <p className="text-sm leading-relaxed whitespace-pre-wrap text-[#c0caf5]">{msg.content}</p>
                              <div className="flex items-center gap-2 mt-2">
                                <span className="text-[8px] text-[#565f89]">{msg.timestamp}</span>
                              </div>
                            </div>
                          )}
                        </div>
                      </motion.div>
                    ))
                  )}
                  <div ref={chatEndRef} />
                </div>

                {/* Input Area */}
                <div className="p-4 border-t border-[#7dcfff]/10 bg-black/20">
                  <div className="flex gap-2">
                    <textarea
                      value={prompt}
                      onChange={(e) => setPrompt(e.target.value)}
                      onKeyDown={handleKeyDown}
                      placeholder={kernelStatus === 'online' ? "Execute command, ask a question, or /generate an image..." : "Awaiting kernel connection..."}
                      className="flex-1 bg-black/50 border border-[#7dcfff]/20 rounded-xl px-4 py-3 text-sm text-[#c0caf5] placeholder:text-[#565f89] outline-none resize-none focus:border-[#7dcfff]/50 transition-all"
                      rows={1}
                    />
                    <button
                      onClick={handleTransmit}
                      disabled={!prompt.trim() || isStreaming || kernelStatus !== 'online'}
                      className="px-6 py-3 rounded-xl bg-gradient-to-r from-[#7dcfff]/20 to-[#9B72CB]/20 border border-[#7dcfff]/30 text-[#7dcfff] hover:shadow-lg transition-all disabled:opacity-50"
                    >
                      <Send className="w-4 h-4" />
                    </button>
                  </div>
                  <div className="flex justify-between mt-3 text-[8px] text-[#565f89] font-mono">
                    <div className="flex gap-3">
                      <span>ENTER â€¢ Send</span>
                      <span>SHIFT+ENTER â€¢ New line</span>
                      <span className="text-[#7dcfff]">ðŸŽ¨ /generate prompt</span>
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
              /* Gallery View */
              <div className="flex-1 overflow-y-auto" aria-live="polite" aria-atomic="false" p-6 custom-scrollbar">
                {generatedImages.length === 0 ? (
                  <div className="h-full flex flex-col items-center justify-center text-center">
                    <Palette className="w-16 h-16 text-[#565f89] mb-4" />
                    <h3 className="text-lg font-bold text-white">No Images Yet</h3>
                    <p className="text-xs text-[#565f89] mt-2">Generate your first image with <code className="text-[#7dcfff]">/generate prompt</code></p>
                  </div>
                ) : (
                  <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
                    {generatedImages.map((img) => (
                      <motion.div
                        key={img.id}
                        initial={{ opacity: 0, scale: 0.9 }}
                        animate={{ opacity: 1, scale: 1 }}
                        whileHover={{ scale: 1.02 }}
                        className="bg-black/40 rounded-xl overflow-hidden border border-[#7dcfff]/10 cursor-pointer"
                      >
                        <img src={img.url} alt={img.prompt} className="w-full h-48 object-cover" />
                        <div className="p-3">
                          <p className="text-xs text-[#c0caf5] truncate">{img.prompt}</p>
                          <p className="text-[8px] text-[#565f89] mt-1">{img.timestamp}</p>
                        </div>
                      </motion.div>
                    ))}
                  </div>
                )}
              </div>
            )}
          </main>

          {/* RIGHT: Command Lexicon - Only show if sidebar visible */}
          {showSidebar && (
            <aside className="w-80 bg-black/30 backdrop-blur-xl border border-[#7dcfff]/10 rounded-2xl p-5 flex flex-col gap-4 sticky top-4 h-[calc(100vh-100px)] shrink-0">
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
                  className="w-full bg-black/50 border border-[#7dcfff]/20 rounded-xl py-2 pl-8 pr-3 text-xs text-white placeholder:text-[#565f89] outline-none focus:border-[#7dcfff]/50"
                />
              </div>

              <div className="flex-1 overflow-y-auto" aria-live="polite" aria-atomic="false" space-y-2">
                <div className="border border-white/10 rounded-lg p-3 hover:bg-white/5 transition">
                  <div className="flex items-center gap-2 mb-1">
                    <Terminal className="w-3 h-3 text-[#7dcfff]" />
                    <span className="text-[9px] font-mono text-white">/generate</span>
                    <span className="text-[8px] text-[#9ece6a] ml-auto">NEW</span>
                  </div>
                  <p className="text-[8px] text-[#565f89]">Generate image via ComfyUI</p>
                  <code className="text-[7px] text-[#7dcfff]/70">ex: /generate cyberpunk cat</code>
                </div>
                <div className="border border-white/10 rounded-lg p-3 hover:bg-white/5 transition">
                  <div className="flex items-center gap-2 mb-1">
                    <Terminal className="w-3 h-3 text-[#7dcfff]" />
                    <span className="text-[9px] font-mono text-white">/video</span>
                  </div>
                  <p className="text-[8px] text-[#565f89]">Generate video (AnimateDiff)</p>
                  <code className="text-[7px] text-[#7dcfff]/70">ex: /video cat running</code>
                </div>
                <div className="border border-white/10 rounded-lg p-3 hover:bg-white/5 transition">
                  <div className="flex items-center gap-2 mb-1">
                    <Terminal className="w-3 h-3 text-[#7dcfff]" />
                    <span className="text-[9px] font-mono text-white">/workflow list</span>
                  </div>
                  <p className="text-[8px] text-[#565f89]">List saved ComfyUI workflows</p>
                </div>
                <div className="border border-white/10 rounded-lg p-3 hover:bg-white/5 transition">
                  <div className="flex items-center gap-2 mb-1">
                    <Terminal className="w-3 h-3 text-[#7dcfff]" />
                    <span className="text-[9px] font-mono text-white">/code</span>
                  </div>
                  <p className="text-[8px] text-[#565f89]">Generate Python code</p>
                </div>
                <div className="border border-white/10 rounded-lg p-3 hover:bg-white/5 transition">
                  <div className="flex items-center gap-2 mb-1">
                    <Terminal className="w-3 h-3 text-[#7dcfff]" />
                    <span className="text-[9px] font-mono text-white">/health</span>
                  </div>
                  <p className="text-[8px] text-[#565f89]">System status</p>
                </div>
                <div className="border border-white/10 rounded-lg p-3 hover:bg-white/5 transition">
                  <div className="flex items-center gap-2 mb-1">
                    <Terminal className="w-3 h-3 text-[#7dcfff]" />
                    <span className="text-[9px] font-mono text-white">/workers</span>
                  </div>
                  <p className="text-[8px] text-[#565f89]">List all workers</p>
                </div>
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

        {/* ===== SECTIONS FOR NAVIGATION ===== */}
        
        {/* PROTOCOL SECTION */}
        <section id="protocol" className="scroll-mt-20 py-20 px-8 border-t border-[#7dcfff]/10 bg-gradient-to-b from-transparent to-black/20">
          <div className="max-w-6xl mx-auto">
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-[#9ece6a]/10 border border-[#9ece6a]/20 mb-4">
              <Shield className="w-4 h-4 text-[#9ece6a]" />
              <span className="text-xs font-mono text-[#9ece6a]">SCE PROTOCOL</span>
            </div>
            <h2 className="text-3xl font-bold text-white mb-4">Constitutional Enforcement</h2>
            <p className="text-[#565f89] mb-8 max-w-2xl">
              Unbreakable laws enforced at the bytecode level. Every action cryptographically signed.
            </p>
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

        {/* WORKERS SECTION */}
        <section id="workers" className="scroll-mt-20 py-20 px-8 border-t border-[#7dcfff]/10 bg-gradient-to-b from-transparent to-black/20">
          <div className="max-w-6xl mx-auto">
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-[#9ece6a]/10 border border-[#9ece6a]/20 mb-4">
              <Users className="w-4 h-4 text-[#9ece6a]" />
              <span className="text-xs font-mono text-[#9ece6a]">SWARM INTELLIGENCE</span>
            </div>
            <h2 className="text-3xl font-bold text-white mb-4">70+ Specialized Workers</h2>
            <p className="text-[#565f89] mb-8 max-w-2xl">
              One hive. 70+ agents. Coordinated by SCE constitutional enforcement.
            </p>
            <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
              {['ComfyUIWorker', 'BacktestWorker', 'VisionWorker', 'VoiceWorker', 'MemoryWorker', 
                'ExecutionWorker', 'CodeGenWorker', 'CryptoWorker', 'ForexWorker', 'RezSwarmWorker'].map((worker) => (
                <div key={worker} className="bg-[#0a0a0c] border border-white/[0.05] rounded-xl p-3 text-center hover:border-[#7dcfff]/20 transition-all">
                  <div className="text-xs font-mono text-white truncate">{worker}</div>
                  <div className="text-[8px] text-[#9ece6a] mt-1">Active</div>
                </div>
              ))}
            </div>
            <div className="text-center mt-4 text-xs text-[#565f89]">
              +60 more workers active
            </div>
          </div>
        </section>

        {/* COMFYUI SECTION - NEW! */}
        <section id="comfyui" className="scroll-mt-20 py-20 px-8 border-t border-[#7dcfff]/10 bg-gradient-to-b from-transparent to-black/20">
          <div className="max-w-6xl mx-auto">
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-[#7dcfff]/10 border border-[#7dcfff]/20 mb-4">
              <Palette className="w-4 h-4 text-[#7dcfff]" />
              <span className="text-xs font-mono text-[#7dcfff]">COMFYUI STUDIO</span>
            </div>
            <h2 className="text-3xl font-bold text-white mb-4">AI Image & Video Studio</h2>
            <p className="text-[#565f89] mb-8 max-w-2xl">
              Generate stunning images and videos with ComfyUI. Full SCE constitutional oversight on every creation.
            </p>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
              <div className="bg-[#0a0a0c] border border-white/[0.05] rounded-xl p-6">
                <div className="flex items-center gap-3 mb-4">
                  <Image className="w-8 h-8 text-[#7dcfff]" />
                  <div>
                    <h3 className="text-lg font-bold text-white">Image Generation</h3>
                    <p className="text-xs text-[#565f89]">SDXL, Flux, Z-Image</p>
                  </div>
                </div>
                <code className="text-xs text-[#7dcfff] block mb-4">/generate cyberpunk cat with neon lights</code>
                <div className="flex gap-2">
                  <span className="text-[8px] bg-[#7dcfff]/10 px-2 py-1 rounded text-[#7dcfff]">--width 1024</span>
                  <span className="text-[8px] bg-[#7dcfff]/10 px-2 py-1 rounded text-[#7dcfff]">--height 768</span>
                  <span className="text-[8px] bg-[#7dcfff]/10 px-2 py-1 rounded text-[#7dcfff]">--steps 30</span>
                </div>
              </div>
              <div className="bg-[#0a0a0c] border border-white/[0.05] rounded-xl p-6">
                <div className="flex items-center gap-3 mb-4">
                  <Video className="w-8 h-8 text-[#9B72CB]" />
                  <div>
                    <h3 className="text-lg font-bold text-white">Video Generation</h3>
                    <p className="text-xs text-[#565f89]">AnimateDiff, SVD</p>
                  </div>
                </div>
                <code className="text-xs text-[#9B72CB] block mb-4">/video cat running in cyberpunk city</code>
                <div className="flex gap-2">
                  <span className="text-[8px] bg-[#9B72CB]/10 px-2 py-1 rounded text-[#9B72CB]">--frames 16</span>
                  <span className="text-[8px] bg-[#9B72CB]/10 px-2 py-1 rounded text-[#9B72CB]">--fps 8</span>
                </div>
              </div>
            </div>
            <div className="mt-6 text-center">
              <div className={`inline-flex items-center gap-2 px-4 py-2 rounded-full ${comfyuiStatus === 'online' ? 'bg-[#9ece6a]/10 border border-[#9ece6a]/20' : 'bg-[#f7768e]/10 border border-[#f7768e]/20'}`}>
                <div className={`w-2 h-2 rounded-full ${comfyuiStatus === 'online' ? 'bg-[#9ece6a]' : 'bg-[#f7768e]'}`} />
                <span className="text-xs font-mono">ComfyUI: {comfyuiStatus === 'online' ? 'Connected' : 'Not Running'}</span>
                {comfyuiStatus !== 'online' && (
                  <button onClick={checkComfyUI} className="text-[10px] text-[#7dcfff] hover:underline ml-2">Retry</button>
                )}
              </div>
            </div>
          </div>
        </section>

        {/* AUDIT SECTION */}
        <section id="audit" className="scroll-mt-20 py-20 px-8 border-t border-[#7dcfff]/10 bg-gradient-to-b from-transparent to-black/20">
          <div className="max-w-6xl mx-auto">
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-[#9ece6a]/10 border border-[#9ece6a]/20 mb-4">
              <FileCheck className="w-4 h-4 text-[#9ece6a]" />
              <span className="text-xs font-mono text-[#9ece6a]">DRIFT CHAIN AUDIT</span>
            </div>
            <h2 className="text-3xl font-bold text-white mb-4">Immutable Proof of Action</h2>
            <p className="text-[#565f89] mb-8 max-w-2xl">
              Every decision. Every generation. Every constitution check. Cryptographically signed.
            </p>
            <div className="bg-[#0a0a0c] border border-white/[0.05] rounded-xl p-6 font-mono text-xs">
              <div className="text-[#9ece6a] mb-4">DRIFT CHAIN â€” {driftLock ? 'ACTIVE' : '70+ EVENTS'}</div>
              <div className="space-y-2 max-h-48 overflow-y-auto">
                <div className="flex items-center gap-2">
                  <div className="w-2 h-2 rounded-full bg-[#9ece6a]"></div>
                  <span className="text-white">0x7f3e... ComfyUIWorker GENERATE (APPROVED)</span>
                </div>
                <div className="flex items-center gap-2">
                  <div className="w-2 h-2 rounded-full bg-[#9ece6a]"></div>
                  <span className="text-white">0xa1b2... CodeGenWorker EXECUTE (APPROVED)</span>
                </div>
                <div className="flex items-center gap-2">
                  <div className="w-2 h-2 rounded-full bg-[#9ece6a]"></div>
                  <span className="text-white">0xc4d5... MemoryWorker STORE (APPROVED)</span>
                </div>
              </div>
              <div className="mt-4 pt-4 border-t border-white/[0.05] text-[#565f89]">
                Integrity Score: {govScore}.2%
              </div>
            </div>
          </div>
        </section>

        {/* DOCS SECTION */}
        <section id="docs" className="scroll-mt-20 py-20 px-8 border-t border-[#7dcfff]/10 bg-gradient-to-b from-transparent to-black/20">
          <div className="max-w-6xl mx-auto">
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-[#9ece6a]/10 border border-[#9ece6a]/20 mb-4">
              <BookOpen className="w-4 h-4 text-[#9ece6a]" />
              <span className="text-xs font-mono text-[#9ece6a]">WHITEPAPER</span>
            </div>
            <h2 className="text-3xl font-bold text-white mb-4">The Sovereign Constitution</h2>
            <p className="text-[#565f89] mb-8 max-w-2xl">
              Complete architectural specification of RezHive. From root seed to sovereign OS.
            </p>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              <div className="bg-[#0a0a0c] border border-white/[0.05] rounded-xl p-6 hover:border-[#9ece6a]/30 transition-all">
                <FileText className="w-8 h-8 text-[#9ece6a] mb-3" />
                <h3 className="text-lg font-bold text-white mb-2">Technical Whitepaper</h3>
                <p className="text-xs text-[#565f89] mb-4">Complete architecture specification: SCE Protocol, Swarm Intelligence, Constitutional Enforcement.</p>
                <button className="text-xs text-[#9ece6a] flex items-center gap-1">Download PDF â†’</button>
              </div>
              <div className="bg-[#0a0a0c] border border-white/[0.05] rounded-xl p-6 hover:border-[#9ece6a]/30 transition-all">
                <Cpu className="w-8 h-8 text-[#9ece6a] mb-3" />
                <h3 className="text-lg font-bold text-white mb-2">Quick Start Guide</h3>
                <p className="text-xs text-[#565f89] mb-4">Get your sovereign AI system running in 10 minutes. Install, configure, deploy.</p>
                <button className="text-xs text-[#9ece6a] flex items-center gap-1">Read Guide â†’</button>
              </div>
              <div className="bg-[#0a0a0c] border border-white/[0.05] rounded-xl p-6 hover:border-[#9ece6a]/30 transition-all">
                <GitBranch className="w-8 h-8 text-[#9ece6a] mb-3" />
                <h3 className="text-lg font-bold text-white mb-2">ComfyUI Integration</h3>
                <p className="text-xs text-[#565f89] mb-4">Connect ComfyUI workflows to Phoenix. Generate images and videos with constitutional oversight.</p>
                <button className="text-xs text-[#9ece6a] flex items-center gap-1">View API â†’</button>
              </div>
            </div>
          </div>
        </section>

        <div className="h-20"></div>
      </div>

      <style jsx global>{`
        .custom-scrollbar::-webkit-scrollbar { width: 4px; }
        .custom-scrollbar::-webkit-scrollbar-track { background: rgba(125,207,255,0.05); border-radius: 10px; }
        .custom-scrollbar::-webkit-scrollbar-thumb { background: rgba(125,207,255,0.3); border-radius: 10px; }
        textarea::-webkit-scrollbar { display: none; }
        ::-webkit-scrollbar { width: 6px; height: 6px; }
        ::-webkit-scrollbar-track { background: rgba(125,207,255,0.05); }
        ::-webkit-scrollbar-thumb { background: rgba(125,207,255,0.3); border-radius: 3px; }
        ::-webkit-scrollbar-thumb:hover { background: rgba(125,207,255,0.5); }
      `}</style>
    </div>
  );
}


