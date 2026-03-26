'use client';

import { motion } from 'framer-motion';
import { 
  Square, Circle, Type, Move, 
  ZoomIn, ZoomOut, Undo, Redo,
  Settings, HelpCircle 
} from 'lucide-react';

export function PremiumToolbar() {
  return (
    <motion.div 
      className="toolbar"
      initial={{ opacity: 0, y: -20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
    >
      {/* App Icon */}
      <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center mr-2">
        <span className="text-white font-bold text-sm">AI</span>
      </div>
      
      {/* File Menu */}
      <button className="toolbar-button">File</button>
      <button className="toolbar-button">Edit</button>
      <button className="toolbar-button">View</button>
      <button className="toolbar-button">Window</button>
      <button className="toolbar-button">Help</button>
      
      <div className="divider vertical" />
      
      {/* Tools */}
      <button className="toolbar-button"><Square size={16} /></button>
      <button className="toolbar-button"><Circle size={16} /></button>
      <button className="toolbar-button"><Type size={16} /></button>
      <button className="toolbar-button"><Move size={16} /></button>
      
      <div className="divider vertical" />
      
      {/* Zoom Controls */}
      <button className="toolbar-button"><ZoomOut size={16} /></button>
      <span className="text-xs text-white/50 px-1">100%</span>
      <button className="toolbar-button"><ZoomIn size={16} /></button>
      
      <div className="divider vertical" />
      
      {/* Undo/Redo */}
      <button className="toolbar-button"><Undo size={16} /></button>
      <button className="toolbar-button"><Redo size={16} /></button>
      
      <div className="flex-1" />
      
      {/* Right side */}
      <button className="toolbar-button"><Settings size={16} /></button>
      <button className="toolbar-button"><HelpCircle size={16} /></button>
    </motion.div>
  );
}
