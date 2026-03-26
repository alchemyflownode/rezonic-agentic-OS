// API client for PHOENIX kernel
export const API_CONFIG = {
  baseUrl: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8002',
  wsUrl: process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8002',
  apiKey: process.env.NEXT_PUBLIC_API_KEY || 'rez-hive-admin-key-2026',
  appName: process.env.NEXT_PUBLIC_APP_NAME || 'PhoenixOS',
  appVersion: process.env.NEXT_PUBLIC_APP_VERSION || '13.3.0',
};

export const MODELS = {
  default: process.env.NEXT_PUBLIC_DEFAULT_MODEL || 'qwen2.5-coder:7b',
  fast: process.env.NEXT_PUBLIC_FAST_MODEL || 'llama3.2:latest',
  code: process.env.NEXT_PUBLIC_CODE_MODEL || 'qwen2.5-coder:7b',
  expert: process.env.NEXT_PUBLIC_EXPERT_MODEL || 'qwen2.5-coder:14b',
  vision: process.env.NEXT_PUBLIC_VISION_MODEL || 'llama3.2-vision:11b',
  available: (process.env.NEXT_PUBLIC_MODELS || 'qwen2.5-coder:7b,llama3.2:latest,qwen2.5-coder:14b,gemma2:9b').split(','),
};

export const FEATURES = {
  vision: process.env.NEXT_PUBLIC_ENABLE_VISION === 'true',
  codeGen: process.env.NEXT_PUBLIC_ENABLE_CODE_GEN === 'true',
  webSearch: process.env.NEXT_PUBLIC_ENABLE_WEB_SEARCH === 'true',
  pcControl: process.env.NEXT_PUBLIC_ENABLE_PC_CONTROL === 'true',
  rezCode: process.env.NEXT_PUBLIC_ENABLE_REZCODE === 'true',
};

export const GPU = {
  name: process.env.NEXT_PUBLIC_GPU_NAME || 'RTX 3060',
  vram: parseInt(process.env.NEXT_PUBLIC_GPU_VRAM || '12'),
  unit: process.env.NEXT_PUBLIC_GPU_VRAM_UNIT || 'GB',
};

export const CONSTITUTION = {
  enabled: process.env.NEXT_PUBLIC_CONSTITUTION_ENABLED === 'true',
  laws: (process.env.NEXT_PUBLIC_CONSTITUTION_LAWS || 'SOVEREIGNTY,TRANSPARENCY,ACCOUNTABILITY,SAFETY,CODE_SAFETY').split(','),
};