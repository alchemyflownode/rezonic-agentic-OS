'use client';
import { Send, Terminal, Sparkles } from 'lucide-react';

export function ChatArea() {
  return (
    <div className="flex-1 flex flex-col bg-[#030405] relative">
      {/* Neural Header */}
      <div className="h-14 border-b border-[#1E293B] flex items-center justify-between px-6 bg-[#030405]/80 backdrop-blur-md sticky top-0 z-10">
        <div className="flex items-center gap-2">
          <Terminal size={16} className="text-[#2DD4BF]" />
          <span className="text-sm font-medium text-slate-300">Sovereign Chat</span>
        </div>
        <div className="flex items-center gap-4 text-[10px] text-slate-500">
          <span>Latency: <span className="text-[#2DD4BF]">12ms</span></span>
          <span>Bus Status: <span className="text-green-500">Connected</span></span>
        </div>
      </div>

      {/* Messages Area */}
      <div className="flex-1 p-8 space-y-6 overflow-y-auto">
        <div className="max-w-3xl mx-auto space-y-6">
          <div className="bg-[#0B0C0E] border border-[#1E293B] rounded-2xl p-4 text-slate-300 text-sm">
            Welcome to Sovereign. Neural Bus is active. 28 specialized workers are standing by.
          </div>
        </div>
      </div>

      {/* Input - Fixed to Bottom */}
      <div className="p-6 bg-gradient-to-t from-[#030405] to-transparent">
        <div className="max-w-3xl mx-auto relative group">
          <input 
            type="text" 
            placeholder="Issue command to Sovereign..."
            className="w-full bg-[#0B0C0E] border border-[#1E293B] group-focus-within:border-[#2DD4BF] rounded-2xl px-6 py-4 text-slate-200 outline-none transition-all pr-14"
          />
          <button className="absolute right-4 top-1/2 -translate-y-1/2 p-2 bg-[#2DD4BF]/10 text-[#2DD4BF] rounded-xl hover:bg-[#2DD4BF] hover:text-black transition-all">
            <Send size={18} />
          </button>
        </div>
      </div>
    </div>
  );
}
