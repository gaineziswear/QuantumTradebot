import asyncio
import sys
import os
import json
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, Any, Optional
import uvicorn
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
from pydantic import BaseModel
import redis.asyncio as redis
from loguru import logger

# Add the backend directory to Python path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

from config import settings
from database import async_session, init_database
from trading_engine import TradingEngine
from ai_model import AITradingModel
from binance_client import BinanceClient
from websocket_manager import WebSocketManager, websocket_manager

class TradingBot:
    """Main trading bot orchestrator"""
    
    def __init__(self):
        self.trading_engine: Optional[TradingEngine] = None
        self.ai_model: Optional[AITradingModel] = None
        self.binance_client: Optional[BinanceClient] = None
        self.redis_client: Optional[redis.Redis] = None
        self.is_initialized = False
        
    async def initialize(self):
        """Initialize all bot components"""
        try:
            logger.info("Initializing AI Crypto Trading Bot...")
            
            # Initialize database
            await init_database()
            
            # Initialize Redis
            self.redis_client = redis.Redis(
                host=settings.REDIS_HOST,
                port=settings.REDIS_PORT,
                db=settings.REDIS_DB,
                decode_responses=True
            )
            
            # Test Redis connection
            try:
                await self.redis_client.ping()
                logger.info("Redis connection established")
            except Exception as e:
                logger.warning(f"Redis connection failed, using memory cache: {e}")
                self.redis_client = None
            
            # Initialize Binance client
            self.binance_client = BinanceClient(
                api_key=settings.BINANCE_API_KEY,
                api_secret=settings.BINANCE_SECRET_KEY,
                testnet=True  # Start with testnet
            )
            
            # Initialize AI model
            self.ai_model = AITradingModel()
            
            # Initialize trading engine
            self.trading_engine = TradingEngine(
                binance_client=self.binance_client,
                ai_model=self.ai_model,
                redis_client=self.redis_client,
                websocket_manager=websocket_manager
            )
            
            self.is_initialized = True
            logger.info("Trading bot initialized successfully")
            
            # Start background data collection
            asyncio.create_task(self._background_data_collection())
            
        except Exception as e:
            logger.error(f"Failed to initialize trading bot: {e}")
            raise
    
    async def _background_data_collection(self):
        """Background task for continuous data collection"""
        while True:
            try:
                if self.trading_engine and not self.trading_engine.is_running:
                    # Collect market data even when not trading
                    await self.trading_engine._real_time_data_stream()
                
                await asyncio.sleep(30)
            except Exception as e:
                logger.error(f"Background data collection error: {e}")
                await asyncio.sleep(60)
    
    async def cleanup(self):
        """Cleanup bot resources"""
        try:
            logger.info("Cleaning up trading bot...")
            
            if self.trading_engine and self.trading_engine.is_running:
                await self.trading_engine.stop()
            
            if self.redis_client:
                await self.redis_client.close()
            
            await websocket_manager.cleanup()
            
            logger.info("Trading bot cleanup completed")
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")

# Global bot instance
bot = TradingBot()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    # Startup
    await bot.initialize()
    yield
    # Shutdown
    await bot.cleanup()

# Create FastAPI app
app = FastAPI(
    title="AI Crypto Trading Bot",
    description="Professional AI-powered cryptocurrency trading bot",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic models
class CapitalRequest(BaseModel):
    amount: float

class TradeRequest(BaseModel):
    symbol: str
    side: str
    quantity: float
    price: Optional[float] = None

# Health check endpoint
@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "bot_initialized": bot.is_initialized,
        "version": "1.0.0"
    }

# Authentication endpoints
@app.post("/api/auth/login")
async def login(credentials: dict):
    """Login endpoint"""
    # For demo purposes, accept any credentials
    return {
        "success": True,
        "message": "Login successful",
        "token": "demo_token_123",
        "user": {
            "id": "demo_user",
            "name": "Trading User"
        }
    }

