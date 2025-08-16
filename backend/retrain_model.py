#!/usr/bin/env python3
"""
AI Model Retraining Script
Triggers AI model retraining with latest market data
"""

import asyncio
import json
import sys
import os

# Add the backend directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from hedge_fund_automation import hedge_fund_automation

async def retrain_model():
    """Retrain the AI model with latest data"""
    try:
        # Initialize if not already done
        if not hedge_fund_automation.ai_model:
            if not await hedge_fund_automation.initialize():
                return {
                    'success': False,
                    'message': 'Failed to initialize AI system',
                    'error': 'Initialization failed'
                }
        
        # Start retraining process
        hedge_fund_automation.status.current_phase = "training"
        hedge_fund_automation.status.last_action = "Retraining AI model with latest data"
        hedge_fund_automation.status.progress_percentage = 0
        
        # Fetch fresh data if needed
        if not hedge_fund_automation.market_data:
            await hedge_fund_automation._phase_1_fetch_data()
        
        # Retrain the model
        await hedge_fund_automation._phase_2_train_model()
        
        return {
            'success': True,
            'message': 'AI model retrained successfully',
            'model_confidence': hedge_fund_automation.status.model_confidence,
            'confidence': hedge_fund_automation.status.model_confidence,
            'status': hedge_fund_automation.get_automation_status()
        }
        
    except Exception as e:
        return {
            'success': False,
            'message': f'Error retraining model: {str(e)}',
            'error': str(e)
        }

if __name__ == "__main__":
    try:
        result = asyncio.run(retrain_model())
        print(json.dumps(result))
    except Exception as e:
        error_result = {
            'success': False,
            'message': f'Critical error retraining model: {str(e)}',
            'error': str(e)
        }
        print(json.dumps(error_result))
        sys.exit(1)
