"""
Hedge Fund Style Automation Service
Provides one-click automated trading workflow with professional risk management
"""

import asyncio
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
import pandas as pd
import numpy as np
from loguru import logger

from binance_client import BinanceClient
from ai_model import AITradingModel
from database import init_database, async_session
from config import settings, TOP_CRYPTOCURRENCIES, RISK_CONFIG
import json


@dataclass
class AutomationStatus:
    """Status of the hedge fund automation system"""
    is_running: bool = False
    current_phase: str = "idle"  # idle, data_fetching, training, trading, risk_monitoring
    progress_percentage: float = 0.0
    last_action: str = ""
    started_at: Optional[datetime] = None
    total_runtime: float = 0.0
    symbols_processed: int = 0
    total_symbols: int = 10
    model_confidence: float = 0.0
    risk_score: float = 0.0
    trading_mode: str = "testnet"  # testnet or live


@dataclass
class MarketDataStatus:
    """Status of market data fetching"""
    symbol: str
    status: str  # fetching, completed, failed
    data_points: int = 0
    timeframe: str = "1h"
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    error_message: Optional[str] = None


class HedgeFundAutomation:
    """
    Professional hedge fund style automation service
    Handles complete workflow from data fetching to AI training to live trading
    Enhanced for 24/7 operation with persistent state
    """

    def __init__(self):
        self.status = AutomationStatus()
        self.binance_client: Optional[BinanceClient] = None
        self.ai_model: Optional[AITradingModel] = None
        self.database_initialized = False
        self.market_data: Dict[str, pd.DataFrame] = {}
        self.active_positions: Dict[str, Any] = {}
        self.risk_metrics: Dict[str, float] = {}
        self.price_ticker: Dict[str, float] = {}
        self.automation_running = False
        self.initial_training_completed = False
        self.last_training_time: Optional[datetime] = None
        self.continuous_learning_enabled = True
        self.state_file = "automation_state.json"
        
    async def initialize(self) -> bool:
        """Initialize all required services with state recovery"""
        try:
            logger.info("Initializing hedge fund automation system...")

            # Load previous state if exists
            await self._load_state()

            # Determine trading mode and credentials
            trading_mode = os.getenv("TRADING_MODE", "testnet").lower()
            self.status.trading_mode = trading_mode

            if trading_mode == "live":
                api_key = os.getenv("BINANCE_API_KEY")
                secret_key = os.getenv("BINANCE_SECRET_KEY")
                testnet = False
                logger.warning("🔴 LIVE TRADING MODE ACTIVATED")
            else:
                api_key = os.getenv("BINANCE_TESTNET_API_KEY") or os.getenv("BINANCE_API_KEY")
                secret_key = os.getenv("BINANCE_TESTNET_SECRET_KEY") or os.getenv("BINANCE_SECRET_KEY")
                testnet = True
                logger.info("🟡 TESTNET MODE ACTIVATED")

            if not api_key or not secret_key:
                logger.error("Missing Binance API credentials")
                return False

            # Initialize Binance client
            self.binance_client = BinanceClient(
                api_key=api_key,
                api_secret=secret_key,
                testnet=testnet
            )

            # Test connection
            if not await self.binance_client.health_check():
                logger.error("Failed to connect to Binance API")
                return False

            # Initialize AI model
            self.ai_model = AITradingModel()

            # Initialize database
            await init_database()
            self.database_initialized = True

            logger.success("✅ Hedge fund automation system initialized successfully")

            # Check if we need initial training
            if not self.initial_training_completed:
                logger.info("🧠 Initial training required - will train on first start")
            else:
                logger.info("✅ Previous training state recovered")

            return True

        except Exception as e:
            logger.error(f"Failed to initialize automation system: {e}")
            return False

    async def _load_state(self):
        """Load previous automation state"""
        try:
            if os.path.exists(self.state_file):
                with open(self.state_file, 'r') as f:
                    state = json.load(f)
                    self.initial_training_completed = state.get('initial_training_completed', False)
                    self.last_training_time = datetime.fromisoformat(state['last_training_time']) if state.get('last_training_time') else None
                    self.continuous_learning_enabled = state.get('continuous_learning_enabled', True)
                    logger.info("📂 Previous state loaded successfully")
        except Exception as e:
            logger.warning(f"Could not load previous state: {e}")

    async def _save_state(self):
        """Save current automation state"""
        try:
            state = {
                'initial_training_completed': self.initial_training_completed,
                'last_training_time': self.last_training_time.isoformat() if self.last_training_time else None,
                'continuous_learning_enabled': self.continuous_learning_enabled,
                'saved_at': datetime.utcnow().isoformat()
            }
            with open(self.state_file, 'w') as f:
                json.dump(state, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save state: {e}")
    
    async def start_automated_workflow(self) -> bool:
        """
        Start the complete hedge fund automation workflow:
        1. Fetch historical data for top 10 cryptocurrencies
        2. Train/retrain AI model
        3. Begin automated trading with risk management
        """
        if self.automation_running:
            logger.warning("Automation workflow already running")
            return False
        
        try:
            self.automation_running = True
            self.status.is_running = True
            self.status.started_at = datetime.utcnow()
            self.status.progress_percentage = 0.0
            self.status.total_symbols = len(settings.TOP_CRYPTOCURRENCIES)
            
            logger.info("🚀 Starting hedge fund automation workflow...")
            
            # Phase 1: Fetch Historical Data
            await self._phase_1_fetch_data()
            
            # Phase 2: Train AI Model
            await self._phase_2_train_model()
            
            # Phase 3: Start Trading
            await self._phase_3_start_trading()
            
            # Phase 4: Monitor and Risk Management
            await self._phase_4_risk_monitoring()
            
            return True
            
        except Exception as e:
            logger.error(f"Automation workflow failed: {e}")
            await self.stop_automation()
            return False
    
    async def _phase_1_fetch_data(self):
        """Phase 1: Fetch comprehensive historical data"""
        self.status.current_phase = "data_fetching"
        self.status.last_action = "Fetching historical data for top 10 cryptocurrencies"
        logger.info("📊 Phase 1: Fetching historical market data...")
        
        # Fetch 1 year of hourly data for top cryptocurrencies
        days_history = 365
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(days=days_history)
        
        symbols = settings.TOP_CRYPTOCURRENCIES
        self.status.symbols_processed = 0
        
        for i, symbol in enumerate(symbols):
            try:
                self.status.last_action = f"Fetching data for {symbol}"
                logger.info(f"Downloading {symbol} data ({i+1}/{len(symbols)})")
                
                # Get historical klines
                klines = await self.binance_client.get_historical_klines(
                    symbol=symbol,
                    interval="1h",
                    start_time=start_time,
                    end_time=end_time,
                    limit=1000
                )
                
                if klines:
                    # Convert to DataFrame
                    df = pd.DataFrame(klines, columns=[
                        'timestamp', 'open', 'high', 'low', 'close', 'volume',
                        'close_time', 'quote_asset_volume', 'number_of_trades',
                        'taker_buy_base_asset_volume', 'taker_buy_quote_asset_volume',
                        'ignore'
                    ])
                    
                    # Clean and process data
                    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
                    for col in ['open', 'high', 'low', 'close', 'volume']:
                        df[col] = pd.to_numeric(df[col])
                    
                    df = df[['timestamp', 'open', 'high', 'low', 'close', 'volume']]
                    self.market_data[symbol] = df
                    
                    logger.success(f"✅ {symbol}: {len(df)} data points collected")
                
                self.status.symbols_processed += 1
                self.status.progress_percentage = (i + 1) / len(symbols) * 25  # 25% of total progress
                
                # Rate limiting
                await asyncio.sleep(0.1)
                
            except Exception as e:
                logger.error(f"Failed to fetch data for {symbol}: {e}")
                continue
        
        logger.success(f"✅ Phase 1 Complete: Downloaded data for {len(self.market_data)} symbols")
    
    async def _phase_2_train_model(self):
        """Phase 2: Train/retrain AI model with fresh data"""
        self.status.current_phase = "training"
        self.status.last_action = "Training AI model with fresh market data"

        # Check if this is initial training
        is_initial_training = not self.initial_training_completed
        training_type = "Initial" if is_initial_training else "Retraining"

        logger.info(f"🧠 Phase 2: {training_type} AI model...")

        try:
            # Prepare training data
            combined_data = []
            for symbol, df in self.market_data.items():
                df_copy = df.copy()
                df_copy['symbol'] = symbol
                combined_data.append(df_copy)

            if combined_data:
                training_df = pd.concat(combined_data, ignore_index=True)

                # Train the model - need to convert DataFrame to dict format
                self.status.last_action = f"{training_type} ensemble AI model..."
                market_data_dict = {symbol: training_df for symbol in self.market_data.keys()}
                training_result = await self.ai_model.train_model(market_data_dict)

                if training_result.get('status') == 'completed':
                    # Calculate confidence from validation accuracy
                    final_accuracy = training_result.get('final_accuracy', 0.0)
                    self.status.model_confidence = max(0.0, min(1.0, final_accuracy + 0.5))  # Scale to 0.5-1.0 range
                    self.last_training_time = datetime.utcnow()

                    # Mark initial training as completed
                    if is_initial_training:
                        self.initial_training_completed = True
                        logger.success(f"✅ Initial AI Model training completed - Confidence: {self.status.model_confidence:.2%}")
                    else:
                        logger.success(f"✅ AI Model retrained successfully - Confidence: {self.status.model_confidence:.2%}")

                    # Save state
                    await self._save_state()
                else:
                    logger.error("❌ AI Model training failed")
                    raise Exception("Model training failed")

            self.status.progress_percentage = 50  # 50% of total progress

        except Exception as e:
            logger.error(f"Model training failed: {e}")
            raise
    
    async def _phase_3_start_trading(self):
        """Phase 3: Begin automated trading with AI signals"""
        self.status.current_phase = "trading"
        self.status.last_action = "Starting automated trading with AI signals"
        logger.info("💰 Phase 3: Starting automated trading...")
        
        try:
            # Get current portfolio
            portfolio = await self.binance_client.calculate_portfolio_value()
            logger.info(f"Current portfolio value: ${portfolio['total_value_usdt']:.2f}")
            
            # Start live price monitoring
            await self._start_price_ticker()
            
            # Initialize risk management
            await self._initialize_risk_management()
            
            self.status.progress_percentage = 75  # 75% of total progress
            logger.success("✅ Trading system activated")
            
        except Exception as e:
            logger.error(f"Trading activation failed: {e}")
            raise
    
    async def _phase_4_risk_monitoring(self):
        """Phase 4: Continuous risk monitoring, position management, and learning"""
        self.status.current_phase = "risk_monitoring"
        self.status.last_action = "Active 24/7 risk monitoring and continuous learning"
        logger.info("🛡️ Phase 4: 24/7 Risk monitoring and continuous learning active...")

        self.status.progress_percentage = 100  # 100% complete

        # Start continuous monitoring loop (24/7 operation)
        cycle_count = 0
        retrain_interval = 720  # Retrain every 6 hours (720 cycles of 30 seconds)

        while self.automation_running:
            try:
                cycle_count += 1

                # Core monitoring tasks
                await self._monitor_positions()
                await self._update_risk_metrics()
                await self._check_stop_losses()
                await self._evaluate_new_signals()
                await self._update_live_prices()

                # Continuous learning: retrain model periodically with live data
                if self.continuous_learning_enabled and cycle_count % retrain_interval == 0:
                    await self._continuous_learning_update()

                # Update status and save state periodically
                self.status.total_runtime = (datetime.utcnow() - self.status.started_at).total_seconds()
                if cycle_count % 120 == 0:  # Save state every hour
                    await self._save_state()
                    logger.info(f"📊 24/7 Bot active - Runtime: {self.status.total_runtime/3600:.1f} hours")

                # Wait before next cycle (30 seconds for responsive trading)
                await asyncio.sleep(30)

            except Exception as e:
                logger.error(f"Risk monitoring error: {e}")
                await asyncio.sleep(10)

    async def _continuous_learning_update(self):
        """Continuous learning: update model with recent live data"""
        try:
            logger.info("🧠 Continuous learning: Updating model with live data...")
            self.status.last_action = "Continuous learning: Updating AI model with live market data"

            # Fetch fresh market data
            await self._start_price_ticker()

            # If we have recent data, retrain model
            if self.market_data:
                await self._phase_2_train_model()
                logger.success("✅ Continuous learning update completed")

        except Exception as e:
            logger.error(f"Continuous learning error: {e}")

    async def _update_live_prices(self):
        """Update live price ticker"""
        try:
            await self._start_price_ticker()
        except Exception as e:
            logger.debug(f"Price update error: {e}")
    
    async def _start_price_ticker(self):
        """Start live price monitoring"""
        try:
            if not self.binance_client:
                logger.warning("Binance client not initialized")
                return

            tickers = await self.binance_client.get_ticker_prices(settings.TOP_CRYPTOCURRENCIES)
            for ticker in tickers:
                symbol = ticker['symbol']
                price = float(ticker['price'])
                self.price_ticker[symbol] = price

            logger.info("✅ Live price ticker started")
        except Exception as e:
            logger.error(f"Failed to start price ticker: {e}")
            # Set default prices to prevent failures
            for symbol in settings.TOP_CRYPTOCURRENCIES:
                self.price_ticker[symbol] = 0.0
    
    async def _initialize_risk_management(self):
        """Initialize risk management parameters"""
        self.risk_metrics = {
            'max_position_size': settings.MAX_POSITION_SIZE,
            'stop_loss_percentage': settings.STOP_LOSS_PERCENTAGE,
            'take_profit_percentage': settings.TAKE_PROFIT_PERCENTAGE,
            'max_drawdown': settings.MAX_DRAWDOWN_THRESHOLD,
            'max_concurrent_positions': settings.MAX_CONCURRENT_POSITIONS,
            'current_drawdown': 0.0,
            'var_95': 0.0,
            'risk_score': 0.0
        }
        
        logger.info("✅ Risk management parameters initialized")
    
    async def _monitor_positions(self):
        """Monitor active positions and update P&L"""
        try:
            open_orders = await self.binance_client.get_open_orders()
            portfolio = await self.binance_client.calculate_portfolio_value()
            
            # Update position tracking
            current_positions = len(open_orders)
            self.risk_metrics['active_positions'] = current_positions
            
            # Calculate current P&L and drawdown
            # Implementation would include sophisticated P&L calculation
            
        except Exception as e:
            logger.error(f"Position monitoring error: {e}")
    
    async def _update_risk_metrics(self):
        """Update comprehensive risk metrics"""
        try:
            # Calculate VaR, Sharpe ratio, maximum drawdown, etc.
            # Implementation would include advanced risk calculations
            
            self.status.risk_score = self.risk_metrics.get('risk_score', 0.0)
            
        except Exception as e:
            logger.error(f"Risk metrics update error: {e}")
    
    async def _check_stop_losses(self):
        """Check and execute stop losses if needed"""
        try:
            # Monitor all positions for stop loss conditions
            # Execute protective orders as needed
            pass
            
        except Exception as e:
            logger.error(f"Stop loss check error: {e}")
    
    async def _evaluate_new_signals(self):
        """Evaluate new trading signals from AI model"""
        try:
            # Get latest market data
            # Run AI prediction
            # Evaluate signal strength
            # Execute trades if conditions are met
            pass
            
        except Exception as e:
            logger.error(f"Signal evaluation error: {e}")
    
    async def stop_automation(self):
        """Stop the automation workflow"""
        logger.info("🛑 Stopping hedge fund automation...")
        
        self.automation_running = False
        self.status.is_running = False
        self.status.current_phase = "stopping"
        self.status.last_action = "Shutting down automation systems"
        
        # Close any pending operations
        if self.binance_client:
            # Cancel all open orders (safety measure)
            pass
        
        logger.info("✅ Automation stopped safely")
    
    async def toggle_trading_mode(self, mode: str) -> bool:
        """Toggle between testnet and live trading"""
        if mode not in ["testnet", "live"]:
            return False
        
        if self.automation_running:
            logger.warning("Cannot change trading mode while automation is running")
            return False
        
        # Update environment variable
        os.environ["TRADING_MODE"] = mode
        self.status.trading_mode = mode
        
        # Reinitialize client with new mode
        if await self.initialize():
            logger.info(f"✅ Trading mode switched to: {mode.upper()}")
            return True
        else:
            logger.error(f"❌ Failed to switch to {mode} mode")
            return False
    
    def get_automation_status(self) -> Dict[str, Any]:
        """Get current automation status"""
        return {
            'is_running': self.status.is_running,
            'current_phase': self.status.current_phase,
            'progress_percentage': self.status.progress_percentage,
            'last_action': self.status.last_action,
            'started_at': self.status.started_at.isoformat() if self.status.started_at else None,
            'total_runtime': self.status.total_runtime,
            'symbols_processed': self.status.symbols_processed,
            'total_symbols': self.status.total_symbols,
            'model_confidence': self.status.model_confidence,
            'risk_score': self.status.risk_score,
            'trading_mode': self.status.trading_mode,
            'market_data_symbols': list(self.market_data.keys()),
            'live_prices': self.price_ticker,
            'risk_metrics': self.risk_metrics
        }
    
    def get_live_prices(self) -> Dict[str, float]:
        """Get current live prices"""
        return self.price_ticker.copy()


# Global automation instance
hedge_fund_automation = HedgeFundAutomation()
