"""
Centralized API Configuration for AI Crypto Trading Bot
Replace placeholder values with your actual API keys
"""

import os
from typing import Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum

class APIProvider(Enum):
    """API provider enumeration"""
    BINANCE = "binance"
    COINGECKO = "coingecko"
    COINMARKETCAP = "coinmarketcap"
    CRYPTOCOMPARE = "cryptocompare"
    ALPHA_VANTAGE = "alpha_vantage"
    TWELVE_DATA = "twelve_data"
    NEWS_API = "news_api"
    REDDIT = "reddit"
    TWITTER = "twitter"
    FEAR_GREED = "fear_greed"
    WHALE_ALERT = "whale_alert"
    MESSARI = "messari"
    LUNARCRUSH = "lunarcrush"
    DEFIPULSE = "defipulse"
    BLOCKCHAIN_INFO = "blockchain_info"

@dataclass
class APIConfig:
    """API configuration dataclass"""
    api_key: str
    secret_key: Optional[str] = None
    base_url: str = ""
    rate_limit: int = 60  # requests per minute
    timeout: int = 10  # seconds
    enabled: bool = True

# API Configurations - Replace with your actual API keys
API_KEYS = {
    # === TRADING APIs ===
    APIProvider.BINANCE: APIConfig(
        api_key=os.getenv("BINANCE_API_KEY", "your_binance_api_key_here"),
        secret_key=os.getenv("BINANCE_SECRET_KEY", "your_binance_secret_key_here"),
        base_url="https://api.binance.com",
        rate_limit=1200,  # 1200 weight per minute
        timeout=10
    ),

    # === MARKET DATA APIs (FREE) ===
    APIProvider.COINGECKO: APIConfig(
        api_key=os.getenv("COINGECKO_API_KEY", ""),  # Free tier doesn't need key
        base_url="https://api.coingecko.com/api/v3",
        rate_limit=50,  # 50 calls per minute (free)
        timeout=15
    ),

    APIProvider.COINMARKETCAP: APIConfig(
        api_key=os.getenv("COINMARKETCAP_API_KEY", "your_coinmarketcap_api_key_here"),
        base_url="https://pro-api.coinmarketcap.com/v1",
        rate_limit=333,  # ~333 calls per day (free tier)
        timeout=10
    ),

    APIProvider.CRYPTOCOMPARE: APIConfig(
        api_key=os.getenv("CRYPTOCOMPARE_API_KEY", "your_cryptocompare_api_key_here"),
        base_url="https://min-api.cryptocompare.com/data",
        rate_limit=100,  # Generous for free tier
        timeout=10
    ),

    # === TECHNICAL ANALYSIS APIs ===
    APIProvider.ALPHA_VANTAGE: APIConfig(
        api_key=os.getenv("ALPHA_VANTAGE_API_KEY", "your_alpha_vantage_api_key_here"),
        base_url="https://www.alphavantage.co/query",
        rate_limit=5,  # 5 calls per minute (free)
        timeout=15
    ),

    APIProvider.TWELVE_DATA: APIConfig(
        api_key=os.getenv("TWELVE_DATA_API_KEY", "your_twelve_data_api_key_here"),
        base_url="https://api.twelvedata.com",
        rate_limit=8,  # ~800 calls per day (free)
        timeout=10
    ),

    # === NEWS & SENTIMENT APIs ===
    APIProvider.NEWS_API: APIConfig(
        api_key=os.getenv("NEWS_API_KEY", "your_news_api_key_here"),
        base_url="https://newsapi.org/v2",
        rate_limit=16,  # ~1000 calls per day (free)
        timeout=10
    ),

    APIProvider.REDDIT: APIConfig(
        api_key=os.getenv("REDDIT_CLIENT_ID", "your_reddit_client_id_here"),
        secret_key=os.getenv("REDDIT_CLIENT_SECRET", "your_reddit_client_secret_here"),
        base_url="https://www.reddit.com",
        rate_limit=60,  # 60 requests per minute
        timeout=10
    ),

    APIProvider.TWITTER: APIConfig(
        api_key=os.getenv("TWITTER_BEARER_TOKEN", "your_twitter_bearer_token_here"),
        base_url="https://api.twitter.com/2",
        rate_limit=300,  # 300 requests per 15 minutes (free)
        timeout=10
    ),

    # === BLOCKCHAIN & WHALE DATA APIs (FREE) ===
    APIProvider.FEAR_GREED: APIConfig(
        api_key="",  # No key needed
        base_url="https://api.alternative.me/fng",
        rate_limit=60,
        timeout=5
    ),

    APIProvider.BLOCKCHAIN_INFO: APIConfig(
        api_key="",  # No key needed
        base_url="https://api.blockchain.info",
        rate_limit=60,
        timeout=10
    ),

    APIProvider.WHALE_ALERT: APIConfig(
        api_key=os.getenv("WHALE_ALERT_API_KEY", "your_whale_alert_api_key_here"),
        base_url="https://api.whale-alert.io/v1",
        rate_limit=16,  # ~1000 calls per month (free)
        timeout=10
    ),

    # === DEFI & MARKET INTELLIGENCE APIs ===
    APIProvider.MESSARI: APIConfig(
        api_key=os.getenv("MESSARI_API_KEY", ""),  # Free tier doesn't need key
        base_url="https://data.messari.io/api/v1",
        rate_limit=20,  # Conservative for free tier
        timeout=10
    ),

    APIProvider.LUNARCRUSH: APIConfig(
        api_key=os.getenv("LUNARCRUSH_API_KEY", "your_lunarcrush_api_key_here"),
        base_url="https://api.lunarcrush.com/v2",
        rate_limit=100,  # Varies by plan
        timeout=10
    ),

    APIProvider.DEFIPULSE: APIConfig(
        api_key=os.getenv("DEFIPULSE_API_KEY", "your_defipulse_api_key_here"),
        base_url="https://data-api.defipulse.com/api/v1",
        rate_limit=30,
        timeout=10
    ),
}

