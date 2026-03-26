import React from 'react';

interface InlineCodeProps {
  children: React.ReactNode;
  className?: string;
}

export function InlineCode({ children, className }: InlineCodeProps) {
  return (
    <code 
      className={
        px-1.5 py-0.5 rounded
        bg-white/10 text-[#00E5FF]
        font-mono text-[11px]
        border border-white/10
        
      }
    >
      {children}
    </code>
  );
}
