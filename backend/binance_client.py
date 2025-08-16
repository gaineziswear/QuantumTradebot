import asyncio
import aiohttp
import hmac
import hashlib
import time
from typing import Dict, List, Optional, Any
from decimal import Decimal
from datetime import datetime, timedelta

from binance.client import Client
from binance.exceptions import BinanceAPIException
from loguru import logger
import pandas as pd

from config import settings

class BinanceClient:
    """Enhanced Binance API client for trading and data collection"""
    
    def __init__(self, api_key: Optional[str] = None, api_secret: Optional[str] = None, testnet: bool = True):
        self.api_key = api_key
        self.api_secret = api_secret
        self.testnet = testnet
        
        # Initialize Binance client
        if api_key and api_secret:
            self.client = Client(
                api_key=api_key,
                api_secret=api_secret,
                testnet=testnet
            )
        else:
            # Use public API only
            self.client = Client(testnet=testnet)
        
        self.session = None
        self.last_request_time = {}
        self.rate_limit_weights = {}
    
    async def __aenter__(self):
        """Async context manager entry"""
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()
    
    async def get_exchange_info(self) -> Dict[str, Any]:
        """Get exchange trading rules and symbol information"""
        try:
            return self.client.get_exchange_info()
        except BinanceAPIException as e:
            logger.error(f"Failed to get exchange info: {e}")
            raise
    
    async def get_ticker_prices(self, symbols: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """Get current ticker prices"""
        try:
            tickers = self.client.get_all_tickers()
            if symbols:
                return [ticker for ticker in tickers if ticker['symbol'] in symbols]
            return tickers
        except BinanceAPIException as e:
            logger.error(f"Failed to get ticker prices: {e}")
            raise
    
    async def get_order_book(self, symbol: str, limit: int = 100) -> Dict[str, Any]:
        """Get order book depth"""
        try:
            return self.client.get_order_book(symbol=symbol, limit=limit)
        except BinanceAPIException as e:
            logger.error(f"Failed to get order book for {symbol}: {e}")
            raise
    
    async def get_historical_klines(
        self,
        symbol: str,
        interval: str = "1h",
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: int = 1000
    ) -> List[List]:
        """Get historical kline/candlestick data"""
        try:
            start_str = int(start_time.timestamp() * 1000) if start_time else None
            end_str = int(end_time.timestamp() * 1000) if end_time else None
            
            klines = self.client.get_historical_klines(
                symbol=symbol,
                interval=interval,
                start_str=start_str,
                end_str=end_str,
                limit=limit
            )
            return klines
        except BinanceAPIException as e:
            logger.error(f"Failed to get historical klines for {symbol}: {e}")
            raise
    
    async def download_all_historical_data(self, symbols: List[str], days: int = 365) -> Dict[str, pd.DataFrame]:
        """Download comprehensive historical data for multiple symbols"""
        logger.info(f"Starting download of {days} days of data for {len(symbols)} symbols")
        
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(days=days)
        
        all_data = {}
        
        for symbol in symbols:
            try:
                logger.info(f"Downloading data for {symbol}")
                
                # Get hourly data
                klines = await self.get_historical_klines(
                    symbol=symbol,
                    interval="1h",
                    start_time=start_time,
                    end_time=end_time,
                    limit=1000
                )
                
                if klines:
                    df = pd.DataFrame(klines, columns=[
                        'timestamp', 'open', 'high', 'low', 'close', 'volume',
                        'close_time', 'quote_asset_volume', 'number_of_trades',
                        'taker_buy_base_asset_volume', 'taker_buy_quote_asset_volume',
                        'ignore'
                    ])
                    
                    # Convert to proper data types
                    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
                    for col in ['open', 'high', 'low', 'close', 'volume']:
                        df[col] = pd.to_numeric(df[col])
                    
                    df = df[['timestamp', 'open', 'high', 'low', 'close', 'volume']]
                    all_data[symbol] = df
                    
                    logger.info(f"Downloaded {len(df)} data points for {symbol}")
                
                # Rate limiting
                await asyncio.sleep(0.1)
                
            except Exception as e:
                logger.error(f"Failed to download data for {symbol}: {e}")
                continue
        
        logger.info(f"Completed data download for {len(all_data)} symbols")
        return all_data
    
    async def get_account_info(self) -> Dict[str, Any]:
        """Get account information"""
        try:
            return self.client.get_account()
        except BinanceAPIException as e:
            logger.error(f"Failed to get account info: {e}")
            raise
    
    async def get_balances(self) -> List[Dict[str, str]]:
        """Get account balances"""
        try:
            account = await self.get_account_info()
            return account['balances']
        except BinanceAPIException as e:
            logger.error(f"Failed to get balances: {e}")
            raise
    
    async def place_order(
        self,
        symbol: str,
        side: str,
        order_type: str,
        quantity: float,
        price: Optional[float] = None,
        time_in_force: str = "GTC",
        stop_price: Optional[float] = None
    ) -> Dict[str, Any]:
        """Place a trading order"""
        try:
            order_params = {
                'symbol': symbol,
                'side': side,
                'type': order_type,
                'quantity': quantity,
                'timeInForce': time_in_force
            }
            
            if price:
                order_params['price'] = price
            if stop_price:
                order_params['stopPrice'] = stop_price
            
            if self.testnet:
                logger.info(f"TESTNET ORDER: {order_params}")
                # Simulate order response for testnet
                return {
                    'symbol': symbol,
                    'orderId': int(time.time() * 1000),
                    'orderListId': -1,
                    'clientOrderId': f"test_{int(time.time())}",
                    'transactTime': int(time.time() * 1000),
                    'price': str(price) if price else '0.00000000',
                    'origQty': str(quantity),
                    'executedQty': str(quantity),
                    'cummulativeQuoteQty': str(quantity * (price or 0)),
                    'status': 'FILLED',
                    'timeInForce': time_in_force,
                    'type': order_type,
                    'side': side
                }
            else:
                return self.client.create_order(**order_params)
        
        except BinanceAPIException as e:
            logger.error(f"Failed to place order: {e}")
            raise
    
    async def cancel_order(self, symbol: str, order_id: int) -> Dict[str, Any]:
        """Cancel an existing order"""
        try:
            return self.client.cancel_order(symbol=symbol, orderId=order_id)
        except BinanceAPIException as e:
            logger.error(f"Failed to cancel order {order_id}: {e}")
            raise
    
    async def get_open_orders(self, symbol: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get open orders"""
        try:
            return self.client.get_open_orders(symbol=symbol)
        except BinanceAPIException as e:
            logger.error(f"Failed to get open orders: {e}")
            raise
    
    async def get_order_history(self, symbol: str, limit: int = 100) -> List[Dict[str, Any]]:
        """Get order history"""
        try:
            return self.client.get_all_orders(symbol=symbol, limit=limit)
        except BinanceAPIException as e:
            logger.error(f"Failed to get order history for {symbol}: {e}")
            raise
    
    async def get_trade_history(self, symbol: str, limit: int = 100) -> List[Dict[str, Any]]:
        """Get trade history"""
        try:
            return self.client.get_my_trades(symbol=symbol, limit=limit)
        except BinanceAPIException as e:
            logger.error(f"Failed to get trade history for {symbol}: {e}")
            raise
    
    async def calculate_portfolio_value(self) -> Dict[str, Any]:
        """Calculate total portfolio value in USDT"""
        try:
            balances = await self.get_balances()
            tickers = await self.get_ticker_prices()
            
            # Create ticker price lookup
            price_lookup = {ticker['symbol']: float(ticker['price']) for ticker in tickers}
            
            total_value = 0.0
            portfolio = []
            
            for balance in balances:
                asset = balance['asset']
                free = float(balance['free'])
                locked = float(balance['locked'])
                total_balance = free + locked
                
                if total_balance > 0:
                    if asset == 'USDT':
                        value_usdt = total_balance
                    else:
                        symbol = f"{asset}USDT"
                        price = price_lookup.get(symbol, 0)
                        value_usdt = total_balance * price
                    
                    if value_usdt > 0.01:  # Only include assets worth more than $0.01
                        portfolio.append({
                            'asset': asset,
                            'balance': total_balance,
                            'value_usdt': value_usdt,
                            'percentage': 0  # Will be calculated after total
                        })
                        total_value += value_usdt
            
            # Calculate percentages
            for item in portfolio:
                item['percentage'] = (item['value_usdt'] / total_value) * 100 if total_value > 0 else 0
            
            return {
                'total_value_usdt': total_value,
                'portfolio': portfolio,
                'last_updated': datetime.utcnow().isoformat()
            }
        
        except Exception as e:
            logger.error(f"Failed to calculate portfolio value: {e}")
            raise
    
    def is_testnet_mode(self) -> bool:
        """Check if running in testnet mode"""
        return self.testnet
    
    async def health_check(self) -> bool:
        """Check if Binance API is accessible"""
        try:
            self.client.ping()
            return True
        except Exception as e:
            logger.error(f"Binance API health check failed: {e}")
            return False