# API Endpoints Configuration
ENDPOINTS = {
    APIProvider.BINANCE: {
        "price": "/api/v3/ticker/price",
        "klines": "/api/v3/klines",
        "depth": "/api/v3/depth",
        "trades": "/api/v3/trades",
        "account": "/api/v3/account",
        "order": "/api/v3/order",
        "exchange_info": "/api/v3/exchangeInfo",
        "ticker_24hr": "/api/v3/ticker/24hr"
    },

    APIProvider.COINGECKO: {
        "trending": "/search/trending",
        "coins_list": "/coins/list",
        "markets": "/coins/markets",
        "coin_data": "/coins/{id}",
        "price_history": "/coins/{id}/market_chart",
        "global": "/global",
        "categories": "/coins/categories",
        "exchanges": "/exchanges",
        "derivatives": "/derivatives"
    },

    APIProvider.COINMARKETCAP: {
        "listings": "/cryptocurrency/listings/latest",
        "trending": "/cryptocurrency/trending/latest",
        "quotes": "/cryptocurrency/quotes/latest",
        "metadata": "/cryptocurrency/info",
        "gainers_losers": "/cryptocurrency/trending/gainers-losers",
        "ohlcv": "/cryptocurrency/ohlcv/latest"
    },

    APIProvider.CRYPTOCOMPARE: {
        "price": "/price",
        "pricemulti": "/pricemulti",
        "histoday": "/v2/histoday",
        "histohour": "/v2/histohour",
        "social_stats": "/social/coin/general"
    },

    APIProvider.NEWS_API: {
        "everything": "/everything",
        "top_headlines": "/top-headlines"
    },

    APIProvider.REDDIT: {
        "subreddit_hot": "/r/{subreddit}/hot.json",
        "search": "/search.json"
    },

    APIProvider.TWITTER: {
        "search": "/tweets/search/recent",
        "user_tweets": "/users/{id}/tweets"
    },

    APIProvider.WHALE_ALERT: {
        "transactions": "/transactions",
        "status": "/status"
    },

    APIProvider.MESSARI: {
        "assets": "/assets",
        "metrics": "/assets/{asset}/metrics",
        "profile": "/assets/{asset}/profile"
    }
}

# Search Keywords for Hidden Gems Detection
HIDDEN_GEMS_KEYWORDS = [
    # Technical breakthrough keywords
    "breakthrough", "innovation", "upgrade", "mainnet", "testnet",
    "partnership", "collaboration", "integration", "adoption",
    
    # DeFi and Web3 keywords
    "defi", "yield farming", "liquidity mining", "staking", "governance",
    "dao", "nft", "metaverse", "web3", "layer 2", "scaling solution",
    
    # Market sentiment keywords
    "undervalued", "hidden gem", "moonshot", "100x", "altcoin season",
    "bull run", "accumulation", "whale buying", "insider trading",
    
    # Social media trending
    "trending", "viral", "community", "diamond hands", "hodl",
    "to the moon", "rocket", "lambo", "wen moon"
]

