// frontend/src/components/EntropyGauge.tsx
import { motion } from 'framer-motion';

interface EntropyGaugeProps {
  entropy?: number;
}

export default function EntropyGauge({ entropy = 0 }: EntropyGaugeProps) {
  const isHigh = entropy > 0.5;
  const color = isHigh ? '#FF4500' : '#00E5FF';

  return (
    <div className="bg-[#0E1015]/90 backdrop-blur-md border border-[#1F222A] rounded-xl p-5 shadow-[0_8px_30px_rgba(0,0,0,0.5)] relative overflow-hidden">
      <div className="flex items-center justify-between mb-4 relative z-10">
        <div className="flex items-center gap-2 text-xs font-bold tracking-[0.15em] uppercase text-white">
          <div className="text-[#00E5FF]">∿</div> Intent Entropy
        </div>
        <span className={`text-xs font-mono font-bold drop-shadow-[0_0_5px_${color}]`} style={{ color }}>
          {entropy.toFixed(3)}
        </span>
      </div>
      
      <div className="relative h-12 w-full flex items-center justify-center">
        {Array.from({ length: 20 }).map((_, i) => (
          <motion.div
            key={i}
            className="absolute rounded-full"
            style={{ backgroundColor: color, width: 4, height: 4 }}
            animate={{
              x: [(Math.random() - 0.5) * 200, (Math.random() - 0.5) * 200],
              y: [(Math.random() - 0.5) * 40, (Math.random() - 0.5) * 40],
              opacity: [0, 0.8, 0],
              scale: [0, Math.random() * (isHigh ? 2 : 1) + 0.5, 0],
            }}
            transition={{
              duration: Math.random() * 2 + 1,
              repeat: Infinity,
              ease: "linear"
            }}
          />
        ))}
      </div>
      <div className="text-[9px] text-[#8A8F9B] text-center uppercase tracking-widest mt-2">
        {isHigh ? 'High Drift Potential' : 'Stable Intent Geometry'}
      </div>
    </div>
  );
}