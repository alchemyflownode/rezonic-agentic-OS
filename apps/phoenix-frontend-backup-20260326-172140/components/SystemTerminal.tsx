'use client';

import { useEffect, useState, useRef } from 'react';

export function SystemTerminal() {
  const [logs, setLogs] = useState([
    { timestamp: '10:42:23', message: '🧠 Kernel initialized', level: 'info' },
    { timestamp: '10:42:24', message: '✅ 28 workers online', level: 'success' },
    { timestamp: '10:42:25', message: '📡 Ollama connected (30 models)', level: 'info' },
    { timestamp: '10:42:26', message: '🔍 Search worker ready', level: 'info' },
    { timestamp: '10:42:27', message: '⚡ System nominal', level: 'success' },
  ]);
  
  const terminalRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    // Simulate real-time logs
    const interval = setInterval(() => {
      const events = [
        { message: '💓 Heartbeat OK', level: 'info' },
        { message: '📊 CPU: 23% RAM: 42%', level: 'info' },
        { message: '🔧 Worker: system_monitor active', level: 'debug' },
        { message: '✅ Command executed', level: 'success' },
      ];
      
      const randomEvent = events[Math.floor(Math.random() * events.length)];
      const now = new Date();
      const timestamp = now.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
      
      setLogs(prev => [...prev.slice(-50), { ...randomEvent, timestamp }]);
    }, 3000);
    
    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    if (terminalRef.current) {
      terminalRef.current.scrollTop = terminalRef.current.scrollHeight;
    }
  }, [logs]);

  return (
    <div className="ide-terminal" ref={terminalRef}>
      {logs.map((log, index) => (
        <div key={index} className="ide-terminal-line">
          <span className="timestamp">[{log.timestamp}]</span>
          <span className={
            log.level === 'success' ? 'text-green-400' :
            log.level === 'error' ? 'text-red-400' :
            log.level === 'debug' ? 'text-blue-400' : 'text-[var(--ide-text-dim)]'
          }>
            {log.message}
          </span>
        </div>
      ))}
    </div>
  );
}
