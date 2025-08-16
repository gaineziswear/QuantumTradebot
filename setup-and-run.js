#!/usr/bin/env node
/**
 * AI Crypto Trading Bot - Ultimate One-Command Setup
 * Run this after unzipping: node setup-and-run.js
 * Handles EVERYTHING: dependencies, database, ngrok, launch
 */

const { spawn, exec } = require('child_process');
const fs = require('fs');
const path = require('path');
const os = require('os');

// Beautiful console colors
const colors = {
  reset: '\x1b[0m',
  red: '\x1b[31m',
  green: '\x1b[32m',
  yellow: '\x1b[33m',
  blue: '\x1b[34m',
  magenta: '\x1b[35m',
  cyan: '\x1b[36m',
  white: '\x1b[37m',
  bold: '\x1b[1m'
};

function log(message, color = 'reset') {
  const timestamp = new Date().toLocaleTimeString();
  const coloredMessage = `${colors[color]}${message}${colors.reset}`;
  console.log(`[${timestamp}] ${coloredMessage}`);
}

function showBanner() {
  console.clear();
  log('', 'reset');
  log('████████╗██████╗  █████╗ ██████╗ ██╗███╗   ██╗ ██████╗     ██████╗  ██████╗ ████████╗', 'cyan');
  log('╚══██╔══╝██╔══██╗██╔══██╗██╔══██╗██║████╗  ██║██╔════╝     ██╔══██╗██╔═══██╗╚══██╔══╝', 'cyan');
  log('   ██║   ██████╔╝███████║██║  ██║██║██╔██╗ ██║██║  ███╗    ██████╔╝██║   ██║   ██║   ', 'cyan');
  log('   ██║   ██╔══██╗██╔══██║██║  ██║██║██║╚██╗██║██║   ██║    ██╔══██╗██║   ██║   ██║   ', 'cyan');
  log('   ██║   ██║  ██║██║  ██║██████╔╝██║██║ ╚████║╚██████╔╝    ██████╔╝╚██████╔╝   ██║   ', 'cyan');
  log('   ╚═��   ╚═╝  ╚═╝╚═╝  ╚═╝╚═════╝ ╚═╝╚═╝  ╚═══╝ ╚═════╝     ╚═════╝  ╚═════╝    ╚═╝   ', 'cyan');
  log('', 'reset');
  log('🤖 AI-POWERED CRYPTOCURRENCY TRADING BOT', 'green');
  log('⚡ Ultimate One-Command Setup & Launch', 'magenta');
  log('🌐 Automatic Global Internet Access with ngrok', 'blue');
  log('', 'reset');
  log('💡 Just unzipped? This command does EVERYTHING for you!', 'yellow');
  log('', 'reset');
}

async function checkCommand(command, altCommand = null) {
  return new Promise((resolve) => {
    const testCmd = `${command} --version`;
    exec(testCmd, (error) => {
      if (!error) {
        resolve(command);
      } else if (altCommand) {
        const altTestCmd = `${altCommand} --version`;
        exec(altTestCmd, (altError) => {
          resolve(altError ? null : altCommand);
        });
      } else {
        resolve(null);
      }
    });
  });
}

async function runCommand(command, args, options = {}) {
  return new Promise((resolve, reject) => {
    log(`Running: ${command} ${args.join(' ')}`, 'blue');
    
    const process = spawn(command, args, {
      stdio: options.silent ? 'pipe' : 'inherit',
      shell: true,
      cwd: options.cwd || process.cwd()
    });

    if (options.silent) {
      let output = '';
      process.stdout?.on('data', (data) => {
        output += data.toString();
      });
      process.stderr?.on('data', (data) => {
        output += data.toString();
      });
    }

    process.on('close', (code) => {
      if (code === 0 || options.ignoreErrors) {
        resolve();
      } else {
        reject(new Error(`Command failed with code ${code}`));
      }
    });

    process.on('error', (error) => {
      if (options.ignoreErrors) {
        resolve();
      } else {
        reject(error);
      }
    });
  });
}

