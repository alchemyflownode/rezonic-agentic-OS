'use client';

import { Panel, PanelGroup, PanelResizeHandle } from "react-resizable-panels";
import { PremiumSidebar } from './PremiumSidebar';
import { PremiumWorkerGrid } from './PremiumWorkerGrid';
import { ModernChat } from './ModernChat';
import { PremiumTerminal } from './PremiumTerminal';
import { WorkerDetails } from './WorkerDetails';
import { useWorkers } from '@/hooks/useWorkers';
import { Cpu, HardDrive, Activity } from 'lucide-react';
import '@/styles/sovereign-restored.css';

export function SovereignWorkspace() {
  const {
    workers,
    selectedWorker,
    loading,
    result,
    workerStats,
    executeWorker,
  } = useWorkers();

  return (
    <div className="h-screen w-screen bg-bg-root text-text-primary overflow-hidden flex flex-col">
      {/* Top Status Bar */}
      <div className="flex items-center justify-between px-4 py-2 border-b border-border-subtle">
        <div className="flex items-center gap-4">
          <h1>SOVEREIGN OS</h1>
          <span className="meta-text">v5.0 • 28 workers</span>
        </div>
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2">
            <Cpu size={14} className="text-text-tertiary" />
            <span className="text-sm text-text-secondary">23%</span>
          </div>
          <div className="flex items-center gap-2">
            <HardDrive size={14} className="text-text-tertiary" />
            <span className="text-sm text-text-secondary">45%</span>
          </div>
          <div className="flex items-center gap-2">
            <span className="status-dot active" />
            <span className="meta-text">connected</span>
          </div>
        </div>
      </div>

      {/* Main Workspace with Splitters */}
      <div className="flex-1 flex">
        {/* Premium Sidebar */}
        <PremiumSidebar />
        
        {/* Resizable Panels */}
        <PanelGroup direction="horizontal" className="flex-1">
          
          {/* LEFT PANEL - Worker Grid */}
          <Panel defaultSize={15} minSize={10} maxSize={20} className="border-r border-border-subtle">
            <div className="p-3 h-full overflow-y-auto">
              <h4 className="section-title">WORKER GRID</h4>
              <PremiumWorkerGrid
                workers={workers}
                onSelect={() => {}}
                selectedId={selectedWorker?.id}
              />
            </div>
          </Panel>
          
          {/* Splitter */}
          <PanelResizeHandle className="hover:bg-accent-primary transition-colors" />
          
          {/* CENTER PANEL - Chat + Terminal */}
          <Panel defaultSize={60}>
            <PanelGroup direction="vertical" className="h-full">
              
              {/* Chat */}
              <Panel defaultSize={70} minSize={40} className="p-3">
                <ModernChat />
              </Panel>
              
              {/* Splitter */}
              <PanelResizeHandle className="hover:bg-accent-primary transition-colors" />
              
              {/* Terminal */}
              <Panel defaultSize={30} minSize={20} className="p-3">
                <h4 className="section-title mb-2">SYSTEM TERMINAL</h4>
                <PremiumTerminal />
              </Panel>
            </PanelGroup>
          </Panel>
          
          {/* Splitter */}
          <PanelResizeHandle className="hover:bg-accent-primary transition-colors" />
          
          {/* RIGHT PANEL - Details */}
          <Panel defaultSize={25} minSize={20} maxSize={35} className="border-l border-border-subtle p-3">
            <h4 className="section-title mb-3">WORKER DETAILS</h4>
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
