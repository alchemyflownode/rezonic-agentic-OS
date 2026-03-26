'use client';

import { useState } from 'react';
import { useRouter, usePathname } from 'next/navigation';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  LayoutDashboard, Cpu, Database, Scale, Scan, 
  Code, TrendingUp, Brain, Zap, ChevronRight,
  DollarSign, Menu, X
} from 'lucide-react';

const systemRoutes = [
  { path: '/system/dashboard', icon: LayoutDashboard, label: 'Dashboard' },
  { path: '/system/workers', icon: Cpu, label: 'Workers' },
  { path: '/system/memory', icon: Database, label: 'Memory' },
  { path: '/system/constitution', icon: Scale, label: 'Constitution' },
  { path: '/system/scanner', icon: Scan, label: 'Scanner' },
  { path: '/system/appbuilder', icon: Code, label: 'App Builder' },
];

const tradingRoutes = [
  { path: '/trading', icon: TrendingUp, label: 'Live Trading' },
  { path: '/trading/strategies', icon: Brain, label: 'Strategies' },
  { path: '/trading/backtest', icon: Zap, label: 'Backtest' },
  { path: '/paper-trading', icon: DollarSign, label: 'Paper Trading' },
];

export const OSSidebar = () => {
  const router = useRouter();
  const pathname = usePathname();
  const [isCollapsed, setIsCollapsed] = useState(false);

  const NavItem = ({ route }: { route: typeof systemRoutes[0] }) => {
    const isActive = pathname === route.path;
    
    return (
      <motion.button
        onClick={() => router.push(route.path)}
        className="group relative w-full flex items-center justify-between px-3 py-2.5 mb-1 rounded-lg transition-all duration-200 overflow-hidden"
        whileHover={{ x: 4 }}
        whileTap={{ scale: 0.98 }}
      >
        {/* Background Highlight with Animation */}
        {isActive && (
          <motion.div 
            layoutId="active-pill"
            className="absolute inset-0 bg-gradient-to-r from-purple-900/40 to-transparent border-l-2 border-purple-500"
            transition={{ type: "spring", stiffness: 300, damping: 30 }}
          />
        )}
        
        {/* Hover Glow Effect */}
        <div className="absolute inset-0 opacity-0 group-hover:opacity-100 transition-opacity duration-300 bg-gradient-to-r from-white/5 to-transparent" />
        
        <div className="relative flex items-center gap-3 z-10">
          <motion.div
            whileHover={{ scale: 1.1 }}
            transition={{ type: "spring", stiffness: 400, damping: 10 }}
          >
            <route.icon className={`w-4 h-4 transition-all duration-200 ${isActive ? 'text-purple-400 drop-shadow-[0_0_4px_rgba(147,51,234,0.5)]' : 'text-zinc-500 group-hover:text-zinc-300'}`} />
          </motion.div>
          
          <AnimatePresence>
            {!isCollapsed && (
              <motion.span 
                initial={{ opacity: 0, x: -10 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: -10 }}
                transition={{ duration: 0.2 }}
                className={`text-sm font-medium tracking-wide transition-colors ${isActive ? 'text-white' : 'text-zinc-400 group-hover:text-zinc-200'}`}
              >
                {route.label}
              </motion.span>
            )}
          </AnimatePresence>
        </div>

        {isActive && !isCollapsed && (
          <motion.div 
            initial={{ opacity: 0, x: -5 }} 
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: 0.1 }}
          >
            <ChevronRight className="w-3 h-3 text-purple-500" />
          </motion.div>
        )}
      </motion.button>
    );
  };

  return (
    <motion.div 
      className="relative bg-zinc-950 border-r border-zinc-800/50 flex flex-col h-full overflow-hidden"
      initial={{ width: 260 }}
      animate={{ width: isCollapsed ? 68 : 260 }}
      transition={{ type: "spring", stiffness: 300, damping: 30 }}
      onMouseEnter={() => setIsCollapsed(false)}
      onMouseLeave={() => setIsCollapsed(true)}
    >
      {/* Logo Section */}
      <div className="p-4">
        <motion.div 
          className="flex items-center justify-center gap-2 mb-6"
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
        >
          <motion.div 
            className="w-10 h-10 bg-gradient-to-br from-purple-600 to-purple-800 rounded-xl flex items-center justify-center shadow-[0_0_15px_rgba(147,51,234,0.4)]"
            whileHover={{ scale: 1.05, rotate: 5 }}
            whileTap={{ scale: 0.95 }}
          >
            <Zap className="w-5 h-5 text-white" />
          </motion.div>
          
          <AnimatePresence>
            {!isCollapsed && (
              <motion.h1 
                initial={{ opacity: 0, x: -10 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: -10 }}
                className="text-xl font-black tracking-tighter bg-gradient-to-r from-white to-purple-400 bg-clip-text text-transparent"
              >
                PHOENIX <span className="text-purple-500">OS</span>
              </motion.h1>
            )}
          </AnimatePresence>
        </motion.div>

        <nav className="space-y-8">
          <div>
            <AnimatePresence>
              {!isCollapsed && (
                <motion.h3 
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  exit={{ opacity: 0 }}
                  className="text-[10px] uppercase tracking-[0.2em] text-zinc-500 font-bold mb-4 px-3"
                >
                  System Core
                </motion.h3>
              )}
            </AnimatePresence>
            {systemRoutes.map((route, i) => (
              <motion.div
                key={route.path}
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: i * 0.05 }}
              >
                <NavItem route={route} />
              </motion.div>
            ))}
          </div>

          <div>
            <AnimatePresence>
              {!isCollapsed && (
                <motion.h3 
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  exit={{ opacity: 0 }}
                  className="text-[10px] uppercase tracking-[0.2em] text-zinc-500 font-bold mb-4 px-3"
                >
                  Terminal
                </motion.h3>
              )}
            </AnimatePresence>
            {tradingRoutes.map((route, i) => (
              <motion.div
                key={route.path}
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: 0.3 + i * 0.05 }}
              >
                <NavItem route={route} />
              </motion.div>
            ))}
          </div>
        </nav>
      </div>
      
      {/* Bottom Section */}
      <motion.div 
        className="mt-auto p-4 border-t border-zinc-800/50 bg-gradient-to-t from-zinc-900/30 to-transparent"
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.5 }}
      >
        <div className="flex items-center justify-center gap-3 px-2">
          <motion.div 
            className="w-2 h-2 rounded-full bg-emerald-500"
            animate={{ scale: [1, 1.2, 1] }}
            transition={{ duration: 2, repeat: Infinity }}
          />
          <AnimatePresence>
            {!isCollapsed && (
              <motion.span 
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                className="text-xs font-mono text-zinc-500 uppercase tracking-widest"
              >
                Network Secure
              </motion.span>
            )}
          </AnimatePresence>
        </div>
        
        <AnimatePresence>
          {!isCollapsed && (
            <motion.div 
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: 10 }}
              className="mt-2 text-[8px] font-mono text-zinc-600 text-center"
            >
              v13.3.0 • SCE Active
            </motion.div>
          )}
        </AnimatePresence>
      </motion.div>

      {/* Collapse Indicator */}
      {isCollapsed && (
        <motion.div 
          className="absolute top-1/2 right-0 transform translate-x-1/2 -translate-y-1/2"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
        >
          <div className="w-1 h-8 bg-purple-500/50 rounded-full" />
        </motion.div>
      )}
    </motion.div>
  );
};