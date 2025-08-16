#!/usr/bin/env python3
"""
Automation Start Script
Initializes and starts the hedge fund automation workflow
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

async def start_automation():
    """Start the complete hedge fund automation workflow"""
    try:
        # Initialize the automation system
        if not await hedge_fund_automation.initialize():
            return {
                'success': False,
                'message': 'Failed to initialize automation system',
                'error': 'Initialization failed'
            }
        
        # Start the automated workflow in a non-blocking way
        # The workflow runs continuously, so we start it and return immediately
        asyncio.create_task(hedge_fund_automation.start_automated_workflow())
        success = True
        
        if success:
            return {
                'success': True,
                'message': 'Hedge fund automation started successfully',
                'data': hedge_fund_automation.get_automation_status()
            }
        else:
            return {
                'success': False,
                'message': 'Failed to start automation workflow',
                'error': 'Workflow startup failed'
            }
            
    except Exception as e:
        return {
            'success': False,
            'message': f'Error starting automation: {str(e)}',
            'error': str(e)
        }

if __name__ == "__main__":
    try:
        result = asyncio.run(start_automation())
        print(json.dumps(result))
    except Exception as e:
        error_result = {
            'success': False,
            'message': f'Critical error: {str(e)}',
            'error': str(e)
        }
        print(json.dumps(error_result))
        sys.exit(1)
