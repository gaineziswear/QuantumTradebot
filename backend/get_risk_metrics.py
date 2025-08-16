#!/usr/bin/env python3
"""
Risk Metrics Script
Returns comprehensive risk management metrics
"""

import json
import sys
import os

# Add the backend directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from hedge_fund_automation import hedge_fund_automation

def get_risk_metrics():
    """Get current risk management metrics"""
    try:
        # Get risk metrics from automation system
        risk_metrics = hedge_fund_automation.risk_metrics
        automation_status = hedge_fund_automation.get_automation_status()
        
        # Enhanced risk metrics
        enhanced_metrics = {
            # Position sizing and limits
            'max_position_size': risk_metrics.get('max_position_size', 0.05),
            'stop_loss_percentage': risk_metrics.get('stop_loss_percentage', 0.02),
            'take_profit_percentage': risk_metrics.get('take_profit_percentage', 0.04),
            'max_drawdown_threshold': risk_metrics.get('max_drawdown', 0.15),
            'max_concurrent_positions': risk_metrics.get('max_concurrent_positions', 10),
            
            # Current state
            'current_drawdown': risk_metrics.get('current_drawdown', 0.0),
            'active_positions': risk_metrics.get('active_positions', 0),
            'risk_score': automation_status.get('risk_score', 0.0),
            
            # Advanced metrics
            'var_95': risk_metrics.get('var_95', 0.0),
            'volatility_target': 0.20,  # 20% target volatility
            'confidence_level': 0.95,   # 95% VaR confidence
            'kelly_criterion_enabled': True,
            'portfolio_correlation_limit': 0.7,
            
            # Risk management features
            'features': {
                'stop_loss': True,
                'take_profit': True,
                'position_sizing': True,
                'correlation_monitoring': True,
                'drawdown_protection': True,
                'emergency_stop': True
            },
            
            # Limits and thresholds
            'limits': {
                'daily_loss_limit': 0.05,      # 5% daily loss limit
                'weekly_loss_limit': 0.10,     # 10% weekly loss limit
                'monthly_loss_limit': 0.20,    # 20% monthly loss limit
                'leverage_limit': 1.0,         # No leverage
                'concentration_limit': 0.15    # Max 15% in single position
            },
            
            # Trading mode and environment
            'trading_mode': automation_status.get('trading_mode', 'testnet'),
            'last_updated': automation_status.get('started_at'),
            'system_status': 'operational' if automation_status.get('is_running') else 'idle'
        }
        
        return enhanced_metrics
        
    except Exception as e:
        # Return safe default metrics
        return {
            'max_position_size': 0.05,
            'stop_loss_percentage': 0.02,
            'take_profit_percentage': 0.04,
            'max_drawdown_threshold': 0.15,
            'current_drawdown': 0.0,
            'var_95': 0.0,
            'risk_score': 0.0,
            'active_positions': 0,
            'max_concurrent_positions': 10,
            'trading_mode': 'testnet',
            'system_status': 'error',
            'error': str(e)
        }

if __name__ == "__main__":
    try:
        result = get_risk_metrics()
        print(json.dumps(result))
    except Exception as e:
        error_result = {
            'error': str(e),
            'message': f'Critical error getting risk metrics: {str(e)}',
            'system_status': 'critical_error'
        }
        print(json.dumps(error_result))
        sys.exit(1)
