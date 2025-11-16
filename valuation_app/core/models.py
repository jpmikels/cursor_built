"""
Core database models for Business Valuation application.
"""

from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from decimal import Decimal


class ProjectStatus(models.TextChoices):
    """Project workflow status choices."""
    NEW = 'NEW', 'New'
    PROCESSING = 'PROCESSING', 'Processing File'
    MAPPING = 'MAPPING', 'Needs Mapping'
    READY = 'READY', 'Ready for Assumptions'
    CALCULATING = 'CALCULATING', 'Calculating Valuation'
    COMPLETE = 'COMPLETE', 'Complete'
    ERROR = 'ERROR', 'Error'


class Project(models.Model):
    """
    Main project/engagement model representing a valuation engagement.
    """
    name = models.CharField(max_length=255, help_text="Project name")
    description = models.TextField(blank=True, help_text="Project description")
    client_name = models.CharField(max_length=255, blank=True, help_text="Client company name")
    
    # Status tracking
    status = models.CharField(
        max_length=20,
        choices=ProjectStatus.choices,
        default=ProjectStatus.NEW,
        help_text="Current project status"
    )
    
    # File information
    uploaded_file = models.FileField(
        upload_to='uploads/%Y/%m/%d/',
        blank=True,
        null=True,
        help_text="Uploaded financial data file"
    )
    original_filename = models.CharField(max_length=255, blank=True)
    
    # Metadata
    fiscal_year_end = models.CharField(max_length=10, blank=True, help_text="e.g., 12-31")
    currency = models.CharField(max_length=3, default='USD', help_text="Currency code")
    industry_code = models.CharField(max_length=50, blank=True, help_text="SIC/NAICS code")
    
    # Ownership
    created_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='projects',
        help_text="User who created this project"
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Error tracking
    error_message = models.TextField(blank=True, help_text="Error details if status is ERROR")
    
    # Report file path
    excel_report_path = models.FileField(
        upload_to='reports/%Y/%m/%d/',
        blank=True,
        null=True,
        help_text="Generated Excel report"
    )
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', 'created_at']),
            models.Index(fields=['created_by', 'created_at']),
        ]
    
    def __str__(self):
        return f"{self.name} ({self.get_status_display()})"
    
    def get_absolute_url(self):
        from django.urls import reverse
        return reverse('project_detail', kwargs={'project_id': self.pk})


class FinancialData(models.Model):
    """
    Stores clean, standardized annual financial data.
    Each row represents one metric for one year.
    """
    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name='financial_data',
        help_text="Associated project"
    )
    
    # Data identification
    metric_name = models.CharField(
        max_length=255,
        help_text="Standardized metric name (e.g., 'Revenue', 'EBITDA')"
    )
    year = models.IntegerField(help_text="Fiscal year")
    value = models.DecimalField(
        max_digits=20,
        decimal_places=2,
        help_text="Metric value"
    )
    
    # Optional metadata
    source_sheet = models.CharField(max_length=100, blank=True, help_text="Source sheet name")
    source_row = models.IntegerField(blank=True, null=True, help_text="Source row number")
    is_derived = models.BooleanField(default=False, help_text="Whether this is a calculated field")
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['project', 'metric_name', 'year']
        unique_together = [['project', 'metric_name', 'year']]
        indexes = [
            models.Index(fields=['project', 'metric_name']),
            models.Index(fields=['project', 'year']),
        ]
    
    def __str__(self):
        return f"{self.metric_name} ({self.year}): {self.value}"


