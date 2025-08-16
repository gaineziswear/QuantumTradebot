/**
 * Centralized API Configuration
 * Replace placeholders with your actual API keys
 */

export const API_KEYS = {
  // Binance API (Required for trading)
  BINANCE: {
    API_KEY: process.env.BINANCE_API_KEY || 'your_binance_api_key_here',
    SECRET_KEY: process.env.BINANCE_SECRET_KEY || 'your_binance_secret_key_here',
    TESTNET: process.env.BINANCE_TESTNET === 'true' || true, // Use testnet by default
  },

  // CoinGecko API (Free - for market data and hidden gems)
  COINGECKO: {
    API_KEY: process.env.COINGECKO_API_KEY || '', // Free tier doesn't need key
    BASE_URL: 'https://api.coingecko.com/api/v3',
    PRO_URL: 'https://pro-api.coingecko.com/api/v3', // If you upgrade to pro
  },

  // CoinMarketCap API (Free tier available)
  COINMARKETCAP: {
    API_KEY: process.env.COINMARKETCAP_API_KEY || 'your_coinmarketcap_api_key_here',
    BASE_URL: 'https://pro-api.coinmarketcap.com/v1',
    SANDBOX_URL: 'https://sandbox-api.coinmarketcap.com/v1',
  },

  // CryptoCompare API (Free tier available)
  CRYPTOCOMPARE: {
    API_KEY: process.env.CRYPTOCOMPARE_API_KEY || 'your_cryptocompare_api_key_here',
    BASE_URL: 'https://min-api.cryptocompare.com/data',
  },

  // Alpha Vantage (Free tier for technical indicators)
  ALPHA_VANTAGE: {
    API_KEY: process.env.ALPHA_VANTAGE_API_KEY || 'your_alpha_vantage_api_key_here',
    BASE_URL: 'https://www.alphavantage.co/query',
  },

  // Twelve Data (Free tier for advanced technical analysis)
  TWELVE_DATA: {
    API_KEY: process.env.TWELVE_DATA_API_KEY || 'your_twelve_data_api_key_here',
    BASE_URL: 'https://api.twelvedata.com',
  },

  // NewsAPI (Free tier for sentiment analysis)
  NEWS_API: {
    API_KEY: process.env.NEWS_API_KEY || 'your_news_api_key_here',
    BASE_URL: 'https://newsapi.org/v2',
  },

  // Reddit API (Free - for social sentiment)
  REDDIT: {
    CLIENT_ID: process.env.REDDIT_CLIENT_ID || 'your_reddit_client_id_here',
    CLIENT_SECRET: process.env.REDDIT_CLIENT_SECRET || 'your_reddit_client_secret_here',
    USER_AGENT: 'AI-Crypto-Trading-Bot/1.0',
  },

  // Twitter API v2 (Free tier available)
  TWITTER: {
    BEARER_TOKEN: process.env.TWITTER_BEARER_TOKEN || 'your_twitter_bearer_token_here',
    BASE_URL: 'https://api.twitter.com/2',
  },

  // Fear & Greed Index (Free)
  FEAR_GREED: {
    BASE_URL: 'https://api.alternative.me/fng/',
  },

  // Blockchain.info API (Free)
  BLOCKCHAIN_INFO: {
    BASE_URL: 'https://api.blockchain.info',
  },

  // Whale Alert API (Free tier)
  WHALE_ALERT: {
    API_KEY: process.env.WHALE_ALERT_API_KEY || 'your_whale_alert_api_key_here',
    BASE_URL: 'https://api.whale-alert.io/v1',
  },

  // DefiPulse API (Free tier)
  DEFIPULSE: {
    API_KEY: process.env.DEFIPULSE_API_KEY || 'your_defipulse_api_key_here',
    BASE_URL: 'https://data-api.defipulse.com/api/v1',
  },

  // Messari API (Free tier)
  MESSARI: {
    API_KEY: process.env.MESSARI_API_KEY || '', // Free tier doesn't need key
    BASE_URL: 'https://data.messari.io/api/v1',
  },

  // LunarCrush API (Free tier for social analytics)
  LUNARCRUSH: {
    API_KEY: process.env.LUNARCRUSH_API_KEY || 'your_lunarcrush_api_key_here',
    BASE_URL: 'https://api.lunarcrush.com/v2',
  },
};

// API Rate Limits (requests per minute)
export const RATE_LIMITS = {
  BINANCE: {
    WEIGHT_LIMIT: 1200, // per minute
    ORDER_LIMIT: 10, // per second
  },
  COINGECKO: {
    FREE: 50, // per minute
    PRO: 500, // per minute
  },
  COINMARKETCAP: {
    FREE: 333, // per day (10,000 per month)
    BASIC: 1000, // per day
  },
  CRYPTOCOMPARE: {
    FREE: 100000, // per month
  },
  ALPHA_VANTAGE: {
    FREE: 5, // per minute (500 per day)
  },
  TWELVE_DATA: {
    FREE: 800, // per day
  },
  NEWS_API: {
    FREE: 1000, // per day
  },
  TWITTER: {
    FREE: 300, // per 15 minutes
  },
  WHALE_ALERT: {
    FREE: 1000, // per month
  },
};

// API Endpoints Configuration
export const ENDPOINTS = {
  BINANCE: {
    SPOT_PRICE: '/api/v3/ticker/price',
    KLINES: '/api/v3/klines',
    ORDERBOOK: '/api/v3/depth',
    TRADES: '/api/v3/trades',
    ACCOUNT: '/api/v3/account',
    NEW_ORDER: '/api/v3/order',
    EXCHANGE_INFO: '/api/v3/exchangeInfo',
  },
  
  COINGECKO: {
    TRENDING: '/search/trending',
    COINS_LIST: '/coins/list',
    MARKET_DATA: '/coins/markets',
    COIN_DATA: '/coins/{id}',
    PRICE_HISTORY: '/coins/{id}/market_chart',
    GLOBAL_DATA: '/global',
  },

  COINMARKETCAP: {
    LATEST_LISTINGS: '/cryptocurrency/listings/latest',
    TRENDING: '/cryptocurrency/trending/latest',
    QUOTES: '/cryptocurrency/quotes/latest',
    METADATA: '/cryptocurrency/info',
    GAINERS_LOSERS: '/cryptocurrency/trending/gainers-losers',
  },

  NEWS_API: {
    EVERYTHING: '/everything',
    TOP_HEADLINES: '/top-headlines',
  },

  REDDIT: {
    SUBREDDIT_HOT: '/r/{subreddit}/hot.json',
    SEARCH: '/search.json',
  },

  TWITTER: {
    SEARCH: '/tweets/search/recent',
    USER_TWEETS: '/users/{id}/tweets',
  },
};

// Validation function to check if required API keys are present
export function validateAPIKeys(): { valid: boolean; missing: string[] } {
  const required = [
    'BINANCE_API_KEY',
    'BINANCE_SECRET_KEY',
  ];

  const missing = required.filter(key => {
    const value = process.env[key];
    return !value || value.includes('your_') || value === '';
  });

  return {
    valid: missing.length === 0,
    missing
  };
}

// Helper function to get API configuration
export function getAPIConfig(service: keyof typeof API_KEYS) {
  return API_KEYS[service];
}

// Helper function to check rate limits
export function getRateLimit(service: keyof typeof RATE_LIMITS) {
  return RATE_LIMITS[service];
}

export default API_KEYS;
