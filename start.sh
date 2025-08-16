#!/bin/bash

# AI Crypto Trading Bot - Ultimate One-Command Setup
# Make this file executable: chmod +x start.sh
# Then run: ./start.sh

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Function to log with timestamp and color
log() {
    local color=$1
    local message=$2
    echo -e "[$(date '+%H:%M:%S')] ${color}${message}${NC}"
}

# Clear screen and show banner
clear
echo ""
echo -e "${CYAN}████████╗██████╗  █████╗ ██████╗ ██╗███╗   ██╗ ██████╗     ██████╗  ██████╗ ████████╗${NC}"
echo -e "${CYAN}╚══██╔══╝██╔══██╗██╔══██╗██╔══██╗██║████╗  ██║██╔════╝     ██╔══██╗██╔═══██╗╚══██╔══╝${NC}"
echo -e "${CYAN}   ██║   ██████╔╝███████║██║  ██║██║██╔██╗ ██║██║  ███╗    ██████╔╝██║   ██║   ██║   ${NC}"
echo -e "${CYAN}   ██║   ██╔══██╗██╔══██║██║  ██║██║██║╚██╗██║██║   ██��    ██╔══██╗██║   ██║   ██║   ${NC}"
echo -e "${CYAN}   ██║   ██║  ██║██║  ██║██████╔╝██║██║ ╚████║╚██████╔╝    ██████╔╝╚██████╔╝   ██║   ${NC}"
echo -e "${CYAN}   ╚═╝   ╚═╝  ╚═╝╚═╝  ╚═╝╚═════╝ ╚═╝╚═╝  ╚═══╝ ╚═════╝     ╚═════╝  ╚═════╝    ╚═╝   ${NC}"
echo ""
echo -e "    ${GREEN}🤖 AI-POWERED CRYPTOCURRENCY TRADING BOT${NC}"
echo -e "    ${YELLOW}⚡ Ultimate One-Command Setup and Launch${NC}"
echo -e "    ${BLUE}🌐 Automatic Global Internet Access${NC}"
echo ""
echo -e "    ${YELLOW}💡 Running this script? Perfect! Everything will be set up automatically.${NC}"
echo ""

log $CYAN "🚀 Starting ultimate setup..."
echo ""

# Check Node.js
if ! command -v node &> /dev/null; then
    log $RED "❌ Node.js not found! Please install from https://nodejs.org/"
    echo ""
    exit 1
fi
log $GREEN "✅ Node.js found"

# Check Python (try python3 first, then python)
PYTHON_CMD=""
if command -v python3 &> /dev/null; then
    PYTHON_CMD="python3"
elif command -v python &> /dev/null; then
    PYTHON_CMD="python"
else
    log $RED "❌ Python not found! Please install from https://python.org/downloads/"
    echo ""
    exit 1
fi
log $GREEN "✅ Python found: $PYTHON_CMD"

# Check pip
PIP_CMD=""
if command -v pip3 &> /dev/null; then
    PIP_CMD="pip3"
elif command -v pip &> /dev/null; then
    PIP_CMD="pip"
else
    log $RED "❌ pip not found! Please install pip"
    echo ""
    exit 1
fi
log $GREEN "✅ pip found: $PIP_CMD"

log $BLUE "🔧 Running ultimate setup script..."
echo ""

# Run the ultimate setup script
if [ -f "setup-and-run.js" ]; then
    node setup-and-run.js
else
    log $YELLOW "⚠️ Setup script not found, running manual setup..."
    echo ""
    
    log $BLUE "📦 Installing dependencies..."
    
    # Install Node.js dependencies
    if command -v pnpm &> /dev/null; then
        pnpm install
    else
        npm install
    fi
    
    # Install Python dependencies
    log $BLUE "🐍 Installing Python packages..."
    if [ -f "requirements.txt" ]; then
        $PIP_CMD install -r requirements.txt
    fi
    
    # Setup database
    log $BLUE "🗄️ Setting up database..."
    if [ -f "setup_database.py" ]; then
        $PYTHON_CMD setup_database.py
    fi
    
    # Start the bot
    log $CYAN "��� Starting bot..."
    if [ -f "scripts/start-with-ngrok.js" ]; then
        node scripts/start-with-ngrok.js
    elif [ -f "dev_start.py" ]; then
        $PYTHON_CMD dev_start.py
    else
        log $YELLOW "🌐 Please start the bot manually with: $PYTHON_CMD dev_start.py"
    fi
fi

echo ""
log $GREEN "🎉 Setup complete!"
