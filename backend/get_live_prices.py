#!/usr/bin/env python3
"""
Get Live Prices Script
Fetches current cryptocurrency prices from Binance
"""

import asyncio
import json
import sys
import os

# Add the backend directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from hedge_fund_automation import hedge_fund_automation

async def get_live_prices():
    """Get current live cryptocurrency prices"""
    try:
        # Initialize if not already done
        if not hedge_fund_automation.binance_client:
            if not await hedge_fund_automation.initialize():
                return {
                    'success': False,
                    'message': 'Failed to initialize Binance client',
                    'prices': {}
                }
        
        # Get live prices from the automation system
        prices = hedge_fund_automation.get_live_prices()
        
        # If no cached prices, fetch fresh ones
        if not prices:
            try:
                await hedge_fund_automation._start_price_ticker()
                prices = hedge_fund_automation.get_live_prices()
            except Exception as e:
                # If ticker fails, return empty prices
                prices = {}
        
        return {
            'success': True,
            'prices': prices,
            'timestamp': hedge_fund_automation.status.started_at.isoformat() if hedge_fund_automation.status.started_at else None,
            'trading_mode': hedge_fund_automation.status.trading_mode
        }
        
    except Exception as e:
        return {
            'success': False,
            'message': f'Error fetching live prices: {str(e)}',
            'prices': {},
            'error': str(e)
        }

if __name__ == "__main__":
    try:
        result = asyncio.run(get_live_prices())
        print(json.dumps(result))
    except Exception as e:
        error_result = {
            'success': False,
            'message': f'Critical error: {str(e)}',
            'prices': {},
            'error': str(e)
        }
        print(json.dumps(error_result))
        sys.exit(1)
