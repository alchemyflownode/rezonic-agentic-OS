// lib/phoenix-sse.ts
export interface SSEEvent {
  type: string;
  timestamp: string;
  source: string;
  payload: Record<string, any>;
}

export interface SSEHandlers {
  onConnect?: () => void;
  onDisconnect?: () => void;
  onError?: (error: Error) => void;
  onIntegrityUpdate?: (score: number, delta: number) => void;
  onWorkerUpdate?: (workers: any[]) => void;
}

export class PhoenixSSEClient {
  private eventSource: EventSource | null = null;
  private reconnectAttempts = 0;
  private readonly maxReconnectAttempts = 5;
  private readonly reconnectDelay = 1000;
  private apiKey: string;
  private baseUrl: string;

  constructor(baseUrl: string, apiKey: string, private handlers: SSEHandlers) {
    this.baseUrl = baseUrl;
    this.apiKey = apiKey;
  }

  connect(): void {
    if (this.eventSource?.readyState === EventSource.OPEN) return;

    const url = `${this.baseUrl}/sse/stream?api_key=${encodeURIComponent(this.apiKey)}`;
    this.eventSource = new EventSource(url);

    this.eventSource.onopen = () => {
      console.log('🔗 SSE connected');
      this.reconnectAttempts = 0;
      this.handlers.onConnect?.();
    };

    this.eventSource.onmessage = (event) => {
      try {
        const sseEvent: SSEEvent = JSON.parse(event.data);
        
        switch (sseEvent.type) {
          case 'integrity.update':
            this.handlers.onIntegrityUpdate?.(
              sseEvent.payload.current_score,
              sseEvent.payload.delta
            );
            break;
          case 'worker.status_update':
            this.handlers.onWorkerUpdate?.(sseEvent.payload.workers);
            break;
        }
        
        this.handlers.onEvent?.(sseEvent);
      } catch (error) {
        console.error('SSE parse error:', error);
      }
    };

    this.eventSource.onerror = () => {
      this.handlers.onError?.(new Error('SSE connection lost'));
      this.handleReconnect();
    };
  }

  private handleReconnect(): void {
    if (this.reconnectAttempts >= this.maxReconnectAttempts) {
      this.handlers.onDisconnect?.();
      return;
    }

    this.reconnectAttempts++;
    const delay = this.reconnectDelay * Math.pow(2, this.reconnectAttempts - 1);
    
    console.log(`🔄 SSE reconnecting in ${delay}ms (attempt ${this.reconnectAttempts})`);
    setTimeout(() => this.connect(), delay);
  }

  disconnect(): void {
    if (this.eventSource) {
      this.eventSource.close();
      this.eventSource = null;
      this.handlers.onDisconnect?.();
    }
  }

  isConnected(): boolean {
    return this.eventSource?.readyState === EventSource.OPEN;
  }
}

// ============================================================================
// HOOK: usePhoenixSSE
// ============================================================================
import { useEffect, useRef } from 'react';
import { useSovereignStore } from '@/lib/store/useSovereignStore';

export function usePhoenixSSE() {
  const clientRef = useRef<PhoenixSSEClient | null>(null);
  const { updateIntegrity, fetchWorkers } = useSovereignStore();

  useEffect(() => {
    const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8002';
    const API_KEY = process.env.NEXT_PUBLIC_API_KEY || '';

    clientRef.current = new PhoenixSSEClient(API_BASE, API_KEY, {
      onConnect: () => console.log('🟢 SSE connected'),
      onDisconnect: () => console.log('🔴 SSE disconnected'),
      onError: (error) => console.error('SSE error:', error),
      onIntegrityUpdate: (score, delta) => {
        updateIntegrity(score);
        if (Math.abs(delta) > 5) {
          console.warn(`Integrity shift: ${delta >= 0 ? '+' : ''}${delta.toFixed(1)}%`);
        }
      },
      onWorkerUpdate: (workers) => {
        fetchWorkers();
      },
    });

    clientRef.current.connect();

    return () => {
      clientRef.current?.disconnect();
    };
  }, [updateIntegrity, fetchWorkers]);

  return {
    isConnected: () => clientRef.current?.isConnected() || false,
    disconnect: () => clientRef.current?.disconnect(),
  };
}
