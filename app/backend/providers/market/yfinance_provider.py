"""Yahoo Finance provider for public market data."""
import logging
from typing import List, Dict, Any
import yfinance as yf
from datetime import datetime, timedelta

from .base import MarketDataProvider

logger = logging.getLogger(__name__)


class YFinanceProvider(MarketDataProvider):
    """Yahoo Finance data provider (free, public market data)."""
    
    def __init__(self):
        self.name = "Yahoo Finance"
    
    def get_comparable_companies(self, criteria: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Get comparable public companies from Yahoo Finance.
        
        Args:
            criteria: Must include 'tickers' list
            
        Returns:
            List of companies with financial metrics
        """
        tickers = criteria.get('tickers', [])
        
        if not tickers:
            logger.warning("No tickers provided for yfinance lookup")
            return []
        
        companies = []
        
        for ticker_symbol in tickers:
            try:
                ticker = yf.Ticker(ticker_symbol)
                info = ticker.info
                
                # Get financial data
                company = {
                    'name': info.get('longName', ticker_symbol),
                    'ticker': ticker_symbol,
                    'metrics': {
                        'market_cap': info.get('marketCap'),
                        'enterprise_value': info.get('enterpriseValue'),
                        'revenue': info.get('totalRevenue'),
                        'ebitda': info.get('ebitda'),
                        'net_income': info.get('netIncomeToCommon'),
                        'book_value': info.get('bookValue', 0) * info.get('sharesOutstanding', 0),
                        'beta': info.get('beta'),
                        'pe_ratio': info.get('trailingPE'),
                    },
                    'industry': info.get('industry'),
                    'sector': info.get('sector'),
                }
                
                companies.append(company)
                
            except Exception as e:
                logger.warning(f"Error fetching data for {ticker_symbol}: {str(e)}")
        
        return companies
    
    def get_comparable_transactions(self, criteria: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Yahoo Finance doesn't provide M&A transaction data.
        
        Returns empty list - use dedicated M&A data providers.
        """
        logger.info("Yahoo Finance does not provide M&A transaction data")
        return []
    
    def get_risk_free_rate(self, maturity: str = '10Y') -> float:
        """
        Get US Treasury yield from Yahoo Finance.
        
        Args:
            maturity: '10Y' or '30Y'
            
        Returns:
            Yield as decimal
        """
        try:
            # US Treasury ticker symbols
            ticker_map = {
                '10Y': '^TNX',  # 10-Year Treasury
                '30Y': '^TYX',  # 30-Year Treasury
            }
            
            ticker_symbol = ticker_map.get(maturity, '^TNX')
            ticker = yf.Ticker(ticker_symbol)
            
            # Get latest price (yield is in percentage, convert to decimal)
            hist = ticker.history(period='1d')
            if not hist.empty:
                latest_yield = hist['Close'].iloc[-1] / 100  # Convert to decimal
                return latest_yield
            
            # Fallback to default
            logger.warning(f"Could not fetch {maturity} Treasury yield, using default")
            return 0.045  # 4.5% default
            
        except Exception as e:
            logger.error(f"Error fetching risk-free rate: {str(e)}")
            return 0.045  # 4.5% default
    
    def get_equity_risk_premium(self, region: str = 'US') -> float:
        """
        Get equity risk premium (not directly available from yfinance).
        
        Returns typical US ERP of 6%.
        """
        # ERP is typically estimated, not directly observable
        # Use Damodaran's typical US ERP
        erp_by_region = {
            'US': 0.06,
            'EU': 0.065,
            'Asia': 0.07,
        }
        
        return erp_by_region.get(region, 0.06)
    
    def get_industry_beta(self, industry_code: str) -> float:
        """
        Get industry beta (not directly available from yfinance).
        
        Returns default of 1.0.
        """
        # Would need to calculate from industry constituents
        logger.info("Industry beta calculation not implemented for yfinance")
        return 1.0

