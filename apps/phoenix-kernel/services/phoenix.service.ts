/**
 * Phoenix API Service - Handles all kernel communication
 */

const API_KEY = process.env.NEXT_PUBLIC_PHOENIX_API_KEY || 'rez-hive-admin-key-2026';
const API_URL = process.env.NEXT_PUBLIC_PHOENIX_API_URL || 'http://localhost:8002';

export interface HealthStatus {
  status: string;
  version: string;
  uptime: number;
  workers: number;
  active_workers: number;
  memory_entries: number;
  drift_chain: number;
  events: number;
  gpu: string | null;
  gpu_temp: number;
  gpu_util: number;
  consciousness: number;
  sce_enforcement: string;
  environment: string;
  ollama_connected: boolean;
}

export interface ExecutionResult {
  output: string;
  error?: string;
  duration: number;
  driftLock?: string;
  blueprint?: any;
}

export interface WorkerInfo {
  name: string;
  path: string;
  loaded: number;
  module: string;
  metrics?: {
    calls: number;
    errors: number;
    avg_duration: number;
  };
}

export interface EventStats {
  total_events: number;
  chain_integrity: boolean;
  genesis_hash: string;
  latest_hash: string;
  event_counts: Record<string, number>;
  persistence_queue: number;
}

class PhoenixServiceClass {
  private abortControllers: Map<string, AbortController> = new Map();

  private async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<T> {
    const response = await fetch(`${API_URL}${endpoint}`, {
      ...options,
      headers: {
        'X-Hive-API-Key': API_KEY,
        'Content-Type': 'application/json',
        ...options.headers,
      },
    });

    if (!response.ok) {
      const error = await response.text();
      throw new Error(`HTTP ${response.status}: ${error}`);
    }

    return response.json();
  }

  // Health
  async getHealth(): Promise<HealthStatus> {
    return this.request('/health');
  }

  // Workers
  async getWorkers(): Promise<{ 
    loaded: string[]; 
    count: number; 
    details: Record<string, WorkerInfo> 
  }> {
    return this.request('/workers/list');
  }

  async getWorkerMetrics(): Promise<any> {
    return this.request('/workers/metrics');
  }

  // SCE Protocol
  async getSCEStatus(): Promise<{
    version: string;
    blueprints: number;
    drift_chain: string[];
    drift_chain_length: number;
  }> {
    return this.request('/sce/status');
  }

  // Memory
  async getBlueprints(): Promise<{ count: number; blueprints: string[] }> {
    return this.request('/memory/blueprints');
  }

  async verifyBlueprint(driftLock: string): Promise<{ verified: boolean; badge?: string }> {
    return this.request(`/memory/verify/${driftLock}`);
  }

  async searchMemory(query: string, limit: number = 10): Promise<any[]> {
    return this.request(`/memory/search?query=${encodeURIComponent(query)}&limit=${limit}`);
  }

  // Events
  async getEventStats(): Promise<EventStats> {
    return this.request('/events/stats');
  }

  async getRecentEvents(limit: number = 100, eventType?: string): Promise<any[]> {
    const url = eventType 
      ? `/events/recent?limit=${limit}&event_type=${encodeURIComponent(eventType)}`
      : `/events/recent?limit=${limit}`;
    return this.request(url);
  }

  // Constitution
  async getConstitutionStats(): Promise<any> {
    return this.request('/constitution/stats');
  }

  async evaluateAction(action: string, context: any = {}): Promise<any> {
    return this.request('/constitution/evaluate', {
      method: 'POST',
      body: JSON.stringify({ action, context }),
    });
  }

  // Router
  async getRouterStats(): Promise<any> {
    return this.request('/router/stats');
  }

  // Ollama
  async getOllamaStatus(): Promise<{ connected: boolean; models: string[]; stats: any }> {
    return this.request('/ollama/status');
  }

  // Task Execution
  async executeTask(task: string, worker: string = 'brain'): Promise<ExecutionResult> {
    return this.request('/kernel/stream', {
      method: 'POST',
      body: JSON.stringify({ task }),
    });
  }

  // Streaming
  streamTask(
    task: string,
    onChunk: (chunk: string) => void,
    onDone: (driftLock?: string) => void,
    onError: (error: string) => void
  ): AbortController {
    const controller = new AbortController();
    const id = Math.random().toString(36).substring(7);
    this.abortControllers.set(id, controller);

    fetch(`${API_URL}/kernel/stream`, {
      method: 'POST',
      headers: {
        'X-Hive-API-Key': API_KEY,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ task }),
      signal: controller.signal,
    })
      .then(async (response) => {
        const reader = response.body?.getReader();
        const decoder = new TextDecoder();
        let buffer = '';

        while (reader) {
          const { done, value } = await reader.read();
          if (done) break;

          buffer += decoder.decode(value, { stream: true });
          const lines = buffer.split('\n\n');
          buffer = lines.pop() || '';

          for (const line of lines) {
            if (line.startsWith('data: ')) {
              onChunk(line);
            }
          }
        }

        onDone();
      })
      .catch((err) => {
        if (err.name === 'AbortError') {
          console.log('Stream aborted');
        } else {
          onError(err.message);
        }
      })
      .finally(() => {
        this.abortControllers.delete(id);
      });

    return controller;
  }

  abortStream(id: string) {
    const controller = this.abortControllers.get(id);
    if (controller) {
      controller.abort();
      this.abortControllers.delete(id);
    }
  }
}

export const PhoenixService = new PhoenixServiceClass();
export default PhoenixService;