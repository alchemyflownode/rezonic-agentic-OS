import { Shield } from 'lucide-react';
import { SovereignCard } from '@/components/ui/SovereignCard';

export default function ConstitutionPanel() {
  return (
    <SovereignCard variant="default" hover={false} className="mt-4 p-3">
      <h3 className="text-xs font-bold text-[var(--sovereign-text-secondary)] mb-2 flex items-center gap-1">
        <Shield className="w-3 h-3 text-[var(--sovereign-primary)]" /> CONSTITUTION
      </h3>
      <ul className="text-[10px] text-[var(--sovereign-text-tertiary)] space-y-1">
        <li className="flex items-center gap-1">
          <span className="w-1 h-1 bg-[var(--sovereign-primary)] rounded-full" />
          Preserve user privacy (Psalm 91:1)
        </li>
        <li className="flex items-center gap-1">
          <span className="w-1 h-1 bg-[var(--sovereign-primary)] rounded-full" />
          Verify before code execution (Psalm 91:11)
        </li>
        <li className="flex items-center gap-1">
          <span className="w-1 h-1 bg-[var(--sovereign-primary)] rounded-full" />
          No unauthorized file deletion (Psalm 91:5)
        </li>
        <li className="flex items-center gap-1">
          <span className="w-1 h-1 bg-[var(--sovereign-primary)] rounded-full" />
          System watches continuously (Psalm 139:1-3)
        </li>
      </ul>
    </SovereignCard>
  );
}
