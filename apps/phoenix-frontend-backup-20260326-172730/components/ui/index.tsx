// components/ui/index.tsx - RezHive Premium UI Components (v9.1 - OKIRU Expanded)
import React, { useState } from 'react';
import { motion, PanInfo, AnimatePresence } from 'framer-motion';

// ============================================================================
// SPLITTER COMPONENT
// ============================================================================
interface SplitterProps {
  axis: 'horizontal' | 'vertical';
  onDrag: (delta: number) => void;
  onDragStart?: () => void;
}

export const Splitter: React.FC<SplitterProps> = ({ axis, onDrag, onDragStart }) => {
  return (
    <motion.div
      className={`splitter ${axis}`}
      drag={axis === 'vertical' ? 'x' : 'y'}
      dragConstraints={{ left: 0, right: 0, top: 0, bottom: 0 }}
      dragElastic={0.1}
      onDragStart={onDragStart}
      onDrag={(event, info: PanInfo) => onDrag(axis === 'vertical' ? info.delta.x : info.delta.y)}
      style={{
        padding: axis === 'vertical' ? '0 4px' : '4px 0',
        margin: axis === 'vertical' ? '0 -4px' : '-4px 0',
      }}
    >
      <div className="splitter-handle" />
    </motion.div>
  );
};

// ============================================================================
// SPLIT PANEL & NAV LAYOUTS
// ============================================================================
export const SplitPanel: React.FC<{
  left: React.ReactNode;
  right: React.ReactNode;
  leftWidth?: number; // percentage
  className?: string;
}> = ({ left, right, leftWidth = 30, className = '' }) => (
  <div className={`flex gap-4 h-full ${className}`}>
    <div className="overflow-y-auto pr-2 custom-scrollbar" style={{ width: `${leftWidth}%` }}>
      {left}
    </div>
    <div className="flex-1 overflow-y-auto custom-scrollbar border-l border-subtle pl-4">
      {right}
    </div>
  </div>
);

export const NavPanel: React.FC<{
  items: Array<{ id: string; label: string; icon: React.ReactNode }>;
  selectedId: string | null;
  onSelect: (id: string) => void;
}> = ({ items, selectedId, onSelect }) => (
  <nav className="space-y-1">
    {items.map(item => (
      <button
        key={item.id}
        onClick={() => onSelect(item.id)}
        className={`w-full flex items-center gap-3 px-3 py-2 rounded-md transition-all ${
          selectedId === item.id
            ? 'bg-accent-cyber/10 text-accent-cyber border-l-2 border-accent-cyber'
            : 'text-text-secondary hover:text-text-primary hover:bg-surface'
        }`}
      >
        <span className="text-lg">{item.icon}</span>
        <span className="text-sm font-mono">{item.label}</span>
      </button>
    ))}
  </nav>
);

// ============================================================================
// CARD COMPONENTS
// ============================================================================
interface CardProps {
  children: React.ReactNode;
  className?: string;
  variant?: 'default' | 'intense' | 'interactive' | 'selectable' | 'action' | 'metric';
}

export const Card: React.FC<CardProps> = ({ 
  children, 
  className = '', 
  variant = 'default' 
}) => {
  const variantClass = {
    default: 'durable-card',
    intense: 'durable-card-intense',
    interactive: 'durable-card-interactive haptic-lift',
    selectable: 'durable-card cursor-pointer transition-all hover:border-accent-cyber/50 hover:shadow-glow selected:border-accent-cyber selected:bg-accent-cyber/10',
    action: 'durable-card group relative overflow-hidden hover:border-accent-cyber/30',
    metric: 'durable-card bg-surface/50 backdrop-blur-sm border-subtle'
  }[variant];

  return (
    <div className={`${variantClass} ${className}`}>
      {children}
    </div>
  );
};

export const CardHeader: React.FC<{ children: React.ReactNode; className?: string }> = ({ 
  children, 
  className = '' 
}) => (
  <div className={`p-4 border-b border-subtle ${className}`}>
    {children}
  </div>
);

export const CardContent: React.FC<{ children: React.ReactNode; className?: string }> = ({ 
  children, 
  className = '' 
}) => (
  <div className={`p-4 ${className}`}>
    {children}
  </div>
);

// ============================================================================
// FORM ELEMENTS
// ============================================================================
export const Textarea: React.FC<React.TextareaHTMLAttributes<HTMLTextAreaElement>> = (props) => (
  <textarea
    {...props}
    className={`w-full bg-surface text-text-primary border border-subtle rounded-md p-3 
      focus:border-glow focus:ring-1 focus:ring-accent-cyber/30 outline-none transition 
      resize-none font-mono text-sm custom-scrollbar ${props.className || ''}`}
  />
);

interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'danger';
}

