// types/dashboard.ts
export interface Message {
  id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  driftLock?: string;
  timestamp: string;
  isStreaming?: boolean;
}

export interface MemorySnapshot {
  id: string;
  content: string;
  fullContent?: string;
  timestamp: number;
  driftLock: string;
  importance: number;
  tags?: string[];
}

export interface SystemHealth {
  kernelStatus: 'online' | 'offline' | 'checking';
  workerCount: number;
  govScore: number;
  consciousness: number;
  driftLock: string;
}
