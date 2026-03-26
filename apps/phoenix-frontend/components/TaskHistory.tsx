import { Clock } from 'lucide-react';
import { SovereignCard } from '@/components/ui/SovereignCard';

export default function TaskHistory({ history }: { history: any[] }) {
  return (
    <SovereignCard variant="default" hover={false} className="mt-4 p-3">
      <h3 className="text-xs font-bold text-[var(--sovereign-text-secondary)] mb-2 flex items-center gap-1">
        <Clock className="w-3 h-3 text-[var(--sovereign-primary)]" /> HISTORY
      </h3>
      <div className="space-y-1 max-h-32 overflow-y-auto">
        {history && history.length > 0 ? (
          history.slice(0, 5).map((h, i) => (
            <div key={i} className="text-[9px] flex items-center justify-between sovereign-fade-in">
              <span className="text-[var(--sovereign-text-tertiary)] truncate max-w-[120px]">{h.task}</span>
              <span className="text-[var(--sovereign-text-disabled)]">{h.time}</span>
            </div>
          ))
        ) : (
          <div className="text-[10px] text-[var(--sovereign-text-disabled)] sovereign-pulse-soft">No history yet</div>
        )}
      </div>
    </SovereignCard>
  );
}
