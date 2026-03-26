// hooks/useSystemHealth.ts
import { useState, useEffect, useCallback } from 'react';

interface SystemHealth {
  kernelStatus: 'online' | 'offline' | 'checking';
  workerCount: number;
  govScore: number;
  consciousness: number;
  driftLock: string;
}

export const useSystemHealth = () => {
  const [health, setHealth] = useState<SystemHealth>({
    kernelStatus: 'checking',
    workerCount: 56,
    govScore: 98,
    consciousness: 0.87,
    driftLock: ''
  });
  const [workers, setWorkers] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);

  const refresh = useCallback(async () => {
    setLoading(true);
    try {
      const res = await fetch('http://localhost:8002/health');
      if (res.ok) {
        const data = await res.json();
        setHealth({
          kernelStatus: 'online',
          workerCount: data.workers || 56,
          govScore: Math.floor(data.integrity_score || 98),
          consciousness: data.consciousness || 0.87,
          driftLock: data.driftLock || ''
        });
      }
    } catch (e) {
      setHealth(prev => ({ ...prev, kernelStatus: 'offline' }));
    }
    setLoading(false);
  }, []);

  useEffect(() => {
    refresh();
    const interval = setInterval(refresh, 10000);
    return () => clearInterval(interval);
  }, [refresh]);

  return { health, workers, loading, refresh };
};
