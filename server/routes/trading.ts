import { RequestHandler } from "express";
import { spawn } from "child_process";
import path from "path";
import fs from "fs";

// Types for API responses
interface AutomationStatusResponse {
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

interface TradingResponse {
  success: boolean;
  message: string;
  data?: any;
}

interface LivePricesResponse {
  prices: Record<string, number>;
  last_updated: string;
}

// Helper function to execute Python scripts
const executePythonScript = (scriptName: string, args: string[] = []): Promise<any> => {
  return new Promise((resolve, reject) => {
    const pythonPath = process.env.PYTHON_PATH || 'python3';
    const scriptPath = path.join(process.cwd(), 'backend', scriptName);

    // Check if script exists
    if (!fs.existsSync(scriptPath)) {
      reject(new Error(`Python script not found: ${scriptPath}`));
      return;
    }
    
    const process = spawn(pythonPath, [scriptPath, ...args], {
      cwd: path.join(process.cwd(), 'backend'),
      env: {
        ...process.env,
        PYTHONPATH: path.join(process.cwd(), 'backend')
      }
    });

    let stdout = '';
    let stderr = '';

    process.stdout.on('data', (data) => {
      stdout += data.toString();
    });

    process.stderr.on('data', (data) => {
      stderr += data.toString();
    });

    process.on('close', (code) => {
      if (code === 0) {
        try {
          const result = JSON.parse(stdout.trim());
          resolve(result);
        } catch (e) {
          resolve({ success: true, message: stdout.trim() });
        }
      } else {
        reject(new Error(stderr || `Process exited with code ${code}`));
      }
    });

    process.on('error', (error) => {
      reject(error);
    });
  });
};

/**
 * Start the hedge fund automation workflow
 * Triggers: Data fetching -> AI training -> Automated trading
 */
export const startAutomation: RequestHandler = async (req, res) => {
  try {
    console.log('🚀 Starting hedge fund automation workflow...');
    
    // Execute the automation startup script
    const result = await executePythonScript('automation_start.py');
    
    const response: TradingResponse = {
      success: true,
      message: 'Hedge fund automation started successfully',
      data: result
    };
    
    res.status(200).json(response);
  } catch (error) {
    console.error('Failed to start automation:', error);
    
    const response: TradingResponse = {
      success: false,
      message: `Failed to start automation: ${error.message}`
    };
    
    res.status(500).json(response);
  }
};

/**
 * Stop the automation workflow
 */
export const stopAutomation: RequestHandler = async (req, res) => {
  try {
    console.log('🛑 Stopping hedge fund automation...');
    
    const result = await executePythonScript('automation_stop.py');
    
    const response: TradingResponse = {
      success: true,
      message: 'Automation stopped successfully',
      data: result
    };
    
    res.status(200).json(response);
  } catch (error) {
    console.error('Failed to stop automation:', error);
    
    const response: TradingResponse = {
      success: false,
      message: `Failed to stop automation: ${error.message}`
    };
    
    res.status(500).json(response);
  }
};

/**
 * Get current automation status and progress
 */
export const getAutomationStatus: RequestHandler = async (req, res) => {
  try {
    const result = await executePythonScript('automation_status.py');
    
    const response: AutomationStatusResponse = {
      is_running: result.is_running || false,
      current_phase: result.current_phase || 'idle',
      progress_percentage: result.progress_percentage || 0,
      last_action: result.last_action || 'Waiting to start',
      started_at: result.started_at || null,
      total_runtime: result.total_runtime || 0,
      symbols_processed: result.symbols_processed || 0,
      total_symbols: result.total_symbols || 10,
      model_confidence: result.model_confidence || 0,
      risk_score: result.risk_score || 0,
      trading_mode: result.trading_mode || 'testnet',
      market_data_symbols: result.market_data_symbols || [],
      live_prices: result.live_prices || {},
      risk_metrics: result.risk_metrics || {}
    };
    
    res.status(200).json(response);
  } catch (error) {
    console.error('Failed to get automation status:', error);
    
    // Return default status if script fails
    const response: AutomationStatusResponse = {
      is_running: false,
      current_phase: 'error',
      progress_percentage: 0,
      last_action: `Error: ${error.message}`,
      started_at: null,
      total_runtime: 0,
      symbols_processed: 0,
      total_symbols: 10,
      model_confidence: 0,
      risk_score: 0,
      trading_mode: 'testnet',
      market_data_symbols: [],
      live_prices: {},
      risk_metrics: {}
    };
    
    res.status(200).json(response);
  }
};

/**
 * Toggle between testnet and live trading
 */
export const toggleTradingMode: RequestHandler = async (req, res) => {
  try {
    const { mode } = req.body;
    
    if (!mode || !['testnet', 'live'].includes(mode)) {
      const response: TradingResponse = {
        success: false,
        message: 'Invalid trading mode. Must be "testnet" or "live"'
      };
      return res.status(400).json(response);
    }
    
    console.log(`🔄 Switching to ${mode.toUpperCase()} trading mode...`);
    
    const result = await executePythonScript('toggle_trading_mode.py', [mode]);
    
    const response: TradingResponse = {
      success: result.success || false,
      message: result.message || `Switched to ${mode} mode`,
      data: result
    };
    
    res.status(200).json(response);
  } catch (error) {
    console.error('Failed to toggle trading mode:', error);
    
    const response: TradingResponse = {
      success: false,
      message: `Failed to change trading mode: ${error.message}`
    };
    
    res.status(500).json(response);
  }
};

/**
 * Get live cryptocurrency prices
 */
export const getLivePrices: RequestHandler = async (req, res) => {
  try {
    const result = await executePythonScript('get_live_prices.py');
    
    const response: LivePricesResponse = {
      prices: result.prices || {},
      last_updated: new Date().toISOString()
    };
    
    res.status(200).json(response);
  } catch (error) {
    console.error('Failed to get live prices:', error);
    
    // Return default crypto prices if script fails
    const response: LivePricesResponse = {
      prices: {
        'BTCUSDT': 0,
        'ETHUSDT': 0,
        'BNBUSDT': 0,
        'ADAUSDT': 0,
        'SOLUSDT': 0,
        'XRPUSDT': 0,
        'DOTUSDT': 0,
        'DOGEUSDT': 0,
        'AVAXUSDT': 0,
        'LINKUSDT': 0
      },
      last_updated: new Date().toISOString()
    };
    
    res.status(200).json(response);
  }
};

/**
 * Force retrain AI model with latest data
 */
export const retrainModel: RequestHandler = async (req, res) => {
  try {
    console.log('🧠 Starting AI model retraining...');
    
    const result = await executePythonScript('retrain_model.py');
    
    const response: TradingResponse = {
      success: result.success || false,
      message: result.message || 'AI model retrained successfully',
      data: result
    };
    
    res.status(200).json(response);
  } catch (error) {
    console.error('Failed to retrain model:', error);
    
    const response: TradingResponse = {
      success: false,
      message: `Failed to retrain model: ${error.message}`
    };
    
    res.status(500).json(response);
  }
};

/**
 * Get comprehensive risk metrics
 */
export const getRiskMetrics: RequestHandler = async (req, res) => {
  try {
    const result = await executePythonScript('get_risk_metrics.py');
    
    res.status(200).json(result);
  } catch (error) {
    console.error('Failed to get risk metrics:', error);
    
    const response = {
      max_position_size: 0.05,
      stop_loss_percentage: 0.02,
      take_profit_percentage: 0.04,
      max_drawdown: 0.15,
      current_drawdown: 0.0,
      var_95: 0.0,
      risk_score: 0.0,
      active_positions: 0,
      max_concurrent_positions: 10
    };
    
    res.status(200).json(response);
  }
};

/**
 * Emergency stop all trading activities
 */
export const emergencyStop: RequestHandler = async (req, res) => {
  try {
    console.log('🚨 EMERGENCY STOP ACTIVATED');
    
    const result = await executePythonScript('emergency_stop.py');
    
    const response: TradingResponse = {
      success: true,
      message: 'Emergency stop executed - All trading halted',
      data: result
    };
    
    res.status(200).json(response);
  } catch (error) {
    console.error('Emergency stop failed:', error);
    
    const response: TradingResponse = {
      success: false,
      message: `Emergency stop failed: ${error.message}`
    };
    
    res.status(500).json(response);
  }
};
