@echo off
title AI Crypto Trading Bot - One Command Setup
color 0A

echo.
echo ████████╗██████╗  █████╗ ██████╗ ██╗███╗   ██╗ ██████╗     ██████╗  ██████╗ ████████╗
echo ╚══██╔══╝██╔══██╗██╔══██╗██╔══██╗██║████╗  ██║██╔════╝     ██╔══██╗██╔═══██╗╚══██╔══╝
echo    ██║   ██████╔╝███████║██║  ██║██║██╔██╗ ██║██║  ███╗    ██████╔╝██║   ██║   ██║   
echo    ██║   ██╔══██╗██╔══██║██║  ██║██║██║╚██╗██║██║   ██║    ██╔══██╗██║   ██║   ██║   
echo    ██║   ██║  ██║██║  ██║██████╔╝██║██║ ╚████║╚██████╔╝    ██████╔╝╚██████╔╝   ██║   
echo    ╚═╝   ╚═╝  ╚═╝╚═╝  ╚═╝╚═════╝ ╚═╝╚═╝  ╚═══╝ ╚═════╝     ╚═════╝  ╚═════╝    ╚═╝   
echo.
echo    🤖 AI-POWERED CRYPTOCURRENCY TRADING BOT
echo    ⚡ Ultimate One-Command Setup and Launch
echo    🌐 Automatic Global Internet Access
echo.
echo    💡 Double-clicked this file? Perfect! Everything will be set up automatically.
echo.

echo [%TIME%] 🚀 Starting ultimate setup...
echo.

REM Check if Node.js is installed
node --version >nul 2>&1
if errorlevel 1 (
    echo [%TIME%] ❌ Node.js not found! Please install from https://nodejs.org/
    echo.
    pause
    exit /b 1
)
echo [%TIME%] ✅ Node.js found

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    python3 --version >nul 2>&1
    if errorlevel 1 (
        echo [%TIME%] ❌ Python not found! Please install from https://python.org/downloads/
        echo.
        pause
        exit /b 1
    )
)
echo [%TIME%] ✅ Python found

echo [%TIME%] 🔧 Running ultimate setup script...
echo.

REM Run the ultimate setup script
node setup-and-run.js

REM If setup script doesn't exist, fall back to manual commands
if errorlevel 1 (
    echo.
    echo [%TIME%] ⚠️ Setup script failed, trying manual setup...
    echo.
    
    echo [%TIME%] 📦 Installing dependencies...
    call npm install
    
    echo [%TIME%] 🐍 Installing Python packages...
    pip install -r requirements.txt
    
    echo [%TIME%] 🗄️ Setting up database...
    python setup_database.py
    
    echo [%TIME%] 🚀 Starting bot...
    python dev_start.py
)

echo.
echo [%TIME%] 🎉 Setup complete!
pause
