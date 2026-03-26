'use client'

import { useKernel } from '@/hooks/useKernel'

export const KernelStatus = () => {
  const { kernel } = useKernel()

  return (
    <div className="durable-card p-4">
      <h2 className="text-lg font-bold mb-4 flex items-center gap-2">
        <span className="status-dot-active" />
        Kernel Status
      </h2>
      
      <div className="grid grid-cols-2 gap-4">
        <div className="parameter-chip">
          <div className="text-xs text-secondary">Workers</div>
          <div className="text-xl font-mono text-accent-cyber">{kernel.workers}</div>
        </div>
        <div className="parameter-chip">
          <div className="text-xs text-secondary">Latency</div>
          <div className="text-xl font-mono text-accent-purple">{kernel.latency}ms</div>
        </div>
        <div className="parameter-chip">
          <div className="text-xs text-secondary">Connection</div>
          <div className={`text-sm font-mono ${kernel.connected ? 'text-green-500' : 'text-red-500'}`}>
            {kernel.connected ? '🟢 Online' : '🔴 Offline'}
          </div>
        </div>
        <div className="parameter-chip">
          <div className="text-xs text-secondary">SCE Protocol</div>
          <div className="text-sm font-mono text-cyan-400">v1.0.0</div>
        </div>
      </div>
    </div>
  )
}
