"""Damodaran data provider (static fallback data)."""
import logging
from typing import List, Dict, Any
import pandas as pd
import os

from .base import MarketDataProvider

logger = logging.getLogger(__name__)


class DamodaranStaticProvider(MarketDataProvider):
    """
    Static data provider based on Aswath Damodaran's publicly available datasets.
    This serves as a fallback when other providers are unavailable.
    """
    
    def __init__(self):
        self.name = "Damodaran Static Data"
        
        # Industry betas (sample data)
        self.industry_betas = {
            'Software': 1.25,
            'Technology': 1.15,
            'Healthcare': 0.95,
            'Financial Services': 1.05,
            'Retail': 1.10,
            'Manufacturing': 0.90,
            'Energy': 0.85,
            'Real Estate': 0.75,
            'Utilities': 0.60,
            'Consumer Goods': 0.85,
        }
        
        # Typical industry margins (sample)
        self.industry_margins = {
            'Software': {'gross_margin': 0.75, 'ebitda_margin': 0.25, 'net_margin': 0.15},
            'Technology': {'gross_margin': 0.50, 'ebitda_margin': 0.20, 'net_margin': 0.12},
            'Healthcare': {'gross_margin': 0.60, 'ebitda_margin': 0.18, 'net_margin': 0.10},
            'Manufacturing': {'gross_margin': 0.35, 'ebitda_margin': 0.12, 'net_margin': 0.06},
            'Retail': {'gross_margin': 0.30, 'ebitda_margin': 0.08, 'net_margin': 0.03},
        }
    
    def get_comparable_companies(self, criteria: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Static provider doesn't have comparable company data.
        
        Returns empty list.
        """
        logger.info("Damodaran static provider does not have comparable company data")
        return []
    
    def get_comparable_transactions(self, criteria: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Static provider doesn't have transaction data.
        
        Returns empty list.
        """
        logger.info("Damodaran static provider does not have transaction data")
        return []
    
    def get_risk_free_rate(self, maturity: str = '10Y') -> float:
        """
        Return typical risk-free rate.
        
        Returns:
            4.5% for 10Y, 4.8% for 30Y
        """
        rates = {
            '10Y': 0.045,
            '30Y': 0.048,
        }
        return rates.get(maturity, 0.045)
    
    def get_equity_risk_premium(self, region: str = 'US') -> float:
        """
        Return typical equity risk premium by region.
        
        Based on Damodaran's historical averages.
        """
        erp_by_region = {
            'US': 0.06,
            'Developed Markets': 0.065,
            'Emerging Markets': 0.08,
        }
        return erp_by_region.get(region, 0.06)
    
    def get_industry_beta(self, industry_code: str) -> float:
        """
        Get industry beta from static lookup.
        
        Args:
            industry_code: Industry name or code
            
        Returns:
            Industry beta (unlevered)
        """
        # Try exact match first
        if industry_code in self.industry_betas:
            return self.industry_betas[industry_code]
        
        # Try fuzzy match
        industry_lower = industry_code.lower()
        for key, beta in self.industry_betas.items():
            if key.lower() in industry_lower or industry_lower in key.lower():
                return beta
        
        # Default to 1.0
        logger.warning(f"No beta found for {industry_code}, using default 1.0")
        return 1.0
    
    def get_industry_margins(self, industry: str) -> Dict[str, float]:
        """
        Get typical industry profit margins.
        
        Args:
            industry: Industry name
            
        Returns:
            Dictionary with margin benchmarks
        """
        return self.industry_margins.get(industry, {
            'gross_margin': 0.40,
            'ebitda_margin': 0.15,
            'net_margin': 0.08
        })

