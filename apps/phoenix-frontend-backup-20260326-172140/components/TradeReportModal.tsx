// components/TradeReportModal.tsx
'use client';

import React from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { X, TrendingUp, TrendingDown, ShieldCheck, Clock, Activity, ArrowUpRight, ArrowDownRight } from 'lucide-react';

interface TradeReportModalProps {
  isOpen: boolean;
  onClose: () => void;
  trade: {
    id: string;
    type: 'BUY' | 'SELL';
    pair: string;
    amount: number;
    price: number;
    time: string;
    status: string;
    driftLock?: string;
  } | null;
}

export const TradeReportModal: React.FC<TradeReportModalProps> = ({ isOpen, onClose, trade }) => {
  if (!isOpen || !trade) return null;

  const formatPHP = (val: number) => new Intl.NumberFormat('en-PH', {
    style: 'currency', currency: 'PHP', minimumFractionDigits: 0, maximumFractionDigits: 0
  }).format(val).replace('PHP', '₱');

  const totalValue = trade.amount * trade.price;
  const isBuy = trade.type === 'BUY';

  return (
    <AnimatePresence>
      {isOpen && (
        <div className="fixed inset-0 z-[200] flex items-center justify-center bg-black/90 backdrop-blur-md p-4">
          <motion.div
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 0.9 }}
            className="w-full max-w-md bg-[#0a0a0c] border border-[#00E5FF]/30 rounded-2xl overflow-hidden shadow-2xl"
          >
            {/* Header */}
            <div className="flex items-center justify-between p-4 border-b border-white/10 bg-gradient-to-r from-[#00E5FF]/10 to-transparent">
              <div className="flex items-center gap-2">
                <div className={`p-1.5 rounded-lg ${isBuy ? 'bg-[#00e676]/20' : 'bg-[#ff0055]/20'}`}>
                  {isBuy ? (
                    <ArrowUpRight className="w-4 h-4 text-[#00e676]" />
                  ) : (
                    <ArrowDownRight className="w-4 h-4 text-[#ff0055]" />
                  )}
                </div>
                <div>
                  <h2 className="text-sm font-bold text-white">Trade Report</h2>
                  <p className="text-[8px] font-mono text-zinc-500">SCE Verified Execution</p>
                </div>
              </div>
              <button
                onClick={onClose}
                className="p-1.5 rounded-lg hover:bg-white/10 transition-colors"
              >
                <X className="w-4 h-4 text-zinc-400" />
              </button>
            </div>

            {/* Content */}
            <div className="p-5 space-y-4">
              {/* Trade Type Badge */}
              <div className="flex justify-center">
                <div className={`px-4 py-2 rounded-full text-xs font-bold uppercase tracking-wider ${
                  isBuy 
                    ? 'bg-[#00e676]/20 text-[#00e676] border border-[#00e676]/30' 
                    : 'bg-[#ff0055]/20 text-[#ff0055] border border-[#ff0055]/30'
                }`}>
                  {trade.type} ORDER
                </div>
              </div>

              {/* Trade Details */}
              <div className="space-y-3 bg-black/30 rounded-xl p-4 border border-white/5">
                <div className="flex justify-between items-center">
                  <span className="text-xs text-zinc-500">Pair</span>
                  <span className="text-sm font-mono text-white">{trade.pair}</span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-xs text-zinc-500">Amount</span>
                  <span className="text-sm font-mono text-white">{trade.amount} units</span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-xs text-zinc-500">Price</span>
                  <span className="text-sm font-mono text-white">{formatPHP(trade.price)}</span>
                </div>
                <div className="flex justify-between items-center pt-2 border-t border-white/10">
                  <span className="text-xs text-zinc-500">Total Value</span>
                  <span className="text-lg font-bold text-[#00E5FF]">{formatPHP(totalValue)}</span>
                </div>
              </div>

              {/* Timestamp & Verification */}
              <div className="space-y-2">
                <div className="flex items-center gap-2 text-[9px] text-zinc-500">
                  <Clock className="w-3 h-3" />
                  <span>Executed at {trade.time}</span>
                </div>
                {trade.driftLock && (
                  <div className="flex items-center gap-2 text-[9px] text-zinc-500 bg-[#00e676]/5 p-2 rounded-lg border border-[#00e676]/20">
                    <ShieldCheck className="w-3 h-3 text-[#00e676]" />
                    <span className="font-mono">SCE Drift Lock: {trade.driftLock.substring(0, 12)}...</span>
                  </div>
                )}
              </div>

              {/* Status */}
              <div className="flex items-center justify-between pt-2 border-t border-white/10">
                <span className="text-xs text-zinc-500">Status</span>
                <span className="text-xs font-mono text-[#00e676] bg-[#00e676]/10 px-2 py-1 rounded-full">
                  {trade.status}
                </span>
              </div>
            </div>

            {/* Footer */}
            <div className="p-4 border-t border-white/10 bg-black/20">
              <button
                onClick={onClose}
                className="w-full py-2 rounded-lg bg-gradient-to-r from-[#00E5FF]/20 to-[#9B72CB]/20 border border-[#00E5FF]/30 text-[#00E5FF] text-xs font-mono uppercase tracking-wider hover:bg-[#00E5FF]/30 transition-all"
              >
                Close Report
              </button>
            </div>
          </motion.div>
        </div>
      )}
    </AnimatePresence>
  );
};

export default TradeReportModal;