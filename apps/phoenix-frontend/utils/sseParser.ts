// D:\Rezonic_Agentic\apps\phoenix-frontend\utils\sseParser.ts

export interface SSEEvent {
  type: string;
  content?: string;
  drift_lock?: string;
  error?: string;
  [key: string]: any;
}

/**
 * Parse Server-Sent Events (SSE) stream
 * Handles the format: data: {"type":"reflex","content":"..."}\n\n
 */
export class SSEParser {
  private buffer: string = '';
  
  /**
   * Feed chunks of data and get parsed events
   */
  feed(chunk: string): SSEEvent[] {
    this.buffer += chunk;
    const events: SSEEvent[] = [];
    const lines = this.buffer.split('\n');
    
    // Keep the last incomplete line in buffer
    this.buffer = lines.pop() || '';
    
    for (const line of lines) {
      if (line.startsWith('data: ')) {
        try {
          const jsonStr = line.slice(6).trim();
          if (jsonStr) {
            const data = JSON.parse(jsonStr);
            events.push(data);
          }
        } catch (e) {
          // Not JSON, treat as raw content
          events.push({
            type: 'raw',
            content: line.slice(6)
          });
        }
      }
    }
    
    return events;
  }
  
  /**
   * Get remaining buffer (for final flush)
   */
  flush(): SSEEvent[] {
    const events: SSEEvent[] = [];
    if (this.buffer.trim()) {
      events.push({
        type: 'raw',
        content: this.buffer
      });
    }
    this.buffer = '';
    return events;
  }
}

/**
 * Helper to extract content from SSE stream
 */
export const extractSSEContent = async (
  response: Response,
  onEvent: (event: SSEEvent, fullContent: string) => void,
  onComplete?: (fullContent: string, driftLock?: string) => void
): Promise<string> => {
  const reader = response.body?.getReader();
  const decoder = new TextDecoder();
  const parser = new SSEParser();
  let fullContent = '';
  let driftLock: string | undefined;
  
  while (reader) {
    const { done, value } = await reader.read();
    if (done) break;
    
    const chunk = decoder.decode(value);
    const events = parser.feed(chunk);
    
    for (const event of events) {
      if (event.content) {
        fullContent += event.content;
      }
      if (event.drift_lock) {
        driftLock = event.drift_lock;
      }
      onEvent(event, fullContent);
    }
  }
  
  // Handle any remaining buffer
  const remaining = parser.flush();
  for (const event of remaining) {
    if (event.content) {
      fullContent += event.content;
    }
    onEvent(event, fullContent);
  }
  
  if (onComplete) {
    onComplete(fullContent, driftLock);
  }
  
  return fullContent;
};
