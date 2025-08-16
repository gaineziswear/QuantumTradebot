import asyncio
import aiohttp
import hmac
import hashlib
import time
import json
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from urllib.parse import urlencode
from loguru import logger

from config import settings, get_pair_config, TRADING_PAIRS_CONFIG

class BinanceClient:
    """Advanced Binance API client with hedge fund-grade features"""
    
    def __init__(self, api_key: str = "", api_secret: str = "", testnet: bool = True):
        self.api_key = api_key or (settings.BINANCE_TESTNET_API_KEY if testnet else settings.BINANCE_API_KEY)
        self.api_secret = api_secret or (settings.BINANCE_TESTNET_SECRET_KEY if testnet else settings.BINANCE_SECRET_KEY)
        self.testnet = testnet
        
        # API endpoints
        if testnet:
            self.base_url = "https://testnet.binance.vision"
            self.ws_url = "wss://testnet.binance.vision/ws"
        else:
            self.base_url = "https://api.binance.com"
            self.ws_url = "wss://stream.binance.com:9443/ws"
        
        # Rate limiting
        self.rate_limit_weight = 0
        self.rate_limit_reset = time.time() + 60
        self.max_weight = 1200  # Per minute
        
        # Session management
        self.session = None
        self.is_connected = False
        
        # Trading state
        self.account_info = {}
        self.open_orders = {}
        self.positions = {}
        self.balances = {}
        
        # Risk management
        self.max_order_value = settings.DEFAULT_CAPITAL * settings.MAX_POSITION_SIZE
        self.trading_enabled = True
        
        logger.info(f"Binance client initialized - {'Testnet' if testnet else 'Live'} mode")
    
    async def __aenter__(self):
        """Async context manager entry"""
        await self.connect()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.disconnect()
    
    async def connect(self):
        """Initialize connection"""
        if self.session is None:
            timeout = aiohttp.ClientTimeout(total=30)
            self.session = aiohttp.ClientSession(timeout=timeout)
        
        # Test connection
        try:
            server_time = await self.get_server_time()
            if server_time:
                self.is_connected = True
                logger.info("Connected to Binance API successfully")
                
                # Load account info
                await self.update_account_info()
            else:
                raise Exception("Failed to get server time")
        except Exception as e:
            logger.error(f"Failed to connect to Binance: {e}")
            self.is_connected = False
            raise
    
    async def disconnect(self):
        """Close connection"""
        if self.session:
            await self.session.close()
            self.session = None
        self.is_connected = False
        logger.info("Disconnected from Binance API")
    
    def _get_signature(self, params: str) -> str:
        """Generate HMAC signature"""
        return hmac.new(
            self.api_secret.encode('utf-8'),
            params.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
    
    async def _request(self, method: str, endpoint: str, params: Dict = None, signed: bool = False) -> Dict:
        """Make HTTP request to Binance API with rate limiting"""
        if not self.session:
            await self.connect()
        
        # Rate limiting check
        if self.rate_limit_weight >= self.max_weight:
            if time.time() < self.rate_limit_reset:
                wait_time = self.rate_limit_reset - time.time()
                logger.warning(f"Rate limit reached, waiting {wait_time:.2f}s")
                await asyncio.sleep(wait_time)
            
            self.rate_limit_weight = 0
            self.rate_limit_reset = time.time() + 60
        
        url = f"{self.base_url}{endpoint}"
        headers = {}
        
        if params is None:
            params = {}
        
        if signed:
            params['timestamp'] = int(time.time() * 1000)
            if self.api_key:
                headers['X-MBX-APIKEY'] = self.api_key
            
            query_string = urlencode(params)
            signature = self._get_signature(query_string)
            params['signature'] = signature
        
        try:
            if method == 'GET':
                response = await self.session.get(url, params=params, headers=headers)
            elif method == 'POST':
                response = await self.session.post(url, data=params, headers=headers)
            elif method == 'DELETE':
                response = await self.session.delete(url, params=params, headers=headers)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
            
            # Update rate limit counter
            self.rate_limit_weight += 1
            
            data = await response.json()
            
            if response.status != 200:
                logger.error(f"Binance API error: {data}")
                raise Exception(f"API Error: {data.get('msg', 'Unknown error')}")
            
            return data
        
        except Exception as e:
            logger.error(f"Request failed: {e}")
            raise
    
    async def get_server_time(self) -> Optional[int]:
        """Get Binance server time"""
        try:
            data = await self._request('GET', '/api/v3/time')
            return data.get('serverTime')
        except Exception as e:
            logger.error(f"Failed to get server time: {e}")
            return None
    
    async def get_exchange_info(self) -> Dict:
        """Get exchange trading rules and symbol information"""
        try:
            return await self._request('GET', '/api/v3/exchangeInfo')
        except Exception as e:
            logger.error(f"Failed to get exchange info: {e}")
            return {}
    
    async def get_ticker_prices(self, symbols: List[str] = None) -> List[Dict]:
        """Get current ticker prices"""
        try:
            data = await self._request('GET', '/api/v3/ticker/price')
            
            if symbols:
                # Filter for requested symbols
                return [item for item in data if item['symbol'] in symbols]
            
            return data
        except Exception as e:
            logger.error(f"Failed to get ticker prices: {e}")
            return []
    
    async def get_24hr_ticker(self, symbols: List[str] = None) -> List[Dict]:
        """Get 24hr ticker statistics"""
        try:
            data = await self._request('GET', '/api/v3/ticker/24hr')
            
            if symbols:
                return [item for item in data if item['symbol'] in symbols]
            
            return data
        except Exception as e:
            logger.error(f"Failed to get 24hr ticker: {e}")
            return []
    
    async def get_historical_klines(self, symbol: str, interval: str = '1h', limit: int = 1000, 
                                   start_time: Optional[int] = None, end_time: Optional[int] = None) -> pd.DataFrame:
        """Get historical kline/candlestick data"""
        try:
            params = {
                'symbol': symbol,
                'interval': interval,
                'limit': min(limit, 1000)  # Binance limit
            }
            
            if start_time:
                params['startTime'] = start_time
            if end_time:
                params['endTime'] = end_time
            
            data = await self._request('GET', '/api/v3/klines', params)
            
            # Convert to DataFrame
            df = pd.DataFrame(data, columns=[
                'timestamp', 'open', 'high', 'low', 'close', 'volume',
                'close_time', 'quote_asset_volume', 'number_of_trades',
                'taker_buy_base_asset_volume', 'taker_buy_quote_asset_volume', 'ignore'
            ])
            
            # Convert data types
            numeric_columns = ['open', 'high', 'low', 'close', 'volume', 'quote_asset_volume']
            for col in numeric_columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
            
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            df['symbol'] = symbol
            
            # Keep only essential columns
            df = df[['timestamp', 'symbol', 'open', 'high', 'low', 'close', 'volume']]
            
            return df
        
        except Exception as e:
            logger.error(f"Failed to get historical data for {symbol}: {e}")
            return pd.DataFrame()
    
    async def download_all_historical_data(self, symbols: List[str] = None, 
                                         days: int = 365, interval: str = '1h') -> Dict[str, pd.DataFrame]:
        """Download comprehensive historical data for all trading pairs"""
        if symbols is None:
            symbols = settings.TOP_CRYPTOCURRENCIES
        
        logger.info(f"Downloading {days} days of historical data for {len(symbols)} symbols")
        
        all_data = {}
        end_time = int(time.time() * 1000)
        start_time = end_time - (days * 24 * 60 * 60 * 1000)  # Convert days to milliseconds
        
        for symbol in symbols:
            try:
                logger.info(f"Downloading data for {symbol}")
                
                # Download data in chunks to handle large datasets
                all_chunks = []
                current_start = start_time
                
                while current_start < end_time:
                    current_end = min(current_start + (1000 * 60 * 60 * 1000), end_time)  # 1000 hours max per request
                    
                    df = await self.get_historical_klines(
                        symbol=symbol,
                        interval=interval,
                        limit=1000,
                        start_time=current_start,
                        end_time=current_end
                    )
                    
                    if not df.empty:
                        all_chunks.append(df)
                    
                    current_start = current_end
                    
                    # Rate limiting
                    await asyncio.sleep(0.1)
                
                if all_chunks:
                    combined_df = pd.concat(all_chunks, ignore_index=True)
                    combined_df = combined_df.drop_duplicates(subset=['timestamp']).sort_values('timestamp')
                    all_data[symbol] = combined_df
                    
                    logger.info(f"Downloaded {len(combined_df)} data points for {symbol}")
                else:
                    logger.warning(f"No data downloaded for {symbol}")
            
            except Exception as e:
                logger.error(f"Failed to download data for {symbol}: {e}")
                continue
        
        logger.info(f"Historical data download completed. Total symbols: {len(all_data)}")
        return all_data
    
    async def update_account_info(self) -> Dict:
        """Update and return account information"""
        try:
            if not self.api_key or not self.api_secret:
                logger.warning("No API credentials provided, using mock account info")
                self.account_info = {
                    'canTrade': True,
                    'canWithdraw': False,
                    'canDeposit': False,
                    'updateTime': int(time.time() * 1000),
                    'accountType': 'SPOT',
                    'balances': [
                        {'asset': 'USDT', 'free': str(settings.DEFAULT_CAPITAL), 'locked': '0.0'}
                    ]
                }
                return self.account_info
            
            self.account_info = await self._request('GET', '/api/v3/account', signed=True)
            
            # Update balances
            self.balances = {}
            for balance in self.account_info.get('balances', []):
                asset = balance['asset']
                free = float(balance['free'])
                locked = float(balance['locked'])
                
                if free > 0 or locked > 0:
                    self.balances[asset] = {
                        'free': free,
                        'locked': locked,
                        'total': free + locked
                    }
            
            return self.account_info
        
        except Exception as e:
            logger.error(f"Failed to update account info: {e}")
            return {}
    
    async def get_open_orders(self, symbol: str = None) -> List[Dict]:
        """Get open orders"""
        try:
            params = {}
            if symbol:
                params['symbol'] = symbol
            
            orders = await self._request('GET', '/api/v3/openOrders', params, signed=True)
            self.open_orders = {order['orderId']: order for order in orders}
            return orders
        
        except Exception as e:
            logger.error(f"Failed to get open orders: {e}")
            return []
    
    async def place_market_order(self, symbol: str, side: str, quantity: float, 
                               test_order: bool = None) -> Dict:
        """Place a market order"""
        try:
            if test_order is None:
                test_order = self.testnet
            
            # Validate order parameters
            pair_config = get_pair_config(symbol)
            
            # Round quantity to proper precision
            quantity = round(quantity, pair_config['quantity_precision'])
            
            # Check minimum quantity
            if quantity < pair_config['min_quantity']:
                raise ValueError(f"Quantity {quantity} below minimum {pair_config['min_quantity']} for {symbol}")
            
            # Check minimum notional value
            current_price = await self.get_symbol_price(symbol)
            notional = quantity * current_price
            
            if notional < pair_config['min_notional']:
                raise ValueError(f"Order value {notional} below minimum {pair_config['min_notional']} for {symbol}")
            
            # Risk management check
            if notional > self.max_order_value:
                raise ValueError(f"Order value {notional} exceeds maximum allowed {self.max_order_value}")
            
            params = {
                'symbol': symbol,
                'side': side.upper(),
                'type': 'MARKET',
                'quantity': str(quantity)
            }
            
            # Use test endpoint if in test mode
            endpoint = '/api/v3/order/test' if test_order else '/api/v3/order'
            
            order = await self._request('POST', endpoint, params, signed=True)
            
            logger.info(f"Market order placed: {side} {quantity} {symbol}")
            return order
        
        except Exception as e:
            logger.error(f"Failed to place market order: {e}")
            raise
    
    async def place_limit_order(self, symbol: str, side: str, quantity: float, price: float,
                              time_in_force: str = 'GTC', test_order: bool = None) -> Dict:
        """Place a limit order"""
        try:
            if test_order is None:
                test_order = self.testnet
            
            pair_config = get_pair_config(symbol)
            
            # Round to proper precision
            quantity = round(quantity, pair_config['quantity_precision'])
            price = round(price, pair_config['price_precision'])
            
            # Validate minimum requirements
            if quantity < pair_config['min_quantity']:
                raise ValueError(f"Quantity {quantity} below minimum {pair_config['min_quantity']}")
            
            notional = quantity * price
            if notional < pair_config['min_notional']:
                raise ValueError(f"Order value {notional} below minimum {pair_config['min_notional']}")
            
            if notional > self.max_order_value:
                raise ValueError(f"Order value {notional} exceeds maximum allowed {self.max_order_value}")
            
            params = {
                'symbol': symbol,
                'side': side.upper(),
                'type': 'LIMIT',
                'timeInForce': time_in_force,
                'quantity': str(quantity),
                'price': str(price)
            }
            
            endpoint = '/api/v3/order/test' if test_order else '/api/v3/order'
            order = await self._request('POST', endpoint, params, signed=True)
            
            logger.info(f"Limit order placed: {side} {quantity} {symbol} @ {price}")
            return order
        
        except Exception as e:
            logger.error(f"Failed to place limit order: {e}")
            raise
    
    async def place_stop_loss_order(self, symbol: str, side: str, quantity: float, 
                                   stop_price: float, test_order: bool = None) -> Dict:
        """Place a stop loss order"""
        try:
            if test_order is None:
                test_order = self.testnet
            
            pair_config = get_pair_config(symbol)
            
            quantity = round(quantity, pair_config['quantity_precision'])
            stop_price = round(stop_price, pair_config['price_precision'])
            
            params = {
                'symbol': symbol,
                'side': side.upper(),
                'type': 'STOP_LOSS_LIMIT',
                'timeInForce': 'GTC',
                'quantity': str(quantity),
                'price': str(stop_price),
                'stopPrice': str(stop_price)
            }
            
            endpoint = '/api/v3/order/test' if test_order else '/api/v3/order'
            order = await self._request('POST', endpoint, params, signed=True)
            
            logger.info(f"Stop loss order placed: {side} {quantity} {symbol} @ {stop_price}")
            return order
        
        except Exception as e:
            logger.error(f"Failed to place stop loss order: {e}")
            raise
    
    async def cancel_order(self, symbol: str, order_id: int) -> Dict:
        """Cancel an order"""
        try:
            params = {
                'symbol': symbol,
                'orderId': order_id
            }
            
            result = await self._request('DELETE', '/api/v3/order', params, signed=True)
            
            if order_id in self.open_orders:
                del self.open_orders[order_id]
            
            logger.info(f"Order {order_id} cancelled for {symbol}")
            return result
        
        except Exception as e:
            logger.error(f"Failed to cancel order {order_id}: {e}")
            raise
    
    async def cancel_all_orders(self, symbol: str) -> List[Dict]:
        """Cancel all open orders for a symbol"""
        try:
            params = {'symbol': symbol}
            result = await self._request('DELETE', '/api/v3/openOrders', params, signed=True)
            
            # Update local orders
            self.open_orders = {k: v for k, v in self.open_orders.items() if v['symbol'] != symbol}
            
            logger.info(f"All orders cancelled for {symbol}")
            return result
        
        except Exception as e:
            logger.error(f"Failed to cancel all orders for {symbol}: {e}")
            return []
    
    async def get_symbol_price(self, symbol: str) -> float:
        """Get current price for a symbol"""
        try:
            data = await self._request('GET', '/api/v3/ticker/price', {'symbol': symbol})
            return float(data['price'])
        except Exception as e:
            logger.error(f"Failed to get price for {symbol}: {e}")
            return 0.0
    
    async def get_order_book(self, symbol: str, limit: int = 100) -> Dict:
        """Get order book depth"""
        try:
            params = {'symbol': symbol, 'limit': limit}
            return await self._request('GET', '/api/v3/depth', params)
        except Exception as e:
            logger.error(f"Failed to get order book for {symbol}: {e}")
            return {}
    
    async def get_recent_trades(self, symbol: str, limit: int = 500) -> List[Dict]:
        """Get recent trades"""
        try:
            params = {'symbol': symbol, 'limit': limit}
            return await self._request('GET', '/api/v3/trades', params)
        except Exception as e:
            logger.error(f"Failed to get recent trades for {symbol}: {e}")
            return []
    
    async def calculate_portfolio_value(self) -> Dict[str, float]:
        """Calculate total portfolio value in USDT"""
        try:
            await self.update_account_info()
            
            total_value = 0.0
            asset_values = {}
            
            for asset, balance_info in self.balances.items():
                balance = balance_info['total']
                
                if asset == 'USDT':
                    value = balance
                else:
                    # Get price in USDT
                    symbol = f"{asset}USDT"
                    try:
                        price = await self.get_symbol_price(symbol)
                        value = balance * price
                    except:
                        # If pair doesn't exist, skip
                        continue
                
                asset_values[asset] = value
                total_value += value
            
            return {
                'total_value_usdt': total_value,
                'asset_values': asset_values,
                'last_updated': datetime.utcnow().isoformat()
            }
        
        except Exception as e:
            logger.error(f"Failed to calculate portfolio value: {e}")
            return {'total_value_usdt': 0.0, 'asset_values': {}}
    
    async def get_trading_fees(self, symbol: str = None) -> Dict:
        """Get trading fees"""
        try:
            params = {}
            if symbol:
                params['symbol'] = symbol
            
            return await self._request('GET', '/api/v3/tradeFee', params, signed=True)
        except Exception as e:
            logger.error(f"Failed to get trading fees: {e}")
            return {}
    
    async def enable_trading(self):
        """Enable trading"""
        self.trading_enabled = True
        logger.info("Trading enabled")
    
    async def disable_trading(self):
        """Disable trading"""
        self.trading_enabled = False
        logger.info("Trading disabled")
    
    async def switch_to_live_mode(self):
        """Switch to live trading mode"""
        if self.testnet:
            logger.warning("Switching to LIVE trading mode!")
            self.testnet = False
            self.base_url = "https://api.binance.com"
            self.ws_url = "wss://stream.binance.com:9443/ws"
            self.api_key = settings.BINANCE_API_KEY
            self.api_secret = settings.BINANCE_SECRET_KEY
            
            # Reconnect with live credentials
            await self.disconnect()
            await self.connect()
            
            logger.info("Switched to LIVE trading mode")
    
    async def switch_to_testnet_mode(self):
        """Switch to testnet mode"""
        if not self.testnet:
            logger.info("Switching to TESTNET mode")
            self.testnet = True
            self.base_url = "https://testnet.binance.vision"
            self.ws_url = "wss://testnet.binance.vision/ws"
            self.api_key = settings.BINANCE_TESTNET_API_KEY
            self.api_secret = settings.BINANCE_TESTNET_SECRET_KEY
            
            await self.disconnect()
            await self.connect()
            
            logger.info("Switched to TESTNET mode")
    
    def get_connection_status(self) -> Dict[str, Any]:
        """Get connection status and statistics"""
        return {
            'is_connected': self.is_connected,
            'testnet_mode': self.testnet,
            'trading_enabled': self.trading_enabled,
            'rate_limit_weight': self.rate_limit_weight,
            'rate_limit_reset': self.rate_limit_reset,
            'open_orders_count': len(self.open_orders),
            'balances_count': len(self.balances),
            'last_update': datetime.utcnow().isoformat()
        }
