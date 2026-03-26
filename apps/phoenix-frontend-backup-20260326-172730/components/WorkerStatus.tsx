import { Cpu } from 'lucide-react';
import { SovereignCard } from '@/components/ui/SovereignCard';
import { SovereignBadge } from '@/components/ui/SovereignBadge';

export default function WorkerStatus({ workers }: { workers: any[] }) {
  return (
    <SovereignCard variant="default" hover={false} className="mt-4 p-3">
      <h3 className="text-xs font-bold text-[var(--sovereign-text-secondary)] mb-2 flex items-center gap-1">
        <Cpu className="w-3 h-3 text-[var(--sovereign-primary)]" /> WORKERS
      </h3>
      <div className="space-y-1">
        {workers && workers.length > 0 ? (
          workers.map((w, i) => (
            <div key={i} className="flex items-center justify-between text-[10px]">
              <span className="text-[var(--sovereign-text-tertiary)]">{w.name}</span>
              <SovereignBadge variant="online" pulse={false} className="px-1 py-0 text-[8px]">
                active
              </SovereignBadge>
            </div>
          ))
        ) : (
          <div className="text-[10px] text-[var(--sovereign-text-disabled)]">No workers connected</div>
        )}
      </div>
    </SovereignCard>
  );
}
