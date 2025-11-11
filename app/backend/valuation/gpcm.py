"""GPCM (Guideline Public Company Method) valuation."""
import logging
from typing import Dict, Any, List
from decimal import Decimal
import statistics

logger = logging.getLogger(__name__)


class GPCMValuation:
    """Guideline Public Company Method valuation."""
    
    def calculate_gpcm(
        self,
        subject_metrics: Dict[str, float],
        comparable_companies: List[Dict[str, Any]],
        multiples_to_use: List[str],
        liquidity_discount: float = 0.25
    ) -> Dict[str, Any]:
        """
        Calculate valuation using guideline public companies.
        
        Args:
            subject_metrics: Subject company financial metrics
            comparable_companies: List of comparable public company data
            multiples_to_use: List of multiple types (e.g., ['EV/Revenue', 'EV/EBITDA'])
            liquidity_discount: Discount for lack of marketability (default 25%)
            
        Returns:
            GPCM valuation results
        """
        logger.info(f"Calculating GPCM with {len(comparable_companies)} comparables")
        
        if not comparable_companies:
            return {'error': 'No comparable companies provided'}
        
        # Calculate multiples for each comp
        comp_multiples = {}
        for multiple_type in multiples_to_use:
            comp_multiples[multiple_type] = self._calculate_multiples(
                comparable_companies, multiple_type
            )
        
        # Calculate subject company values using each multiple
        valuations_by_multiple = {}
        
        for multiple_type, multiples in comp_multiples.items():
            # Calculate statistics
            median_multiple = statistics.median(multiples)
            mean_multiple = statistics.mean(multiples)
            
            # Determine which metric to multiply
            subject_metric = self._get_subject_metric(subject_metrics, multiple_type)
            
            if subject_metric is None:
                logger.warning(f"Subject metric not found for {multiple_type}")
                continue
            
            # Calculate indicated values
            indicated_value_median = Decimal(str(subject_metric)) * Decimal(str(median_multiple))
            indicated_value_mean = Decimal(str(subject_metric)) * Decimal(str(mean_multiple))
            
            # Apply liquidity discount
            discount_factor = Decimal('1') - Decimal(str(liquidity_discount))
            adjusted_value_median = indicated_value_median * discount_factor
            adjusted_value_mean = indicated_value_mean * discount_factor
            
            valuations_by_multiple[multiple_type] = {
                'comparable_multiples': multiples,
                'median_multiple': median_multiple,
                'mean_multiple': mean_multiple,
                'subject_metric': subject_metric,
                'indicated_value_median': float(indicated_value_median),
                'indicated_value_mean': float(indicated_value_mean),
                'adjusted_value_median': float(adjusted_value_median),
                'adjusted_value_mean': float(adjusted_value_mean),
                'liquidity_discount': liquidity_discount
            }
        
        # Calculate weighted average (equal weight for simplicity)
        all_adjusted_values = [
            v['adjusted_value_median'] 
            for v in valuations_by_multiple.values()
        ]
        
        concluded_value = statistics.mean(all_adjusted_values) if all_adjusted_values else 0
        
        return {
            'concluded_value': concluded_value,
            'valuations_by_multiple': valuations_by_multiple,
            'comparable_companies': [
                {
                    'name': comp.get('name'),
                    'ticker': comp.get('ticker'),
                    'metrics': comp.get('metrics', {})
                }
                for comp in comparable_companies
            ],
            'liquidity_discount': liquidity_discount,
            'methodology': 'gpcm'
        }
    
    def _calculate_multiples(
        self,
        comparable_companies: List[Dict[str, Any]],
        multiple_type: str
    ) -> List[float]:
        """Calculate a specific multiple for all comparables."""
        multiples = []
        
        for comp in comparable_companies:
            metrics = comp.get('metrics', {})
            
            if multiple_type == 'EV/Revenue':
                ev = metrics.get('enterprise_value')
                revenue = metrics.get('revenue')
                if ev and revenue and revenue > 0:
                    multiples.append(ev / revenue)
            
            elif multiple_type == 'EV/EBITDA':
                ev = metrics.get('enterprise_value')
                ebitda = metrics.get('ebitda')
                if ev and ebitda and ebitda > 0:
                    multiples.append(ev / ebitda)
            
            elif multiple_type == 'P/E':
                market_cap = metrics.get('market_cap')
                net_income = metrics.get('net_income')
                if market_cap and net_income and net_income > 0:
                    multiples.append(market_cap / net_income)
            
            elif multiple_type == 'P/B':
                market_cap = metrics.get('market_cap')
                book_value = metrics.get('book_value')
                if market_cap and book_value and book_value > 0:
                    multiples.append(market_cap / book_value)
        
        return multiples
    
    def _get_subject_metric(self, subject_metrics: Dict[str, float], multiple_type: str) -> float:
        """Get the appropriate subject company metric for a multiple."""
        
        if multiple_type == 'EV/Revenue':
            return subject_metrics.get('revenue')
        elif multiple_type == 'EV/EBITDA':
            return subject_metrics.get('ebitda')
        elif multiple_type == 'P/E':
            return subject_metrics.get('net_income')
        elif multiple_type == 'P/B':
            return subject_metrics.get('book_value')
        
        return None
    
    def adjust_for_differences(
        self,
        base_value: float,
        adjustments: Dict[str, float]
    ) -> Dict[str, Any]:
        """
        Apply adjustments for differences between subject and comparables.
        
        Args:
            base_value: Base valuation before adjustments
            adjustments: Dictionary of adjustment factors
                e.g., {'size': -0.10, 'growth': 0.05, 'profitability': 0.03}
                
        Returns:
            Adjusted valuation
        """
        adjusted_value = Decimal(str(base_value))
        adjustment_detail = []
        
        for factor, adjustment_pct in adjustments.items():
            adjustment_amount = adjusted_value * Decimal(str(adjustment_pct))
            adjusted_value += adjustment_amount
            
            adjustment_detail.append({
                'factor': factor,
                'percentage': adjustment_pct,
                'amount': float(adjustment_amount)
            })
        
        return {
            'base_value': base_value,
            'adjustments': adjustment_detail,
            'adjusted_value': float(adjusted_value)
        }

