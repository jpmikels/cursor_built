"""
CCA (Comparable Company Analysis) Engine.
"""

import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)


class CCAEngine:
    """
    Performs Comparable Company Analysis valuation.
    """
    
    def __init__(self):
        """Initialize the CCA engine."""
        pass
    
    def calculate_cca(
        self,
        financial_data: Dict[str, Dict[int, float]],
        assumptions: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Calculate valuation using comparable company multiples.
        
        Args:
            financial_data: Dict mapping metric_name -> {year: value}
            assumptions: Valuation assumptions including multiples
            
        Returns:
            CCA valuation results
        """
        logger.info("Calculating CCA valuation")
        
        try:
            # Get EBITDA multiples from assumptions
            ebitda_multiple_min = float(assumptions.get('ebitda_multiple_min', 5.0))
            ebitda_multiple_median = float(assumptions.get('ebitda_multiple_median', 7.0))
            ebitda_multiple_max = float(assumptions.get('ebitda_multiple_max', 9.0))
            
            # Get latest EBITDA
            ebitda_history = financial_data.get('ebitda', {})
            
            if not ebitda_history:
                # Try to calculate EBITDA from other metrics
                revenue_history = financial_data.get('revenue', {})
                if revenue_history:
                    latest_year = max(revenue_history.keys())
                    # Use 20% margin as default
                    latest_ebitda = revenue_history[latest_year] * 0.20
                else:
                    raise ValueError("EBITDA or Revenue data required for CCA calculation")
            else:
                latest_year = max(ebitda_history.keys())
                latest_ebitda = ebitda_history[latest_year]
            
            logger.info(f"Using EBITDA: {latest_ebitda:,.2f} for year {latest_year}")
            
            # Calculate Enterprise Values
            ev_min = latest_ebitda * ebitda_multiple_min
            ev_median = latest_ebitda * ebitda_multiple_median
            ev_max = latest_ebitda * ebitda_multiple_max
            
            # Get cash and debt
            cash = financial_data.get('cash', {}).get(latest_year, 0)
            debt = financial_data.get('debt', {}).get(latest_year, 0)
            
            # Calculate Equity Values
            equity_value_min = ev_min + cash - debt
            equity_value_median = ev_median + cash - debt
            equity_value_max = ev_max + cash - debt
            
            logger.info(f"CCA calculation complete: Equity range={equity_value_min:,.2f} to {equity_value_max:,.2f}")
            
            return {
                'ev_min': ev_min,
                'ev_median': ev_median,
                'ev_max': ev_max,
                'equity_value_min': equity_value_min,
                'equity_value_median': equity_value_median,
                'equity_value_max': equity_value_max,
                'ebitda_used': latest_ebitda,
                'ebitda_year': latest_year,
                'multiple_min': ebitda_multiple_min,
                'multiple_median': ebitda_multiple_median,
                'multiple_max': ebitda_multiple_max,
                'cash': cash,
                'debt': debt
            }
            
        except Exception as e:
            logger.error(f"Error calculating CCA: {e}")
            raise
    
    def calculate_revenue_multiples(
        self,
        financial_data: Dict[str, Dict[int, float]],
        revenue_multiple: float
    ) -> Dict[str, Any]:
        """
        Alternative valuation using revenue multiples.
        
        Args:
            financial_data: Financial data
            revenue_multiple: Revenue multiple to apply
            
        Returns:
            Revenue-based valuation
        """
        logger.info("Calculating revenue multiple valuation")
        
        try:
            revenue_history = financial_data.get('revenue', {})
            
            if not revenue_history:
                raise ValueError("Revenue data required")
            
            latest_year = max(revenue_history.keys())
            latest_revenue = revenue_history[latest_year]
            
            # Calculate Enterprise Value
            enterprise_value = latest_revenue * revenue_multiple
            
            # Get cash and debt
            cash = financial_data.get('cash', {}).get(latest_year, 0)
            debt = financial_data.get('debt', {}).get(latest_year, 0)
            
            # Calculate Equity Value
            equity_value = enterprise_value + cash - debt
            
            return {
                'enterprise_value': enterprise_value,
                'equity_value': equity_value,
                'revenue_used': latest_revenue,
                'revenue_multiple': revenue_multiple,
                'cash': cash,
                'debt': debt
            }
            
        except Exception as e:
            logger.error(f"Error calculating revenue multiple valuation: {e}")
            raise
