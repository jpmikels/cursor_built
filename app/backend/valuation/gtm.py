"""GTM (Guideline Transaction Method) valuation."""
import logging
from typing import Dict, Any, List
from decimal import Decimal
import statistics

logger = logging.getLogger(__name__)


class GTMValuation:
    """Guideline Transaction Method (Market Approach) valuation."""
    
    def calculate_gtm(
        self,
        subject_metrics: Dict[str, float],
        comparable_transactions: List[Dict[str, Any]],
        multiples_to_use: List[str]
    ) -> Dict[str, Any]:
        """
        Calculate valuation using guideline transactions.
        
        Args:
            subject_metrics: Subject company financial metrics
            comparable_transactions: List of comparable transaction data
            multiples_to_use: List of multiple types (e.g., ['EV/Revenue', 'EV/EBITDA'])
            
        Returns:
            GTM valuation results
        """
        logger.info(f"Calculating GTM with {len(comparable_transactions)} transactions")
        
        if not comparable_transactions:
            return {'error': 'No comparable transactions provided'}
        
        # Calculate multiples for each transaction
        transaction_multiples = {}
        for multiple_type in multiples_to_use:
            transaction_multiples[multiple_type] = self._calculate_multiples(
                comparable_transactions, multiple_type
            )
        
        # Calculate subject company values using each multiple
        valuations_by_multiple = {}
        
        for multiple_type, multiples in transaction_multiples.items():
            if not multiples:
                logger.warning(f"No valid multiples for {multiple_type}")
                continue
            
            # Calculate statistics
            median_multiple = statistics.median(multiples)
            mean_multiple = statistics.mean(multiples)
            
            # Determine which metric to multiply
            subject_metric = self._get_subject_metric(subject_metrics, multiple_type)
            
            if subject_metric is None or subject_metric == 0:
                logger.warning(f"Subject metric not found or zero for {multiple_type}")
                continue
            
            # Calculate indicated values (no liquidity discount for transactions)
            indicated_value_median = Decimal(str(subject_metric)) * Decimal(str(median_multiple))
            indicated_value_mean = Decimal(str(subject_metric)) * Decimal(str(mean_multiple))
            
            valuations_by_multiple[multiple_type] = {
                'transaction_multiples': multiples,
                'median_multiple': median_multiple,
                'mean_multiple': mean_multiple,
                'subject_metric': subject_metric,
                'indicated_value_median': float(indicated_value_median),
                'indicated_value_mean': float(indicated_value_mean),
            }
        
        # Calculate weighted average (equal weight for simplicity)
        all_indicated_values = [
            v['indicated_value_median'] 
            for v in valuations_by_multiple.values()
        ]
        
        concluded_value = statistics.mean(all_indicated_values) if all_indicated_values else 0
        
        return {
            'concluded_value': concluded_value,
            'valuations_by_multiple': valuations_by_multiple,
            'comparable_transactions': [
                {
                    'target_name': txn.get('target_name'),
                    'acquirer_name': txn.get('acquirer_name'),
                    'date': txn.get('date'),
                    'metrics': txn.get('metrics', {})
                }
                for txn in comparable_transactions
            ],
            'methodology': 'gtm'
        }
    
    def _calculate_multiples(
        self,
        comparable_transactions: List[Dict[str, Any]],
        multiple_type: str
    ) -> List[float]:
        """Calculate a specific multiple for all transactions."""
        multiples = []
        
        for txn in comparable_transactions:
            metrics = txn.get('metrics', {})
            
            if multiple_type == 'EV/Revenue':
                ev = metrics.get('enterprise_value') or metrics.get('transaction_value')
                revenue = metrics.get('revenue') or metrics.get('ltm_revenue')
                if ev and revenue and revenue > 0:
                    multiples.append(ev / revenue)
            
            elif multiple_type == 'EV/EBITDA':
                ev = metrics.get('enterprise_value') or metrics.get('transaction_value')
                ebitda = metrics.get('ebitda') or metrics.get('ltm_ebitda')
                if ev and ebitda and ebitda > 0:
                    multiples.append(ev / ebitda)
            
            elif multiple_type == 'EV/Gross Profit':
                ev = metrics.get('enterprise_value') or metrics.get('transaction_value')
                gp = metrics.get('gross_profit')
                if ev and gp and gp > 0:
                    multiples.append(ev / gp)
        
        return multiples
    
    def _get_subject_metric(self, subject_metrics: Dict[str, float], multiple_type: str) -> float:
        """Get the appropriate subject company metric for a multiple."""
        
        if multiple_type == 'EV/Revenue':
            return subject_metrics.get('revenue')
        elif multiple_type == 'EV/EBITDA':
            return subject_metrics.get('ebitda')
        elif multiple_type == 'EV/Gross Profit':
            return subject_metrics.get('gross_profit')
        
        return None
    
    def filter_transactions(
        self,
        transactions: List[Dict[str, Any]],
        filters: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Filter transactions based on criteria.
        
        Args:
            transactions: List of all transactions
            filters: Filtering criteria
                - industry_codes: List of SIC/NAICS codes
                - min_size: Minimum transaction size
                - max_size: Maximum transaction size
                - min_date: Earliest transaction date
                - max_date: Latest transaction date
                
        Returns:
            Filtered list of transactions
        """
        filtered = transactions
        
        # Filter by industry
        if filters.get('industry_codes'):
            industry_codes = set(filters['industry_codes'])
            filtered = [
                txn for txn in filtered
                if txn.get('industry_code') in industry_codes
            ]
        
        # Filter by size
        if filters.get('min_size'):
            min_size = filters['min_size']
            filtered = [
                txn for txn in filtered
                if txn.get('metrics', {}).get('transaction_value', 0) >= min_size
            ]
        
        if filters.get('max_size'):
            max_size = filters['max_size']
            filtered = [
                txn for txn in filtered
                if txn.get('metrics', {}).get('transaction_value', float('inf')) <= max_size
            ]
        
        # Filter by date (would need datetime parsing)
        # Simplified for now
        
        logger.info(f"Filtered {len(transactions)} transactions to {len(filtered)}")
        
        return filtered

