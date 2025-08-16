"""
Hidden Gems Detection System
Advanced market scanning for identifying promising cryptocurrencies
"""

import asyncio
import aiohttp
import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import json
import re
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
from sklearn.ensemble import IsolationForest
import yfinance as yf
import warnings
warnings.filterwarnings('ignore')

from api_config import APIProvider, get_api_config, is_api_enabled, HIDDEN_GEMS_KEYWORDS
from analysis.technical_analysis import analyzer, SignalType

class GemCategory(Enum):
    """Hidden gem categories"""
    NEW_LISTING = "new_listing"
    BREAKOUT = "breakout"
    UNDERVALUED = "undervalued"
    HIGH_MOMENTUM = "high_momentum"
    SOCIAL_BUZZ = "social_buzz"
    VOLUME_SPIKE = "volume_spike"
    TECHNICAL_SETUP = "technical_setup"
    FUNDAMENTAL_STRONG = "fundamental_strong"

@dataclass
class HiddenGem:
    """Hidden gem cryptocurrency"""
    symbol: str
    name: str
    price: float
    market_cap: float
    volume_24h: float
    price_change_24h: float
    category: GemCategory
    confidence_score: float  # 0-100
    risk_score: float  # 0-100
    potential_return: float  # Expected return %
    discovered_at: datetime
    reasons: List[str] = field(default_factory=list)
    technical_signals: List[Any] = field(default_factory=list)
    social_metrics: Dict = field(default_factory=dict)
    fundamental_metrics: Dict = field(default_factory=dict)
    metadata: Dict = field(default_factory=dict)

@dataclass
class MarketScanResult:
    """Market scanning result"""
    timestamp: datetime
    total_coins_scanned: int
    hidden_gems_found: int
    gems: List[HiddenGem]
    market_summary: Dict
    scan_duration: float

