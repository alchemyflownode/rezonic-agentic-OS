'use client';

import { cn } from '@/lib/utils';
import { forwardRef, HTMLAttributes } from 'react';

interface GlassCardProps extends HTMLAttributes<HTMLDivElement> {
  variant?: 'ultra-thin' | 'thin' | 'medium' | 'heavy';
  hover?: boolean;
  glow?: boolean;
  radius?: 'sm' | 'md' | 'lg' | 'xl' | '2xl' | '3xl' | 'full';
}

export const GlassCard = forwardRef<HTMLDivElement, GlassCardProps>(
  ({ className, variant = 'thin', hover = true, glow = false, radius = 'lg', children, ...props }, ref) => {
    const variantStyles = {
      'ultra-thin': 'bg-white/[0.02] backdrop-blur-sm',
      'thin': 'bg-white/[0.03] backdrop-blur-md',
      'medium': 'bg-white/[0.05] backdrop-blur-lg',
      'heavy': 'bg-white/[0.08] backdrop-blur-xl'
    };

    const radiusStyles = {
      'sm': 'rounded-[8px]',
      'md': 'rounded-[12px]',
      'lg': 'rounded-[16px]',
      'xl': 'rounded-[20px]',
      '2xl': 'rounded-[24px]',
      '3xl': 'rounded-[28px]',
      'full': 'rounded-[9999px]'
    };

    return (
      <div
        ref={ref}
        className={cn(
          variantStyles[variant],
          radiusStyles[radius],
          'border border-white/10 transition-all duration-300',
          hover && 'hover:bg-white/[0.08] hover:border-white/20 hover:shadow-xl hover:-translate-y-0.5',
          glow && 'shadow-glow',
          className
        )}
        style={{
          boxShadow: glow ? '0 0 30px rgba(139, 92, 246, 0.2)' : undefined
        }}
        {...props}
      >
        {/* Rim light effect */}
        <div className="absolute inset-0 rounded-[inherit] pointer-events-none">
          <div className="absolute inset-x-0 top-0 h-px bg-gradient-to-r from-transparent via-white/20 to-transparent rounded-t-[inherit]" />
          <div className="absolute inset-x-0 bottom-0 h-px bg-gradient-to-r from-transparent via-white/5 to-transparent rounded-b-[inherit]" />
        </div>
        
        {children}
      </div>
    );
  }
);

GlassCard.displayName = 'GlassCard';
