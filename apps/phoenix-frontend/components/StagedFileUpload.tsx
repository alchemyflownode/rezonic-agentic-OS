'use client';

import React, { useState, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Paperclip, X, FileText } from 'lucide-react';

interface StagedFile {
  id: string;
  file: File;
  preview?: string;
}

interface StagedFileUploadProps {
  onFilesStaged: (files: StagedFile[]) => void;
  onFileRemove: (fileId: string) => void;
  stagedFiles: StagedFile[];
  accept?: string;
  maxSize?: number; // in MB
}

export const StagedFileUpload: React.FC<StagedFileUploadProps> = ({
  onFilesStaged,
  onFileRemove,
  stagedFiles,
  accept = '.csv,.xlsx,.xls',
  maxSize = 10
}) => {
  const [isDragging, setIsDragging] = useState(false);

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  }, []);

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
  }, []);

  const processFiles = useCallback((files: FileList | null) => {
    if (!files) return;

    const newFiles: StagedFile[] = [];
    
    Array.from(files).forEach(file => {
      // Check file size
      if (file.size > maxSize * 1024 * 1024) {
        alert(`File ${file.name} exceeds ${maxSize}MB limit`);
        return;
      }

      // Check file extension
      const ext = file.name.split('.').pop()?.toLowerCase();
      const allowed = accept.split(',').map(e => e.trim().replace('.', ''));
      
      if (ext && allowed.includes(ext)) {
        newFiles.push({
          id: `${file.name}-${Date.now()}-${Math.random()}`,
          file
        });
      }
    });

    if (newFiles.length > 0) {
      onFilesStaged(newFiles);
    }
  }, [accept, maxSize, onFilesStaged]);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    processFiles(e.dataTransfer.files);
  }, [processFiles]);

  const handleFileSelect = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    processFiles(e.target.files);
    e.target.value = ''; // Reset input
  }, [processFiles]);

  const formatFileSize = (bytes: number) => {
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
    return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
  };

  return (
    <div className="relative">
      {/* Staged Files */}
      <AnimatePresence>
        {stagedFiles.length > 0 && (
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
            className="mb-3 flex flex-wrap gap-2"
          >
            {stagedFiles.map((staged) => (
              <motion.div
                key={staged.id}
                layout
                initial={{ scale: 0.8 }}
                animate={{ scale: 1 }}
                exit={{ scale: 0.8 }}
                className="group relative bg-[#12141A] border border-[#00E5FF]/30 rounded-lg px-3 py-2 pr-8 flex items-center gap-2"
              >
                <FileText className="w-4 h-4 text-[#00E5FF]" />
                <div className="flex flex-col">
                  <span className="text-xs text-white max-w-[150px] truncate">
                    {staged.file.name}
                  </span>
                  <span className="text-[8px] text-white/40">
                    {formatFileSize(staged.file.size)}
                  </span>
                </div>
                <button
                  onClick={() => onFileRemove(staged.id)}
                  className="absolute right-2 top-1/2 -translate-y-1/2 opacity-0 group-hover:opacity-100 transition-opacity"
                >
                  <X className="w-3 h-3 text-white/40 hover:text-white" />
                </button>
              </motion.div>
            ))}
          </motion.div>
        )}
      </AnimatePresence>

      {/* Upload Area */}
      <div
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        className={`relative rounded-xl border-2 border-dashed transition-all ${
          isDragging 
            ? 'border-[#00E5FF] bg-[#00E5FF]/5' 
            : 'border-[#1F222A] hover:border-[#00E5FF]/50'
        }`}
      >
        <input
          type="file"
          multiple
          accept={accept}
          onChange={handleFileSelect}
          className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
        />
        <div className="py-3 px-4 flex items-center gap-3">
          <Paperclip className={`w-4 h-4 ${isDragging ? 'text-[#00E5FF]' : 'text-[#8A8F9B]'}`} />
          <span className="text-[10px] font-mono uppercase tracking-wider">
            {isDragging ? 'DROP FILES HERE' : 'DRAG & DROP OR CLICK TO ATTACH'}
          </span>
          {stagedFiles.length > 0 && (
            <span className="text-[8px] px-2 py-1 bg-[#00E5FF]/10 rounded-full text-[#00E5FF]">
              {stagedFiles.length} file{stagedFiles.length > 1 ? 's' : ''} staged
            </span>
          )}
        </div>
      </div>
    </div>
  );
};