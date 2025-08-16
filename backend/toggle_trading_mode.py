#!/usr/bin/env python3
"""
Toggle Trading Mode Script
Switches between testnet and live trading modes
"""

import asyncio
import json
import sys
import os

# Add the backend directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from hedge_fund_automation import hedge_fund_automation

async def toggle_mode(mode):
    """Toggle between testnet and live trading"""
    try:
        success = await hedge_fund_automation.toggle_trading_mode(mode)
        
        if success:
            return {
                'success': True,
                'message': f'Successfully switched to {mode.upper()} mode',
                'new_mode': mode,
                'status': hedge_fund_automation.get_automation_status()
            }
        else:
            return {
                'success': False,
                'message': f'Failed to switch to {mode} mode',
                'current_mode': hedge_fund_automation.status.trading_mode
            }
            
    except Exception as e:
        return {
            'success': False,
            'message': f'Error toggling trading mode: {str(e)}',
            'error': str(e)
        }

if __name__ == "__main__":
    try:
        if len(sys.argv) < 2:
            result = {
                'success': False,
                'message': 'Trading mode not specified. Use "testnet" or "live"',
                'error': 'Missing mode parameter'
            }
        else:
            mode = sys.argv[1].lower()
            if mode not in ['testnet', 'live']:
                result = {
                    'success': False,
                    'message': 'Invalid trading mode. Use "testnet" or "live"',
                    'error': 'Invalid mode parameter'
                }
            else:
                result = asyncio.run(toggle_mode(mode))
        
        print(json.dumps(result))
    except Exception as e:
        error_result = {
            'success': False,
            'message': f'Critical error: {str(e)}',
            'error': str(e)
        }
        print(json.dumps(error_result))
        sys.exit(1)
