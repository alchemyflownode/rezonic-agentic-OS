'use client';

import { motion, AnimatePresence } from 'framer-motion';

interface ThinkingIndicatorProps {
  isThinking: boolean;
  variant?: 'dots' | 'neural' | 'minimal' | 'avatar';
  worker?: string;
  message?: string;
}

export function ThinkingIndicator({ 
  isThinking, 
  variant = 'dots',
  worker,
  message = 'AI is thinking...'
}: ThinkingIndicatorProps) {
  
  if (!isThinking) return null;
  
  // Dots variant (classic)
  if (variant === 'dots') {
    return (
      <motion.div
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        exit={{ opacity: 0, y: -10 }}
        className="thinking-dots"
      >
        <div className="dot" />
        <div className="dot" />
        <div className="dot" />
        {worker && (
          <span className="text-xs text-text-tertiary ml-2">{worker} working...</span>
        )}
      </motion.div>
    );
  }
  
  // Neural pulse variant (modern)
  if (variant === 'neural') {
    return (
      <motion.div
        initial={{ opacity: 0, scale: 0.9 }}
        animate={{ opacity: 1, scale: 1 }}
        exit={{ opacity: 0, scale: 0.9 }}
        className="neural-pulse"
      >
        <div className="pulse-dot" />
        <span className="pulse-text">{message}</span>
        {worker && <span className="text-[10px] text-text-tertiary">• {worker}</span>}
      </motion.div>
    );
  }
  
  // Minimal variant (processing bar)
  if (variant === 'minimal') {
    return (
      <div className="space-y-1 w-full">
        <div className="flex justify-between text-xs text-text-tertiary">
          <span>{message}</span>
          {worker && <span>{worker}</span>}
        </div>
        <div className="processing-bar">
          <div className="bar-fill" />
        </div>
      </div>
    );
  }
  
  // Avatar variant (for chat)
  if (variant === 'avatar') {
    return (
      <div className="flex items-center gap-3">
        <div className="thinking-avatar">
          <div className="avatar-ring" />
          <div className="avatar-glow" />
        </div>
        <div>
          <div className="text-sm text-text-secondary">{message}</div>
          {worker && (
            <div className="worker-activity mt-1">
              <span className="worker-status" />
              <span className="worker-name">{worker}</span>
            </div>
          )}
        </div>
      </div>
    );
  }
  
  return null;
}
