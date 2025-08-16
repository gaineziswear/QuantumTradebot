#!/usr/bin/env python3
"""
Startup script for the AI Crypto Trading Bot backend server
"""

import sys
import os
import asyncio
import uvicorn
from pathlib import Path

# Add the backend directory to Python path
backend_dir = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_dir))

def main():
    """Main entry point"""
    print("Starting AI Crypto Trading Bot Backend Server...")
    
    # Change to backend directory
    os.chdir(backend_dir)
    
    try:
        # Run the server
        uvicorn.run(
            "main:app",
            host="0.0.0.0",
            port=8000,
            reload=True,
            log_level="info",
            access_log=True
        )
    except KeyboardInterrupt:
        print("\nShutting down gracefully...")
    except Exception as e:
        print(f"Error starting server: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
