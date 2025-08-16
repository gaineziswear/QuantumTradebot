/**
 * Advanced Technical Analysis Library
 * Hedge Fund Grade Technical Indicators
 */

export interface CandleData {
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
  timestamp: number;
}

export interface TechnicalSignal {
  signal: 'BUY' | 'SELL' | 'HOLD';
  strength: number; // 0-1
  confidence: number; // 0-1
  indicator: string;
  value: number;
  metadata?: any;
}

export interface TechnicalAnalysis {
  signals: TechnicalSignal[];
  overallSignal: 'BUY' | 'SELL' | 'HOLD';
  confidence: number;
  riskScore: number;
  supportLevels: number[];
  resistanceLevels: number[];
}

/**
 * Simple Moving Average
 */
export function calculateSMA(prices: number[], period: number): number[] {
  const sma: number[] = [];
  
  for (let i = period - 1; i < prices.length; i++) {
    const sum = prices.slice(i - period + 1, i + 1).reduce((a, b) => a + b, 0);
    sma.push(sum / period);
  }
  
  return sma;
}

/**
 * Exponential Moving Average
 */
export function calculateEMA(prices: number[], period: number): number[] {
  const ema: number[] = [];
  const multiplier = 2 / (period + 1);
  
  // First EMA is SMA
  const firstSMA = prices.slice(0, period).reduce((a, b) => a + b, 0) / period;
  ema.push(firstSMA);
  
  for (let i = period; i < prices.length; i++) {
    const currentEMA = (prices[i] - ema[ema.length - 1]) * multiplier + ema[ema.length - 1];
    ema.push(currentEMA);
  }
  
  return ema;
}

/**
 * Relative Strength Index (RSI)
 */
export function calculateRSI(prices: number[], period: number = 14): number[] {
  const rsi: number[] = [];
  const changes: number[] = [];
  
  // Calculate price changes
  for (let i = 1; i < prices.length; i++) {
    changes.push(prices[i] - prices[i - 1]);
  }
  
  for (let i = period - 1; i < changes.length; i++) {
    const gains = changes.slice(i - period + 1, i + 1).filter(change => change > 0);
    const losses = changes.slice(i - period + 1, i + 1).filter(change => change < 0).map(loss => Math.abs(loss));
    
    const avgGain = gains.length > 0 ? gains.reduce((a, b) => a + b, 0) / period : 0;
    const avgLoss = losses.length > 0 ? losses.reduce((a, b) => a + b, 0) / period : 0;
    
    if (avgLoss === 0) {
      rsi.push(100);
    } else {
      const rs = avgGain / avgLoss;
      rsi.push(100 - (100 / (1 + rs)));
    }
  }
  
  return rsi;
}

/**
 * MACD (Moving Average Convergence Divergence)
 */
export function calculateMACD(prices: number[], fastPeriod: number = 12, slowPeriod: number = 26, signalPeriod: number = 9) {
  const fastEMA = calculateEMA(prices, fastPeriod);
  const slowEMA = calculateEMA(prices, slowPeriod);
  
  // Align arrays (slow EMA starts later)
  const startIndex = slowPeriod - fastPeriod;
  const alignedFastEMA = fastEMA.slice(startIndex);
  
  const macdLine = alignedFastEMA.map((fast, i) => fast - slowEMA[i]);
  const signalLine = calculateEMA(macdLine, signalPeriod);
  
  // Align MACD line with signal line
  const alignedMACDLine = macdLine.slice(macdLine.length - signalLine.length);
  const histogram = alignedMACDLine.map((macd, i) => macd - signalLine[i]);
  
  return {
    macd: alignedMACDLine,
    signal: signalLine,
    histogram: histogram
  };
}

/**
 * Bollinger Bands
 */
export function calculateBollingerBands(prices: number[], period: number = 20, stdDev: number = 2) {
  const sma = calculateSMA(prices, period);
  const bands = {
    upper: [] as number[],
    middle: sma,
    lower: [] as number[]
  };
  
  for (let i = period - 1; i < prices.length; i++) {
    const slice = prices.slice(i - period + 1, i + 1);
    const mean = slice.reduce((a, b) => a + b, 0) / period;
    const variance = slice.reduce((a, b) => a + Math.pow(b - mean, 2), 0) / period;
    const standardDeviation = Math.sqrt(variance);
    
    bands.upper.push(mean + (stdDev * standardDeviation));
    bands.lower.push(mean - (stdDev * standardDeviation));
  }
  
  return bands;
}

/**
 * Stochastic Oscillator
 */
