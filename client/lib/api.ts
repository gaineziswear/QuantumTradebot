import React from 'react';
import type {
  TradingStatus,
  PerformanceMetrics,
  Trade,
  AIStatus,
  Portfolio
} from '@shared/api';

// Re-export types for backward compatibility
export type { TradingStatus, PerformanceMetrics, Trade, AIStatus, Portfolio };

export interface MarketPrice {
  symbol: string;
  price: string;
  change_24h?: string;
  volume_24h?: string;
}

export interface SystemStats {
  bot_initialized: boolean;
  trading_active: boolean;
  websocket_stats: {
    connected_clients: number;
    messages_sent: number;
    success_rate: number;
  };
  uptime: string;
  version: string;
}

class APIClient {
  private baseURL: string;
  private token: string | null = null;
  private pollingTimer: NodeJS.Timeout | null = null;
  private pollingInterval = 2000; // 2 seconds for near real-time updates
  private slowPollingInterval = 10000; // 10 seconds for when no changes detected
  private eventHandlers: Map<string, Set<Function>> = new Map();
  private lastDataFetch: { [key: string]: any } = {};
  private consecutiveNoChanges = 0;
  private currentInterval = 2000;

  constructor(baseURL: string = '/api') {
    this.baseURL = baseURL;

    // Safely access localStorage (might not be available in SSR)
    try {
      this.token = typeof window !== 'undefined' ? localStorage.getItem('trading_bot_token') : null;
    } catch (error) {
      console.warn('LocalStorage not accessible:', error);
      this.token = null;
    }

    this.initializePolling();
  }

  private async request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
    const url = `${this.baseURL}${endpoint}`;
    const headers: HeadersInit = {
      'Content-Type': 'application/json',
      ...options.headers,
    };

    if (this.token) {
      headers['Authorization'] = `Bearer ${this.token}`;
    }

    try {
      const response = await fetch(url, {
        ...options,
        headers,
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ error: 'Unknown error' }));

        // Handle backend service unavailable
        if (response.status === 503 && errorData.message?.includes('Backend service unavailable')) {
          throw new Error('⚠️ Python backend not running. Please start it with: python dev_start.py');
        }

