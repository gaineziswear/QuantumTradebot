import React, { useState, useEffect, useCallback, useMemo } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useNavigate } from 'react-router-dom';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { LineChart, Line, XAxis, YAxis, ResponsiveContainer, Tooltip, AreaChart, Area, ComposedChart, Bar } from 'recharts';
import { 
  Play, 
  Square, 
  Plus, 
  Minus,
  TrendingUp, 
  TrendingDown,
  Activity, 
  Brain, 
  History, 
  LogOut, 
  ArrowUpRight, 
  ArrowDownRight, 
  Target, 
  BarChart3, 
  Zap, 
  RefreshCw,
  Clock,
  DollarSign,
  TrendingUpIcon,
  Wallet,
  Eye,
  Database,
  Shield,
  Cpu
} from 'lucide-react';
import { apiClient, useAPI } from '@/lib/api';
import { formatINR, formatINRWithDecimals, fetchUSDToINRRate, getCurrentUSDToINRRate } from '@/lib/currency';
import type {
  TradingStatus,
  PerformanceMetrics,
  Trade,
  AIStatus,
  Portfolio,
  AutomationStatus
} from '@shared/api';

export default function Dashboard() {
  const navigate = useNavigate();
  const api = useAPI();
  
  // State management
  const [tradingStatus, setTradingStatus] = useState<TradingStatus | null>(null);
  const [performance, setPerformance] = useState<PerformanceMetrics | null>(null);
  const [trades, setTrades] = useState<Trade[]>([]);
  const [aiStatus, setAIStatus] = useState<AIStatus | null>(null);
  const [portfolio, setPortfolio] = useState<Portfolio | null>(null);
  const [exchangeRate, setExchangeRate] = useState<number>(getCurrentUSDToINRRate());
  const [automationStatus, setAutomationStatus] = useState<AutomationStatus | null>(null);
  const [livePrices, setLivePrices] = useState<Record<string, number>>({});
  
  // UI State
  const [capitalAmount, setCapitalAmount] = useState('');
  const [addFundOpen, setAddFundOpen] = useState(false);
  const [viewMode, setViewMode] = useState<'daily' | 'monthly'>('daily');
  const [isLoading, setIsLoading] = useState(true);
  const [lastUpdate, setLastUpdate] = useState<Date>(new Date());
  const [currentTime, setCurrentTime] = useState<Date>(new Date());
  const [livePnL, setLivePnL] = useState(0);

  // Mobile-specific optimization
  const [isMobile, setIsMobile] = useState(window.innerWidth < 768);

  // Real-time clock
  useEffect(() => {
    const timer = setInterval(() => {
      setCurrentTime(new Date());
    }, 1000);

    return () => clearInterval(timer);
  }, []);

  // Mobile detection and optimization
  useEffect(() => {
    const handleResize = () => {
      setIsMobile(window.innerWidth < 768);
    };

    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, []);

  // Memoized load function to prevent unnecessary recreations
  const loadData = useCallback(async () => {
    try {
      if (isLoading) setIsLoading(true);

      // Load all data in parallel for instant updates including automation status
      const [statusData, performanceData, tradesData, aiData, portfolioData, newRate, automationData, pricesData] = await Promise.all([
        api.getTradingStatus(),
        api.getPerformanceMetrics(),
        api.getRecentTrades(20),
        api.getAIStatus(),
        api.getPortfolio(),
        fetchUSDToINRRate(),
        fetch('/api/automation/status').then(res => res.json()).catch(() => null),
        fetch('/api/automation/prices').then(res => res.json()).catch(() => ({}))
      ]);

      setTradingStatus(statusData);
      setPerformance(performanceData);
      setTrades(tradesData);
      setAIStatus(aiData);
      setPortfolio(portfolioData);
      setExchangeRate(newRate);
      setAutomationStatus(automationData);
      setLivePrices(pricesData.prices || {});
      setLastUpdate(new Date());

      // Calculate live P&L
      const totalPnL = tradesData.reduce((sum, trade) => sum + (trade.pnl || 0), 0);
      setLivePnL(totalPnL);

    } catch (error) {
      console.error('Data load error:', error);
    } finally {
      setIsLoading(false);
    }
  }, [api, isLoading]);

  // Auto-update data for instant backend updates
  useEffect(() => {
    // Initial load
    loadData();

    // Adaptive polling: slower on mobile to save battery and data
    const pollInterval = isMobile ? 5000 : 2000; // 5s on mobile, 2s on desktop
    const interval = setInterval(loadData, pollInterval);

    return () => clearInterval(interval);
  }, [loadData, isMobile]);

  // Trading controls - Enhanced for hedge fund automation
  const handleStart = async () => {
    try {
      // Use new hedge fund automation endpoint
      const response = await fetch('/api/automation/start', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' }
      });
      const result = await response.json();

      if (result.success) {
        console.log('🚀 Hedge fund automation started:', result.message);
      } else {
        console.error('Failed to start automation:', result.message);
      }
    } catch (error) {
      console.error('Start automation failed:', error);
    }
  };

  const handleStop = async () => {
    try {
      const response = await fetch('/api/automation/stop', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' }
      });
      const result = await response.json();

      if (result.success) {
        console.log('🛑 Automation stopped:', result.message);
      } else {
        console.error('Failed to stop automation:', result.message);
      }
    } catch (error) {
      console.error('Stop automation failed:', error);
    }
  };

  const handleGoLive = async () => {
    try {
      const response = await fetch('/api/automation/toggle-mode', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ mode: 'live' })
      });
      const result = await response.json();

      if (result.success) {
        console.log('🔴 Switched to LIVE trading:', result.message);
      } else {
        console.error('Failed to switch to live mode:', result.message);
      }
    } catch (error) {
      console.error('Go live failed:', error);
    }
  };

  const handleAddCapital = async () => {
    if (capitalAmount && parseFloat(capitalAmount) > 0) {
      try {
        await api.addCapital(parseFloat(capitalAmount));
        setCapitalAmount('');
        setAddFundOpen(false);
      } catch (error) {
        console.error('Add capital failed:', error);
      }
    }
  };

  const handleSubtractCapital = async () => {
    if (capitalAmount && parseFloat(capitalAmount) > 0) {
      try {
        await api.addCapital(-parseFloat(capitalAmount));
        setCapitalAmount('');
        setAddFundOpen(false);
      } catch (error) {
        console.error('Subtract capital failed:', error);
      }
    }
  };

  const handleLogout = () => {
    api.logout();
    navigate('/login');
  };

  if (isLoading) {
    return (
      <div className="h-screen bg-gradient-to-br from-gray-50 to-white flex items-center justify-center">
        <motion.div 
          initial={{ opacity: 0, scale: 0.9 }}
          animate={{ opacity: 1, scale: 1 }}
          className="text-center"
        >
          <div className="w-12 h-12 border-2 border-gray-300 border-t-gray-900 rounded-full animate-spin mx-auto mb-4"></div>
          <p className="text-gray-600 font-medium">Loading Trading Interface...</p>
        </motion.div>
      </div>
    );
  }

  // Memoize expensive calculations
  const { currentCapital, totalPnL, dailyPnL, isProfitable } = useMemo(() => {
    const capital = tradingStatus?.current_capital || 0;
    const total = performance?.total_pnl || livePnL;
    const daily = performance?.daily_pnl || 0;
    const profitable = total >= 0;

    return {
      currentCapital: capital,
      totalPnL: total,
      dailyPnL: daily,
      isProfitable: profitable
    };
  }, [tradingStatus?.current_capital, performance?.total_pnl, performance?.daily_pnl, livePnL]);

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 to-white text-gray-900 flex flex-col font-['Inter',sans-serif] md:overflow-hidden mobile-optimized">
      <div className="h-full flex flex-col max-w-[2000px] mx-auto w-full mobile-safe-area">
        
        {/* Ultra-Professional Header - Mobile Optimized */}
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          className="flex-shrink-0 bg-white border-b border-gray-100 shadow-sm mobile-safe-area"
        >
          <div className="px-3 sm:px-4 md:px-6 py-4 phone-p-2">
            <div className="flex justify-between items-center">

              {/* Left: Bot Status & Capital - Responsive */}
              <div className="flex items-center gap-2 md:gap-6">
                <div className="flex items-center gap-2 md:gap-3">
                  <div className="relative">
                    <div className={`w-3 h-3 rounded-full ${tradingStatus?.is_running ? 'bg-green-500 animate-pulse' : 'bg-gray-400'}`} />
                    {tradingStatus?.is_running && (
                      <div className="absolute inset-0 w-3 h-3 rounded-full bg-green-500 animate-ping opacity-75" />
                    )}
                  </div>
                  <span className="text-xs md:text-sm font-semibold text-gray-700">
                    {tradingStatus?.is_running ? 'ACTIVE' : 'STOPPED'}
                  </span>
                </div>

                <div className="h-4 md:h-6 w-px bg-gray-200" />

                <div className="flex items-center gap-1 md:gap-2">
                  <Wallet className="w-3 md:w-4 h-3 md:h-4 text-gray-500" />
                  <span className="text-sm md:text-lg font-bold text-gray-900">{formatINR(currentCapital)}</span>
                  <span className="hidden md:inline text-xs text-gray-500 uppercase tracking-wide">Capital</span>
                </div>

                <div className="hidden md:block h-6 w-px bg-gray-200" />

                <div className="hidden md:flex items-center gap-2">
                  <div className={`w-2 h-2 rounded-full ${automationStatus?.trading_mode === 'live' ? 'bg-red-500' : 'bg-yellow-500'}`} />
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={async () => {
                      const newMode = automationStatus?.trading_mode === 'live' ? 'testnet' : 'live';
                      try {
                        const response = await fetch('/api/automation/toggle-mode', {
                          method: 'POST',
                          headers: { 'Content-Type': 'application/json' },
                          body: JSON.stringify({ mode: newMode })
                        });
                        const result = await response.json();
                        if (result.success) {
                          console.log(`Switched to ${newMode.toUpperCase()} mode`);
                        }
                      } catch (error) {
                        console.error('Failed to toggle mode:', error);
                      }
                    }}
                    className="text-sm font-medium hover:bg-gray-100 px-2 py-1 rounded"
                  >
                    {automationStatus?.trading_mode === 'live' ? 'LIVE' : 'TESTNET'}
                  </Button>
                </div>
              </div>

              {/* Right: Time & Controls - Responsive */}
              <div className="flex items-center gap-2 md:gap-4">
                <div className="text-right">
                  <div className="text-xs md:text-sm font-mono text-gray-900">
                    {currentTime.toLocaleTimeString()}
                  </div>
                  <div className="hidden md:block text-xs text-gray-500">
                    USD/INR: {exchangeRate.toFixed(2)}
                  </div>
                </div>

                <div className="h-4 md:h-6 w-px bg-gray-200" />

                <Button
                  variant="ghost"
                  size="sm"
                  onClick={handleLogout}
                  className="text-gray-600 hover:text-gray-900 hover:bg-gray-100 p-1 md:p-2"
                >
                  <LogOut className="w-3 md:w-4 h-3 md:h-4" />
                </Button>
              </div>
            </div>
          </div>
        </motion.div>

        {/* Main Content Area - Mobile Optimized */}
        <div className="flex-1 md:overflow-hidden overflow-y-auto mobile-scroll">
          <Tabs defaultValue="main" className="h-full flex flex-col landscape-compact">

            {/* Tab Navigation - Mobile Optimized */}
            <div className="bg-white border-b border-gray-100 px-3 sm:px-4 md:px-6 mobile-safe-area">
              <TabsList className="bg-transparent border-none h-12 md:h-12 p-0 gap-2 sm:gap-4 md:gap-8 overflow-x-auto mobile-scroll">
                {[
                  { id: 'main', label: 'Trading', icon: Activity },
                  { id: 'performance', label: 'Analytics', icon: TrendingUp },
                  { id: 'portfolio', label: 'Portfolio', icon: BarChart3 },
                  { id: 'training', label: 'AI Model', icon: Brain },
                  { id: 'history', label: 'History', icon: History }
                ].map((tab) => (
                  <TabsTrigger
                    key={tab.id}
                    value={tab.id}
                    className="bg-transparent border-none data-[state=active]:bg-transparent data-[state=active]:shadow-none data-[state=active]:border-b-2 data-[state=active]:border-gray-900 data-[state=active]:text-gray-900 text-gray-600 hover:text-gray-800 pb-2 md:pb-3 px-2 sm:px-0 rounded-none font-medium text-sm md:text-base whitespace-nowrap mobile-button mobile-tap min-h-[44px] flex items-center"
                  >
                    <tab.icon className="w-3 md:w-4 h-3 md:h-4 mr-1 md:mr-2" />
                    <span className="hidden sm:inline">{tab.label}</span>
                  </TabsTrigger>
                ))}
              </TabsList>
            </div>

            {/* Main Trading Tab - Responsive Grid */}
            <TabsContent value="main" className="flex-1 md:overflow-hidden m-0 p-0">
              <div className="h-full p-4 md:p-6">
                <div className="h-full flex flex-col lg:grid lg:grid-cols-12 gap-4 md:gap-6">
                  
                  {/* Mobile: Stacked Layout, Desktop: 3-column Grid */}

                  {/* Top Section on Mobile - Live Trades Feed (was right column) */}
                  <div className="lg:hidden order-1">
                    <Card className="border-0 shadow-lg bg-white rounded-2xl">
                      <CardHeader className="pb-4">
                        <CardTitle className="text-lg font-bold text-gray-900 flex items-center gap-2">
                          <Activity className="w-5 h-5 animate-pulse" />
                          Live Trades
                        </CardTitle>
                      </CardHeader>
                      <CardContent>
                        <div className="space-y-2 max-h-64 overflow-y-auto">
                          <AnimatePresence>
                            {trades.length > 0 ? trades.slice(0, 5).map((trade, index) => (
                              <motion.div
                                key={trade.id}
                                initial={{ opacity: 0, x: -20 }}
                                animate={{ opacity: 1, x: 0 }}
                                exit={{ opacity: 0, x: 20 }}
                                transition={{ delay: index * 0.02 }}
                                className="flex items-center justify-between p-3 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors"
                              >
                                <div className="flex items-center gap-3">
                                  <Badge
                                    className={`text-xs px-2 py-1 font-semibold ${
                                      trade.side === 'BUY'
                                        ? 'bg-green-100 text-green-700'
                                        : 'bg-red-100 text-red-700'
                                    }`}
                                  >
                                    {trade.side}
                                  </Badge>
                                  <div>
                                    <div className="font-medium text-sm text-gray-900">{trade.symbol}</div>
                                    <div className="text-xs text-gray-500">
                                      {new Date(trade.timestamp).toLocaleTimeString()}
                                    </div>
                                  </div>
                                </div>
                                <div className="text-right">
                                  <div className="text-sm font-medium text-gray-900">{formatINR(trade.entry_price)}</div>
                                  {trade.pnl && (
                                    <div className={`text-sm font-bold ${trade.pnl > 0 ? 'text-green-600' : 'text-red-600'}`}>
                                      {trade.pnl > 0 ? '+' : ''}{formatINR(trade.pnl)}
                                    </div>
                                  )}
                                </div>
                              </motion.div>
                            )) : (
                              <div className="text-center py-8 text-gray-400">
                                <Activity className="w-12 h-12 mx-auto mb-3 opacity-50" />
                                <p className="text-sm font-medium">No trades yet</p>
                                <p className="text-xs">Waiting for AI signals</p>
                              </div>
                            )}
                          </AnimatePresence>
                        </div>
                      </CardContent>
                    </Card>
                  </div>

                  {/* Left Column - Controls & Stats */}
                  <div className="lg:col-span-3 order-2 lg:order-1 space-y-4 lg:space-y-6">

                    {/* Trading Controls */}
                    <Card className="border-0 shadow-lg bg-white rounded-2xl">
                      <CardHeader className="pb-4">
                        <CardTitle className="text-base lg:text-lg font-bold text-gray-900 flex items-center gap-2">
                          <Target className="w-4 lg:w-5 h-4 lg:h-5" />
                          Controls
                        </CardTitle>
                      </CardHeader>
                      <CardContent className="space-y-3">
                        <Button
                          onClick={handleStart}
                          disabled={automationStatus?.is_running}
                          className="w-full h-12 lg:h-12 bg-gray-900 hover:bg-black text-white font-semibold rounded-xl transition-all shadow-md disabled:opacity-50 text-sm lg:text-base mobile-button mobile-tap"
                        >
                          {automationStatus?.is_running ? (
                            <>
                              <RefreshCw className="w-3 lg:w-4 h-3 lg:h-4 mr-2 animate-spin" />
                              {automationStatus.current_phase === 'data_fetching' ? 'FETCHING DATA' :
                               automationStatus.current_phase === 'training' ? 'TRAINING AI' :
                               automationStatus.current_phase === 'trading' ? 'TRADING' :
                               automationStatus.current_phase === 'risk_monitoring' ? 'ACTIVE' : 'RUNNING'}
                            </>
                          ) : (
                            <>
                              <Play className="w-3 lg:w-4 h-3 lg:h-4 mr-2" />
                              START HEDGE FUND
                            </>
                          )}
                        </Button>

                        <Button
                          onClick={handleStop}
                          disabled={!automationStatus?.is_running}
                          variant="outline"
                          className="w-full h-12 lg:h-12 border-2 border-gray-200 hover:bg-gray-50 font-semibold rounded-xl transition-all disabled:opacity-50 text-sm lg:text-base mobile-button mobile-tap"
                        >
                          <Square className="w-3 lg:w-4 h-3 lg:h-4 mr-2" />
                          STOP AUTOMATION
                        </Button>

                        {automationStatus?.trading_mode !== 'live' && (
                          <Button
                            onClick={handleGoLive}
                            variant="outline"
                            className="w-full h-12 lg:h-12 border-2 border-red-200 text-red-600 hover:bg-red-50 font-semibold rounded-xl transition-all text-sm lg:text-base mobile-button mobile-tap"
                          >
                            <ArrowUpRight className="w-3 lg:w-4 h-3 lg:h-4 mr-2" />
                            SWITCH TO LIVE
                          </Button>
                        )}

                        <Dialog open={addFundOpen} onOpenChange={setAddFundOpen}>
                          <DialogTrigger asChild>
                            <Button
                              variant="outline"
                              className="w-full h-12 lg:h-12 border-2 border-gray-200 hover:bg-gray-50 font-semibold rounded-xl transition-all text-sm lg:text-base mobile-button mobile-tap"
                            >
                              <DollarSign className="w-3 lg:w-4 h-3 lg:h-4 mr-2" />
                              MANAGE CAPITAL
                            </Button>
                          </DialogTrigger>
                          <DialogContent className="sm:max-w-md">
                            <DialogHeader>
                              <DialogTitle>Manage Capital</DialogTitle>
                            </DialogHeader>
                            <div className="space-y-4">
                              <div>
                                <Input
                                  type="number"
                                  value={capitalAmount}
                                  onChange={(e) => setCapitalAmount(e.target.value)}
                                  placeholder="Enter amount (₹)"
                                  className="text-center text-lg h-12"
                                />
                              </div>
                              <div className="grid grid-cols-2 gap-3">
                                <Button
                                  onClick={handleAddCapital}
                                  className="h-11 bg-green-600 hover:bg-green-700 text-white font-semibold"
                                >
                                  <Plus className="w-4 h-4 mr-2" />
                                  Add
                                </Button>
                                <Button
                                  onClick={handleSubtractCapital}
                                  variant="outline"
                                  className="h-11 border-red-200 text-red-600 hover:bg-red-50 font-semibold"
                                >
                                  <Minus className="w-4 h-4 mr-2" />
                                  Remove
                                </Button>
                              </div>
                            </div>
                          </DialogContent>
                        </Dialog>
                      </CardContent>
                    </Card>

                    {/* Automation Status */}
                    <Card className="border-0 shadow-lg bg-white rounded-2xl">
                      <CardHeader className="pb-4">
                        <CardTitle className="text-base lg:text-lg font-bold text-gray-900 flex items-center gap-2">
                          <Cpu className="w-4 lg:w-5 h-4 lg:h-5" />
                          Automation
                        </CardTitle>
                      </CardHeader>
                      <CardContent className="space-y-4">
                        <div className="space-y-3">
                          <div className="flex items-center justify-between">
                            <span className="text-sm text-gray-600">Status</span>
                            <div className="flex items-center gap-2">
                              <div className={`w-2 h-2 rounded-full ${automationStatus?.is_running ? 'bg-green-500 animate-pulse' : 'bg-gray-400'}`} />
                              <span className="text-sm font-medium">
                                {automationStatus?.is_running ? 'ACTIVE' : 'IDLE'}
                              </span>
                            </div>
                          </div>

                          <div className="flex items-center justify-between">
                            <span className="text-sm text-gray-600">Phase</span>
                            <span className="text-sm font-medium capitalize">
                              {automationStatus?.current_phase || 'Idle'}
                            </span>
                          </div>

                          <div className="space-y-2">
                            <div className="flex justify-between items-center">
                              <span className="text-sm text-gray-600">Progress</span>
                              <span className="text-sm font-bold text-gray-900">
                                {automationStatus?.progress_percentage?.toFixed(0) || '0'}%
                              </span>
                            </div>
                            <div className="w-full bg-gray-200 rounded-full h-2">
                              <div
                                className="bg-gradient-to-r from-blue-500 to-purple-600 h-2 rounded-full transition-all duration-500"
                                style={{ width: `${automationStatus?.progress_percentage || 0}%` }}
                              />
                            </div>
                          </div>

                          <div className="pt-3 border-t border-gray-100">
                            <div className="text-xs text-gray-500 mb-1">Current Action</div>
                            <div className="text-sm font-medium text-gray-900 leading-tight">
                              {automationStatus?.last_action || 'Waiting for activation'}
                            </div>
                          </div>
                        </div>
                      </CardContent>
                    </Card>

                    {/* Live Stats */}
                    <Card className="border-0 shadow-lg bg-white rounded-2xl">
                      <CardHeader className="pb-4">
                        <CardTitle className="text-base lg:text-lg font-bold text-gray-900 flex items-center gap-2">
                          <Activity className="w-4 lg:w-5 h-4 lg:h-5" />
                          Live Stats
                        </CardTitle>
                      </CardHeader>
                      <CardContent className="space-y-4">
                        <div className="grid grid-cols-2 gap-4">
                          <div className="text-center">
                            <div className="text-xl lg:text-2xl font-bold text-gray-900">{tradingStatus?.active_positions || 0}</div>
                            <div className="text-xs text-gray-500 mt-1">Positions</div>
                          </div>
                          <div className="text-center">
                            <div className="text-xl lg:text-2xl font-bold text-gray-900">{tradingStatus?.total_trades || 0}</div>
                            <div className="text-xs text-gray-500 mt-1">Trades</div>
                          </div>
                        </div>

                        <div className="pt-4 border-t border-gray-100">
                          <div className="text-center">
                            <div className="text-lg lg:text-xl font-bold text-gray-900">{tradingStatus?.win_rate?.toFixed(1) || '0'}%</div>
                            <div className="text-xs text-gray-500 mt-1">Win Rate</div>
                          </div>
                        </div>
                      </CardContent>
                    </Card>

                    {/* Market Scanner - Hidden on mobile */}
                    <Card className="hidden lg:block border-0 shadow-lg bg-white rounded-2xl">
                      <CardHeader className="pb-4">
                        <CardTitle className="text-lg font-bold text-gray-900 flex items-center gap-2">
                          <Eye className="w-5 h-5" />
                          Market Focus
                        </CardTitle>
                      </CardHeader>
                      <CardContent>
                        <div className="space-y-3">
                          {['BTC/USDT', 'ETH/USDT', 'BNB/USDT'].map((symbol, index) => (
                            <div key={symbol} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                              <span className="font-medium text-sm">{symbol}</span>
                              <div className="text-xs text-gray-500">Live</div>
                            </div>
                          ))}
                        </div>
                      </CardContent>
                    </Card>
                  </div>

                  {/* Center Column - Performance Chart and Mobile P&L */}
                  <div className="lg:col-span-6 order-3 lg:order-2 space-y-4 lg:space-y-6">

                    {/* Large P&L Display - Smaller on mobile */}
                    <Card className="border-0 shadow-lg bg-gradient-to-r from-gray-50 to-white rounded-2xl">
                      <CardContent className="p-4 lg:p-8 text-center">
                        <div className="mb-3 lg:mb-4">
                          <div className="text-xs lg:text-sm text-gray-500 uppercase tracking-wide mb-2">Total P&L</div>
                          <motion.div
                            key={totalPnL}
                            initial={{ scale: 0.95 }}
                            animate={{ scale: 1 }}
                            transition={{ duration: 0.3 }}
                            className={`text-3xl lg:text-5xl font-bold ${isProfitable ? 'text-green-600' : 'text-red-600'}`}
                          >
                            {isProfitable ? '+' : ''}{formatINR(totalPnL)}
                          </motion.div>
                        </div>

                        <div className="flex justify-center gap-4 lg:gap-8">
                          <div className="text-center">
                            <div className="text-xs lg:text-sm text-gray-500">Daily</div>
                            <div className={`text-lg lg:text-xl font-semibold ${dailyPnL >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                              {dailyPnL >= 0 ? '+' : ''}{formatINR(dailyPnL)}
                            </div>
                          </div>
                          <div className="text-center">
                            <div className="text-xs lg:text-sm text-gray-500">Monthly</div>
                            <div className={`text-lg lg:text-xl font-semibold ${totalPnL >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                              {totalPnL >= 0 ? '+' : ''}{formatINR(totalPnL)}
                            </div>
                          </div>
                        </div>
                      </CardContent>
                    </Card>

                    {/* Performance Chart */}
                    <Card className="border-0 shadow-lg bg-white rounded-2xl">
                      <CardHeader className="pb-4">
                        <div className="flex justify-between items-center">
                          <CardTitle className="text-base lg:text-lg font-bold text-gray-900 flex items-center gap-2">
                            <BarChart3 className="w-4 lg:w-5 h-4 lg:h-5" />
                            Performance Chart
                          </CardTitle>
                          <div className="flex gap-2">
                            <Button
                              variant={viewMode === 'daily' ? 'default' : 'ghost'}
                              size="sm"
                              onClick={() => setViewMode('daily')}
                              className="text-xs h-6 lg:h-8 px-2 lg:px-4"
                            >
                              Daily
                            </Button>
                            <Button
                              variant={viewMode === 'monthly' ? 'default' : 'ghost'}
                              size="sm"
                              onClick={() => setViewMode('monthly')}
                              className="text-xs h-6 lg:h-8 px-2 lg:px-4"
                            >
                              Monthly
                            </Button>
                          </div>
                        </div>
                      </CardHeader>
                      <CardContent>
                        <div className="h-64 lg:h-80">
                          {trades.length > 0 ? (
                            <ResponsiveContainer width="100%" height="100%">
                              <ComposedChart data={trades.map((trade, i) => ({
                                name: `${i + 1}`,
                                pnl: (trade.pnl || 0) * exchangeRate,
                                cumulative: trades.slice(0, i + 1).reduce((sum, t) => sum + ((t.pnl || 0) * exchangeRate), 0)
                              }))}>
                                <defs>
                                  <linearGradient id="pnlGradient" x1="0" y1="0" x2="0" y2="1">
                                    <stop offset="5%" stopColor="#059669" stopOpacity={0.3}/>
                                    <stop offset="95%" stopColor="#059669" stopOpacity={0.05}/>
                                  </linearGradient>
                                </defs>
                                <XAxis dataKey="name" tick={{ fontSize: 12 }} stroke="#6B7280" />
                                <YAxis tick={{ fontSize: 12 }} stroke="#6B7280" />
                                <Tooltip
                                  formatter={(value: number, name: string) => [
                                    formatINR(value),
                                    name === 'pnl' ? 'Trade P&L' : 'Cumulative P&L'
                                  ]}
                                  labelStyle={{ color: '#374151' }}
                                  contentStyle={{
                                    backgroundColor: 'white',
                                    border: '1px solid #E5E7EB',
                                    borderRadius: '8px'
                                  }}
                                />
                                <Bar dataKey="pnl" fill="#10B981" fillOpacity={0.6} />
                                <Line
                                  type="monotone"
                                  dataKey="cumulative"
                                  stroke="#059669"
                                  strokeWidth={3}
                                  dot={{ fill: '#059669', strokeWidth: 2, r: 4 }}
                                />
                              </ComposedChart>
                            </ResponsiveContainer>
                          ) : (
                            <div className="flex items-center justify-center h-full text-gray-400">
                              <div className="text-center">
                                <BarChart3 className="w-12 lg:w-16 h-12 lg:h-16 mx-auto mb-4 opacity-50" />
                                <p className="text-base lg:text-lg font-medium">Performance Chart</p>
                                <p className="text-sm">Updates live when trading</p>
                              </div>
                            </div>
                          )}
                        </div>
                      </CardContent>
                    </Card>
                  </div>

                  {/* Right Column - AI Insights (Desktop only - Live Trades moved to center) */}
                  <div className="hidden lg:block lg:col-span-3 order-4 lg:order-3 space-y-6">

                    {/* AI Model Status */}
                    <Card className="border-0 shadow-lg bg-white rounded-2xl">
                      <CardHeader className="pb-4">
                        <CardTitle className="text-lg font-bold text-gray-900 flex items-center gap-2">
                          <Brain className="w-5 h-5" />
                          AI Insights
                        </CardTitle>
                      </CardHeader>
                      <CardContent className="space-y-4">
                        <div>
                          <div className="flex justify-between items-center mb-2">
                            <span className="text-sm text-gray-600">Training Progress</span>
                            <span className="text-sm font-bold text-gray-900">{aiStatus?.progress_percentage?.toFixed(0) || '0'}%</span>
                          </div>
                          <div className="w-full bg-gray-200 rounded-full h-2">
                            <div
                              className="bg-gradient-to-r from-blue-500 to-purple-600 h-2 rounded-full transition-all duration-500"
                              style={{ width: `${aiStatus?.progress_percentage || 0}%` }}
                            />
                          </div>
                        </div>

                        <div className="grid grid-cols-2 gap-3">
                          <div className="text-center p-3 bg-gray-50 rounded-lg">
                            <div className="text-lg font-bold text-gray-900">{aiStatus?.model_confidence || 'N/A'}</div>
                            <div className="text-xs text-gray-500 mt-1">Confidence</div>
                          </div>
                          <div className="text-center p-3 bg-gray-50 rounded-lg">
                            <div className="text-lg font-bold text-gray-900">{aiStatus?.is_training ? 'Training' : 'Ready'}</div>
                            <div className="text-xs text-gray-500 mt-1">Status</div>
                          </div>
                        </div>

                        <div className="pt-3 border-t border-gray-100">
                          <div className="text-xs text-gray-500 mb-2">Last Retrain</div>
                          <div className="text-sm font-medium text-gray-900">
                            {aiStatus?.last_training ? new Date(aiStatus.last_training).toLocaleDateString() : 'Never'}
                          </div>
                        </div>
                      </CardContent>
                    </Card>

                    {/* Live Trade Feed - Desktop Version */}
                    <Card className="border-0 shadow-lg bg-white rounded-2xl flex-1">
                      <CardHeader className="pb-4">
                        <CardTitle className="text-lg font-bold text-gray-900 flex items-center gap-2">
                          <Activity className="w-5 h-5 animate-pulse" />
                          Live Trades
                        </CardTitle>
                      </CardHeader>
                      <CardContent>
                        <div className="space-y-2 max-h-96 overflow-y-auto">
                          <AnimatePresence>
                            {trades.length > 0 ? trades.slice(0, 8).map((trade, index) => (
                              <motion.div
                                key={trade.id}
                                initial={{ opacity: 0, x: -20 }}
                                animate={{ opacity: 1, x: 0 }}
                                exit={{ opacity: 0, x: 20 }}
                                transition={{ delay: index * 0.02 }}
                                className="flex items-center justify-between p-3 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors"
                              >
                                <div className="flex items-center gap-3">
                                  <Badge
                                    className={`text-xs px-2 py-1 font-semibold ${
                                      trade.side === 'BUY'
                                        ? 'bg-green-100 text-green-700'
                                        : 'bg-red-100 text-red-700'
                                    }`}
                                  >
                                    {trade.side}
                                  </Badge>
                                  <div>
                                    <div className="font-medium text-sm text-gray-900">{trade.symbol}</div>
                                    <div className="text-xs text-gray-500">
                                      {new Date(trade.timestamp).toLocaleTimeString()}
                                    </div>
                                  </div>
                                </div>
                                <div className="text-right">
                                  <div className="text-sm font-medium text-gray-900">{formatINR(trade.entry_price)}</div>
                                  {trade.pnl && (
                                    <div className={`text-sm font-bold ${trade.pnl > 0 ? 'text-green-600' : 'text-red-600'}`}>
                                      {trade.pnl > 0 ? '+' : ''}{formatINR(trade.pnl)}
                                    </div>
                                  )}
                                </div>
                              </motion.div>
                            )) : (
                              <div className="text-center py-8 text-gray-400">
                                <Activity className="w-12 h-12 mx-auto mb-3 opacity-50" />
                                <p className="text-sm font-medium">No trades yet</p>
                                <p className="text-xs">Waiting for AI signals</p>
                              </div>
                            )}
                          </AnimatePresence>
                        </div>
                      </CardContent>
                    </Card>
                  </div>
                </div>
              </div>
            </TabsContent>

            {/* Other Tabs - Simplified */}
            <TabsContent value="performance" className="flex-1 overflow-hidden m-0 p-0">
              <div className="h-full flex items-center justify-center">
                <div className="text-center">
                  <TrendingUp className="w-20 h-20 mx-auto mb-6 text-gray-300" />
                  <h3 className="text-2xl font-bold text-gray-900 mb-2">Performance Analytics</h3>
                  <p className="text-gray-600">Detailed analytics available when trading is active</p>
                </div>
              </div>
            </TabsContent>

            <TabsContent value="portfolio" className="flex-1 overflow-hidden m-0 p-0">
              <div className="h-full flex items-center justify-center">
                <div className="text-center">
                  <BarChart3 className="w-20 h-20 mx-auto mb-6 text-gray-300" />
                  <h3 className="text-2xl font-bold text-gray-900 mb-2">Portfolio Analysis</h3>
                  <p className="text-gray-600">Portfolio breakdown and allocation insights</p>
                </div>
              </div>
            </TabsContent>

            <TabsContent value="training" className="flex-1 overflow-hidden m-0 p-0">
              <div className="h-full flex items-center justify-center">
                <div className="text-center">
                  <Brain className="w-20 h-20 mx-auto mb-6 text-gray-300" />
                  <h3 className="text-2xl font-bold text-gray-900 mb-2">AI Training Center</h3>
                  <p className="text-gray-600">Model training metrics and performance data</p>
                </div>
              </div>
            </TabsContent>

            <TabsContent value="history" className="flex-1 overflow-hidden m-0 p-0">
              <div className="h-full flex items-center justify-center">
                <div className="text-center">
                  <History className="w-20 h-20 mx-auto mb-6 text-gray-300" />
                  <h3 className="text-2xl font-bold text-gray-900 mb-2">Trade History</h3>
                  <p className="text-gray-600">Complete historical trading record</p>
                </div>
              </div>
            </TabsContent>

          </Tabs>
        </div>

        {/* Enhanced Live Price Ticker - Hidden on mobile */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="hidden md:block flex-shrink-0 bg-white border-t border-gray-100 px-4 md:px-6 py-3"
        >
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4 md:gap-6">
              <span className="text-sm font-medium text-gray-600">Live Prices:</span>
              <div className="flex items-center gap-3 md:gap-4 overflow-x-auto">
                {Object.entries(livePrices).slice(0, 5).map(([symbol, price]) => (
                  <div key={symbol} className="flex items-center gap-2 text-sm whitespace-nowrap">
                    <span className="font-medium text-gray-700">{symbol.replace('USDT', '')}</span>
                    <span className="font-bold text-gray-900">
                      ${typeof price === 'number' ? price.toFixed(2) : '0.00'}
                    </span>
                  </div>
                ))}
              </div>
            </div>

            <div className="flex items-center gap-4">
              <div className="text-xs text-gray-500">
                Mode: <span className="font-medium uppercase">{automationStatus?.trading_mode || 'TESTNET'}</span>
              </div>
              <div className="text-xs text-gray-500">
                Last update: {lastUpdate.toLocaleTimeString()}
              </div>
            </div>
          </div>
        </motion.div>
      </div>
    </div>
  );
}
