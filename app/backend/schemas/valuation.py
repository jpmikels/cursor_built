"""Valuation-related schemas."""
from datetime import datetime
from typing import Optional, Any
from pydantic import BaseModel, Field
from decimal import Decimal


class WACCInputs(BaseModel):
    """WACC calculation inputs."""
    risk_free_rate: float = Field(..., ge=0, le=1, description="Risk-free rate (e.g., 0.045 for 4.5%)")
    equity_risk_premium: float = Field(..., ge=0, le=1, description="Equity risk premium")
    beta: float = Field(..., gt=0, description="Beta coefficient")
    size_premium: float = Field(0, ge=0, le=1, description="Size premium")
    company_specific_premium: float = Field(0, ge=0, le=1, description="Company-specific risk premium")
    cost_of_debt: float = Field(..., ge=0, le=1, description="Pre-tax cost of debt")
    tax_rate: float = Field(..., ge=0, le=1, description="Effective tax rate")
    debt_weight: float = Field(..., ge=0, le=1, description="Debt % of capital structure")
    equity_weight: float = Field(..., ge=0, le=1, description="Equity % of capital structure")


class DCFInputs(BaseModel):
    """DCF method inputs."""
    forecast_years: int = Field(5, ge=3, le=10, description="Number of forecast years")
    terminal_growth_rate: float = Field(..., ge=0, le=0.1, description="Terminal growth rate")
    use_exit_multiple: bool = Field(False, description="Use exit multiple instead of Gordon growth")
    exit_multiple: Optional[float] = Field(None, ge=0, description="Exit EV/EBITDA multiple")
    mid_year_convention: bool = Field(True, description="Use mid-year discounting")


class GPCMInputs(BaseModel):
    """Guideline Public Company inputs."""
    comparable_tickers: list[str] = Field(..., min_length=1, description="Public company ticker symbols")
    multiples: list[str] = Field(
        ["EV/Revenue", "EV/EBITDA", "P/E"],
        description="Multiples to calculate"
    )
    liquidity_discount: float = Field(0.25, ge=0, le=0.5, description="Liquidity discount")


class GTMInputs(BaseModel):
    """Guideline Transaction inputs."""
    industry_filter: Optional[list[str]] = Field(None, description="SIC/NAICS codes")
    min_transaction_size: Optional[float] = Field(None, ge=0, description="Minimum transaction size")
    max_transaction_size: Optional[float] = Field(None, ge=0, description="Maximum transaction size")
    date_range_months: int = Field(36, ge=12, le=60, description="Lookback period in months")
    multiples: list[str] = Field(
        ["EV/Revenue", "EV/EBITDA"],
        description="Multiples to calculate"
    )


class ValuationRunRequest(BaseModel):
    """Request to run valuation."""
    run_name: Optional[str] = None
    valuation_date: datetime
    wacc_inputs: WACCInputs
    methods: dict[str, Any] = Field(
        ...,
        description="Method configurations: 'dcf', 'gpcm', 'gtm'"
    )
    method_weights: dict[str, float] = Field(
        {"dcf": 0.5, "gpcm": 0.3, "gtm": 0.2},
        description="Weight for each method in final conclusion"
    )


class ValuationRunResponse(BaseModel):
    """Valuation run response."""
    id: int
    engagement_id: int
    run_number: int
    run_name: Optional[str]
    valuation_date: datetime
    methods_config: dict[str, Any]
    assumptions: dict[str, Any]
    dcf_value: Optional[Decimal]
    gpcm_value: Optional[Decimal]
    gtm_value: Optional[Decimal]
    concluded_value: Optional[Decimal]
    status: str
    created_by: Optional[int]
    created_at: datetime
    completed_at: Optional[datetime]
    
    class Config:
        from_attributes = True


class ValuationResultDetail(BaseModel):
    """Detailed valuation results."""
    run: ValuationRunResponse
    dcf_details: Optional[dict[str, Any]] = None
    gpcm_details: Optional[dict[str, Any]] = None
    gtm_details: Optional[dict[str, Any]] = None
    reconciliation: dict[str, Any]

