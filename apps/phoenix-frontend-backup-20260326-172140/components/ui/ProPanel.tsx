"use client";
import { motion } from 'framer-motion';

export const ProPanel = ({ 
  children, 
  title, 
  icon: Icon, 
  className = "" 
}: { 
  children: React.ReactNode; 
  title: string; 
  icon: any;
  className?: string;
}) => (
  <motion.div 
    className={`
      flex flex-col
      rounded-xl overflow-hidden
      pro-glass
      ${className}
    `}
    initial={{ opacity: 0, scale: 0.98 }}
    animate={{ opacity: 1, scale: 1 }}
    transition={{ type: "spring", stiffness: 300, damping: 25 }}
  >
    {/* Panel Header (Adobe Style) */}
    <div className="
      flex items-center gap-2 px-3 h-9 
      border-b border-white/5 
      bg-black/10
    ">
      <Icon className="w-3.5 h-3.5 text-white/40" />
      <span className="text-[11px] font-medium text-white/50 tracking-wide">
        {title.toUpperCase()}
      </span>
    </div>
    
    {/* Content Area */}
    <div className="flex-1 p-2">
      {children}
    </div>
  </motion.div>
);
