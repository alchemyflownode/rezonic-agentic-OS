// lib/phoenix-client.ts
const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8002';
const API_KEY = process.env.NEXT_PUBLIC_API_KEY || 'rez-hive-admin-key-2026';

export interface PhoenixResponse {
  type: 'reflex' | 'result' | 'error' | 'done';
  content?: string;
  drift_lock?: string;
}

export async function phoenixFetch(command: string): Promise<PhoenixResponse | null> {
  try {
    const response = await fetch(`${API_BASE}/kernel/stream`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${API_KEY}`
      },
      body: JSON.stringify({ task: command })
    });
    
    const text = await response.text();
    const lines = text.split('\n');
    
    for (const line of lines) {
      if (line.startsWith('data: ')) {
        try {
          return JSON.parse(line.slice(6));
        } catch (e) {}
      }
    }
    return null;
  } catch (error) {
    console.error('Phoenix API error:', error);
    return null;
  }
}

export async function phoenixStream(command: string, onChunk: (data: PhoenixResponse) => void): Promise<void> {
  try {
    const response = await fetch(`${API_BASE}/kernel/stream`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${API_KEY}`
      },
      body: JSON.stringify({ task: command })
    });
    
    const reader = response.body?.getReader();
    const decoder = new TextDecoder();
    let buffer = '';
    
    while (reader) {
      const { done, value } = await reader.read();
      if (done) break;
      
      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split('\n');
      buffer = lines.pop() || '';
      
      for (const line of lines) {
        if (line.startsWith('data: ')) {
          try {
            onChunk(JSON.parse(line.slice(6)));
          } catch (e) {}
        }
      }
    }
  } catch (error) {
    console.error('Stream error:', error);
  }
}
