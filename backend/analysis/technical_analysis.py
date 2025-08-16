"""
Advanced Technical Analysis Library
Hedge Fund Grade Technical Indicators and Signal Generation
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional, Union
from dataclasses import dataclass, field
from enum import Enum
import talib
from scipy import stats
from sklearn.preprocessing import StandardScaler
import warnings
warnings.filterwarnings('ignore')

class SignalType(Enum):
    """Signal type enumeration"""
    BUY = "BUY"
    SELL = "SELL"
    HOLD = "HOLD"

@dataclass
class TechnicalSignal:
    """Technical analysis signal"""
    signal: SignalType
    strength: float  # 0.0 to 1.0
    confidence: float  # 0.0 to 1.0
    indicator: str
    value: float
    timestamp: pd.Timestamp
    metadata: Dict = field(default_factory=dict)

@dataclass
class TechnicalAnalysis:
    """Comprehensive technical analysis result"""
    symbol: str
    timestamp: pd.Timestamp
    price: float
    signals: List[TechnicalSignal]
    overall_signal: SignalType
    confidence: float
    risk_score: float
    support_levels: List[float]
    resistance_levels: List[float]
    volatility: float
    trend_strength: float
    momentum_score: float
    volume_profile: Dict

class AdvancedTechnicalAnalyzer:
    """Advanced technical analysis with hedge fund grade indicators"""
    
    def __init__(self):
        self.scaler = StandardScaler()
        
    def analyze(self, df: pd.DataFrame, symbol: str) -> TechnicalAnalysis:
        """
        Perform comprehensive technical analysis
        
        Args:
            df: DataFrame with OHLCV data
            symbol: Trading symbol
            
        Returns:
            TechnicalAnalysis object
        """
        if len(df) < 50:
            return self._create_empty_analysis(symbol, df.iloc[-1]['close'] if len(df) > 0 else 0)
        
        # Ensure data is properly formatted
        df = self._prepare_data(df)
        
        signals = []
        current_price = df['close'].iloc[-1]
        
        # Generate all technical signals
        signals.extend(self._momentum_signals(df))
        signals.extend(self._trend_signals(df))
        signals.extend(self._volume_signals(df))
        signals.extend(self._volatility_signals(df))
        signals.extend(self._pattern_signals(df))
        signals.extend(self._fibonacci_signals(df))
        signals.extend(self._market_structure_signals(df))
        
        # Calculate support and resistance
        support_levels, resistance_levels = self._calculate_support_resistance(df)
        
        # Calculate risk metrics
        volatility = self._calculate_volatility(df)
        risk_score = self._calculate_risk_score(df, volatility)
        
        # Calculate trend and momentum
        trend_strength = self._calculate_trend_strength(df)
        momentum_score = self._calculate_momentum_score(df)
        
        # Volume profile analysis
        volume_profile = self._analyze_volume_profile(df)
        
        # Generate overall signal
        overall_signal, confidence = self._generate_overall_signal(signals)
        
        return TechnicalAnalysis(
            symbol=symbol,
            timestamp=df.index[-1],
            price=current_price,
            signals=signals,
            overall_signal=overall_signal,
            confidence=confidence,
            risk_score=risk_score,
            support_levels=support_levels[-5:],  # Last 5 levels
            resistance_levels=resistance_levels[-5:],
            volatility=volatility,
            trend_strength=trend_strength,
            momentum_score=momentum_score,
            volume_profile=volume_profile
        )
    
    def _prepare_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Prepare and validate OHLCV data"""
        df = df.copy()
        
        # Ensure required columns
        required_cols = ['open', 'high', 'low', 'close', 'volume']
        for col in required_cols:
            if col not in df.columns:
                raise ValueError(f"Missing required column: {col}")
        
        # Convert to float and handle NaN
        for col in required_cols:
            df[col] = pd.to_numeric(df[col], errors='coerce')
        
        df = df.dropna()
        
        # Add derived columns
        df['hl2'] = (df['high'] + df['low']) / 2
        df['hlc3'] = (df['high'] + df['low'] + df['close']) / 3
        df['ohlc4'] = (df['open'] + df['high'] + df['low'] + df['close']) / 4
        
        return df
    
    def _momentum_signals(self, df: pd.DataFrame) -> List[TechnicalSignal]:
        """Generate momentum-based signals"""
        signals = []
        
        # RSI Analysis (Multiple timeframes)
        for period in [14, 21, 30]:
            rsi = talib.RSI(df['close'].values, timeperiod=period)
            current_rsi = rsi[-1]
            
            if current_rsi < 30:
                strength = min((30 - current_rsi) / 30, 1.0)
                signals.append(TechnicalSignal(
                    signal=SignalType.BUY,
                    strength=strength,
                    confidence=0.7 + (period - 14) * 0.05,  # Higher confidence for longer periods
                    indicator=f'RSI_{period}',
                    value=current_rsi,
                    timestamp=df.index[-1],
                    metadata={'oversold': True, 'period': period}
                ))
            elif current_rsi > 70:
                strength = min((current_rsi - 70) / 30, 1.0)
                signals.append(TechnicalSignal(
                    signal=SignalType.SELL,
                    strength=strength,
                    confidence=0.7 + (period - 14) * 0.05,
                    indicator=f'RSI_{period}',
                    value=current_rsi,
                    timestamp=df.index[-1],
                    metadata={'overbought': True, 'period': period}
                ))
        
        # Stochastic Oscillator
        slowk, slowd = talib.STOCH(df['high'].values, df['low'].values, df['close'].values)
        if slowk[-1] < 20 and slowd[-1] < 20:
            signals.append(TechnicalSignal(
                signal=SignalType.BUY,
                strength=min((20 - slowk[-1]) / 20, 1.0),
                confidence=0.65,
                indicator='STOCH',
                value=slowk[-1],
                timestamp=df.index[-1],
                metadata={'k': slowk[-1], 'd': slowd[-1]}
            ))
        elif slowk[-1] > 80 and slowd[-1] > 80:
            signals.append(TechnicalSignal(
                signal=SignalType.SELL,
                strength=min((slowk[-1] - 80) / 20, 1.0),
                confidence=0.65,
                indicator='STOCH',
                value=slowk[-1],
                timestamp=df.index[-1],
                metadata={'k': slowk[-1], 'd': slowd[-1]}
            ))
        
        # Williams %R
        williams_r = talib.WILLR(df['high'].values, df['low'].values, df['close'].values)
        current_wr = williams_r[-1]
        
        if current_wr < -80:
            signals.append(TechnicalSignal(
                signal=SignalType.BUY,
                strength=min((-80 - current_wr) / 20, 1.0),
                confidence=0.6,
                indicator='WILLIAMS_R',
                value=current_wr,
                timestamp=df.index[-1]
            ))
        elif current_wr > -20:
            signals.append(TechnicalSignal(
                signal=SignalType.SELL,
                strength=min((current_wr + 20) / 20, 1.0),
                confidence=0.6,
                indicator='WILLIAMS_R',
                value=current_wr,
                timestamp=df.index[-1]
            ))
        
        # CCI (Commodity Channel Index)
        cci = talib.CCI(df['high'].values, df['low'].values, df['close'].values)
        current_cci = cci[-1]
        
        if current_cci < -100:
            signals.append(TechnicalSignal(
                signal=SignalType.BUY,
                strength=min((-100 - current_cci) / 200, 1.0),
                confidence=0.6,
                indicator='CCI',
                value=current_cci,
                timestamp=df.index[-1]
            ))
        elif current_cci > 100:
            signals.append(TechnicalSignal(
                signal=SignalType.SELL,
                strength=min((current_cci - 100) / 200, 1.0),
                confidence=0.6,
                indicator='CCI',
                value=current_cci,
                timestamp=df.index[-1]
            ))
        
        return signals
    
    def _trend_signals(self, df: pd.DataFrame) -> List[TechnicalSignal]:
        """Generate trend-based signals"""
        signals = []
        
        # MACD Analysis
        macd, macdsignal, macdhist = talib.MACD(df['close'].values)
        
        # MACD crossover
        if len(macd) > 1 and len(macdsignal) > 1:
            if macd[-1] > macdsignal[-1] and macd[-2] <= macdsignal[-2]:
                signals.append(TechnicalSignal(
                    signal=SignalType.BUY,
                    strength=min(abs(macdhist[-1]) / 5, 1.0),
                    confidence=0.75,
                    indicator='MACD_CROSSOVER',
                    value=macdhist[-1],
                    timestamp=df.index[-1],
                    metadata={'bullish_crossover': True}
                ))
            elif macd[-1] < macdsignal[-1] and macd[-2] >= macdsignal[-2]:
                signals.append(TechnicalSignal(
                    signal=SignalType.SELL,
                    strength=min(abs(macdhist[-1]) / 5, 1.0),
                    confidence=0.75,
                    indicator='MACD_CROSSOVER',
                    value=macdhist[-1],
                    timestamp=df.index[-1],
                    metadata={'bearish_crossover': True}
                ))
        
        # Moving Average Analysis
        ma_periods = [9, 21, 50, 100, 200]
        mas = {}
        
        for period in ma_periods:
            if len(df) >= period:
                mas[period] = talib.SMA(df['close'].values, timeperiod=period)
        
        current_price = df['close'].iloc[-1]
        
        # Golden Cross / Death Cross (50/200 MA)
        if 50 in mas and 200 in mas and len(mas[50]) > 1 and len(mas[200]) > 1:
            ma50_current = mas[50][-1]
            ma50_previous = mas[50][-2]
            ma200_current = mas[200][-1]
            ma200_previous = mas[200][-2]
            
            # Golden Cross
            if ma50_current > ma200_current and ma50_previous <= ma200_previous:
                signals.append(TechnicalSignal(
                    signal=SignalType.BUY,
                    strength=0.8,
                    confidence=0.85,
                    indicator='GOLDEN_CROSS',
                    value=ma50_current - ma200_current,
                    timestamp=df.index[-1],
                    metadata={'ma50': ma50_current, 'ma200': ma200_current}
                ))
            
            # Death Cross
            elif ma50_current < ma200_current and ma50_previous >= ma200_previous:
                signals.append(TechnicalSignal(
                    signal=SignalType.SELL,
                    strength=0.8,
                    confidence=0.85,
                    indicator='DEATH_CROSS',
                    value=ma200_current - ma50_current,
                    timestamp=df.index[-1],
                    metadata={'ma50': ma50_current, 'ma200': ma200_current}
                ))
        
        # Price vs MA analysis
        if 21 in mas:
            ma21 = mas[21][-1]
            if current_price > ma21 * 1.02:  # 2% above MA
                signals.append(TechnicalSignal(
                    signal=SignalType.BUY,
                    strength=min((current_price / ma21 - 1) * 10, 1.0),
                    confidence=0.6,
                    indicator='PRICE_ABOVE_MA21',
                    value=current_price / ma21,
                    timestamp=df.index[-1]
                ))
            elif current_price < ma21 * 0.98:  # 2% below MA
                signals.append(TechnicalSignal(
                    signal=SignalType.SELL,
                    strength=min((1 - current_price / ma21) * 10, 1.0),
                    confidence=0.6,
                    indicator='PRICE_BELOW_MA21',
                    value=current_price / ma21,
                    timestamp=df.index[-1]
                ))
        
        # ADX (Average Directional Index) - Trend Strength
        adx = talib.ADX(df['high'].values, df['low'].values, df['close'].values)
        plus_di = talib.PLUS_DI(df['high'].values, df['low'].values, df['close'].values)
        minus_di = talib.MINUS_DI(df['high'].values, df['low'].values, df['close'].values)
        
        if len(adx) > 0 and adx[-1] > 25:  # Strong trend
            if plus_di[-1] > minus_di[-1]:
                signals.append(TechnicalSignal(
                    signal=SignalType.BUY,
                    strength=min(adx[-1] / 50, 1.0),
                    confidence=0.7,
                    indicator='ADX_TREND',
                    value=adx[-1],
                    timestamp=df.index[-1],
                    metadata={'plus_di': plus_di[-1], 'minus_di': minus_di[-1]}
                ))
            else:
                signals.append(TechnicalSignal(
                    signal=SignalType.SELL,
                    strength=min(adx[-1] / 50, 1.0),
                    confidence=0.7,
                    indicator='ADX_TREND',
                    value=adx[-1],
                    timestamp=df.index[-1],
                    metadata={'plus_di': plus_di[-1], 'minus_di': minus_di[-1]}
                ))
        
        return signals
    
    def _volume_signals(self, df: pd.DataFrame) -> List[TechnicalSignal]:
        """Generate volume-based signals"""
        signals = []
        
        # On-Balance Volume (OBV)
        obv = talib.OBV(df['close'].values, df['volume'].values)
        obv_ma = talib.SMA(obv, timeperiod=21)
        
        if len(obv) > 1 and len(obv_ma) > 1:
            if obv[-1] > obv_ma[-1] and df['close'].iloc[-1] > df['close'].iloc[-2]:
                signals.append(TechnicalSignal(
                    signal=SignalType.BUY,
                    strength=0.6,
                    confidence=0.65,
                    indicator='OBV_BULLISH',
                    value=obv[-1],
                    timestamp=df.index[-1],
                    metadata={'obv_above_ma': True}
                ))
        
        # Volume Rate of Change
        volume_roc = talib.ROC(df['volume'].values, timeperiod=10)
        if len(volume_roc) > 0 and volume_roc[-1] > 50:  # High volume increase
            price_change = (df['close'].iloc[-1] - df['close'].iloc[-2]) / df['close'].iloc[-2]
            if price_change > 0:
                signals.append(TechnicalSignal(
                    signal=SignalType.BUY,
                    strength=min(volume_roc[-1] / 100, 1.0),
                    confidence=0.7,
                    indicator='VOLUME_BREAKOUT',
                    value=volume_roc[-1],
                    timestamp=df.index[-1]
                ))
        
        # Volume Weighted Average Price (VWAP)
        typical_price = (df['high'] + df['low'] + df['close']) / 3
        cumulative_tpv = (typical_price * df['volume']).cumsum()
        cumulative_volume = df['volume'].cumsum()
        vwap = cumulative_tpv / cumulative_volume
        
        current_price = df['close'].iloc[-1]
        current_vwap = vwap.iloc[-1]
        
        if current_price > current_vwap * 1.01:  # 1% above VWAP
            signals.append(TechnicalSignal(
                signal=SignalType.BUY,
                strength=min((current_price / current_vwap - 1) * 20, 1.0),
                confidence=0.6,
                indicator='ABOVE_VWAP',
                value=current_price / current_vwap,
                timestamp=df.index[-1]
            ))
        elif current_price < current_vwap * 0.99:  # 1% below VWAP
            signals.append(TechnicalSignal(
                signal=SignalType.SELL,
                strength=min((1 - current_price / current_vwap) * 20, 1.0),
                confidence=0.6,
                indicator='BELOW_VWAP',
                value=current_price / current_vwap,
                timestamp=df.index[-1]
            ))
        
        return signals
    
    def _volatility_signals(self, df: pd.DataFrame) -> List[TechnicalSignal]:
        """Generate volatility-based signals"""
        signals = []
        
        # Bollinger Bands
        bb_upper, bb_middle, bb_lower = talib.BBANDS(df['close'].values, timeperiod=20, nbdevup=2, nbdevdn=2)
        current_price = df['close'].iloc[-1]
        
        if current_price <= bb_lower[-1]:
            signals.append(TechnicalSignal(
                signal=SignalType.BUY,
                strength=min((bb_lower[-1] - current_price) / (bb_upper[-1] - bb_lower[-1]), 1.0),
                confidence=0.7,
                indicator='BB_OVERSOLD',
                value=current_price,
                timestamp=df.index[-1],
                metadata={'bb_lower': bb_lower[-1], 'bb_upper': bb_upper[-1]}
            ))
        elif current_price >= bb_upper[-1]:
            signals.append(TechnicalSignal(
                signal=SignalType.SELL,
                strength=min((current_price - bb_upper[-1]) / (bb_upper[-1] - bb_lower[-1]), 1.0),
                confidence=0.7,
                indicator='BB_OVERBOUGHT',
                value=current_price,
                timestamp=df.index[-1],
                metadata={'bb_lower': bb_lower[-1], 'bb_upper': bb_upper[-1]}
            ))
        
        # Average True Range (ATR) for volatility breakouts
        atr = talib.ATR(df['high'].values, df['low'].values, df['close'].values, timeperiod=14)
        atr_ma = talib.SMA(atr, timeperiod=10)
        
        if len(atr) > 1 and len(atr_ma) > 1:
            if atr[-1] > atr_ma[-1] * 1.5:  # High volatility
                signals.append(TechnicalSignal(
                    signal=SignalType.HOLD,  # High volatility = caution
                    strength=0.8,
                    confidence=0.6,
                    indicator='HIGH_VOLATILITY',
                    value=atr[-1],
                    timestamp=df.index[-1],
                    metadata={'atr_ratio': atr[-1] / atr_ma[-1]}
                ))
        
        return signals
    
    def _pattern_signals(self, df: pd.DataFrame) -> List[TechnicalSignal]:
        """Generate pattern recognition signals"""
        signals = []
        
        # Candlestick patterns using talib
        patterns = {
            'HAMMER': talib.CDLHAMMER(df['open'], df['high'], df['low'], df['close']),
            'DOJI': talib.CDLDOJI(df['open'], df['high'], df['low'], df['close']),
            'ENGULFING': talib.CDLENGULFING(df['open'], df['high'], df['low'], df['close']),
            'MORNING_STAR': talib.CDLMORNINGSTAR(df['open'], df['high'], df['low'], df['close']),
            'EVENING_STAR': talib.CDLEVENINGSTAR(df['open'], df['high'], df['low'], df['close']),
            'SHOOTING_STAR': talib.CDLSHOOTINGSTAR(df['open'], df['high'], df['low'], df['close']),
            'HANGING_MAN': talib.CDLHANGINGMAN(df['open'], df['high'], df['low'], df['close'])
        }
        
        for pattern_name, pattern_values in patterns.items():
            if len(pattern_values) > 0 and pattern_values[-1] != 0:
                signal_type = SignalType.BUY if pattern_values[-1] > 0 else SignalType.SELL
                strength = min(abs(pattern_values[-1]) / 100, 1.0)
                
                signals.append(TechnicalSignal(
                    signal=signal_type,
                    strength=strength,
                    confidence=0.5,  # Pattern recognition has moderate confidence
                    indicator=f'PATTERN_{pattern_name}',
                    value=pattern_values[-1],
                    timestamp=df.index[-1],
                    metadata={'pattern': pattern_name}
                ))
        
        return signals
    
    def _fibonacci_signals(self, df: pd.DataFrame) -> List[TechnicalSignal]:
        """Generate Fibonacci retracement signals"""
        signals = []
        
        # Calculate recent high and low (last 50 periods)
        recent_data = df.tail(50)
        high = recent_data['high'].max()
        low = recent_data['low'].min()
        
        # Fibonacci levels
        fib_levels = {
            0.236: high - (high - low) * 0.236,
            0.382: high - (high - low) * 0.382,
            0.500: high - (high - low) * 0.500,
            0.618: high - (high - low) * 0.618,
            0.786: high - (high - low) * 0.786
        }
        
        current_price = df['close'].iloc[-1]
        
        # Check if price is near Fibonacci levels (within 1%)
        for level, price_level in fib_levels.items():
            if abs(current_price - price_level) / price_level < 0.01:
                # Near support level (bullish)
                if level >= 0.5:  # Deep retracement levels
                    signals.append(TechnicalSignal(
                        signal=SignalType.BUY,
                        strength=0.6,
                        confidence=0.6,
                        indicator=f'FIB_SUPPORT_{level}',
                        value=current_price,
                        timestamp=df.index[-1],
                        metadata={'fib_level': level, 'price_level': price_level}
                    ))
                # Near resistance level (bearish)
                elif level <= 0.382:
                    signals.append(TechnicalSignal(
                        signal=SignalType.SELL,
                        strength=0.6,
                        confidence=0.6,
                        indicator=f'FIB_RESISTANCE_{level}',
                        value=current_price,
                        timestamp=df.index[-1],
                        metadata={'fib_level': level, 'price_level': price_level}
                    ))
        
        return signals
    
    def _market_structure_signals(self, df: pd.DataFrame) -> List[TechnicalSignal]:
        """Generate market structure signals (higher highs, lower lows, etc.)"""
        signals = []
        
        # Find pivots (simplified)
        high_pivots = []
        low_pivots = []
        
        window = 5  # Look for pivots in 5-period windows
        
        for i in range(window, len(df) - window):
            # High pivot
            if all(df['high'].iloc[i] >= df['high'].iloc[i-j] for j in range(1, window+1)) and \
               all(df['high'].iloc[i] >= df['high'].iloc[i+j] for j in range(1, window+1)):
                high_pivots.append((i, df['high'].iloc[i]))
            
            # Low pivot
            if all(df['low'].iloc[i] <= df['low'].iloc[i-j] for j in range(1, window+1)) and \
               all(df['low'].iloc[i] <= df['low'].iloc[i+j] for j in range(1, window+1)):
                low_pivots.append((i, df['low'].iloc[i]))
        
        # Analyze trend structure
        if len(high_pivots) >= 2 and len(low_pivots) >= 2:
            recent_highs = high_pivots[-2:]
            recent_lows = low_pivots[-2:]
            
            # Higher highs and higher lows (uptrend)
            if recent_highs[-1][1] > recent_highs[-2][1] and recent_lows[-1][1] > recent_lows[-2][1]:
                signals.append(TechnicalSignal(
                    signal=SignalType.BUY,
                    strength=0.7,
                    confidence=0.8,
                    indicator='HIGHER_HIGHS_LOWS',
                    value=1.0,
                    timestamp=df.index[-1],
                    metadata={'trend': 'uptrend'}
                ))
            
            # Lower highs and lower lows (downtrend)
            elif recent_highs[-1][1] < recent_highs[-2][1] and recent_lows[-1][1] < recent_lows[-2][1]:
                signals.append(TechnicalSignal(
                    signal=SignalType.SELL,
                    strength=0.7,
                    confidence=0.8,
                    indicator='LOWER_HIGHS_LOWS',
                    value=-1.0,
                    timestamp=df.index[-1],
                    metadata={'trend': 'downtrend'}
                ))
        
        return signals
    
    def _calculate_support_resistance(self, df: pd.DataFrame) -> Tuple[List[float], List[float]]:
        """Calculate support and resistance levels"""
        # Use local minima/maxima for support/resistance
        window = 10
        
        support_levels = []
        resistance_levels = []
        
        # Find local minima (support)
        for i in range(window, len(df) - window):
            if all(df['low'].iloc[i] <= df['low'].iloc[i-j] for j in range(1, window+1)) and \
               all(df['low'].iloc[i] <= df['low'].iloc[i+j] for j in range(1, window+1)):
                support_levels.append(df['low'].iloc[i])
        
        # Find local maxima (resistance)
        for i in range(window, len(df) - window):
            if all(df['high'].iloc[i] >= df['high'].iloc[i-j] for j in range(1, window+1)) and \
               all(df['high'].iloc[i] >= df['high'].iloc[i+j] for j in range(1, window+1)):
                resistance_levels.append(df['high'].iloc[i])
        
        return sorted(support_levels), sorted(resistance_levels, reverse=True)
    
    def _calculate_volatility(self, df: pd.DataFrame) -> float:
        """Calculate volatility (annualized)"""
        returns = df['close'].pct_change().dropna()
        return returns.std() * np.sqrt(365)  # Annualized volatility
    
    def _calculate_risk_score(self, df: pd.DataFrame, volatility: float) -> float:
        """Calculate risk score based on multiple factors"""
        # ATR-based risk
        atr = talib.ATR(df['high'].values, df['low'].values, df['close'].values, timeperiod=14)
        current_atr = atr[-1] if len(atr) > 0 else 0
        current_price = df['close'].iloc[-1]
        atr_risk = (current_atr / current_price) if current_price > 0 else 0
        
        # Volatility risk
        vol_risk = min(volatility / 2.0, 1.0)  # Normalize to 0-1
        
        # Combine risks
        risk_score = (atr_risk + vol_risk) / 2
        return min(risk_score, 1.0)
    
    def _calculate_trend_strength(self, df: pd.DataFrame) -> float:
        """Calculate trend strength (-1 to 1)"""
        # Use ADX and price momentum
        adx = talib.ADX(df['high'].values, df['low'].values, df['close'].values)
        current_adx = adx[-1] if len(adx) > 0 else 0
        
        # Price momentum
        momentum = (df['close'].iloc[-1] - df['close'].iloc[-20]) / df['close'].iloc[-20]
        
        # Combine ADX strength with direction
        strength = (current_adx / 50) * np.sign(momentum)  # ADX normalized to 0-1, then apply direction
        return np.clip(strength, -1, 1)
    
    def _calculate_momentum_score(self, df: pd.DataFrame) -> float:
        """Calculate momentum score (0 to 1)"""
        # Multiple momentum indicators
        rsi = talib.RSI(df['close'].values, timeperiod=14)
        current_rsi = rsi[-1] if len(rsi) > 0 else 50
        
        # ROC (Rate of Change)
        roc = talib.ROC(df['close'].values, timeperiod=10)
        current_roc = roc[-1] if len(roc) > 0 else 0
        
        # Combine momentum indicators
        rsi_score = (current_rsi - 50) / 50  # -1 to 1
        roc_score = np.tanh(current_roc / 10)  # Normalize ROC
        
        momentum_score = (rsi_score + roc_score) / 2
        return (momentum_score + 1) / 2  # Convert to 0-1 scale
    
    def _analyze_volume_profile(self, df: pd.DataFrame) -> Dict:
        """Analyze volume profile"""
        # Volume-weighted metrics
        total_volume = df['volume'].sum()
        recent_volume = df['volume'].tail(10).mean()
        volume_trend = df['volume'].tail(20).mean()
        
        return {
            'total_volume': float(total_volume),
            'recent_avg_volume': float(recent_volume),
            'volume_trend_ratio': float(recent_volume / volume_trend) if volume_trend > 0 else 1.0,
            'high_volume_threshold': float(volume_trend * 2)
        }
    
    def _generate_overall_signal(self, signals: List[TechnicalSignal]) -> Tuple[SignalType, float]:
        """Generate overall signal from individual signals"""
        if not signals:
            return SignalType.HOLD, 0.0
        
        # Weight signals by their confidence and strength
        buy_weight = sum(s.strength * s.confidence for s in signals if s.signal == SignalType.BUY)
        sell_weight = sum(s.strength * s.confidence for s in signals if s.signal == SignalType.SELL)
        
        total_signals = len([s for s in signals if s.signal != SignalType.HOLD])
        
        # Normalize weights
        if total_signals > 0:
            buy_weight /= total_signals
            sell_weight /= total_signals
        
        # Determine overall signal
        if buy_weight > sell_weight and buy_weight > 0.3:
            return SignalType.BUY, min(buy_weight, 1.0)
        elif sell_weight > buy_weight and sell_weight > 0.3:
            return SignalType.SELL, min(sell_weight, 1.0)
        else:
            return SignalType.HOLD, max(buy_weight, sell_weight)
    
    def _create_empty_analysis(self, symbol: str, price: float) -> TechnicalAnalysis:
        """Create empty analysis for insufficient data"""
        return TechnicalAnalysis(
            symbol=symbol,
            timestamp=pd.Timestamp.now(),
            price=price,
            signals=[],
            overall_signal=SignalType.HOLD,
            confidence=0.0,
            risk_score=1.0,
            support_levels=[],
            resistance_levels=[],
            volatility=0.0,
            trend_strength=0.0,
            momentum_score=0.5,
            volume_profile={}
        )

