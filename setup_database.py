#!/usr/bin/env python3
"""
Database Setup Script for AI Crypto Trading Bot

This script sets up PostgreSQL and Redis for the trading bot.

Prerequisites:
1. PostgreSQL installed and running
2. Redis installed and running
3. Python dependencies installed: pip install -r requirements.txt

Usage:
    python setup_database.py
"""

import os
import sys
import asyncio
import asyncpg
import redis
from pathlib import Path

# Add backend to path
backend_dir = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_dir))

from config import settings

async def setup_database():
    """Set up database (PostgreSQL or SQLite)"""
    db_url = settings.DATABASE_URL

    if db_url.startswith('postgresql://'):
        print("🗄️  Setting up PostgreSQL database...")
        return await setup_postgresql()
    elif db_url.startswith('sqlite'):
        print("🗄️  Setting up SQLite database...")
        return await setup_sqlite()
    else:
        print(f"❌ Unsupported database URL format: {db_url}")
        return False

async def setup_postgresql():
    """Set up PostgreSQL database"""
    try:
        # Parse database URL to get connection details
        db_url = settings.DATABASE_URL
        import urllib.parse
        parsed = urllib.parse.urlparse(db_url)

        # Connect to postgres database first to create our database
        try:
            conn = await asyncpg.connect(
                host=parsed.hostname or 'localhost',
                port=parsed.port or 5432,
                user=parsed.username or 'postgres',
                password=parsed.password or 'password',
                database='postgres'
            )

            # Create database if it doesn't exist
            db_name = parsed.path.lstrip('/')
            await conn.execute(f'CREATE DATABASE "{db_name}"')
            print(f"✅ Created database: {db_name}")

        except asyncpg.DuplicateDatabaseError:
            print(f"✅ Database already exists: {db_name}")
        except Exception as e:
            print(f"ℹ️  Database may already exist or error: {e}")
        finally:
            if 'conn' in locals():
                await conn.close()

        # Now connect to our database and create tables
        from database import init_database
        await init_database()
        print("✅ Database tables created successfully")
        return True

    except Exception as e:
        print(f"❌ Failed to setup PostgreSQL: {e}")
        print("Please ensure PostgreSQL is running and accessible")
        return False

async def setup_sqlite():
    """Set up SQLite database"""
    try:
        print("✅ SQLite database will be created automatically")

        # Initialize database tables
        from database import init_database
        await init_database()
        print("✅ Database tables created successfully")
        return True

    except Exception as e:
        print(f"❌ Failed to setup SQLite: {e}")
        return False
            
    except Exception as e:
        print(f"❌ Failed to setup PostgreSQL: {e}")
        print("Please ensure PostgreSQL is running and accessible")
        return False
    
    return True

def setup_redis():
    """Set up Redis connection"""
    print("🔴 Setting up Redis connection...")

    try:
        # Use individual Redis settings instead of URL
        r = redis.Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            db=settings.REDIS_DB,
            decode_responses=True
        )
        r.ping()
        print("✅ Redis connection successful")

        # Set some initial values
        r.set("bot:status", "initialized")
        r.set("bot:setup_time", str(asyncio.get_event_loop().time()))

        return True
    except Exception as e:
        print(f"❌ Failed to connect to Redis: {e}")
        print("Redis is optional - the bot will work without it (reduced real-time features)")
        return True  # Return True since Redis is optional

def check_environment():
    """Check environment configuration"""
    print("🔧 Checking environment configuration...")
    
    if not os.path.exists('.env'):
        print("⚠️  .env file not found, using default settings")
        print("   Consider copying .env.example to .env for custom configuration")
    else:
        print("✅ Environment file found")
    
    # Check critical settings
    if not settings.SECRET_KEY or settings.SECRET_KEY == "your-secret-key-change-this-in-production":
        print("⚠️  Warning: Using default SECRET_KEY - change this in production!")
    
    if not settings.BINANCE_API_KEY:
        print("⚠️  Binance API key not configured - using public data only")
    
    return True

async def main():
    """Main setup function"""
    print("🚀 Setting up AI Crypto Trading Bot Database")
    print("=" * 50)
    
    # Check environment
    if not check_environment():
        sys.exit(1)
    
    # Setup Database
    if not await setup_database():
        print("\n❌ Database setup failed")
        print("Please check the error messages above for details")
        sys.exit(1)
    
    # Setup Redis
    if not setup_redis():
        print("\n❌ Redis setup failed")
        print("Please ensure Redis is installed and running:")
        print("   - Install: https://redis.io/download")
        print("   - Start: redis-server")
        sys.exit(1)
    
    print("\n✅ Database setup completed successfully!")
    print("=" * 50)
    print("Next steps:")
    print("1. Configure your Binance API keys in .env (optional)")
    print("2. Run: python run_backend.py")
    print("3. Access dashboard at: http://localhost:8000")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Setup interrupted")
    except Exception as e:
        print(f"\n❌ Setup failed: {e}")
        sys.exit(1)
