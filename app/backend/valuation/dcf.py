"""DCF (Discounted Cash Flow) valuation."""
import logging
from typing import Dict, Any, List
from decimal import Decimal
import numpy as np

logger = logging.getLogger(__name__)


class DCFValuation:
    """Perform DCF valuation."""
    
    def calculate_dcf(
        self,
        historical_financials: Dict[str, Any],
        forecast: Dict[str, Any],
        wacc: float,
        terminal_growth_rate: float = None,
        exit_multiple: float = None,
        mid_year_convention: bool = True
    ) -> Dict[str, Any]:
        """
        Calculate DCF valuation.
        
        Args:
            historical_financials: Historical financial data
            forecast: Forecasted cash flows
            wacc: Weighted average cost of capital
            terminal_growth_rate: Perpetuity growth rate (if using Gordon Growth)
            exit_multiple: Exit EV/EBITDA multiple (if using exit multiple method)
            mid_year_convention: Whether to use mid-year discounting
            
        Returns:
            DCF valuation results
        """
        logger.info("Calculating DCF valuation")
        
        # Extract forecast cash flows
        forecast_fcf = forecast.get('free_cash_flow', [])
        forecast_years = len(forecast_fcf)
        
        if not forecast_fcf:
            logger.error("No forecasted free cash flows provided")
            return {'error': 'No forecast data'}
        
        # Discount periods (adjust for mid-year convention)
        if mid_year_convention:
            periods = [i + 0.5 for i in range(1, forecast_years + 1)]
        else:
            periods = list(range(1, forecast_years + 1))
        
        # Discount factors
        discount_factors = [(1 + wacc) ** -p for p in periods]
        
        # Present value of forecast cash flows
        pv_fcf = [Decimal(str(fcf)) * Decimal(str(df)) for fcf, df in zip(forecast_fcf, discount_factors)]
        total_pv_fcf = sum(pv_fcf)
        
        # Calculate terminal value
        if exit_multiple is not None:
            # Exit Multiple Method
            terminal_ebitda = forecast.get('terminal_ebitda', forecast_fcf[-1] * 1.5)  # Rough proxy
            terminal_value = Decimal(str(terminal_ebitda)) * Decimal(str(exit_multiple))
            tv_method = 'exit_multiple'
        elif terminal_growth_rate is not None:
            # Gordon Growth Model
            # TV = FCF_final * (1 + g) / (WACC - g)
            final_fcf = Decimal(str(forecast_fcf[-1]))
            g = Decimal(str(terminal_growth_rate))
            w = Decimal(str(wacc))
            
            if w <= g:
                logger.warning(f"WACC ({w}) <= terminal growth ({g}), adjusting growth rate")
                g = w * Decimal('0.8')  # Set g to 80% of WACC
            
            terminal_value = (final_fcf * (Decimal('1') + g)) / (w - g)
            tv_method = 'gordon_growth'
        else:
            logger.error("Must provide either terminal_growth_rate or exit_multiple")
            return {'error': 'Missing terminal value method'}
        
        # Present value of terminal value
        tv_period = periods[-1]
        tv_discount_factor = Decimal(str((1 + wacc) ** -tv_period))
        pv_terminal_value = terminal_value * tv_discount_factor
        
        # Enterprise Value = PV of forecast FCF + PV of Terminal Value
        enterprise_value = total_pv_fcf + pv_terminal_value
        
        # Equity Value = Enterprise Value + Cash - Debt
        cash = Decimal(str(historical_financials.get('cash', 0)))
        debt = Decimal(str(historical_financials.get('total_debt', 0)))
        equity_value = enterprise_value + cash - debt
        
        return {
            'enterprise_value': float(enterprise_value),
            'equity_value': float(equity_value),
            'pv_forecast_fcf': float(total_pv_fcf),
            'pv_terminal_value': float(pv_terminal_value),
            'terminal_value': float(terminal_value),
            'terminal_value_method': tv_method,
            'wacc': wacc,
            'terminal_growth_rate': terminal_growth_rate if terminal_growth_rate else None,
            'exit_multiple': exit_multiple if exit_multiple else None,
            'forecast_years': forecast_years,
            'mid_year_convention': mid_year_convention,
            'detail': {
                'forecast_fcf': [float(f) for f in forecast_fcf],
                'discount_factors': discount_factors,
                'pv_fcf': [float(p) for p in pv_fcf],
                'cash': float(cash),
                'debt': float(debt)
            }
        }
    
    def calculate_free_cash_flow(
        self,
        ebit: float,
        tax_rate: float,
        depreciation: float,
        capex: float,
        change_in_wc: float
    ) -> float:
        """
        Calculate Unlevered Free Cash Flow.
        
        FCF = EBIT * (1 - Tax Rate) + D&A - CapEx - Change in WC
        
        Args:
            ebit: Earnings Before Interest and Taxes
            tax_rate: Tax rate
            depreciation: Depreciation & Amortization
            capex: Capital Expenditures
            change_in_wc: Change in Working Capital
            
        Returns:
            Free Cash Flow
        """
        nopat = ebit * (1 - tax_rate)
        fcf = nopat + depreciation - capex - change_in_wc
        return fcf
    
    def sensitivity_analysis(
        self,
        base_fcf: List[float],
        base_wacc: float,
        base_growth: float,
        wacc_range: List[float],
        growth_range: List[float],
        historical_financials: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Perform sensitivity analysis on WACC and terminal growth rate.
        
        Args:
            base_fcf: Base case free cash flows
            base_wacc: Base case WACC
            base_growth: Base case terminal growth rate
            wacc_range: Range of WACC values to test
            growth_range: Range of growth rates to test
            historical_financials: Historical financial data
            
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
                    result = self.calculate_dcf(
                        historical_financials=historical_financials,
                        forecast={'free_cash_flow': base_fcf},
                        wacc=wacc,
                        terminal_growth_rate=growth,
                        mid_year_convention=True
                    )
                    row.append(result.get('equity_value'))
            sensitivity_table.append(row)
        
        return {
            'wacc_range': wacc_range,
            'growth_range': growth_range,
            'sensitivity_table': sensitivity_table,
            'base_case': {
                'wacc': base_wacc,
                'growth': base_growth
            }
        }

