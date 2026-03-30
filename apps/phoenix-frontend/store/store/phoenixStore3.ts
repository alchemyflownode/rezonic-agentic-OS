// store/phoenixStore.ts
import React from 'react';
import { create } from 'zustand';
import { persist, createJSONStorage } from 'zustand/middleware';
import { immer } from 'zustand/middleware/immer';
import { io, Socket } from 'socket.io-client';

// ==========================================
// TYPES
// ==========================================

export interface Worker {
  name: string;
  status: 'active' | 'inactive' | 'error';
  drift_score: number;
  last_heartbeat: number;
  capabilities: string[];
}

export interface TelemetryData {
  workers: number;
  memory: number;
  gpu: {
    has_gpu: boolean;
    name?: string;
    total_gb?: number;
    used_gb?: number;
    free_gb?: number;
    utilization?: number;
    temperature?: number;
    error?: string;
  };
  chain_valid: boolean;
  kernel_load: number;
}

export interface MarketData {
  name: string;
  btcPrice: number;
  ethPrice: number;
  latency: number;
  status: string;
}

export interface KillSwitchStatus {
  active: boolean;
  triggered_at: number | null;
  triggered_by: string | null;
  reason: string | null;
}

export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant' | 'system' | 'error';
  content: string;
  timestamp: number;
  drift_lock?: string;
  isStreaming?: boolean;
  imageUrl?: string;
  videoUrl?: string;
}

export interface Portfolio {
  balance: number;
  positions: Record<string, number>;
  total_value: number;
  trades: Array<{
    action: 'BUY' | 'SELL';
    symbol: string;
    amount: number;
    price: number;
    timestamp?: number;
  }>;
}

export interface ChainStats {
  total_events: number;
  chain_valid: boolean;
  genesis: string;
  latest: string;
  counts: Record<string, number>;
}

export interface ComfyUIStatus {
  connected: boolean;
  workflows: string[];
  last_generation: {
    prompt: string;
    timestamp: number;
    image_url?: string;
  } | null;
}

export interface ResourceStats {
  cpu_percent: number;
  memory_percent: number;
  memory_used_gb: number;
  memory_total_gb: number;
  disk_percent: number;
  gpu_utilization?: number;
  gpu_memory_percent?: number;
  top_processes: Array<{
    pid: number;
    name: string;
    cpu_percent: number;
    memory_percent: number;
  }>;
  timestamp: number;
}

export interface ResourceAlert {
  type: 'CPU_HIGH' | 'MEMORY_HIGH' | 'DISK_HIGH' | 'GPU_HIGH';
  value: number;
  threshold: number;
  timestamp: number;
  top_process?: {
    pid: number;
    name: string;
    cpu_percent: number;
    memory_percent: number;
  };
}

export interface SSEMessage {
  type: 'token' | 'done' | 'error' | 'reflex' | 'integrity.update' | 'worker.status_update';
  content?: string;
  drift_lock?: string;
  payload?: any;
  timestamp?: string;
  source?: string;
}

export interface SymbioteStatus {
  initialized: boolean;
  providers: Record<string, {
    available: boolean;
    name: string;
    quality_score: number;
    models: string[];
    requires_auth: boolean;
    auth_configured: boolean;
    success_rate: number;
  }>;
  stats: {
    routes: number;
    by_provider: Record<string, number>;
    by_task: Record<string, number>;
    success: number;
    failures: number;
  };
  routing_strategies: string[];
}

// ==========================================
// STORE STATE
// ==========================================

interface PhoenixState {
  connected: boolean;
  apiKey: string | null;
  role: 'admin' | 'viewer' | 'anonymous' | null;
  socket: Socket | null;
  version: string;
  workers: Worker[];
  telemetry: TelemetryData;
  memory: {
    blueprints: string[];
    total: number;
    searchResults: any[];
  };
  portfolio: Portfolio;
  marketData: MarketData[];
  arbitrageOpportunities: any[];
  killSwitch: KillSwitchStatus;
  messages: ChatMessage[];
  isStreaming: boolean;
  currentResponse: string;
  driftEvents: any[];
  chainStats: ChainStats;
  comfyui: ComfyUIStatus;
  resourceStats: ResourceStats | null;
  resourceAlerts: ResourceAlert[];
  symbiote: SymbioteStatus | null;
  isLoading: boolean;
  error: string | null;
  lastUpdate: number;
}

// ==========================================
// STORE ACTIONS
// ==========================================