export function calculateStochastic(candles: CandleData[], kPeriod: number = 14, dPeriod: number = 3) {
  const stochastic = {
    k: [] as number[],
    d: [] as number[]
  };
  
  for (let i = kPeriod - 1; i < candles.length; i++) {
    const slice = candles.slice(i - kPeriod + 1, i + 1);
    const highest = Math.max(...slice.map(c => c.high));
    const lowest = Math.min(...slice.map(c => c.low));
    const current = candles[i].close;
    
    const k = ((current - lowest) / (highest - lowest)) * 100;
    stochastic.k.push(k);
  }
  
  // Calculate %D (SMA of %K)
  for (let i = dPeriod - 1; i < stochastic.k.length; i++) {
    const slice = stochastic.k.slice(i - dPeriod + 1, i + 1);
    const d = slice.reduce((a, b) => a + b, 0) / dPeriod;
    stochastic.d.push(d);
  }
  
  return stochastic;
}

/**
 * Average True Range (ATR) - Volatility indicator
 */
export function calculateATR(candles: CandleData[], period: number = 14): number[] {
  const trueRanges: number[] = [];
  
  for (let i = 1; i < candles.length; i++) {
    const current = candles[i];
    const previous = candles[i - 1];
    
    const tr1 = current.high - current.low;
    const tr2 = Math.abs(current.high - previous.close);
    const tr3 = Math.abs(current.low - previous.close);
    
    trueRanges.push(Math.max(tr1, tr2, tr3));
  }
  
  return calculateSMA(trueRanges, period);
}

/**
 * Volume Weighted Average Price (VWAP)
 */
export function calculateVWAP(candles: CandleData[]): number[] {
  const vwap: number[] = [];
  let cumulativeTPV = 0; // Typical Price * Volume
  let cumulativeVolume = 0;
  
  for (const candle of candles) {
    const typicalPrice = (candle.high + candle.low + candle.close) / 3;
    cumulativeTPV += typicalPrice * candle.volume;
    cumulativeVolume += candle.volume;
    
    vwap.push(cumulativeTPV / cumulativeVolume);
  }
  
  return vwap;
}

/**
 * Williams %R
 */
export function calculateWilliamsR(candles: CandleData[], period: number = 14): number[] {
  const williamsR: number[] = [];
  
  for (let i = period - 1; i < candles.length; i++) {
    const slice = candles.slice(i - period + 1, i + 1);
    const highest = Math.max(...slice.map(c => c.high));
    const lowest = Math.min(...slice.map(c => c.low));
    const current = candles[i].close;
    
    const wr = ((highest - current) / (highest - lowest)) * -100;
    williamsR.push(wr);
  }
  
  return williamsR;
}

/**
 * Fibonacci Retracement Levels
 */
export function calculateFibonacciLevels(high: number, low: number) {
  const range = high - low;
  
  return {
    level_0: high,
    level_236: high - (range * 0.236),
    level_382: high - (range * 0.382),
    level_500: high - (range * 0.500),
    level_618: high - (range * 0.618),
    level_786: high - (range * 0.786),
    level_100: low
  };
}

/**
 * Support and Resistance Levels
 */
export function findSupportResistance(candles: CandleData[], period: number = 20): { support: number[], resistance: number[] } {
  const support: number[] = [];
  const resistance: number[] = [];
  
  for (let i = period; i < candles.length - period; i++) {
    const current = candles[i];
    const leftSlice = candles.slice(i - period, i);
    const rightSlice = candles.slice(i + 1, i + period + 1);
    
    // Check for resistance (local high)
    const isLocalHigh = leftSlice.every(c => c.high <= current.high) && 
                        rightSlice.every(c => c.high <= current.high);
    
    // Check for support (local low)
    const isLocalLow = leftSlice.every(c => c.low >= current.low) && 
                       rightSlice.every(c => c.low >= current.low);
    
    if (isLocalHigh) {
      resistance.push(current.high);
    }
    
    if (isLocalLow) {
      support.push(current.low);
    }
  }
  
  return { support, resistance };
}

/**
 * Comprehensive Technical Analysis
 */