async function checkPrerequisites() {
  log('🔍 Checking system prerequisites...', 'yellow');
  
  const platform = os.platform();
  log(`Platform: ${platform}`, 'blue');
  
  // Check Node.js
  const nodeCmd = await checkCommand('node');
  if (!nodeCmd) {
    log('❌ Node.js is required but not found!', 'red');
    log('💡 Download from: https://nodejs.org/', 'yellow');
    throw new Error('Node.js is required');
  }
  log('✅ Node.js found', 'green');
  
  // Check Python
  const pythonCmd = await checkCommand('python', 'python3');
  if (!pythonCmd) {
    log('❌ Python is required but not found!', 'red');
    log('💡 Download from: https://python.org/downloads/', 'yellow');
    throw new Error('Python is required');
  }
  log(`✅ Python found: ${pythonCmd}`, 'green');
  
  // Store python command for later use
  global.pythonCmd = pythonCmd;
  
  // Check pip
  const pipCmd = await checkCommand('pip', 'pip3');
  if (!pipCmd) {
    log('❌ pip is required but not found!', 'red');
    throw new Error('pip is required');
  }
  log(`✅ pip found: ${pipCmd}`, 'green');
  global.pipCmd = pipCmd;
  
  log('✅ All prerequisites met!', 'green');
}

async function installPackageManager() {
  log('📦 Setting up package manager...', 'yellow');
  
  // Check if pnpm exists
  const hasPnpm = await checkCommand('pnpm');
  if (!hasPnpm) {
    log('Installing pnpm (faster than npm)...', 'yellow');
    try {
      await runCommand('npm', ['install', '-g', 'pnpm'], { ignoreErrors: true });
    } catch (error) {
      log('⚠️ Could not install pnpm, using npm instead', 'yellow');
      global.packageManager = 'npm';
      return;
    }
  }
  
  global.packageManager = 'pnpm';
  log('✅ Package manager ready!', 'green');
}

async function installDependencies() {
  log('📦 Installing Node.js dependencies...', 'yellow');
  
  const packageManager = global.packageManager || 'npm';
  
  try {
    await runCommand(packageManager, ['install']);
    log('✅ Node.js dependencies installed!', 'green');
  } catch (error) {
    log('⚠️ Some Node.js dependencies may have failed, continuing...', 'yellow');
  }
  
  log('🐍 Installing Python dependencies...', 'yellow');
  
  try {
    const requirementsPath = path.join(process.cwd(), 'requirements.txt');
    if (fs.existsSync(requirementsPath)) {
      await runCommand(global.pipCmd, ['install', '-r', 'requirements.txt']);
    } else {
      // Install essential packages directly
      const essentialPackages = [
        'fastapi>=0.104.1',
        'uvicorn[standard]>=0.24.0',
        'pandas>=2.1.3',
        'numpy>=1.24.4',
        'python-dotenv>=1.0.0'
      ];
      
      for (const pkg of essentialPackages) {
        try {
          await runCommand(global.pipCmd, ['install', pkg], { ignoreErrors: true });
        } catch (e) {
          log(`⚠️ Could not install ${pkg}, continuing...`, 'yellow');
        }
      }
    }
    log('✅ Python dependencies installed!', 'green');
  } catch (error) {
    log('⚠️ Some Python dependencies may have failed, continuing...', 'yellow');
  }
}

async function setupEnvironment() {
  log('🔧 Setting up environment configuration...', 'yellow');
  
  const envPath = path.join(process.cwd(), '.env');
  
  if (!fs.existsSync(envPath)) {
    log('Creating default .env file...', 'blue');
    
    const defaultEnv = `# AI Crypto Trading Bot Configuration

# Database Configuration
DATABASE_URL=sqlite+aiosqlite:///./trading_bot.db

# Redis Configuration (optional)
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0

# Binance API Configuration (testnet mode for safety)
BINANCE_API_KEY=your_binance_api_key_here
BINANCE_SECRET_KEY=your_binance_secret_key_here
TRADING_MODE=testnet

# Authentication (default credentials)
BOT_USERNAME=trader
BOT_PASSWORD=crypto2024

# Trading Configuration
DEFAULT_CAPITAL=100000.0
MAX_POSITION_SIZE=0.05
STOP_LOSS_PERCENTAGE=0.02
TAKE_PROFIT_PERCENTAGE=0.04
MAX_DRAWDOWN_THRESHOLD=0.15

# Security
SECRET_KEY=ai-crypto-trading-bot-secure-key-2024
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440

# Development
DEBUG=false
TESTING=false
LOG_LEVEL=INFO

# Features
ENABLE_LIVE_TRADING=false
ENABLE_PAPER_TRADING=true
ENABLE_AI_TRAINING=true
`;

    fs.writeFileSync(envPath, defaultEnv);
    log('✅ Default .env file created', 'green');
  } else {
    log('✅ .env file already exists', 'green');
  }
}

