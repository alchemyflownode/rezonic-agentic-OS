// store/phoenixStore.ts
import React from 'react';
import { create } from 'zustand';
import { persist, createJSONStorage } from 'zustand/middleware';
import { immer } from 'zustand/middleware/immer';
import { io, Socket } from 'socket.io-client';
import { useStream } from '@/store/phoenixStream';

// ==========================================
// TYPES & INTERFACES
// ==========================================

export type ErrorCategory = 'network' | 'kernel' | 'stream' | 'auth' | 'drift_violation';

export interface StreamMetadata {
  worker_id?: string;
  drift_lock?: string;
  latency_ms?: number;
  tokens_per_sec?: number;
  model_id?: string;
}

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

export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant' | 'system' | 'error';
  content: string;
  timestamp: number;
  isStreaming?: boolean;
  metadata?: StreamMetadata;
  error_type?: ErrorCategory;
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

// ==========================================
// SSE PARSER (THE INTERPRETER)
// ==========================================

const parseSSEResponse = async (
  stream: ReadableStream<Uint8Array>,
  onToken: (token: string) => void,
  onDone: (metadata: StreamMetadata) => void,
  onError: (error: string, category: ErrorCategory) => void,
  messageId: string
) => {
  const reader = stream.getReader();
  const decoder = new TextDecoder('utf-8');
  let buffer = '';
  let hasReceivedData = false;
  let startTime = Date.now();
  let tokenCount = 0;

  try {
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split('\n');
      buffer = lines.pop() || '';

      for (const line of lines) {
        const trimmed = line.trim();
        if (!trimmed || !trimmed.startsWith('data: ')) continue;

        try {
          const jsonStr = trimmed.slice(6).trim();
          const data = JSON.parse(jsonStr);
          const { pushEvent } = useStream.getState();

          switch (data.type) {
            case 'token':
              if (data.content) {
                hasReceivedData = true;
                tokenCount++;
                onToken(data.content);
                pushEvent({ id: crypto.randomUUID(), type: 'token', content: data.content });
              }
              break;
            case 'reflex':
              if (data.content) {
                hasReceivedData = true;
                onToken(data.content);
                pushEvent({ id: crypto.randomUUID(), type: 'status', message: `[REFLEX] ${data.content}` });
              }
              break;
            case 'done':
              onDone({
                drift_lock: data.drift_lock,
                latency_ms: Date.now() - startTime,
                tokens_per_sec: Math.round(tokenCount / (Math.max(1, Date.now() - startTime) / 1000)),
                model_id: data.model
              });
              pushEvent({ id: crypto.randomUUID(), type: 'result', data: { lock: data.drift_lock, messageId } });
              break;
            case 'error':
              if (!hasReceivedData) {
                onError(data.content || 'Kernel Execution Error', 'kernel');
                pushEvent({ id: crypto.randomUUID(), type: 'error', message: data.content });
              }
              break;
          }
        } catch (e) {
          const raw = trimmed.slice(6).trim();
          if (raw) { hasReceivedData = true; onToken(raw); }
        }
      }
    }
  } catch (err: any) {
    if (!hasReceivedData && err.name !== 'AbortError') onError(err.message, 'stream');
  } finally {
    reader.releaseLock();
  }
};

// ==========================================
// API CLIENT
// ==========================================

class PhoenixAPI {
  public baseUrl: string;
  private apiKey: string | null = null;

  constructor(baseUrl: string = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8002') {
    this.baseUrl = baseUrl;
  }

  setApiKey(key: string | null) { this.apiKey = key; }

  private async request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
    const headers: HeadersInit = { 'Content-Type': 'application/json', ...options.headers };
    if (this.apiKey) headers['Authorization'] = `Bearer ${this.apiKey}`;
    const response = await fetch(`${this.baseUrl}${endpoint}`, { ...options, headers });
    if (!response.ok) throw new Error(await response.text() || `HTTP ${response.status}`);
    return response.json();
  }

  async health() { return this.request<any>('/health'); }
  async workersStatus() { return this.request<any>('/workers/status'); }
  async chainStats() { return this.request<any>('/events/stats'); }
  async killStatus() { return this.request<any>('/kill/status'); }
  async resourceStats() { return this.request<any>('/resource/stats'); }
  
  async chatStream(task: string, model?: string, signal?: AbortSignal): Promise<ReadableStream<Uint8Array>> {
    const response = await fetch(`${this.baseUrl}/kernel/stream`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...(this.apiKey && { 'Authorization': `Bearer ${this.apiKey}` }),
      },
      body: JSON.stringify({ task, model }),
      signal
    });
    if (!response.ok || !response.body) throw new Error('Kernel stream offline');
    return response.body;
  }
}

const api = new PhoenixAPI();

// ==========================================
// ZUSTAND STORE
// ==========================================

