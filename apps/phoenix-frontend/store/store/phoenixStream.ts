// stores/phoenixStream.ts
import { create } from 'zustand';

export type StreamEvent =
  | { id: string; type: 'token'; content: string }
  | { id: string; type: 'status'; message: string }
  | { id: string; type: 'result'; data: any }
  | { id: string; type: 'error'; message: string }
  | { id: string; type: 'metric'; cpu?: number; workers?: number; memory?: number };

type StreamStore = {
  events: StreamEvent[];
  pushEvent: (event: StreamEvent) => void;
  clear: () => void;
  getLatest: () => StreamEvent | undefined;
};

export const useStream = create<StreamStore>((set, get) => ({
  events: [],

  pushEvent: (event) =>
    set((state) => ({
      events: [...state.events.slice(-500), event],
    })),

  clear: () => set({ events: [] }),

  getLatest: () => {
    const events = get().events;
    return events[events.length - 1];
  },
}));