@app.post("/api/auth/logout")
async def logout():
    """Logout endpoint"""
    return {"success": True, "message": "Logout successful"}

# Trading control endpoints
@app.post("/api/trading/start")
async def start_trading():
    """Start the trading bot"""
    try:
        if not bot.is_initialized:
            raise HTTPException(status_code=503, detail="Bot not initialized")
        
        if bot.trading_engine.is_running:
            return {"success": True, "message": "Trading already running"}
        
        await bot.trading_engine.start()
        
        # Broadcast status update
        await websocket_manager.broadcast_trading_status({
            "is_running": True,
            "message": "Trading started successfully"
        })
        
        return {"success": True, "message": "Trading started successfully"}
    
    except Exception as e:
        logger.error(f"Failed to start trading: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/trading/stop")
async def stop_trading():
    """Stop the trading bot"""
    try:
        if not bot.is_initialized:
            raise HTTPException(status_code=503, detail="Bot not initialized")
        
        if not bot.trading_engine.is_running:
            return {"success": True, "message": "Trading already stopped"}
        
        await bot.trading_engine.stop()
        
        # Broadcast status update
        await websocket_manager.broadcast_trading_status({
            "is_running": False,
            "message": "Trading stopped successfully"
        })
        
        return {"success": True, "message": "Trading stopped successfully"}
    
    except Exception as e:
        logger.error(f"Failed to stop trading: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/trading/go-live")
async def go_live():
    """Switch to live trading mode"""
    try:
        if not bot.is_initialized:
            raise HTTPException(status_code=503, detail="Bot not initialized")
        
        await bot.trading_engine.switch_to_live()
        
        # Broadcast status update
        await websocket_manager.broadcast_trading_status({
            "is_live_trading": True,
            "message": "Switched to live trading mode"
        })
        
        return {"success": True, "message": "Switched to live trading mode"}
    
    except Exception as e:
        logger.error(f"Failed to switch to live trading: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/trading/add-capital")
