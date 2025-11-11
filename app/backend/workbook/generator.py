"""Excel workbook generator with formulas."""
import logging
from typing import Dict, Any, List
from datetime import datetime
import xlsxwriter
from google.cloud import storage

from config import settings

logger = logging.getLogger(__name__)


class WorkbookGenerator:
    """Generate formula-rich Excel workbooks."""
    
    def __init__(self):
        self.storage_client = storage.Client(project=settings.project_id)
    
    def generate_consolidated_workbook(
        self,
        engagement_data: Dict[str, Any],
        normalized_data: Dict[str, Any],
        tenant_id: int,
        engagement_id: int
    ) -> str:
        """
        Generate consolidated Excel workbook with formulas.
        
        Args:
            engagement_data: Engagement metadata
            normalized_data: Normalized financial data
            tenant_id: Tenant ID
            engagement_id: Engagement ID
            
        Returns:
            GCS path to generated workbook
        """
        logger.info(f"Generating workbook for engagement {engagement_id}")
        
        # Create temp file
        temp_file = f"/tmp/workbook_{engagement_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}.xlsx"
        
        # Create workbook
        workbook = xlsxwriter.Workbook(temp_file)
        
        # Define formats
        formats = self._create_formats(workbook)
        
        # Create sheets
        self._create_cover_sheet(workbook, formats, engagement_data)
        self._create_assumptions_sheet(workbook, formats, engagement_data)
        self._create_raw_imports_sheet(workbook, formats, normalized_data)
        self._create_normalized_is(workbook, formats, normalized_data.get('income_statement', {}))
        self._create_normalized_bs(workbook, formats, normalized_data.get('balance_sheet', {}))
        self._create_normalized_cf(workbook, formats, normalized_data.get('cash_flow', {}))
        self._create_adjustments_sheet(workbook, formats)
        self._create_ratios_sheet(workbook, formats)
        self._create_forecast_sheet(workbook, formats)
        self._create_valuation_sheet(workbook, formats)
        self._create_audit_log_sheet(workbook, formats)
        
        workbook.close()
        
        # Upload to GCS
        gcs_path = f"{tenant_id}/{engagement_id}/workbook/consolidated.xlsx"
        bucket = self.storage_client.bucket(settings.artifacts_bucket)
        blob = bucket.blob(gcs_path)
        blob.upload_from_filename(temp_file)
        
        logger.info(f"Workbook uploaded to {gcs_path}")
        
        return gcs_path
    
    def _create_formats(self, workbook: xlsxwriter.Workbook) -> Dict[str, Any]:
        """Create cell formats."""
        return {
            'title': workbook.add_format({'bold': True, 'font_size': 16}),
            'header': workbook.add_format({'bold': True, 'bg_color': '#4472C4', 'font_color': 'white'}),
            'currency': workbook.add_format({'num_format': '$#,##0'}),
            'currency_decimal': workbook.add_format({'num_format': '$#,##0.00'}),
            'percent': workbook.add_format({'num_format': '0.0%'}),
            'number': workbook.add_format({'num_format': '#,##0'}),
            'date': workbook.add_format({'num_format': 'mm/dd/yyyy'}),
            'bold': workbook.add_format({'bold': True}),
            'subtotal': workbook.add_format({'bold': True, 'top': 1, 'bottom': 6}),
        }
    
    def _create_cover_sheet(self, workbook, formats, engagement_data):
        """Create cover/summary sheet."""
        sheet = workbook.add_worksheet('Cover')
        
        sheet.write('A1', 'Valuation Workbench', formats['title'])
        sheet.write('A2', 'Consolidated Financial Analysis')
        
        sheet.write('A4', 'Engagement:', formats['bold'])
        sheet.write('B4', engagement_data.get('name', 'N/A'))
        
        sheet.write('A5', 'Client:', formats['bold'])
        sheet.write('B5', engagement_data.get('client_name', 'N/A'))
        
        sheet.write('A6', 'Currency:', formats['bold'])
        sheet.write('B6', engagement_data.get('currency', 'USD'))
        
        sheet.write('A7', 'Fiscal Year End:', formats['bold'])
        sheet.write('B7', engagement_data.get('fiscal_year_end', 'N/A'))
        
        sheet.write('A8', 'Generated:', formats['bold'])
        sheet.write('B8', datetime.now(), formats['date'])
        
        sheet.set_column('A:A', 20)
        sheet.set_column('B:B', 30)
    
    def _create_assumptions_sheet(self, workbook, formats, engagement_data):
        """Create assumptions sheet."""
        sheet = workbook.add_worksheet('Assumptions')
        
        sheet.write('A1', 'Valuation Assumptions', formats['header'])
        
        sheet.write('A3', 'Revenue Growth Rate (Annual):', formats['bold'])
        sheet.write('B3', 0.10, formats['percent'])  # Default 10%
        sheet.set_row(2, None, None, {'hidden': False, 'level': 0})
        
        sheet.write('A4', 'Terminal Growth Rate:', formats['bold'])
        sheet.write('B4', 0.025, formats['percent'])  # Default 2.5%
        
        sheet.write('A5', 'Risk-free Rate:', formats['bold'])
        sheet.write('B5', 0.045, formats['percent'])  # Default 4.5%
        
        sheet.write('A6', 'Equity Risk Premium:', formats['bold'])
        sheet.write('B6', 0.06, formats['percent'])  # Default 6%
        
        sheet.write('A7', 'Beta:', formats['bold'])
        sheet.write('B7', 1.0)
        
        sheet.write('A8', 'Tax Rate:', formats['bold'])
        sheet.write('B8', 0.25, formats['percent'])  # Default 25%
        
        # Named ranges for assumptions
        workbook.define_name('RevenueGrowth', '=Assumptions!$B$3')
        workbook.define_name('TerminalGrowth', '=Assumptions!$B$4')
        workbook.define_name('RiskFreeRate', '=Assumptions!$B$5')
        workbook.define_name('EquityRiskPremium', '=Assumptions!$B$6')
        workbook.define_name('Beta', '=Assumptions!$B$7')
        workbook.define_name('TaxRate', '=Assumptions!$B$8')
        
        sheet.set_column('A:A', 30)
        sheet.set_column('B:B', 15)
    
    def _create_raw_imports_sheet(self, workbook, formats, normalized_data):
        """Create raw imports sheet."""
        sheet = workbook.add_worksheet('Raw Imports')
        
        sheet.write('A1', 'Raw Imported Data', formats['header'])
        sheet.write('A2', 'This sheet contains snapshots of parsed source documents')
        
        # Would add actual raw data here
        sheet.set_column('A:A', 40)
    
    def _create_normalized_is(self, workbook, formats, is_data):
        """Create normalized income statement with formulas."""
        sheet = workbook.add_worksheet('Income Statement')
        
        periods = is_data.get('periods', [])
        line_items = is_data.get('line_items', [])
        
        # Headers
        sheet.write('A1', 'Income Statement', formats['header'])
        for col, period in enumerate(periods, start=1):
            sheet.write(0, col, period, formats['header'])
        
        # Line items
        row = 1
        for item in line_items:
            sheet.write(row, 0, item['label'])
            for col, period in enumerate(periods, start=1):
                value = item['values'].get(period, 0)
                sheet.write(row, col, float(value), formats['currency'])
            row += 1
        
        # Add calculated fields with formulas
        if len(periods) > 0:
            # Gross Margin %
            sheet.write(row, 0, 'Gross Margin %', formats['bold'])
            for col in range(1, len(periods) + 1):
                # Formula: Gross Profit / Revenue
                formula = f'=IF({xlsxwriter.utility.xl_col_to_name(col)}3=0,0,{xlsxwriter.utility.xl_col_to_name(col)}4/{xlsxwriter.utility.xl_col_to_name(col)}3)'
                sheet.write_formula(row, col, formula, formats['percent'])
            row += 1
        
        sheet.set_column('A:A', 35)
        sheet.set_column('B:Z', 15)
    
    def _create_normalized_bs(self, workbook, formats, bs_data):
        """Create normalized balance sheet with formulas."""
        sheet = workbook.add_worksheet('Balance Sheet')
        
        periods = bs_data.get('periods', [])
        line_items = bs_data.get('line_items', [])
        
        # Headers
        sheet.write('A1', 'Balance Sheet', formats['header'])
        for col, period in enumerate(periods, start=1):
            sheet.write(0, col, period, formats['header'])
        
        # Line items
        row = 1
        for item in line_items:
            sheet.write(row, 0, item['label'])
            for col, period in enumerate(periods, start=1):
                value = item['values'].get(period, 0)
                sheet.write(row, col, float(value), formats['currency'])
            row += 1
        
        sheet.set_column('A:A', 35)
        sheet.set_column('B:Z', 15)
    
    def _create_normalized_cf(self, workbook, formats, cf_data):
        """Create normalized cash flow statement."""
        sheet = workbook.add_worksheet('Cash Flow')
        
        periods = cf_data.get('periods', [])
        line_items = cf_data.get('line_items', [])
        
        # Headers
        sheet.write('A1', 'Cash Flow Statement', formats['header'])
        for col, period in enumerate(periods, start=1):
            sheet.write(0, col, period, formats['header'])
        
        # Line items
        row = 1
        for item in line_items:
            sheet.write(row, 0, item['label'])
            for col, period in enumerate(periods, start=1):
                value = item['values'].get(period, 0)
                sheet.write(row, col, float(value), formats['currency'])
            row += 1
        
        sheet.set_column('A:A', 35)
        sheet.set_column('B:Z', 15)
    
    def _create_adjustments_sheet(self, workbook, formats):
        """Create quality of earnings adjustments sheet."""
        sheet = workbook.add_worksheet('Adjustments')
        
        sheet.write('A1', 'Quality of Earnings Adjustments', formats['header'])
        
        headers = ['Adjustment Type', 'Description', 'Amount', 'Period', 'Justification']
        for col, header in enumerate(headers):
            sheet.write(1, col, header, formats['header'])
        
        # Example adjustment
        sheet.write('A3', 'Owner Compensation')
        sheet.write('B3', 'Normalize to market rate')
        sheet.write('C3', 50000, formats['currency'])
        sheet.write('D3', '2023')
        sheet.write('E3', 'Owner comp $200k vs market $150k')
        
        sheet.set_column('A:A', 25)
        sheet.set_column('B:B', 35)
        sheet.set_column('C:C', 15)
        sheet.set_column('D:D', 12)
        sheet.set_column('E:E', 40)
    
    def _create_ratios_sheet(self, workbook, formats):
        """Create financial ratios sheet."""
        sheet = workbook.add_worksheet('Ratios')
        
        sheet.write('A1', 'Financial Ratios & KPIs', formats['header'])
        
        # Profitability ratios
        sheet.write('A3', 'Profitability', formats['bold'])
        sheet.write('A4', 'Gross Margin %')
        sheet.write('A5', 'Operating Margin %')
        sheet.write('A6', 'Net Margin %')
        
        # Liquidity ratios
        sheet.write('A8', 'Liquidity', formats['bold'])
        sheet.write('A9', 'Current Ratio')
        sheet.write('A10', 'Quick Ratio')
        
        # Leverage ratios
        sheet.write('A12', 'Leverage', formats['bold'])
        sheet.write('A13', 'Debt to Equity')
        sheet.write('A14', 'Interest Coverage')
        
        sheet.set_column('A:A', 30)
        sheet.set_column('B:Z', 15)
    
    def _create_forecast_sheet(self, workbook, formats):
        """Create forecast sheet with driver-based model."""
        sheet = workbook.add_worksheet('Forecast')
        
        sheet.write('A1', 'Financial Forecast', formats['header'])
        
        # Forecast periods
        sheet.write('A3', 'Period')
        for col in range(1, 6):  # 5 forecast years
            sheet.write(2, col, f'Year {col}', formats['header'])
        
        # Revenue forecast
        sheet.write('A4', 'Revenue')
        sheet.write('B4', '=\'Income Statement\'!B3')  # Link to historical
        for col in range(2, 6):
            # Formula: Prior year * (1 + growth rate)
            formula = f'={xlsxwriter.utility.xl_col_to_name(col)}4*(1+RevenueGrowth)'
            sheet.write_formula(3, col, formula, formats['currency'])
        
        sheet.set_column('A:A', 30)
        sheet.set_column('B:Z', 15)
    
    def _create_valuation_sheet(self, workbook, formats):
        """Create valuation calculations sheet."""
        sheet = workbook.add_worksheet('Valuation')
        
        sheet.write('A1', 'Business Valuation', formats['header'])
        
        # WACC calculation
        sheet.write('A3', 'WACC Calculation', formats['bold'])
        sheet.write('A4', 'Cost of Equity')
        sheet.write('B4', '=RiskFreeRate+Beta*EquityRiskPremium', formats['percent'])
        
        sheet.write('A5', 'After-tax Cost of Debt')
        sheet.write('B5', '=0.06*(1-TaxRate)', formats['percent'])  # Assuming 6% pre-tax
        
        sheet.write('A6', 'WACC')
        sheet.write('B6', '=B4*0.8+B5*0.2', formats['percent'])  # Assuming 80/20 equity/debt
        
        # Valuation methods
        sheet.write('A8', 'Valuation Methods', formats['bold'])
        sheet.write('A9', 'DCF Value')
        sheet.write('B9', 0, formats['currency'])  # Placeholder
        
        sheet.write('A10', 'GPCM Value')
        sheet.write('B10', 0, formats['currency'])  # Placeholder
        
        sheet.write('A11', 'GTM Value')
        sheet.write('B11', 0, formats['currency'])  # Placeholder
        
        sheet.write('A13', 'Concluded Value', formats['subtotal'])
        sheet.write_formula('B13', '=(B9*0.5+B10*0.3+B11*0.2)', formats['currency'])
        
        sheet.set_column('A:A', 30)
        sheet.set_column('B:B', 20)
    
    def _create_audit_log_sheet(self, workbook, formats):
        """Create audit trail sheet."""
        sheet = workbook.add_worksheet('Audit Log')
        
        sheet.write('A1', 'Audit Trail', formats['header'])
        
        headers = ['Timestamp', 'User', 'Action', 'Details', 'IP Address']
        for col, header in enumerate(headers):
            sheet.write(1, col, header, formats['header'])
        
        # Sample entry
        sheet.write('A3', datetime.now(), formats['date'])
        sheet.write('B3', 'System')
        sheet.write('C3', 'Workbook Generated')
        sheet.write('D3', 'Consolidated workbook created from parsed documents')
        
        sheet.set_column('A:A', 20)
        sheet.set_column('B:B', 20)
        sheet.set_column('C:C', 25)
        sheet.set_column('D:D', 50)
        sheet.set_column('E:E', 15)

