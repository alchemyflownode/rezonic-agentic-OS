// src/components/LoadingIndicator.tsx
'use client';

import clsx from 'clsx';

type LoadingIndicatorProps = {
  size?: 'sm' | 'md' | 'lg';
  color?: string;
  className?: string;
};

export const LoadingIndicator = ({
  size = 'md',
  color = 'bg-cyan-400',
  className,
}: LoadingIndicatorProps) => {
  const sizeMap = {
    sm: 'w-1.5 h-1.5',
    md: 'w-2 h-2',
    lg: 'w-3 h-3',
  };

  return (
    <div className={clsx('flex items-center gap-1', className)}>
      {[0, 0.15, 0.3].map((delay, i) => (
        <div
          key={i}
          className={clsx(
            sizeMap[size],
            color,
            'rounded-full animate-pulse'
          )}
          style={{
            animationDelay: `${delay}s`,
          }}
        />
      ))}
    </div>
  );
};