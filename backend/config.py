import os
from typing import List
from pydantic_settings import BaseSettings
from pydantic import ConfigDict

class Settings(BaseSettings):
    """Application settings"""

    # Database settings
    DATABASE_URL: str = "sqlite+aiosqlite:///./trading_bot.db"

    # Redis settings
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0

    # Binance API settings - Secure environment variable integration
    BINANCE_API_KEY: str = os.getenv("BINANCE_API_KEY", "")
    BINANCE_SECRET_KEY: str = os.getenv("BINANCE_SECRET_KEY", "")
    BINANCE_TESTNET_API_KEY: str = os.getenv("BINANCE_TESTNET_API_KEY", "")
    BINANCE_TESTNET_SECRET_KEY: str = os.getenv("BINANCE_TESTNET_SECRET_KEY", "")
    TRADING_MODE: str = os.getenv("TRADING_MODE", "testnet")  # "testnet" or "live"
    BINANCE_TESTNET: bool = os.getenv("TRADING_MODE", "testnet") == "testnet"
    
    # Trading settings
    DEFAULT_CAPITAL: float = 100000.0  # Default capital in USD
    MAX_POSITION_SIZE: float = 0.05    # Maximum 5% of capital per position
    STOP_LOSS_PERCENTAGE: float = 0.02  # 2% stop loss
    TAKE_PROFIT_PERCENTAGE: float = 0.04  # 4% take profit
    MAX_DRAWDOWN_THRESHOLD: float = 0.15  # 15% max drawdown
    VOLATILITY_TARGET: float = 0.20  # 20% target volatility
    VAR_CONFIDENCE_LEVEL: float = 0.95  # 95% VaR confidence
    
    # AI Model settings
    MODEL_UPDATE_INTERVAL: int = 24  # Hours between model retraining
    TRAINING_DATA_DAYS: int = 365    # Days of historical data for training
    PREDICTION_CONFIDENCE_THRESHOLD: float = 0.7  # Minimum confidence for trades
    
    # Risk Management
    MAX_CONCURRENT_POSITIONS: int = 10
    RISK_FREE_RATE: float = 0.02  # 2% annual risk-free rate
    MAX_LEVERAGE: float = 1.0     # No leverage by default
    
    # Top cryptocurrencies to trade
    TOP_CRYPTOCURRENCIES: List[str] = [
        "BTCUSDT", "ETHUSDT", "BNBUSDT", "ADAUSDT", "SOLUSDT",
        "XRPUSDT", "DOTUSDT", "DOGEUSDT", "AVAXUSDT", "LINKUSDT"
    ]
    
    # Market data settings
    MARKET_DATA_INTERVAL: str = "1h"  # Hourly candles
    MAX_CANDLES_PER_REQUEST: int = 1000
    DATA_UPDATE_FREQUENCY: int = 300  # 5 minutes in seconds
    
    # WebSocket settings
    WS_HEARTBEAT_INTERVAL: int = 30  # Seconds
    WS_MAX_CONNECTIONS: int = 100
    WS_MESSAGE_RATE_LIMIT: int = 10  # Messages per second
    
    # Logging settings
    LOG_LEVEL: str = "INFO"
    LOG_RETENTION_DAYS: int = 30
    
    # Security settings
    SECRET_KEY: str = "your-secret-key-here"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440  # 24 hours

    # Authentication credentials
    BOT_USERNAME: str = os.getenv("BOT_USERNAME", "trader")
    BOT_PASSWORD: str = os.getenv("BOT_PASSWORD", "crypto2024")
    
    # Feature flags
    ENABLE_LIVE_TRADING: bool = False
    ENABLE_PAPER_TRADING: bool = True
    ENABLE_AI_TRAINING: bool = True
    ENABLE_MARKET_MAKING: bool = False
    ENABLE_ARBITRAGE: bool = False
    
    # Performance settings
    MAX_WORKERS: int = 4
    CACHE_TTL: int = 300  # 5 minutes
    
    # Notification settings
    ENABLE_NOTIFICATIONS: bool = True
    NOTIFICATION_CHANNELS: List[str] = ["websocket", "email"]
    
    # Advanced trading features
    ENABLE_PORTFOLIO_REBALANCING: bool = True
    REBALANCING_FREQUENCY: int = 24  # Hours
    ENABLE_DYNAMIC_POSITION_SIZING: bool = True
    ENABLE_SENTIMENT_ANALYSIS: bool = True
    
    # External API settings
    COINMARKETCAP_API_KEY: str = ""
    ALPHA_VANTAGE_API_KEY: str = ""
    
    # Development settings
    DEBUG: bool = False
    TESTING: bool = False
    
    model_config = ConfigDict(env_file=".env", case_sensitive=True)

