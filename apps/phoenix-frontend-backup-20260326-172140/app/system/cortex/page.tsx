// app/system/cortex/page.tsx
'use client';

import { motion } from 'framer-motion';
import { Database, Activity, Cpu, Zap, Brain, ShieldCheck, Clock } from 'lucide-react';

export default function CortexPage() {
  const [blueprintCount] = useState(11593);
  const [activeWorkers] = useState(56);

  return (
    <div className="min-h-screen bg-gradient-to-br from-[#0a0a0c] via-[#050505] to-[#0a0a0c] p-8">
      {/* Animated Background */}
      <div className="fixed inset-0 pointer-events-none opacity-20">
        <div className="absolute inset-0 bg-[radial-gradient(circle_at_50%_50%,_#7dcfff_0%,_transparent_50%)] opacity-5" />
        <div className="absolute inset-0" style={{ backgroundImage: 'linear-gradient(to right, #7dcfff0a 1px, transparent 1px), linear-gradient(to bottom, #7dcfff0a 1px, transparent 1px)', backgroundSize: '40px 40px' }} />
      </div>

      <div className="relative z-10 max-w-6xl mx-auto">
        <motion.div
          initial={{ y: -20, opacity: 0 }}
          animate={{ y: 0, opacity: 1 }}
          className="mb-8"
        >
          <div className="flex items-center gap-4">
            <div className="w-12 h-12 rounded-2xl bg-gradient-to-br from-[#9B72CB]/20 to-[#7dcfff]/20 border border-[#9B72CB]/30 flex items-center justify-center">
              <Database className="w-6 h-6 text-[#9B72CB]" />
            </div>
            <div>
              <h1 className="text-3xl font-bold bg-gradient-to-r from-[#c0caf5] to-[#9B72CB] bg-clip-text text-transparent">
                CORTEX MEMORY
              </h1>
              <p className="text-[#565f89] mt-1">Sovereign Memory Architecture • SCE Protocol</p>
            </div>
          </div>
        </motion.div>

        {/* Stats Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
          <motion.div
            initial={{ y: 20, opacity: 0 }}
            animate={{ y: 0, opacity: 1 }}
            transition={{ delay: 0.1 }}
            className="bg-black/30 backdrop-blur-xl border border-[#7dcfff]/10 rounded-xl p-4"
          >
            <div className="flex items-center gap-2 mb-2">
              <Database className="w-4 h-4 text-[#9B72CB]" />
              <span className="text-[10px] text-[#565f89] uppercase">Blueprints</span>
            </div>
            <div className="text-2xl font-bold text-white">{blueprintCount.toLocaleString()}</div>
            <div className="text-[8px] text-[#9ece6a] mt-1">↑ 127 this week</div>
          </motion.div>

          <motion.div
            initial={{ y: 20, opacity: 0 }}
            animate={{ y: 0, opacity: 1 }}
            transition={{ delay: 0.2 }}
            className="bg-black/30 backdrop-blur-xl border border-[#7dcfff]/10 rounded-xl p-4"
          >
            <div className="flex items-center gap-2 mb-2">
              <Brain className="w-4 h-4 text-[#7dcfff]" />
              <span className="text-[10px] text-[#565f89] uppercase">Active Workers</span>
            </div>
            <div className="text-2xl font-bold text-white">{activeWorkers}</div>
            <div className="text-[8px] text-[#9ece6a] mt-1">56 total workers</div>
          </motion.div>

          <motion.div
            initial={{ y: 20, opacity: 0 }}
            animate={{ y: 0, opacity: 1 }}
            transition={{ delay: 0.3 }}
            className="bg-black/30 backdrop-blur-xl border border-[#7dcfff]/10 rounded-xl p-4"
          >
            <div className="flex items-center gap-2 mb-2">
              <ShieldCheck className="w-4 h-4 text-[#9ece6a]" />
              <span className="text-[10px] text-[#565f89] uppercase">SCE Integrity</span>
            </div>
            <div className="text-2xl font-bold text-[#9ece6a]">98.2%</div>
            <div className="text-[8px] text-[#565f89] mt-1">Constitutional Verified</div>
          </motion.div>

          <motion.div
            initial={{ y: 20, opacity: 0 }}
            animate={{ y: 0, opacity: 1 }}
            transition={{ delay: 0.4 }}
            className="bg-black/30 backdrop-blur-xl border border-[#7dcfff]/10 rounded-xl p-4"
          >
            <div className="flex items-center gap-2 mb-2">
              <Clock className="w-4 h-4 text-[#ff9e64]" />
              <span className="text-[10px] text-[#565f89] uppercase">Last Sync</span>
            </div>
            <div className="text-2xl font-bold text-white">Now</div>
            <div className="text-[8px] text-[#565f89] mt-1">Real-time</div>
          </motion.div>
        </div>

        {/* Memory Visualization */}
        <motion.div
          initial={{ y: 20, opacity: 0 }}
          animate={{ y: 0, opacity: 1 }}
          transition={{ delay: 0.5 }}
          className="bg-black/30 backdrop-blur-xl border border-[#7dcfff]/10 rounded-2xl p-6"
        >
          <div className="flex items-center gap-2 mb-6">
            <Activity className="w-4 h-4 text-[#7dcfff]" />
            <h2 className="text-sm font-bold text-white">Memory Architecture</h2>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="p-4 bg-white/5 rounded-xl border border-white/10">
              <div className="text-[10px] text-[#7dcfff] mb-2">Semantic Memory</div>
              <div className="text-2xl font-bold text-white">8,234</div>
              <div className="text-[8px] text-[#565f89] mt-1">Knowledge embeddings</div>
            </div>
            <div className="p-4 bg-white/5 rounded-xl border border-white/10">
              <div className="text-[10px] text-[#9B72CB] mb-2">Episodic Memory</div>
              <div className="text-2xl font-bold text-white">2,847</div>
              <div className="text-[8px] text-[#565f89] mt-1">Interaction records</div>
            </div>
            <div className="p-4 bg-white/5 rounded-xl border border-white/10">
              <div className="text-[10px] text-[#9ece6a] mb-2">Procedural Memory</div>
              <div className="text-2xl font-bold text-white">512</div>
              <div className="text-[8px] text-[#565f89] mt-1">Learned patterns</div>
            </div>
          </div>
        </motion.div>
      </div>
    </div>
  );
}