// hooks/usePhoenix.ts
import { usePhoenixStore, useAutoRefresh } from '@/store/phoenixStore';
import { useCallback } from 'react';

export const usePhoenix = () => {
  const {
    connected, isLoading, error, messages, isStreaming, currentResponse,
    workers, telemetry, portfolio, marketData, killSwitch, chainStats, comfyui, version,
    connect, disconnect, sendMessage, executeTrade, generateImage, generateVideo,
    activateKillSwitch, clearMessages, fetchPortfolio, fetchWorkers, fetchTelemetry,
    fetchChainStats, fetchKillSwitchStatus, checkComfyUI, runBacktest, searchMemory,
  } = usePhoenixStore();

  return {
    connected, isLoading, error, messages, isStreaming, currentResponse,
    workers, telemetry, portfolio, marketData, killSwitch, chainStats, comfyui, version,
    connect, disconnect, sendMessage, executeTrade, generateImage, generateVideo,
    activateKillSwitch, clearMessages, fetchPortfolio, fetchWorkers, fetchTelemetry,
    fetchChainStats, fetchKillSwitchStatus, checkComfyUI, runBacktest, searchMemory,
  };
};

export const useCommandParser = () => {
  const { sendMessage, generateImage, generateVideo, executeTrade } = usePhoenix();

  const executeCommand = useCallback(async (input: string) => {
    const trimmed = input.trim();
    if (trimmed.startsWith('/generate')) {
      const prompt = trimmed.replace('/generate', '').trim();
      if (prompt) { await generateImage(prompt); return { success: true, type: 'image', prompt }; }
    }
    if (trimmed.startsWith('/video')) {
      const prompt = trimmed.replace('/video', '').trim();
      if (prompt) { await generateVideo(prompt); return { success: true, type: 'video', prompt }; }
    }
    if (trimmed.startsWith('/trade')) {
      const parts = trimmed.split(' ');
      if (parts.length >= 4) {
        const action = parts[1] as 'buy' | 'sell';
        const symbol = parts[2];
        const amount = parseFloat(parts[3]);
        if (!isNaN(amount)) { await executeTrade(action, symbol, amount); return { success: true, type: 'trade', action, symbol, amount }; }
      }
    }
    if (trimmed === '/portfolio') { await usePhoenixStore.getState().fetchPortfolio(); return { success: true, type: 'portfolio' }; }
    if (trimmed === '/workers') { await usePhoenixStore.getState().fetchWorkers(); return { success: true, type: 'workers' }; }
    if (trimmed === '/health') { await usePhoenixStore.getState().fetchTelemetry(); return { success: true, type: 'health' }; }
    await sendMessage(trimmed);
    return { success: true, type: 'chat', message: trimmed };
  }, [sendMessage, generateImage, generateVideo, executeTrade]);

  return { executeCommand };
};

export { useAutoRefresh };
