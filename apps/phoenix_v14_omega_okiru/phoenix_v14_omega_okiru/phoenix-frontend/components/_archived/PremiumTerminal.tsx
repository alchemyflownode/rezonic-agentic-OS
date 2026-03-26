'use client';

import { useState, useEffect, useRef } from 'react';

export function PremiumTerminal() {
  const [logs, setLogs] = useState([
    { time: '10:42:23', msg: '🧠 Kernel initialized', type: 'info' },
    { time: '10:42:24', msg: '✅ 28 workers online', type: 'success' },
    { time: '10:42:25', msg: '📡 Ollama connected', type: 'info' },
    { time: '10:42:26', msg: '🔍 Search worker ready', type: 'info' },
    { time: '10:42:27', msg: '⚡ System nominal', type: 'success' },
  ]);
  
  const terminalRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    // Simulate logs
    const interval = setInterval(() => {
      const events = [
        { msg: '💓 Heartbeat OK', type: 'info' },
        { msg: '📊 CPU: 23% RAM: 42%', type: 'info' },
        { msg: '🔧 Worker: system_monitor active', type: 'debug' },
      ];
      
      const random = events[Math.floor(Math.random() * events.length)];
      const now = new Date();
      const time = now.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
      
      setLogs(prev => [...prev.slice(-50), { time, ...random }]);
    }, 5000);
    
    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    if (terminalRef.current) {
      terminalRef.current.scrollTop = terminalRef.current.scrollHeight;
    }
  }, [logs]);

  return (
    <div className="terminal-container h-full overflow-auto" ref={terminalRef}>
      {logs.map((log, i) => (
        <div key={i} className="terminal-line">
          <span className="timestamp">[{log.time}]</span>
          <span className={
            log.type === 'success' ? 'text-status-success' :
            log.type === 'error' ? 'text-status-error' :
            log.type === 'debug' ? 'text-accent-primary' : ''
          }>
            {log.msg}
          </span>
        </div>
      ))}
    </div>
  );
}
