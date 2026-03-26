// utils/dashboardUtils.ts
export const formatTimestamp = (): string => {
  return new Date().toLocaleTimeString('en-US', { 
    hour12: false, hour: '2-digit', minute: '2-digit', second: '2-digit' 
  });
};

export const truncateDriftLock = (driftLock: string): string => {
  return driftLock ? driftLock.slice(0, 8) : '—';
};

export const predictNextCommands = (messages: any[]): string[] => {
  return ['/health', '/workers', '/code'];
};

export const calculateStats = (workers: any[]) => ({
  active: workers.filter(w => w.status === 'active').length,
  idle: workers.filter(w => w.status === 'idle').length,
  busy: workers.filter(w => w.status === 'busy').length,
});
