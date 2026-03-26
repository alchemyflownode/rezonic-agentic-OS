'use client';
import { motion } from 'framer-motion';
import { cn } from '@/lib/utils';
import { Glass } from './Glass';

interface KineticMetricsProps {
  cpu: number;
  ram: number;
  gpu: number;
  className?: string;
}

export const KineticMetrics: React.FC<KineticMetricsProps> = ({
  cpu,
  ram,
  gpu,
  className
}) => {
  const spring = { type: 'spring', stiffness: 300, damping: 25 };

  return (
    <Glass intensity="thin" className={cn('p-4', className)}>
      <div className="grid grid-cols-3 gap-4">
        {/* CPU */}
        <div>
          <div className="flex items-center justify-between text-[8px] font-mono mb-1">
            <span className="text-white/30">CPU</span>
            <motion.span
              key={cpu}
              initial={false}
              animate={{ opacity: 1 }}
              transition={spring}
              className="text-[var(--accent-cyan)] text-xs"
            >
              {Math.round(cpu)}%
            </motion.span>
          </div>
          <div className="w-full h-px bg-white/10 mb-1" />
          <motion.div
            className="h-[2px] bg-[var(--accent-cyan)]"
            initial={false}
            animate={{ width: `${cpu}%` }}
            transition={spring}
          />
        </div>

        {/* RAM */}
        <div>
          <div className="flex items-center justify-between text-[8px] font-mono mb-1">
            <span className="text-white/30">RAM</span>
            <motion.span
              key={ram}
              initial={false}
              animate={{ opacity: 1 }}
              transition={spring}
              className="text-[var(--accent-cyan)] text-xs"
            >
              {Math.round(ram)}%
            </motion.span>
          </div>
          <div className="w-full h-px bg-white/10 mb-1" />
          <motion.div
            className="h-[2px] bg-[var(--accent-cyan)]"
            initial={false}
            animate={{ width: `${ram}%` }}
            transition={spring}
          />
        </div>

        {/* GPU */}
        <div>
          <div className="flex items-center justify-between text-[8px] font-mono mb-1">
            <span className="text-white/30">GPU</span>
            <motion.span
              key={gpu}
              initial={false}
              animate={{ opacity: 1 }}
              transition={spring}
              className="text-[var(--accent-cyan)] text-xs"
            >
              {Math.round(gpu)}%
            </motion.span>
          </div>
          <div className="w-full h-px bg-white/10 mb-1" />
          <motion.div
            className="h-[2px] bg-[var(--accent-cyan)]"
            initial={false}
            animate={{ width: `${gpu}%` }}
            transition={spring}
          />
        </div>
      </div>
    </Glass>
  );
};

