"""
Excel report generator for valuation results.
"""

import logging
from datetime import datetime
from typing import Dict, Any
import xlsxwriter
from pathlib import Path

logger = logging.getLogger(__name__)


class ExcelExporter:
    """
    Generates detailed Excel reports with valuation results.
    """
    
    def __init__(self):
        """Initialize the Excel exporter."""
        pass
    
    def generate_valuation_excel(
        self,
        project_data: Dict[str, Any],
        financial_data: Dict[str, Dict[int, float]],
        assumptions: Dict[str, Any],
        dcf_results: Dict[str, Any],
        cca_results: Dict[str, Any],
        output_path: str
    ) -> str:
        """
        Generate comprehensive Excel report.
        
        Args:
            project_data: Project metadata
            financial_data: Historical financial data
            assumptions: Valuation assumptions
            dcf_results: DCF calculation results
            cca_results: CCA calculation results
            output_path: Path to save the Excel file
            
        Returns:
            Path to generated Excel file
        """
        logger.info(f"Generating Excel report: {output_path}")
        
        try:
            # Create workbook
            workbook = xlsxwriter.Workbook(output_path)
            
            # Define formats
            formats = self._create_formats(workbook)
            
            # Create sheets
            self._create_summary_sheet(workbook, formats, project_data, dcf_results, cca_results)
            self._create_historical_data_sheet(workbook, formats, financial_data)
            self._create_assumptions_sheet(workbook, formats, assumptions)
            self._create_dcf_sheet(workbook, formats, dcf_results)
            self._create_cca_sheet(workbook, formats, cca_results)
            
            # Close workbook
            workbook.close()
            
            logger.info(f"Excel report generated successfully: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"Error generating Excel report: {e}")
            raise
    
    def _create_formats(self, workbook: xlsxwriter.Workbook) -> Dict[str, Any]:
        """Create cell formats."""
        return {
            'title': workbook.add_format({
                'bold': True,
                'font_size': 16,
                'align': 'left',
                'valign': 'vcenter'
            }),
            'header': workbook.add_format({
                'bold': True,
                'bg_color': '#4472C4',
                'font_color': 'white',
                'align': 'center',
                'valign': 'vcenter',
                'border': 1
            }),
            'currency': workbook.add_format({
                'num_format': '$#,##0',
                'align': 'right'
            }),
            'currency_decimal': workbook.add_format({
                'num_format': '$#,##0.00',
                'align': 'right'
            }),
            'percent': workbook.add_format({
                'num_format': '0.00%',
                'align': 'right'
            }),
            'number': workbook.add_format({
                'num_format': '#,##0',
                'align': 'right'
            }),
            'bold': workbook.add_format({'bold': True}),
            'bold_currency': workbook.add_format({
                'bold': True,
                'num_format': '$#,##0',
                'align': 'right'
            }),
        }
    
    def _create_summary_sheet(self, workbook, formats, project_data, dcf_results, cca_results):
        """Create executive summary sheet."""
        sheet = workbook.add_worksheet('Executive Summary')
        
        row = 0
        
        # Title
        sheet.write(row, 0, 'Business Valuation Report', formats['title'])
        row += 2
        
        # Project details
        sheet.write(row, 0, 'Project:', formats['bold'])
        sheet.write(row, 1, project_data.get('name', 'N/A'))
        row += 1
        
        sheet.write(row, 0, 'Client:', formats['bold'])
        sheet.write(row, 1, project_data.get('client_name', 'N/A'))
        row += 1
        
        sheet.write(row, 0, 'Date:', formats['bold'])
        sheet.write(row, 1, datetime.now().strftime('%Y-%m-%d'))
        row += 2
        
        # Valuation summary
        sheet.write(row, 0, 'Valuation Summary', formats['header'])
        sheet.write(row, 1, 'Value', formats['header'])
        row += 1
        
        # DCF results
        sheet.write(row, 0, 'DCF Method', formats['bold'])
        row += 1
        
        sheet.write(row, 0, '  Enterprise Value')
        sheet.write(row, 1, dcf_results.get('enterprise_value', 0), formats['currency'])
        row += 1
        
        sheet.write(row, 0, '  Equity Value')
        sheet.write(row, 1, dcf_results.get('equity_value', 0), formats['bold_currency'])
        row += 2
        
        # CCA results
        sheet.write(row, 0, 'Comparable Company Analysis', formats['bold'])
        row += 1
        
        sheet.write(row, 0, '  Equity Value (Min)')
        sheet.write(row, 1, cca_results.get('equity_value_min', 0), formats['currency'])
        row += 1
        
        sheet.write(row, 0, '  Equity Value (Median)')
        sheet.write(row, 1, cca_results.get('equity_value_median', 0), formats['currency'])
        row += 1
        
        sheet.write(row, 0, '  Equity Value (Max)')
        sheet.write(row, 1, cca_results.get('equity_value_max', 0), formats['currency'])
        row += 2
        
        # Concluded value (simple average of DCF and CCA median)
        dcf_equity = dcf_results.get('equity_value', 0)
        cca_equity = cca_results.get('equity_value_median', 0)
        concluded_value = (dcf_equity + cca_equity) / 2 if (dcf_equity and cca_equity) else dcf_equity or cca_equity
        
        sheet.write(row, 0, 'Concluded Equity Value', formats['bold'])
        sheet.write(row, 1, concluded_value, formats['bold_currency'])
        
        # Set column widths
        sheet.set_column('A:A', 35)
        sheet.set_column('B:B', 20)
    
    def _create_historical_data_sheet(self, workbook, formats, financial_data):
        """Create historical financial data sheet."""
        sheet = workbook.add_worksheet('Historical Data')
        
        # Get all years
        all_years = set()
        for metric_data in financial_data.values():
            all_years.update(metric_data.keys())
        
        years = sorted(list(all_years))
        
        # Headers
        sheet.write(0, 0, 'Metric', formats['header'])
        for col, year in enumerate(years, start=1):
            sheet.write(0, col, str(year), formats['header'])
        
        # Data rows
        row = 1
        for metric_name, year_values in sorted(financial_data.items()):
            sheet.write(row, 0, metric_name, formats['bold'])
            for col, year in enumerate(years, start=1):
                value = year_values.get(year, 0)
                sheet.write(row, col, value, formats['currency'])
            row += 1
        
        # Set column widths
        sheet.set_column('A:A', 30)
        sheet.set_column('B:Z', 15)
    
    def _create_assumptions_sheet(self, workbook, formats, assumptions):
        """Create assumptions sheet."""
        sheet = workbook.add_worksheet('Assumptions')
        
        row = 0
        sheet.write(row, 0, 'Valuation Assumptions', formats['header'])
        row += 2
        
        # WACC components
        sheet.write(row, 0, 'WACC Components', formats['bold'])
        row += 1
        
        items = [
            ('Risk-free Rate', 'risk_free_rate', 'percent'),
            ('Equity Risk Premium', 'equity_risk_premium', 'percent'),
            ('Beta', 'beta', 'number'),
            ('Size Premium', 'size_premium', 'percent'),
            ('Company-Specific Premium', 'company_specific_premium', 'percent'),
            ('Cost of Debt', 'cost_of_debt', 'percent'),
            ('Tax Rate', 'tax_rate', 'percent'),
            ('Debt Weight', 'debt_weight', 'percent'),
            ('Equity Weight', 'equity_weight', 'percent'),
        ]
        
        for label, key, format_type in items:
            sheet.write(row, 0, label)
            value = assumptions.get(key, 0)
            sheet.write(row, 1, value, formats[format_type])
            row += 1
        
        row += 1
        sheet.write(row, 0, 'Calculated WACC', formats['bold'])
        sheet.write(row, 1, assumptions.get('wacc', 0), formats['percent'])
        row += 2
        
        # DCF assumptions
        sheet.write(row, 0, 'DCF Assumptions', formats['bold'])
        row += 1
        
        dcf_items = [
            ('Terminal Growth Rate', 'terminal_growth_rate', 'percent'),
            ('Forecast Years', 'forecast_years', 'number'),
            ('Revenue Growth Rate', 'revenue_growth_rate', 'percent'),
        ]
        
        for label, key, format_type in dcf_items:
            sheet.write(row, 0, label)
            sheet.write(row, 1, assumptions.get(key, 0), formats[format_type])
            row += 1
        
        # Set column widths
        sheet.set_column('A:A', 35)
        sheet.set_column('B:B', 20)
    
    def _create_dcf_sheet(self, workbook, formats, dcf_results):
        """Create DCF calculation sheet."""
        sheet = workbook.add_worksheet('DCF Analysis')
        
        row = 0
        sheet.write(row, 0, 'DCF Valuation Analysis', formats['title'])
        row += 2
        
        # Forecast details
        forecast_details = dcf_results.get('forecast_details', [])
        
        if forecast_details:
            sheet.write(row, 0, 'Free Cash Flow Forecast', formats['header'])
            row += 1
            
            # Headers
            headers = ['Year', 'Revenue', 'EBITDA', 'EBIT', 'NOPAT', 'D&A', 'CapEx', 'FCF']
            for col, header in enumerate(headers):
                sheet.write(row, col, header, formats['header'])
            row += 1
            
            # Data
            for detail in forecast_details:
                sheet.write(row, 0, detail['year'])
                sheet.write(row, 1, detail['revenue'], formats['currency'])
                sheet.write(row, 2, detail['ebitda'], formats['currency'])
                sheet.write(row, 3, detail['ebit'], formats['currency'])
                sheet.write(row, 4, detail['nopat'], formats['currency'])
                sheet.write(row, 5, detail['depreciation'], formats['currency'])
                sheet.write(row, 6, detail['capex'], formats['currency'])
                sheet.write(row, 7, detail['fcf'], formats['currency'])
                row += 1
            
            row += 1
        
        # Valuation summary
        sheet.write(row, 0, 'Valuation Summary', formats['header'])
        row += 1
        
        summary_items = [
            ('PV of Forecast FCF', 'pv_forecast_fcf'),
            ('PV of Terminal Value', 'pv_terminal_value'),
            ('Enterprise Value', 'enterprise_value'),
            ('Plus: Cash', 'cash'),
            ('Less: Debt', 'debt'),
            ('Equity Value', 'equity_value'),
        ]
        
        for label, key in summary_items:
            sheet.write(row, 0, label, formats['bold'] if key == 'equity_value' else None)
            value = dcf_results.get(key, 0)
            if key == 'debt':
                value = -value  # Show as negative
            sheet.write(row, 1, value, formats['bold_currency'] if key == 'equity_value' else formats['currency'])
            row += 1
        
        # Set column widths
        sheet.set_column('A:A', 30)
        sheet.set_column('B:H', 15)
    
    def _create_cca_sheet(self, workbook, formats, cca_results):
        """Create CCA analysis sheet."""
        sheet = workbook.add_worksheet('CCA Analysis')
        
        row = 0
        sheet.write(row, 0, 'Comparable Company Analysis', formats['title'])
        row += 2
        
        # EBITDA used
        sheet.write(row, 0, 'Subject Company EBITDA', formats['bold'])
        sheet.write(row, 1, cca_results.get('ebitda_used', 0), formats['currency'])
        row += 2
        
        # Multiples table
        sheet.write(row, 0, 'Multiple', formats['header'])
        sheet.write(row, 1, 'Enterprise Value', formats['header'])
        sheet.write(row, 2, 'Equity Value', formats['header'])
        row += 1
        
        multiples = [
            ('Minimum', 'multiple_min', 'ev_min', 'equity_value_min'),
            ('Median', 'multiple_median', 'ev_median', 'equity_value_median'),
            ('Maximum', 'multiple_max', 'ev_max', 'equity_value_max'),
        ]
        
        for label, mult_key, ev_key, eq_key in multiples:
            sheet.write(row, 0, f"{cca_results.get(mult_key, 0):.1f}x ({label})")
            sheet.write(row, 1, cca_results.get(ev_key, 0), formats['currency'])
            sheet.write(row, 2, cca_results.get(eq_key, 0), formats['currency'])
            row += 1
        
        # Set column widths
        sheet.set_column('A:A', 30)
        sheet.set_column('B:C', 20)
