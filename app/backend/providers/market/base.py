"""Base class for market data providers."""
from abc import ABC, abstractmethod
from typing import List, Dict, Any


class MarketDataProvider(ABC):
    """Base class for all market data providers."""
    
    @abstractmethod
    def get_comparable_companies(self, criteria: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Get list of comparable public companies.
        
        Args:
            criteria: Search criteria (industry, size, etc.)
            
        Returns:
            List of comparable companies with financial metrics
        """
        pass
    
    @abstractmethod
    def get_comparable_transactions(self, criteria: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Get list of comparable M&A transactions.
        
        Args:
            criteria: Search criteria (industry, size, date range, etc.)
            
        Returns:
            List of comparable transactions with deal metrics
        """
        pass
    
    @abstractmethod
    def get_risk_free_rate(self, maturity: str = '10Y') -> float:
        """
        Get risk-free rate (e.g., US Treasury yield).
        
        Args:
            maturity: Maturity period (e.g., '10Y', '30Y')
            
        Returns:
            Risk-free rate as decimal
        """
        pass
    
    @abstractmethod
    def get_equity_risk_premium(self, region: str = 'US') -> float:
        """
        Get equity risk premium for a region.
        
        Args:
            region: Geographic region
            
        Returns:
            Equity risk premium as decimal
        """
        pass
    
    @abstractmethod
    def get_industry_beta(self, industry_code: str) -> float:
        """
        Get median beta for an industry.
        
        Args:
            industry_code: Industry classification code
            
        Returns:
            Industry beta
        """
        pass

