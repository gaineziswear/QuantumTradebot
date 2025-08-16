#!/usr/bin/env python3
"""
Setup Validation Script
Checks if all dependencies and configurations are properly set up
"""

import sys
import os
import json

def validate_imports():
    """Validate that all required Python packages are available"""
    required_packages = [
        'pandas', 'numpy', 'torch', 'sklearn', 'ta', 'binance',
        'aiohttp', 'loguru', 'pydantic', 'sqlalchemy', 'jose', 'passlib'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            missing_packages.append(package)
    
    return missing_packages

def validate_environment():
    """Validate environment variables"""
    required_env_vars = [
        'BINANCE_API_KEY', 'BINANCE_SECRET_KEY', 'BOT_USERNAME', 'BOT_PASSWORD'
    ]
    
    missing_env_vars = []
    
    for var in required_env_vars:
        if not os.getenv(var):
            missing_env_vars.append(var)
    
    return missing_env_vars

def validate_files():
    """Validate that required files exist"""
    backend_dir = os.path.dirname(os.path.abspath(__file__))
    required_files = [
        'config.py', 'database.py', 'ai_model.py', 'binance_client.py',
        'hedge_fund_automation.py', 'auth.py'
    ]
    
    missing_files = []
    
    for file in required_files:
        file_path = os.path.join(backend_dir, file)
        if not os.path.exists(file_path):
            missing_files.append(file)
    
    return missing_files

def main():
    """Main validation function"""
    validation_results = {
        'status': 'success',
        'errors': [],
        'warnings': [],
        'info': []
    }
    
    # Check imports
    missing_packages = validate_imports()
    if missing_packages:
        validation_results['status'] = 'error'
        validation_results['errors'].append({
            'type': 'missing_packages',
            'message': f"Missing Python packages: {', '.join(missing_packages)}",
            'fix': f"Run: pip install {' '.join(missing_packages)}"
        })
    
    # Check environment variables
    missing_env_vars = validate_environment()
    if missing_env_vars:
        validation_results['status'] = 'error'
        validation_results['errors'].append({
            'type': 'missing_env_vars',
            'message': f"Missing environment variables: {', '.join(missing_env_vars)}",
            'fix': "Set these variables in your .env file or environment"
        })
    
    # Check files
    missing_files = validate_files()
    if missing_files:
        validation_results['status'] = 'error'
        validation_results['errors'].append({
            'type': 'missing_files',
            'message': f"Missing backend files: {', '.join(missing_files)}",
            'fix': "Ensure all backend Python files are present"
        })
    
    # Additional validations
    try:
        import torch
        if torch.cuda.is_available():
            validation_results['info'].append("CUDA available for GPU acceleration")
        else:
            validation_results['warnings'].append("CUDA not available, using CPU only")
    except ImportError:
        pass
    
    # Check if running in correct directory
    if not os.path.exists('../package.json'):
        validation_results['warnings'].append("Script should be run from the backend directory")
    
    if validation_results['status'] == 'success':
        validation_results['message'] = "All validations passed successfully"
    else:
        validation_results['message'] = f"Found {len(validation_results['errors'])} errors"
    
    return validation_results

if __name__ == "__main__":
    try:
        # Load environment variables
        try:
            from dotenv import load_dotenv
            load_dotenv()
        except ImportError:
            pass
        
        result = main()
        print(json.dumps(result, indent=2))
        
        if result['status'] != 'success':
            sys.exit(1)
            
    except Exception as e:
        error_result = {
            'status': 'error',
            'message': f'Validation script failed: {str(e)}',
            'errors': [{'type': 'script_error', 'message': str(e)}]
        }
        print(json.dumps(error_result, indent=2))
        sys.exit(1)
