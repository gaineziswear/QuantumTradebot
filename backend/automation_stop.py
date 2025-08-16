#!/usr/bin/env python3
"""
Automation Stop Script
Safely stops the hedge fund automation workflow
"""

import asyncio
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

async def stop_automation():
    """Stop the automation workflow safely"""
    try:
        await hedge_fund_automation.stop_automation()
        
        return {
            'success': True,
            'message': 'Automation stopped successfully',
            'final_status': hedge_fund_automation.get_automation_status()
        }
        
    except Exception as e:
        return {
            'success': False,
            'message': f'Error stopping automation: {str(e)}',
            'error': str(e)
        }

if __name__ == "__main__":
    try:
        result = asyncio.run(stop_automation())
        print(json.dumps(result))
    except Exception as e:
        error_result = {
            'success': False,
            'message': f'Critical error stopping automation: {str(e)}',
            'error': str(e)
        }
        print(json.dumps(error_result))
        sys.exit(1)