export const Button: React.FC<ButtonProps> = ({ 
  children, 
  className = '',
  variant = 'primary',
  ...props 
}) => {
  const variantClass = {
    primary: props.disabled 
      ? 'bg-surface text-text-secondary border border-subtle' 
      : 'bg-accent-cyber/10 text-accent-cyber border border-accent-cyber/30 hover:bg-accent-cyber/20 hover:border-accent-cyber/50 hover:shadow-glow',
    secondary: props.disabled
      ? 'bg-surface text-text-secondary border border-subtle'
      : 'bg-accent-purple/10 text-accent-purple border border-accent-purple/30 hover:bg-accent-purple/20 hover:border-accent-purple/50',
    danger: props.disabled
      ? 'bg-surface text-text-secondary border border-subtle'
      : 'bg-accent-red/10 text-accent-red border border-accent-red/30 hover:bg-accent-red/20 hover:border-accent-red/50'
  }[variant];

  return (
    <button
      {...props}
      className={`px-4 py-2 rounded-md font-mono text-xs font-bold tracking-widest uppercase
        transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed
        flex items-center justify-center gap-2 haptic-press
        ${variantClass} ${className}`}
    >
      {children}
    </button>
  );
};

export const Input: React.FC<React.InputHTMLAttributes<HTMLInputElement>> = (props) => (
  <input
    {...props}
    className={`w-full bg-surface border border-subtle rounded-md p-2.5 text-text-primary 
      focus:border-glow focus:ring-1 focus:ring-accent-cyber/30 outline-none transition 
      font-mono text-sm ${props.className || ''}`}
  />
);

export const Select: React.FC<React.SelectHTMLAttributes<HTMLSelectElement>> = ({ 
  children, 
  className = '',
  ...props 
}) => (
  <select
    {...props}
    className={`w-full bg-surface border border-subtle rounded-md p-2.5 text-text-primary 
      focus:border-glow focus:ring-1 focus:ring-accent-cyber/30 outline-none transition 
      font-mono text-sm appearance-none ${className}`}
    style={{
      backgroundImage: `url("data:image/svg+xml,%3csvg xmlns='http://www.w3.org/2000/svg' fill='none' viewBox='0 0 20 20'%3e%3cpath stroke='%238A8F9B' stroke-linecap='round' stroke-linejoin='round' stroke-width='1.5' d='M6 8l4 4 4-4'/%3e%3c/svg%3e")`,
      backgroundPosition: 'right 0.5rem center',
      backgroundRepeat: 'no-repeat',
      backgroundSize: '1.5em 1.5em',
      paddingRight: '2.5rem',
    }}
  >
    {children}
  </select>
);

export const SliderGroup: React.FC<{
  label: string;
  value: number;
  onChange: (value: number) => void;
  min?: number;
  max?: number;
  step?: number;
  unit?: string;
}> = ({ label, value, onChange, min = 0, max = 100, step = 1, unit = '' }) => (
  <div>
    <div className="flex justify-between items-center mb-1">
      <label className="text-sm text-text-secondary">{label}</label>
      <div className="flex items-center">
        <Input
          type="number"
          value={value}
          onChange={(e) => onChange(Number(e.target.value))}
          min={min}
          max={max}
          step={step}
          className="w-20 bg-transparent border-0 focus:ring-0 p-0 text-right font-mono"
        />
        <span className="text-xs text-text-tertiary ml-1">{unit}</span>
      </div>
    </div>
    <input
      type="range"
      value={value}
      onChange={(e) => onChange(Number(e.target.value))}
      min={min}
      max={max}
      step={step}
      className="w-full h-1.5 bg-surface rounded-lg appearance-none cursor-pointer
        [&::-webkit-slider-thumb]:appearance-none [&::-webkit-slider-thumb]:w-4 [&::-webkit-slider-thumb]:h-4 
        [&::-webkit-slider-thumb]:rounded-full [&::-webkit-slider-thumb]:bg-accent-cyber 
        [&::-webkit-slider-thumb]:cursor-pointer[&::-webkit-slider-thumb]:border-2 
        [&::-webkit-slider-thumb]:border-white/20 [&::-webkit-slider-thumb]:shadow-glow"
    />
  </div>
);

export const Toggle: React.FC<{
  checked: boolean;
  onChange: () => void;
  label?: string;
}> = ({ checked, onChange, label }) => (
  <label className="flex items-center gap-3 cursor-pointer">
    {label && <span className="text-sm text-text-secondary">{label}</span>}
    <div className="relative">
      <input type="checkbox" checked={checked} onChange={onChange} className="sr-only" />
      <div className={`block w-10 h-6 rounded-full transition-colors ${checked ? 'bg-accent-cyber' : 'bg-surface'}`}>
        <div className={`dot absolute top-1 left-1 w-4 h-4 rounded-full bg-white transition-transform ${checked ? 'transform translate-x-4' : ''}`} />
      </div>
    </div>
  </label>
);

