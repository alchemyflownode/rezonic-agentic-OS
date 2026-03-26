'use client';

import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';

interface SimulationControlsProps {
  onRunSimulation: (episodes: number) => void;
  onLoadPolicy: () => void;
  isTraining: boolean;
}

export default function SimulationControls({ 
  onRunSimulation, 
  onLoadPolicy,
  isTraining 
}: SimulationControlsProps) {
  
  const[episodes, setEpisodes] = useState(1000);
  const [showControls, setShowControls] = useState(false);

  return (
    <div className="fixed bottom-24 right-6 z-50">
      <motion.div
        initial={{ scale: 0 }}
        animate={{ scale: 1 }}
        className="relative"
      >
        {/* Main Toggle Button */}
        <button
          onClick={() => setShowControls(!showControls)}
          className={`w-14 h-14 rounded-full border flex items-center justify-center shadow-[0_0_20px_rgba(0,0,0,0.5)] transition-all duration-300 ${
            showControls 
              ? 'bg-[#00E5FF]/20 border-[#00E5FF] text-[#00E5FF]' 
              : 'bg-[#0E1015] border-[#2A2E38] text-[#00E5FF] hover:border-[#00E5FF]/50'
          }`}
          title="Agamoto-X Simulation Dashboard"
        >
          <span className="text-2xl">🎯</span>
        </button>

        {/* Controls Panel */}
        <AnimatePresence>
          {showControls && (
            <motion.div
              initial={{ opacity: 0, y: 10, scale: 0.95 }}
              animate={{ opacity: 1, y: 0, scale: 1 }}
              exit={{ opacity: 0, y: 10, scale: 0.95 }}
              className="absolute bottom-20 right-0 w-80 bg-[#0E1015]/95 backdrop-blur-xl border border-[#2A2E38] rounded-xl shadow-2xl overflow-hidden"
            >
              <div className="p-4 border-b border-[#1F222A] bg-[#0A0C10] flex items-center gap-2">
                <div className="w-2 h-2 bg-[#FF9800] rounded-full animate-pulse shadow-[0_0_8px_#FF9800]" />
                <h3 className="text-sm font-bold text-white uppercase tracking-[0.15em]">
                  Agamoto-X Simulator
                </h3>
              </div>

              <div className="p-5 space-y-5">
                {/* Training Controls */}
                <div>
                  <label className="block text-[10px] font-mono text-[#8A8F9B] mb-3 uppercase tracking-wider">
                    RL Training Episodes
                  </label>
                  <input
                    type="range"
                    min="100"
                    max="10000"
                    step="100"
                    value={episodes}
                    onChange={(e) => setEpisodes(parseInt(e.target.value))}
                    className="w-full h-1 bg-[#1A1D24] rounded-lg appearance-none cursor-pointer accent-[#00E5FF]"
                  />
                  <div className="flex justify-between mt-2 text-[10px] font-mono text-[#4B5563]">
                    <span>100</span>
                    <span className="text-[#00E5FF] drop-shadow-[0_0_5px_rgba(0,229,255,0.5)]">{episodes.toLocaleString()}</span>
                    <span>10k</span>
                  </div>
                </div>

                {/* Action Buttons */}
                <div className="space-y-3">
                  <button
                    onClick={() => onRunSimulation(episodes)}
                    disabled={isTraining}
                    className="w-full py-3 bg-gradient-to-r from-[#00E5FF]/10 to-transparent border border-[#00E5FF]/30 rounded-lg text-[#00E5FF] text-xs font-mono uppercase tracking-widest hover:bg-[#00E5FF] hover:text-black hover:shadow-[0_0_15px_rgba(0,229,255,0.4)] transition-all disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    {isTraining ? (
                      <span className="flex items-center justify-center gap-2">
                        <span className="w-3.5 h-3.5 border-2 border-[#00E5FF] border-t-transparent rounded-full animate-spin" />
                        TRAINING...
                      </span>
                    ) : (
                      '▶ RUN SIMULATION'
                    )}
                  </button>

                  <button
                    onClick={onLoadPolicy}
                    className="w-full py-3 bg-[#12141A] border border-[#2A2E38] rounded-lg text-[#8A8F9B] text-xs font-mono uppercase tracking-widest hover:text-white hover:border-[#10b981] hover:bg-[#10b981]/5 transition-all"
                  >
                    📥 LOAD POLICY
                  </button>
                </div>

                {/* Security Note */}
                <div className="bg-[#FF4500]/10 border border-[#FF4500]/20 rounded-lg p-3">
                  <div className="flex items-start gap-2">
                    <span className="text-[#FF4500] text-sm">⚠️</span>
                    <p className="text-[9px] text-[#FF4500] font-mono leading-relaxed uppercase tracking-wider">
                      Policy files alter core execution routing. Verify integrity before load.
                    </p>
                  </div>
                </div>
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </motion.div>
    </div>
  );
}