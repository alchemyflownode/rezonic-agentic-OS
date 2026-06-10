"use client";
import { motion } from 'framer-motion';

export const KineticTool = ({ 
  children, 
  onClick, 
  active = false,
  hint
}: { 
  children: React.ReactNode; 
  onClick: () => void;
  active?: boolean;
  hint?: string;
}) => (
  <motion.button
    onClick={onClick}
    className={`
      relative flex items-center justify-center
      w-9 h-9 rounded-[6px]
      transition-colors duration-100
      ${active 
        ? 'bg-[#0D99FF] text-white shadow-[0_0_15px_rgba(13,153,255,0.3)]' 
        : 'text-white/40 hover:text-white hover:bg-white/5'
      }
    `}
    whileHover={{ scale: 1.05 }}
    whileTap={{ scale: 0.95 }}
  >
    {children}
    
    {/* Hint (Tooltip) */}
    {hint && (
      <div className="
        absolute left-full ml-2 px-2 py-1 
        bg-[#323232] text-white text-[10px] rounded
        opacity-0 group-hover:opacity-100 pointer-events-none
        whitespace-nowrap z-50
      ">
        {hint}
      </div>
    )}
    
    {/* Active Glow Ring */}
    {active && (
      <motion.div 
        className="absolute inset-0 rounded-[6px] border border-[#0D99FF]/50"
        animate={{ opacity: [0.5, 1, 0.5] }}
        transition={{ duration: 2, repeat: Infinity }}
      />
    )}
  </motion.button>
);