interface PhoenixActions {
  connect: (apiKey?: string) => Promise<void>;
  disconnect: () => void;
  setApiKey: (key: string) => void;
  fetchHealth: () => Promise<void>;
  fetchWorkers: () => Promise<void>;
  fetchTelemetry: () => Promise<void>;
  fetchMemory: () => Promise<void>;
  searchMemory: (query: string) => Promise<any[]>;
  fetchChainStats: () => Promise<void>;
  fetchDriftEvents: (limit?: number) => Promise<void>;
  fetchPortfolio: () => Promise<void>;
  executeTrade: (action: 'buy' | 'sell', symbol: string, amount: number, price?: number) => Promise<boolean>;
  runBacktest: (strategy: string) => Promise<any>;
  fetchKillSwitchStatus: () => Promise<void>;
  activateKillSwitch: (reason?: string) => Promise<boolean>;
  resetKillSwitch: () => Promise<boolean>;
  sendMessage: (message: string, model?: string) => Promise<void>;
  sendReflexCommand: (command: string) => Promise<any>;
  clearMessages: () => void;
  checkComfyUI: () => Promise<void>;
  generateImage: (prompt: string, options?: { width?: number; height?: number }) => Promise<boolean>;
  generateVideo: (prompt: string) => Promise<boolean>;
  executeCommand: (command: string) => Promise<any>;
  
  // Resource monitoring
  fetchResourceStats: () => Promise<void>;
  startResourceMonitoring: (interval?: number) => Promise<void>;
  stopResourceMonitoring: () => Promise<void>;
  
  // Symbiote orchestration
  fetchSymbioteStatus: () => Promise<void>;
  getSymbioteRecommendation: (task: string) => Promise<any>;
  
  // UI actions
  setError: (error: string | null) => void;
  clearError: () => void;
  resetState: () => void;
}

// ==========================================
// API CLIENT
// ==========================================

class PhoenixAPI {
  private baseUrl: string;
  private apiKey: string | null = null;
  private retryCount = 0;
  private maxRetries = 3;

  constructor(baseUrl: string = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8002') {
    this.baseUrl = baseUrl;
  }

  setApiKey(key: string | null) {
    this.apiKey = key;
  }

  private async request<T>(endpoint: string, options: RequestInit = {}, retry = true): Promise<T> {
    const headers: HeadersInit = { 'Content-Type': 'application/json', ...options.headers };
    if (this.apiKey) headers['Authorization'] = `Bearer ${this.apiKey}`;

    try {
      const response = await fetch(`${this.baseUrl}${endpoint}`, { ...options, headers });
      
      if (!response.ok) {
        const error = await response.text();
        throw new Error(error || `HTTP ${response.status}`);
      }
      
      // Reset retry count on success
      this.retryCount = 0;
      return response.json();
      
    } catch (error: any) {
      // Retry logic for network errors
      if (retry && this.retryCount < this.maxRetries && error.message?.includes('Failed to fetch')) {
        this.retryCount++;
        await new Promise(resolve => setTimeout(resolve, 1000 * this.retryCount));
        return this.request<T>(endpoint, options, false);
      }
      throw error;
    }
  }

  // Health & Status
  async health() { return this.request<any>('/health'); }
  async workers() { return this.request<{ workers: string[]; count: number }>('/workers/list'); }
  async workersStatus() { return this.request<{ workers: Worker[]; total: number }>('/workers/status'); }
  async ollamaStatus() { return this.request<{ connected: boolean; model: string; models: string[] }>('/ollama/status'); }
  
  // Memory & Events
  async memoryBlueprints() { return this.request<{ blueprints: string[]; total: number }>('/memory/blueprints'); }
  async memorySearch(query: string, limit: number = 10) {
    return this.request<{ results: any[] }>(`/memory/search?q=${encodeURIComponent(query)}&limit=${limit}`);
  }
  async chainStats() { return this.request<ChainStats>('/events/stats'); }
  async driftEvents(limit: number = 50) { 
    return this.request<{ events: any[]; count: number; timestamp: number; chain_valid: boolean }>(`/drift/events?limit=${limit}`); 
  }
  
  // Kill Switch
  async killStatus() { return this.request<KillSwitchStatus>('/kill/status'); }
  async activateKillSwitch() { return this.request<{ status: string; triggered_at: number }>('/kill', { method: 'POST' }); }
  async resetKillSwitch() { return this.request<{ status: string }>('/kill/reset', { method: 'POST' }); }
  
  // Constitution
  async constitutionHistory() { return this.request<{ rulings: any[]; total: number }>('/constitution/history'); }
  
  // Resource Monitoring
  async resourceStats() { return this.request<ResourceStats>('/resource/stats'); }
  async resourceAlerts(limit: number = 20) { return this.request<{ alerts: ResourceAlert[] }>(`/resource/alerts?limit=${limit}`); }
  
  // Symbiote
  async symbioteStatus() { return this.request<SymbioteStatus>('/symbiote/status'); }
  async symbioteRecommend(task: string) { 
    return this.request<any>('/symbiote/recommend', { 
      method: 'POST', 
      body: JSON.stringify({ task }) 
    }); 
  }
  
