'use client';

import { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { Code, GitBranch, Database, Shield, Zap, ExternalLink } from 'lucide-react';

export function JetBrainsPanel() {
  const [ides, setIDEs] = useState([]);
  const [selectedFile, setSelectedFile] = useState('');
  const [action, setAction] = useState('');

  useEffect(() => {
    fetch('/api/jetbrains')
      .then(res => res.json())
      .then(data => {
        if (data.success) {
          setIDEs(data.ides);
        }
      });
  }, []);

  const openInIDE = async (action: string, file?: string) => {
    const response = await fetch('/api/jetbrains', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        action,
        file: file || selectedFile,
        line: 1
      })
    });
    const data = await response.json();
    if (data.success) {
      setAction(`${action} executed in ${data.ide}`);
    }
  };

  const visualizeCrystals = async () => {
    await fetch('/api/workers/datagrip', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ action: 'visualize' })
    });
  };

  return (
    <div className="obsidian-panel p-4">
      <h3 className="text-sm font-medium text-white mb-4 flex items-center gap-2">
        <Code className="w-4 h-4 text-cyan-400" />
        JetBrains Integration
      </h3>
      
      {ides.length > 0 && (
        <div className="mb-4">
          <div className="text-xs text-white/50 mb-2">Available IDEs:</div>
          <div className="space-y-1">
            {ides.map((ide: any, i: number) => (
              <div key={i} className="flex items-center gap-2 text-xs text-white/70">
                <Zap className="w-3 h-3 text-cyan-400" />
                {ide.name}
              </div>
            ))}
          </div>
        </div>
      )}
      
      <div className="space-y-3">
        <button
          onClick={() => openInIDE('open-project')}
          className="w-full obsidian-button flex items-center justify-between"
        >
          <span className="flex items-center gap-2">
            <GitBranch className="w-4 h-4" />
            Open Project in IDE
          </span>
          <ExternalLink className="w-3 h-3" />
        </button>
        
        <button
          onClick={visualizeCrystals}
          className="w-full obsidian-button flex items-center justify-between"
        >
          <span className="flex items-center gap-2">
            <Database className="w-4 h-4" />
            Visualize Crystals
          </span>
          <ExternalLink className="w-3 h-3" />
        </button>
        
        <button
          onClick={() => openInIDE('inspect')}
          className="w-full obsidian-button flex items-center justify-between"
        >
          <span className="flex items-center gap-2">
            <Shield className="w-4 h-4" />
            Run Code Inspection
          </span>
          <ExternalLink className="w-3 h-3" />
        </button>
      </div>
      
      {action && (
        <div className="mt-4 p-2 bg-cyan-500/10 border border-cyan-500/30 rounded text-xs text-cyan-400">
          {action}
        </div>
      )}
      
      <div className="mt-4 text-[10px] text-white/30 border-t border-white/10 pt-3">
        <div className="flex items-center gap-2">
          <span>Kotlin workers ready for high-performance tasks</span>
        </div>
      </div>
    </div>
  );
}
