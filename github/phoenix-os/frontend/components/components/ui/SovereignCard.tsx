'use client';

import { motion } from 'framer-motion';
import { ReactNode } from 'react';

interface SovereignCardProps {
  children: ReactNode;
  className?: string;
  variant?: 'default' | 'glass' | 'outline' | 'gradient';
  glowColor?: string;
  onClick?: () => void;
}

const variantStyles = {
  default: 'bg-gradient-to-br from-[#0E1015]/90 to-[#1A1D24]/90 border-[#2A2E38]',
  glass: 'bg-[#0E1015]/40 backdrop-blur-xl border border-white/5',
  outline: 'bg-transparent border-2 border-[#2A2E38]',
  gradient: 'bg-gradient-to-r from-[#00E5FF]/10 to-[#B388FF]/10 border-[#00E5FF]/20'
};

export const SovereignCard = ({ 
  children, 
  className = '', 
  variant = 'default',
  glowColor = '#00E5FF',
  onClick 
}: SovereignCardProps) => {
  return (
    <motion.div
      whileHover={{ scale: variant === 'glass' ? 1.01 : 1.02 }}
      transition={{ type: "spring", stiffness: 300, damping: 20 }}
      className={\
        rounded-xl p-6
        backdrop-blur-md shadow-[0_8px_30px_rgba(0,0,0,0.5)]
        hover:shadow-[0_0_20px_\20]
        transition-all duration-300
        \
        \
      \}
      onClick={onClick}
    >
      {children}
    </motion.div>
  );
};

export default SovereignCard;
