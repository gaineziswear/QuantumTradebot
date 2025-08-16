#!/usr/bin/env python3
"""
AI Crypto Trading Bot - Integrated Startup Script

This script starts both the backend API and serves the frontend dashboard
in a single integrated application for production use.

Prerequisites:
1. Run: python setup_database.py
2. Configure .env file
3. Build frontend: npm run build

Usage:
    python start_bot.py

The integrated app will start on http://localhost:8000
- Frontend dashboard: http://localhost:8000
- API endpoints: http://localhost:8000/api/*
- WebSocket: ws://localhost:8000/ws
- API docs: http://localhost:8000/docs
"""

import os
import sys
import asyncio
import uvicorn
from pathlib import Path
from fastapi.staticfiles import StaticFiles

# Add backend directory to Python path
backend_dir = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_dir))

# Import the FastAPI app
from main import app

def setup_static_files():
    """Mount static files for frontend"""
    frontend_dist = Path(__file__).parent / "dist"
    
    if frontend_dist.exists():
        # Mount built frontend
        app.mount("/assets", StaticFiles(directory=frontend_dist / "assets"), name="assets")
        app.mount("/", StaticFiles(directory=frontend_dist, html=True), name="frontend")
        print("✅ Frontend assets mounted successfully")
    else:
        print("⚠️  Frontend not built. Run 'npm run build' first")
        print("   Starting backend-only mode...")

def print_startup_info():
    """Print startup information"""
    print("\n" + "=" * 60)
    print("🤖 AI Crypto Trading Bot - Production Mode")
    print("=" * 60)
    print(f"🌐 Dashboard: http://localhost:8000")
    print(f"📚 API Docs: http://localhost:8000/docs")
    print(f"🔌 WebSocket: ws://localhost:8000/ws")
    print(f"🔐 Login: Use credentials from .env file")
    print("=" * 60)
    print("🎯 Features Available:")
    print("   ✅ AI-Powered Trading Engine")
    print("   ✅ Real-time Dashboard")
    print("   ✅ WebSocket Live Updates")
    print("   ✅ Secure Authentication")
    print("   ✅ Risk Management")
    print("   ✅ Portfolio Analytics")
    print("=" * 60)
    print("📱 Mobile Access: Use Cloudflare Tunnel for remote access")
    print("🔧 Troubleshooting: Check SETUP_GUIDE.md")
    print("=" * 60 + "\n")

async def main():
    """Main startup function"""
    print("🚀 Starting AI Crypto Trading Bot...")
    
    # Check environment
    if not os.path.exists('.env'):
        print("⚠️  .env file not found!")
        print("   Please copy .env.example to .env and configure settings")
        print("   Run: cp .env.example .env")
        return
    
    # Setup static files
    setup_static_files()
    
    # Print startup info
    print_startup_info()
    
    # Configure and start server
    config = uvicorn.Config(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=False,  # Disable reload in production
        log_level="info",
        access_log=True,
        use_colors=True
    )
    
    server = uvicorn.Server(config)
    
    try:
        await server.serve()
    except KeyboardInterrupt:
        print("\n👋 Shutting down AI Crypto Trading Bot...")

if __name__ == "__main__":
    try:
        # Change to backend directory for imports
        os.chdir(Path(__file__).parent / "backend")
        asyncio.run(main())
    except Exception as e:
        print(f"❌ Failed to start: {e}")
        print("\n🔧 Troubleshooting:")
        print("1. Run: python setup_database.py")
        print("2. Check PostgreSQL and Redis are running")
        print("3. Verify .env configuration")
        print("4. Check SETUP_GUIDE.md for detailed instructions")
        sys.exit(1)