export const usePhoenixStore = create<any>()(
  persist(
    immer((set, get) => {
      let socket: Socket | null = null;

      return {
        // Initial State
        connected: false,
        apiKey: null,
        role: null,
        version: '15.3.1',
        workers: [],
        telemetry: { workers: 0, memory: 0, gpu: { has_gpu: false }, chain_valid: false, kernel_load: 0 },
        portfolio: { balance: 1000000, positions: {}, total_value: 1000000, trades: [] },
        messages: [],
        activeStreams: {}, // Track AbortControllers for parallel processing
        isStreaming: false,
        error: null,
        lastUpdate: 0,

        // Connection Actions
        setApiKey: (key: string) => {
          set(state => { state.apiKey = key; });
          api.setApiKey(key);
        },

        connect: (apiKey?: string) => {
          const key = apiKey || get().apiKey || process.env.NEXT_PUBLIC_PHOENIX_API_KEY;
          if (key) get().setApiKey(key);

          if (socket?.connected) return;

          socket = io(api.baseUrl.replace(/^http/, 'ws'), {
            auth: { token: key },
            reconnection: true,
            reconnectionAttempts: 10,
            reconnectionDelay: 1000,
          });

          socket.on('connect', () => set({ connected: true }));
          socket.on('disconnect', () => set({ connected: false }));
          
          socket.onAny((event, data) => {
             useStream.getState().pushEvent({ id: crypto.randomUUID(), type: 'status', message: `[SIGNAL] ${event}` });
          });
        },

        disconnect: () => {
          socket?.disconnect();
          set({ connected: false });
        },

        // System Actions
        fetchWorkers: async () => {
          try {
            const data = await api.workersStatus();
            set(s => { s.workers = data.workers || []; });
          } catch (e) {}
        },

        fetchTelemetry: async () => {
          try {
            const data = await api.health();
            set(s => { s.telemetry.gpu = data.gpu; s.telemetry.workers = data.workers; });
          } catch (e) {}
        },

        fetchPortfolio: async () => {
          try {
            const stream = await api.chatStream('/portfolio');
            let buffer = '';
            await parseSSEResponse(stream, (t) => buffer += t, () => {
               const data = buffer.match(/\{[\s\S]*\}/);
               if (data) {
                 const parsed = JSON.parse(data[0]);
                 set(s => { s.portfolio = { ...s.portfolio, ...parsed }; });
               }
            }, () => {}, 'portfolio-update');
          } catch (e) {}
        },

        fetchChainStats: async () => { try { await api.chainStats(); } catch(e){} },
        fetchKillSwitchStatus: async () => { try { await api.killStatus(); } catch(e){} },
        fetchResourceStats: async () => { try { await api.resourceStats(); } catch(e){} },

        // Messaging & Reflexes
        sendMessage: async (message: string, model?: string) => {
          if (!message.trim()) return;
          
          const assistantId = `assistant-${Date.now()}`;
          const controller = new AbortController();

          set(state => {
            state.activeStreams[assistantId] = controller;
            state.isStreaming = true;
            state.messages.push({ id: `u-${Date.now()}`, role: 'user', content: message, timestamp: Date.now() });
            state.messages.push({ id: assistantId, role: 'assistant', content: '', timestamp: Date.now(), isStreaming: true });
          });

          try {
            const stream = await api.chatStream(message, model, controller.signal);
            let fullContent = '';

            await parseSSEResponse(
              stream,
              (token) => {
                fullContent += token;
                set(s => {
                  const m = s.messages.find((msg: any) => msg.id === assistantId);
                  if (m) m.content = fullContent;
                });
              },
              (metadata) => {
                set(s => {
                  const m = s.messages.find((msg: any) => msg.id === assistantId);
                  if (m) { m.isStreaming = false; m.metadata = metadata; }
                  delete s.activeStreams[assistantId];
                  s.isStreaming = Object.keys(s.activeStreams).length > 0;
                });
              },
              (err, category) => {
                set(s => {
                  const m = s.messages.find((msg: any) => msg.id === assistantId);
                  if (m) { m.content = `❌ [${category}] ${err}`; m.role = 'error'; m.isStreaming = false; }
                  delete s.activeStreams[assistantId];
                });
              },
              assistantId
            );
          } catch (e: any) {
             if (e.name === 'AbortError') return;
             set(s => { delete s.activeStreams[assistantId]; s.isStreaming = false; });
          }
        },

        sendReflexCommand: async (cmd: string) => {
          const command = cmd.startsWith('/') ? cmd : `/${cmd}`;
          return get().sendMessage(command);
        },

        stopStream: (id: string) => {
          if (get().activeStreams[id]) {
            get().activeStreams[id].abort();
            set(state => { delete state.activeStreams[id]; });
          }
        },

        clearMessages: () => set({ messages: [] }),
        setError: (error: string | null) => set({ error }),
        clearError: () => set({ error: null }),
      };
    }),
    {
      name: 'phoenix-v16-storage',
      storage: createJSONStorage(() => localStorage),
      partialize: (state: any) => ({
        apiKey: state.apiKey,
        portfolio: state.portfolio,
        messages: state.messages.slice(-30),
      }),
    }
  )
);

// ==========================================
// CUSTOM HOOKS (DASHBOARD COMPATIBILITY)
// ==========================================

export const useAutoRefresh = (interval: number = 5000) => {
  const { 
    fetchWorkers, fetchTelemetry, fetchChainStats, 
    fetchKillSwitchStatus, fetchPortfolio, fetchResourceStats, connected 
  } = usePhoenixStore();
  
  React.useEffect(() => {
    if (!connected) return;
    
    // Initial blast
    fetchWorkers(); fetchTelemetry(); fetchPortfolio();

    const timer = setInterval(() => {
      fetchWorkers();
      fetchTelemetry();
      fetchChainStats?.();
      fetchKillSwitchStatus?.();
      fetchPortfolio();
      fetchResourceStats?.();
    }, interval);
    
    return () => clearInterval(timer);
  }, [connected, interval, fetchWorkers, fetchTelemetry, fetchChainStats, fetchKillSwitchStatus, fetchPortfolio, fetchResourceStats]);
};

export const useWebSocket = () => {
  const { connected, connect, apiKey } = usePhoenixStore();
  React.useEffect(() => {
    if (!connected && apiKey) connect(apiKey);
  }, [connected, apiKey, connect]);
};

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