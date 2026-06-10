'use client';

export function TypographyDemo() {
  return (
    <div className="panel p-4 space-y-4">
      <div>
        <h1>h1. Sovereign OS (24px/600)</h1>
        <h2>h2. System Dashboard (20px/500)</h2>
        <h3>h3. Worker Status (18px/500)</h3>
        <h4>h4. Section Title (16px/500 uppercase)</h4>
      </div>
      
      <div className="space-y-2">
        <p className="text-primary">Body text primary (13px/400) - Main content</p>
        <p className="text-secondary">Body text secondary (13px/400) - Less important</p>
        <p className="meta-text">Meta text (11px/400) - Timestamps, metadata</p>
        <p className="label-text">Label text (12px/500) - Form labels</p>
      </div>
      
      <div className="font-mono space-y-1">
        <p className="text-xs">Monospace 11px - Code</p>
        <p className="text-sm">Monospace 12px - Terminal</p>
        <p className="text-base">Monospace 13px - Commands</p>
      </div>
    </div>
  );
}
