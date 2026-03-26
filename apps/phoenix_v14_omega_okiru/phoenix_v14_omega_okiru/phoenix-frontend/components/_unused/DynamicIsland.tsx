'use client';

import { useState } from 'react';
import { cn } from '@/lib/utils';
import { motion, AnimatePresence } from 'framer-motion';
import { Brain, Sparkles, FileText, X } from 'lucide-react';
import { GlassCard } from './ui/GlassCard';

interface DynamicIslandProps {
  className?: string;
}

export function DynamicIsland({ className }: DynamicIslandProps) {
  const [isExpanded, setIsExpanded] = useState(false);
  const [isHovered, setIsHovered] = useState(false);

  return (
    <div className={cn(
      'fixed top-6 left-1/2 transform -translate-x-1/2 z-50',
      className
    )}>
      <motion.div
        animate={{ 
          width: isExpanded ? 400 : isHovered ? 200 : 140,
          height: isExpanded ? 120 : 40
        }}
        transition={{ type: "spring", stiffness: 400, damping: 30 }}
      >
        <GlassCard 
          variant="medium" 
          radius="full"
          hover={false}
          glow={isExpanded}
          className="relative overflow-hidden cursor-pointer"
          onMouseEnter={() => setIsHovered(true)}
          onMouseLeave={() => setIsHovered(false)}
          onClick={() => setIsExpanded(!isExpanded)}
        >
          <AnimatePresence mode="wait">
            {!isExpanded ? (
              <motion.div
                key="collapsed"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                className="flex items-center justify-center h-full px-4 gap-2"
              >
                <Brain className="w-3 h-3 text-primary animate-pulse" />
                <span className="text-[10px] font-mono text-white/70 whitespace-nowrap">
                  NEURAL CORE
                </span>
              </motion.div>
            ) : (
              <motion.div
                key="expanded"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                className="p-4 space-y-3"
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <Sparkles className="w-4 h-4 text-primary" />
                    <span className="text-xs font-medium text-white/90">Context Engine</span>
                  </div>
                  <button 
                    onClick={(e) => {
                      e.stopPropagation();
                      setIsExpanded(false);
                    }}
                    className="p-1 hover:bg-white/10 rounded-full"
                  >
                    <X className="w-3 h-3 text-white/50" />
                  </button>
                </div>
                
                <div className="flex items-center gap-2 p-2 bg-white/5 rounded-lg border border-white/5">
                  <FileText className="w-3 h-3 text-white/30" />
                  <span className="text-[10px] text-white/50">Drop files for analysis</span>
                </div>
                
                <div className="flex gap-1">
                  <span className="px-2 py-1 bg-white/5 rounded-full text-[8px] text-white/40">IMAGE</span>
                  <span className="px-2 py-1 bg-white/5 rounded-full text-[8px] text-white/40">AUDIO</span>
                  <span className="px-2 py-1 bg-white/5 rounded-full text-[8px] text-white/40">TEXT</span>
                </div>
              </motion.div>
            )}
          </AnimatePresence>

          {/* Rim light effect */}
          <div className="absolute inset-0 rounded-[inherit] pointer-events-none">
            <div className="absolute inset-x-0 top-0 h-px bg-gradient-to-r from-transparent via-white/20 to-transparent" />
          </div>
        </GlassCard>
      </motion.div>
    </div>
  );
}