# Subreddits to monitor for sentiment
CRYPTO_SUBREDDITS = [
    "CryptoCurrency", "Bitcoin", "ethereum", "altcoin", "CryptoMoonShots",
    "SatoshiStreetBets", "CryptoMarkets", "DeFi", "NFT", "Web3"
]

# Twitter accounts to monitor (crypto influencers)
CRYPTO_TWITTER_ACCOUNTS = [
    "elonmusk", "VitalikButerin", "coinbase", "binance", "cz_binance",
    "aantonop", "naval", "balajis", "satoshilite", "Tyler"
]

def get_api_config(provider: APIProvider) -> APIConfig:
    """Get API configuration for a provider"""
    return API_KEYS.get(provider)

def is_api_enabled(provider: APIProvider) -> bool:
    """Check if an API provider is enabled and configured"""
    config = get_api_config(provider)
    if not config:
        return False
    
    # Check if API key is properly configured (not placeholder)
    if config.api_key and not config.api_key.startswith("your_"):
        return config.enabled
    
    # Some APIs don't need keys (free tier)
    if provider in [APIProvider.COINGECKO, APIProvider.FEAR_GREED, APIProvider.BLOCKCHAIN_INFO]:
        return config.enabled
    
    return False

def get_enabled_apis() -> Dict[APIProvider, APIConfig]:
    """Get all enabled API configurations"""
    return {provider: config for provider, config in API_KEYS.items() 
            if is_api_enabled(provider)}

def validate_api_keys() -> Dict[str, bool]:
    """Validate all API keys and return status"""
    validation_results = {}
    
    for provider, config in API_KEYS.items():
        if provider in [APIProvider.COINGECKO, APIProvider.FEAR_GREED, APIProvider.BLOCKCHAIN_INFO]:
            # Free APIs without keys
            validation_results[provider.value] = True
        else:
            # APIs that require keys
            has_key = bool(config.api_key and not config.api_key.startswith("your_"))
            validation_results[provider.value] = has_key
    
    return validation_results

def get_rate_limited_config(provider: APIProvider) -> tuple[int, int]:
    """Get rate limit configuration (requests, time_window_seconds)"""
    config = get_api_config(provider)
    if not config:
        return 60, 60  # Default: 60 requests per minute
    
    return config.rate_limit, 60  # Most APIs use per-minute limits

# API priority for redundancy (higher number = higher priority)
API_PRIORITY = {
    APIProvider.BINANCE: 10,         # Highest priority for trading
    APIProvider.COINGECKO: 9,        # Best free market data
    APIProvider.COINMARKETCAP: 8,    # Good market data
    APIProvider.CRYPTOCOMPARE: 7,    # Social sentiment data
    APIProvider.MESSARI: 6,          # Fundamental analysis
    APIProvider.FEAR_GREED: 5,       # Market sentiment
    APIProvider.LUNARCRUSH: 4,       # Social analytics
    APIProvider.NEWS_API: 3,         # News sentiment
    APIProvider.REDDIT: 2,           # Social sentiment
    APIProvider.TWITTER: 1,          # Real-time social sentiment
}

def get_fallback_apis(primary_api: APIProvider) -> list[APIProvider]:
    """Get fallback APIs sorted by priority"""
    fallbacks = [(api, priority) for api, priority in API_PRIORITY.items() 
                 if api != primary_api and is_api_enabled(api)]
    
    return [api for api, _ in sorted(fallbacks, key=lambda x: x[1], reverse=True)]

# Required APIs for basic functionality
REQUIRED_APIS = [
    APIProvider.BINANCE,  # For trading
    APIProvider.COINGECKO  # For market data (free)
]

def check_minimum_requirements() -> bool:
    """Check if minimum required APIs are available"""
    return all(is_api_enabled(api) for api in REQUIRED_APIS)

# Export main configuration
__all__ = [
    'APIProvider', 'APIConfig', 'API_KEYS', 'ENDPOINTS',
    'get_api_config', 'is_api_enabled', 'get_enabled_apis',
    'validate_api_keys', 'check_minimum_requirements',
    'HIDDEN_GEMS_KEYWORDS', 'CRYPTO_SUBREDDITS', 'CRYPTO_TWITTER_ACCOUNTS'
]
