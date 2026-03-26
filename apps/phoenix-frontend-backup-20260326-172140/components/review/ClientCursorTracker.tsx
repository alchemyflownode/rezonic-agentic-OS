'use client';

import { useEffect } from 'react';

export default function ClientCursorTracker() {
  useEffect(() => {
    const updateCursor = (e: MouseEvent) => {
      document.documentElement.style.setProperty('--cursor-x', `${(e.clientX / window.innerWidth) * 100}%`);
      document.documentElement.style.setProperty('--cursor-y', `${(e.clientY / window.innerHeight) * 100}%`);
    };
    
    window.addEventListener('mousemove', updateCursor);
    return () => window.removeEventListener('mousemove', updateCursor);
  }, []);

  // This component doesn't render anything visible
  return (
    <div 
      className="fixed inset-0 pointer-events-none z-0"
      style={{
        background: `radial-gradient(circle at var(--cursor-x, 50%) var(--cursor-y, 50%), rgba(0,255,194,0.03) 0%, transparent 50%)`
      }}
    />
  );
}
