#!/usr/bin/env python3
"""
Automation Status Script
Returns current status of the hedge fund automation system
"""

import json
import sys
import os

# Add the backend directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Load environment variables
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    # dotenv not available, skip
    pass

from hedge_fund_automation import hedge_fund_automation

def get_status():
    """Get current automation status"""
    try:
        status = hedge_fund_automation.get_automation_status()
        
        # Add additional system information
        status['system_info'] = {
            'script_version': '1.0.0',
            'timestamp': status.get('last_updated', None),
            'automation_initialized': True
        }
        
        return status
        
    except Exception as e:
        # Return safe default status if there's an error
        return {
            'is_running': False,
            'current_phase': 'error',
            'progress_percentage': 0,
            'last_action': f'Error retrieving status: {str(e)}',
            'started_at': None,
            'total_runtime': 0,
            'symbols_processed': 0,
            'total_symbols': 10,
            'model_confidence': 0,
            'risk_score': 0,
            'trading_mode': 'testnet',
            'market_data_symbols': [],
            'live_prices': {},
            'risk_metrics': {},
            'system_info': {
                'script_version': '1.0.0',
                'error': str(e),
                'automation_initialized': False
            }
        }

if __name__ == "__main__":
    try:
        result = get_status()
        print(json.dumps(result))
    except Exception as e:
        error_result = {
            'is_running': False,
            'current_phase': 'critical_error',
            'progress_percentage': 0,
            'last_action': f'Critical error: {str(e)}',
            'error': str(e)
        }
        print(json.dumps(error_result))
        sys.exit(1)
