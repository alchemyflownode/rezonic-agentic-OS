import { create } from 'zustand';
import { persist, createJSONStorage } from 'zustand/middleware';

// ============================================================================
// TYPES
// ============================================================================
export interface Message {
  id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  driftLock?: string;
  timestamp: string;
  isStreaming?: boolean;
}

export interface Telemetry {
  status: 'online' | 'offline' | 'checking' | 'drifted';
  workers: number;
  integrity_score: number;
  drift_chain_length: number;
  uptime: number;
}

export interface WorkerStatus {
  name: string;
  status: string;
  drift_score: number;
  last_heartbeat: number;
}

// ============================================================================
// API CONFIG
// ============================================================================
const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8002';
const API_KEY = process.env.NEXT_PUBLIC_API_KEY || 'rez-hive-admin-key-2026';

// ============================================================================
// STORE INTERFACE
// ============================================================================
interface SovereignState {
  // State
  telemetry: Telemetry;
  workers: WorkerStatus[];
  messages: Message[];
  isStreaming: boolean;
  activeTab: 'chat' | 'gallery' | 'workers';
  sidebarOpen: boolean;
  integrityHistory: number[];
  
  // Actions
  fetchTelemetry: () => Promise<void>;
  fetchWorkers: () => Promise<void>;
  sendMessage: (content: string) => Promise<void>;
  updateStreamingMessage: (id: string, content: string, driftLock?: string) => void;
  finishStreaming: (id: string) => void;
  clearMessages: () => void;
  updateIntegrity: (score: number) => void;
  setActiveTab: (tab: 'chat' | 'gallery' | 'workers') => void;
  toggleSidebar: () => void;
  reset: () => void;
}

// ============================================================================
// API HELPERS
// ============================================================================
async function fetchWithAuth(endpoint: string, options?: RequestInit) {
  const res = await fetch(`${API_BASE}${endpoint}`, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${API_KEY}`,
      ...options?.headers,
    },
  });
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return res.json();
}

// ============================================================================
// STORE IMPLEMENTATION
// ============================================================================
export const useSovereignStore = create<SovereignState>()(
  persist(
    (set, get) => ({
      // Initial State
      telemetry: {
        status: 'checking',
        workers: 0,
        integrity_score: 98,
        drift_chain_length: 0,
        uptime: 0,
      },
      workers: [],
      messages: [],
      isStreaming: false,
      activeTab: 'chat',
      sidebarOpen: true,
      integrityHistory: new Array(30).fill(98),
      
      // Actions
      fetchTelemetry: async () => {
        try {
          const data = await fetchWithAuth('/health');
          const newScore = data.integrity_score || 98;
          set({
            telemetry: {
              status: 'online',
              workers: data.workers || 0,
              integrity_score: newScore,
              drift_chain_length: data.drift_chain_length || 0,
              uptime: data.uptime || 0,
            }
          });
          get().updateIntegrity(newScore);
        } catch (error) {
          set({ telemetry: { ...get().telemetry, status: 'offline' } });
        }
      },
      
      fetchWorkers: async () => {
        try {
          const data = await fetchWithAuth('/workers/status');
          set({ workers: data.workers || [] });
        } catch (error) {
          console.error('Failed to fetch workers:', error);
        }
      },
      
      sendMessage: async (content: string) => {
        if (!content.trim() || get().isStreaming) return;
        
        const userMessage: Message = {
          id: crypto.randomUUID(),
          role: 'user',
          content: content.trim(),
          timestamp: new Date().toLocaleTimeString(),
        };
        
        const assistantId = crypto.randomUUID();
        const assistantMessage: Message = {
          id: assistantId,
          role: 'assistant',
          content: '',
          timestamp: new Date().toLocaleTimeString(),
          isStreaming: true,
        };
        
        set({ 
          messages: [...get().messages, userMessage, assistantMessage],
          isStreaming: true,
        });
        
        try {
          const response = await fetch(`${API_BASE}/kernel/stream`, {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
              'Authorization': `Bearer ${API_KEY}`,
            },
            body: JSON.stringify({ task: content }),
          });
          
          const reader = response.body?.getReader();
          const decoder = new TextDecoder();
          let fullContent = '';
          let buffer = '';
          let driftLock = '';
          
          while (reader) {
            const { done, value } = await reader.read();
            if (done) break;
            
            buffer += decoder.decode(value, { stream: true });
            const lines = buffer.split('\n');
            buffer = lines.pop() || '';
            
            for (const line of lines) {
              if (line.startsWith('data: ')) {
                try {
                  const data = JSON.parse(line.slice(6));
                  if (data.content) fullContent += data.content;
                  if (data.drift_lock) driftLock = data.drift_lock;
                  get().updateStreamingMessage(assistantId, fullContent, driftLock);
                } catch (e) {}
              }
            }
          }
        } catch (error) {
          console.error('Send message failed:', error);
          get().updateStreamingMessage(assistantId, '❌ Connection lost');
        } finally {
          get().finishStreaming(assistantId);
        }
      },
      
      updateStreamingMessage: (id, content, driftLock) => {
        set({
          messages: get().messages.map(m =>
            m.id === id ? { ...m, content, driftLock: driftLock || m.driftLock } : m
          ),
        });
      },
      
      finishStreaming: (id) => {
        set({
          messages: get().messages.map(m =>
            m.id === id ? { ...m, isStreaming: false } : m
          ),
          isStreaming: false,
        });
      },
      
      clearMessages: () => set({ messages: [] }),
      
      updateIntegrity: (score) => {
        set({
          integrityHistory: [...get().integrityHistory.slice(-29), score],
        });
      },
      
      setActiveTab: (tab) => set({ activeTab: tab }),
      toggleSidebar: () => set({ sidebarOpen: !get().sidebarOpen }),
      reset: () => set({ messages: [], isStreaming: false }),
    }),
    {
      name: 'sovereign-storage',
      storage: createJSONStorage(() => localStorage),
      partialize: (state) => ({
        messages: state.messages.slice(-50),
        telemetry: {
          integrity_score: state.telemetry.integrity_score,
        },
        integrityHistory: state.integrityHistory,
      }),
    }
  )
);

// ============================================================================
// SELECTORS (Performance)
// ============================================================================
export const selectTelemetry = (state: SovereignState) => state.telemetry;
export const selectMessages = (state: SovereignState) => state.messages;
export const selectWorkers = (state: SovereignState) => state.workers;
export const selectIntegrityHistory = (state: SovereignState) => state.integrityHistory;
