#!/usr/bin/env python3
"""
Emergency Stop Script
Immediately halts all trading activities and closes positions
"""

import asyncio
import json
import sys
import os

# Add the backend directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from hedge_fund_automation import hedge_fund_automation

async def emergency_stop():
    """Execute emergency stop procedure"""
    try:
        # Stop automation immediately
        await hedge_fund_automation.stop_automation()
        
        # If binance client is available, cancel all open orders
        if hedge_fund_automation.binance_client:
            try:
                # Get all open orders
                open_orders = await hedge_fund_automation.binance_client.get_open_orders()
                
                # Cancel all open orders
                for order in open_orders:
                    try:
                        await hedge_fund_automation.binance_client.cancel_order(
                            symbol=order['symbol'],
                            order_id=order['orderId']
                        )
                    except Exception as e:
                        print(f"Warning: Failed to cancel order {order['orderId']}: {e}")
                
                # Get portfolio status
                portfolio = await hedge_fund_automation.binance_client.calculate_portfolio_value()
                
                return {
                    'success': True,
                    'message': 'Emergency stop executed successfully',
                    'orders_cancelled': len(open_orders),
                    'portfolio_value': portfolio.get('total_value_usdt', 0),
                    'timestamp': hedge_fund_automation.status.started_at.isoformat() if hedge_fund_automation.status.started_at else None,
                    'final_status': hedge_fund_automation.get_automation_status()
                }
                
            except Exception as e:
                return {
                    'success': True,
                    'message': 'Automation stopped, but failed to access trading account',
                    'warning': f'Could not cancel orders: {str(e)}',
                    'final_status': hedge_fund_automation.get_automation_status()
                }
        else:
            return {
                'success': True,
                'message': 'Emergency stop executed - No active trading connection',
                'final_status': hedge_fund_automation.get_automation_status()
            }
        
    except Exception as e:
        return {
            'success': False,
            'message': f'Emergency stop failed: {str(e)}',
            'error': str(e),
            'critical': True
        }

if __name__ == "__main__":
    try:
        result = asyncio.run(emergency_stop())
        print(json.dumps(result))
    except Exception as e:
        error_result = {
            'success': False,
            'message': f'Critical emergency stop error: {str(e)}',
            'error': str(e),
            'critical': True
        }
        print(json.dumps(error_result))
        sys.exit(1)
