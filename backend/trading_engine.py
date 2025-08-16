import asyncio
import json
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from loguru import logger
import uuid
from concurrent.futures import ThreadPoolExecutor

from config import settings, RISK_CONFIG, AI_MODEL_CONFIG
from database import async_session, Trade, BotStatus, PerformanceMetrics, TradingSignal, RiskMetrics
from binance_client import BinanceClient
from ai_model import AITradingModel
from websocket_manager import WebSocketManager
from analysis.technical_analysis import TechnicalAnalysisEngine
from analysis.hidden_gems import HiddenGemsDetector

class TradingEngine:
    """
    Professional hedge fund-grade trading engine with comprehensive risk management,
    AI-driven decision making, and real-time portfolio optimization.
    """
    
    def __init__(self, binance_client: BinanceClient, ai_model: AITradingModel, 
                 redis_client=None, websocket_manager: WebSocketManager = None):
        self.binance_client = binance_client
        self.ai_model = ai_model
        self.redis_client = redis_client
        self.websocket_manager = websocket_manager
        
        # Core trading state
        self.is_running = False
        self.is_live_trading = False
        self.current_capital = settings.DEFAULT_CAPITAL
        self.max_drawdown_reached = 0.0
        self.daily_pnl = 0.0
        self.total_pnl = 0.0
        
        # Risk management
        self.risk_metrics = {
            'var_95': 0.0,
            'sharpe_ratio': 0.0,
            'max_drawdown': 0.0,
            'volatility': 0.0,
            'beta': 0.0,
            'alpha': 0.0
        }
        
        # Trading statistics
        self.stats = {
            'total_trades': 0,
            'winning_trades': 0,
            'losing_trades': 0,
            'win_rate': 0.0,
            'avg_profit': 0.0,
            'avg_loss': 0.0,
            'profit_factor': 0.0,
            'active_positions': 0,
            'max_concurrent_positions': 0
        }
        
        # Portfolio tracking
        self.positions = {}  # symbol -> position_info
        self.open_orders = {}  # order_id -> order_info
        self.trade_history = []
        self.market_data = {}
        
        # AI and analysis engines
        self.technical_analyzer = TechnicalAnalysisEngine()
        self.gems_detector = HiddenGemsDetector()
        
        # Background tasks
        self.background_tasks = []
        self.executor = ThreadPoolExecutor(max_workers=settings.MAX_WORKERS)
        
        # Performance tracking
        self.performance_history = []
        self.last_model_update = None
        self.last_risk_check = datetime.utcnow()
        
        logger.info("Trading engine initialized with hedge fund-grade features")
    
    async def start(self) -> Dict[str, Any]:
        """Start the trading engine with full automation sequence"""
        try:
            if self.is_running:
                return {"success": False, "message": "Trading engine already running"}
            
            logger.info("🚀 Starting hedge fund automation sequence")
            await self._broadcast_status("Starting hedge fund automation...")
            
            # Phase 1: Initialize and validate
            await self._broadcast_status("Initializing systems...", phase="initialization")
            await self._initialize_systems()
            
            # Phase 2: Download historical data
            await self._broadcast_status("Downloading market data...", phase="data_fetching", progress=10)
            market_data = await self._download_comprehensive_data()
            
            # Phase 3: Train AI models
            await self._broadcast_status("Training AI models...", phase="training", progress=40)
            await self._train_ai_models(market_data)
            
            # Phase 4: Start real-time trading
            await self._broadcast_status("Starting real-time trading...", phase="trading", progress=80)
            await self._start_trading_loop()
            
            # Phase 5: Risk monitoring
            await self._broadcast_status("Hedge fund automation active", phase="risk_monitoring", progress=100)
            await self._start_risk_monitoring()
            
            self.is_running = True
            
            result = {
                "success": True,
                "message": "Hedge fund automation started successfully",
                "data_points": sum(len(df) for df in market_data.values()) if market_data else 0,
                "symbols_analyzed": len(market_data) if market_data else 0,
                "ai_confidence": "High" if self.ai_model else "Medium"
            }
            
            await self._save_bot_status()
            logger.info("🎯 Hedge fund automation fully operational")
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to start trading engine: {e}")
            await self._broadcast_status(f"Startup failed: {str(e)}", phase="error")
            raise
    
    async def stop(self) -> Dict[str, Any]:
        """Stop the trading engine gracefully"""
        try:
            if not self.is_running:
                return {"success": False, "message": "Trading engine not running"}
            
            logger.info("🛑 Stopping hedge fund automation")
            await self._broadcast_status("Stopping automation...", phase="shutdown")
            
            # Cancel all background tasks
            for task in self.background_tasks:
                if not task.done():
                    task.cancel()
            
            # Close all open positions
            await self._close_all_positions("Emergency shutdown")
            
            # Cancel all open orders
            await self._cancel_all_orders()
            
            self.is_running = False
            await self._save_bot_status()
            
            logger.info("✅ Trading engine stopped successfully")
            return {"success": True, "message": "Trading engine stopped successfully"}
            
        except Exception as e:
            logger.error(f"Error stopping trading engine: {e}")
            raise
    
    async def switch_to_live(self) -> Dict[str, Any]:
        """Switch from testnet to live trading"""
        try:
            if self.is_live_trading:
                return {"success": False, "message": "Already in live trading mode"}
            
            logger.warning("🔴 SWITCHING TO LIVE TRADING MODE!")
            
            # Switch Binance client to live
            await self.binance_client.switch_to_live_mode()
            
            self.is_live_trading = True
            await self._save_bot_status()
            
            await self._broadcast_status("Switched to LIVE trading mode", phase="live_trading")
            
            return {"success": True, "message": "Switched to live trading mode"}
            
        except Exception as e:
            logger.error(f"Failed to switch to live trading: {e}")
            raise
    
    async def add_capital(self, amount: float) -> float:
        """Add or remove capital from the trading account"""
        try:
            if amount == 0:
                return self.current_capital
            
            self.current_capital += amount
            
            # Ensure capital doesn't go negative
            self.current_capital = max(self.current_capital, 0)
            
            await self._save_bot_status()
            
            action = "added" if amount > 0 else "removed"
            logger.info(f"Capital {action}: {abs(amount)}, New total: {self.current_capital}")
            
            await self._broadcast_status(f"Capital {action}: {abs(amount)}")
            
            return self.current_capital
            
        except Exception as e:
            logger.error(f"Failed to modify capital: {e}")
            raise
    
    async def _initialize_systems(self):
        """Initialize all trading systems"""
        try:
            # Connect to Binance
            if not self.binance_client.is_connected:
                await self.binance_client.connect()
            
            # Update account info
            await self.binance_client.update_account_info()
            
            # Initialize technical analyzer
            await self.technical_analyzer.initialize()
            
            # Initialize gems detector
            await self.gems_detector.initialize()
            
            # Load bot state from database
            await self._load_bot_state()
            
            logger.info("All systems initialized successfully")
            
        except Exception as e:
            logger.error(f"System initialization failed: {e}")
            raise
    
    async def _download_comprehensive_data(self) -> Dict[str, pd.DataFrame]:
        """Download comprehensive historical data for AI training"""
        try:
            # Download data for top cryptocurrencies
            market_data = await self.binance_client.download_all_historical_data(
                symbols=settings.TOP_CRYPTOCURRENCIES,
                days=settings.TRAINING_DATA_DAYS,
                interval=settings.MARKET_DATA_INTERVAL
            )
            
            # Discover and analyze hidden gems
            await self._broadcast_status("Discovering hidden gems...", progress=30)
            hidden_gems = await self.gems_detector.discover_gems()
            
            # Download data for promising hidden gems
            if hidden_gems:
                gem_symbols = [gem['symbol'] for gem in hidden_gems[:5]]  # Top 5 gems
                gem_data = await self.binance_client.download_all_historical_data(
                    symbols=gem_symbols,
                    days=settings.TRAINING_DATA_DAYS // 2,  # Less history for gems
                    interval=settings.MARKET_DATA_INTERVAL
                )
                market_data.update(gem_data)
            
            # Store in Redis cache if available
            if self.redis_client:
                await self._cache_market_data(market_data)
            
            logger.info(f"Downloaded data for {len(market_data)} symbols")
            return market_data
            
        except Exception as e:
            logger.error(f"Data download failed: {e}")
            return {}
    
    async def _train_ai_models(self, market_data: Dict[str, pd.DataFrame]):
        """Train AI models with downloaded data"""
        try:
            if not market_data:
                logger.warning("No market data available for training")
                return
            
            # Train the main AI model
            training_result = await self.ai_model.train_model(market_data)
            
            # Update last training time
            self.last_model_update = datetime.utcnow()
            
            logger.info(f"AI training completed: {training_result}")
            
        except Exception as e:
            logger.error(f"AI training failed: {e}")
            # Continue without AI if training fails
            pass
    
    async def _start_trading_loop(self):
        """Start the main trading loop"""
        try:
            # Create background tasks
            self.background_tasks = [
                asyncio.create_task(self._market_data_loop()),
                asyncio.create_task(self._trading_decision_loop()),
                asyncio.create_task(self._position_management_loop()),
                asyncio.create_task(self._performance_tracking_loop())
            ]
            
            logger.info("Trading loops started")
            
        except Exception as e:
            logger.error(f"Failed to start trading loops: {e}")
            raise
    
    async def _start_risk_monitoring(self):
        """Start risk monitoring systems"""
        try:
            # Add risk monitoring task
            self.background_tasks.append(
                asyncio.create_task(self._risk_monitoring_loop())
            )
            
            logger.info("Risk monitoring started")
            
        except Exception as e:
            logger.error(f"Failed to start risk monitoring: {e}")
            pass
    
    async def _market_data_loop(self):
        """Continuously update market data"""
        while self.is_running:
            try:
                # Get latest prices for all symbols
                symbols = list(set(settings.TOP_CRYPTOCURRENCIES + list(self.positions.keys())))
                
                ticker_data = await self.binance_client.get_24hr_ticker(symbols)
                
                # Update market data
                for ticker in ticker_data:
                    symbol = ticker['symbol']
                    self.market_data[symbol] = {
                        'price': float(ticker['lastPrice']),
                        'volume': float(ticker['volume']),
                        'change_24h': float(ticker['priceChangePercent']),
                        'high_24h': float(ticker['highPrice']),
                        'low_24h': float(ticker['lowPrice']),
                        'timestamp': datetime.utcnow()
                    }
                
                # Broadcast market data
                await self._broadcast_market_data()
                
                # Wait before next update
                await asyncio.sleep(settings.DATA_UPDATE_FREQUENCY)
                
            except Exception as e:
                logger.error(f"Market data loop error: {e}")
                await asyncio.sleep(30)
    
    async def _trading_decision_loop(self):
        """Main trading decision loop"""
        while self.is_running:
            try:
                # Check if we should make trading decisions
                if not self._should_trade():
                    await asyncio.sleep(60)
                    continue
                
                # Get AI predictions for all symbols
                predictions = await self._get_ai_predictions()
                
                # Analyze each prediction
                for symbol, prediction in predictions.items():
                    await self._process_trading_signal(symbol, prediction)
                
                # Wait before next decision cycle
                await asyncio.sleep(30)  # 30 second decision cycle
                
            except Exception as e:
                logger.error(f"Trading decision loop error: {e}")
                await asyncio.sleep(60)
    
    async def _position_management_loop(self):
        """Manage open positions"""
        while self.is_running:
            try:
                # Check each open position
                for symbol, position in list(self.positions.items()):
                    await self._manage_position(symbol, position)
                
                # Update position statistics
                self.stats['active_positions'] = len(self.positions)
                self.stats['max_concurrent_positions'] = max(
                    self.stats['max_concurrent_positions'],
                    self.stats['active_positions']
                )
                
                await asyncio.sleep(10)  # Check positions every 10 seconds
                
            except Exception as e:
                logger.error(f"Position management loop error: {e}")
                await asyncio.sleep(30)
    
    async def _performance_tracking_loop(self):
        """Track and broadcast performance metrics"""
        while self.is_running:
            try:
                # Calculate current performance
                await self._calculate_performance_metrics()
                
                # Save to database
                await self._save_performance_metrics()
                
                # Broadcast to clients
                await self._broadcast_performance_update()
                
                await asyncio.sleep(60)  # Update every minute
                
            except Exception as e:
                logger.error(f"Performance tracking loop error: {e}")
                await asyncio.sleep(120)
    
    async def _risk_monitoring_loop(self):
        """Monitor risk metrics and enforce limits"""
        while self.is_running:
            try:
                # Calculate current risk metrics
                await self._calculate_risk_metrics()
                
                # Check risk limits
                await self._enforce_risk_limits()
                
                # Update last check time
                self.last_risk_check = datetime.utcnow()
                
                await asyncio.sleep(30)  # Check risk every 30 seconds
                
            except Exception as e:
                logger.error(f"Risk monitoring loop error: {e}")
                await asyncio.sleep(60)
    
    async def _get_ai_predictions(self) -> Dict[str, Dict[str, Any]]:
        """Get AI predictions for trading decisions"""
        try:
            if not self.ai_model:
                return {}
            
            # Prepare recent market data for prediction
            prediction_data = {}
            
            for symbol in settings.TOP_CRYPTOCURRENCIES:
                if symbol in self.market_data:
                    # Get recent klines for analysis
                    df = await self.binance_client.get_historical_klines(
                        symbol=symbol,
                        interval='1h',
                        limit=100
                    )
                    
                    if not df.empty:
                        prediction_data[symbol] = df
            
            # Get predictions from AI model
            predictions = await self.ai_model.predict(prediction_data)
            
            return predictions
            
        except Exception as e:
            logger.error(f"Error getting AI predictions: {e}")
            return {}
    
    async def _process_trading_signal(self, symbol: str, prediction: Dict[str, Any]):
        """Process a trading signal and execute if conditions are met"""
        try:
            if symbol not in self.market_data:
                return
            
            current_price = self.market_data[symbol]['price']
            confidence = prediction.get('confidence', 0)
            predicted_direction = prediction.get('ensemble_prediction', 0)
            risk_score = prediction.get('risk_score', 1.0)
            
            # Check minimum confidence threshold
            if confidence < settings.PREDICTION_CONFIDENCE_THRESHOLD:
                return
            
            # Determine trade direction
            if predicted_direction > 0.01:  # 1% upward prediction
                side = 'BUY'
            elif predicted_direction < -0.01:  # 1% downward prediction
                side = 'SELL'
            else:
                return  # No clear signal
            
            # Check if we already have a position in this symbol
            if symbol in self.positions:
                # Consider adjusting existing position
                await self._consider_position_adjustment(symbol, prediction)
                return
            
            # Calculate position size
            position_size = await self._calculate_position_size(
                symbol, confidence, risk_score, current_price
            )
            
            if position_size <= 0:
                return
            
            # Execute the trade
            await self._execute_trade(symbol, side, position_size, current_price, prediction)
            
        except Exception as e:
            logger.error(f"Error processing trading signal for {symbol}: {e}")
    
    async def _calculate_position_size(self, symbol: str, confidence: float, 
                                     risk_score: float, price: float) -> float:
        """Calculate optimal position size using Kelly Criterion and risk management"""
        try:
            # Base position size as percentage of capital
            base_position_pct = RISK_CONFIG['position_sizing']['max_risk_per_trade']
            
            # Adjust for confidence
            confidence_multiplier = RISK_CONFIG['position_sizing']['confidence_multiplier']
            adjusted_position_pct = base_position_pct * (1 + (confidence - 0.5) * confidence_multiplier)
            
            # Adjust for risk score (lower risk score = larger position)
            risk_adjustment = 1 - (risk_score * 0.5)
            adjusted_position_pct *= risk_adjustment
            
            # Calculate maximum allowed position size
            max_position_value = self.current_capital * settings.MAX_POSITION_SIZE
            confidence_position_value = self.current_capital * adjusted_position_pct
            
            # Use the smaller of the two
            position_value = min(max_position_value, confidence_position_value)
            
            # Convert to quantity
            quantity = position_value / price
            
            # Apply minimum trade size constraints
            pair_config = self.binance_client.get_pair_config(symbol)
            if hasattr(pair_config, 'min_quantity'):
                quantity = max(quantity, pair_config['min_quantity'])
            
            return quantity
            
        except Exception as e:
            logger.error(f"Error calculating position size: {e}")
            return 0.0
    
    async def _execute_trade(self, symbol: str, side: str, quantity: float, 
                           price: float, prediction: Dict[str, Any]):
        """Execute a trade with comprehensive error handling and logging"""
        try:
            # Create trade record
            trade_id = str(uuid.uuid4())
            
            # Place the order
            if self.is_live_trading:
                order = await self.binance_client.place_market_order(
                    symbol=symbol,
                    side=side,
                    quantity=quantity,
                    test_order=False
                )
                order_id = order.get('orderId')
                actual_price = float(order.get('fills', [{}])[0].get('price', price))
            else:
                # Testnet or paper trading
                order = await self.binance_client.place_market_order(
                    symbol=symbol,
                    side=side,
                    quantity=quantity,
                    test_order=True
                )
                order_id = f"test_{trade_id}"
                actual_price = price
            
            # Calculate stop loss and take profit
            stop_loss = self._calculate_stop_loss(actual_price, side)
            take_profit = self._calculate_take_profit(actual_price, side)
            
            # Create position record
            position = {
                'id': trade_id,
                'symbol': symbol,
                'side': side,
                'quantity': quantity,
                'entry_price': actual_price,
                'current_price': actual_price,
                'stop_loss': stop_loss,
                'take_profit': take_profit,
                'timestamp': datetime.utcnow(),
                'order_id': order_id,
                'prediction': prediction,
                'unrealized_pnl': 0.0,
                'status': 'OPEN'
            }
            
            # Add to positions
            self.positions[symbol] = position
            
            # Update statistics
            self.stats['total_trades'] += 1
            
            # Save to database
            await self._save_trade_to_db(position)
            
            # Broadcast trade update
            await self._broadcast_trade_update(position)
            
            logger.info(f"✅ Trade executed: {side} {quantity:.6f} {symbol} @ {actual_price:.2f}")
            
        except Exception as e:
            logger.error(f"Trade execution failed: {e}")
            raise
    
    async def _manage_position(self, symbol: str, position: Dict[str, Any]):
        """Manage an open position with stop-loss, take-profit, and trailing stops"""
        try:
            if symbol not in self.market_data:
                return
            
            current_price = self.market_data[symbol]['price']
            entry_price = position['entry_price']
            side = position['side']
            
            # Update current price
            position['current_price'] = current_price
            
            # Calculate unrealized P&L
            if side == 'BUY':
                pnl = (current_price - entry_price) * position['quantity']
                pnl_pct = (current_price - entry_price) / entry_price
            else:  # SELL
                pnl = (entry_price - current_price) * position['quantity']
                pnl_pct = (entry_price - current_price) / entry_price
            
            position['unrealized_pnl'] = pnl
            
            # Check exit conditions
            should_close = False
            close_reason = ""
            
            # Stop loss check
            if ((side == 'BUY' and current_price <= position['stop_loss']) or
                (side == 'SELL' and current_price >= position['stop_loss'])):
                should_close = True
                close_reason = "Stop Loss"
            
            # Take profit check
            elif ((side == 'BUY' and current_price >= position['take_profit']) or
                  (side == 'SELL' and current_price <= position['take_profit'])):
                should_close = True
                close_reason = "Take Profit"
            
            # Time-based exit (24 hours max)
            elif datetime.utcnow() - position['timestamp'] > timedelta(hours=24):
                should_close = True
                close_reason = "Time Limit"
            
            # Risk-based exit (if risk has increased significantly)
            elif abs(pnl_pct) > 0.1:  # 10% move
                should_close = True
                close_reason = "Risk Management"
            
            if should_close:
                await self._close_position(symbol, position, close_reason)
            else:
                # Update trailing stop if profitable
                await self._update_trailing_stop(symbol, position)
            
        except Exception as e:
            logger.error(f"Error managing position for {symbol}: {e}")
    
    async def _close_position(self, symbol: str, position: Dict[str, Any], reason: str):
        """Close a position and record the trade"""
        try:
            current_price = self.market_data[symbol]['price']
            
            # Calculate final P&L
            if position['side'] == 'BUY':
                pnl = (current_price - position['entry_price']) * position['quantity']
            else:
                pnl = (position['entry_price'] - current_price) * position['quantity']
            
            # Update position record
            position['exit_price'] = current_price
            position['realized_pnl'] = pnl
            position['status'] = 'CLOSED'
            position['close_reason'] = reason
            position['close_timestamp'] = datetime.utcnow()
            
            # Update statistics
            if pnl > 0:
                self.stats['winning_trades'] += 1
                self.stats['avg_profit'] = (
                    (self.stats['avg_profit'] * (self.stats['winning_trades'] - 1) + pnl) /
                    self.stats['winning_trades']
                )
            else:
                self.stats['losing_trades'] += 1
                self.stats['avg_loss'] = (
                    (self.stats['avg_loss'] * (self.stats['losing_trades'] - 1) + abs(pnl)) /
                    self.stats['losing_trades']
                )
            
            # Update win rate
            total_closed_trades = self.stats['winning_trades'] + self.stats['losing_trades']
            self.stats['win_rate'] = (self.stats['winning_trades'] / total_closed_trades * 100) if total_closed_trades > 0 else 0
            
            # Update P&L
            self.total_pnl += pnl
            self.daily_pnl += pnl
            
            # Remove from active positions
            del self.positions[symbol]
            
            # Add to trade history
            self.trade_history.append(position)
            
            # Save to database
            await self._update_trade_in_db(position)
            
            # Broadcast trade update
            await self._broadcast_trade_update(position)
            
            logger.info(f"🔒 Position closed: {symbol} - {reason} - P&L: {pnl:.2f}")
            
        except Exception as e:
            logger.error(f"Error closing position for {symbol}: {e}")
    
    def _calculate_stop_loss(self, price: float, side: str) -> float:
        """Calculate stop loss price"""
        stop_loss_pct = settings.STOP_LOSS_PERCENTAGE
        
        if side == 'BUY':
            return price * (1 - stop_loss_pct)
        else:
            return price * (1 + stop_loss_pct)
    
    def _calculate_take_profit(self, price: float, side: str) -> float:
        """Calculate take profit price"""
        take_profit_pct = settings.TAKE_PROFIT_PERCENTAGE
        
        if side == 'BUY':
            return price * (1 + take_profit_pct)
        else:
            return price * (1 - take_profit_pct)
    
    async def _update_trailing_stop(self, symbol: str, position: Dict[str, Any]):
        """Update trailing stop loss for profitable positions"""
        try:
            current_price = position['current_price']
            entry_price = position['entry_price']
            side = position['side']
            
            # Only update if position is profitable
            if side == 'BUY' and current_price > entry_price:
                # Update stop loss to lock in profits
                new_stop_loss = current_price * (1 - settings.STOP_LOSS_PERCENTAGE)
                if new_stop_loss > position['stop_loss']:
                    position['stop_loss'] = new_stop_loss
            
            elif side == 'SELL' and current_price < entry_price:
                # Update stop loss to lock in profits
                new_stop_loss = current_price * (1 + settings.STOP_LOSS_PERCENTAGE)
                if new_stop_loss < position['stop_loss']:
                    position['stop_loss'] = new_stop_loss
            
        except Exception as e:
            logger.error(f"Error updating trailing stop for {symbol}: {e}")
    
    def _should_trade(self) -> bool:
        """Check if trading should be allowed based on various conditions"""
        # Check if we're at maximum positions
        if len(self.positions) >= settings.MAX_CONCURRENT_POSITIONS:
            return False
        
        # Check if we have sufficient capital
        if self.current_capital <= 1000:  # Minimum $1000
            return False
        
        # Check maximum drawdown
        if self.max_drawdown_reached >= settings.MAX_DRAWDOWN_THRESHOLD:
            return False
        
        # Check if AI model is available and confident
        if not self.ai_model:
            return False
        
        return True
    
    async def _calculate_performance_metrics(self):
        """Calculate comprehensive performance metrics"""
        try:
            if not self.trade_history:
                return
            
            # Get closed trades for calculations
            closed_trades = [t for t in self.trade_history if t['status'] == 'CLOSED']
            
            if not closed_trades:
                return
            
            # Calculate returns
            returns = [t['realized_pnl'] / (t['entry_price'] * t['quantity']) for t in closed_trades]
            
            if len(returns) < 2:
                return
            
            # Sharpe Ratio
            avg_return = np.mean(returns)
            std_return = np.std(returns)
            risk_free_rate = settings.RISK_FREE_RATE / 252  # Daily rate
            
            if std_return > 0:
                self.risk_metrics['sharpe_ratio'] = (avg_return - risk_free_rate) / std_return
            
            # Maximum Drawdown
            cumulative_returns = np.cumsum(returns)
            peak = np.maximum.accumulate(cumulative_returns)
            drawdown = (peak - cumulative_returns) / peak
            self.risk_metrics['max_drawdown'] = np.max(drawdown) if len(drawdown) > 0 else 0
            
            # Volatility
            self.risk_metrics['volatility'] = std_return * np.sqrt(252)  # Annualized
            
            # VaR (95% confidence)
            if len(returns) >= 10:
                sorted_returns = np.sort(returns)
                var_index = int(0.05 * len(sorted_returns))
                self.risk_metrics['var_95'] = abs(sorted_returns[var_index]) * self.current_capital
            
            # Update max drawdown reached
            current_drawdown = self.risk_metrics['max_drawdown']
            self.max_drawdown_reached = max(self.max_drawdown_reached, current_drawdown)
            
        except Exception as e:
            logger.error(f"Error calculating performance metrics: {e}")
    
    async def _calculate_risk_metrics(self):
        """Calculate and update risk metrics"""
        try:
            # Portfolio concentration risk
            if self.positions:
                position_values = [
                    pos['quantity'] * pos['current_price'] 
                    for pos in self.positions.values()
                ]
                total_position_value = sum(position_values)
                
                # Check concentration limits
                max_position_pct = max(position_values) / self.current_capital if position_values else 0
                
                if max_position_pct > settings.MAX_POSITION_SIZE * 1.5:  # 150% of normal limit
                    logger.warning(f"Position concentration risk: {max_position_pct:.1%}")
            
            # Total exposure check
            total_exposure = sum(
                pos['quantity'] * pos['current_price'] 
                for pos in self.positions.values()
            )
            
            exposure_ratio = total_exposure / self.current_capital if self.current_capital > 0 else 0
            
            if exposure_ratio > 0.8:  # 80% of capital deployed
                logger.warning(f"High exposure ratio: {exposure_ratio:.1%}")
            
        except Exception as e:
            logger.error(f"Error calculating risk metrics: {e}")
    
    async def _enforce_risk_limits(self):
        """Enforce risk management limits"""
        try:
            # Check maximum drawdown
            if self.risk_metrics['max_drawdown'] > settings.MAX_DRAWDOWN_THRESHOLD:
                logger.warning("Maximum drawdown exceeded - stopping new trades")
                await self._emergency_stop("Maximum drawdown exceeded")
                return
            
            # Check VaR limits
            var_limit = self.current_capital * 0.1  # 10% of capital
            if self.risk_metrics['var_95'] > var_limit:
                logger.warning("VaR limit exceeded - reducing positions")
                await self._reduce_position_sizes()
            
            # Check correlation limits (simplified)
            if len(self.positions) > 1:
                await self._check_correlation_limits()
            
        except Exception as e:
            logger.error(f"Error enforcing risk limits: {e}")
    
    async def _emergency_stop(self, reason: str):
        """Emergency stop all trading activities"""
        try:
            logger.warning(f"🚨 EMERGENCY STOP: {reason}")
            
            # Close all positions
            await self._close_all_positions(reason)
            
            # Stop trading
            self.is_running = False
            
            # Broadcast emergency stop
            await self._broadcast_status(f"Emergency stop: {reason}", phase="emergency_stop")
            
        except Exception as e:
            logger.error(f"Error in emergency stop: {e}")
    
    async def _close_all_positions(self, reason: str):
        """Close all open positions"""
        try:
            for symbol in list(self.positions.keys()):
                position = self.positions[symbol]
                await self._close_position(symbol, position, reason)
            
        except Exception as e:
            logger.error(f"Error closing all positions: {e}")
    
    async def _cancel_all_orders(self):
        """Cancel all open orders"""
        try:
            for symbol in settings.TOP_CRYPTOCURRENCIES:
                await self.binance_client.cancel_all_orders(symbol)
            
        except Exception as e:
            logger.error(f"Error cancelling orders: {e}")
    
    # Database operations
    async def _save_bot_status(self):
        """Save bot status to database"""
        try:
            async with async_session() as session:
                bot_status = BotStatus(
                    is_running=self.is_running,
                    is_live_trading=self.is_live_trading,
                    current_capital=self.current_capital,
                    total_pnl=self.total_pnl,
                    daily_pnl=self.daily_pnl,
                    active_positions=len(self.positions),
                    total_trades=self.stats['total_trades'],
                    winning_trades=self.stats['winning_trades'],
                    losing_trades=self.stats['losing_trades'],
                    win_rate=self.stats['win_rate'],
                    max_drawdown=self.risk_metrics['max_drawdown'],
                    sharpe_ratio=self.risk_metrics['sharpe_ratio'],
                    last_updated=datetime.utcnow()
                )
                session.add(bot_status)
                await session.commit()
                
        except Exception as e:
            logger.error(f"Error saving bot status: {e}")
    
    async def _load_bot_state(self):
        """Load bot state from database"""
        try:
            async with async_session() as session:
                # Load latest bot status
                latest_status = await session.execute(
                    "SELECT * FROM bot_status ORDER BY last_updated DESC LIMIT 1"
                )
                result = latest_status.fetchone()
                
                if result:
                    self.current_capital = result.current_capital or settings.DEFAULT_CAPITAL
                    self.total_pnl = result.total_pnl or 0.0
                    self.daily_pnl = result.daily_pnl or 0.0
                    
        except Exception as e:
            logger.error(f"Error loading bot state: {e}")
    
    async def _save_trade_to_db(self, position: Dict[str, Any]):
        """Save trade to database"""
        try:
            async with async_session() as session:
                trade = Trade(
                    id=position['id'],
                    symbol=position['symbol'],
                    side=position['side'],
                    entry_price=position['entry_price'],
                    quantity=position['quantity'],
                    timestamp=position['timestamp'],
                    stop_loss=position['stop_loss'],
                    take_profit=position['take_profit'],
                    status=position['status'],
                    is_live=self.is_live_trading
                )
                session.add(trade)
                await session.commit()
                
        except Exception as e:
            logger.error(f"Error saving trade to database: {e}")
    
    async def _update_trade_in_db(self, position: Dict[str, Any]):
        """Update trade in database when closed"""
        try:
            async with async_session() as session:
                # Update trade record
                await session.execute(
                    """UPDATE trades SET 
                       exit_price = ?, pnl = ?, status = ?, 
                       close_timestamp = ?
                       WHERE id = ?""",
                    (position['exit_price'], position['realized_pnl'], 
                     position['status'], position['close_timestamp'], position['id'])
                )
                await session.commit()
                
        except Exception as e:
            logger.error(f"Error updating trade in database: {e}")
    
    async def _save_performance_metrics(self):
        """Save performance metrics to database"""
        try:
            async with async_session() as session:
                metrics = PerformanceMetrics(
                    timestamp=datetime.utcnow(),
                    total_pnl=self.total_pnl,
                    daily_pnl=self.daily_pnl,
                    win_rate=self.stats['win_rate'],
                    sharpe_ratio=self.risk_metrics['sharpe_ratio'],
                    max_drawdown=self.risk_metrics['max_drawdown'],
                    total_trades=self.stats['total_trades'],
                    var=self.risk_metrics['var_95'],
                    volatility=self.risk_metrics['volatility']
                )
                session.add(metrics)
                await session.commit()
                
        except Exception as e:
            logger.error(f"Error saving performance metrics: {e}")
    
    # WebSocket broadcasting
    async def _broadcast_status(self, message: str, phase: str = None, progress: float = None):
        """Broadcast status update via WebSocket"""
        if self.websocket_manager:
            await self.websocket_manager.broadcast_trading_status({
                'message': message,
                'phase': phase,
                'progress': progress,
                'timestamp': datetime.utcnow().isoformat()
            })
    
    async def _broadcast_trade_update(self, trade: Dict[str, Any]):
        """Broadcast trade update via WebSocket"""
        if self.websocket_manager:
            await self.websocket_manager.broadcast_message({
                'type': 'trade_update',
                'data': trade,
                'timestamp': datetime.utcnow().isoformat()
            })
    
    async def _broadcast_market_data(self):
        """Broadcast market data via WebSocket"""
        if self.websocket_manager:
            await self.websocket_manager.broadcast_message({
                'type': 'market_data',
                'data': self.market_data,
                'timestamp': datetime.utcnow().isoformat()
            })
    
    async def _broadcast_performance_update(self):
        """Broadcast performance update via WebSocket"""
        if self.websocket_manager:
            await self.websocket_manager.broadcast_message({
                'type': 'performance_update',
                'data': {
                    'total_pnl': self.total_pnl,
                    'daily_pnl': self.daily_pnl,
                    'win_rate': self.stats['win_rate'],
                    'sharpe_ratio': self.risk_metrics['sharpe_ratio'],
                    'max_drawdown': self.risk_metrics['max_drawdown'],
                    'total_trades': self.stats['total_trades'],
                    'var': self.risk_metrics['var_95'],
                    'volatility': self.risk_metrics['volatility']
                },
                'timestamp': datetime.utcnow().isoformat()
            })
    
    # Public API methods
    async def get_status(self) -> Dict[str, Any]:
        """Get current trading status"""
        return {
            'is_running': self.is_running,
            'is_live_trading': self.is_live_trading,
            'current_capital': self.current_capital,
            'total_pnl': self.total_pnl,
            'daily_pnl': self.daily_pnl,
            'active_positions': len(self.positions),
            'total_trades': self.stats['total_trades'],
            'winning_trades': self.stats['winning_trades'],
            'losing_trades': self.stats['losing_trades'],
            'win_rate': self.stats['win_rate'],
            'last_trade_time': max([p['timestamp'] for p in self.positions.values()]).isoformat() if self.positions else None,
            'model_last_updated': self.last_model_update.isoformat() if self.last_model_update else None
        }
    
    async def get_performance_metrics(self) -> Dict[str, Any]:
        """Get performance metrics"""
        return {
            'total_pnl': self.total_pnl,
            'daily_pnl': self.daily_pnl,
            'win_rate': self.stats['win_rate'],
            'sharpe_ratio': self.risk_metrics['sharpe_ratio'],
            'max_drawdown': self.risk_metrics['max_drawdown'],
            'total_trades': self.stats['total_trades'],
            'var': self.risk_metrics['var_95'],
            'volatility': self.risk_metrics['volatility'],
            'profit_factor': self.stats['profit_factor'],
            'avg_profit': self.stats['avg_profit'],
            'avg_loss': self.stats['avg_loss']
        }
    
    async def get_recent_trades(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent trades"""
        all_trades = list(self.positions.values()) + self.trade_history
        sorted_trades = sorted(all_trades, key=lambda x: x['timestamp'], reverse=True)
        return sorted_trades[:limit]
    
    async def get_portfolio_allocation(self) -> Dict[str, Any]:
        """Get current portfolio allocation"""
        total_value = self.current_capital + self.total_pnl
        
        portfolio = []
        
        # Cash allocation
        cash_value = self.current_capital - sum(
            pos['quantity'] * pos['current_price'] 
            for pos in self.positions.values()
        )
        
        if cash_value > 0:
            portfolio.append({
                'asset': 'USDT',
                'balance': cash_value,
                'value_usdt': cash_value,
                'percentage': (cash_value / total_value) * 100 if total_value > 0 else 0
            })
        
        # Position allocations
        for symbol, position in self.positions.items():
            value = position['quantity'] * position['current_price']
            portfolio.append({
                'asset': symbol.replace('USDT', ''),
                'balance': position['quantity'],
                'value_usdt': value,
                'percentage': (value / total_value) * 100 if total_value > 0 else 0
            })
        
        return {
            'total_value_usdt': total_value,
            'portfolio': portfolio,
            'last_updated': datetime.utcnow().isoformat()
        }
    
    async def start_data_download(self) -> str:
        """Start background data download"""
        task_id = f"data_download_{int(datetime.utcnow().timestamp())}"
        
        # Start download in background
        task = asyncio.create_task(self._download_comprehensive_data())
        self.background_tasks.append(task)
        
        return task_id
    
    async def _start_model_training(self):
        """Start model training in background"""
        try:
            # Get recent market data
            market_data = await self._download_comprehensive_data()
            
            # Train models
            await self._train_ai_models(market_data)
            
        except Exception as e:
            logger.error(f"Background model training failed: {e}")
