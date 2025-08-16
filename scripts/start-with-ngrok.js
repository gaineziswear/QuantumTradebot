#!/usr/bin/env node
/**
 * Crypto Trading Bot with ngrok Remote Access
 * Starts the trading bot with global internet access via ngrok
 */

const { spawn } = require('child_process');
const fs = require('fs');
const path = require('path');

// Configuration
const config = {
  port: 8080, // Frontend port (Vite serves frontend + proxies to backend)
  region: 'us', // Change to your region: us, eu, ap, au, sa, jp, in
  logFile: path.join(__dirname, '../logs/trading-bot.log')
};

// Colors for console output
const colors = {
  reset: '\x1b[0m',
  red: '\x1b[31m',
  green: '\x1b[32m',
  yellow: '\x1b[33m',
  blue: '\x1b[34m',
  magenta: '\x1b[35m',
  cyan: '\x1b[36m'
};

function log(message, color = 'reset') {
  const timestamp = new Date().toISOString();
  const coloredMessage = `${colors[color]}${message}${colors.reset}`;
  console.log(`[${timestamp}] ${coloredMessage}`);
  
  // Also log to file
  const logDir = path.dirname(config.logFile);
  if (!fs.existsSync(logDir)) {
    fs.mkdirSync(logDir, { recursive: true });
  }
  fs.appendFileSync(config.logFile, `[${timestamp}] ${message}\n`);
}

function checkNgrok() {
  return new Promise((resolve) => {
    const ngrokCheck = spawn('ngrok', ['--version'], { stdio: 'pipe' });
    
    ngrokCheck.on('close', (code) => {
      resolve(code === 0);
    });
    
    ngrokCheck.on('error', () => {
      resolve(false);
    });
  });
}

async function installNgrok() {
  log('Installing ngrok...', 'yellow');
  
  return new Promise((resolve, reject) => {
    const install = spawn('npm', ['install', '-g', 'ngrok'], { 
      stdio: 'inherit',
      shell: true 
    });
    
    install.on('close', (code) => {
      if (code === 0) {
        log('✅ ngrok installed successfully', 'green');
        resolve();
      } else {
        reject(new Error('Failed to install ngrok'));
      }
    });
  });
}

async function startBackend() {
  log('🚀 Starting AI Crypto Trading Bot Backend (Python FastAPI)...', 'cyan');

  return new Promise((resolve, reject) => {
    const bot = spawn('python', ['dev_start.py'], {
      stdio: 'pipe',
      shell: true,
      cwd: process.cwd()
    });

    bot.stdout.on('data', (data) => {
      const output = data.toString();
      if (output.includes('Application startup complete') || output.includes('Uvicorn running on')) {
        log('✅ AI Trading Bot backend is ready', 'green');
        resolve(bot);
      }
      // Log bot output
      output.split('\n').forEach(line => {
        if (line.trim()) {
          log(`[BACKEND] ${line.trim()}`, 'blue');
        }
      });
    });
    
    bot.stderr.on('data', (data) => {
      const error = data.toString();
      error.split('\n').forEach(line => {
        if (line.trim()) {
          log(`[BACKEND ERROR] ${line.trim()}`, 'red');
        }
      });
    });

    bot.on('close', (code) => {
      if (code !== 0) {
        reject(new Error(`Backend exited with code ${code}`));
      }
    });

    // Timeout after 30 seconds
    setTimeout(() => {
      reject(new Error('Backend startup timeout'));
    }, 30000);
  });
}

async function startFrontend() {
  log('🌐 Starting Frontend (React + Vite)...', 'magenta');

  return new Promise((resolve, reject) => {
    const packageManager = global.packageManager || 'pnpm';
    const frontend = spawn(packageManager, ['run', 'dev:frontend'], {
      stdio: 'pipe',
      shell: true,
      cwd: process.cwd()
    });

    frontend.stdout.on('data', (data) => {
      const output = data.toString();
      if (output.includes('ready in') || output.includes('Local:') || output.includes('localhost:8080')) {
        log('✅ Frontend server is ready', 'green');
        resolve(frontend);
      }
      // Log frontend output
      output.split('\n').forEach(line => {
        if (line.trim()) {
          log(`[FRONTEND] ${line.trim()}`, 'magenta');
        }
      });
    });

    frontend.stderr.on('data', (data) => {
      const error = data.toString();
      error.split('\n').forEach(line => {
        if (line.trim()) {
          log(`[FRONTEND ERROR] ${line.trim()}`, 'red');
        }
      });
    });

    frontend.on('close', (code) => {
      if (code !== 0) {
        reject(new Error(`Frontend exited with code ${code}`));
      }
    });

    // Timeout after 20 seconds
    setTimeout(() => {
      reject(new Error('Frontend startup timeout'));
    }, 20000);
  });
}

async function startNgrok() {
  log('🌐 Starting ngrok tunnel...', 'magenta');

  return new Promise((resolve, reject) => {
    const ngrokArgs = [
      'http',
      config.port.toString(),
      '--region', config.region
    ];
    
    const ngrok = spawn('ngrok', ngrokArgs, { 
      stdio: 'pipe',
      shell: true 
    });
    
    let tunnelUrl = null;
    
    ngrok.stdout.on('data', (data) => {
      const output = data.toString();
      
      // Parse ngrok output for tunnel URL
      const urlMatch = output.match(/https:\/\/[a-zA-Z0-9-]+\.ngrok\.io/);
      if (urlMatch && !tunnelUrl) {
        tunnelUrl = urlMatch[0];
        log(`✅ ngrok tunnel active: ${tunnelUrl}`, 'green');
        log(`🔐 Login with: trader / crypto2024`, 'yellow');
        resolve({ process: ngrok, url: tunnelUrl });
      }
      
      // Log ngrok output
      output.split('\n').forEach(line => {
        if (line.trim() && !line.includes('lvl=info')) {
          log(`[NGROK] ${line.trim()}`, 'magenta');
        }
      });
    });
    
    ngrok.stderr.on('data', (data) => {
      const error = data.toString();
      if (!error.includes('level=info')) {
        log(`[NGROK ERROR] ${error}`, 'red');
      }
    });
    
    ngrok.on('close', (code) => {
      if (code !== 0) {
        log(`ngrok exited with code ${code}`, 'red');
      }
    });
    
    // Timeout after 15 seconds
    setTimeout(() => {
      if (!tunnelUrl) {
        reject(new Error('ngrok tunnel startup timeout'));
      }
    }, 15000);
  });
}

