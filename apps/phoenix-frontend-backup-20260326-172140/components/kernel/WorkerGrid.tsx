'use client'

import { useState } from 'react'

const mockWorkers = [
  { name: 'BrainWorker', status: 'active', category: 'core' },
  { name: 'ApexWorker', status: 'active', category: 'trading' },
  { name: 'CryptoWorker', status: 'active', category: 'trading' },
  { name: 'VisionWorker', status: 'idle', category: 'vision' },
  { name: 'VoiceWorker', status: 'idle', category: 'audio' },
  { name: 'MemoryWorker', status: 'active', category: 'system' },
]

export const WorkerGrid = () => {
  const [filter, setFilter] = useState('all')

  const filtered = filter === 'all' 
    ? mockWorkers 
    : mockWorkers.filter(w => w.category === filter)

  return (
    <div className="durable-card p-4">
      <div className="flex justify-between items-center mb-4">
        <h2 className="text-lg font-bold">Active Workers</h2>
        <select 
          value={filter}
          onChange={(e) => setFilter(e.target.value)}
          className="bg-surface border border-subtle rounded px-2 py-1 text-sm"
        >
          <option value="all">All</option>
          <option value="core">Core</option>
          <option value="trading">Trading</option>
          <option value="vision">Vision</option>
          <option value="audio">Audio</option>
          <option value="system">System</option>
        </select>
      </div>

      <div className="grid grid-cols-2 gap-3">
        {filtered.map((worker) => (
          <div key={worker.name} className="parameter-chip hover:bg-surface/50">
            <div className="flex items-center gap-2">
              <span className={`w-2 h-2 rounded-full ${
                worker.status === 'active' ? 'bg-green-500' : 'bg-yellow-500'
              }`} />
              <span className="font-mono text-sm">{worker.name}</span>
            </div>
            <span className="text-xs text-secondary mt-1 block">{worker.category}</span>
          </div>
        ))}
      </div>
    </div>
  )
}
