"""Financial data normalization service."""
import logging
from typing import Dict, Any, List
import pandas as pd
from decimal import Decimal

logger = logging.getLogger(__name__)


class FinancialNormalizer:
    """Normalize financial data to canonical format with reconciliation."""
    
    def __init__(self, canonical_coa: pd.DataFrame):
        """
        Initialize normalizer with canonical COA.
        
        Args:
            canonical_coa: DataFrame with canonical chart of accounts
        """
        self.canonical_coa = canonical_coa
        self.coa_by_code = canonical_coa.set_index('code').to_dict('index')
    
    def normalize_income_statement(
        self,
        mapped_data: List[Dict[str, Any]],
        periods: List[str]
    ) -> Dict[str, Any]:
        """
        Normalize income statement data.
        
        Args:
            mapped_data: List of mapped line items with values
            periods: List of period labels (e.g., ['2021', '2022', '2023'])
            
        Returns:
            Normalized income statement with reconciliation
        """
        logger.info("Normalizing income statement")
        
        # Group by canonical codes
        grouped = {}
        for item in mapped_data:
            code = item.get('canonical_code')
            if code and code in self.coa_by_code:
                if code not in grouped:
                    grouped[code] = {
                        'code': code,
                        'label': self.coa_by_code[code]['label'],
                        'values': {period: Decimal('0') for period in periods}
                    }
                
                # Add values for each period
                for period in periods:
                    value = item.get('values', {}).get(period, 0)
                    grouped[code]['values'][period] += Decimal(str(value))
        
        # Build normalized structure
        normalized = {
            'periods': periods,
            'line_items': list(grouped.values()),
            'calculations': self._calculate_is_subtotals(grouped, periods),
            'reconciliation': self._reconcile_income_statement(grouped, periods)
        }
        
        return normalized
    
    def normalize_balance_sheet(
        self,
        mapped_data: List[Dict[str, Any]],
        periods: List[str]
    ) -> Dict[str, Any]:
        """Normalize balance sheet data."""
        logger.info("Normalizing balance sheet")
        
        # Group by canonical codes
        grouped = {}
        for item in mapped_data:
            code = item.get('canonical_code')
            if code and code in self.coa_by_code:
                if code not in grouped:
                    grouped[code] = {
                        'code': code,
                        'label': self.coa_by_code[code]['label'],
                        'values': {period: Decimal('0') for period in periods}
                    }
                
                for period in periods:
                    value = item.get('values', {}).get(period, 0)
                    grouped[code]['values'][period] += Decimal(str(value))
        
        normalized = {
            'periods': periods,
            'line_items': list(grouped.values()),
            'calculations': self._calculate_bs_subtotals(grouped, periods),
            'reconciliation': self._reconcile_balance_sheet(grouped, periods)
        }
        
        return normalized
    
    def normalize_cash_flow(
        self,
        mapped_data: List[Dict[str, Any]],
        periods: List[str]
    ) -> Dict[str, Any]:
        """Normalize cash flow statement."""
        logger.info("Normalizing cash flow statement")
        
        # Group by canonical codes
        grouped = {}
        for item in mapped_data:
            code = item.get('canonical_code')
            if code and code in self.coa_by_code:
                if code not in grouped:
                    grouped[code] = {
                        'code': code,
                        'label': self.coa_by_code[code]['label'],
                        'values': {period: Decimal('0') for period in periods}
                    }
                
                for period in periods:
                    value = item.get('values', {}).get(period, 0)
                    grouped[code]['values'][period] += Decimal(str(value))
        
        normalized = {
            'periods': periods,
            'line_items': list(grouped.values()),
            'calculations': self._calculate_cf_subtotals(grouped, periods),
            'reconciliation': self._reconcile_cash_flow(grouped, periods)
        }
        
        return normalized
    
    def _calculate_is_subtotals(self, grouped: Dict, periods: List[str]) -> Dict[str, Any]:
        """Calculate income statement subtotals."""
        calculations = {}
        
        # Gross Profit = Revenue - COGS
        revenue = self._get_value(grouped, 'REV_001', periods)
        cogs = self._get_value(grouped, 'COGS_001', periods)
        calculations['gross_profit'] = {period: revenue[period] - cogs[period] for period in periods}
        
        # Operating Income = Gross Profit - OpEx - D&A
        opex = self._get_value(grouped, 'OPEX_001', periods)
        calculations['operating_income'] = {
            period: calculations['gross_profit'][period] - opex[period]
            for period in periods
        }
        
        # Net Income (simplified)
        ebit = calculations['operating_income']
        interest = self._get_value(grouped, 'INT_002', periods)
        tax = self._get_value(grouped, 'TAX_001', periods)
        calculations['net_income'] = {
            period: ebit[period] - interest[period] - tax[period]
            for period in periods
        }
        
        return calculations
    
    def _calculate_bs_subtotals(self, grouped: Dict, periods: List[str]) -> Dict[str, Any]:
        """Calculate balance sheet subtotals."""
        calculations = {}
        
        # Total Current Assets
        cash = self._get_value(grouped, 'ASSET_CURR_001', periods)
        ar = self._get_value(grouped, 'ASSET_CURR_002', periods)
        inv = self._get_value(grouped, 'ASSET_CURR_004', periods)
        calculations['total_current_assets'] = {
            period: cash[period] + ar[period] + inv[period]
            for period in periods
        }
        
        # Total Assets (simplified)
        current_assets = calculations['total_current_assets']
        ppe_net = self._get_value(grouped, 'ASSET_FA_008', periods)
        calculations['total_assets'] = {
            period: current_assets[period] + ppe_net[period]
            for period in periods
        }
        
        # Total Current Liabilities
        ap = self._get_value(grouped, 'LIAB_CURR_001', periods)
        st_debt = self._get_value(grouped, 'LIAB_CURR_003', periods)
        calculations['total_current_liabilities'] = {
            period: ap[period] + st_debt[period]
            for period in periods
        }
        
        # Total Liabilities
        current_liab = calculations['total_current_liabilities']
        lt_debt = self._get_value(grouped, 'LIAB_LT_001', periods)
        calculations['total_liabilities'] = {
            period: current_liab[period] + lt_debt[period]
            for period in periods
        }
        
        # Total Equity
        common = self._get_value(grouped, 'EQUITY_001', periods)
        re = self._get_value(grouped, 'EQUITY_004', periods)
        calculations['total_equity'] = {
            period: common[period] + re[period]
            for period in periods
        }
        
        return calculations
    
    def _calculate_cf_subtotals(self, grouped: Dict, periods: List[str]) -> Dict[str, Any]:
        """Calculate cash flow subtotals."""
        calculations = {}
        
        # Operating Cash Flow
        calculations['cfo'] = self._get_value(grouped, 'CF_OP_001', periods)
        
        # Investing Cash Flow
        calculations['cfi'] = self._get_value(grouped, 'CF_INV_001', periods)
        
        # Financing Cash Flow
        calculations['cff'] = self._get_value(grouped, 'CF_FIN_001', periods)
        
        # Net Change in Cash
        calculations['net_change_cash'] = {
            period: (calculations['cfo'][period] + 
                    calculations['cfi'][period] + 
                    calculations['cff'][period])
            for period in periods
        }
        
        return calculations
    
    def _reconcile_income_statement(self, grouped: Dict, periods: List[str]) -> List[Dict[str, Any]]:
        """Perform reconciliation checks on income statement."""
        issues = []
        
        # Check if Revenue - COGS = Gross Profit
        revenue = self._get_value(grouped, 'REV_001', periods)
        cogs = self._get_value(grouped, 'COGS_001', periods)
        gp = self._get_value(grouped, 'GP_001', periods)
        
        for period in periods:
            calculated_gp = revenue[period] - cogs[period]
            if gp[period] != 0 and abs(calculated_gp - gp[period]) > Decimal('0.01'):
                issues.append({
                    'period': period,
                    'rule': 'gross_profit_calculation',
                    'description': f'Gross Profit mismatch in {period}',
                    'expected': float(calculated_gp),
                    'actual': float(gp[period]),
                    'difference': float(calculated_gp - gp[period])
                })
        
        return issues
    
    def _reconcile_balance_sheet(self, grouped: Dict, periods: List[str]) -> List[Dict[str, Any]]:
        """Perform reconciliation checks on balance sheet."""
        issues = []
        
        # Check if Assets = Liabilities + Equity
        for period in periods:
            total_assets = Decimal('0')
            total_liab = Decimal('0')
            total_equity = Decimal('0')
            
            # Sum assets
            for code, item in grouped.items():
                if code.startswith('ASSET_'):
                    total_assets += item['values'][period]
            
            # Sum liabilities
            for code, item in grouped.items():
                if code.startswith('LIAB_'):
                    total_liab += item['values'][period]
            
            # Sum equity
            for code, item in grouped.items():
                if code.startswith('EQUITY_'):
                    total_equity += item['values'][period]
            
            difference = total_assets - (total_liab + total_equity)
            
            if abs(difference) > Decimal('0.01'):
                issues.append({
                    'period': period,
                    'rule': 'balance_sheet_equation',
                    'description': f'Balance sheet out of balance in {period}',
                    'total_assets': float(total_assets),
                    'total_liabilities': float(total_liab),
                    'total_equity': float(total_equity),
                    'difference': float(difference)
                })
        
        return issues
    
    def _reconcile_cash_flow(self, grouped: Dict, periods: List[str]) -> List[Dict[str, Any]]:
        """Perform reconciliation checks on cash flow."""
        issues = []
        
        # Check if Net Change in Cash = Ending Cash - Beginning Cash
        # (Simplified - would need balance sheet data for complete check)
        
        return issues
    
    def _get_value(self, grouped: Dict, code: str, periods: List[str]) -> Dict[str, Decimal]:
        """Helper to get values for a specific code."""
        if code in grouped:
            return grouped[code]['values']
        return {period: Decimal('0') for period in periods}