async function validatePythonSetup() {
  log('🔍 Validating Python backend setup...', 'yellow');

  return new Promise((resolve, reject) => {
    const pythonPath = process.env.PYTHON_PATH || 'python3';
    const validationScript = path.join(process.cwd(), 'backend', 'validate_setup.py');

    const validation = spawn(pythonPath, [validationScript], {
      stdio: 'pipe',
      shell: true,
      cwd: process.cwd()
    });

    let stdout = '';
    let stderr = '';

    validation.stdout.on('data', (data) => {
      stdout += data.toString();
    });

    validation.stderr.on('data', (data) => {
      stderr += data.toString();
    });

    validation.on('close', (code) => {
      if (code === 0) {
        try {
          const result = JSON.parse(stdout.trim());
          if (result.status === 'success') {
            log('✅ Python backend validation passed', 'green');
            resolve(true);
          } else {
            log('❌ Python backend validation failed:', 'red');
            result.errors.forEach(error => {
              log(`  - ${error.message}`, 'red');
              log(`    Fix: ${error.fix}`, 'yellow');
            });
            reject(new Error('Python backend validation failed'));
          }
        } catch (e) {
          log('✅ Python backend appears to be working', 'green');
          resolve(true);
        }
      } else {
        log('❌ Python backend validation failed', 'red');
        if (stderr) log(stderr, 'red');
        reject(new Error('Python validation failed'));
      }
    });
  });
}

async function main() {
  try {
    log('🔄 Initializing Crypto Trading Bot with Global Access...', 'cyan');

    // Validate Python backend setup first
    await validatePythonSetup();

    // Check if ngrok is installed
    const hasNgrok = await checkNgrok();
    if (!hasNgrok) {
      await installNgrok();
    }
    
    // Start backend first
    log('Starting backend server...', 'yellow');
    const backendProcess = await startBackend();

    // Wait a bit for backend to fully initialize
    await new Promise(resolve => setTimeout(resolve, 3000));

    // Start frontend
    log('Starting frontend server...', 'yellow');
    const frontendProcess = await startFrontend();

    // Wait a bit for frontend to fully initialize
    await new Promise(resolve => setTimeout(resolve, 2000));
    
    // Start ngrok tunnel
    const ngrokResult = await startNgrok();
    
    // Success messages with enhanced display
    log('', 'reset');
    log('🎉 AI CRYPTO TRADING BOT IS NOW GLOBALLY ACCESSIBLE!', 'green');
    log('══════════════════════════════════════════════════════', 'cyan');
    log('', 'reset');
    log(`🌐 GLOBAL ACCESS URL: ${ngrokResult.url}`, 'cyan');
    log(`🌐 DIRECT LOGIN: ${ngrokResult.url}/login`, 'cyan');
    log('', 'reset');
    log(`🔐 LOGIN CREDENTIALS:`, 'yellow');
    log(`   👤 Username: trader`, 'yellow');
    log(`   🔑 Password: crypto2024`, 'yellow');
    log('', 'reset');
    log('🚀 SERVICES RUNNING:', 'blue');
    log('   ✅ Python Backend (AI Engine): http://localhost:8000', 'blue');
    log('   ✅ React Frontend (Dashboard): http://localhost:8080', 'blue');
    log('   ✅ ngrok Tunnel (Global Access): ' + ngrokResult.url, 'blue');
    log('', 'reset');
    log('📱 MOBILE READY: Works perfectly on phone browsers!', 'green');
    log('🤖 AI FEATURES: LSTM + Ensemble models with real-time learning', 'green');
    log('📊 REAL-TIME: Live prices, P&L tracking, automated trading', 'green');
    log('🛡️  SAFE MODE: Testnet trading with professional risk management', 'green');
    log('', 'reset');
    log('💰 FEATURES READY:', 'magenta');
    log('   • Click "START HEDGE FUND" to begin AI training', 'magenta');
    log('   • Monitor live trading with real-time dashboard', 'magenta');
    log('   • Track P&L and performance metrics', 'magenta');
    log('   • Mobile-optimized for trading on the go', 'magenta');
    log('', 'reset');
    log('💡 Press Ctrl+C to stop all services and tunnel', 'yellow');
    log('══════════════════════════════════════════════════════', 'cyan');
    log('', 'reset');
    
    // Handle graceful shutdown
    process.on('SIGINT', () => {
      log('🛑 Shutting down...', 'yellow');
      ngrokResult.process.kill();
      backendProcess.kill();
      frontendProcess.kill();
      process.exit(0);
    });
    
    // Keep the script running
    process.on('exit', () => {
      log('👋 Trading bot stopped', 'cyan');
    });
    
  } catch (error) {
    log(`❌ Error: ${error.message}`, 'red');
    process.exit(1);
  }
}

// Run the application
main().catch(error => {
  log(`❌ Fatal error: ${error.message}`, 'red');
  process.exit(1);
});
