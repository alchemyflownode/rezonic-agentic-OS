'use client';

import React from 'react';

interface SkeletonProps {
  className?: string;
  count?: number;
}

export const LoadingSkeleton: React.FC<SkeletonProps> = ({ className = '', count = 1 }) => {
  return (
    <>
      {Array.from({ length: count }).map((_, i) => (
        <div
          key={i}
          className={`skeleton-premium rounded ${className}`}
          style={{ height: '1rem' }}
        />
      ))}
    </>
  );
};

export const MetricCardSkeleton = () => (
  <div className="premium-card p-6 space-y-3">
    <div className="skeleton-premium h-4 w-20 rounded" />
    <div className="skeleton-premium h-8 w-32 rounded" />
    <div className="skeleton-premium h-1.5 w-full rounded" />
  </div>
);

export const ChatMessageSkeleton = () => (
  <div className="flex gap-3">
    <div className="skeleton-premium w-8 h-8 rounded-lg" />
    <div className="flex-1 space-y-2">
      <div className="skeleton-premium h-4 w-32 rounded" />
      <div className="skeleton-premium h-16 w-full rounded" />
    </div>
  </div>
);