class HiddenGemsDetector:
    """Advanced hidden gems detection system"""
    
    def __init__(self):
        self.session: Optional[aiohttp.ClientSession] = None
        self.scaler = StandardScaler()
        self.isolation_forest = IsolationForest(contamination=0.1, random_state=42)
        self.kmeans = KMeans(n_clusters=5, random_state=42)
        
        # Thresholds for gem detection
        self.thresholds = {
            'min_volume_24h': 100000,  # $100k minimum volume
            'max_market_cap': 1000000000,  # $1B max market cap for "hidden" gems
            'min_price_change_breakout': 15,  # 15% price increase for breakout
            'min_volume_spike': 3.0,  # 3x volume increase
            'min_social_score': 30,  # Social sentiment score
            'min_confidence_score': 60,  # Minimum confidence to report
            'max_age_days': 1000,  # Maximum age for "new" projects
        }
    
    async def __aenter__(self):
        """Async context manager entry"""
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=30),
            headers={'User-Agent': 'AI-Crypto-Trading-Bot/1.0'}
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()
    
    async def scan_market(self) -> MarketScanResult:
        """Comprehensive market scan for hidden gems"""
        start_time = datetime.now()
        
        # Get all available coins
        all_coins = await self._fetch_all_coins()
        
        gems = []
        total_scanned = 0
        
        # Scan in batches to respect rate limits
        batch_size = 50
        for i in range(0, len(all_coins), batch_size):
            batch = all_coins[i:i + batch_size]
            batch_gems = await self._scan_coin_batch(batch)
            gems.extend(batch_gems)
            total_scanned += len(batch)
            
            # Rate limiting delay
            await asyncio.sleep(2)
        
        # Filter and rank gems
        filtered_gems = self._filter_and_rank_gems(gems)
        
        # Generate market summary
        market_summary = self._generate_market_summary(all_coins, filtered_gems)
        
        scan_duration = (datetime.now() - start_time).total_seconds()
        
        return MarketScanResult(
            timestamp=datetime.now(),
            total_coins_scanned=total_scanned,
            hidden_gems_found=len(filtered_gems),
            gems=filtered_gems,
            market_summary=market_summary,
            scan_duration=scan_duration
        )
    
    async def _fetch_all_coins(self) -> List[Dict]:
        """Fetch all available coins from multiple sources"""
        all_coins = []
        
        # CoinGecko - Free and comprehensive
        if is_api_enabled(APIProvider.COINGECKO):
            cg_coins = await self._fetch_coingecko_coins()
            all_coins.extend(cg_coins)
        
        # CoinMarketCap - If available
        if is_api_enabled(APIProvider.COINMARKETCAP):
            cmc_coins = await self._fetch_coinmarketcap_coins()
            all_coins.extend(cmc_coins)
        
        # Remove duplicates based on symbol
        unique_coins = {coin['symbol']: coin for coin in all_coins}.values()
        
        return list(unique_coins)
    
    async def _fetch_coingecko_coins(self) -> List[Dict]:
        """Fetch coins from CoinGecko"""
        try:
            config = get_api_config(APIProvider.COINGECKO)
            url = f"{config.base_url}/coins/markets"
            
            params = {
                'vs_currency': 'usd',
                'order': 'market_cap_desc',
                'per_page': 250,  # Top 250 coins
                'page': 1,
                'sparkline': False,
                'price_change_percentage': '24h,7d'
            }
            
            if config.api_key:
                params['x_cg_demo_api_key'] = config.api_key
            
            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    return self._normalize_coingecko_data(data)
                else:
                    print(f"CoinGecko API error: {response.status}")
                    return []
        
        except Exception as e:
            print(f"Error fetching CoinGecko data: {e}")
            return []
    
    async def _fetch_coinmarketcap_coins(self) -> List[Dict]:
        """Fetch coins from CoinMarketCap"""
        try:
            config = get_api_config(APIProvider.COINMARKETCAP)
            if not config.api_key or config.api_key.startswith('your_'):
                return []
            
            url = f"{config.base_url}/cryptocurrency/listings/latest"
            
            headers = {
                'X-CMC_PRO_API_KEY': config.api_key,
                'Accept': 'application/json'
            }
            
            params = {
                'start': 1,
                'limit': 200,
                'convert': 'USD'
            }
            
            async with self.session.get(url, headers=headers, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    return self._normalize_coinmarketcap_data(data['data'])
                else:
                    print(f"CoinMarketCap API error: {response.status}")
                    return []
        
        except Exception as e:
            print(f"Error fetching CoinMarketCap data: {e}")
            return []
    
    def _normalize_coingecko_data(self, data: List[Dict]) -> List[Dict]:
        """Normalize CoinGecko data format"""
        normalized = []
        
        for coin in data:
            try:
                normalized_coin = {
                    'id': coin.get('id', ''),
                    'symbol': coin.get('symbol', '').upper(),
                    'name': coin.get('name', ''),
                    'price': float(coin.get('current_price', 0)),
                    'market_cap': float(coin.get('market_cap', 0)),
                    'volume_24h': float(coin.get('total_volume', 0)),
                    'price_change_24h': float(coin.get('price_change_percentage_24h', 0)),
                    'price_change_7d': float(coin.get('price_change_percentage_7d_in_currency', 0)),
                    'market_cap_rank': coin.get('market_cap_rank', 999999),
                    'circulating_supply': float(coin.get('circulating_supply', 0)),
                    'total_supply': float(coin.get('total_supply', 0)),
                    'ath': float(coin.get('ath', 0)),
                    'ath_change_percentage': float(coin.get('ath_change_percentage', 0)),
                    'last_updated': coin.get('last_updated', ''),
                    'source': 'coingecko'
                }
                normalized.append(normalized_coin)
            except (ValueError, TypeError) as e:
                continue
        
        return normalized
    
    def _normalize_coinmarketcap_data(self, data: List[Dict]) -> List[Dict]:
        """Normalize CoinMarketCap data format"""
        normalized = []
        
        for coin in data:
            try:
                quote = coin.get('quote', {}).get('USD', {})
                normalized_coin = {
                    'id': coin.get('slug', ''),
                    'symbol': coin.get('symbol', '').upper(),
                    'name': coin.get('name', ''),
                    'price': float(quote.get('price', 0)),
                    'market_cap': float(quote.get('market_cap', 0)),
                    'volume_24h': float(quote.get('volume_24h', 0)),
                    'price_change_24h': float(quote.get('percent_change_24h', 0)),
                    'price_change_7d': float(quote.get('percent_change_7d', 0)),
                    'market_cap_rank': coin.get('cmc_rank', 999999),
                    'circulating_supply': float(coin.get('circulating_supply', 0)),
                    'total_supply': float(coin.get('total_supply', 0)),
                    'max_supply': float(coin.get('max_supply', 0)),
                    'last_updated': quote.get('last_updated', ''),
                    'source': 'coinmarketcap'
                }
                normalized.append(normalized_coin)
            except (ValueError, TypeError) as e:
                continue
        
        return normalized
    
    async def _scan_coin_batch(self, coins: List[Dict]) -> List[HiddenGem]:
        """Scan a batch of coins for hidden gem characteristics"""
        gems = []
        
        for coin in coins:
            try:
                # Basic filtering
                if not self._meets_basic_criteria(coin):
                    continue
                
                # Analyze coin for gem characteristics
                gem = await self._analyze_coin_for_gems(coin)
                if gem and gem.confidence_score >= self.thresholds['min_confidence_score']:
                    gems.append(gem)
            
            except Exception as e:
                print(f"Error analyzing coin {coin.get('symbol', 'Unknown')}: {e}")
                continue
        
        return gems
    
    def _meets_basic_criteria(self, coin: Dict) -> bool:
        """Check if coin meets basic criteria for hidden gem analysis"""
        # Minimum volume requirement
        if coin.get('volume_24h', 0) < self.thresholds['min_volume_24h']:
            return False
        
        # Maximum market cap (shouldn't be too large to be "hidden")
        if coin.get('market_cap', 0) > self.thresholds['max_market_cap']:
            return False
        
        # Must have valid price data
        if coin.get('price', 0) <= 0:
            return False
        
        return True
    
    async def _analyze_coin_for_gems(self, coin: Dict) -> Optional[HiddenGem]:
        """Analyze individual coin for hidden gem characteristics"""
        symbol = coin['symbol']
        confidence_factors = []
        reasons = []
        gem_categories = []
        
        # 1. Technical Analysis
        technical_score, technical_signals = await self._analyze_technical_setup(coin)
        if technical_score > 0.6:
            confidence_factors.append(technical_score * 30)
            reasons.append(f"Strong technical setup (score: {technical_score:.2f})")
            gem_categories.append(GemCategory.TECHNICAL_SETUP)
        
        # 2. Volume Analysis
        volume_score = self._analyze_volume_spike(coin)
        if volume_score > 0.7:
            confidence_factors.append(volume_score * 25)
            reasons.append(f"Unusual volume spike detected")
            gem_categories.append(GemCategory.VOLUME_SPIKE)
        
        # 3. Price Momentum Analysis
        momentum_score = self._analyze_price_momentum(coin)
        if momentum_score > 0.6:
            confidence_factors.append(momentum_score * 20)
            reasons.append(f"Strong price momentum")
            gem_categories.append(GemCategory.HIGH_MOMENTUM)
        
        # 4. Breakout Analysis
        breakout_score = self._analyze_breakout_potential(coin)
        if breakout_score > 0.5:
            confidence_factors.append(breakout_score * 25)
            reasons.append(f"Breakout pattern detected")
            gem_categories.append(GemCategory.BREAKOUT)
        
        # 5. Market Cap vs Volume Ratio
        undervalued_score = self._analyze_undervaluation(coin)
        if undervalued_score > 0.6:
            confidence_factors.append(undervalued_score * 20)
            reasons.append(f"Potentially undervalued")
            gem_categories.append(GemCategory.UNDERVALUED)
        
        # 6. Social Media Buzz (if available)
        social_score = await self._analyze_social_buzz(coin)
        if social_score > 0.5:
            confidence_factors.append(social_score * 15)
            reasons.append(f"Growing social media attention")
            gem_categories.append(GemCategory.SOCIAL_BUZZ)
        
        # 7. New Listing Detection
        if self._is_potential_new_listing(coin):
            confidence_factors.append(30)
            reasons.append("Recently listed or low market cap")
            gem_categories.append(GemCategory.NEW_LISTING)
        
        # Calculate overall confidence
        if not confidence_factors:
            return None
        
        confidence_score = min(sum(confidence_factors), 100)
        
        # Determine primary category
        primary_category = gem_categories[0] if gem_categories else GemCategory.UNDERVALUED
        
        # Calculate risk score
        risk_score = self._calculate_risk_score(coin)
        
        # Estimate potential return
        potential_return = self._estimate_potential_return(coin, confidence_score)
        
        return HiddenGem(
            symbol=symbol,
            name=coin.get('name', ''),
            price=coin['price'],
            market_cap=coin['market_cap'],
            volume_24h=coin['volume_24h'],
            price_change_24h=coin['price_change_24h'],
            category=primary_category,
            confidence_score=confidence_score,
            risk_score=risk_score,
            potential_return=potential_return,
            discovered_at=datetime.now(),
            reasons=reasons,
            technical_signals=technical_signals,
            social_metrics={},
            fundamental_metrics=self._extract_fundamental_metrics(coin),
            metadata={'source': coin.get('source', 'unknown')}
        )
    
    async def _analyze_technical_setup(self, coin: Dict) -> Tuple[float, List]:
        """Analyze technical setup for the coin"""
        # This would require historical price data
        # For now, return a simplified score based on price change patterns
        
        price_change_24h = coin.get('price_change_24h', 0)
        price_change_7d = coin.get('price_change_7d', 0)
        
        score = 0.0
        signals = []
        
        # Positive momentum
        if price_change_24h > 5 and price_change_7d > 10:
            score += 0.3
            signals.append("Positive momentum trend")
        
        # Recovery pattern
        if price_change_24h > 0 and price_change_7d < 0:
            score += 0.2
            signals.append("Recovery from weekly decline")
        
        # ATH distance analysis
        ath_change = coin.get('ath_change_percentage', 0)
        if ath_change < -70:  # More than 70% down from ATH
            score += 0.4
            signals.append("Significant discount from ATH")
        
        return min(score, 1.0), signals
    
    def _analyze_volume_spike(self, coin: Dict) -> float:
        """Analyze volume spike potential"""
        # This is simplified - would need historical volume data for accurate analysis
        volume_24h = coin.get('volume_24h', 0)
        market_cap = coin.get('market_cap', 1)
        
        # Volume to market cap ratio
        volume_ratio = volume_24h / market_cap if market_cap > 0 else 0
        
        # High volume relative to market cap suggests interest
        if volume_ratio > 0.1:  # 10% of market cap traded in 24h
            return min(volume_ratio * 5, 1.0)
        
        return 0.0
    
    def _analyze_price_momentum(self, coin: Dict) -> float:
        """Analyze price momentum"""
        price_change_24h = coin.get('price_change_24h', 0)
        price_change_7d = coin.get('price_change_7d', 0)
        
        # Weighted momentum score
        momentum_24h = max(0, price_change_24h / 20)  # Normalize to 20% max
        momentum_7d = max(0, price_change_7d / 50)    # Normalize to 50% max
        
        # Combine with more weight on recent performance
        momentum_score = (momentum_24h * 0.7 + momentum_7d * 0.3)
        
        return min(momentum_score, 1.0)
    
    def _analyze_breakout_potential(self, coin: Dict) -> float:
        """Analyze breakout potential"""
        price_change_24h = coin.get('price_change_24h', 0)
        
        # Simple breakout detection based on significant price movement
        if price_change_24h > self.thresholds['min_price_change_breakout']:
            return min(price_change_24h / 30, 1.0)  # Normalize to 30% max
        
        return 0.0
    
    def _analyze_undervaluation(self, coin: Dict) -> float:
        """Analyze potential undervaluation"""
        market_cap = coin.get('market_cap', 0)
        volume_24h = coin.get('volume_24h', 0)
        
        if market_cap <= 0:
            return 0.0
        
        # Volume to market cap ratio
        volume_ratio = volume_24h / market_cap
        
        # Low market cap with decent volume suggests potential
        if market_cap < 50000000:  # Less than $50M market cap
            if volume_ratio > 0.05:  # At least 5% of market cap traded
                return 0.8
            elif volume_ratio > 0.02:
                return 0.6
        elif market_cap < 200000000:  # Less than $200M market cap
            if volume_ratio > 0.1:
                return 0.7
        
        return 0.0
    
    async def _analyze_social_buzz(self, coin: Dict) -> float:
        """Analyze social media buzz (simplified)"""
        # This would integrate with Reddit, Twitter, etc.
        # For now, return a placeholder score
        
        symbol = coin['symbol'].lower()
        
        # Check if symbol matches trending keywords
        for keyword in HIDDEN_GEMS_KEYWORDS:
            if keyword.lower() in coin.get('name', '').lower():
                return 0.6
        
        return 0.0
    
    def _is_potential_new_listing(self, coin: Dict) -> bool:
        """Check if coin is potentially a new listing"""
        market_cap = coin.get('market_cap', 0)
        market_cap_rank = coin.get('market_cap_rank', 999999)
        
        # Low market cap or high rank number suggests newer project
        return market_cap < 10000000 or market_cap_rank > 1000
    
    def _calculate_risk_score(self, coin: Dict) -> float:
        """Calculate risk score for the coin"""
        risk_factors = 0
        total_factors = 5
        
        # Market cap risk (lower = higher risk)
        market_cap = coin.get('market_cap', 0)
        if market_cap < 1000000:  # Less than $1M
            risk_factors += 2
        elif market_cap < 10000000:  # Less than $10M
            risk_factors += 1
        
        # Volume risk (lower = higher risk)
        volume_24h = coin.get('volume_24h', 0)
        if volume_24h < 100000:  # Less than $100k volume
            risk_factors += 1
        
        # Volatility risk (higher price change = higher risk)
        price_change_24h = abs(coin.get('price_change_24h', 0))
        if price_change_24h > 20:  # More than 20% change
            risk_factors += 1
        
        # Rank risk (higher rank = higher risk)
        market_cap_rank = coin.get('market_cap_rank', 999999)
        if market_cap_rank > 500:
            risk_factors += 1
        
        return (risk_factors / total_factors) * 100
    
    def _estimate_potential_return(self, coin: Dict, confidence_score: float) -> float:
        """Estimate potential return based on analysis"""
        base_return = confidence_score / 2  # Base return from confidence
        
        # Adjust based on market cap (smaller = higher potential)
        market_cap = coin.get('market_cap', 1)
        if market_cap < 1000000:
            market_cap_multiplier = 3.0
        elif market_cap < 10000000:
            market_cap_multiplier = 2.5
        elif market_cap < 100000000:
            market_cap_multiplier = 2.0
        else:
            market_cap_multiplier = 1.5
        
        # Adjust based on current momentum
        momentum_multiplier = 1 + (coin.get('price_change_24h', 0) / 100)
        
        potential_return = base_return * market_cap_multiplier * momentum_multiplier
        
        return min(potential_return, 500)  # Cap at 500% potential return
    
    def _extract_fundamental_metrics(self, coin: Dict) -> Dict:
        """Extract fundamental metrics from coin data"""
        return {
            'market_cap_rank': coin.get('market_cap_rank', 999999),
            'circulating_supply': coin.get('circulating_supply', 0),
            'total_supply': coin.get('total_supply', 0),
            'max_supply': coin.get('max_supply', 0),
            'volume_to_market_cap_ratio': (
                coin.get('volume_24h', 0) / coin.get('market_cap', 1)
                if coin.get('market_cap', 0) > 0 else 0
            ),
            'ath_change_percentage': coin.get('ath_change_percentage', 0)
        }
    
    def _filter_and_rank_gems(self, gems: List[HiddenGem]) -> List[HiddenGem]:
        """Filter and rank hidden gems by quality"""
        # Filter by minimum confidence
        filtered_gems = [
            gem for gem in gems 
            if gem.confidence_score >= self.thresholds['min_confidence_score']
        ]
        
        # Sort by confidence score (descending) and potential return
        filtered_gems.sort(
            key=lambda x: (x.confidence_score, x.potential_return),
            reverse=True
        )
        
        # Return top 20 gems
        return filtered_gems[:20]
    
    def _generate_market_summary(self, all_coins: List[Dict], gems: List[HiddenGem]) -> Dict:
        """Generate market summary statistics"""
        if not all_coins:
            return {}
        
        total_market_cap = sum(coin.get('market_cap', 0) for coin in all_coins)
        total_volume = sum(coin.get('volume_24h', 0) for coin in all_coins)
        
        avg_price_change = np.mean([coin.get('price_change_24h', 0) for coin in all_coins])
        
        # Category distribution
        category_counts = {}
        for gem in gems:
            category = gem.category.value
            category_counts[category] = category_counts.get(category, 0) + 1
        
        return {
            'total_market_cap': total_market_cap,
            'total_volume_24h': total_volume,
            'average_price_change_24h': avg_price_change,
            'coins_scanned': len(all_coins),
            'gems_found': len(gems),
            'gem_categories': category_counts,
            'average_confidence': np.mean([gem.confidence_score for gem in gems]) if gems else 0,
            'average_risk': np.mean([gem.risk_score for gem in gems]) if gems else 0,
            'average_potential_return': np.mean([gem.potential_return for gem in gems]) if gems else 0
        }

# Utility functions
async def scan_for_hidden_gems() -> MarketScanResult:
    """Convenience function to scan for hidden gems"""
    async with HiddenGemsDetector() as detector:
        return await detector.scan_market()

def filter_gems_by_category(gems: List[HiddenGem], category: GemCategory) -> List[HiddenGem]:
    """Filter gems by category"""
    return [gem for gem in gems if gem.category == category]

def get_top_gems_by_confidence(gems: List[HiddenGem], limit: int = 10) -> List[HiddenGem]:
    """Get top gems by confidence score"""
    sorted_gems = sorted(gems, key=lambda x: x.confidence_score, reverse=True)
    return sorted_gems[:limit]

def get_low_risk_gems(gems: List[HiddenGem], max_risk: float = 50) -> List[HiddenGem]:
    """Get gems with risk score below threshold"""
    return [gem for gem in gems if gem.risk_score <= max_risk]

# Create global detector instance
detector = HiddenGemsDetector()

# Export main components
__all__ = [
    'HiddenGemsDetector', 'HiddenGem', 'GemCategory', 'MarketScanResult',
    'scan_for_hidden_gems', 'filter_gems_by_category', 'get_top_gems_by_confidence',
    'get_low_risk_gems', 'detector'
]
