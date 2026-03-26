'use client';

import { motion } from 'framer-motion';

export interface ChainRecord {
  intent: string;
  chain: string[];
  drift: number;
  success: boolean;
  timestamp: string;
}

interface ChainHistoryProps {
  history: ChainRecord[];
}

export default function ChainHistory({ history }: ChainHistoryProps) {
  return (
    <div className="bg-[#0E1015]/90 backdrop-blur-md border border-[#1F222A] rounded-xl p-5 shadow-[0_8px_30px_rgba(0,0,0,0.5)]">
      <h3 className="text-xs font-bold text-white uppercase tracking-[0.15em] mb-4 flex items-center gap-2">
        <span className="text-[#B388FF] drop-shadow-[0_0_5px_#B388FF]">📋</span> Policy Executions
      </h3>

      <div className="space-y-3 max-h-64 overflow-y-auto custom-scrollbar pr-2">
        {history.length === 0 ? (
          <div className="text-center py-8">
            <div className="text-[#4B5563] text-sm mb-2">No executions logged</div>
            <div className="text-[10px] font-mono text-[#8A8F9B] uppercase tracking-wider">Awaiting Intents</div>
          </div>
        ) : (
          history.map((record, i) => (
            <motion.div
              key={i}
              initial={{ opacity: 0, x: -10 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: i * 0.05 }}
              className="bg-[#12141A] border border-[#1F222A] rounded-lg p-3 hover:border-[#00E5FF]/30 transition-colors"
            >
              <div className="flex items-start justify-between gap-2 mb-2">
                <p className="text-[11px] text-white/90 line-clamp-1 flex-1 font-mono">{record.intent}</p>
                <span className={`text-[8px] px-1.5 py-0.5 rounded-sm font-mono tracking-widest ${
                  record.success 
                    ? 'bg-[#10b981]/10 text-[#10b981] border border-[#10b981]/30' 
                    : 'bg-[#FF4500]/10 text-[#FF4500] border border-[#FF4500]/30'
                }`}>
                  {record.success ? 'PASS' : 'FAIL'}
                </span>
              </div>

              <div className="flex items-center gap-1 mb-2 flex-wrap">
                {record.chain.map((worker, idx) => (
                  <div key={idx} className="flex items-center">
                    <span className="text-[9px] font-mono px-1.5 py-0.5 rounded bg-[#0A0C10] border border-[#2A2E38] text-[#00E5FF]">
                      {worker}
                    </span>
                    {idx < record.chain.length - 1 && (
                      <span className="text-[#2A2E38] mx-1 text-[10px]">▶</span>
                    )}
                  </div>
                ))}
              </div>

              <div className="flex items-center justify-between text-[9px] font-mono text-[#4B5563]">
                <span>DRIFT: <span className={record.drift > 0.15 ? 'text-[#FF9800]' : 'text-[#10b981]'}>{(record.drift * 100).toFixed(1)}%</span></span>
                <span>{record.timestamp}</span>
              </div>
            </motion.div>
          ))
        )}
      </div>
    </div>
  );
}