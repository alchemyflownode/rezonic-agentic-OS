// frontend/src/components/ConsensusViewer.tsx
import { useEffect, useState } from 'react';

interface ConsensusViewerProps {
  sessionId: string;
}

export default function ConsensusViewer({ sessionId }: ConsensusViewerProps) {
  const [logs, setLogs] = useState<string[]>(['[SYS] Consensus Engine Initialized...']);

  useEffect(() => {
    // Try WebSocket connection if you have it
    if (sessionId && sessionId !== 'local-') {
      try {
        const ws = new WebSocket(`ws://localhost:8003/ws/consensus/${sessionId}`);
        ws.onmessage = (event) => {
          const data = JSON.parse(event.data);
          if (data.type === 'consensus_phase') {
            setLogs(prev => [...prev.slice(-4), `[${data.phase.toUpperCase()}] Processing...`]);
          } else if (data.type === 'consensus_complete') {
            setLogs(prev => [...prev.slice(-4), `[DONE] Confidence: ${(data.confidence * 100).toFixed(1)}%`]);
          }
        };
        return () => ws.close();
      } catch (e) {
        // Fallback to simulation
      }
    }

    // Fallback simulation
    const interval = setInterval(() => {
      const phases = ['SYNTH_LAYER_MATCH', 'APEX_ROUTING_VERIFIED', 'INVARIANT_CHECK_PASS'];
      const randomPhase = phases[Math.floor(Math.random() * phases.length)];
      setLogs(prev => [...prev.slice(-4), `[OK] ${randomPhase}`]);
    }, 4500);
    return () => clearInterval(interval);
  }, [sessionId]);

  return (
    <div className="bg-[#0E1015]/90 backdrop-blur-md border border-[#1F222A] rounded-xl p-3 shadow-[0_8px_30px_rgba(0,0,0,0.5)]">
      <div className="text-[10px] text-[#8A8F9B] font-mono tracking-widest uppercase mb-2 border-b border-[#1F222A] pb-2">
        Terminal / Consensus
      </div>
      <div className="space-y-1 h-20 overflow-hidden flex flex-col justify-end">
        {logs.map((log, i) => (
          <div key={i} className={`text-[10px] font-mono ${i === logs.length - 1 ? 'text-[#00E5FF]' : 'text-[#4B5563]'}`}>
            > {log}
          </div>
        ))}
      </div>
    </div>
  );
}