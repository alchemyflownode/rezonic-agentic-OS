'use client';
import { cn } from '@/lib/utils';
import { Fingerprint } from 'lucide-react';
import { useEffect, useState } from 'react';

interface ProofBadgeProps {
  proof?: string;
  status?: 'verified' | 'verifying' | 'active';
  className?: string;
}

export const ProofBadge: React.FC<ProofBadgeProps> = ({
  proof = '0x7A3F_REZNIC',
  status = 'verified',
  className
}) => {
  const [hash, setHash] = useState(proof);

  useEffect(() => {
    // Regenerate proof every 30 seconds (simulates state change)
    const interval = setInterval(() => {
      const newHash = '0x' + Math.floor(Math.random() * 0xFFFFFF).toString(16).toUpperCase().slice(0,4) + '_REZNIC';
      setHash(newHash);
    }, 30000);
    return () => clearInterval(interval);
  }, []);

  const statusColors = {
    verified: 'text-[var(--accent-cyan)]',
    verifying: 'text-[var(--accent-amber)]',
    active: 'text-[var(--accent-cyan)]'
  };

  const statusDots = {
    verified: 'bg-[var(--accent-cyan)]',
    verifying: 'bg-[var(--accent-amber)] animate-pulse',
    active: 'bg-[var(--accent-cyan)] animate-pulse'
  };

  return (
    <div className={cn(
      'fixed top-4 right-4 z-50',
      'bg-[rgba(18,18,20,0.7)] backdrop-blur-xl',
      'border border-white/5 rounded-[4px]',
      'px-4 py-2',
      'flex items-center gap-3',
      className
    )}>
      <Fingerprint size={14} className={statusColors[status]} />
      <div>
        <div className="text-[8px] font-mono text-white/30 tracking-wider mb-0.5">
          REZONIC_PROOF
        </div>
        <div className={cn('text-[10px] font-mono tracking-wider', statusColors[status])}>
          {hash}
        </div>
      </div>
      <div className="flex items-center gap-1 ml-2">
        <span className={cn('w-1.5 h-1.5 rounded-full', statusDots[status])} />
        <span className={cn('text-[8px] font-mono', statusColors[status])}>
          {status.toUpperCase()}
        </span>
      </div>
    </div>
  );
};

