'use client';

import { motion } from 'framer-motion';
import { Repeat, Share2, Upload, Sparkles } from 'lucide-react';

interface ActionButtonsProps {
  variant?: 'default' | 'compact';
}

export function ActionButtons({ variant = 'default' }: ActionButtonsProps) {
  const buttons = [
    { icon: Repeat, label: 'REMIX', color: '#00FFC2' },
    { icon: Share2, label: 'SHARE', color: '#8B5CF6' },
    { icon: Upload, label: 'PUBLISH', color: '#FFB800' },
  ];

  return (
    <motion.div
      className={`flex ${variant === 'compact' ? 'flex-col' : 'flex-row'} gap-2`}
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
    >
      {buttons.map((button, index) => (
        <motion.button
          key={index}
          className={`flex items-center justify-center gap-2 px-4 py-2 rounded-lg border border-white/10 hover:border-[${button.color}] transition-all nexus-panel`}
          whileHover={{ scale: 1.05, y: -2 }}
          whileTap={{ scale: 0.95 }}
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: index * 0.1 }}
        >
          <button.icon className="w-4 h-4" style={{ color: button.color }} />
          <span className="text-xs font-medium">{button.label}</span>
        </motion.button>
      ))}
    </motion.div>
  );
}
