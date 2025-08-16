import asyncio
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from decimal import Decimal
import numpy as np
import pandas as pd
from loguru import logger
import json

from config import settings
from database import async_session, Trade, PerformanceMetrics, PortfolioBalance, BotStatus, TradingLog, get_bot_status, update_bot_status
from binance_client import BinanceClient
from ai_model import AITradingModel
from websocket_manager import WebSocketManager
import redis.asyncio as redis

class RiskManager:
    """Advanced risk management system"""
    
    def __init__(self):
        self.max_position_size = settings.MAX_POSITION_SIZE
        self.stop_loss_pct = settings.STOP_LOSS_PERCENTAGE
        self.take_profit_pct = settings.TAKE_PROFIT_PERCENTAGE
        self.max_drawdown = settings.MAX_DRAWDOWN_THRESHOLD
        self.volatility_target = settings.VOLATILITY_TARGET
        self.var_confidence = settings.VAR_CONFIDENCE_LEVEL
    
    def calculate_position_size(self, capital: float, price: float, volatility: float, confidence: float) -> float:
        """Calculate optimal position size using Kelly Criterion and risk management"""
        # Kelly Criterion adjustment
        kelly_fraction = confidence * 0.1  # Conservative Kelly
        
        # Volatility adjustment
        vol_adjustment = min(1.0, self.volatility_target / max(volatility, 0.01))
        
        # Risk-adjusted position size
        risk_adjusted_size = min(
            self.max_position_size,
            kelly_fraction * vol_adjustment
        )
        
        # Convert to actual quantity
        max_investment = capital * risk_adjusted_size
        quantity = max_investment / price
        
        return quantity
    
    def should_enter_trade(self, prediction: Dict[str, Any], market_conditions: Dict[str, Any]) -> bool:
        """Determine if conditions are suitable for entering a trade"""
        # Minimum confidence threshold
        if prediction.get('confidence', 0) < 0.7:
            return False
        
        # Check volatility conditions
        if market_conditions.get('volatility', 0) > self.volatility_target * 2:
            return False
        
        # Check for sufficient prediction magnitude
        if abs(prediction.get('ensemble_prediction', 0)) < 0.005:  # 0.5% minimum movement
            return False
        
        return True
    
    def calculate_stop_loss_take_profit(self, entry_price: float, side: str) -> tuple:
        """Calculate stop loss and take profit levels"""
        if side == 'BUY':
            stop_loss = entry_price * (1 - self.stop_loss_pct)
            take_profit = entry_price * (1 + self.take_profit_pct)
        else:  # SELL
            stop_loss = entry_price * (1 + self.stop_loss_pct)
            take_profit = entry_price * (1 - self.take_profit_pct)
        
        return stop_loss, take_profit
    
    def calculate_var(self, returns: List[float]) -> float:
        """Calculate Value at Risk"""
        if len(returns) < 10:
            return 0.0
        
        returns_array = np.array(returns)
        return np.percentile(returns_array, self.var_confidence * 100)

