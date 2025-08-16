import asyncio
from datetime import datetime, date, timezone, timedelta
from typing import Optional, Dict, Any, List
from decimal import Decimal
import json

from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, Text, Date, JSON, Index
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
from sqlalchemy import select, update, delete
from loguru import logger

from config import settings

# Create base class
Base = declarative_base()

# Database engine
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    future=True
)

# Session factory
async_session = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False
)

class BotStatus(Base):
    """Bot status and configuration"""
    __tablename__ = "bot_status"
    
    id = Column(Integer, primary_key=True, index=True)
    is_running = Column(Boolean, default=False)
    is_live_trading = Column(Boolean, default=False)
    current_capital = Column(Float, default=100000.0)
    active_positions = Column(Integer, default=0)
    total_trades = Column(Integer, default=0)
    total_pnl = Column(Float, default=0.0)
    win_rate = Column(Float, default=0.0)
    last_trade_time = Column(DateTime, nullable=True)
    last_data_update = Column(DateTime, nullable=True)
    model_last_updated = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

class Trade(Base):
    """Individual trade records"""
    __tablename__ = "trades"
    
    id = Column(String, primary_key=True, index=True)
    symbol = Column(String, nullable=False, index=True)
    side = Column(String, nullable=False)  # BUY or SELL
    order_type = Column(String, default="MARKET")
    entry_price = Column(Float, nullable=False)
    exit_price = Column(Float, nullable=True)
    quantity = Column(Float, nullable=False)
    pnl = Column(Float, nullable=True)
    pnl_percentage = Column(Float, nullable=True)
    status = Column(String, default="OPEN")  # OPEN, CLOSED, CANCELLED
    strategy = Column(String, default="AI_ENSEMBLE")
    confidence_score = Column(Float, nullable=True)
    stop_loss = Column(Float, nullable=True)
    take_profit = Column(Float, nullable=True)
    is_live = Column(Boolean, default=False)
    entry_time = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    exit_time = Column(DateTime, nullable=True)
    trade_metadata = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    
    # Indexes for performance
    __table_args__ = (
        Index('idx_trades_symbol_status', 'symbol', 'status'),
        Index('idx_trades_entry_time', 'entry_time'),
        Index('idx_trades_is_live', 'is_live'),
    )

class PerformanceMetrics(Base):
    """Daily performance metrics"""
    __tablename__ = "performance_metrics"
    
    id = Column(Integer, primary_key=True, index=True)
    date = Column(Date, unique=True, nullable=False, index=True)
    total_pnl = Column(Float, default=0.0)
    daily_pnl = Column(Float, default=0.0)
    win_rate = Column(Float, default=0.0)
    sharpe_ratio = Column(Float, default=0.0)
    max_drawdown = Column(Float, default=0.0)
    volatility = Column(Float, default=0.0)
    var = Column(Float, default=0.0)  # Value at Risk
    total_trades = Column(Integer, default=0)
    winning_trades = Column(Integer, default=0)
    losing_trades = Column(Integer, default=0)
    avg_win = Column(Float, default=0.0)
    avg_loss = Column(Float, default=0.0)
    profit_factor = Column(Float, default=0.0)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

class PortfolioBalance(Base):
    """Portfolio balance tracking"""
    __tablename__ = "portfolio_balances"
    
    id = Column(Integer, primary_key=True, index=True)
    asset = Column(String, nullable=False, index=True)
    balance = Column(Float, nullable=False)
    locked_balance = Column(Float, default=0.0)
    value_usdt = Column(Float, nullable=False)
    percentage = Column(Float, nullable=False)
    last_price = Column(Float, nullable=True)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)

class AIModelMetrics(Base):
    """AI model training metrics"""
    __tablename__ = "ai_model_metrics"
    
    id = Column(Integer, primary_key=True, index=True)
    model_version = Column(String, nullable=False)
    model_type = Column(String, default="ENSEMBLE")
    training_start = Column(DateTime, nullable=False)
    training_end = Column(DateTime, nullable=True)
    training_loss = Column(Float, nullable=True)
    validation_loss = Column(Float, nullable=True)
    accuracy = Column(Float, nullable=True)
    precision = Column(Float, nullable=True)
    recall = Column(Float, nullable=True)
    f1_score = Column(Float, nullable=True)
    data_points = Column(Integer, nullable=True)
    features_count = Column(Integer, nullable=True)
    epochs_trained = Column(Integer, nullable=True)
    is_active = Column(Boolean, default=False)
    hyperparameters = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

