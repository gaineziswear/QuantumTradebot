/**
 * Shared code between client and server
 * Useful to share types between client and server
 * and/or small pure JS functions that can be used on both client and server
 */

/**
 * Example response type for /api/demo
 */
export interface DemoResponse {
  message: string;
}

// Automation Status Types
export interface AutomationStatus {
  is_running: boolean;
  current_phase: string;
  progress_percentage: number;
  last_action: string;
  started_at: string | null;
  total_runtime: number;
  symbols_processed: number;
  total_symbols: number;
  model_confidence: number;
  risk_score: number;
  trading_mode: string;
  market_data_symbols: string[];
  live_prices: Record<string, number>;
  risk_metrics: Record<string, any>;
}

// Trading Response Types
export interface TradingResponse {
  success: boolean;
  message: string;
  data?: any;
}

// Live Prices Response
export interface LivePricesResponse {
  prices: Record<string, number>;
  last_updated: string;
}

// Risk Metrics Types
export interface RiskMetrics {
  max_position_size: number;
  stop_loss_percentage: number;
  take_profit_percentage: number;
  max_drawdown_threshold: number;
  current_drawdown: number;
  var_95: number;
  risk_score: number;
  active_positions: number;
  max_concurrent_positions: number;
  trading_mode: string;
  system_status: string;
}

// Trading Status (matching what Dashboard expects)
export interface TradingStatus {
  is_running: boolean;
  is_live_trading: boolean;
  current_capital: number;
  total_pnl: number;
  daily_pnl: number;
  active_positions: number;
  total_trades: number;
  winning_trades: number;
  losing_trades: number;
  win_rate: number;
  last_trade_time?: string;
  model_last_updated?: string;
}

// Performance Metrics
export interface PerformanceMetrics {
  total_pnl: number;
  win_rate: number;
  sharpe_ratio: number;
  max_drawdown: number;
  total_trades: number;
  var: number;
  volatility: number;
  daily_pnl?: number;
  winning_trades?: number;
  losing_trades?: number;
}

// Trade interface
export interface Trade {
  id: string;
  symbol: string;
  side: string;
  entry_price: number;
  exit_price?: number;
  quantity: number;
  pnl?: number;
  status: string;
  confidence_score?: number;
  timestamp: string;
  is_live: boolean;
}

// AI Status
export interface AIStatus {
  is_training: boolean;
  progress_percentage: number;
  model_confidence: string;
  current_epoch?: number;
  total_epochs?: number;
  last_training?: string;
  feature_count?: number;
  model_version?: string;
}

// Portfolio
export interface Portfolio {
  total_value_usdt: number;
  portfolio: Array<{
    asset: string;
    balance: number;
    value_usdt: number;
    percentage: number;
  }>;
  last_updated: string;
}
