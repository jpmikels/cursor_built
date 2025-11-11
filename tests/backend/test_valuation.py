"""Valuation engine tests."""
import pytest
from valuation.wacc import WACCCalculator
from valuation.dcf import DCFValuation
from valuation.gpcm import GPCMValuation


def test_wacc_calculation():
    """Test WACC calculation."""
    calculator = WACCCalculator()
    
    inputs = {
        'risk_free_rate': 0.045,
        'equity_risk_premium': 0.06,
        'beta': 1.2,
        'size_premium': 0.02,
        'company_specific_premium': 0.01,
        'cost_of_debt': 0.06,
        'tax_rate': 0.25,
        'debt_weight': 0.3,
        'equity_weight': 0.7
    }
    
    result = calculator.calculate_wacc(inputs)
    
    assert 'wacc' in result
    assert 'cost_of_equity' in result
    assert result['wacc'] > 0
    assert result['wacc'] < 1


def test_dcf_calculation():
    """Test DCF valuation."""
    dcf = DCFValuation()
    
    historical = {
        'cash': 1000000,
        'total_debt': 500000
    }
    
    forecast = {
        'free_cash_flow': [100000, 110000, 120000, 130000, 140000]
    }
    
    result = dcf.calculate_dcf(
        historical_financials=historical,
        forecast=forecast,
        wacc=0.10,
        terminal_growth_rate=0.025,
        mid_year_convention=True
    )
    
    assert 'enterprise_value' in result
    assert 'equity_value' in result
    assert result['enterprise_value'] > 0


def test_gpcm_calculation():
    """Test GPCM valuation."""
    gpcm = GPCMValuation()
    
    subject = {
        'revenue': 5000000,
        'ebitda': 1000000
    }
    
    comparables = [
        {
            'name': 'Comp A',
            'ticker': 'COMPA',
            'metrics': {
                'enterprise_value': 50000000,
                'revenue': 10000000,
                'ebitda': 2000000
            }
        },
        {
            'name': 'Comp B',
            'ticker': 'COMPB',
            'metrics': {
                'enterprise_value': 60000000,
                'revenue': 12000000,
                'ebitda': 2400000
            }
        }
    ]
    
    result = gpcm.calculate_gpcm(
        subject_metrics=subject,
        comparable_companies=comparables,
        multiples_to_use=['EV/Revenue', 'EV/EBITDA'],
        liquidity_discount=0.25
    )
    
    assert 'concluded_value' in result
    assert result['concluded_value'] > 0