  // Streaming Chat
  async chat(task: string, model?: string): Promise<ReadableStream<Uint8Array>> {
    const response = await fetch(`${this.baseUrl}/kernel/stream`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...(this.apiKey && { 'Authorization': `Bearer ${this.apiKey}` }),
      },
      body: JSON.stringify({ task, model }),
    });
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    if (!response.body) throw new Error('No response body');
    return response.body;
  }
  
  // File Upload
  async upload(file: File): Promise<{ filename: string; size: number; status: string }> {
    const formData = new FormData();
    formData.append('file', file);
    
    const response = await fetch(`${this.baseUrl}/kernel/upload`, {
      method: 'POST',
      headers: this.apiKey ? { 'Authorization': `Bearer ${this.apiKey}` } : {},
      body: formData,
    });
    
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    return response.json();
  }
}

// ==========================================
// WEBSOCKET MANAGER
// ==========================================

class PhoenixWebSocket {
  private socket: Socket | null = null;
  private listeners: Map<string, Set<Function>> = new Map();
  private baseUrl: string;
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;
  private reconnectDelay = 1000;

  constructor(baseUrl: string = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8002') {
    this.baseUrl = baseUrl;
  }

  connect(apiKey?: string) {
    if (this.socket?.connected) return;
    
    const wsUrl = this.baseUrl.replace(/^http/, 'ws');
    
    this.socket = io(wsUrl, {
      transports: ['websocket', 'polling'],
      auth: apiKey ? { token: apiKey } : undefined,
      reconnection: true,
      reconnectionAttempts: this.maxReconnectAttempts,
      reconnectionDelay: this.reconnectDelay,
      reconnectionDelayMax: 5000,
      timeout: 10000,
    });

    this.socket.on('connect', () => {
      console.log('🟢 WebSocket connected');
      this.reconnectAttempts = 0;
      this.reconnectDelay = 1000; // Reset on success
      this.emit('connect', null);
    });

    this.socket.on('disconnect', (reason) => {
      console.log('🔴 WebSocket disconnected:', reason);
      this.emit('disconnect', { reason });
    });

    this.socket.on('connect_error', (error) => {
      console.error('WebSocket connection error:', error);
      this.reconnectAttempts++;
      // Exponential backoff
      this.reconnectDelay = Math.min(this.reconnectDelay * 2, 5000);
      
      if (this.reconnectAttempts >= this.maxReconnectAttempts) {
        this.emit('connect_failed', { attempts: this.reconnectAttempts, error });
      }
    });

    // Backend events
    this.socket.on('marketUpdate', (data: MarketData[]) => {
      console.log('📊 Market update:', data);
      this.emit('marketUpdate', data);
    });
    
    this.socket.on('arbitrageUpdate', (data: any[]) => {
      console.log('💰 Arbitrage update:', data);
      this.emit('arbitrageUpdate', data);
    });
    
    this.socket.on('agentLog', (data: any) => {
      console.log('📝 Agent log:', data);
      this.emit('agentLog', data);
    });
    
    this.socket.on('trade_result', (data: any) => {
      console.log('💼 Trade result:', data);
      this.emit('trade_result', data);
    });
    
    this.socket.on('kill_switch', (data: any) => {
      console.log('🔴 Kill switch event:', data);
      this.emit('kill_switch', data);
    });
    
    this.socket.on('generation_complete', (data: any) => {
      console.log('🎨 Generation complete:', data);
      this.emit('generation_complete', data);
    });
    
    this.socket.on('resource_alert', (data: ResourceAlert) => {
      console.log('🚨 Resource alert:', data);
      this.emit('resource_alert', data);
    });
  }

  disconnect() {
    if (this.socket) {
      this.socket.disconnect();
      this.socket = null;
    }
    this.listeners.clear();
  }

  on(event: string, callback: Function) {
    if (!this.listeners.has(event)) this.listeners.set(event, new Set());
    this.listeners.get(event)!.add(callback);
  }

  off(event: string, callback: Function) {
    this.listeners.get(event)?.delete(callback);
  }

  emit(event: string, data: any) {
    this.listeners.get(event)?.forEach(cb => cb(data));
  }

  get connected(): boolean {
    return this.socket?.connected || false;
  }
}

// ==========================================
// SSE PARSER (Improved)
// ==========================================

const parseSSEResponse = async (
  stream: ReadableStream<Uint8Array>,
  onToken: (token: string) => void,
  onDone: (driftLock?: string) => void,
  onError: (error: string) => void
) => {
  const reader = stream.getReader();
  const decoder = new TextDecoder('utf-8');
  let buffer = '';
  
  try {
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      
      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split('\n');
      buffer = lines.pop() || '';
      
      for (const line of lines) {
        if (!line.trim()) continue;
        
        if (line.startsWith('data: ')) {
          try {
            const data = JSON.parse(line.slice(6).trim());
            
            switch (data.type) {
              case 'token':
                if (data.content) onToken(data.content);
                break;
              case 'done':
                onDone(data.drift_lock);
                break;
              case 'error':
                onError(data.content || 'Unknown error');
                break;
              case 'reflex':
                if (data.content) onToken(data.content);
                break;
              case 'integrity.update':
              case 'worker.status_update':
                // Pass through system events as tokens for display
                if (data.payload) onToken(JSON.stringify(data.payload, null, 2));
                break;
              default:
                // Fallback: treat content as token
                if (data.content) onToken(data.content);
            }
          } catch (e) {
            // Not JSON, treat as plain text token
            const text = line.slice(6).trim();
            if (text) onToken(text);
          }
        }
      }
    }
  } catch (error: any) {
    onError(error?.message || 'Stream parsing error');
  } finally {
    reader.releaseLock();
  }
};