export function performTechnicalAnalysis(candles: CandleData[]): TechnicalAnalysis {
  if (candles.length < 50) {
    return {
      signals: [],
      overallSignal: 'HOLD',
      confidence: 0,
      riskScore: 1,
      supportLevels: [],
      resistanceLevels: []
    };
  }
  
  const prices = candles.map(c => c.close);
  const signals: TechnicalSignal[] = [];
  
  // RSI Analysis
  const rsi = calculateRSI(prices);
  const currentRSI = rsi[rsi.length - 1];
  
  if (currentRSI < 30) {
    signals.push({
      signal: 'BUY',
      strength: (30 - currentRSI) / 30,
      confidence: 0.7,
      indicator: 'RSI',
      value: currentRSI
    });
  } else if (currentRSI > 70) {
    signals.push({
      signal: 'SELL',
      strength: (currentRSI - 70) / 30,
      confidence: 0.7,
      indicator: 'RSI',
      value: currentRSI
    });
  }
  
  // MACD Analysis
  const macd = calculateMACD(prices);
  if (macd.macd.length > 0 && macd.signal.length > 0) {
    const currentMACD = macd.macd[macd.macd.length - 1];
    const currentSignal = macd.signal[macd.signal.length - 1];
    const histogram = macd.histogram[macd.histogram.length - 1];
    
    if (currentMACD > currentSignal && histogram > 0) {
      signals.push({
        signal: 'BUY',
        strength: Math.min(Math.abs(histogram) / 10, 1),
        confidence: 0.6,
        indicator: 'MACD',
        value: histogram
      });
    } else if (currentMACD < currentSignal && histogram < 0) {
      signals.push({
        signal: 'SELL',
        strength: Math.min(Math.abs(histogram) / 10, 1),
        confidence: 0.6,
        indicator: 'MACD',
        value: histogram
      });
    }
  }
  
  // Bollinger Bands Analysis
  const bb = calculateBollingerBands(prices);
  if (bb.upper.length > 0) {
    const currentPrice = prices[prices.length - 1];
    const upperBand = bb.upper[bb.upper.length - 1];
    const lowerBand = bb.lower[bb.lower.length - 1];
    const middleBand = bb.middle[bb.middle.length - 1];
    
    if (currentPrice <= lowerBand) {
      signals.push({
        signal: 'BUY',
        strength: (lowerBand - currentPrice) / (upperBand - lowerBand),
        confidence: 0.65,
        indicator: 'Bollinger Bands',
        value: currentPrice
      });
    } else if (currentPrice >= upperBand) {
      signals.push({
        signal: 'SELL',
        strength: (currentPrice - upperBand) / (upperBand - lowerBand),
        confidence: 0.65,
        indicator: 'Bollinger Bands',
        value: currentPrice
      });
    }
  }
  
  // Moving Average Analysis
  const sma20 = calculateSMA(prices, 20);
  const sma50 = calculateSMA(prices, 50);
  
  if (sma20.length > 0 && sma50.length > 0) {
    const currentSMA20 = sma20[sma20.length - 1];
    const currentSMA50 = sma50[sma50.length - 1];
    const currentPrice = prices[prices.length - 1];
    
    // Golden Cross / Death Cross
    if (currentSMA20 > currentSMA50 && currentPrice > currentSMA20) {
      signals.push({
        signal: 'BUY',
        strength: 0.7,
        confidence: 0.8,
        indicator: 'Moving Average Cross',
        value: currentSMA20 - currentSMA50
      });
    } else if (currentSMA20 < currentSMA50 && currentPrice < currentSMA20) {
      signals.push({
        signal: 'SELL',
        strength: 0.7,
        confidence: 0.8,
        indicator: 'Moving Average Cross',
        value: currentSMA50 - currentSMA20
      });
    }
  }
  
  // Support/Resistance Analysis
  const { support, resistance } = findSupportResistance(candles);
  
  // Calculate overall signal
  const buySignals = signals.filter(s => s.signal === 'BUY');
  const sellSignals = signals.filter(s => s.signal === 'SELL');
  
  const buyWeight = buySignals.reduce((sum, s) => sum + (s.strength * s.confidence), 0);
  const sellWeight = sellSignals.reduce((sum, s) => sum + (s.strength * s.confidence), 0);
  
  let overallSignal: 'BUY' | 'SELL' | 'HOLD' = 'HOLD';
  let confidence = 0;
  
  if (buyWeight > sellWeight && buyWeight > 0.5) {
    overallSignal = 'BUY';
    confidence = Math.min(buyWeight, 1);
  } else if (sellWeight > buyWeight && sellWeight > 0.5) {
    overallSignal = 'SELL';
    confidence = Math.min(sellWeight, 1);
  }
  
  // Calculate risk score
  const atr = calculateATR(candles);
  const currentATR = atr.length > 0 ? atr[atr.length - 1] : 0;
  const currentPrice = prices[prices.length - 1];
  const riskScore = Math.min((currentATR / currentPrice) * 100, 1);
  
  return {
    signals,
    overallSignal,
    confidence,
    riskScore,
    supportLevels: support.slice(-5), // Last 5 support levels
    resistanceLevels: resistance.slice(-5) // Last 5 resistance levels
  };
}

export default {
  calculateSMA,
  calculateEMA,
  calculateRSI,
  calculateMACD,
  calculateBollingerBands,
  calculateStochastic,
  calculateATR,
  calculateVWAP,
  calculateWilliamsR,
  calculateFibonacciLevels,
  findSupportResistance,
  performTechnicalAnalysis
};