# Create settings instance
settings = Settings()

# Trading pairs configuration
TRADING_PAIRS_CONFIG = {
    "BTCUSDT": {
        "min_quantity": 0.00001,
        "quantity_precision": 5,
        "price_precision": 2,
        "min_notional": 10.0
    },
    "ETHUSDT": {
        "min_quantity": 0.0001,
        "quantity_precision": 4,
        "price_precision": 2,
        "min_notional": 10.0
    },
    "BNBUSDT": {
        "min_quantity": 0.001,
        "quantity_precision": 3,
        "price_precision": 2,
        "min_notional": 10.0
    },
    "ADAUSDT": {
        "min_quantity": 0.1,
        "quantity_precision": 1,
        "price_precision": 4,
        "min_notional": 10.0
    },
    "SOLUSDT": {
        "min_quantity": 0.001,
        "quantity_precision": 3,
        "price_precision": 2,
        "min_notional": 10.0
    },
    "XRPUSDT": {
        "min_quantity": 0.1,
        "quantity_precision": 1,
        "price_precision": 4,
        "min_notional": 10.0
    },
    "DOTUSDT": {
        "min_quantity": 0.01,
        "quantity_precision": 2,
        "price_precision": 3,
        "min_notional": 10.0
    },
    "DOGEUSDT": {
        "min_quantity": 1,
        "quantity_precision": 0,
        "price_precision": 5,
        "min_notional": 10.0
    },
    "AVAXUSDT": {
        "min_quantity": 0.01,
        "quantity_precision": 2,
        "price_precision": 3,
        "min_notional": 10.0
    },
    "LINKUSDT": {
        "min_quantity": 0.01,
        "quantity_precision": 2,
        "price_precision": 3,
        "min_notional": 10.0
    }
}

# AI Model configuration
AI_MODEL_CONFIG = {
    "lstm": {
        "hidden_size": 128,
        "num_layers": 2,
        "dropout": 0.2,
        "sequence_length": 24,
        "learning_rate": 0.001
    },
    "random_forest": {
        "n_estimators": 100,
        "max_depth": 10,
        "random_state": 42
    },
    "gradient_boosting": {
        "n_estimators": 100,
        "max_depth": 6,
        "learning_rate": 0.1,
        "random_state": 42
    },
    "ensemble_weights": {
        "lstm": 0.5,
        "random_forest": 0.25,
        "gradient_boosting": 0.25
    }
}

# Risk management configuration
RISK_CONFIG = {
    "position_sizing": {
        "method": "kelly_criterion",
        "max_risk_per_trade": 0.02,  # 2% of capital
        "confidence_multiplier": 0.1
    },
    "stop_loss": {
        "method": "atr_based",
        "atr_multiplier": 2.0,
        "max_loss_percentage": 0.02
    },
    "take_profit": {
        "method": "risk_reward_ratio",
        "risk_reward_ratio": 2.0,
        "trailing_stop": True
    },
    "portfolio": {
        "max_correlation": 0.7,
        "diversification_target": 0.8,
        "rebalancing_threshold": 0.05
    }
}

# Market conditions configuration
MARKET_CONDITIONS = {
    "bull_market": {
        "rsi_threshold": 30,
        "volatility_threshold": 0.15,
        "trend_strength": 0.7
    },
    "bear_market": {
        "rsi_threshold": 70,
        "volatility_threshold": 0.25,
        "trend_strength": -0.7
    },
    "sideways_market": {
        "volatility_threshold": 0.10,
        "trend_strength_range": [-0.3, 0.3]
    }
}

def get_pair_config(symbol: str) -> dict:
    """Get configuration for a trading pair"""
    return TRADING_PAIRS_CONFIG.get(symbol, {
        "min_quantity": 0.001,
        "quantity_precision": 3,
        "price_precision": 4,
        "min_notional": 10.0
    })

def validate_settings() -> bool:
    """Validate application settings"""
    required_settings = [
        "DATABASE_URL",
        "DEFAULT_CAPITAL",
        "TOP_CRYPTOCURRENCIES"
    ]
    
    for setting in required_settings:
        if not hasattr(settings, setting):
            raise ValueError(f"Missing required setting: {setting}")
    
    if settings.DEFAULT_CAPITAL <= 0:
        raise ValueError("DEFAULT_CAPITAL must be positive")
    
    if not settings.TOP_CRYPTOCURRENCIES:
        raise ValueError("TOP_CRYPTOCURRENCIES cannot be empty")
    
    return True

# Validate settings on import
validate_settings()
