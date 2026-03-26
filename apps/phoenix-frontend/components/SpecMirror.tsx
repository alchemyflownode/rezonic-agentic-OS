'use client';

import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Copy, Download, FileText, Check, Zap } from 'lucide-react';

interface SpecMirrorProps {
  content?: string;
  isConverging?: boolean;
  onConverge?: () => void;
}

export function SpecMirror({ content, isConverging = false, onConverge }: SpecMirrorProps) {
  const [showReveal, setShowReveal] = useState(false);
  const [copied, setCopied] = useState(false);
  const [activeLayer, setActiveLayer] = useState(1);

  useEffect(() => {
    if (isConverging) {
      setShowReveal(true);
      setTimeout(() => {
        setShowReveal(false);
        onConverge?.();
      }, 800);
    }
  }, [isConverging, onConverge]);

  const handleCopy = () => {
    navigator.clipboard.writeText(content || '');
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="relative">
      {/* Spec Mirror Container */}
      <div className={`spec-mirror ${showReveal ? 'convergence-reveal' : ''}`}>
        {/* Metadata Ribbon */}
        <div className="metadata-ribbon" />
        
        {/* Document Content */}
        <div className="p-8">
          {/* Header */}
          <div className="flex items-center justify-between mb-8">
            <div>
              <h2 className="spec-header">SPECIFICATION MIRROR</h2>
              <p className="text-xs text-white/30 mt-1">
                High-Fidelity Document • v3.1.2
              </p>
            </div>
            
            {/* Normalization Stats */}
            <div className="flex items-center gap-4">
              <div className="flex items-center">
                <span className="stat-glow cyan" />
                <span className="text-xs text-white/50">98.2%</span>
              </div>
              <div className="flex items-center">
                <span className="stat-glow purple" />
                <span className="text-xs text-white/50">87.3%</span>
              </div>
            </div>
          </div>

          {/* Document Layers */}
          <div className="space-y-6">
            {/* Layer 1 - Parameters */}
            <motion.div 
              className="document-layer layer-1"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.1 }}
            >
              <div className="spec-header mb-4">PARAMETERS</div>
              <div className="grid grid-cols-2 gap-3">
                <div className="physical-chip recessed">
                  <span className="text-white/40 text-[10px] block">APEX</span>
                  <span className="text-[#00FFC2] text-sm">87.3%</span>
                </div>
                <div className="physical-chip recessed">
                  <span className="text-white/40 text-[10px] block">CLARITY</span>
                  <span className="text-[#00FFC2] text-sm">98.2%</span>
                </div>
                <div className="physical-chip recessed">
                  <span className="text-white/40 text-[10px] block">SYNTH</span>
                  <span className="text-[#00FFC2] text-sm">ACTIVE</span>
                </div>
                <div className="physical-chip recessed">
                  <span className="text-white/40 text-[10px] block">NEXUS</span>
                  <span className="text-[#FFB800] text-sm">LOCKED</span>
                </div>
              </div>
            </motion.div>

            {/* Layer 2 - Generated Specification */}
            <motion.div 
              className="document-layer layer-2"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.2 }}
            >
              <div className="spec-header mb-4">GENERATED SPECIFICATION</div>
              <div className="spec-content">
                {content ? (
                  <pre className="whitespace-pre-wrap">{content}</pre>
                ) : (
                  <div className="space-y-2">
                    <p className="text-white/40 italic">
                      {isConverging 
                        ? 'Converging specification...' 
                        : 'Awaiting synthesis parameters...'}
                    </p>
                  </div>
                )}
              </div>
            </motion.div>

            {/* Layer 3 - Analysis */}
            <motion.div 
              className="document-layer"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.3 }}
            >
              <div className="spec-header mb-4">ANALYSIS</div>
              <div className="flex items-center gap-4 text-sm">
                <div className="flex items-center gap-2">
                  <Zap className="w-4 h-4 text-[#00FFC2]" />
                  <span className="text-white/70">Convergence Apex</span>
                </div>
                <div className="physical-chip">
                  +23.4%
                </div>
              </div>
            </motion.div>
          </div>

          {/* Haptic Action Bar */}
          <div className="flex justify-center mt-8">
            <motion.div
              className="haptic-bar"
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.4 }}
            >
              <button 
                className="haptic-button primary"
                onClick={handleCopy}
              >
                {copied ? (
                  <span className="flex items-center gap-1">
                    <Check className="w-4 h-4" /> Copied
                  </span>
                ) : (
                  <span className="flex items-center gap-1">
                    <Copy className="w-4 h-4" /> Copy Specification
                  </span>
                )}
              </button>
              <button className="haptic-button">
                <span className="flex items-center gap-1">
                  <Download className="w-4 h-4" /> Export
                </span>
              </button>
              <button className="haptic-button">
                <span className="flex items-center gap-1">
                  <FileText className="w-4 h-4" /> Save
                </span>
              </button>
            </motion.div>
          </div>
        </div>
      </div>

      {/* Active Convergence Indicator */}
      <AnimatePresence>
        {isConverging && (
          <motion.div
            className="absolute inset-0 pointer-events-none flex items-center justify-center"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
          >
            <div className="bg-black/50 backdrop-blur-xl rounded-full px-6 py-3 border border-[#00FFC2]/30">
              <span className="text-[#00FFC2] font-mono text-sm">
                CONVERGING SPECIFICATION...
              </span>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