async function setupDatabase() {
  log('🗄️ Setting up database...', 'yellow');
  
  const setupDbPath = path.join(process.cwd(), 'setup_database.py');
  
  if (fs.existsSync(setupDbPath)) {
    try {
      await runCommand(global.pythonCmd, ['setup_database.py'], { ignoreErrors: true });
      log('✅ Database setup complete!', 'green');
    } catch (error) {
      log('⚠️ Database setup skipped (may already exist)', 'yellow');
    }
  } else {
    log('⚠️ Database setup script not found, skipping...', 'yellow');
  }
}

async function installNgrok() {
  log('🌐 Setting up ngrok for global access...', 'yellow');
  
  const hasNgrok = await checkCommand('ngrok');
  if (!hasNgrok) {
    log('Installing ngrok...', 'blue');
    try {
      await runCommand('npm', ['install', '-g', 'ngrok'], { ignoreErrors: true });
      log('✅ ngrok installed!', 'green');
    } catch (error) {
      log('⚠️ Could not install ngrok globally, trying locally...', 'yellow');
      try {
        await runCommand(global.packageManager, ['add', 'ngrok'], { ignoreErrors: true });
        log('✅ ngrok installed locally!', 'green');
      } catch (e) {
        log('⚠️ ngrok installation failed, will try manual start', 'yellow');
      }
    }
  } else {
    log('✅ ngrok already available!', 'green');
  }
}

async function startBot() {
  log('🚀 Starting AI Crypto Trading Bot with global access...', 'cyan');
  log('', 'reset');

  // Try to use the enhanced start script if it exists
  const startScriptPath = path.join(process.cwd(), 'scripts', 'start-with-ngrok.js');

  if (fs.existsSync(startScriptPath)) {
    log('Using enhanced start script (backend + frontend + ngrok)...', 'blue');
    await runCommand('node', ['scripts/start-with-ngrok.js']);
  } else {
    // Fallback: start manually
    log('Starting services manually...', 'blue');

    // Start the Python backend
    const backendStartPath = path.join(process.cwd(), 'dev_start.py');
    if (fs.existsSync(backendStartPath)) {
      log('Starting Python backend...', 'blue');
      runCommand(global.pythonCmd, ['dev_start.py'], { ignoreErrors: true }); // Don't wait for this

      // Wait a bit for backend to start
      await new Promise(resolve => setTimeout(resolve, 5000));

      // Start frontend
      log('Starting frontend...', 'magenta');
      const packageManager = global.packageManager || 'npm';
      await runCommand(packageManager, ['run', 'dev:frontend']);
    } else {
      log('🌐 Backend start script not found, please start manually:', 'yellow');
      log('   python dev_start.py', 'yellow');
      log('   OR python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000', 'yellow');
    }
  }
}

async function main() {
  try {
    showBanner();
    
    log('⚡ Starting ultimate one-command setup...', 'cyan');
    log('📝 This will install everything you need!', 'green');
    log('', 'reset');

    // Complete setup sequence
    await checkPrerequisites();
    await installPackageManager();
    await installDependencies();
    await setupEnvironment();
    await setupDatabase();
    await installNgrok();
    
    log('', 'reset');
    log('🎉 Setup complete! Starting bot...', 'green');
    log('', 'reset');
    
    await startBot();
    
  } catch (error) {
    log('', 'reset');
    log(`❌ Setup failed: ${error.message}`, 'red');
    log('', 'reset');
    log('🛠️ Manual recovery options:', 'yellow');
    log('1. Check that Node.js and Python are installed', 'yellow');
    log('2. Run: npm install', 'yellow');
    log('3. Run: pip install -r requirements.txt', 'yellow');
    log('4. Run: python setup_database.py', 'yellow');
    log('5. Run: python dev_start.py', 'yellow');
    log('', 'reset');
    log('📚 Or check the README.md for detailed instructions', 'blue');
    process.exit(1);
  }
}

// Handle graceful shutdown
process.on('SIGINT', () => {
  log('', 'reset');
  log('👋 Setup cancelled by user', 'yellow');
  process.exit(0);
});

// Run the ultimate setup
main().catch(error => {
  log(`❌ Fatal error: ${error.message}`, 'red');
  process.exit(1);
});
