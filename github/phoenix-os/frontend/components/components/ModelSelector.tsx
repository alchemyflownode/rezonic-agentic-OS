'use client';

import React, { useState, useEffect } from 'react';
import { 
  Brain, Cpu, Eye, Zap, Shield, Code, 
  ChevronDown, Check, AlertTriangle 
} from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

interface ModelInfo {
  name: string;
  size: string;
  strength: string;
  bestFor: string[];
  description: string;
  recommended?: boolean;
  vramWarning?: string;
}

interface ModelCategory {
  [key: string]: ModelInfo[];
}

const modelCategories: ModelCategory = {
  "💻 CODE & ARCHITECTURE": [
    { 
      name: "qwen2.5-coder:14b", 
      size: "9.0 GB", 
      strength: "⭐⭐⭐⭐⭐", 
      bestFor: ["Code Generation", "Architecture Design", "Debugging"],
      description: "Best for BrainWorker - generates production-ready code",
      recommended: true
    },
    { 
      name: "qwen2.5-coder:7b", 
      size: "4.7 GB", 
      strength: "⭐⭐⭐⭐", 
      bestFor: ["Code Generation", "Script Writing"],
      description: "Good balance of speed and quality"
    },
    { 
      name: "deepseek-coder:latest", 
      size: "776 MB", 
      strength: "⭐⭐⭐", 
      bestFor: ["Quick Code Snippets", "Simple Functions"],
      description: "Ultra-fast for quick coding tasks"
    }
  ],
  
  "🧠 REASONING & GOVERNANCE": [
    { 
      name: "qwen:32b", 
      size: "18 GB", 
      strength: "⭐⭐⭐⭐⭐", 
      bestFor: ["Constitutional Reasoning", "Complex Analysis", "Strategic Planning"],
      description: "Best for ConstitutionalGovernor - deep reasoning",
      vramWarning: "Requires 18GB VRAM - may swap"
    },
    { 
      name: "gemma2:9b", 
      size: "5.4 GB", 
      strength: "⭐⭐⭐⭐", 
      bestFor: ["Reasoning", "Analysis", "Decision Making"],
      description: "Excellent for ConsensusEngine"
    },
    { 
      name: "sovereign-constitutional:latest", 
      size: "3.8 GB", 
      strength: "⭐⭐⭐⭐", 
      bestFor: ["Constitutional Checks", "Governance", "Policy"],
      description: "Custom model for your 9 laws"
    },
    { 
      name: "sovereign-architect:latest", 
      size: "2.0 GB", 
      strength: "⭐⭐⭐", 
      bestFor: ["System Design", "Architecture"],
      description: "Custom architecture model"
    }
  ],
  
  "🖼️ VISION & MULTIMODAL": [
    { 
      name: "llama3.2-vision:11b", 
      size: "7.8 GB", 
      strength: "⭐⭐⭐⭐⭐", 
      bestFor: ["Image Analysis", "Visual Understanding", "Screen Reading"],
      description: "Best for VisionWorker - multimodal understanding"
    },
    { 
      name: "llava:7b", 
      size: "4.7 GB", 
      strength: "⭐⭐⭐⭐", 
      bestFor: ["Image Description", "Visual QA"],
      description: "Solid vision-language model"
    },
    { 
      name: "moondream:1.8b", 
      size: "1.7 GB", 
      strength: "⭐⭐", 
      bestFor: ["Basic Image Recognition"],
      description: "Lightweight vision model"
    },
    { 
      name: "qwen3-vl:8b", 
      size: "6.1 GB", 
      strength: "⭐⭐⭐⭐", 
      bestFor: ["Vision-Language Tasks", "Document Understanding"],
      description: "Latest Qwen vision model"
    }
  ],
  
  "⚡ FAST & LIGHTWEIGHT": [
    { 
      name: "llama3.2:latest", 
      size: "2.0 GB", 
      strength: "⭐⭐⭐", 
      bestFor: ["Quick Responses", "Simple Chat", "Prototyping"],
      description: "Fastest response time"
    },
    { 
      name: "llama3.2:1b", 
      size: "1.3 GB", 
      strength: "⭐⭐", 
      bestFor: ["Very Fast", "Simple Tasks"],
      description: "Ultra-lightweight"
    },
    { 
      name: "phi3.5:3.8b", 
      size: "2.2 GB", 
      strength: "⭐⭐⭐⭐", 
      bestFor: ["Efficient Reasoning", "Mobile/Edge"],
      description: "Microsoft's efficient model"
    },
    { 
      name: "phi3:medium", 
      size: "7.9 GB", 
      strength: "⭐⭐⭐⭐", 
      bestFor: ["Balanced Performance"],
      description: "Good all-around performer"
    },
    { 
      name: "smollm2:360m", 
      size: "725 MB", 
      strength: "⭐", 
      bestFor: ["Extreme Speed", "Embeddings"],
      description: "Tiniest model - instant responses"
    }
  ],
  
  "🔬 SPECIALIZED": [
    { 
      name: "phi4:latest", 
      size: "9.1 GB", 
      strength: "⭐⭐⭐⭐", 
      bestFor: ["Scientific Reasoning", "Math"],
      description: "Phi-4 specialized reasoning"
    },
    { 
      name: "glm4:latest", 
      size: "5.5 GB", 
      strength: "⭐⭐⭐", 
      bestFor: ["Chinese Language", "Bilingual Tasks"],
      description: "Good for multilingual"
    },
    { 
      name: "llama3:8b", 
      size: "4.7 GB", 
      strength: "⭐⭐⭐⭐", 
      bestFor: ["General Purpose"],
      description: "Solid all-around model"
    },
    { 
      name: "gpt-oss:20b", 
      size: "13 GB", 
      strength: "⭐⭐⭐⭐⭐", 
      bestFor: ["Heavy Lifting", "Complex Tasks"],
      description: "Massive model for hard problems",
      vramWarning: "Requires 13GB VRAM"
    }
  ]
};

