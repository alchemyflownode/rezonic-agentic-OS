'use client';

import { useEffect, useState } from 'react';

export function ModeToggle() {
  const [mode, setMode] = useState<'dark' | 'light'>('dark');

  useEffect(() => {
    // Load saved preference
    const saved = localStorage.getItem('theme') as 'dark' | 'light' | null;
    if (saved) {
      setMode(saved);
      document.documentElement.dataset.theme = saved;
    }
  }, []);

  const toggleMode = (newMode: 'dark' | 'light') => {
    setMode(newMode);
    document.documentElement.dataset.theme = newMode;
    localStorage.setItem('theme', newMode);
  };

  return (
    <div className="mode-toggle">
      <button
        className={`toggle-option ${mode === 'dark' ? 'active' : ''}`}
        onClick={() => toggleMode('dark')}
      >
        ⚡ Builder
      </button>
      <button
        className={`toggle-option ${mode === 'light' ? 'active' : ''}`}
        onClick={() => toggleMode('light')}
      >
        🌤 Flow
      </button>
    </div>
  );
}
