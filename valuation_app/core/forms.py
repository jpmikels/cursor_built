"""
Django forms for the core application.
"""

from django import forms
from .models import Project, ValuationAssumptions


class ProjectUploadForm(forms.ModelForm):
    """
    Form for creating a new project and uploading a financial data file.
    """
    
    class Meta:
        model = Project
        fields = ['name', 'client_name', 'description', 'uploaded_file', 'fiscal_year_end', 'currency', 'industry_code']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter project name'
            }),
            'client_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter client company name'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Optional project description'
            }),
            'uploaded_file': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': '.xlsx,.xls,.csv'
            }),
            'fiscal_year_end': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., 12-31'
            }),
            'currency': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'USD'
            }),
            'industry_code': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., SIC/NAICS code'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Make some fields optional
        self.fields['description'].required = False
        self.fields['fiscal_year_end'].required = False
        self.fields['industry_code'].required = False
        self.fields['client_name'].required = False
    
    def save(self, commit=True):
        """Save the form and set the created_by user."""
        project = super().save(commit=False)
        
        if self.user:
            project.created_by = self.user
        
        if commit:
            project.save()
            # Save the uploaded file name
            if project.uploaded_file:
                project.original_filename = project.uploaded_file.name
                project.save()
        
        return project


class ValuationAssumptionsForm(forms.ModelForm):
    """
    Form for inputting valuation assumptions.
    """
    
    class Meta:
        model = ValuationAssumptions
        fields = [
            'risk_free_rate',
            'equity_risk_premium',
            'beta',
            'size_premium',
            'company_specific_premium',
            'cost_of_debt',
            'tax_rate',
            'debt_weight',
            'equity_weight',
            'terminal_growth_rate',
            'forecast_years',
            'mid_year_convention',
            'revenue_growth_rate',
            'ebitda_multiple_min',
            'ebitda_multiple_median',
            'ebitda_multiple_max',
        ]
        
        widgets = {
            'risk_free_rate': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.0001',
                'placeholder': '0.0450'
            }),
            'equity_risk_premium': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.0001',
                'placeholder': '0.0600'
            }),
            'beta': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'placeholder': '1.00'
            }),
            'size_premium': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.0001',
                'placeholder': '0.0000'
            }),
            'company_specific_premium': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.0001',
                'placeholder': '0.0000'
            }),
            'cost_of_debt': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.0001',
                'placeholder': '0.0600'
            }),
            'tax_rate': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.0001',
                'placeholder': '0.2500'
            }),
            'debt_weight': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.0001',
                'placeholder': '0.2000'
            }),
            'equity_weight': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.0001',
                'placeholder': '0.8000'
            }),
            'terminal_growth_rate': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.0001',
                'placeholder': '0.0250'
            }),
            'forecast_years': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '1',
                'max': '10',
                'placeholder': '5'
            }),
            'mid_year_convention': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'revenue_growth_rate': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.0001',
                'placeholder': '0.1000'
            }),
            'ebitda_multiple_min': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'placeholder': '5.00'
            }),
            'ebitda_multiple_median': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'placeholder': '7.00'
            }),
            'ebitda_multiple_max': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'placeholder': '9.00'
            }),
        }
        
        help_texts = {
            'risk_free_rate': 'e.g., 0.0450 for 4.5%',
            'equity_risk_premium': 'e.g., 0.0600 for 6.0%',
            'beta': 'Company beta (e.g., 1.00)',
            'size_premium': 'Size premium for small companies',
            'company_specific_premium': 'Company-specific risk premium',
            'cost_of_debt': 'Pre-tax cost of debt',
            'tax_rate': 'Effective tax rate (e.g., 0.2500 for 25%)',
            'debt_weight': 'Debt weight in capital structure (e.g., 0.20 for 20%)',
            'equity_weight': 'Equity weight in capital structure (e.g., 0.80 for 80%)',
            'terminal_growth_rate': 'Perpetual growth rate (e.g., 0.025 for 2.5%)',
            'forecast_years': 'Number of forecast years (typically 5)',
            'mid_year_convention': 'Check to use mid-year discounting',
            'revenue_growth_rate': 'Annual revenue growth rate',
            'ebitda_multiple_min': 'Minimum EBITDA multiple from comps',
            'ebitda_multiple_median': 'Median EBITDA multiple from comps',
            'ebitda_multiple_max': 'Maximum EBITDA multiple from comps',
        }
    
    def clean(self):
        """Validate that debt and equity weights sum to approximately 1.0."""
        cleaned_data = super().clean()
        
        debt_weight = cleaned_data.get('debt_weight')
        equity_weight = cleaned_data.get('equity_weight')
        
        if debt_weight is not None and equity_weight is not None:
            total = debt_weight + equity_weight
            if abs(total - 1.0) > 0.01:
                raise forms.ValidationError(
                    f"Debt weight and equity weight must sum to 1.0 (currently {total:.4f})"
                )
        
        return cleaned_data