class TradingEngine:
    """Main trading engine orchestrating all trading activities"""
    
    def __init__(self, binance_client: BinanceClient, ai_model: AITradingModel, 
                 redis_client: redis.Redis, websocket_manager: WebSocketManager):
        self.binance_client = binance_client
        self.ai_model = ai_model
        self.redis_client = redis_client
        self.websocket_manager = websocket_manager
        self.risk_manager = RiskManager()
        
        # Trading state
        self.is_running = False
        self.is_live_trading = False
        self.current_capital = settings.DEFAULT_CAPITAL
        self.active_trades = {}
        self.performance_history = []
        
        # Data collection
        self.market_data = {}
        self.historical_data_task = None
        self.trading_task = None
        self.model_training_task = None
        
        # Performance tracking
        self.daily_pnl = 0.0
        self.total_pnl = 0.0
        self.trade_count = 0
        self.winning_trades = 0
        self.losing_trades = 0
    
    async def start(self):
        """Start the trading bot"""
        try:
            logger.info("Starting AI Crypto Trading Bot...")
            
            self.is_running = True
            await update_bot_status(
                is_running=True,
                last_data_update=datetime.utcnow()
            )
            
            # Start data collection
            await self._start_data_collection()
            
            # Start AI model training if not already trained
            if not self.ai_model.models:
                await self._start_model_training()
            
            # Start trading loop
            self.trading_task = asyncio.create_task(self._trading_loop())
            
            # Start performance monitoring
            asyncio.create_task(self._performance_monitoring_loop())
            
            logger.info("Trading bot started successfully")
            await self._log_event("INFO", "Trading bot started", {})
            
        except Exception as e:
            logger.error(f"Failed to start trading bot: {e}")
            self.is_running = False
            await update_bot_status(is_running=False)
            raise
    
    async def stop(self):
        """Stop the trading bot"""
        try:
            logger.info("Stopping AI Crypto Trading Bot...")
            
            self.is_running = False
            
            # Cancel running tasks
            if self.trading_task:
                self.trading_task.cancel()
            if self.historical_data_task:
                self.historical_data_task.cancel()
            if self.model_training_task:
                self.model_training_task.cancel()
            
            # Close all open positions
            await self._close_all_positions()
            
            await update_bot_status(is_running=False)
            
            logger.info("Trading bot stopped successfully")
            await self._log_event("INFO", "Trading bot stopped", {})
            
        except Exception as e:
            logger.error(f"Error stopping trading bot: {e}")
            raise
    
    async def switch_to_live(self):
        """Switch from testnet to live trading"""
        try:
            if self.is_live_trading:
                return
            
            logger.warning("Switching to LIVE trading mode")
            
            # Close all testnet positions
            await self._close_all_positions()
            
            # Update Binance client to live mode
            self.binance_client.testnet = False
            self.is_live_trading = True
            
            await update_bot_status(is_live_trading=True)
            
            logger.info("Successfully switched to live trading")
            await self._log_event("WARNING", "Switched to live trading", {"live_mode": True})
            
        except Exception as e:
            logger.error(f"Failed to switch to live trading: {e}")
            raise
    
    async def add_capital(self, amount: float) -> float:
        """Add capital to trading account"""
        try:
            self.current_capital += amount
            await update_bot_status(current_capital=self.current_capital)
            
            logger.info(f"Added ${amount} capital. New balance: ${self.current_capital}")
            await self._log_event("INFO", f"Capital added: ${amount}", {"new_balance": self.current_capital})
            
            return self.current_capital
        
        except Exception as e:
            logger.error(f"Failed to add capital: {e}")
            raise
    
    async def _start_data_collection(self):
        """Start collecting historical and real-time market data"""
        try:
            logger.info("Starting market data collection...")
            
            # Download historical data for top cryptocurrencies
            symbols = settings.TOP_CRYPTOCURRENCIES
            self.historical_data_task = asyncio.create_task(
                self._download_historical_data(symbols)
            )
            
            # Start real-time data stream
            asyncio.create_task(self._real_time_data_stream())
            
        except Exception as e:
            logger.error(f"Failed to start data collection: {e}")
            raise
    
    async def _download_historical_data(self, symbols: List[str]):
        """Download historical OHLCV data"""
        try:
            logger.info(f"Downloading historical data for {len(symbols)} symbols...")
            
            # Download data using Binance client
            historical_data = await self.binance_client.download_all_historical_data(
                symbols=symbols,
                days=settings.TRAINING_DATA_DAYS
            )
            
            # Store in market_data
            self.market_data.update(historical_data)
            
            # Cache in Redis
            for symbol, df in historical_data.items():
                await self.redis_client.setex(
                    f"historical_data:{symbol}",
                    3600,  # 1 hour expiry
                    df.to_json()
                )
            
            logger.info(f"Downloaded historical data for {len(historical_data)} symbols")
            await self._log_event("INFO", "Historical data download completed", {
                "symbols_count": len(historical_data),
                "total_data_points": sum(len(df) for df in historical_data.values())
            })
            
        except Exception as e:
            logger.error(f"Failed to download historical data: {e}")
            await self._log_event("ERROR", f"Historical data download failed: {str(e)}", {})
    
    async def _real_time_data_stream(self):
        """Stream real-time market data"""
        while self.is_running:
            try:
                # Get current prices for all symbols
                tickers = await self.binance_client.get_ticker_prices(settings.TOP_CRYPTOCURRENCIES)
                
                current_time = datetime.utcnow()
                
                for ticker in tickers:
                    symbol = ticker['symbol']
                    price = float(ticker['price'])
                    
                    # Update Redis cache
                    await self.redis_client.setex(
                        f"current_price:{symbol}",
                        60,  # 1 minute expiry
                        price
                    )
                    
                    # Broadcast to WebSocket clients
                    await self.websocket_manager.broadcast_market_data({
                        'symbol': symbol,
                        'price': price,
                        'timestamp': current_time.isoformat()
                    })
                
                await asyncio.sleep(5)  # Update every 5 seconds
                
            except Exception as e:
                logger.error(f"Error in real-time data stream: {e}")
                await asyncio.sleep(10)
    
    async def _start_model_training(self):
        """Start AI model training"""
        try:
            if not self.market_data:
                logger.warning("No market data available for training, waiting...")
                await asyncio.sleep(10)
                return
            
            logger.info("Starting AI model training...")
            
            self.model_training_task = asyncio.create_task(
                self.ai_model.train_model(self.market_data)
            )
            
            training_result = await self.model_training_task
            
            logger.info(f"AI model training completed: {training_result}")
            await self._log_event("INFO", "AI model training completed", training_result)
            
        except Exception as e:
            logger.error(f"Failed to start model training: {e}")
            await self._log_event("ERROR", f"Model training failed: {str(e)}", {})
    
    async def _trading_loop(self):
        """Main trading loop"""
        while self.is_running:
            try:
                # Check if AI model is ready
                if not self.ai_model.models or self.ai_model.is_training:
                    await asyncio.sleep(30)
                    continue
                
                # Get market predictions
                predictions = await self.ai_model.predict(self.market_data)
                
                if not predictions:
                    await asyncio.sleep(60)
                    continue
                
                # Process each symbol
                for symbol, prediction in predictions.items():
                    await self._process_trading_signal(symbol, prediction)
                
                # Check existing positions
                await self._manage_open_positions()
                
                # Update performance metrics
                await self._update_performance_metrics()
                
                await asyncio.sleep(30)  # Run every 30 seconds
                
            except Exception as e:
                logger.error(f"Error in trading loop: {e}")
                await asyncio.sleep(60)
    
    async def _process_trading_signal(self, symbol: str, prediction: Dict[str, Any]):
        """Process trading signal for a symbol"""
        try:
            # Get current market conditions
            current_price = await self.redis_client.get(f"current_price:{symbol}")
            if not current_price:
                return
            
            current_price = float(current_price)
            
            # Calculate market volatility
            if symbol in self.market_data:
                recent_data = self.market_data[symbol].tail(24)  # Last 24 hours
                returns = recent_data['close'].pct_change().dropna()
                volatility = returns.std() * np.sqrt(24)  # Annualized volatility
            else:
                volatility = 0.2  # Default volatility
            
            market_conditions = {
                'volatility': volatility,
                'current_price': current_price
            }
            
            # Check if we should enter a trade
            if not self.risk_manager.should_enter_trade(prediction, market_conditions):
                return
            
            # Check if we already have a position in this symbol
            if symbol in self.active_trades:
                return
            
            # Determine trade direction
            ensemble_pred = prediction.get('ensemble_prediction', 0)
            confidence = prediction.get('confidence', 0)
            
            if ensemble_pred > 0.01:  # Buy signal
                side = 'BUY'
            elif ensemble_pred < -0.01:  # Sell signal  
                side = 'SELL'
            else:
                return  # No clear signal
            
            # Calculate position size
            quantity = self.risk_manager.calculate_position_size(
                capital=self.current_capital,
                price=current_price,
                volatility=volatility,
                confidence=confidence
            )
            
            if quantity * current_price < 10:  # Minimum $10 trade
                return
            
            # Place the order
            await self._place_trade(symbol, side, quantity, current_price, prediction)
            
        except Exception as e:
            logger.error(f"Error processing trading signal for {symbol}: {e}")
    
    async def _place_trade(self, symbol: str, side: str, quantity: float, price: float, prediction: Dict[str, Any]):
        """Place a trade order"""
        try:
            # Place market order
            order_result = await self.binance_client.place_order(
                symbol=symbol,
                side=side,
                order_type='MARKET',
                quantity=quantity
            )
            
            # Calculate stop loss and take profit
            stop_loss, take_profit = self.risk_manager.calculate_stop_loss_take_profit(price, side)
            
            # Create trade record
            trade_id = str(uuid.uuid4())
            trade = Trade(
                id=trade_id,
                symbol=symbol,
                side=side,
                entry_price=price,
                quantity=quantity,
                status='OPEN',
                strategy='AI_ENSEMBLE',
                confidence_score=prediction.get('confidence', 0),
                is_live=self.is_live_trading,
                entry_time=datetime.utcnow()
            )
            
            # Save to database
            async with async_session() as session:
                session.add(trade)
                await session.commit()
            
            # Add to active trades
            self.active_trades[symbol] = {
                'trade_id': trade_id,
                'symbol': symbol,
                'side': side,
                'entry_price': price,
                'quantity': quantity,
                'stop_loss': stop_loss,
                'take_profit': take_profit,
                'entry_time': datetime.utcnow(),
                'prediction': prediction
            }
            
            # Update trade count
            self.trade_count += 1
            await update_bot_status(
                active_positions=len(self.active_trades),
                last_trade_time=datetime.utcnow()
            )
            
            # Broadcast trade update
            await self.websocket_manager.broadcast_trade_update({
                'id': trade_id,
                'symbol': symbol,
                'side': side,
                'entry_price': price,
                'quantity': quantity,
                'status': 'OPEN',
                'timestamp': datetime.utcnow().isoformat()
            })
            
            logger.info(f"Placed {side} order for {symbol}: {quantity} @ ${price}")
            await self._log_event("INFO", f"Trade placed: {side} {symbol}", {
                'trade_id': trade_id,
                'price': price,
                'quantity': quantity,
                'confidence': prediction.get('confidence', 0)
            })
            
        except Exception as e:
            logger.error(f"Failed to place trade for {symbol}: {e}")
            await self._log_event("ERROR", f"Trade placement failed for {symbol}: {str(e)}", {})
    
    async def _manage_open_positions(self):
        """Manage open trading positions"""
        positions_to_close = []
        
        for symbol, position in self.active_trades.items():
            try:
                # Get current price
                current_price = await self.redis_client.get(f"current_price:{symbol}")
                if not current_price:
                    continue
                
                current_price = float(current_price)
                entry_price = position['entry_price']
                side = position['side']
                
                # Calculate current P&L
                if side == 'BUY':
                    pnl_pct = (current_price - entry_price) / entry_price
                else:  # SELL
                    pnl_pct = (entry_price - current_price) / entry_price
                
                pnl_amount = pnl_pct * position['quantity'] * entry_price
                
                # Check stop loss and take profit
                should_close = False
                close_reason = ""
                
                if side == 'BUY':
                    if current_price <= position['stop_loss']:
                        should_close = True
                        close_reason = "stop_loss"
                    elif current_price >= position['take_profit']:
                        should_close = True
                        close_reason = "take_profit"
                else:  # SELL
                    if current_price >= position['stop_loss']:
                        should_close = True
                        close_reason = "stop_loss"
                    elif current_price <= position['take_profit']:
                        should_close = True
                        close_reason = "take_profit"
                
                # Check time-based exit (maximum 24 hours)
                time_in_trade = datetime.utcnow() - position['entry_time']
                if time_in_trade > timedelta(hours=24):
                    should_close = True
                    close_reason = "time_exit"
                
                if should_close:
                    positions_to_close.append((symbol, current_price, close_reason))
            
            except Exception as e:
                logger.error(f"Error managing position for {symbol}: {e}")
        
        # Close positions
        for symbol, exit_price, reason in positions_to_close:
            await self._close_position(symbol, exit_price, reason)
    
    async def _close_position(self, symbol: str, exit_price: float, reason: str):
        """Close a trading position"""
        try:
            if symbol not in self.active_trades:
                return
            
            position = self.active_trades[symbol]
            
            # Place closing order
            opposite_side = 'SELL' if position['side'] == 'BUY' else 'BUY'
            await self.binance_client.place_order(
                symbol=symbol,
                side=opposite_side,
                order_type='MARKET',
                quantity=position['quantity']
            )
            
            # Calculate P&L
            entry_price = position['entry_price']
            
            if position['side'] == 'BUY':
                pnl_pct = (exit_price - entry_price) / entry_price
            else:  # SELL
                pnl_pct = (entry_price - exit_price) / entry_price
            
            pnl_amount = pnl_pct * position['quantity'] * entry_price
            
            # Update trade in database
            async with async_session() as session:
                from sqlalchemy import select
                result = await session.execute(select(Trade).where(Trade.id == position['trade_id']))
                trade = result.scalar_one()
                
                trade.exit_price = exit_price
                trade.exit_time = datetime.utcnow()
                trade.pnl = pnl_amount
                trade.status = 'CLOSED'
                
                await session.commit()
            
            # Update performance
            self.total_pnl += pnl_amount
            self.daily_pnl += pnl_amount
            
            if pnl_amount > 0:
                self.winning_trades += 1
            else:
                self.losing_trades += 1
            
            # Remove from active trades
            del self.active_trades[symbol]
            
            await update_bot_status(
                active_positions=len(self.active_trades),
                total_pnl=self.total_pnl
            )
            
            # Broadcast trade update
            await self.websocket_manager.broadcast_trade_update({
                'id': position['trade_id'],
                'symbol': symbol,
                'side': position['side'],
                'entry_price': entry_price,
                'exit_price': exit_price,
                'quantity': position['quantity'],
                'pnl': pnl_amount,
                'status': 'CLOSED',
                'close_reason': reason,
                'timestamp': datetime.utcnow().isoformat()
            })
            
            logger.info(f"Closed {position['side']} position for {symbol}: P&L ${pnl_amount:.2f} ({reason})")
            await self._log_event("INFO", f"Position closed: {symbol}", {
                'trade_id': position['trade_id'],
                'pnl': pnl_amount,
                'reason': reason,
                'entry_price': entry_price,
                'exit_price': exit_price
            })
            
        except Exception as e:
            logger.error(f"Failed to close position for {symbol}: {e}")
    
    async def _close_all_positions(self):
        """Close all open positions"""
        for symbol in list(self.active_trades.keys()):
            try:
                current_price = await self.redis_client.get(f"current_price:{symbol}")
                if current_price:
                    await self._close_position(symbol, float(current_price), "force_close")
            except Exception as e:
                logger.error(f"Error closing position for {symbol}: {e}")
    
    async def _update_performance_metrics(self):
        """Update and save performance metrics"""
        try:
            if self.trade_count == 0:
                return
            
            # Calculate metrics
            win_rate = (self.winning_trades / self.trade_count) * 100
            
            # Get recent returns for Sharpe ratio calculation
            returns = []
            async with async_session() as session:
                from sqlalchemy import select
                result = await session.execute(
                    select(Trade).where(Trade.status == 'CLOSED').limit(100)
                )
                recent_trades = result.scalars().all()
                
                for trade in recent_trades:
                    if trade.pnl:
                        returns.append(float(trade.pnl))
            
            if len(returns) > 10:
                returns_array = np.array(returns)
                avg_return = np.mean(returns_array)
                std_return = np.std(returns_array)
                sharpe_ratio = (avg_return / std_return) if std_return > 0 else 0
                
                # Calculate max drawdown
                cumulative_returns = np.cumsum(returns_array)
                running_max = np.maximum.accumulate(cumulative_returns)
                drawdown = (cumulative_returns - running_max) / running_max
                max_drawdown = np.min(drawdown) * 100
                
                # Calculate VaR
                var = self.risk_manager.calculate_var(returns)
            else:
                sharpe_ratio = 0
                max_drawdown = 0
                var = 0
            
            # Broadcast performance update
            performance_data = {
                'total_pnl': self.total_pnl,
                'daily_pnl': self.daily_pnl,
                'win_rate': win_rate,
                'sharpe_ratio': sharpe_ratio,
                'max_drawdown': max_drawdown,
                'var': var,
                'total_trades': self.trade_count,
                'winning_trades': self.winning_trades,
                'losing_trades': self.losing_trades,
                'active_positions': len(self.active_trades)
            }
            
            await self.websocket_manager.broadcast_performance_update(performance_data)
            
        except Exception as e:
            logger.error(f"Error updating performance metrics: {e}")
    
    async def _performance_monitoring_loop(self):
        """Monitor performance and save metrics daily"""
        while self.is_running:
            try:
                await asyncio.sleep(3600)  # Check every hour
                
                # Reset daily P&L at midnight
                current_hour = datetime.utcnow().hour
                if current_hour == 0:
                    # Save daily performance
                    await self._save_daily_performance()
                    self.daily_pnl = 0.0
                
            except Exception as e:
                logger.error(f"Error in performance monitoring: {e}")
    
    async def _save_daily_performance(self):
        """Save daily performance metrics to database"""
        try:
            # Calculate daily metrics
            win_rate = (self.winning_trades / max(self.trade_count, 1)) * 100
            
            performance = PerformanceMetrics(
                date=datetime.utcnow().date(),
                total_pnl=self.total_pnl,
                daily_pnl=self.daily_pnl,
                win_rate=win_rate,
                sharpe_ratio=0,  # Calculate later with more data
                max_drawdown=0,  # Calculate later
                volatility=0,    # Calculate later
                var=0,           # Calculate later
                total_trades=self.trade_count,
                winning_trades=self.winning_trades,
                losing_trades=self.losing_trades
            )
            
            async with async_session() as session:
                session.add(performance)
                await session.commit()
            
        except Exception as e:
            logger.error(f"Error saving daily performance: {e}")
    
    async def get_status(self) -> Dict[str, Any]:
        """Get current trading bot status"""
        bot_status = await get_bot_status()
        
        return {
            'is_running': self.is_running,
            'is_live_trading': self.is_live_trading,
            'current_capital': self.current_capital,
            'total_pnl': self.total_pnl,
            'daily_pnl': self.daily_pnl,
            'active_positions': len(self.active_trades),
            'total_trades': self.trade_count,
            'winning_trades': self.winning_trades,
            'losing_trades': self.losing_trades,
            'win_rate': (self.winning_trades / max(self.trade_count, 1)) * 100,
            'last_trade_time': bot_status.last_trade_time.isoformat() if bot_status.last_trade_time else None,
            'model_last_updated': bot_status.model_last_updated.isoformat() if bot_status.model_last_updated else None
        }
    
    async def get_performance_metrics(self) -> Dict[str, Any]:
        """Get detailed performance metrics"""
        # Get recent trades for calculations
        returns = []
        async with async_session() as session:
            from sqlalchemy import select
            result = await session.execute(
                select(Trade).where(Trade.status == 'CLOSED').limit(100)
            )
            recent_trades = result.scalars().all()
            
            for trade in recent_trades:
                if trade.pnl:
                    returns.append(float(trade.pnl))
        
        if len(returns) > 10:
            returns_array = np.array(returns)
            avg_return = np.mean(returns_array)
            std_return = np.std(returns_array)
            sharpe_ratio = (avg_return / std_return) if std_return > 0 else 0
            
            # Calculate max drawdown
            cumulative_returns = np.cumsum(returns_array)
            running_max = np.maximum.accumulate(cumulative_returns)
            drawdown = (cumulative_returns - running_max) / running_max
            max_drawdown = np.min(drawdown) * 100
            
            volatility = std_return * np.sqrt(252)  # Annualized volatility
            var = self.risk_manager.calculate_var(returns)
        else:
            sharpe_ratio = 0
            max_drawdown = 0
            volatility = 0
            var = 0
        
        win_rate = (self.winning_trades / max(self.trade_count, 1)) * 100
        
        return {
            'total_pnl': self.total_pnl,
            'win_rate': win_rate,
            'sharpe_ratio': sharpe_ratio,
            'max_drawdown': max_drawdown,
            'total_trades': self.trade_count,
            'var': var,
            'volatility': volatility * 100  # Convert to percentage
        }
    
    async def get_recent_trades(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent trades"""
        trades = []
        
        async with async_session() as session:
            from sqlalchemy import select
            result = await session.execute(
                select(Trade).order_by(Trade.entry_time.desc()).limit(limit)
            )
            recent_trades = result.scalars().all()
            
            for trade in recent_trades:
                trades.append({
                    'id': trade.id,
                    'symbol': trade.symbol,
                    'side': trade.side,
                    'entry_price': float(trade.entry_price) if trade.entry_price else 0,
                    'exit_price': float(trade.exit_price) if trade.exit_price else None,
                    'quantity': float(trade.quantity) if trade.quantity else 0,
                    'pnl': float(trade.pnl) if trade.pnl else None,
                    'status': trade.status,
                    'timestamp': trade.entry_time.isoformat()
                })
        
        return trades
    
    async def get_portfolio_allocation(self) -> Dict[str, Any]:
        """Get current portfolio allocation"""
        try:
            if not self.binance_client.api_key:
                # Return mock data for demo
                return {
                    'total_value_usdt': self.current_capital,
                    'portfolio': [
                        {'asset': 'USDT', 'balance': self.current_capital * 0.6, 'value_usdt': self.current_capital * 0.6, 'percentage': 60.0},
                        {'asset': 'BTC', 'balance': 0.01, 'value_usdt': self.current_capital * 0.3, 'percentage': 30.0},
                        {'asset': 'ETH', 'balance': 0.1, 'value_usdt': self.current_capital * 0.1, 'percentage': 10.0}
                    ],
                    'last_updated': datetime.utcnow().isoformat()
                }
            
            return await self.binance_client.calculate_portfolio_value()
        
        except Exception as e:
            logger.error(f"Error getting portfolio allocation: {e}")
            return {'total_value_usdt': 0, 'portfolio': [], 'last_updated': datetime.utcnow().isoformat()}
    
    async def start_data_download(self) -> str:
        """Start historical data download task"""
        task_id = str(uuid.uuid4())
        
        asyncio.create_task(self._download_historical_data(settings.TOP_CRYPTOCURRENCIES))
        
        return task_id
    
    async def _log_event(self, level: str, message: str, metadata: Dict[str, Any]):
        """Log trading event"""
        try:
            async with async_session() as session:
                log_entry = TradingLog(
                    level=level,
                    message=message,
                    component='TRADING_ENGINE',
                    metadata=json.dumps(metadata)
                )
                session.add(log_entry)
                await session.commit()
        
        except Exception as e:
            logger.error(f"Error logging event: {e}")
