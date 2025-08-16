#!/usr/bin/env python3
"""
AI Crypto Trading Bot - Development Startup Script

This script starts the backend in development mode with hot reload.
Run the frontend separately with: npm run dev

Usage:
    python dev_start.py

Backend will start on http://localhost:8000
Frontend should run on http://localhost:5173 (Vite default)
"""

import os
import sys
import asyncio
import uvicorn
from pathlib import Path

# Add backend directory to Python path  
backend_dir = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_dir))

async def main():
    """Main development startup function"""
    print("🚀 Starting AI Crypto Trading Bot Backend (Development Mode)")
    print("=" * 60)
    print("🔧 Development Mode Features:")
    print("   ✅ Hot Reload Enabled")
    print("   ✅ Detailed Logging")
    print("   ✅ CORS Enabled for Frontend")
    print("=" * 60)
    print("🌐 Backend API: http://localhost:8000")
    print("📚 API Docs: http://localhost:8000/docs")
    print("🔌 WebSocket: ws://localhost:8000/ws")
    print("=" * 60)
    print("💡 To start frontend:")
    print("   Run in another terminal: npm run dev")
    print("   Frontend URL: http://localhost:5173")
    print("=" * 60 + "\n")
    
    # Check environment
    if not os.path.exists('.env'):
        print("⚠️  .env file not found, using defaults")
    
    # Configure and start server
    config = uvicorn.Config(
        "main:app",
        host="0.0.0.0", 
        port=8000,
        reload=True,  # Enable hot reload
        log_level="debug",
        access_log=True,
        use_colors=True,
        reload_dirs=[str(backend_dir)]
    )
    
    server = uvicorn.Server(config)
    
    try:
        await server.serve()
    except KeyboardInterrupt:
        print("\n👋 Development server stopped")

if __name__ == "__main__":
    try:
        # Change to backend directory
        os.chdir(Path(__file__).parent / "backend")
        asyncio.run(main())
    except Exception as e:
        print(f"❌ Failed to start development server: {e}")
        sys.exit(1)
