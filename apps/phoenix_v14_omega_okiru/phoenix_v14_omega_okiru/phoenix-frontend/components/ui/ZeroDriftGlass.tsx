"use client";
import { motion } from 'framer-motion';

export const ZeroDriftGlass = ({ children, className = "" }: { children: React.ReactNode, className?: string }) => (
  <motion.div 
    className={`
      relative overflow-hidden
      bg-[var(--bg-surface)]/70 
      backdrop-blur-[80px] 
      border 
      border-white/[0.02] 
      rounded-[4px] 
      shadow-[0_20px_50px_rgba(0,0,0,0.5)]
      ${className}
    `}
    initial={{ opacity: 0, y: 10 }}
    animate={{ opacity: 1, y: 0 }}
    transition={{ duration: 0.6, ease: [0.19, 1, 0.22, 1] }}
  >
    <div className="absolute inset-x-0 top-0 h-px bg-gradient-to-r from-transparent via-white/[0.07] to-transparent" />
    {children}
  </motion.div>
);

