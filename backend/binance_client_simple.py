"""
Simplified Binance client for testing without full dependencies
"""
import asyncio
import random
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import pandas as pd
from loguru import logger

class BinanceClient:
    """Simplified Binance API client for demo/testing"""
    
    def __init__(self, api_key: Optional[str] = None, api_secret: Optional[str] = None, testnet: bool = True):
        self.api_key = api_key
        self.api_secret = api_secret
        self.testnet = testnet
        
        # Mock data for testing
        self.symbols = [
            "BTCUSDT", "ETHUSDT", "BNBUSDT", "ADAUSDT", "SOLUSDT",
            "XRPUSDT", "DOTUSDT", "DOGEUSDT", "AVAXUSDT", "LINKUSDT"
        ]
        
        # Mock prices (will be updated with random variations)
        self.mock_prices = {
            "BTCUSDT": 45000.0,
            "ETHUSDT": 2500.0,
            "BNBUSDT": 300.0,
            "ADAUSDT": 0.5,
            "SOLUSDT": 100.0,
            "XRPUSDT": 0.6,
            "DOTUSDT": 7.0,
            "DOGEUSDT": 0.08,
            "AVAXUSDT": 40.0,
            "LINKUSDT": 15.0
        }
        
        logger.info(f"Initialized simplified Binance client (testnet: {testnet})")
    
    async def get_exchange_info(self) -> Dict[str, Any]:
        """Get mock exchange trading rules"""
        return {
            "timezone": "UTC",
            "serverTime": int(datetime.utcnow().timestamp() * 1000),
            "symbols": [{"symbol": symbol, "status": "TRADING"} for symbol in self.symbols]
        }
    
    async def get_ticker_prices(self, symbols: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """Get mock ticker prices with random variations"""
        if symbols is None:
            symbols = self.symbols
        
        tickers = []
        for symbol in symbols:
            if symbol in self.mock_prices:
                # Add small random variation
                base_price = self.mock_prices[symbol]
                variation = random.uniform(-0.02, 0.02)  # ±2% variation
                current_price = base_price * (1 + variation)
                
                tickers.append({
                    "symbol": symbol,
                    "price": f"{current_price:.8f}",
                    "volume": f"{random.uniform(1000, 100000):.8f}"
                })
        
        return tickers
    
    async def get_historical_klines(
        self,
        symbol: str,
        interval: str = "1h",
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: int = 1000
    ) -> List[List]:
        """Generate mock historical kline data"""
        if start_time is None:
            start_time = datetime.utcnow() - timedelta(days=30)
        if end_time is None:
            end_time = datetime.utcnow()
        
        # Generate mock klines
        klines = []
        current_time = start_time
        current_price = self.mock_prices.get(symbol, 1000.0)
        
        while current_time < end_time and len(klines) < limit:
            # Generate OHLCV data with random walk
            price_change = random.uniform(-0.01, 0.01)  # ±1% change per hour
            
            open_price = current_price
            close_price = current_price * (1 + price_change)
            high_price = max(open_price, close_price) * random.uniform(1.0, 1.005)
            low_price = min(open_price, close_price) * random.uniform(0.995, 1.0)
            volume = random.uniform(100, 10000)
            
            kline = [
                int(current_time.timestamp() * 1000),  # timestamp
                f"{open_price:.8f}",   # open
                f"{high_price:.8f}",   # high
                f"{low_price:.8f}",    # low
                f"{close_price:.8f}",  # close
                f"{volume:.8f}",       # volume
                int((current_time + timedelta(hours=1)).timestamp() * 1000),  # close_time
                f"{volume * close_price:.8f}",  # quote_volume
                random.randint(100, 1000),      # trades_count
                f"{volume * 0.6:.8f}",          # taker_buy_base_volume
                f"{volume * 0.6 * close_price:.8f}",  # taker_buy_quote_volume
                "0"  # ignore
            ]
            
            klines.append(kline)
            current_price = close_price
            current_time += timedelta(hours=1)
        
        return klines
    
    async def download_all_historical_data(self, symbols: List[str], days: int = 365) -> Dict[str, pd.DataFrame]:
        """Download mock historical data for multiple symbols"""
        logger.info(f"Downloading mock data for {len(symbols)} symbols ({days} days)")
        
        all_data = {}
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(days=days)
        
        for symbol in symbols:
            klines = await self.get_historical_klines(
                symbol=symbol,
                interval="1h",
                start_time=start_time,
                end_time=end_time,
                limit=days * 24
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
                
                logger.info(f"Generated {len(df)} data points for {symbol}")
            
            # Small delay to simulate API rate limits
            await asyncio.sleep(0.1)
        
        logger.info(f"Completed mock data generation for {len(all_data)} symbols")
        return all_data
    
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
        """Simulate placing a trading order"""
        current_price = self.mock_prices.get(symbol, 1000.0)
        
        if price is None:
            price = current_price
        
        # Simulate order response
        return {
            'symbol': symbol,
            'orderId': random.randint(1000000, 9999999),
            'orderListId': -1,
            'clientOrderId': f"mock_{int(datetime.utcnow().timestamp())}",
            'transactTime': int(datetime.utcnow().timestamp() * 1000),
            'price': f"{price:.8f}",
            'origQty': f"{quantity:.8f}",
            'executedQty': f"{quantity:.8f}",
            'cummulativeQuoteQty': f"{quantity * price:.8f}",
            'status': 'FILLED',
            'timeInForce': time_in_force,
            'type': order_type,
            'side': side
        }
    
    async def get_account_info(self) -> Dict[str, Any]:
        """Get mock account information"""
        return {
            "makerCommission": 10,
            "takerCommission": 10,
            "buyerCommission": 0,
            "sellerCommission": 0,
            "canTrade": True,
            "canWithdraw": True,
            "canDeposit": True,
            "updateTime": int(datetime.utcnow().timestamp() * 1000),
            "accountType": "SPOT",
            "balances": [
                {"asset": "USDT", "free": "10000.00000000", "locked": "0.00000000"},
                {"asset": "BTC", "free": "0.10000000", "locked": "0.00000000"},
                {"asset": "ETH", "free": "1.00000000", "locked": "0.00000000"}
            ]
        }
    
    async def calculate_portfolio_value(self) -> Dict[str, Any]:
        """Calculate mock portfolio value"""
        account = await self.get_account_info()
        tickers = await self.get_ticker_prices()
        
        # Create price lookup
        price_lookup = {ticker['symbol']: float(ticker['price']) for ticker in tickers}
        
        total_value = 0.0
        portfolio = []
        
        for balance in account['balances']:
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
                
                if value_usdt > 0.01:
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
    
    def is_testnet_mode(self) -> bool:
        """Check if running in testnet mode"""
        return self.testnet
    
    async def health_check(self) -> bool:
        """Mock health check"""
        return True
