'use client';

import { Panel, PanelGroup, PanelResizeHandle } from "react-resizable-panels";
import { PremiumSidebar } from './PremiumSidebar';
import { PremiumWorkerGrid } from './PremiumWorkerGrid';
import { PremiumTerminal } from './PremiumTerminal';
import { ObsidianChat } from './ObsidianChat';
import { WorkerDetails } from './WorkerDetails';
import { useWorkers } from '@/hooks/useWorkers';
import '@/styles/sovereign-design-system.css';

export function PremiumWorkspace() {
  const {
    workers,
    selectedWorker,
    loading,
    result,
    workerStats,
    executeWorker,
  } = useWorkers();

  return (
    <div className="h-screen w-screen bg-bg-root text-text-primary overflow-hidden flex">
      {/* Premium Sidebar */}
      <PremiumSidebar />
      
      {/* Main Workspace */}
      <div className="flex-1 flex">
        <PanelGroup direction="horizontal" className="flex-grow">
          
          {/* Worker Grid Panel */}
          <Panel defaultSize={15} minSize={10} maxSize={20} className="border-r border-border-subtle p-3">
            <div className="section-title">WORKERS • {workers.length}</div>
            <PremiumWorkerGrid
              workers={workers}
              onSelect={() => {}}
              selectedId={selectedWorker?.id}
            />
          </Panel>
          
          <PanelResizeHandle className="hover:bg-accent-primary/30 transition-colors" />
          
          {/* Chat + Terminal Panel */}
          <Panel defaultSize={60}>
            <PanelGroup direction="vertical">
              <Panel defaultSize={65} minSize={40} className="p-3">
                <ObsidianChat />
              </Panel>
              
              <PanelResizeHandle className="hover:bg-accent-primary/30 transition-colors" />
              
              <Panel defaultSize={35} minSize={20} className="p-3">
                <div className="section-title mb-2">SYSTEM TERMINAL</div>
                <PremiumTerminal />
              </Panel>
            </PanelGroup>
          </Panel>
          
          <PanelResizeHandle className="hover:bg-accent-primary/30 transition-colors" />
          
          {/* Details Panel */}
          <Panel defaultSize={25} minSize={20} maxSize={35} className="border-l border-border-subtle p-3">
            <div className="section-title mb-3">DETAILS</div>
            <WorkerDetails
              worker={selectedWorker}
              onExecute={executeWorker}
              isLoading={loading}
              result={result}
              stats={selectedWorker ? workerStats[selectedWorker.id] : null}
            />
          </Panel>
          
        </PanelGroup>
      </div>
    </div>
  );
}
