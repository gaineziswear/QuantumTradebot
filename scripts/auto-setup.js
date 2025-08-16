#!/usr/bin/env node
/**
 * AI Crypto Trading Bot - Automatic Setup & Global Access
 * One-command setup that handles everything: dependencies, database, ngrok
 */

const { spawn, exec } = require('child_process');
const fs = require('fs');
const path = require('path');

// Colors for beautiful console output
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

function banner() {
  console.clear();
  log('', 'reset');
  log('██████╗ ██████╗ ██╗   ██╗██████╗ ████████╗ ██████╗     ██████╗  ██████╗ ████████╗', 'cyan');
  log('██╔══██╗██╔══██╗╚██╗ ██╔╝██╔══██╗╚══██╔══╝██╔═══██╗    ██╔══██╗██╔═══██╗╚══██╔══╝', 'cyan');
  log('██████╔╝██████╔╝ ╚████╔╝ ██████╔╝   ██║   ██║   ██║    ██████╔╝██║   ██║   ██║   ', 'cyan');
  log('██╔═══╝ ██╔══██╗  ╚██╔╝  ██╔═══╝    ██║   ██║   ██║    ██╔══██╗██║   ██║   ██║   ', 'cyan');
  log('██║     ██║  ██║   ██║   ██║        ██║   ╚██████╔╝    ██████╔╝╚██████╔╝   ██║   ', 'cyan');
  log('╚���╝     ╚═╝  ╚═╝   ╚═╝   ╚═╝        ╚═╝    ╚═════╝     ╚═════╝  ╚═════╝    ╚═╝   ', 'cyan');
  log('', 'reset');
  log('🤖 AI-POWERED CRYPTOCURRENCY TRADING BOT', 'green');
  log('🌐 Automatic Setup with Global Internet Access', 'magenta');
  log('', 'reset');
}

async function checkCommand(command) {
  return new Promise((resolve) => {
    exec(`${command} --version`, (error) => {
      resolve(!error);
    });
  });
}

async function runCommand(command, args, options = {}) {
  return new Promise((resolve, reject) => {
    const process = spawn(command, args, {
      stdio: options.silent ? 'pipe' : 'inherit',
      shell: true,
      ...options
    });

    process.on('close', (code) => {
      if (code === 0) {
        resolve();
      } else {
        reject(new Error(`Command failed with code ${code}`));
      }
    });
  });
}

async function setupDependencies() {
  log('📦 Installing dependencies...', 'yellow');
  
  // Check if pnpm is available
  const hasPnpm = await checkCommand('pnpm');
  if (!hasPnpm) {
    log('Installing pnpm package manager...', 'yellow');
    await runCommand('npm', ['install', '-g', 'pnpm']);
  }

  // Install Node.js dependencies
  log('📦 Installing Node.js dependencies...', 'blue');
  await runCommand('pnpm', ['install']);

  // Check for Python
  const hasPython = await checkCommand('python') || await checkCommand('python3');
  if (!hasPython) {
    log('❌ Python is required but not found. Please install Python 3.8+', 'red');
    process.exit(1);
  }

  // Install Python dependencies
  log('🐍 Installing Python dependencies...', 'blue');
  await runCommand('pnpm', ['run', 'setup:python']);
  
  log('✅ All dependencies installed!', 'green');
}

async function setupDatabase() {
  log('🗄️ Setting up database...', 'yellow');
  
  try {
    await runCommand('python', ['setup_database.py']);
    log('✅ Database setup complete!', 'green');
  } catch (error) {
    log('⚠️ Database setup skipped (may already exist)', 'yellow');
  }
}

async function checkEnvironment() {
  log('🔧 Checking environment configuration...', 'yellow');
  
  const envPath = path.join(process.cwd(), '.env');
  if (fs.existsSync(envPath)) {
    log('✅ Environment file found', 'green');
  } else {
    log('⚠️ No .env file found - using defaults', 'yellow');
  }
}

async function installNgrok() {
  log('🌐 Setting up ngrok for global access...', 'magenta');
  
  const hasNgrok = await checkCommand('ngrok');
  if (!hasNgrok) {
    log('Installing ngrok...', 'yellow');
    await runCommand('npm', ['install', '-g', 'ngrok']);
  }
  
  log('✅ ngrok ready for global access!', 'green');
}

async function startBot() {
  log('🚀 Starting AI Crypto Trading Bot with global access...', 'cyan');
  
  // Start the enhanced ngrok script
  await runCommand('node', ['scripts/start-with-ngrok.js']);
}

async function main() {
  try {
    banner();
    
    log('🔄 Starting automatic setup...', 'cyan');
    log('', 'reset');

    // Setup steps
    await setupDependencies();
    await setupDatabase();
    await checkEnvironment();
    await installNgrok();
    
    log('', 'reset');
    log('🎉 Setup complete! Starting bot...', 'green');
    log('', 'reset');
    
    // Start the bot with ngrok
    await startBot();
    
  } catch (error) {
    log(`❌ Error during setup: ${error.message}`, 'red');
    log('', 'reset');
    log('🔧 Try running these commands manually:', 'yellow');
    log('   pnpm install', 'yellow');
    log('   pnpm run setup:python', 'yellow');
    log('   python setup_database.py', 'yellow');
    log('   pnpm run start:global', 'yellow');
    process.exit(1);
  }
}

// Handle graceful shutdown
process.on('SIGINT', () => {
  log('', 'reset');
  log('👋 Setup cancelled', 'yellow');
  process.exit(0);
});

// Run the setup
main().catch(error => {
  log(`❌ Fatal error: ${error.message}`, 'red');
  process.exit(1);
});
