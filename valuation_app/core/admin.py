"""
Django admin configuration for core models.
"""

from django.contrib import admin
from .models import Project, FinancialData, ValuationAssumptions, ValuationResult


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    """Admin interface for Project model."""
    
    list_display = ['name', 'client_name', 'status', 'created_by', 'created_at', 'updated_at']
    list_filter = ['status', 'created_at', 'currency']
    search_fields = ['name', 'client_name', 'description']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'client_name', 'description', 'status')
        }),
        ('File Information', {
            'fields': ('uploaded_file', 'original_filename', 'excel_report_path')
        }),
        ('Metadata', {
            'fields': ('fiscal_year_end', 'currency', 'industry_code')
        }),
        ('Error Tracking', {
            'fields': ('error_message',),
            'classes': ('collapse',)
        }),
        ('System Information', {
            'fields': ('created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(FinancialData)
class FinancialDataAdmin(admin.ModelAdmin):
    """Admin interface for FinancialData model."""
    
    list_display = ['project', 'metric_name', 'year', 'value', 'is_derived']
    list_filter = ['project', 'year', 'is_derived']
    search_fields = ['metric_name', 'project__name']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(ValuationAssumptions)
class ValuationAssumptionsAdmin(admin.ModelAdmin):
    """Admin interface for ValuationAssumptions model."""
    
    list_display = ['project', 'risk_free_rate', 'beta', 'terminal_growth_rate', 'forecast_years']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Project', {
            'fields': ('project',)
        }),
        ('WACC Components', {
            'fields': (
                'risk_free_rate',
                'equity_risk_premium',
                'beta',
                'size_premium',
                'company_specific_premium',
                'cost_of_debt',
                'tax_rate',
            )
        }),
        ('Capital Structure', {
            'fields': ('debt_weight', 'equity_weight')
        }),
        ('DCF Assumptions', {
            'fields': (
                'terminal_growth_rate',
                'forecast_years',
                'mid_year_convention',
                'revenue_growth_rate',
            )
        }),
        ('CCA Assumptions', {
            'fields': (
                'ebitda_multiple_min',
                'ebitda_multiple_median',
                'ebitda_multiple_max',
            )
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(ValuationResult)
class ValuationResultAdmin(admin.ModelAdmin):
    """Admin interface for ValuationResult model."""
    
    list_display = [
        'project',
        'dcf_equity_value',
        'cca_equity_value_median',
        'concluded_equity_value',
        'calculated_at'
    ]
    readonly_fields = ['calculated_at', 'updated_at']
    
    fieldsets = (
        ('Project', {
            'fields': ('project',)
        }),
        ('DCF Results', {
            'fields': (
                'dcf_enterprise_value',
                'dcf_equity_value',
                'dcf_pv_forecast_fcf',
                'dcf_pv_terminal_value',
            )
        }),
        ('CCA Results', {
            'fields': (
                'cca_equity_value_min',
                'cca_equity_value_median',
                'cca_equity_value_max',
            )
        }),
        ('Conclusion', {
            'fields': ('concluded_equity_value', 'wacc_used', 'calculation_notes')
        }),
        ('Timestamps', {
            'fields': ('calculated_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
