import { useEffect, useRef, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';

export interface LogEntry {
  id: string;
  timestamp: string;
  level: 'info' | 'warn' | 'error' | 'debug' | 'worker';
  source: string;
  message: string;
  metadata?: Record<string, any>;
}

interface ExecutionLogsProps {
  logs: LogEntry[];
  maxHeight?: string;
  className?: string;
  onClear?: () => void;
}

const levelConfig = {
  info: { color: '#00E5FF', bg: 'rgba(0,229,255,0.1)', icon: 'ℹ' },
  warn: { color: '#FFB800', bg: 'rgba(255,184,0,0.1)', icon: '⚠' },
  error: { color: '#FF4500', bg: 'rgba(255,69,0,0.1)', icon: '✕' },
  debug: { color: '#8A8F9B', bg: 'rgba(138,143,155,0.1)', icon: '◆' },
  worker: { color: '#10b981', bg: 'rgba(16,185,129,0.1)', icon: '⚡' }
};

export default function ExecutionLogs({ logs, maxHeight = '300px', className = '', onClear }: ExecutionLogsProps) {
  const scrollRef = useRef<HTMLDivElement>(null);
  const [isAutoScroll, setIsAutoScroll] = useState(true);
  const[filter, setFilter] = useState<string | null>(null);
  const [selectedLog, setSelectedLog] = useState<LogEntry | null>(null);

  useEffect(() => {
    if (isAutoScroll && scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [logs, isAutoScroll]);

  const filteredLogs = filter ? logs.filter(l => l.level === filter || l.source.includes(filter)) : logs;

  return (
    <div className={`bg-[#0E1015]/90 backdrop-blur-md border border-[#1F222A] rounded-xl shadow-[0_8px_30px_rgba(0,0,0,0.5)] relative overflow-hidden flex flex-col ${className}`}>
      <div className="absolute top-0 right-0 w-32 h-32 bg-[#00E5FF]/5 rounded-full blur-3xl pointer-events-none" />
      <div className="flex items-center justify-between p-4 border-b border-[#1F222A] bg-[#0A0C10]/50 relative z-10">
        <div className="flex items-center gap-2 text-xs font-bold tracking-[0.15em] uppercase text-white">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className="text-[#00E5FF]"><polyline points="4 17 10 11 4 5"/><line x1="12" y1="19" x2="20" y2="19"/></svg>
          Execution Logs
        </div>
        <div className="flex items-center gap-2">
          {(['info', 'worker', 'warn', 'error'] as const).map(level => (
            <button
              key={level} onClick={() => setFilter(filter === level ? null : level)}
              className="text-[9px] px-2 py-0.5 rounded font-mono uppercase transition-all"
              style={filter === level ? { backgroundColor: levelConfig[level].bg, color: levelConfig[level].color, borderColor: `${levelConfig[level].color}40`, borderWidth: '1px' } : { backgroundColor: '#1A1D24', color: '#4B5563', borderColor: '#2A2E38', borderWidth: '1px' }}
            >
              {level}
            </button>
          ))}
          <div className="w-px h-3 bg-[#1F222A] mx-1" />
          <button onClick={() => setIsAutoScroll(!isAutoScroll)} className={`text-[9px] px-2 py-0.5 rounded font-mono uppercase transition-all ${isAutoScroll ? 'bg-[#10b981]/10 text-[#10b981] border border-[#10b981]/30' : 'bg-[#1A1D24] text-[#4B5563] border border-[#2A2E38]'}`}>
            {isAutoScroll ? 'AUTO' : 'PAUSE'}
          </button>
          {onClear && (
            <button onClick={onClear} className="text-[9px] px-2 py-0.5 rounded bg-[#1A1D24] text-[#8A8F9B] border border-[#2A2E38] hover:text-[#FF4500] hover:border-[#FF4500]/30 transition-all font-mono uppercase">
              CLEAR
            </button>
          )}
        </div>
      </div>
      <div ref={scrollRef} className="flex-1 overflow-y-auto custom-scrollbar p-0 font-mono text-xs relative z-10" style={{ maxHeight }}>
        {filteredLogs.length === 0 ? (
          <div className="flex items-center justify-center h-32 text-[#4B5563] text-[10px] uppercase tracking-wider">No execution logs available</div>
        ) : (
          <div className="divide-y divide-[#1F222A]/50">
            {filteredLogs.map((log, index) => {
              const config = levelConfig[log.level];
              const isEven = index % 2 === 0;
              return (
                <motion.div
                  key={log.id} initial={{ opacity: 0, x: -10 }} animate={{ opacity: 1, x: 0 }} transition={{ duration: 0.2 }} onClick={() => setSelectedLog(selectedLog?.id === log.id ? null : log)}
                  className={`flex items-start gap-3 p-3 cursor-pointer transition-all ${isEven ? 'bg-[#0A0C10]/30' : 'bg-transparent'} hover:bg-[#00E5FF]/5 group`}
                >
                  <span className="text-[9px] text-[#4B5563] shrink-0 w-16 pt-0.5">{log.timestamp}</span>
                  <span className="shrink-0 w-5 h-5 flex items-center justify-center rounded text-[10px] font-bold" style={{ color: config.color, backgroundColor: config.bg, border: `1px solid ${config.color}30` }}>{config.icon}</span>
                  <span className="shrink-0 text-[9px] uppercase tracking-wider px-1.5 py-0.5 rounded bg-[#1A1D24] text-[#8A8F9B] border border-[#2A2E38]">{log.source}</span>
                  <span className={`flex-1 text-[11px] leading-relaxed ${log.level === 'error' ? 'text-[#FF4500]' : log.level === 'warn' ? 'text-[#FFB800]' : 'text-[#D1D5DB]'}`}>{log.message}</span>
                  {log.metadata && <motion.span animate={{ rotate: selectedLog?.id === log.id ? 90 : 0 }} className="text-[#4B5563] group-hover:text-[#00E5FF] transition-colors">›</motion.span>}
                </motion.div>
              );
            })}
          </div>
        )}
      </div>
      <div className="flex items-center justify-between px-4 py-2 border-t border-[#1F222A] bg-[#0A0C10]/50 text-[9px] font-mono text-[#4B5563] uppercase tracking-wider relative z-10">
        <span>{filteredLogs.length} entries</span>
        <span>last: {logs[logs.length - 1]?.timestamp || '--:--:--'}</span>
      </div>
      <AnimatePresence>
        {selectedLog?.metadata && (
          <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: 20 }} className="absolute bottom-0 left-0 right-0 bg-[#12141A] border-t border-[#00E5FF]/30 p-4 shadow-[0_-10px_30px_rgba(0,0,0,0.5)] z-20">
            <div className="flex items-center justify-between mb-2">
              <span className="text-[10px] font-bold text-[#00E5FF] uppercase tracking-wider">Execution Metadata</span>
              <button onClick={() => setSelectedLog(null)} className="text-[#4B5563] hover:text-white">✕</button>
            </div>
            <pre className="text-[10px] font-mono text-[#8A8F9B] overflow-x-auto custom-scrollbar bg-[#0A0C10] p-2 rounded border border-[#1F222A]">{JSON.stringify(selectedLog.metadata, null, 2)}</pre>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}