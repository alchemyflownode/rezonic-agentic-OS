'use client';

import { motion } from 'framer-motion';
import { useState } from 'react';
import { 
  Settings, Sliders, Palette, Type,
  Maximize, Minimize, RotateCw
} from 'lucide-react';

export function PremiumInspector() {
  const [opacity, setOpacity] = useState(100);
  const [blur, setBlur] = useState(0);

  return (
    <motion.div 
      className="w-72 h-full bg-[#252525] border-l border-white/10 p-4"
      initial={{ x: 20, opacity: 0 }}
      animate={{ x: 0, opacity: 1 }}
    >
      <div className="panel-header">
        <span>INSPECTOR</span>
        <Settings className="w-4 h-4 text-white/50" />
      </div>
      
      {/* Properties */}
      <div className="space-y-4">
        <div>
          <label className="text-xs text-white/50 block mb-1">Opacity</label>
          <input 
            type="range" 
            className="slider w-full"
            value={opacity}
            onChange={(e) => setOpacity(parseInt(e.target.value))}
          />
          <div className="flex justify-between text-xs text-white/30 mt-1">
            <span>0%</span>
            <span>{opacity}%</span>
            <span>100%</span>
          </div>
        </div>
        
        <div>
          <label className="text-xs text-white/50 block mb-1">Blur</label>
          <input 
            type="range" 
            className="slider w-full"
            value={blur}
            onChange={(e) => setBlur(parseInt(e.target.value))}
          />
        </div>
        
        <div className="divider" />
        
        {/* Color Picker */}
        <div>
          <label className="text-xs text-white/50 block mb-2">Color</label>
          <div className="grid grid-cols-5 gap-1">
            {['#0A84FF', '#BF5AF2', '#32D74B', '#FF9F0A', '#FF453A'].map(color => (
              <button
                key={color}
                className="w-6 h-6 rounded border border-white/10"
                style={{ backgroundColor: color }}
              />
            ))}
          </div>
        </div>
        
        <div className="divider" />
        
        {/* Transform Controls */}
        <div>
          <label className="text-xs text-white/50 block mb-2">Transform</label>
          <div className="grid grid-cols-3 gap-1">
            <button className="p-1 bg-white/5 hover:bg-white/10 rounded flex items-center justify-center">
              <Maximize size={14} />
            </button>
            <button className="p-1 bg-white/5 hover:bg-white/10 rounded flex items-center justify-center">
              <Minimize size={14} />
            </button>
            <button className="p-1 bg-white/5 hover:bg-white/10 rounded flex items-center justify-center">
              <RotateCw size={14} />
            </button>
          </div>
        </div>
        
        <div className="divider" />
        
        {/* Quick Actions */}
        <button className="w-full p-2 bg-blue-500 hover:bg-blue-600 rounded text-sm font-medium">
          Apply Changes
        </button>
      </div>
    </motion.div>
  );
}
