"""WACC (Weighted Average Cost of Capital) calculator."""
import logging
from typing import Dict, Any
from decimal import Decimal

logger = logging.getLogger(__name__)


class WACCCalculator:
    """Calculate Weighted Average Cost of Capital."""
    
    def calculate_wacc(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculate WACC from inputs.
        
        Args:
            inputs: Dictionary with keys:
                - risk_free_rate: float
                - equity_risk_premium: float
                - beta: float
                - size_premium: float (optional)
                - company_specific_premium: float (optional)
                - cost_of_debt: float
                - tax_rate: float
                - debt_weight: float (% of capital structure)
                - equity_weight: float (% of capital structure)
                
        Returns:
            Dictionary with WACC calculation details
        """
        logger.info("Calculating WACC")
        
        # Extract inputs
        rf = Decimal(str(inputs['risk_free_rate']))
        erp = Decimal(str(inputs['equity_risk_premium']))
        beta = Decimal(str(inputs['beta']))
        size_prem = Decimal(str(inputs.get('size_premium', 0)))
        co_specific = Decimal(str(inputs.get('company_specific_premium', 0)))
        kd = Decimal(str(inputs['cost_of_debt']))
        tax = Decimal(str(inputs['tax_rate']))
        wd = Decimal(str(inputs['debt_weight']))
        we = Decimal(str(inputs['equity_weight']))
        
        # Validate weights sum to 1
        if abs(wd + we - Decimal('1.0')) > Decimal('0.01'):
            logger.warning(f"Debt and equity weights don't sum to 1.0: {wd + we}")
        
        # Calculate Cost of Equity using CAPM + adjustments
        # Ke = Rf + Beta * ERP + Size Premium + Company-Specific Risk
        cost_of_equity = rf + (beta * erp) + size_prem + co_specific
        
        # Calculate After-tax Cost of Debt
        # Kd(1-T)
        after_tax_cost_of_debt = kd * (Decimal('1') - tax)
        
        # Calculate WACC
        # WACC = (We * Ke) + (Wd * Kd * (1-T))
        wacc = (we * cost_of_equity) + (wd * after_tax_cost_of_debt)
        
        return {
            'cost_of_equity': float(cost_of_equity),
            'cost_of_equity_components': {
                'risk_free_rate': float(rf),
                'beta_times_erp': float(beta * erp),
                'size_premium': float(size_prem),
                'company_specific_premium': float(co_specific)
            },
            'after_tax_cost_of_debt': float(after_tax_cost_of_debt),
            'wacc': float(wacc),
            'capital_structure': {
                'equity_weight': float(we),
                'debt_weight': float(wd)
            }
        }
    
    def calculate_levered_beta(
        self,
        unlevered_beta: float,
        debt_to_equity: float,
        tax_rate: float
    ) -> float:
        """
        Calculate levered beta from unlevered beta.
        
        Formula: βL = βU * (1 + (1 - T) * D/E)
        
        Args:
            unlevered_beta: Unlevered (asset) beta
            debt_to_equity: D/E ratio
            tax_rate: Corporate tax rate
            
        Returns:
            Levered (equity) beta
        """
        bu = Decimal(str(unlevered_beta))
        de = Decimal(str(debt_to_equity))
        t = Decimal(str(tax_rate))
        
        levered_beta = bu * (Decimal('1') + (Decimal('1') - t) * de)
        
        return float(levered_beta)
    
    def calculate_unlevered_beta(
        self,
        levered_beta: float,
        debt_to_equity: float,
        tax_rate: float
    ) -> float:
        """
        Calculate unlevered beta from levered beta.
        
        Formula: βU = βL / (1 + (1 - T) * D/E)
        
        Args:
            levered_beta: Levered (equity) beta
            debt_to_equity: D/E ratio
            tax_rate: Corporate tax rate
            
        Returns:
            Unlevered (asset) beta
        """
        bl = Decimal(str(levered_beta))
        de = Decimal(str(debt_to_equity))
        t = Decimal(str(tax_rate))
        
        unlevered_beta = bl / (Decimal('1') + (Decimal('1') - t) * de)
        
        return float(unlevered_beta)