// ============================================================================
// DATA VISUALIZATION & METRICS
// ============================================================================
export const MetricGrid: React.FC<{
  metrics: Array<{ label: string; value: string | number; trend?: 'up' | 'down' | 'stable' }>;
  columns?: 2 | 3 | 4;
}> = ({ metrics, columns = 4 }) => {
  const gridCols = {
    2: 'grid-cols-2',
    3: 'grid-cols-3',
    4: 'grid-cols-4'
  }[columns];
  
  return (
    <div className={`grid ${gridCols} gap-4`}>
      {metrics.map((metric, i) => (
        <div key={i} className="bg-surface/50 p-3 rounded-md border border-subtle">
          <p className="text-xs text-text-secondary">{metric.label}</p>
          <p className="font-mono text-lg text-text-primary">
            {metric.value}
            {metric.trend === 'up' && <span className="text-accent-green ml-1">↑</span>}
            {metric.trend === 'down' && <span className="text-accent-red ml-1">↓</span>}
          </p>
        </div>
      ))}
    </div>
  );
};

export const ProgressBar: React.FC<{ 
  progress: number; 
  variant?: 'default' | 'kintsugi';
  showLabel?: boolean;
}> = ({ progress, variant = 'default', showLabel = false }) => (
  <div className="w-full">
    {showLabel && (
      <div className="flex justify-between items-center mb-1 text-sm">
        <span className="text-accent-cyber">Processing...</span>
        <span className="text-text-secondary">{Math.round(progress)}%</span>
      </div>
    )}
    <div className="h-2 w-full bg-surface rounded-full overflow-hidden border border-subtle">
      <motion.div 
        className={`h-full rounded-full ${
          variant === 'kintsugi' 
            ? 'bg-gradient-to-r from-accent-purple to-accent-cyber' 
            : 'bg-accent-cyber'
        }`}
        initial={{ width: 0 }}
        animate={{ width: `${progress}%` }}
        transition={{ duration: 0.3 }}
      />
    </div>
  </div>
);

// ============================================================================
// FEEDBACK & STATUS
// ============================================================================
export const StatusBadge: React.FC<{
  status: 'pending' | 'active' | 'complete' | 'error';
  children?: React.ReactNode;
}> = ({ status, children }) => {
  const statusConfig = {
    pending: { bg: 'bg-surface', text: 'text-text-secondary', dot: 'bg-text-tertiary' },
    active: { bg: 'bg-accent-cyber/10', text: 'text-accent-cyber', dot: 'bg-accent-cyber animate-pulse' },
    complete: { bg: 'bg-[#6AAB73]/10', text: 'text-[#6AAB73]', dot: 'bg-[#6AAB73]' }, // JetBrains Green
    error: { bg: 'bg-accent-red/10', text: 'text-accent-red', dot: 'bg-accent-red' }
  }[status];
  
  return (
    <span className={`px-2 py-1 rounded-md text-xs font-mono flex items-center gap-2 ${statusConfig.bg} ${statusConfig.text}`}>
      <span className={`w-1.5 h-1.5 rounded-full ${statusConfig.dot}`} />
      {children || status.toUpperCase()}
    </span>
  );
};

export const StatusDot: React.FC<{ status: 'active' | 'idle' | 'warning' | 'danger' }> = ({ status }) => {
  const statusClass = {
    active: 'status-dot-active',
    idle: 'status-dot-idle',
    warning: 'status-dot-warning',
    danger: 'status-dot-danger'
  }[status];

  return <span className={`status-dot ${statusClass}`} />;
};

export const ParameterChip: React.FC<{ 
  children: React.ReactNode; 
  active?: boolean;
  small?: boolean;
}> = ({ children, active = false, small = false }) => (
  <span className={`
    ${small ? 'parameter-chip-small' : 'parameter-chip'}
    ${active ? 'parameter-chip-active' : ''}
  `}>
    {children}
  </span>
);

export const LoadingSpinner: React.FC<{
  size?: 'sm' | 'md' | 'lg';
  text?: string;
}> = ({ size = 'md', text }) => {
  const sizeClasses = {
    sm: 'w-4 h-4 border-2',
    md: 'w-6 h-6 border-2',
    lg: 'w-8 h-8 border-3'
  }[size];
  
  return (
    <div className="flex flex-col items-center justify-center gap-3">
      <div className={`${sizeClasses} border-accent-cyber border-t-transparent rounded-full animate-spin`} />
      {text && <p className="text-sm font-mono tracking-widest text-text-secondary uppercase">{text}</p>}
    </div>
  );
};

