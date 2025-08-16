#!/usr/bin/env node
/**
 * System Test Script
 * Tests the main components of the crypto trading bot
 */

const fs = require('fs');
const path = require('path');

console.log('🧪 Testing Crypto Trading Bot System...\n');

// Test 1: Check if all required files exist
console.log('1️⃣ Checking file structure...');
const requiredFiles = [
  'package.json',
  'client/pages/Dashboard.tsx',
  'client/lib/api.ts',
  'server/index.ts',
  'server/routes/trading.ts',
  'shared/api.ts',
  'backend/config.py',
  'backend/hedge_fund_automation.py',
  'backend/automation_start.py',
  'backend/automation_status.py',
  'backend/automation_stop.py',
  'requirements.txt',
  '.env.example'
];

let missingFiles = [];
for (const file of requiredFiles) {
  if (!fs.existsSync(file)) {
    missingFiles.push(file);
  }
}

if (missingFiles.length === 0) {
  console.log('✅ All required files present');
} else {
  console.log('❌ Missing files:', missingFiles.join(', '));
}

// Test 2: Check package.json scripts
console.log('\n2️⃣ Checking package.json scripts...');
const packageJson = JSON.parse(fs.readFileSync('package.json', 'utf8'));
const requiredScripts = ['dev', 'start:global', 'setup:python'];

let missingScripts = [];
for (const script of requiredScripts) {
  if (!packageJson.scripts[script]) {
    missingScripts.push(script);
  }
}

if (missingScripts.length === 0) {
  console.log('✅ All required scripts present');
} else {
  console.log('❌ Missing scripts:', missingScripts.join(', '));
}

// Test 3: Check environment variables example
console.log('\n3️⃣ Checking environment configuration...');
const envExample = fs.readFileSync('.env.example', 'utf8');
const requiredEnvVars = [
  'BINANCE_API_KEY',
  'BINANCE_SECRET_KEY',
  'BOT_USERNAME',
  'BOT_PASSWORD',
  'TRADING_MODE'
];

let missingEnvVars = [];
for (const envVar of requiredEnvVars) {
  if (!envExample.includes(envVar)) {
    missingEnvVars.push(envVar);
  }
}

if (missingEnvVars.length === 0) {
  console.log('✅ All required environment variables documented');
} else {
  console.log('❌ Missing environment variables:', missingEnvVars.join(', '));
}

// Test 4: Check TypeScript imports
console.log('\n4️⃣ Checking TypeScript configuration...');
const sharedApi = fs.readFileSync('shared/api.ts', 'utf8');
const requiredTypes = ['AutomationStatus', 'TradingStatus', 'Trade', 'AIStatus'];

let missingTypes = [];
for (const type of requiredTypes) {
  if (!sharedApi.includes(`export interface ${type}`)) {
    missingTypes.push(type);
  }
}

if (missingTypes.length === 0) {
  console.log('✅ All required TypeScript interfaces present');
} else {
  console.log('❌ Missing TypeScript interfaces:', missingTypes.join(', '));
}

// Test 5: Check Python requirements
console.log('\n5️⃣ Checking Python requirements...');
const requirements = fs.readFileSync('requirements.txt', 'utf8');
const requiredPackages = ['fastapi', 'pandas', 'torch', 'python-jose', 'passlib'];

let missingPackages = [];
for (const pkg of requiredPackages) {
  if (!requirements.includes(pkg)) {
    missingPackages.push(pkg);
  }
}

if (missingPackages.length === 0) {
  console.log('✅ All required Python packages listed');
} else {
  console.log('❌ Missing Python packages:', missingPackages.join(', '));
}

// Summary
console.log('\n📊 Test Summary:');
const totalTests = 5;
const passedTests = [
  missingFiles.length === 0,
  missingScripts.length === 0,
  missingEnvVars.length === 0,
  missingTypes.length === 0,
  missingPackages.length === 0
].filter(Boolean).length;

console.log(`✅ Passed: ${passedTests}/${totalTests} tests`);

if (passedTests === totalTests) {
  console.log('\n🎉 All system tests passed! The crypto trading bot should work properly.');
  console.log('\n🚀 Next steps:');
  console.log('1. Copy .env.example to .env and fill in your API keys');
  console.log('2. Run: pnpm setup:python (to install Python dependencies)');
  console.log('3. Run: pnpm start:global (to start with global access)');
  console.log('4. Open the provided URL and login with: trader / crypto2024');
} else {
  console.log('\n❌ Some tests failed. Please check the issues above.');
  process.exit(1);
}
