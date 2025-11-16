"""
Data ingestion module for reading and parsing financial data files.
"""

import logging
import pandas as pd
from typing import Dict, List, Any
from pathlib import Path

logger = logging.getLogger(__name__)


class DataIngestionEngine:
    """
    Reads financial data files (Excel/CSV) and extracts structured data.
    """
    
    def __init__(self):
        """Initialize the data ingestion engine."""
        pass
    
    def read_file(self, file_path: str) -> Dict[str, Any]:
        """
        Read and parse a financial data file.
        
        Args:
            file_path: Path to the file to read
            
        Returns:
            Dictionary containing parsed data with structure:
            {
                'sheets': List of sheet names or 'csv',
                'data': Dict mapping metric_name -> {year: value},
                'metadata': Additional parsing metadata
            }
        """
        logger.info(f"Reading file: {file_path}")
        
        file_path_obj = Path(file_path)
        
        if not file_path_obj.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        # Determine file type and parse accordingly
        if file_path.endswith('.xlsx') or file_path.endswith('.xls'):
            return self._read_excel(file_path)
        elif file_path.endswith('.csv'):
            return self._read_csv(file_path)
        else:
            raise ValueError(f"Unsupported file format: {file_path}")
    
    def _read_excel(self, file_path: str) -> Dict[str, Any]:
        """Read and parse Excel file."""
        logger.info(f"Parsing Excel file: {file_path}")
        
        try:
            # Read all sheets
            excel_file = pd.ExcelFile(file_path)
            sheets = excel_file.sheet_names
            
            logger.info(f"Found {len(sheets)} sheets: {sheets}")
            
            # Parse each sheet
            all_data = {}
            metadata = {'sheets': sheets}
            
            for sheet_name in sheets:
                sheet_data = self._parse_sheet(file_path, sheet_name)
                if sheet_data:
                    all_data.update(sheet_data)
            
            return {
                'sheets': sheets,
                'data': all_data,
                'metadata': metadata
            }
            
        except Exception as e:
            logger.error(f"Error reading Excel file: {e}")
            raise
    
    def _parse_sheet(self, file_path: str, sheet_name: str) -> Dict[str, Dict[int, float]]:
        """
        Parse a single Excel sheet.
        
        Expected format:
        - First column: metric names (Revenue, COGS, EBITDA, etc.)
        - Subsequent columns: years (2020, 2021, 2022, etc.)
        
        Returns:
            Dict mapping metric_name -> {year: value}
        """
        try:
            # Read the sheet
            df = pd.read_excel(file_path, sheet_name=sheet_name, header=None)
            
            # Find header row (row with years)
            header_row = self._find_header_row(df)
            
            if header_row is None:
                logger.warning(f"Could not find header row in sheet {sheet_name}")
                return {}
            
            # Re-read with proper header
            df = pd.read_excel(file_path, sheet_name=sheet_name, header=header_row)
            
            # Clean up column names
            df.columns = [str(col).strip() for col in df.columns]
            
            # Drop empty rows
            df = df.dropna(how='all')
            
            # Get the first column (metric names)
            if df.empty or len(df.columns) < 2:
                return {}
            
            first_col_name = df.columns[0]
            df[first_col_name] = df[first_col_name].astype(str).str.strip()
            
            # Parse data into dictionary
            parsed_data = {}
            
            for _, row in df.iterrows():
                metric_name = str(row[first_col_name])
                
                if not metric_name or metric_name == 'nan':
                    continue
                
                # Extract values for each year
                year_values = {}
                for col in df.columns[1:]:
                    try:
                        # Try to parse column as year
                        year = int(float(col))
                        value = row[col]
                        
                        if pd.notna(value):
                            try:
                                year_values[year] = float(value)
                            except (ValueError, TypeError):
                                logger.warning(f"Could not parse value for {metric_name}, {year}: {value}")
                    except (ValueError, TypeError):
                        # Column is not a year, skip
                        continue
                
                if year_values:
                    parsed_data[metric_name] = year_values
            
            logger.info(f"Parsed {len(parsed_data)} metrics from sheet {sheet_name}")
            return parsed_data
            
        except Exception as e:
            logger.error(f"Error parsing sheet {sheet_name}: {e}")
            return {}
    
    def _find_header_row(self, df: pd.DataFrame, max_search_rows: int = 20) -> int:
        """
        Find the header row by looking for a row with year-like values.
        
        Returns:
            Row index (0-based) or None if not found
        """
        for i in range(min(max_search_rows, len(df))):
            row = df.iloc[i]
            
            # Check if row contains year-like values (4-digit numbers starting with 19 or 20)
            year_count = 0
            for val in row:
                try:
                    val_str = str(val)
                    if val_str.isdigit() and len(val_str) == 4:
                        year = int(val_str)
                        if 1900 <= year <= 2100:
                            year_count += 1
                except:
                    pass
            
            # If we found at least 2 years, this is likely the header row
            if year_count >= 2:
                return i
        
        return None
    
    def _read_csv(self, file_path: str) -> Dict[str, Any]:
        """Read and parse CSV file."""
        logger.info(f"Parsing CSV file: {file_path}")
        
        try:
            df = pd.read_csv(file_path)
            
            # Clean up column names
            df.columns = [str(col).strip() for col in df.columns]
            
            # Parse data (same logic as Excel)
            first_col_name = df.columns[0]
            df[first_col_name] = df[first_col_name].astype(str).str.strip()
            
            parsed_data = {}
            
            for _, row in df.iterrows():
                metric_name = str(row[first_col_name])
                
                if not metric_name or metric_name == 'nan':
                    continue
                
                year_values = {}
                for col in df.columns[1:]:
                    try:
                        year = int(float(col))
                        value = row[col]
                        
                        if pd.notna(value):
                            try:
                                year_values[year] = float(value)
                            except (ValueError, TypeError):
                                pass
                    except (ValueError, TypeError):
                        continue
                
                if year_values:
                    parsed_data[metric_name] = year_values
            
            return {
                'sheets': ['csv'],
                'data': parsed_data,
                'metadata': {'type': 'csv'}
            }
            
        except Exception as e:
            logger.error(f"Error reading CSV file: {e}")
            raise
    
    def normalize_metric_names(self, data: Dict[str, Dict[int, float]]) -> Dict[str, Dict[int, float]]:
        """
        Normalize metric names to standard format.
        
        This is a simple version - can be enhanced with fuzzy matching, ML, etc.
        """
        METRIC_MAPPINGS = {
            'revenue': ['revenue', 'sales', 'total revenue', 'net sales', 'gross sales'],
            'cogs': ['cogs', 'cost of goods sold', 'cost of sales'],
            'gross_profit': ['gross profit', 'gross income'],
            'operating_expenses': ['operating expenses', 'opex', 'sg&a'],
            'ebitda': ['ebitda', 'ebit da', 'adjusted ebitda'],
            'ebit': ['ebit', 'operating income', 'operating profit'],
            'interest_expense': ['interest expense', 'interest'],
            'tax_expense': ['tax expense', 'taxes', 'income tax'],
            'net_income': ['net income', 'net profit', 'net earnings'],
            'total_assets': ['total assets', 'assets'],
            'total_liabilities': ['total liabilities', 'liabilities'],
            'total_equity': ['total equity', 'equity', 'shareholders equity'],
            'cash': ['cash', 'cash and equivalents', 'cash & cash equivalents'],
            'debt': ['debt', 'total debt', 'long-term debt'],
            'depreciation': ['depreciation', 'depreciation and amortization', 'd&a'],
            'capex': ['capex', 'capital expenditures'],
        }
        
        normalized_data = {}
        
        for metric_name, year_values in data.items():
            metric_lower = metric_name.lower().strip()
            
            # Find matching standard name
            standard_name = metric_name  # Default to original
            
            for standard, variations in METRIC_MAPPINGS.items():
                if metric_lower in variations:
                    standard_name = standard
                    break
            
            normalized_data[standard_name] = year_values
        
        return normalized_data