// ============================================================================
// OVERLAYS & MODALS
// ============================================================================
export const Modal: React.FC<{
  isOpen: boolean;
  onClose: () => void;
  children: React.ReactNode;
  title?: string;
  size?: 'sm' | 'md' | 'lg' | 'xl';
}> = ({ isOpen, onClose, children, title, size = 'md' }) => {
  const sizeClasses = {
    sm: 'max-w-md',
    md: 'max-w-2xl',
    lg: 'max-w-4xl',
    xl: 'max-w-6xl'
  }[size];
  
  return (
    <AnimatePresence>
      {isOpen && (
        <motion.div
          className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-sm p-4"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          onClick={onClose}
        >
          <motion.div
            className={`w-full ${sizeClasses} bg-[#1E1F22] rounded-xl border border-subtle shadow-2xl overflow-hidden`}
            initial={{ y: 20, scale: 0.95 }}
            animate={{ y: 0, scale: 1 }}
            exit={{ y: 20, scale: 0.95 }}
            transition={{ type: 'spring', stiffness: 400, damping: 30 }}
            onClick={(e) => e.stopPropagation()}
          >
            {title && (
              <div className="flex justify-between items-center p-4 border-b border-subtle bg-[#2B2D30]">
                <h2 className="text-sm font-bold tracking-widest text-text-primary uppercase font-mono">{title}</h2>
                <button onClick={onClose} className="text-text-tertiary hover:text-text-primary transition-colors">
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><line x1="18" y1="6" x2="6" y2="18"></line><line x1="6" y1="6" x2="18" y2="18"></line></svg>
                </button>
              </div>
            )}
            <div className="p-6">
              {children}
            </div>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  );
};

// ============================================================================
// GLASS SURFACE & PREVIEW UTILS
// ============================================================================
export const GlassSurface: React.FC<{ 
  children: React.ReactNode; 
  variant?: 'default' | 'deep' | 'intense';
  className?: string;
}> = ({ children, variant = 'default', className = '' }) => {
  const variantClass = {
    default: 'glass-surface',
    deep: 'glass-surface-deep',
    intense: 'glass-surface-intense'
  }[variant];

  return (
    <div className={`${variantClass} ${className}`}>
      {children}
    </div>
  );
};

export const ResponsivePreview: React.FC<{
  children: React.ReactNode;
  minWidth?: number;
  maxWidth?: number;
}> = ({ children, minWidth = 320, maxWidth = 1920 }) => {
  const [width, setWidth] = useState(1024);
  const scaleFactor = width / maxWidth;
  
  return (
    <div className="space-y-4">
      <div className="flex items-center gap-4">
        <span className="text-xs font-mono text-text-secondary uppercase">Viewport:</span>
        <input
          type="range"
          min={minWidth}
          max={maxWidth}
          value={width}
          onChange={(e) => setWidth(Number(e.target.value))}
          className="flex-1 h-1.5 bg-surface rounded-lg appearance-none cursor-pointer [&::-webkit-slider-thumb]:appearance-none [&::-webkit-slider-thumb]:w-3 [&::-webkit-slider-thumb]:h-3 [&::-webkit-slider-thumb]:rounded-full [&::-webkit-slider-thumb]:bg-accent-cyber"
        />
        <span className="font-mono text-xs text-accent-cyber w-12 text-right">{width}px</span>
      </div>
      <div className="border border-subtle rounded-lg overflow-hidden bg-[#0A0C10] flex justify-center py-8">
        <div 
          className="bg-surface shadow-2xl transition-all duration-200 ease-out border border-subtle rounded-md overflow-hidden relative"
          style={{ width: `${width}px`, maxWidth: '100%', minHeight: '400px' }}
        >
          {children}
        </div>
      </div>
    </div>
  );
};

// ============================================================================
// ANIMATION WRAPPERS
// ============================================================================
export const FadeUp: React.FC<{ 
  children: React.ReactNode; 
  delay?: number;
  className?: string;
}> = ({ children, delay = 0, className = '' }) => (
  <motion.div
    initial={{ opacity: 0, y: 20 }}
    animate={{ opacity: 1, y: 0 }}
    transition={{ duration: 0.6, delay, ease:[0.34, 1.56, 0.64, 1] }}
    className={className}
  >
    {children}
  </motion.div>
);

export const ScaleIn: React.FC<{ 
  children: React.ReactNode; 
  delay?: number;
  className?: string;
}> = ({ children, delay = 0, className = '' }) => (
  <motion.div
    initial={{ scale: 0.95, opacity: 0 }}
    animate={{ scale: 1, opacity: 1 }}
    transition={{ duration: 0.4, delay, ease:[0.2, 0, 0, 1] }}
    className={className}
  >
    {children}
  </motion.div>
);