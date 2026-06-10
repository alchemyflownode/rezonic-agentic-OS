'use client';

import { usePathname } from 'next/navigation';
import { motion } from 'framer-motion';
import { Shield, Cpu, Activity, FileText, Users, FileCheck, BookOpen } from 'lucide-react';
import Link from 'next/link';
import { useState, useEffect } from 'react';

export const OSHeader = () => {
  const pathname = usePathname();
  const segments = pathname.split('/').filter(Boolean);
  const [activeHash, setActiveHash] = useState('');

  // Navigation items for the top bar
  const navItems = [
    { name: 'Protocol', href: '#protocol', icon: Shield, description: 'Constitutional enforcement' },
    { name: 'Workers', href: '#workers', icon: Users, description: '53 specialized agents' },
    { name: 'Audit', href: '#audit', icon: FileCheck, description: 'Drift chain records' },
    { name: 'Docs', href: '#docs', icon: BookOpen, description: 'Whitepaper & documentation' },
  ];

  // Handle hash change for active state
  useEffect(() => {
    const handleHashChange = () => {
      setActiveHash(window.location.hash);
    };
    
    handleHashChange();
    window.addEventListener('hashchange', handleHashChange);
    
    return () => window.removeEventListener('hashchange', handleHashChange);
  }, []);

  // Smooth scroll to section
  const scrollToSection = (e: React.MouseEvent<HTMLAnchorElement>, hash: string) => {
    e.preventDefault();
    const element = document.querySelector(hash);
    if (element) {
      element.scrollIntoView({ behavior: 'smooth' });
      window.history.pushState(null, '', hash);
      setActiveHash(hash);
    }
  };

  return (
    <motion.div 
      className="h-16 border-b border-white/[0.05] bg-[#0a0a0c]/80 backdrop-blur-xl flex items-center px-8 justify-between sticky top-0 z-50"
      initial={{ y: -20, opacity: 0 }}
      animate={{ y: 0, opacity: 1 }}
      transition={{ duration: 0.3 }}
    >
      {/* LEFT SECTION: Version & Breadcrumb */}
      <div className="flex items-center gap-4">
        <motion.div 
          className="text-xs font-mono text-[#565f89] uppercase tracking-widest border border-white/[0.05] px-2 py-1 rounded bg-white/[0.02]"
          whileHover={{ scale: 1.05 }}
        >
          v13.3.0
        </motion.div>
        <div className="flex items-center gap-2 text-sm">
          <span className="text-[#565f89] uppercase tracking-tighter">Root</span>
          {segments.map((s, i) => (
            <div key={i} className="flex items-center gap-2">
              <span className="text-white/[0.1]">/</span>
              <motion.span 
                className="font-semibold text-[#c0caf5] capitalize"
                initial={{ opacity: 0, x: -5 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: i * 0.1 }}
              >
                {s}
              </motion.span>
            </div>
          ))}
        </div>
      </div>

      {/* CENTER SECTION: Navigation */}
      <div className="flex items-center gap-2 bg-white/[0.02] rounded-full p-1 border border-white/[0.05]">
        {navItems.map((item) => {
          const Icon = item.icon;
          const isActive = activeHash === item.href;
          
          return (
            <motion.a
              key={item.name}
              href={item.href}
              onClick={(e) => scrollToSection(e, item.href)}
              className={`relative px-4 py-1.5 rounded-full text-xs font-mono transition-all cursor-pointer ${
                isActive 
                  ? 'text-[#9ece6a]' 
                  : 'text-[#565f89] hover:text-[#c0caf5]'
              }`}
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
              title={item.description}
            >
              <span className="flex items-center gap-2">
                <Icon className="w-3.5 h-3.5" />
                {item.name}
              </span>
              {isActive && (
                <motion.div
                  layoutId="activeNav"
                  className="absolute inset-0 bg-[#9ece6a]/10 rounded-full border border-[#9ece6a]/30"
                  transition={{ type: "spring", bounce: 0.2, duration: 0.6 }}
                />
              )}
            </motion.a>
          );
        })}
      </div>

      {/* RIGHT SECTION: Security & Logout */}
      <div className="flex items-center gap-6">
        <div className="text-right">
          <div className="text-[10px] text-[#565f89] uppercase font-bold tracking-widest">Integrity Score</div>
          <div className="text-xs font-mono text-[#9ece6a] flex items-center gap-1">
            <Shield className="w-3 h-3" />
            98.2% // DRIFT CHAIN: 10
          </div>
        </div>
        <div className="h-8 w-[1px] bg-gradient-to-b from-transparent via-white/[0.1] to-transparent" />
        <motion.button 
          className="bg-white/[0.03] hover:bg-white/[0.08] border border-white/[0.05] text-[#c0caf5] text-xs px-4 py-2 rounded-md transition-all active:scale-95 backdrop-blur-sm"
          whileHover={{ scale: 1.02 }}
          whileTap={{ scale: 0.98 }}
        >
          LOGOUT
        </motion.button>
      </div>
    </motion.div>
  );
};