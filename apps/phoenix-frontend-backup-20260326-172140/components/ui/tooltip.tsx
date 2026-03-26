'use client';

import React, { useState } from 'react';

interface TooltipProps {
  content: string;
  children: React.ReactNode;
  position?: 'top' | 'bottom' | 'left' | 'right';
}

export const Tooltip: React.FC<TooltipProps> = ({ content, children, position = 'top' }) => {
  const [show, setShow] = useState(false);

  const positionClasses = {
    top: 'bottom-full left-1/2 -translate-x-1/2 mb-2',
    bottom: 'top-full left-1/2 -translate-x-1/2 mt-2',
    left: 'right-full top-1/2 -translate-y-1/2 mr-2',
    right: 'left-full top-1/2 -translate-y-1/2 ml-2',
  };

  return (
    <div 
      className="relative inline-block"
      onMouseEnter={() => setShow(true)}
      onMouseLeave={() => setShow(false)}
    >
      {children}
      {show && (
        <div className={`absolute ${positionClasses[position]} z-50 px-2 py-1 text-xs font-mono text-white/90 bg-black/90 backdrop-blur-md border border-white/10 rounded shadow-premium whitespace-nowrap`}>
          {content}
          <div className={`absolute ${
            position === 'top' ? 'bottom-0 left-1/2 -translate-x-1/2 translate-y-1/2 rotate-45' :
            position === 'bottom' ? 'top-0 left-1/2 -translate-x-1/2 -translate-y-1/2 rotate-45' :
            position === 'left' ? 'right-0 top-1/2 translate-x-1/2 -translate-y-1/2 rotate-45' :
            'left-0 top-1/2 -translate-x-1/2 -translate-y-1/2 rotate-45'
          } w-2 h-2 bg-black/90 border-t border-l border-white/10`} />
        </div>
      )}
    </div>
  );
};
