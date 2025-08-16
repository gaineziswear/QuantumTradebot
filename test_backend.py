#!/usr/bin/env python3
"""
Simple test to verify backend can start
"""

import sys
import os
from pathlib import Path

# Add the backend directory to Python path
backend_dir = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_dir))

def test_imports():
    """Test if all required modules can be imported"""
    try:
        print("Testing imports...")
        
        # Test basic FastAPI
        from fastapi import FastAPI
        print("✓ FastAPI imported")
        
        # Test pydantic
        from pydantic import BaseModel
        print("✓ Pydantic imported")
        
        # Test configuration
        from config import settings
        print("✓ Configuration imported")
        
        # Test database
        from database import async_session
        print("✓ Database module imported")
        
        print("\nAll imports successful!")
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("Please install required dependencies:")
        print("pip install -r requirements.txt")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def test_app_creation():
    """Test if FastAPI app can be created"""
    try:
        print("\nTesting app creation...")
        from fastapi import FastAPI
        
        app = FastAPI(title="Test App")
        print("✓ FastAPI app created successfully")
        return True
        
    except Exception as e:
        print(f"❌ App creation failed: {e}")
        return False

def main():
    """Run all tests"""
    print("AI Crypto Trading Bot - Backend Test")
    print("=" * 40)
    
    # Test imports
    if not test_imports():
        sys.exit(1)
    
    # Test app creation
    if not test_app_creation():
        sys.exit(1)
    
    print("\n✅ All tests passed! Backend should work correctly.")
    print("\nTo start the backend server, run:")
    print("python start_backend.py")

if __name__ == "__main__":
    main()
