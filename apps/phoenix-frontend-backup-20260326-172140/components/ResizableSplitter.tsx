'use client';

import React, { useState, useRef, useCallback, useEffect } from 'react';

interface ResizableSplitterProps {
  leftPanel: React.ReactNode;
  rightPanel: React.ReactNode;
  defaultLeftWidth?: number;
  minLeftWidth?: number;
  maxLeftWidth?: number;
  className?: string;
}

export default function ResizableSplitter({
  leftPanel,
  rightPanel,
  defaultLeftWidth = 22,
  minLeftWidth = 15,
  maxLeftWidth = 30,
  className = ''
}: ResizableSplitterProps) {
  const [leftWidth, setLeftWidth] = useState(defaultLeftWidth);
  const [isDragging, setIsDragging] = useState(false);
  const containerRef = useRef<HTMLDivElement>(null);
  const dragStartX = useRef(0);
  const dragStartWidth = useRef(0);

  useEffect(() => {
    const saved = localStorage.getItem('splitter-width');
    if (saved) {
      const w = parseFloat(saved);
      if (!isNaN(w) && w >= minLeftWidth && w <= maxLeftWidth) setLeftWidth(w);
    }
  }, [minLeftWidth, maxLeftWidth]);

  useEffect(() => {
    localStorage.setItem('splitter-width', leftWidth.toString());
  }, [leftWidth]);

  const handleMouseDown = useCallback((e: React.MouseEvent) => {
    e.preventDefault();
    setIsDragging(true);
    dragStartX.current = e.clientX;
    dragStartWidth.current = leftWidth;
    document.body.style.cursor = 'col-resize';
    document.body.style.userSelect = 'none';
  }, [leftWidth]);

  const handleMouseMove = useCallback((e: MouseEvent) => {
    if (!isDragging || !containerRef.current) return;
    const rect = containerRef.current.getBoundingClientRect();
    const delta = (e.clientX - dragStartX.current) / rect.width * 100;
    let newWidth = dragStartWidth.current + delta;
    newWidth = Math.max(minLeftWidth, Math.min(maxLeftWidth, newWidth));
    setLeftWidth(newWidth);
  }, [isDragging, minLeftWidth, maxLeftWidth]);

  const handleMouseUp = useCallback(() => {
    setIsDragging(false);
    document.body.style.cursor = '';
    document.body.style.userSelect = '';
  }, []);

  useEffect(() => {
    if (isDragging) {
      window.addEventListener('mousemove', handleMouseMove);
      window.addEventListener('mouseup', handleMouseUp);
      return () => {
        window.removeEventListener('mousemove', handleMouseMove);
        window.removeEventListener('mouseup', handleMouseUp);
      };
    }
  }, [isDragging, handleMouseMove, handleMouseUp]);

  return (
    <div ref={containerRef} className={`flex h-full w-full ${className}`}>
      <div style={{ width: `${leftWidth}%` }} className="overflow-hidden">{leftPanel}</div>
      <div className="w-1 relative group">
        <div onMouseDown={handleMouseDown} className={`absolute inset-0 cursor-col-resize hover:bg-[#7dcfff]/30 transition-all ${isDragging ? 'bg-[#7dcfff]/50' : ''}`} />
      </div>
      <div style={{ width: `${100 - leftWidth}%` }} className="overflow-hidden">{rightPanel}</div>
    </div>
  );
}
