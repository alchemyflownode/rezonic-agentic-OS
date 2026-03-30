// hooks/useDriftStream.ts
'use client';

import { useState, useEffect, useCallback, useRef } from 'react';

export interface DriftEntry {
  id: string;
  timestamp: number;
  type: 'constitution' | 'worker' | 'memory' | 'trade' | 'audit';
  message: string;
  hash: string;
  status: 'pass' | 'fail' | 'pending';
}

// Simulated stream — replace with real WebSocket when ready
const SEED_ENTRIES: Omit<DriftEntry, 'id' | 'timestamp' | 'hash'>[] = [
  { type: 'constitution', message: 'SCE check passed — Article 2.1 (No Deception)',          status: 'pass' },
  { type: 'worker',       message: 'Worker[Meridian] spawned → ComfyUI pipeline',            status: 'pass' },
  { type: 'memory',       message: 'Memory index updated (Δ +12 semantic nodes)',             status: 'pass' },
  { type: 'trade',        message: 'Paper trade executed: LONG SPY 585.20 × 100',            status: 'pass' },
  { type: 'audit',        message: 'Drift chain block #48,291 sealed',                       status: 'pass' },
  { type: 'constitution', message: 'SCE check passed — Article 1.3 (Sovereign Memory)',      status: 'pass' },
  { type: 'worker',       message: 'Worker[Codex] completed code generation task',           status: 'pass' },
  { type: 'memory',       message: 'Blueprint indexed: trading-strategy-momentum-v3',        status: 'pass' },
  { type: 'trade',        message: 'Backtest complete: Sharpe 2.41, Max DD -3.2%',           status: 'pass' },
  { type: 'worker',       message: 'Worker[Vision] rendered SDXL output (1024×1024)',        status: 'pass' },
  { type: 'audit',        message: 'Constitution integrity verified — 0 violations',         status: 'pass' },
  { type: 'constitution', message: 'SCE check passed — Article 4.0 (Zero Data Leakage)',    status: 'pass' },
];

function generateHash(): string {
  return '0x' + Array.from({ length: 8 }, () =>
    Math.floor(Math.random() * 16).toString(16)
  ).join('');
}

export function useDriftStream(maxEntries = 50) {
  const [entries, setEntries] = useState<DriftEntry[]>([]);
  const [isStreaming, setIsStreaming] = useState(false);
  const indexRef = useRef(0);
  const intervalRef = useRef<NodeJS.Timeout | null>(null);

  const start = useCallback(() => {
    if (intervalRef.current) return;
    setIsStreaming(true);

    // Seed initial entries
    const initial = SEED_ENTRIES.slice(0, 5).map((e, i) => ({
      ...e,
      id: `drift-${Date.now()}-${i}`,
      timestamp: Date.now() - (5 - i) * 3000,
      hash: generateHash(),
    }));
    setEntries(initial);
    indexRef.current = 5;

    intervalRef.current = setInterval(() => {
      const seed = SEED_ENTRIES[indexRef.current % SEED_ENTRIES.length];
      const entry: DriftEntry = {
        ...seed,
        id: `drift-${Date.now()}`,
        timestamp: Date.now(),
        hash: generateHash(),
      };

      setEntries(prev => {
        const next = [entry, ...prev];
        return next.slice(0, maxEntries);
      });

      indexRef.current++;
    }, 2500 + Math.random() * 2000); // Staggered for realism
  }, [maxEntries]);

  const stop = useCallback(() => {
    if (intervalRef.current) {
      clearInterval(intervalRef.current);
      intervalRef.current = null;
    }
    setIsStreaming(false);
  }, []);

  useEffect(() => {
    return () => stop();
  }, [stop]);

  return { entries, isStreaming, start, stop };
}