interface ModelSelectorProps {
  onModelChange?: (worker: string, model: string) => void;
  currentModels?: Record<string, string>;
}

export const ModelSelector: React.FC<ModelSelectorProps> = ({ 
  onModelChange,
  currentModels = {
    brain: 'qwen2.5-coder:14b',
    vision: 'llama3.2-vision:11b',
    reason: 'gemma2:9b',
    fast: 'phi3.5:3.8b'
  }
}) => {
  const [selectedCategory, setSelectedCategory] = useState<string>("💻 CODE & ARCHITECTURE");
  const [selectedWorker, setSelectedWorker] = useState<string>('brain');
  const [isOpen, setIsOpen] = useState(false);
  const [vramInfo, setVramInfo] = useState({ total: 12, used: 0 });

  const workers = [
    { id: 'brain', name: 'BrainWorker', icon: Brain, color: '#00E5FF' },
    { id: 'vision', name: 'VisionWorker', icon: Eye, color: '#9B72CB' },
    { id: 'reason', name: 'ReasonWorker', icon: Shield, color: '#8AB4F8' },
    { id: 'fast', name: 'FastWorker', icon: Zap, color: '#00e676' },
  ];

  const getModelSize = (modelName: string): number => {
    for (const category of Object.values(modelCategories)) {
      const model = category.find(m => m.name === modelName);
      if (model) return parseFloat(model.size);
    }
    return 0;
  };

  useEffect(() => {
    // Calculate VRAM usage
    let used = 0;
    Object.values(currentModels).forEach(model => {
      used += getModelSize(model);
    });
    setVramInfo(prev => ({ ...prev, used: Math.round(used * 10) / 10 }));
  }, [currentModels]);

  return (
    <div className="bg-black/40 backdrop-blur-xl border border-white/10 rounded-2xl overflow-hidden">
      {/* Header */}
      <div className="border-b border-white/10 p-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Cpu className="w-5 h-5 text-[#00E5FF]" />
            <h2 className="text-sm font-bold text-white uppercase tracking-widest">
              MODEL TOGGLE
            </h2>
          </div>
          
          {/* VRAM Meter */}
          <div className="flex items-center gap-2">
            <span className="text-[8px] font-mono text-zinc-500">VRAM</span>
            <div className="w-16 h-2 bg-white/5 rounded-full overflow-hidden">
              <div 
                className="h-full bg-gradient-to-r from-[#00E5FF] to-[#9B72CB]"
                style={{ width: `${(vramInfo.used / vramInfo.total) * 100}%` }}
              />
            </div>
            <span className="text-[8px] font-mono text-white">
              {vramInfo.used}/{vramInfo.total}GB
            </span>
          </div>
        </div>
      </div>

      {/* Worker Tabs */}
      <div className="flex border-b border-white/10 bg-black/20">
        {workers.map(worker => {
          const Icon = worker.icon;
          return (
            <button
              key={worker.id}
              onClick={() => setSelectedWorker(worker.id)}
              className={`flex-1 py-3 text-[9px] font-mono font-bold uppercase tracking-widest transition-all relative`}
              style={{
                color: selectedWorker === worker.id ? worker.color : '#666',
                borderBottom: selectedWorker === worker.id ? `2px solid ${worker.color}` : 'none'
              }}
            >
              <Icon className="w-3 h-3 mx-auto mb-1" />
              {worker.name}
            </button>
          );
        })}
      </div>

      {/* Current Model Display */}
      <div className="p-4 bg-white/5 border-b border-white/10">
        <div className="text-[8px] text-zinc-500 mb-1">CURRENT MODEL</div>
        <div className="flex items-center justify-between">
          <div>
            <div className="text-sm font-mono text-white">
              {currentModels[selectedWorker as keyof typeof currentModels]}
            </div>
            <div className="text-[8px] text-zinc-500 mt-1">
              {modelCategories[selectedCategory]?.find(
                m => m.name === currentModels[selectedWorker as keyof typeof currentModels]
              )?.description || ''}
            </div>
          </div>
          <button
            onClick={() => setIsOpen(!isOpen)}
            className="px-3 py-1 bg-white/5 border border-white/10 rounded text-[9px] font-mono flex items-center gap-1 hover:bg-white/10 transition-colors"
          >
            Switch <ChevronDown className={`w-3 h-3 transition-transform ${isOpen ? 'rotate-180' : ''}`} />
          </button>
        </div>
      </div>

      {/* Category Tabs */}
      <AnimatePresence>
        {isOpen && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            className="overflow-hidden"
          >
            <div className="p-4 space-y-4 max-h-96 overflow-y-auto custom-scrollbar">
              {/* Category Selector */}
              <div className="flex flex-wrap gap-1">
                {Object.keys(modelCategories).map(category => (
                  <button
                    key={category}
                    onClick={() => setSelectedCategory(category)}
                    className={`px-2 py-1 rounded text-[8px] font-mono transition-colors ${
                      selectedCategory === category
                        ? 'bg-[#00E5FF]/20 border border-[#00E5FF]/30 text-[#00E5FF]'
                        : 'bg-white/5 border border-white/10 text-zinc-400 hover:text-white'
                    }`}
                  >
                    {category.split(' ')[1]}
                  </button>
                ))}
              </div>

              {/* Model List */}
              <div className="space-y-2">
                {modelCategories[selectedCategory].map((model, index) => {
                  const isSelected = currentModels[selectedWorker as keyof typeof currentModels] === model.name;
                  const isCompatible = parseFloat(model.size) <= vramInfo.total - (vramInfo.used - getModelSize(currentModels[selectedWorker as keyof typeof currentModels]));

                  return (
                    <motion.div
                      key={model.name}
                      initial={{ x: -10, opacity: 0 }}
                      animate={{ x: 0, opacity: 1 }}
                      transition={{ delay: index * 0.05 }}
                      className={`p-3 rounded-lg border transition-all cursor-pointer ${
                        isSelected
                          ? 'bg-[#00E5FF]/10 border-[#00E5FF]/30'
                          : isCompatible
                            ? 'bg-black/20 border-white/5 hover:border-white/20'
                            : 'bg-black/20 border-red-500/20 opacity-50 cursor-not-allowed'
                      }`}
                      onClick={() => {
                        if (isCompatible && onModelChange) {
                          onModelChange(selectedWorker, model.name);
                          setIsOpen(false);
                        }
                      }}
                    >
                      <div className="flex justify-between items-start mb-2">
                        <div>
                          <div className="flex items-center gap-2">
                            <span className="text-xs font-mono font-bold text-white">
                              {model.name}
                            </span>
                            {model.recommended && (
                              <span className="px-1 py-0.5 bg-[#00E5FF]/20 border border-[#00E5FF]/30 rounded text-[6px] font-mono text-[#00E5FF]">
                                BEST
                              </span>
                            )}
                          </div>
                          <div className="text-[8px] text-zinc-500 mt-1">
                            {model.size} • {model.strength}
                          </div>
                        </div>
                        {isSelected && <Check className="w-4 h-4 text-[#00E5FF]" />}
                      </div>

                      <div className="text-[8px] text-zinc-400 mb-2">
                        {model.description}
                      </div>

                      <div className="flex flex-wrap gap-1">
                        {model.bestFor.map((use, i) => (
                          <span
                            key={i}
                            className="px-1 py-0.5 bg-white/5 rounded text-[6px] font-mono text-zinc-300"
                          >
                            {use}
                          </span>
                        ))}
                      </div>

                      {model.vramWarning && (
                        <div className="mt-2 flex items-center gap-1 text-[6px] text-yellow-500">
                          <AlertTriangle className="w-2 h-2" />
                          {model.vramWarning}
                        </div>
                      )}

                      {!isCompatible && (
                        <div className="mt-2 flex items-center gap-1 text-[6px] text-red-500">
                          <AlertTriangle className="w-2 h-2" />
                          Not enough VRAM
                        </div>
                      )}
                    </motion.div>
                  );
                })}
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      <style jsx>{`
        .custom-scrollbar::-webkit-scrollbar {
          width: 4px;
        }
        .custom-scrollbar::-webkit-scrollbar-track {
          background: rgba(255, 255, 255, 0.05);
        }
        .custom-scrollbar::-webkit-scrollbar-thumb {
          background: rgba(255, 255, 255, 0.2);
          border-radius: 10px;
        }
      `}</style>
    </div>
  );
};