class MarketData(Base):
    """Market data storage"""
    __tablename__ = "market_data"
    
    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String, nullable=False, index=True)
    timestamp = Column(DateTime, nullable=False, index=True)
    open_price = Column(Float, nullable=False)
    high_price = Column(Float, nullable=False)
    low_price = Column(Float, nullable=False)
    close_price = Column(Float, nullable=False)
    volume = Column(Float, nullable=False)
    quote_volume = Column(Float, nullable=True)
    trades_count = Column(Integer, nullable=True)
    interval = Column(String, default="1h")
    
    __table_args__ = (
        Index('idx_market_data_symbol_timestamp', 'symbol', 'timestamp'),
    )

class TradingSignal(Base):
    """AI trading signals"""
    __tablename__ = "trading_signals"
    
    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String, nullable=False, index=True)
    signal_type = Column(String, nullable=False)  # BUY, SELL, HOLD
    confidence = Column(Float, nullable=False)
    predicted_price = Column(Float, nullable=True)
    predicted_change = Column(Float, nullable=True)
    risk_score = Column(Float, nullable=True)
    model_predictions = Column(JSON, nullable=True)  # Individual model predictions
    market_conditions = Column(JSON, nullable=True)
    is_executed = Column(Boolean, default=False)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)

class TradingLog(Base):
    """System and trading event logs"""
    __tablename__ = "trading_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    level = Column(String, nullable=False, index=True)  # INFO, WARNING, ERROR
    message = Column(Text, nullable=False)
    component = Column(String, nullable=False)  # TRADING_ENGINE, AI_MODEL, etc.
    trade_id = Column(String, nullable=True)
    symbol = Column(String, nullable=True)
    trade_metadata = Column(JSON, nullable=True)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)

