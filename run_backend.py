#!/usr/bin/env python3
"""
AI Crypto Trading Bot Backend Startup Script

This script starts the FastAPI backend server for the AI crypto trading bot.

Prerequisites:
1. Python 3.9+ installed
2. PostgreSQL running locally
3. Redis running locally  
4. Install dependencies: pip install -r requirements.txt
5. Copy .env.example to .env and configure your settings

Usage:
    python run_backend.py

The backend will start on http://localhost:8000
Dashboard API will be available at http://localhost:8000/docs
"""

import os
import sys
import asyncio
import uvicorn
from pathlib import Path

# Add backend directory to Python path
backend_dir = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_dir))

def check_dependencies():
    """Check if required dependencies are installed"""
    required_packages = [
        'fastapi', 'uvicorn', 'sqlalchemy', 'asyncpg', 'redis',
        'torch', 'pandas', 'numpy', 'binance', 'loguru'
    ]
    
    missing_packages = []
    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        print(f"❌ Missing required packages: {', '.join(missing_packages)}")
        print("Please install them with: pip install -r requirements.txt")
        return False
    
    print("✅ All required packages are installed")
    return True

def check_environment():
    """Check if environment is properly configured"""
    if not os.path.exists('.env'):
        print("❌ .env file not found")
        print("Please copy .env.example to .env and configure your settings")
        return False
    
    print("✅ Environment file found")
    return True

def check_services():
    """Check if required services are running"""
    # Note: In a real implementation, you'd check PostgreSQL and Redis connectivity
    print("⚠️  Please ensure PostgreSQL and Redis are running locally")
    print("   PostgreSQL: Default port 5432")
    print("   Redis: Default port 6379")
    return True

async def main():
    """Main startup function"""
    print("🚀 Starting AI Crypto Trading Bot Backend")
    print("=" * 50)
    
    # Check prerequisites
    if not check_dependencies():
        sys.exit(1)
    
    if not check_environment():
        sys.exit(1)
    
    if not check_services():
        print("⚠️  Warning: Some services may not be available")
    
    print("\n🎯 Starting FastAPI server...")
    print("📊 Dashboard will be available at: http://localhost:8000")
    print("📚 API Documentation: http://localhost:8000/docs")
    print("🔗 WebSocket endpoint: ws://localhost:8000/ws")
    print("\n" + "=" * 50)
    
    # Start the server
    config = uvicorn.Config(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info",
        access_log=True
    )
    
    server = uvicorn.Server(config)
    await server.serve()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Shutting down AI Crypto Trading Bot Backend")
    except Exception as e:
        print(f"❌ Failed to start backend: {e}")
        sys.exit(1)
