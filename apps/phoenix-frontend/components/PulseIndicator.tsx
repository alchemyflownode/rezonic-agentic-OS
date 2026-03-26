'use client';

interface PulseIndicatorProps {
  status?: 'online' | 'processing' | 'idle';
  size?: 'sm' | 'md' | 'lg';
  showLabel?: boolean;
}

export function PulseIndicator({ 
  status = 'online', 
  size = 'md',
  showLabel = false 
}: PulseIndicatorProps) {
  
  const sizeMap = {
    sm: 'w-1.5 h-1.5',
    md: 'w-2 h-2',
    lg: 'w-2.5 h-2.5'
  };
  
  const statusMap = {
    online: 'bg-green-success shadow-[0_0_10px_rgba(34,197,94,0.5)]',
    processing: 'bg-cyan-primary shadow-[0_0_10px_rgba(45,212,191,0.5)] animate-pulse-cyan',
    idle: 'bg-text-tertiary'
  };
  
  const labelMap = {
    online: 'Online',
    processing: 'Processing',
    idle: 'Idle'
  };
  
  return (
    <div className="flex items-center gap-2">
      <div className={`${sizeMap[size]} rounded-full ${statusMap[status]}`} />
      {showLabel && (
        <span className="text-xs text-text-muted">{labelMap[status]}</span>
      )}
    </div>
  );
}