async def add_capital(request: CapitalRequest):
    """Add or remove capital"""
    try:
        if not bot.is_initialized:
            raise HTTPException(status_code=503, detail="Bot not initialized")
        
        new_capital = await bot.trading_engine.add_capital(request.amount)
        
        # Broadcast capital update
        await websocket_manager.broadcast_trading_status({
            "current_capital": new_capital,
            "message": f"Capital {'added' if request.amount > 0 else 'removed'}: {abs(request.amount)}"
        })
        
        return {
            "success": True,
            "message": f"Capital {'added' if request.amount > 0 else 'removed'} successfully",
            "new_capital": new_capital
        }
    
    except Exception as e:
        logger.error(f"Failed to modify capital: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Data retrieval endpoints
@app.get("/api/trading/status")
async def get_trading_status():
    """Get current trading status"""
    try:
        if not bot.is_initialized:
            return {
                "is_running": False,
                "is_live_trading": False,
                "current_capital": 0,
                "active_positions": 0,
                "total_trades": 0,
                "win_rate": 0
            }
        
        status = await bot.trading_engine.get_status()
        return status
    
    except Exception as e:
        logger.error(f"Failed to get trading status: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/trading/performance")
async def get_performance():
    """Get performance metrics"""
    try:
        if not bot.is_initialized:
            return {
                "total_pnl": 0,
                "win_rate": 0,
                "sharpe_ratio": 0,
                "max_drawdown": 0,
                "total_trades": 0,
                "var": 0
            }
        
        performance = await bot.trading_engine.get_performance_metrics()
        return performance
    
    except Exception as e:
        logger.error(f"Failed to get performance metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/trading/trades")
async def get_recent_trades(limit: int = 10):
    """Get recent trades"""
    try:
        if not bot.is_initialized:
            return []
        
        trades = await bot.trading_engine.get_recent_trades(limit)
        return trades
    
    except Exception as e:
        logger.error(f"Failed to get recent trades: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/trading/portfolio")
async def get_portfolio():
    """Get portfolio allocation"""
    try:
        if not bot.is_initialized:
            return {"total_value_usdt": 0, "portfolio": []}
        
        portfolio = await bot.trading_engine.get_portfolio_allocation()
        return portfolio
    
    except Exception as e:
        logger.error(f"Failed to get portfolio: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# AI model endpoints
@app.get("/api/ai/status")
async def get_ai_status():
    """Get AI model status"""
    try:
        if not bot.is_initialized or not bot.ai_model:
            return {
                "is_training": False,
                "progress_percentage": 0,
                "model_confidence": "Unknown",
                "last_training": None
            }
        
        status = await bot.ai_model.get_training_status()
        return status
    
    except Exception as e:
        logger.error(f"Failed to get AI status: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/ai/train")
async def start_ai_training(background_tasks: BackgroundTasks):
    """Start AI model training"""
    try:
        if not bot.is_initialized:
            raise HTTPException(status_code=503, detail="Bot not initialized")
        
        if bot.ai_model.is_training:
            return {"success": False, "message": "Training already in progress"}
        
        # Start training in background
        background_tasks.add_task(bot.trading_engine._start_model_training)
        
        return {"success": True, "message": "AI training started"}
    
    except Exception as e:
        logger.error(f"Failed to start AI training: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/data/download")
async def start_data_download(background_tasks: BackgroundTasks):
    """Start historical data download"""
    try:
        if not bot.is_initialized:
            raise HTTPException(status_code=503, detail="Bot not initialized")
        
        # Start data download in background
        task_id = await bot.trading_engine.start_data_download()
        
        return {
            "success": True,
            "message": "Historical data download started",
            "task_id": task_id
        }
    
    except Exception as e:
        logger.error(f"Failed to start data download: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Market data endpoints
@app.get("/api/market/prices")
async def get_market_prices():
    """Get current market prices"""
    try:
        if not bot.is_initialized:
            return []
        
        prices = await bot.binance_client.get_ticker_prices(settings.TOP_CRYPTOCURRENCIES)
        return prices
    
    except Exception as e:
        logger.error(f"Failed to get market prices: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# WebSocket endpoint
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time updates"""
    await websocket.accept()
    
    try:
        await websocket_manager.register(websocket)
        
        # Send initial data
        if bot.is_initialized:
            status = await bot.trading_engine.get_status()
            await websocket_manager.send_to_connection(websocket, {
                'type': 'initial_data',
                'data': {
                    'trading_status': status,
                    'timestamp': datetime.now(timezone.utc).isoformat()
                }
            })
        
        # Keep connection alive
        while True:
            try:
                data = await websocket.receive_text()
                message = json.loads(data)
                
                # Handle ping/pong
                if message.get('type') == 'ping':
                    await websocket_manager.send_to_connection(websocket, {
                        'type': 'pong',
                        'timestamp': datetime.now(timezone.utc).isoformat()
                    })
                
            except WebSocketDisconnect:
                break
            except Exception as e:
                logger.error(f"WebSocket message error: {e}")
                break
    
    except Exception as e:
        logger.error(f"WebSocket connection error: {e}")
    finally:
        await websocket_manager.unregister(websocket)

# Statistics endpoint
@app.get("/api/stats")
async def get_system_stats():
    """Get system statistics"""
    try:
        stats = {
            "bot_initialized": bot.is_initialized,
            "trading_active": bot.trading_engine.is_running if bot.is_initialized else False,
            "websocket_stats": websocket_manager.get_stats(),
            "uptime": datetime.now(timezone.utc).isoformat(),
            "version": "1.0.0"
        }
        
        if bot.is_initialized:
            status = await bot.trading_engine.get_status()
            stats.update(status)
        
        return stats
    
    except Exception as e:
        logger.error(f"Failed to get system stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    # Configure logging
    logger.add(
        "logs/trading_bot_{time}.log",
        rotation="1 day",
        retention="30 days",
        level="INFO"
    )
    
    # Run the server
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=False,
        log_level="info"
    )
