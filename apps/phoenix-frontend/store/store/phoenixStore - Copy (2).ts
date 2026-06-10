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
    timestamp: number;
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
  clearMessages: () => void;
  checkComfyUI: () => Promise<void>;
  generateImage: (prompt: string, options?: { width?: number; height?: number }) => Promise<boolean>;
  generateVideo: (prompt: string) => Promise<boolean>;
  executeCommand: (command: string) => Promise<any>;
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

  constructor(baseUrl: string = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8002') {
    this.baseUrl = baseUrl;
  }

  setApiKey(key: string | null) {
    this.apiKey = key;
  }

  private async request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
    const headers: HeadersInit = { 'Content-Type': 'application/json', ...options.headers };
    if (this.apiKey) headers['Authorization'] = `Bearer ${this.apiKey}`;

    const response = await fetch(`${this.baseUrl}${endpoint}`, { ...options, headers });
    if (!response.ok) {
      const error = await response.text();
      throw new Error(error || `HTTP ${response.status}`);
    }
    return response.json();
  }

  async health() { return this.request<any>('/health'); }
  async workers() { return this.request<{ workers: string[]; count: number }>('/workers/list'); }
  async workersStatus() { return this.request<{ workers: Worker[]; total: number }>('/workers/status'); }
  async memoryBlueprints() { return this.request<{ blueprints: string[] }>('/memory/blueprints'); }
  async memorySearch(query: string, limit: number = 10) {
    return this.request<{ results: any[] }>(`/memory/search?q=${encodeURIComponent(query)}&limit=${limit}`);
  }
  async chainStats() { return this.request<ChainStats>('/events/stats'); }
  async driftEvents(limit: number = 50) { return this.request<{ events: any[]; count: number }>(`/drift/events?limit=${limit}`); }
  async killStatus() { return this.request<KillSwitchStatus>('/kill/status'); }
  async activateKillSwitch() { return this.request<{ status: string; triggered_at: number }>('/kill', { method: 'POST' }); }
  async resetKillSwitch() { return this.request<{ status: string }>('/kill/reset', { method: 'POST' }); }
  
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
    return response.body!;
  }
  
  async generateImage(prompt: string, width: number = 1024, height: number = 1024) {
    return this.chat(`/generate ${prompt} --width ${width} --height ${height}`);
  }
  
  async generateVideo(prompt: string) {
    return this.chat(`/video ${prompt}`);
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

  constructor(baseUrl: string = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8002') {
    this.baseUrl = baseUrl;
  }

  connect(apiKey?: string) {
    if (this.socket?.connected) return;
    
    this.socket = io(this.baseUrl, {
      transports: ['websocket', 'polling'],
      auth: apiKey ? { token: apiKey } : undefined,
      reconnection: true,
      reconnectionAttempts: this.maxReconnectAttempts,
      reconnectionDelay: 1000,
      reconnectionDelayMax: 5000,
      timeout: 10000,
    });

    this.socket.on('connect', () => {
      this.reconnectAttempts = 0;
      this.emit('connect', null);
    });

    this.socket.on('disconnect', (reason) => {
      this.emit('disconnect', { reason });
    });

    this.socket.on('connect_error', (error) => {
      this.reconnectAttempts++;
      if (this.reconnectAttempts >= this.maxReconnectAttempts) {
        this.emit('connect_failed', { attempts: this.reconnectAttempts });
      }
    });

    this.socket.on('marketUpdate', (data) => this.emit('marketUpdate', data));
    this.socket.on('arbitrageUpdate', (data) => this.emit('arbitrageUpdate', data));
    this.socket.on('agentLog', (data) => this.emit('agentLog', data));
    this.socket.on('trade_result', (data) => this.emit('trade_result', data));
    this.socket.on('kill_switch', (data) => this.emit('kill_switch', data));
    this.socket.on('generation_complete', (data) => this.emit('generation_complete', data));
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
// SSE PARSER
// ==========================================

const parseSSEResponse = async (
  stream: ReadableStream<Uint8Array>,
  onToken: (token: string) => void,
  onDone: (driftLock?: string) => void,
  onError: (error: string) => void
) => {
  const reader = stream.getReader();
  const decoder = new TextDecoder();
  let buffer = '';
  
  try {
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      
      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split('\n');
      buffer = lines.pop() || '';
      
      for (const line of lines) {
        if (line.startsWith('data: ')) {
          try {
            const data = JSON.parse(line.slice(6));
            if (data.type === 'token') onToken(data.content);
            else if (data.type === 'done') onDone(data.drift_lock);
            else if (data.type === 'error') onError(data.content);
            else if (data.type === 'reflex') onToken(data.content);
          } catch (e) {
            // Not JSON, treat as plain text
            if (line.length > 6) onToken(line.slice(6));
          }
        }
      }
    }
  } catch (error) {
    onError(error instanceof Error ? error.message : 'Stream error');
  } finally {
    reader.releaseLock();
  }
};

// ==========================================
// HELPER: Extract JSON from text
// ==========================================

const extractJSON = (text: string): any | null => {
  // Pattern 1: Direct JSON object
  let match = text.match(/\{[\s\S]*\}/);
  if (match) {
    try {
      return JSON.parse(match[0]);
    } catch (e) {}
  }
  
  // Pattern 2: After "Portfolio:"
  match = text.match(/Portfolio:\s*(\{[\s\S]*\})/);
  if (match) {
    try {
      return JSON.parse(match[1]);
    } catch (e) {}
  }
  
  // Pattern 3: After "📊 Portfolio:"
  match = text.match(/📊\s*Portfolio:\s*(\{[\s\S]*\})/);
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
        version: '15.3.0',
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
          const defaultKey = "rez-hive-admin-key-2026";
          const keyToUse = apiKey || defaultKey;
          
          set(state => {
            state.apiKey = keyToUse;
            api.setApiKey(keyToUse);
          });
          
          set({ isLoading: true, error: null });
          
          try {
            const health = await api.health();
            set(state => {
              state.connected = true;
              state.version = health.version;
              state.telemetry.workers = health.workers;
              state.telemetry.memory = health.memory_entries;
              state.telemetry.gpu = health.gpu || { has_gpu: false };
              state.role = 'admin';
            });
            
            ws.connect(keyToUse);
            
            ws.on('marketUpdate', (data: MarketData[]) => {
              set(state => { state.marketData = data; });
            });
            
            ws.on('arbitrageUpdate', (data: any[]) => {
              set(state => { state.arbitrageOpportunities = data; });
            });
            
            ws.on('agentLog', (data: any) => {
              set(state => {
                state.messages.push({
                  id: `system-${Date.now()}`,
                  role: 'system',
                  content: data.message,
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
                  content: `Trade Result: ${JSON.stringify(data)}`,
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
                  content: `🔴 KILL SWITCH ACTIVATED by ${data.triggered_by}`,
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
            
            await Promise.allSettled([
              get().fetchWorkers(),
              get().fetchTelemetry(),
              get().fetchMemory(),
              get().fetchChainStats(),
              get().fetchKillSwitchStatus(),
              get().fetchPortfolio(),
              get().checkComfyUI(),
            ]);
            
          } catch (error: any) {
            console.error('Connection error:', error);
            set({ error: error.message, connected: false });
          } finally {
            set({ isLoading: false });
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
          });
        },

        // System actions
        fetchHealth: async () => {
          try {
            const health = await api.health();
            set(state => {
              state.version = health.version;
              state.telemetry.workers = health.workers;
              state.telemetry.memory = health.memory_entries;
              state.telemetry.gpu = health.gpu || { has_gpu: false };
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
              state.workers = status.workers;
              state.telemetry.workers = status.total;
            });
          } catch (error: any) {
            console.error('Workers fetch failed:', error);
            set({ error: error.message });
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
                workers: health.workers,
                memory: health.memory_entries,
                gpu: health.gpu || { has_gpu: false },
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
              state.memory.blueprints = blueprints.blueprints;
              state.memory.total = blueprints.blueprints.length;
            });
          } catch (error: any) {
            console.error('Memory fetch failed:', error);
            set({ error: error.message });
          }
        },

        searchMemory: async (query: string) => {
          if (!query.trim()) return [];
          try {
            const results = await api.memorySearch(query);
            set(state => {
              state.memory.searchResults = results.results;
            });
            return results.results;
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
            set({ error: error.message });
          }
        },

        fetchDriftEvents: async (limit: number = 50) => {
          try {
            const events = await api.driftEvents(limit);
            set(state => {
              state.driftEvents = events.events;
            });
          } catch (error: any) {
            console.error('Drift events fetch failed:', error);
            set({ error: error.message });
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
                if (portfolioData) {
                  set(state => {
                    state.portfolio = {
                      balance: portfolioData.balance ?? state.portfolio.balance,
                      positions: portfolioData.positions ?? {},
                      total_value: portfolioData.total_value ?? portfolioData.balance ?? state.portfolio.total_value,
                      trades: portfolioData.trades ?? state.portfolio.trades,
                    };
                  });
                } else {
                  console.warn('No JSON found in portfolio response:', fullResponse);
                }
              },
              (error) => { console.error('Portfolio fetch error:', error); }
            );
          } catch (error: any) {
            console.error('Portfolio fetch failed:', error);
            set({ error: error.message });
          }
        },

        executeTrade: async (action: 'buy' | 'sell', symbol: string, amount: number, price?: number) => {
          try {
            const task = `/trade ${action} ${symbol} ${amount}`;
            const stream = await api.chat(task);
            let success = false;
            
            await parseSSEResponse(
              stream,
              (token) => { if (token.includes('success')) success = true; },
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
                  } catch (e) {}
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
            set({ error: error.message });
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
            id: `user-${Date.now()}`,
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

        clearMessages: () => {
          set({ messages: [], currentResponse: '' });
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
            const stream = await api.generateImage(prompt, width, height);
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
            const stream = await api.generateVideo(prompt);
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
          await get().sendMessage(command);
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
      }),
    }
  )
);

// ==========================================
// CUSTOM HOOKS
// ==========================================

export const useAutoRefresh = (interval: number = 5000) => {
  const { fetchWorkers, fetchTelemetry, fetchChainStats, fetchKillSwitchStatus, fetchPortfolio, connected } = usePhoenixStore();
  
  React.useEffect(() => {
    if (!connected) return;
    const timer = setInterval(() => {
      fetchWorkers();
      fetchTelemetry();
      fetchChainStats();
      fetchKillSwitchStatus();
      fetchPortfolio();
    }, interval);
    return () => clearInterval(timer);
  }, [connected, interval, fetchWorkers, fetchTelemetry, fetchChainStats, fetchKillSwitchStatus, fetchPortfolio]);
};