        throw new Error(errorData.detail || errorData.error || errorData.message || `HTTP ${response.status}`);
      }

      return response.json();
    } catch (error) {
      if (error instanceof TypeError && error.message.includes('fetch')) {
        throw new Error('🔌 Cannot connect to backend. Please ensure the Python backend is running on port 8000.');
      }
      throw error;
    }
  }

  // Authentication
  isAuthenticated(): boolean {
    return !!this.token;
  }

  getToken(): string | null {
    return this.token;
  }

  async login(credentials: { username: string; password: string }): Promise<{ success: boolean; token: string; user: any }> {
    const response = await this.request<{ success: boolean; token: string; user: any }>('/auth/login', {
      method: 'POST',
      body: JSON.stringify(credentials),
    });

    if (response.success && response.token) {
      this.token = response.token;
      try {
        if (typeof window !== 'undefined') {
          localStorage.setItem('trading_bot_token', response.token);
        }
      } catch (error) {
        console.warn('Could not save token to localStorage:', error);
      }

      // Start polling for real-time updates after successful login
      this.restartPolling();
    }

    return response;
  }

  async logout(): Promise<void> {
    try {
      await this.request('/auth/logout', { method: 'POST' });
    } finally {
      this.token = null;
      try {
        if (typeof window !== 'undefined') {
          localStorage.removeItem('trading_bot_token');
        }
      } catch (error) {
        console.warn('Could not remove token from localStorage:', error);
      }
      this.stopPolling();
    }
  }

  // Trading Controls
  async startTrading(): Promise<{ success: boolean; message: string }> {
    return this.request('/trading/start', { method: 'POST' });
  }

  async stopTrading(): Promise<{ success: boolean; message: string }> {
    return this.request('/trading/stop', { method: 'POST' });
  }

  async goLive(): Promise<{ success: boolean; message: string }> {
    return this.request('/trading/go-live', { method: 'POST' });
  }

  async addCapital(amount: number): Promise<{ success: boolean; message: string; new_capital: number }> {
    return this.request('/trading/add-capital', {
      method: 'POST',
      body: JSON.stringify({ amount }),
    });
  }

  // Data Retrieval
  async getTradingStatus(): Promise<TradingStatus> {
    return this.request('/trading/status');
  }

  async getPerformanceMetrics(): Promise<PerformanceMetrics> {
    return this.request('/trading/performance');
  }

  async getRecentTrades(limit: number = 10): Promise<Trade[]> {
    return this.request(`/trading/trades?limit=${limit}`);
  }

  async getPortfolio(): Promise<Portfolio> {
    return this.request('/trading/portfolio');
  }

  async getAIStatus(): Promise<AIStatus> {
    return this.request('/ai/status');
  }

  async getMarketPrices(): Promise<MarketPrice[]> {
    return this.request('/market/prices');
  }

  async getSystemStats(): Promise<SystemStats> {
    return this.request('/stats');
  }

  // AI Training
  async startAITraining(): Promise<{ success: boolean; message: string }> {
    return this.request('/ai/train', { method: 'POST' });
  }

  async startDataDownload(): Promise<{ success: boolean; message: string; task_id: string }> {
    return this.request('/data/download', { method: 'POST' });
  }

  // Health Check
  async healthCheck(): Promise<{ status: string; timestamp: string; bot_initialized: boolean }> {
    return this.request('/health');
  }

  // HTTP Polling for Real-time Updates
  private initializePolling(): void {
    if (typeof window === 'undefined') return; // Skip in SSR

    this.startPolling();
  }

  private startPolling(): void {
    if (this.pollingTimer) return; // Already polling

    console.log('🔄 Starting adaptive HTTP polling for real-time updates');

    // Initial data fetch
    this.pollAllData();

    // Set up adaptive polling interval
    this.scheduleNextPoll();
  }

  private scheduleNextPoll(): void {
    this.pollingTimer = setTimeout(() => {
      this.pollAllData();
      this.scheduleNextPoll(); // Schedule next poll
    }, this.currentInterval);
  }

  private async pollAllData(): Promise<void> {
    try {
      // Only poll if we have a token (user is logged in)
      if (!this.token) return;

      // Fetch all real-time data in parallel
      const [status, performance, trades, aiStatus, portfolio] = await Promise.allSettled([
        this.getTradingStatus(),
        this.getPerformanceMetrics(),
        this.getRecentTrades(10),
        this.getAIStatus(),
        this.getPortfolio()
      ]);

      // Process successful responses and emit events
      if (status.status === 'fulfilled') {
        this.emitDataUpdate('trading_status', status.value);
      }

      if (performance.status === 'fulfilled') {
        this.emitDataUpdate('performance_update', performance.value);
      }

      if (trades.status === 'fulfilled') {
        this.emitDataUpdate('trade_update', trades.value);
      }

      if (aiStatus.status === 'fulfilled') {
        this.emitDataUpdate('ai_status', aiStatus.value);
      }

      if (portfolio.status === 'fulfilled') {
        this.emitDataUpdate('portfolio_update', portfolio.value);
      }

    } catch (error) {
      // Silently handle polling errors to avoid spam
      console.debug('Polling error (will retry):', error);
    }
  }

  private emitDataUpdate(type: string, newData: any): void {
    // Only emit if data has changed to avoid unnecessary updates
    const lastData = this.lastDataFetch[type];
    const dataStr = JSON.stringify(newData);

    if (lastData !== dataStr) {
      this.lastDataFetch[type] = dataStr;
      this.handleMessage({ type, data: newData });

      // Reset to fast polling when changes detected
      this.consecutiveNoChanges = 0;
      this.currentInterval = this.pollingInterval;
    } else {
      // Increase interval if no changes for multiple polls
      this.consecutiveNoChanges++;
      if (this.consecutiveNoChanges > 5) {
        this.currentInterval = this.slowPollingInterval;
      }
    }
  }

  private handleMessage(data: any): void {
    const { type, data: messageData } = data;
    
    // Emit to registered handlers
    const handlers = this.eventHandlers.get(type);
    if (handlers) {
      handlers.forEach(handler => {
        try {
          handler(messageData);
        } catch (error) {
          console.error(`Error in ${type} handler:`, error);
        }
      });
    }

    // Emit to catch-all handlers
    const allHandlers = this.eventHandlers.get('*');
    if (allHandlers) {
      allHandlers.forEach(handler => {
        try {
          handler({ type, data: messageData });
        } catch (error) {
          console.error(`Error in catch-all handler:`, error);
        }
      });
    }
  }

  private stopPolling(): void {
    if (this.pollingTimer) {
      clearTimeout(this.pollingTimer);
      this.pollingTimer = null;
      this.consecutiveNoChanges = 0;
      this.currentInterval = this.pollingInterval;
      console.log('🛑 Stopped HTTP polling');
    }
  }

  private restartPolling(): void {
    this.stopPolling();
    this.startPolling();
  }

  // Event Subscription
  on(event: string, handler: Function): void {
    if (!this.eventHandlers.has(event)) {
      this.eventHandlers.set(event, new Set());
    }
    this.eventHandlers.get(event)!.add(handler);
  }

  off(event: string, handler: Function): void {
    const handlers = this.eventHandlers.get(event);
    if (handlers) {
      handlers.delete(handler);
      if (handlers.size === 0) {
        this.eventHandlers.delete(event);
      }
    }
  }

  // Polling status
  isPollingActive(): boolean {
    return this.pollingTimer !== null;
  }

  // Cleanup
  destroy(): void {
    this.stopPolling();
    this.eventHandlers.clear();
  }
}

// Create singleton instance
export const apiClient = new APIClient();

// React hook for API usage
export function useAPI() {
  return apiClient;
}

// WebSocket event types
export const WS_EVENTS = {
  TRADING_STATUS: 'trading_status',
  TRADE_UPDATE: 'trade_update',
  PERFORMANCE_UPDATE: 'performance_update',
  MARKET_DATA: 'market_data',
  AI_STATUS: 'ai_status',
  PORTFOLIO_UPDATE: 'portfolio_update',
  SYSTEM_ALERT: 'system_alert',
  TRAINING_PROGRESS: 'training_progress',
  CONNECTION: 'connection',
  SERVER_SHUTDOWN: 'server_shutdown',
} as const;

// Utility function for real-time data subscription
export function useRealTimeData<T>(
  event: string,
  callback: (data: T) => void,
  deps: React.DependencyList = []
) {
  React.useEffect(() => {
    apiClient.on(event, callback);
    return () => apiClient.off(event, callback);
  }, deps);
}

// Export types and client
export default apiClient;