class ValuationAssumptions(models.Model):
    """
    Stores user-defined valuation assumptions and inputs.
    """
    project = models.OneToOneField(
        Project,
        on_delete=models.CASCADE,
        related_name='assumptions',
        help_text="Associated project"
    )
    
    # WACC Components
    risk_free_rate = models.DecimalField(
        max_digits=5,
        decimal_places=4,
        default=Decimal('0.0450'),
        help_text="Risk-free rate (e.g., 0.0450 for 4.5%)"
    )
    equity_risk_premium = models.DecimalField(
        max_digits=5,
        decimal_places=4,
        default=Decimal('0.0600'),
        help_text="Equity risk premium"
    )
    beta = models.DecimalField(
        max_digits=4,
        decimal_places=2,
        default=Decimal('1.00'),
        help_text="Company beta"
    )
    size_premium = models.DecimalField(
        max_digits=5,
        decimal_places=4,
        default=Decimal('0.0000'),
        help_text="Size premium for small companies"
    )
    company_specific_premium = models.DecimalField(
        max_digits=5,
        decimal_places=4,
        default=Decimal('0.0000'),
        help_text="Company-specific risk premium"
    )
    
    # Debt Components
    cost_of_debt = models.DecimalField(
        max_digits=5,
        decimal_places=4,
        default=Decimal('0.0600'),
        help_text="Pre-tax cost of debt"
    )
    tax_rate = models.DecimalField(
        max_digits=5,
        decimal_places=4,
        default=Decimal('0.2500'),
        help_text="Effective tax rate"
    )
    
    # Capital Structure
    debt_weight = models.DecimalField(
        max_digits=5,
        decimal_places=4,
        default=Decimal('0.2000'),
        help_text="Debt weight in capital structure (e.g., 0.20 for 20%)"
    )
    equity_weight = models.DecimalField(
        max_digits=5,
        decimal_places=4,
        default=Decimal('0.8000'),
        help_text="Equity weight in capital structure (e.g., 0.80 for 80%)"
    )
    
    # DCF Assumptions
    terminal_growth_rate = models.DecimalField(
        max_digits=5,
        decimal_places=4,
        default=Decimal('0.0250'),
        help_text="Perpetual growth rate (e.g., 0.025 for 2.5%)"
    )
    forecast_years = models.IntegerField(
        default=5,
        help_text="Number of forecast years"
    )
    mid_year_convention = models.BooleanField(
        default=True,
        help_text="Use mid-year discounting convention"
    )
    
    # Revenue Growth (for forecasting)
    revenue_growth_rate = models.DecimalField(
        max_digits=5,
        decimal_places=4,
        default=Decimal('0.1000'),
        help_text="Annual revenue growth rate"
    )
    
    # CCA (Comparable Company Analysis) Assumptions
    ebitda_multiple_min = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal('5.00'),
        help_text="Minimum EBITDA multiple from comps"
    )
    ebitda_multiple_median = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal('7.00'),
        help_text="Median EBITDA multiple from comps"
    )
    ebitda_multiple_max = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal('9.00'),
        help_text="Maximum EBITDA multiple from comps"
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name_plural = "Valuation Assumptions"
    
    def __str__(self):
        return f"Assumptions for {self.project.name}"
    
    def calculate_wacc(self):
        """Calculate WACC from the assumptions."""
        # Cost of Equity = Rf + Beta * ERP + Size Premium + Company-Specific Premium
        cost_of_equity = (
            self.risk_free_rate +
            (self.beta * self.equity_risk_premium) +
            self.size_premium +
            self.company_specific_premium
        )
        
        # After-tax Cost of Debt = Kd * (1 - Tax Rate)
        after_tax_cost_of_debt = self.cost_of_debt * (Decimal('1') - self.tax_rate)
        
        # WACC = (We * Ke) + (Wd * Kd * (1-T))
        wacc = (self.equity_weight * cost_of_equity) + (self.debt_weight * after_tax_cost_of_debt)
        
        return float(wacc)


class ValuationResult(models.Model):
    """
    Stores the final summarized valuation output.
    """
    project = models.OneToOneField(
        Project,
        on_delete=models.CASCADE,
        related_name='result',
        help_text="Associated project"
    )
    
    # DCF Results
    dcf_enterprise_value = models.DecimalField(
        max_digits=20,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="DCF Enterprise Value"
    )
    dcf_equity_value = models.DecimalField(
        max_digits=20,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="DCF Equity Value"
    )
    dcf_pv_forecast_fcf = models.DecimalField(
        max_digits=20,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Present value of forecast FCF"
    )
    dcf_pv_terminal_value = models.DecimalField(
        max_digits=20,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Present value of terminal value"
    )
    
    # CCA Results
    cca_equity_value_min = models.DecimalField(
        max_digits=20,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="CCA Equity Value (Min Multiple)"
    )
    cca_equity_value_median = models.DecimalField(
        max_digits=20,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="CCA Equity Value (Median Multiple)"
    )
    cca_equity_value_max = models.DecimalField(
        max_digits=20,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="CCA Equity Value (Max Multiple)"
    )
    
    # Final Conclusion
    concluded_equity_value = models.DecimalField(
        max_digits=20,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Concluded Equity Value (weighted average or analyst selection)"
    )
    
    # Metadata
    wacc_used = models.DecimalField(
        max_digits=5,
        decimal_places=4,
        null=True,
        blank=True,
        help_text="WACC used in calculation"
    )
    calculation_notes = models.TextField(blank=True, help_text="Notes about the calculation")
    
    # Timestamps
    calculated_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name_plural = "Valuation Results"
    
    def __str__(self):
        return f"Results for {self.project.name}"