# Utility functions
def calculate_kelly_criterion(win_rate: float, avg_win: float, avg_loss: float) -> float:
    """Calculate Kelly Criterion for position sizing"""
    if avg_loss <= 0:
        return 0.0
    
    b = avg_win / avg_loss  # Ratio of win to loss
    p = win_rate  # Probability of winning
    q = 1 - p  # Probability of losing
    
    kelly = (b * p - q) / b
    return max(0, min(kelly, 0.25))  # Cap at 25% of capital

def calculate_sharpe_ratio(returns: pd.Series, risk_free_rate: float = 0.02) -> float:
    """Calculate Sharpe ratio"""
    excess_returns = returns - risk_free_rate / 365  # Daily risk-free rate
    return excess_returns.mean() / excess_returns.std() * np.sqrt(365) if excess_returns.std() > 0 else 0

def calculate_max_drawdown(prices: pd.Series) -> float:
    """Calculate maximum drawdown"""
    peak = prices.expanding().max()
    drawdown = (prices - peak) / peak
    return abs(drawdown.min())

# Create global analyzer instance
analyzer = AdvancedTechnicalAnalyzer()

# Export main functions
__all__ = [
    'AdvancedTechnicalAnalyzer', 'TechnicalAnalysis', 'TechnicalSignal', 'SignalType',
    'analyzer', 'calculate_kelly_criterion', 'calculate_sharpe_ratio', 'calculate_max_drawdown'
]
