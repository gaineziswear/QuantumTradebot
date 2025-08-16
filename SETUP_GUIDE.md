# AI Crypto Trading Bot - Complete Setup Guide

A production-ready, AI-powered cryptocurrency trading bot with secure remote access via Cloudflare Tunnel.

## 🎯 What You Get

- **AI-Powered Trading**: Deep reinforcement learning with ensemble models
- **Professional Dashboard**: Non-scrollable, real-time animated interface  
- **Secure Remote Access**: Access from anywhere via Cloudflare Tunnel
- **Risk Management**: Advanced portfolio allocation and risk controls
- **Real-time Updates**: WebSocket-powered live data synchronization
- **Mobile Friendly**: Optimized for phone browsers

## 📋 Prerequisites

### Required Software
1. **Python 3.9+** - [Download](https://python.org/downloads/)
2. **Node.js 18+** - [Download](https://nodejs.org/)
3. **PostgreSQL** - [Download](https://postgresql.org/download/)
4. **Redis** - [Download](https://redis.io/download)
5. **Git** - [Download](https://git-scm.com/)

### Optional (Recommended)
- **Cloudflared** - [Install Guide](https://developers.cloudflare.com/cloudflare-one/connections/connect-apps/install-and-setup/)
- **Binance Account** - [Sign Up](https://binance.com/) (for live trading)

## 🚀 Quick Start

### 1. Clone and Setup Environment

```bash
# Clone the repository (if from git)
git clone <repository-url>
cd ai-crypto-trading-bot

# Create Python virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# Install Python dependencies
pip install -r requirements.txt

# Install Node.js dependencies
npm install
```

### 2. Configure Environment

```bash
# Copy environment template
cp .env.example .env

# Edit .env file with your settings
nano .env  # or use any text editor
```

**Key Configuration Options:**
```env
# Database (use default for local setup)
DATABASE_URL=postgresql://postgres:password@localhost:5432/crypto_bot
REDIS_URL=redis://localhost:6379

# Binance API (optional - leave empty for demo mode)
BINANCE_API_KEY=your_api_key_here
BINANCE_API_SECRET=your_secret_here
USE_TESTNET=true

# Authentication (CHANGE THESE!)
SECRET_KEY=your-super-secret-jwt-key
BOT_USERNAME=admin
BOT_PASSWORD=your-secure-password

# Trading Settings
DEFAULT_CAPITAL=10000.0
MAX_POSITION_SIZE=0.1
STOP_LOSS_PERCENTAGE=0.02
TAKE_PROFIT_PERCENTAGE=0.04
```

### 3. Setup Databases

**Start Required Services:**
```bash
# Start PostgreSQL (varies by OS)
# Windows: net start postgresql
# macOS: brew services start postgresql
# Linux: sudo systemctl start postgresql

# Start Redis
redis-server

# Setup database tables
python setup_database.py
```

### 4. Start the Application

**Option A: Development Mode (Two Terminals)**

Terminal 1 - Backend:
```bash
python run_backend.py
```

Terminal 2 - Frontend:
```bash
npm run dev
```

**Option B: Production Mode (Single Command)**
```bash
# Build frontend
npm run build

# Start integrated server
python run_backend.py
```

### 5. Access Dashboard

- **Local Access**: http://localhost:8000
- **Login**: Use credentials from your .env file
- **API Docs**: http://localhost:8000/docs

## 🌐 Cloudflare Tunnel Setup (Remote Access)

### 1. Install Cloudflared

```bash
# Download from: https://developers.cloudflare.com/cloudflare-one/connections/connect-apps/install-and-setup/

# Verify installation
cloudflared --version
```

### 2. Configure Tunnel

```bash
# Login to Cloudflare
cloudflared tunnel login

# Create tunnel
cloudflared tunnel create crypto-trading-bot

# Note the tunnel UUID from output
```

### 3. Update Configuration

Edit `cloudflare-tunnel.yml`:
```yaml
tunnel: YOUR_TUNNEL_UUID  # Replace with actual UUID
credentials-file: /path/to/YOUR_TUNNEL_UUID.json

ingress:
  - hostname: your-bot.yourdomain.com  # Your custom domain
    service: http://localhost:8000
  - service: http_status:404
```

### 4. Start Tunnel

```bash
# Start tunnel
cloudflared tunnel --config cloudflare-tunnel.yml run

# Or run as background service
cloudflared service install
```

Now access your bot securely from anywhere: `https://your-bot.yourdomain.com`

## 🤖 AI Model Configuration

### Training Data Sources
- **Binance Spot API**: Historical OHLCV data for top 10 cryptocurrencies
- **Technical Indicators**: RSI, MACD, Bollinger Bands, Moving Averages
- **Market Features**: Volume, volatility, price patterns

### AI Architecture
- **LSTM Networks**: Time series prediction with attention mechanism
- **Ensemble Methods**: Random Forest + Gradient Boosting
- **Risk Models**: Dynamic position sizing with Kelly Criterion
- **Online Learning**: Continuous model updates with new data

### Performance Optimization
- **GPU Support**: Automatic CUDA detection for PyTorch
- **Batch Processing**: Efficient data handling
- **Model Caching**: Fast inference with saved models
- **Real-time Inference**: <500ms decision latency

## 📊 Trading Features

### Risk Management
- **Position Sizing**: Kelly Criterion-based allocation
- **Stop Loss**: Configurable percentage-based stops
- **Take Profit**: Automated profit taking
- **Drawdown Control**: Maximum loss protection
- **Volatility Targeting**: Dynamic risk adjustment

### Portfolio Management
- **Dynamic Allocation**: AI-driven portfolio rebalancing
- **Capital Management**: Add/remove funds anytime
- **Multi-Asset**: Trade multiple cryptocurrencies
- **Hidden Gems**: Discover new opportunities beyond top 10

### Execution
- **Testnet First**: Safe testing before live trading
- **Real Orders**: No simulated trades (when live)
- **Low Latency**: Optimized execution speed
- **Error Handling**: Robust failure recovery

## 🔒 Security Features

### Authentication
- **JWT Tokens**: Secure session management
- **Password Protection**: Required for all access
- **Session Expiry**: Automatic logout

### API Security
- **Environment Variables**: Secrets stored in .env
- **HTTPS Only**: Encrypted communication via Cloudflare
- **No Key Exposure**: API keys never sent to frontend
- **Rate Limiting**: Protection against abuse

### Network Security
- **Cloudflare Tunnel**: No open ports required
- **DDoS Protection**: Built-in Cloudflare security
- **SSL/TLS**: End-to-end encryption

## 📱 Mobile Access

The dashboard is fully optimized for mobile devices:
- **Responsive Design**: Adapts to any screen size
- **Touch Friendly**: Large buttons and touch targets
- **Fast Loading**: Optimized for mobile networks
- **Real-time**: Same features as desktop

## 🔧 Troubleshooting

### Common Issues

**Database Connection Failed:**
```bash
# Check PostgreSQL status
sudo systemctl status postgresql  # Linux
brew services list | grep postgres  # macOS

# Reset database
dropdb crypto_bot
python setup_database.py
```

**Redis Connection Failed:**
```bash
# Check Redis status
redis-cli ping

# Restart Redis
sudo systemctl restart redis  # Linux
brew services restart redis  # macOS
```

**Binance API Errors:**
- Verify API keys in .env file
- Check API key permissions on Binance
- Ensure IP whitelist includes your server
- Confirm testnet vs live mode settings

**Frontend Not Loading:**
```bash
# Clear build cache
rm -rf dist/ .vite/

# Rebuild
npm run build
```

### Log Files
- **Backend Logs**: Check terminal output where `run_backend.py` is running
- **Database Logs**: PostgreSQL logs location varies by OS
- **Cloudflare Logs**: `/var/log/cloudflared.log`

## 📈 Performance Monitoring

### Key Metrics to Watch
- **Total P&L**: Overall profitability
- **Sharpe Ratio**: Risk-adjusted returns
- **Win Rate**: Percentage of profitable trades
- **Max Drawdown**: Largest loss from peak
- **Model Confidence**: AI prediction quality

### Optimization Tips
1. **Increase Training Data**: More history = better predictions
2. **Tune Risk Parameters**: Adjust stop loss/take profit levels
3. **Monitor Model Performance**: Retrain when accuracy drops
4. **Review Portfolio Allocation**: Rebalance based on performance

## 🚦 Going Live

### Pre-Live Checklist
- [ ] Tested extensively on testnet
- [ ] Comfortable with performance metrics
- [ ] Backup strategy in place
- [ ] Emergency stop procedures tested
- [ ] API keys configured for live trading

### Live Trading Steps
1. **Update .env**: Set `USE_TESTNET=false`
2. **Add Live API Keys**: Get from Binance Pro account
3. **Start Small**: Begin with minimal capital
4. **Monitor Closely**: Watch first few trades carefully
5. **Scale Gradually**: Increase capital as confidence grows

## 🆘 Support

### Getting Help
1. **Check Logs**: Most issues show in terminal output
2. **Review Configuration**: Verify .env settings
3. **Database Status**: Ensure PostgreSQL/Redis running
4. **Network Issues**: Check firewall/internet connection

### Best Practices
- **Regular Backups**: Export database regularly
- **Monitor Performance**: Check dashboard daily
- **Update Software**: Keep dependencies current
- **Security Reviews**: Rotate passwords/keys periodically

## 📚 Additional Resources

- **Binance API Documentation**: https://binance-docs.github.io/apidocs/
- **Cloudflare Tunnel Guide**: https://developers.cloudflare.com/cloudflare-one/
- **PostgreSQL Documentation**: https://postgresql.org/docs/
- **Redis Documentation**: https://redis.io/documentation

---

## 🎉 Congratulations!

You now have a professional, AI-powered cryptocurrency trading bot with:
- ✅ Secure remote access from anywhere
- ✅ Real-time trading with advanced AI
- ✅ Professional dashboard interface
- ✅ Comprehensive risk management
- ✅ Mobile-friendly design
- ✅ Production-ready security

**Start trading smart with AI! 🚀**
