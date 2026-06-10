// frontend/src/components/ConfidenceMeter.tsx
import { motion } from 'framer-motion';

interface ConfidenceMeterProps {
  confidence?: number;
}

export default function ConfidenceMeter({ confidence = 0.85 }: ConfidenceMeterProps) {
  const segments = 10;
  const activeSegments = Math.round(confidence * segments);

  return (
    <div className="bg-[#0E1015]/90 backdrop-blur-md border border-[#1F222A] rounded-xl p-5 shadow-[0_8px_30px_rgba(0,0,0,0.5)]">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2 text-xs font-bold tracking-[0.15em] uppercase text-white">
          <div className="text-[#10b981]">⚖</div> Consensus Certainty
        </div>
        <span className="text-xs font-mono text-[#10b981]">{(confidence * 100).toFixed(1)}%</span>
      </div>
      
      <div className="flex gap-1 h-3 w-full">
        {Array.from({ length: segments }).map((_, i) => (
          <motion.div
            key={i}
            className="flex-1 rounded-sm border border-[#1F222A]"
            initial={{ backgroundColor: '#12141A' }}
            animate={{ 
              backgroundColor: i < activeSegments ? '#10b981' : '#12141A',
              boxShadow: i < activeSegments ? '0 0 8px rgba(16,185,129,0.4)' : 'none'
            }}
            transition={{ duration: 0.5, delay: i * 0.05 }}
          />
        ))}
      </div>
    </div>
  );
}