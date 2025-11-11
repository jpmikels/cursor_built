"""Rule-based validation engine."""
import logging
from typing import Dict, Any, List
from decimal import Decimal

logger = logging.getLogger(__name__)


class ValidationRules:
    """Rule-based financial statement validation."""
    
    def validate_income_statement(self, normalized_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Validate income statement data."""
        issues = []
        
        issues.extend(self._check_negative_revenue(normalized_data))
        issues.extend(self._check_extreme_margins(normalized_data))
        issues.extend(self._check_missing_items(normalized_data, 'income_statement'))
        
        return issues
    
    def validate_balance_sheet(self, normalized_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Validate balance sheet data."""
        issues = []
        
        issues.extend(self._check_balance_sheet_equation(normalized_data))
        issues.extend(self._check_negative_equity(normalized_data))
        issues.extend(self._check_negative_inventory(normalized_data))
        issues.extend(self._check_missing_items(normalized_data, 'balance_sheet'))
        
        return issues
    
    def validate_cash_flow(self, normalized_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Validate cash flow statement."""
        issues = []
        
        issues.extend(self._check_cash_reconciliation(normalized_data))
        issues.extend(self._check_missing_items(normalized_data, 'cash_flow'))
        
        return issues
    
    def _check_negative_revenue(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Check for negative revenue."""
        issues = []
        
        line_items = data.get('line_items', [])
        revenue_item = next((item for item in line_items if item['code'] == 'REV_001'), None)
        
        if revenue_item:
            for period, value in revenue_item['values'].items():
                if Decimal(str(value)) < 0:
                    issues.append({
                        'rule_code': 'NEG_REVENUE',
                        'severity': 'error',
                        'description': f'Negative revenue detected in {period}',
                        'affected_items': ['REV_001'],
                        'period': period,
                        'value': float(value)
                    })
        
        return issues
    
    def _check_extreme_margins(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Check for unrealistic profit margins."""
        issues = []
        
        line_items = {item['code']: item for item in data.get('line_items', [])}
        
        if 'REV_001' in line_items and 'GP_001' in line_items:
            revenue = line_items['REV_001']['values']
            gross_profit = line_items['GP_001']['values']
            
            for period in revenue.keys():
                rev_val = Decimal(str(revenue[period]))
                gp_val = Decimal(str(gross_profit[period]))
                
                if rev_val > 0:
                    margin = (gp_val / rev_val) * 100
                    
                    if margin > 95:
                        issues.append({
                            'rule_code': 'EXTREME_MARGIN_HIGH',
                            'severity': 'warning',
                            'description': f'Unusually high gross margin ({margin:.1f}%) in {period}',
                            'affected_items': ['REV_001', 'GP_001'],
                            'period': period,
                            'margin': float(margin)
                        })
                    elif margin < 0:
                        issues.append({
                            'rule_code': 'NEGATIVE_MARGIN',
                            'severity': 'warning',
                            'description': f'Negative gross margin ({margin:.1f}%) in {period}',
                            'affected_items': ['REV_001', 'GP_001'],
                            'period': period,
                            'margin': float(margin)
                        })
        
        return issues
    
    def _check_balance_sheet_equation(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Check if Assets = Liabilities + Equity."""
        issues = []
        
        reconciliation = data.get('reconciliation', [])
        
        for recon in reconciliation:
            if recon['rule'] == 'balance_sheet_equation':
                issues.append({
                    'rule_code': 'BS_IMBALANCE',
                    'severity': 'error',
                    'description': recon['description'],
                    'affected_items': ['ASSET_*', 'LIAB_*', 'EQUITY_*'],
                    'period': recon['period'],
                    'difference': recon['difference']
                })
        
        return issues
    
    def _check_negative_equity(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Check for negative equity."""
        issues = []
        
        calculations = data.get('calculations', {})
        total_equity = calculations.get('total_equity', {})
        
        for period, value in total_equity.items():
            if Decimal(str(value)) < 0:
                issues.append({
                    'rule_code': 'NEGATIVE_EQUITY',
                    'severity': 'warning',
                    'description': f'Negative equity in {period} (may indicate financial distress)',
                    'affected_items': ['EQUITY_*'],
                    'period': period,
                    'value': float(value)
                })
        
        return issues
    
    def _check_negative_inventory(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Check for negative inventory."""
        issues = []
        
        line_items = data.get('line_items', [])
        inventory_item = next((item for item in line_items if item['code'] == 'ASSET_CURR_004'), None)
        
        if inventory_item:
            for period, value in inventory_item['values'].items():
                if Decimal(str(value)) < 0:
                    issues.append({
                        'rule_code': 'NEGATIVE_INVENTORY',
                        'severity': 'error',
                        'description': f'Negative inventory in {period}',
                        'affected_items': ['ASSET_CURR_004'],
                        'period': period,
                        'value': float(value)
                    })
        
        return issues
    
    def _check_cash_reconciliation(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Check cash flow reconciliation."""
        issues = []
        
        # Would check if CFO + CFI + CFF = Change in Cash
        reconciliation = data.get('reconciliation', [])
        
        for recon in reconciliation:
            if 'cash' in recon.get('rule', '').lower():
                issues.append({
                    'rule_code': 'CF_RECON_FAIL',
                    'severity': 'error',
                    'description': recon['description'],
                    'affected_items': ['CF_*'],
                    'period': recon.get('period'),
                })
        
        return issues
    
    def _check_missing_items(self, data: Dict[str, Any], statement_type: str) -> List[Dict[str, Any]]:
        """Check for critical missing line items."""
        issues = []
        
        required_items = {
            'income_statement': ['REV_001', 'COGS_001', 'NI_001'],
            'balance_sheet': ['ASSET_CURR_001', 'LIAB_CURR_001', 'EQUITY_001'],
            'cash_flow': ['CF_OP_001', 'CF_INV_001', 'CF_FIN_001']
        }
        
        line_items = data.get('line_items', [])
        present_codes = {item['code'] for item in line_items}
        
        for required_code in required_items.get(statement_type, []):
            if required_code not in present_codes:
                issues.append({
                    'rule_code': 'MISSING_CRITICAL_ITEM',
                    'severity': 'error',
                    'description': f'Critical line item {required_code} is missing',
                    'affected_items': [required_code],
                })
        
        return issues

