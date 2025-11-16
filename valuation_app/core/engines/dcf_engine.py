"""
DCF (Discounted Cash Flow) Valuation Engine.
"""

import logging
from typing import Dict, Any, List
from decimal import Decimal

logger = logging.getLogger(__name__)


class DCFEngine:
    """
    Performs DCF valuation calculations.
    """
    
    def __init__(self):
        """Initialize the DCF engine."""
        pass
    
    def calculate_dcf(
        self,
        financial_data: Dict[str, Dict[int, float]],
        assumptions: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Calculate DCF valuation.
        
        Args:
            financial_data: Dict mapping metric_name -> {year: value}
            assumptions: Valuation assumptions dictionary
            
        Returns:
            DCF valuation results
        """
        logger.info("Calculating DCF valuation")
        
        try:
            # Extract assumptions
            wacc = float(assumptions['wacc'])
            terminal_growth_rate = float(assumptions['terminal_growth_rate'])
            forecast_years = int(assumptions.get('forecast_years', 5))
            mid_year_convention = assumptions.get('mid_year_convention', True)
            revenue_growth_rate = float(assumptions.get('revenue_growth_rate', 0.10))
            
            # Get historical financials
            revenue_history = financial_data.get('revenue', {})
            ebitda_history = financial_data.get('ebitda', {})
            depreciation_history = financial_data.get('depreciation', {})
            capex_history = financial_data.get('capex', {})
            
            # Get most recent year data
            if not revenue_history:
                raise ValueError("Revenue data is required for DCF calculation")
            
            latest_year = max(revenue_history.keys())
            latest_revenue = revenue_history[latest_year]
            
            # Calculate EBITDA margin (use historical average or latest)
            if ebitda_history:
                latest_ebitda = ebitda_history.get(latest_year, latest_revenue * 0.20)
                ebitda_margin = latest_ebitda / latest_revenue if latest_revenue > 0 else 0.20
            else:
                ebitda_margin = 0.20  # Default 20%
            
            # Calculate CapEx as % of revenue
            if capex_history:
                latest_capex = capex_history.get(latest_year, latest_revenue * 0.05)
                capex_rate = latest_capex / latest_revenue if latest_revenue > 0 else 0.05
            else:
                capex_rate = 0.05  # Default 5%
            
            # Calculate D&A as % of revenue
            if depreciation_history:
                latest_depreciation = depreciation_history.get(latest_year, latest_revenue * 0.03)
                da_rate = latest_depreciation / latest_revenue if latest_revenue > 0 else 0.03
            else:
                da_rate = 0.03  # Default 3%
            
            # Build forecast
            forecast_fcf = []
            forecast_details = []
            
            for year in range(1, forecast_years + 1):
                # Forecast revenue
                forecast_revenue = latest_revenue * ((1 + revenue_growth_rate) ** year)
                
                # Forecast EBITDA
                forecast_ebitda = forecast_revenue * ebitda_margin
                
                # Forecast D&A
                forecast_da = forecast_revenue * da_rate
                
                # EBIT = EBITDA - D&A
                forecast_ebit = forecast_ebitda - forecast_da
                
                # NOPAT = EBIT * (1 - Tax Rate)
                tax_rate = float(assumptions.get('tax_rate', 0.25))
                nopat = forecast_ebit * (1 - tax_rate)
                
                # FCF = NOPAT + D&A - CapEx - Change in WC
                forecast_capex = forecast_revenue * capex_rate
                change_in_wc = 0  # Simplified - assume no change
                
                fcf = nopat + forecast_da - forecast_capex - change_in_wc
                forecast_fcf.append(fcf)
                
                forecast_details.append({
                    'year': latest_year + year,
                    'revenue': forecast_revenue,
                    'ebitda': forecast_ebitda,
                    'ebit': forecast_ebit,
                    'nopat': nopat,
                    'depreciation': forecast_da,
                    'capex': forecast_capex,
                    'fcf': fcf
                })
            
            # Discount periods (adjust for mid-year convention)
            if mid_year_convention:
                periods = [i + 0.5 for i in range(1, forecast_years + 1)]
            else:
                periods = list(range(1, forecast_years + 1))
            
            # Discount factors
            discount_factors = [(1 + wacc) ** -p for p in periods]
            
            # Present value of forecast cash flows
            pv_fcf = [fcf * df for fcf, df in zip(forecast_fcf, discount_factors)]
            total_pv_fcf = sum(pv_fcf)
            
            # Calculate terminal value using Gordon Growth Model
            final_fcf = forecast_fcf[-1]
            
            if wacc <= terminal_growth_rate:
                logger.warning(f"WACC ({wacc}) <= terminal growth ({terminal_growth_rate}), adjusting")
                terminal_growth_rate = wacc * 0.8
            
            terminal_value = (final_fcf * (1 + terminal_growth_rate)) / (wacc - terminal_growth_rate)
            
            # Present value of terminal value
            tv_period = periods[-1]
            tv_discount_factor = (1 + wacc) ** -tv_period
            pv_terminal_value = terminal_value * tv_discount_factor
            
            # Enterprise Value
            enterprise_value = total_pv_fcf + pv_terminal_value
            
            # Equity Value = Enterprise Value + Cash - Debt
            cash = financial_data.get('cash', {}).get(latest_year, 0)
            debt = financial_data.get('debt', {}).get(latest_year, 0)
            equity_value = enterprise_value + cash - debt
            
            logger.info(f"DCF calculation complete: EV={enterprise_value:,.2f}, Equity={equity_value:,.2f}")
            
            return {
                'enterprise_value': enterprise_value,
                'equity_value': equity_value,
                'pv_forecast_fcf': total_pv_fcf,
                'pv_terminal_value': pv_terminal_value,
                'terminal_value': terminal_value,
                'wacc': wacc,
                'terminal_growth_rate': terminal_growth_rate,
                'forecast_years': forecast_years,
                'forecast_details': forecast_details,
                'discount_factors': discount_factors,
                'cash': cash,
                'debt': debt
            }
            
        except Exception as e:
            logger.error(f"Error calculating DCF: {e}")
            raise
    
    def sensitivity_analysis(
        self,
        financial_data: Dict[str, Dict[int, float]],
        base_assumptions: Dict[str, Any],
        wacc_range: List[float],
        growth_range: List[float]
    ) -> Dict[str, Any]:
        """
        Perform sensitivity analysis on WACC and terminal growth rate.
        
        Returns:
            Sensitivity table and analysis
        """
        logger.info("Performing DCF sensitivity analysis")
        
        sensitivity_table = []
        
        for wacc in wacc_range:
            row = []
            for growth in growth_range:
                if wacc <= growth:
                    row.append(None)  # Invalid combination
                else:
                    assumptions = base_assumptions.copy()
                    assumptions['wacc'] = wacc
                    assumptions['terminal_growth_rate'] = growth
                    
                    try:
                        result = self.calculate_dcf(financial_data, assumptions)
                        row.append(result['equity_value'])
                    except Exception as e:
                        logger.warning(f"Error in sensitivity calculation: {e}")
                        row.append(None)
            
            sensitivity_table.append(row)
        
        return {
            'wacc_range': wacc_range,
            'growth_range': growth_range,
            'sensitivity_table': sensitivity_table
        }
