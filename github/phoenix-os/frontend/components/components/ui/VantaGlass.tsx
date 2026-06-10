// src/components/ui/VantaGlass.tsx
'use client';

import { cn } from '@/lib/utils';
import { forwardRef, HTMLAttributes } from 'react';

interface VantaGlassProps extends HTMLAttributes<HTMLDivElement> {
  layer?: 'base' | 'mantle' | 'crust';
  blur?: 'sm' | 'md' | 'lg' | 'xl';
  border?: boolean;
  glow?: boolean;
  interactive?: boolean;
}

export const VantaGlass = forwardRef<HTMLDivElement, VantaGlassProps>(
  ({ className, layer = 'mantle', blur = 'xl', border = true, glow = true, interactive = true, children, ...props }, ref) => {
    const blurMap = {
      sm: 'backdrop-blur-sm',
      md: 'backdrop-blur-md',
      lg: 'backdrop-blur-lg',
      xl: 'backdrop-blur-xl'
    };

    const layerMap = {
      base: 'bg-black/95',
      mantle: 'bg-black/60',
      crust: 'bg-black/40'
    };

    return (
      <div
        ref={ref}
        className={cn(
          layerMap[layer],
          blurMap[blur],
          'rounded-[2.5rem] relative overflow-hidden transition-all duration-300',
          border && 'border border-white/10',
          glow && 'shadow-[0_0_50px_rgba(168,85,247,0.15)]',
          interactive && 'hover:border-white/20 hover:shadow-[0_0_60px_rgba(168,85,247,0.25)]',
          className
        )}
        {...props}
      >
        {/* Top Edge Highlight */}
        <div className="absolute inset-x-0 top-0 h-px bg-gradient-to-r from-transparent via-white/20 to-transparent" />
        
        {/* Bottom Edge Glow */}
        <div className="absolute inset-x-0 bottom-0 h-px bg-gradient-to-r from-transparent via-white/10 to-transparent" />
        
        {/* Corner Accents */}
        <div className="absolute top-0 left-0 w-12 h-12 border-l-2 border-t-2 border-white/5 rounded-tl-[2.5rem]" />
        <div className="absolute top-0 right-0 w-12 h-12 border-r-2 border-t-2 border-white/5 rounded-tr-[2.5rem]" />
        
        {children}
      </div>
    );
  }
);

VantaGlass.displayName = 'VantaGlass';