class RiskMetrics(Base):
    """Risk management metrics"""
    __tablename__ = "risk_metrics"
    
    id = Column(Integer, primary_key=True, index=True)
    date = Column(Date, nullable=False, index=True)
    var_95 = Column(Float, nullable=True)  # Value at Risk 95%
    var_99 = Column(Float, nullable=True)  # Value at Risk 99%
    expected_shortfall = Column(Float, nullable=True)
    max_drawdown = Column(Float, nullable=True)
    current_drawdown = Column(Float, nullable=True)
    volatility = Column(Float, nullable=True)
    beta = Column(Float, nullable=True)
    correlation_btc = Column(Float, nullable=True)
    leverage = Column(Float, default=1.0)
    exposure = Column(Float, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

class BacktestResult(Base):
    """Backtest results storage"""
    __tablename__ = "backtest_results"
    
    id = Column(Integer, primary_key=True, index=True)
    strategy_name = Column(String, nullable=False)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    initial_capital = Column(Float, nullable=False)
    final_capital = Column(Float, nullable=False)
    total_return = Column(Float, nullable=False)
    sharpe_ratio = Column(Float, nullable=True)
    max_drawdown = Column(Float, nullable=True)
    win_rate = Column(Float, nullable=True)
    total_trades = Column(Integer, nullable=False)
    parameters = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

# Database operations
async def init_database():
    """Initialize database tables"""
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        
        # Create initial bot status if not exists
        async with async_session() as session:
            result = await session.execute(select(BotStatus))
            bot_status = result.scalar_one_or_none()
            
            if not bot_status:
                bot_status = BotStatus(
                    is_running=False,
                    is_live_trading=False,
                    current_capital=settings.DEFAULT_CAPITAL
                )
                session.add(bot_status)
                await session.commit()
        
        logger.info("Database initialized successfully")
        
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        raise

async def get_bot_status() -> BotStatus:
    """Get current bot status"""
    async with async_session() as session:
        result = await session.execute(select(BotStatus).limit(1))
        bot_status = result.scalar_one_or_none()
        
        if not bot_status:
            bot_status = BotStatus(
                is_running=False,
                is_live_trading=False,
                current_capital=settings.DEFAULT_CAPITAL
            )
            session.add(bot_status)
            await session.commit()
            await session.refresh(bot_status)
        
        return bot_status

async def update_bot_status(**kwargs) -> BotStatus:
    """Update bot status"""
    async with async_session() as session:
        result = await session.execute(select(BotStatus).limit(1))
        bot_status = result.scalar_one_or_none()
        
        if not bot_status:
            bot_status = BotStatus(**kwargs)
            session.add(bot_status)
        else:
            for key, value in kwargs.items():
                if hasattr(bot_status, key):
                    setattr(bot_status, key, value)
            bot_status.updated_at = datetime.now(timezone.utc)
        
        await session.commit()
        await session.refresh(bot_status)
        return bot_status

async def save_trade(trade_data: Dict[str, Any]) -> Trade:
    """Save a trade to database"""
    async with async_session() as session:
        trade = Trade(**trade_data)
        session.add(trade)
        await session.commit()
        await session.refresh(trade)
        return trade

async def update_trade(trade_id: str, **kwargs) -> Optional[Trade]:
    """Update a trade"""
    async with async_session() as session:
        result = await session.execute(select(Trade).where(Trade.id == trade_id))
        trade = result.scalar_one_or_none()
        
        if trade:
            for key, value in kwargs.items():
                if hasattr(trade, key):
                    setattr(trade, key, value)
            
            await session.commit()
            await session.refresh(trade)
        
        return trade

async def get_recent_trades(limit: int = 10, symbol: Optional[str] = None) -> List[Trade]:
    """Get recent trades"""
    async with async_session() as session:
        query = select(Trade).order_by(Trade.entry_time.desc()).limit(limit)
        
        if symbol:
            query = query.where(Trade.symbol == symbol)
        
        result = await session.execute(query)
        return result.scalars().all()

async def get_open_trades(symbol: Optional[str] = None) -> List[Trade]:
    """Get open trades"""
    async with async_session() as session:
        query = select(Trade).where(Trade.status == "OPEN")
        
        if symbol:
            query = query.where(Trade.symbol == symbol)
        
        result = await session.execute(query)
        return result.scalars().all()

async def save_performance_metrics(metrics_data: Dict[str, Any]) -> PerformanceMetrics:
    """Save performance metrics"""
    async with async_session() as session:
        # Check if metrics for this date already exist
        target_date = metrics_data.get('date', date.today())
        result = await session.execute(
            select(PerformanceMetrics).where(PerformanceMetrics.date == target_date)
        )
        existing = result.scalar_one_or_none()
        
        if existing:
            # Update existing metrics
            for key, value in metrics_data.items():
                if hasattr(existing, key):
                    setattr(existing, key, value)
            metrics = existing
        else:
            # Create new metrics
            metrics = PerformanceMetrics(**metrics_data)
            session.add(metrics)
        
        await session.commit()
        await session.refresh(metrics)
        return metrics

async def save_market_data(market_data_list: List[Dict[str, Any]]) -> int:
    """Save market data in batch"""
    async with async_session() as session:
        count = 0
        for data in market_data_list:
            market_data = MarketData(**data)
            session.add(market_data)
            count += 1
        
        await session.commit()
        return count

async def get_market_data(
    symbol: str,
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
    limit: int = 1000
) -> List[MarketData]:
    """Get market data for a symbol"""
    async with async_session() as session:
        query = select(MarketData).where(MarketData.symbol == symbol)
        
        if start_time:
            query = query.where(MarketData.timestamp >= start_time)
        if end_time:
            query = query.where(MarketData.timestamp <= end_time)
        
        query = query.order_by(MarketData.timestamp.desc()).limit(limit)
        
        result = await session.execute(query)
        return result.scalars().all()

async def save_trading_log(log_data: Dict[str, Any]) -> TradingLog:
    """Save trading log entry"""
    async with async_session() as session:
        log_entry = TradingLog(**log_data)
        session.add(log_entry)
        await session.commit()
        await session.refresh(log_entry)
        return log_entry

async def cleanup_old_data(days: int = 90):
    """Clean up old data to prevent database bloat"""
    cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)
    
    async with async_session() as session:
        # Clean old logs
        await session.execute(
            delete(TradingLog).where(TradingLog.timestamp < cutoff_date)
        )
        
        # Clean old market data (keep more recent data)
        market_cutoff = datetime.now(timezone.utc) - timedelta(days=days * 2)
        await session.execute(
            delete(MarketData).where(MarketData.timestamp < market_cutoff)
        )
        
        await session.commit()
        logger.info(f"Cleaned up data older than {days} days")

# Initialize database on import
if __name__ == "__main__":
    asyncio.run(init_database())