// ==========================================
// HELPER: Extract JSON from text (Improved)
// ==========================================

const extractJSON = (text: string): any | null => {
  if (!text) return null;
  
  // Pattern 1: Direct JSON object (most reliable)
  let match = text.match(/\{[\s\S]*\}/);
  if (match) {
    try {
      return JSON.parse(match[0]);
    } catch (e) {}
  }
  
  // Pattern 2: After common prefixes
  const prefixes = ['Portfolio:', '📊 Portfolio:', 'Result:', 'Response:'];
  for (const prefix of prefixes) {
    const idx = text.indexOf(prefix);
    if (idx !== -1) {
      const after = text.slice(idx + prefix.length).trim();
      match = after.match(/^\{[\s\S]*\}/);
      if (match) {
        try {
          return JSON.parse(match[0]);
        } catch (e) {}
      }
    }
  }
  
  // Pattern 3: Try to find any valid JSON substring
  const jsonRegex = /(\{[\s\S]*?"success"[\s\S]*?\})/;
  match = text.match(jsonRegex);
  if (match) {
    try {
      return JSON.parse(match[1]);
    } catch (e) {}
  }
  
  return null;
};

// ==========================================
// ZUSTAND STORE
// ==========================================

export const usePhoenixStore = create<PhoenixState & PhoenixActions>()(
  persist(
    immer((set, get) => {
      const api = new PhoenixAPI();
      const ws = new PhoenixWebSocket();

      return {
        // Initial state
        connected: false,
        apiKey: null,
        role: null,
        socket: null,
        version: '15.3.1',
        workers: [],
        telemetry: {
          workers: 0,
          memory: 0,
          gpu: { has_gpu: false },
          chain_valid: false,
          kernel_load: 0,
        },
        memory: {
          blueprints: [],
          total: 0,
          searchResults: [],
        },
        portfolio: {
          balance: 1000000,
          positions: {},
          total_value: 1000000,
          trades: [],
        },
        marketData: [],
        arbitrageOpportunities: [],
        killSwitch: {
          active: false,
          triggered_at: null,
          triggered_by: null,
          reason: null,
        },
        messages: [],
        isStreaming: false,
        currentResponse: '',
        driftEvents: [],
        chainStats: {
          total_events: 0,
          chain_valid: false,
          genesis: '',
          latest: '',
          counts: {},
        },
        comfyui: {
          connected: false,
          workflows: [],
          last_generation: null,
        },
        resourceStats: null,
        resourceAlerts: [],
        symbiote: null,
        isLoading: false,
        error: null,
        lastUpdate: 0,

        // Connection actions
        setApiKey: (key: string) => {
          set(state => {
            state.apiKey = key;
            api.setApiKey(key);
          });
        },

        connect: async (apiKey?: string) => {
          const defaultKey = process.env.NEXT_PUBLIC_PHOENIX_API_KEY || "rez-hive-admin-key-2026";
          const keyToUse = apiKey || defaultKey;
          
          set(state => {
            state.apiKey = keyToUse;
            api.setApiKey(keyToUse);
          });
          
          set({ isLoading: true, error: null });
          
          try {
            // Test connection with retry
            const health = await api.health();
            
            set(state => {
              state.connected = true;
              state.version = health.version || '15.3.1';
              state.telemetry.workers = health.workers || 0;
              state.telemetry.memory = health.memory_entries || 0;
              state.telemetry.gpu = health.gpu || { has_gpu: false };
              state.role = 'admin';
              state.lastUpdate = Date.now();
            });
            
            // Connect WebSocket
            ws.connect(keyToUse);
            
            // Set up WebSocket listeners
            ws.on('marketUpdate', (data: MarketData[]) => {
              set(state => { 
                state.marketData = data; 
                state.lastUpdate = Date.now();
              });
            });
            
            ws.on('arbitrageUpdate', (data: any[]) => {
              set(state => { 
                state.arbitrageOpportunities = data; 
                state.lastUpdate = Date.now();
              });
            });
            
            ws.on('agentLog', (data: any) => {
              set(state => {
                state.messages.push({
                  id: `system-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
                  role: 'system',
                  content: data.message || JSON.stringify(data),
                  timestamp: Date.now(),
                });
                if (state.messages.length > 200) {
                  state.messages = state.messages.slice(-200);
                }
              });
            });
            
            ws.on('trade_result', (data: any) => {
              set(state => {
                state.messages.push({
                  id: `trade-${Date.now()}`,
                  role: 'system',
                  content: `Trade Result: ${JSON.stringify(data, null, 2)}`,
                  timestamp: Date.now(),
                });
              });
              get().fetchPortfolio();
            });
            
            ws.on('kill_switch', (data: any) => {
              set(state => {
                state.killSwitch = {
                  active: data.active,
                  triggered_at: data.triggered_at,
                  triggered_by: data.triggered_by,
                  reason: data.reason || null,
                };
                state.messages.push({
                  id: `kill-${Date.now()}`,
                  role: 'system',
                  content: `🔴 KILL SWITCH ACTIVATED by ${data.triggered_by || 'unknown'}`,
                  timestamp: Date.now(),
                });
              });
            });
            
            ws.on('generation_complete', (data: any) => {
              set(state => {
                state.comfyui.last_generation = {
                  prompt: data.prompt,
                  timestamp: Date.now(),
                  image_url: data.image_url,
                };
              });
            });
            
            ws.on('resource_alert', (alert: ResourceAlert) => {
              set(state => {
                state.resourceAlerts.push(alert);
                if (state.resourceAlerts.length > 50) {
                  state.resourceAlerts = state.resourceAlerts.slice(-50);
                }
                // Show alert as system message
                state.messages.push({
                  id: `alert-${Date.now()}`,
                  role: 'system',
                  content: `🚨 ${alert.type}: ${alert.value}% (threshold: ${alert.threshold}%)`,
                  timestamp: Date.now(),
                });
              });
            });
            
            // Initial data fetch (parallel, non-blocking)
            await Promise.allSettled([
              get().fetchWorkers(),
              get().fetchTelemetry(),
              get().fetchMemory(),
              get().fetchChainStats(),
              get().fetchKillSwitchStatus(),
              get().fetchPortfolio(),
              get().checkComfyUI(),
              get().fetchSymbioteStatus(),
            ]);
            
            console.log('✅ Phoenix connected successfully');
            
          } catch (error: any) {
            console.error('❌ Connection error:', error);
            set({ 
              error: `Connection failed: ${error.message}`, 
              connected: false,
              isLoading: false 
            });
          }
        },

        disconnect: () => {
          ws.disconnect();
          set({ 
            connected: false, 
            apiKey: null, 
            role: null,
            marketData: [],
            arbitrageOpportunities: [],
            error: null,
          });
          console.log('🔌 Phoenix disconnected');
        },

        // System actions
        fetchHealth: async () => {
          try {
            const health = await api.health();
            set(state => {
              state.version = health.version || state.version;
              state.telemetry.workers = health.workers || state.telemetry.workers;
              state.telemetry.memory = health.memory_entries || state.telemetry.memory;
              state.telemetry.gpu = health.gpu || state.telemetry.gpu;
              state.lastUpdate = Date.now();
            });
          } catch (error: any) {
            console.error('Health fetch failed:', error);
            set({ error: error.message });
          }
        },

        fetchWorkers: async () => {
          try {
            const status = await api.workersStatus();
            set(state => {
              state.workers = status.workers || [];
              state.telemetry.workers = status.total || 0;
            });
          } catch (error: any) {
            console.error('Workers fetch failed:', error);
          }
        },

        fetchTelemetry: async () => {
          try {
            const [health, stats] = await Promise.all([
              api.health(),
              api.chainStats()
            ]);
            set(state => {
              state.telemetry = {
                workers: health.workers || state.telemetry.workers,
                memory: health.memory_entries || state.telemetry.memory,
                gpu: health.gpu || state.telemetry.gpu,
                chain_valid: stats.chain_valid,
                kernel_load: Math.floor(Math.random() * 40) + 30,
              };
              state.lastUpdate = Date.now();
            });
          } catch (error: any) {
            console.error('Telemetry fetch failed:', error);
          }
        },

        fetchMemory: async () => {
          try {
            const blueprints = await api.memoryBlueprints();
            set(state => {
              state.memory.blueprints = blueprints.blueprints || [];
              state.memory.total = blueprints.total || blueprints.blueprints?.length || 0;
            });
          } catch (error: any) {
            console.error('Memory fetch failed:', error);
          }
        },

        searchMemory: async (query: string) => {
          if (!query.trim()) return [];
          try {
            const results = await api.memorySearch(query);
            set(state => {
              state.memory.searchResults = results.results || [];
            });
            return results.results || [];
          } catch (error: any) {
            set({ error: error.message });
            return [];
          }
        },

        fetchChainStats: async () => {
          try {
            const stats = await api.chainStats();
            set(state => {
              state.chainStats = stats;
              state.telemetry.chain_valid = stats.chain_valid;
            });
          } catch (error: any) {
            console.error('Chain stats fetch failed:', error);
          }
        },

        fetchDriftEvents: async (limit: number = 50) => {
          try {
            const events = await api.driftEvents(limit);
            set(state => {
              state.driftEvents = events.events || [];
            });
          } catch (error: any) {
            console.error('Drift events fetch failed:', error);
          }
        },

        // Trading actions
        fetchPortfolio: async () => {
          try {
            const response = await fetch(`${api['baseUrl']}/kernel/stream`, {
              method: 'POST',
              headers: {
                'Content-Type': 'application/json',
                ...(api['apiKey'] && { 'Authorization': `Bearer ${api['apiKey']}` }),
              },
              body: JSON.stringify({ task: '/portfolio' }),
            });
            
            if (!response.ok) throw new Error(`Failed to fetch portfolio: ${response.status}`);
            
            const stream = response.body;
            if (!stream) return;
            
            let fullResponse = '';
            
            await parseSSEResponse(
              stream,
              (token) => { fullResponse += token; },
              () => {
                const portfolioData = extractJSON(fullResponse);
                if (portfolioData && portfolioData.success !== false) {
                  set(state => {
                    state.portfolio = {
                      balance: portfolioData.balance ?? state.portfolio.balance,
                      positions: portfolioData.positions ?? {},
                      total_value: portfolioData.total_value ?? portfolioData.balance ?? state.portfolio.total_value,
                      trades: portfolioData.trades ?? state.portfolio.trades,
                    };
                  });
                }
              },
              (error) => { console.error('Portfolio fetch error:', error); }
            );
          } catch (error: any) {
            console.error('Portfolio fetch failed:', error);
          }
        },

        executeTrade: async (action: 'buy' | 'sell', symbol: string, amount: number, price?: number) => {
          try {
            const task = `/trade ${action} ${symbol} ${amount}`;
            const stream = await api.chat(task);
            let success = false;
            let errorMsg = '';
            
            await parseSSEResponse(
              stream,
              (token) => { 
                if (token.includes('success') && token.includes('true')) success = true;
                if (token.includes('error')) errorMsg = token;
              },
              async () => {
                if (success) {
                  await get().fetchPortfolio();
                  set(state => {
                    state.messages.push({
                      id: `trade-${Date.now()}`,
                      role: 'system',
                      content: `✅ Trade executed: ${action.toUpperCase()} ${amount} ${symbol}`,
                      timestamp: Date.now(),
                    });
                  });
                } else {
                  set(state => {
                    state.messages.push({
                      id: `trade-fail-${Date.now()}`,
                      role: 'error',
                      content: `❌ Trade failed: ${errorMsg || 'Unknown error'}`,
                      timestamp: Date.now(),
                    });
                  });
                }
              },
              (error) => {
                set(state => {
                  state.messages.push({
                    id: `trade-error-${Date.now()}`,
                    role: 'error',
                    content: `❌ Trade failed: ${error}`,
                    timestamp: Date.now(),
                  });
                });
              }
            );
            return success;
          } catch (error: any) {
            set({ error: error.message });
            return false;
          }
        },

        runBacktest: async (strategy: string) => {
          try {
            const stream = await api.chat(`/backtest ${strategy}`);
            let result: any = null;
            let fullResponse = '';
            
            await parseSSEResponse(
              stream,
              (token) => { fullResponse += token; },
              () => {
                const jsonMatch = fullResponse.match(/\{[\s\S]*\}/);
                if (jsonMatch) {
                  try {
                    result = JSON.parse(jsonMatch[0]);
                  } catch (e) {
                    console.error('Failed to parse backtest result:', e);
                  }
                }
              },
              (error) => { console.error('Backtest error:', error); }
            );
            return result;
          } catch (error: any) {
            set({ error: error.message });
            return null;
          }
        },

        // Kill switch actions
        fetchKillSwitchStatus: async () => {
          try {
            const status = await api.killStatus();
            set(state => {
              state.killSwitch = status;
            });
          } catch (error: any) {
            console.error('Kill switch status fetch failed:', error);
          }
        },

        activateKillSwitch: async (reason: string = 'Manual trigger') => {
          try {
            const result = await api.activateKillSwitch();
            set(state => {
              state.killSwitch.active = true;
              state.killSwitch.triggered_at = result.triggered_at;
              state.killSwitch.triggered_by = 'api';
              state.killSwitch.reason = reason;
              state.messages.push({
                id: `kill-activate-${Date.now()}`,
                role: 'system',
                content: `🔴 KILL SWITCH ACTIVATED: ${reason}`,
                timestamp: Date.now(),
              });
            });
            return true;
          } catch (error: any) {
            set({ error: error.message });
            return false;
          }
        },

        resetKillSwitch: async () => {
          try {
            await api.resetKillSwitch();
            set(state => {
              state.killSwitch.active = false;
              state.killSwitch.triggered_at = null;
              state.killSwitch.triggered_by = null;
              state.killSwitch.reason = null;
              state.messages.push({
                id: `kill-reset-${Date.now()}`,
                role: 'system',
                content: `🔓 Kill switch RESET`,
                timestamp: Date.now(),
              });
            });
            return true;
          } catch (error: any) {
            set({ error: error.message });
            return false;
          }
        },

        // Chat actions
        sendMessage: async (message: string, model?: string) => {
          if (!message.trim() || get().isStreaming) return;
          
          const userMessage: ChatMessage = {
            id: `user-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
            role: 'user',
            content: message,
            timestamp: Date.now(),
          };
          
          set(state => {
            state.messages.push(userMessage);
            state.isStreaming = true;
            state.currentResponse = '';
          });
          
          const assistantId = `assistant-${Date.now()}`;
          set(state => {
            state.messages.push({
              id: assistantId,
              role: 'assistant',
              content: '',
              timestamp: Date.now(),
              isStreaming: true,
            });
          });
          
          try {
            const stream = await api.chat(message, model);
            let fullContent = '';
            
            await parseSSEResponse(
              stream,
              (token) => {
                fullContent += token;
                set(state => {
                  const msg = state.messages.find(m => m.id === assistantId);
                  if (msg) msg.content = fullContent;
                  state.currentResponse = fullContent;
                });
              },
              (lock) => {
                set(state => {
                  const msg = state.messages.find(m => m.id === assistantId);
                  if (msg) {
                    msg.isStreaming = false;
                    msg.drift_lock = lock;
                  }
                  state.isStreaming = false;
                  state.currentResponse = '';
                });
              },
              (error) => {
                set(state => {
                  const msg = state.messages.find(m => m.id === assistantId);
                  if (msg) {
                    msg.content = `❌ Error: ${error}`;
                    msg.isStreaming = false;
                  }
                  state.isStreaming = false;
                  state.currentResponse = '';
                  state.error = error;
                });
              }
            );
          } catch (error: any) {
            set(state => {
              const msg = state.messages.find(m => m.id === assistantId);
              if (msg) {
                msg.content = `❌ Connection error: ${error.message}`;
                msg.isStreaming = false;
              }
              state.isStreaming = false;
              state.currentResponse = '';
              state.error = error.message;
            });
          }
        },

        // Reflex command handler
        sendReflexCommand: async (command: string) => {
          if (!command.startsWith('/')) {
            command = '/' + command;
          }
          
          const messageId = `reflex-${Date.now()}`;
          set(state => {
            state.messages.push({
              id: messageId,
              role: 'system',
              content: `Executing: ${command}`,
              timestamp: Date.now(),
            });
          });
          
          try {
            const stream = await api.chat(command);
            let fullResponse = '';
            
            await parseSSEResponse(
              stream,
              (token) => { fullResponse += token; },
              () => {
                set(state => {
                  const msg = state.messages.find(m => m.id === messageId);
                  if (msg) {
                    msg.content = fullResponse;
                    msg.role = 'assistant';
                  }
                });
              },
              (error) => {
                set(state => {
                  const msg = state.messages.find(m => m.id === messageId);
                  if (msg) {
                    msg.content = `❌ Command failed: ${error}`;
                    msg.role = 'error';
                  }
                });
              }
            );
            
            return fullResponse;
          } catch (error: any) {
            set(state => {
              const msg = state.messages.find(m => m.id === messageId);
              if (msg) {
                msg.content = `❌ Command error: ${error.message}`;
                msg.role = 'error';
              }
            });
            return null;
          }
        },

        clearMessages: () => {
          set({ messages: [], currentResponse: '' });
        },

        // Resource monitoring actions
        fetchResourceStats: async () => {
          try {
            const stats = await api.resourceStats();
            set(state => {
              state.resourceStats = stats;
            });
          } catch (error: any) {
            // Resource endpoint may not be enabled yet
            console.debug('Resource stats not available:', error.message);
          }
        },

        startResourceMonitoring: async (interval: number = 1) => {
          await get().sendReflexCommand(`/resource_monitor start interval=${interval}`);
        },

        stopResourceMonitoring: async () => {
          await get().sendReflexCommand('/resource_monitor stop');
        },

        // Symbiote orchestration actions
        fetchSymbioteStatus: async () => {
          try {
            const status = await api.symbioteStatus();
            set(state => {
              state.symbiote = status;
            });
          } catch (error: any) {
            console.debug('Symbiote not enabled yet:', error.message);
          }
        },

        getSymbioteRecommendation: async (task: string) => {
          try {
            return await api.symbioteRecommend(task);
          } catch (error: any) {
            console.error('Symbiote recommendation failed:', error);
            return null;
          }
        },

        // ComfyUI actions
        checkComfyUI: async () => {
          try {
            const controller = new AbortController();
            const timeoutId = setTimeout(() => controller.abort(), 3000);
            const response = await fetch('http://127.0.0.1:8188/system_stats', { signal: controller.signal });
            clearTimeout(timeoutId);
            set(state => {
              state.comfyui.connected = response.ok;
            });
          } catch {
            set(state => {
              state.comfyui.connected = false;
            });
          }
        },

        generateImage: async (prompt: string, options?: { width?: number; height?: number }) => {
          const width = options?.width || 1024;
          const height = options?.height || 1024;
          
          set(state => {
            state.messages.push({
              id: `gen-${Date.now()}`,
              role: 'user',
              content: `🎨 Generating image: ${prompt}`,
              timestamp: Date.now(),
            });
          });
          
          try {
            const stream = await api.chat(`/generate ${prompt} --width ${width} --height ${height}`);
            let fullResponse = '';
            
            await parseSSEResponse(
              stream,
              (token) => { fullResponse += token; },
              () => {
                set(state => {
                  state.messages.push({
                    id: `gen-result-${Date.now()}`,
                    role: 'assistant',
                    content: fullResponse,
                    timestamp: Date.now(),
                  });
                });
              },
              (error) => {
                set(state => {
                  state.messages.push({
                    id: `gen-error-${Date.now()}`,
                    role: 'error',
                    content: `Failed to generate image: ${error}`,
                    timestamp: Date.now(),
                  });
                });
              }
            );
            return true;
          } catch (error: any) {
            set({ error: error.message });
            return false;
          }
        },

        generateVideo: async (prompt: string) => {
          set(state => {
            state.messages.push({
              id: `vid-${Date.now()}`,
              role: 'user',
              content: `🎬 Generating video: ${prompt}`,
              timestamp: Date.now(),
            });
          });
          
          try {
            const stream = await api.chat(`/video ${prompt}`);
            let fullResponse = '';
            
            await parseSSEResponse(
              stream,
              (token) => { fullResponse += token; },
              () => {
                set(state => {
                  state.messages.push({
                    id: `vid-result-${Date.now()}`,
                    role: 'assistant',
                    content: fullResponse,
                    timestamp: Date.now(),
                  });
                });
              },
              (error) => {
                set(state => {
                  state.messages.push({
                    id: `vid-error-${Date.now()}`,
                    role: 'error',
                    content: `Failed to generate video: ${error}`,
                    timestamp: Date.now(),
                  });
                });
              }
            );
            return true;
          } catch (error: any) {
            set({ error: error.message });
            return false;
          }
        },

        executeCommand: async (command: string) => {
          if (command.startsWith('/')) {
            return get().sendReflexCommand(command);
          } else {
            return get().sendMessage(command);
          }
        },

        // UI actions
        setError: (error: string | null) => {
          set({ error });
        },

        clearError: () => {
          set({ error: null });
        },

        resetState: () => {
          set({
            connected: false,
            apiKey: null,
            role: null,
            messages: [],
            isStreaming: false,
            currentResponse: '',
            error: null,
            marketData: [],
            arbitrageOpportunities: [],
            killSwitch: {
              active: false,
              triggered_at: null,
              triggered_by: null,
              reason: null,
            },
            resourceStats: null,
            resourceAlerts: [],
            symbiote: null,
          });
        },
      };
    }),
    {
      name: 'phoenix-storage',
      storage: createJSONStorage(() => localStorage),
      partialize: (state) => ({
        apiKey: state.apiKey,
        messages: state.messages.slice(-50),
        portfolio: state.portfolio,
        killSwitch: state.killSwitch,
        resourceAlerts: state.resourceAlerts.slice(-20),
      }),
    }
  )
);

// ==========================================
// CUSTOM HOOKS
// ==========================================

export const useAutoRefresh = (interval: number = 5000) => {
  const { 
    fetchWorkers, 
    fetchTelemetry, 
    fetchChainStats, 
    fetchKillSwitchStatus, 
    fetchPortfolio,
    fetchResourceStats,
    connected 
  } = usePhoenixStore();
  
  React.useEffect(() => {
    if (!connected) return;
    
    const timer = setInterval(() => {
      fetchWorkers();
      fetchTelemetry();
      fetchChainStats();
      fetchKillSwitchStatus();
      fetchPortfolio();
      fetchResourceStats();
    }, interval);
    
    return () => clearInterval(timer);
  }, [connected, interval, fetchWorkers, fetchTelemetry, fetchChainStats, fetchKillSwitchStatus, fetchPortfolio, fetchResourceStats]);
};

export const useWebSocket = () => {
  const { connected } = usePhoenixStore();
  
  React.useEffect(() => {
    if (!connected) return;
    return () => {
      // Cleanup handled by store disconnect
    };
  }, [connected]);
};

// Helper hook for resource monitoring UI
export const useResourceMonitor = (enabled: boolean = true, interval: number = 5000) => {
  const { connected, fetchResourceStats, resourceStats } = usePhoenixStore();
  
  React.useEffect(() => {
    if (!connected || !enabled) return;
    
    fetchResourceStats();
    const timer = setInterval(fetchResourceStats, interval);
    return () => clearInterval(timer);
  }, [connected, enabled, interval, fetchResourceStats]);
  
  return resourceStats;
};