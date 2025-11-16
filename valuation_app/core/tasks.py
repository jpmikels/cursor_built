"""
Celery tasks for asynchronous processing.
"""

import logging
from celery import shared_task
from django.core.files.base import ContentFile
from pathlib import Path

from .models import Project, FinancialData, ValuationAssumptions, ValuationResult, ProjectStatus
from .engines.data_ingestion import DataIngestionEngine
from .engines.dcf_engine import DCFEngine
from .engines.cca_engine import CCAEngine
from .engines.excel_exporter import ExcelExporter

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3)
def process_financial_file(self, project_id, file_path):
    """
    Process uploaded financial file and extract data.
    
    Args:
        project_id: ID of the Project
        file_path: Path to the uploaded file
        
    Returns:
        dict with status and message
    """
    logger.info(f"Starting file processing for project {project_id}")
    
    try:
        # Get project
        project = Project.objects.get(id=project_id)
        project.status = ProjectStatus.PROCESSING
        project.error_message = ''
        project.save()
        
        # Initialize ingestion engine
        ingestion_engine = DataIngestionEngine()
        
        # Read and parse file
        logger.info(f"Reading file: {file_path}")
        parsed_data = ingestion_engine.read_file(file_path)
        
        # Normalize metric names
        financial_data = ingestion_engine.normalize_metric_names(parsed_data['data'])
        
        logger.info(f"Extracted {len(financial_data)} metrics")
        
        # Delete existing financial data for this project
        FinancialData.objects.filter(project=project).delete()
        
        # Save to database
        data_objects = []
        for metric_name, year_values in financial_data.items():
            for year, value in year_values.items():
                data_objects.append(
                    FinancialData(
                        project=project,
                        metric_name=metric_name,
                        year=year,
                        value=value
                    )
                )
        
        # Bulk create for efficiency
        FinancialData.objects.bulk_create(data_objects)
        
        logger.info(f"Saved {len(data_objects)} data points to database")
        
        # Check if we have unmapped lines (simplified - assume all mapped)
        # In a real system, you'd check for unrecognized metric names
        project.status = ProjectStatus.READY
        project.save()
        
        logger.info(f"File processing complete for project {project_id}")
        
        return {
            'status': 'success',
            'message': f'Processed {len(data_objects)} data points',
            'metrics_count': len(financial_data)
        }
        
    except Project.DoesNotExist:
        logger.error(f"Project {project_id} not found")
        return {'status': 'error', 'message': 'Project not found'}
        
    except Exception as e:
        logger.error(f"Error processing file for project {project_id}: {e}", exc_info=True)
        
        try:
            project = Project.objects.get(id=project_id)
            project.status = ProjectStatus.ERROR
            project.error_message = str(e)
            project.save()
        except:
            pass
        
        # Retry on failure
        raise self.retry(exc=e, countdown=60)


@shared_task(bind=True, max_retries=3)
def run_valuation_calculation(self, project_id):
    """
    Run DCF and CCA valuation calculations.
    
    Args:
        project_id: ID of the Project
        
    Returns:
        dict with status and results
    """
    logger.info(f"Starting valuation calculation for project {project_id}")
    
    try:
        # Get project
        project = Project.objects.get(id=project_id)
        project.status = ProjectStatus.CALCULATING
        project.error_message = ''
        project.save()
        
        # Get financial data
        financial_data_qs = FinancialData.objects.filter(project=project)
        
        if not financial_data_qs.exists():
            raise ValueError("No financial data found for project")
        
        # Convert to dictionary format for engines
        financial_data = {}
        for data_point in financial_data_qs:
            if data_point.metric_name not in financial_data:
                financial_data[data_point.metric_name] = {}
            financial_data[data_point.metric_name][data_point.year] = float(data_point.value)
        
        logger.info(f"Loaded {len(financial_data)} metrics for calculation")
        
        # Get or create assumptions
        assumptions_obj, created = ValuationAssumptions.objects.get_or_create(project=project)
        
        # Calculate WACC
        wacc = assumptions_obj.calculate_wacc()
        
        # Convert assumptions to dictionary
        assumptions = {
            'wacc': wacc,
            'risk_free_rate': float(assumptions_obj.risk_free_rate),
            'equity_risk_premium': float(assumptions_obj.equity_risk_premium),
            'beta': float(assumptions_obj.beta),
            'size_premium': float(assumptions_obj.size_premium),
            'company_specific_premium': float(assumptions_obj.company_specific_premium),
            'cost_of_debt': float(assumptions_obj.cost_of_debt),
            'tax_rate': float(assumptions_obj.tax_rate),
            'debt_weight': float(assumptions_obj.debt_weight),
            'equity_weight': float(assumptions_obj.equity_weight),
            'terminal_growth_rate': float(assumptions_obj.terminal_growth_rate),
            'forecast_years': assumptions_obj.forecast_years,
            'mid_year_convention': assumptions_obj.mid_year_convention,
            'revenue_growth_rate': float(assumptions_obj.revenue_growth_rate),
            'ebitda_multiple_min': float(assumptions_obj.ebitda_multiple_min),
            'ebitda_multiple_median': float(assumptions_obj.ebitda_multiple_median),
            'ebitda_multiple_max': float(assumptions_obj.ebitda_multiple_max),
        }
        
        # Run DCF calculation
        logger.info("Running DCF calculation")
        dcf_engine = DCFEngine()
        dcf_results = dcf_engine.calculate_dcf(financial_data, assumptions)
        
        # Run CCA calculation
        logger.info("Running CCA calculation")
        cca_engine = CCAEngine()
        cca_results = cca_engine.calculate_cca(financial_data, assumptions)
        
        # Save results
        result, created = ValuationResult.objects.get_or_create(project=project)
        
        result.dcf_enterprise_value = dcf_results.get('enterprise_value')
        result.dcf_equity_value = dcf_results.get('equity_value')
        result.dcf_pv_forecast_fcf = dcf_results.get('pv_forecast_fcf')
        result.dcf_pv_terminal_value = dcf_results.get('pv_terminal_value')
        
        result.cca_equity_value_min = cca_results.get('equity_value_min')
        result.cca_equity_value_median = cca_results.get('equity_value_median')
        result.cca_equity_value_max = cca_results.get('equity_value_max')
        
        # Calculate concluded value (simple average of DCF and CCA median)
        dcf_equity = dcf_results.get('equity_value', 0)
        cca_equity = cca_results.get('equity_value_median', 0)
        result.concluded_equity_value = (dcf_equity + cca_equity) / 2 if (dcf_equity and cca_equity) else dcf_equity or cca_equity
        
        result.wacc_used = wacc
        result.save()
        
        # Update project status
        project.status = ProjectStatus.COMPLETE
        project.save()
        
        logger.info(f"Valuation calculation complete for project {project_id}")
        
        return {
            'status': 'success',
            'message': 'Valuation calculation complete',
            'dcf_equity_value': float(dcf_results.get('equity_value', 0)),
            'cca_equity_value_median': float(cca_results.get('equity_value_median', 0)),
            'concluded_equity_value': float(result.concluded_equity_value)
        }
        
    except Project.DoesNotExist:
        logger.error(f"Project {project_id} not found")
        return {'status': 'error', 'message': 'Project not found'}
        
    except Exception as e:
        logger.error(f"Error calculating valuation for project {project_id}: {e}", exc_info=True)
        
        try:
            project = Project.objects.get(id=project_id)
            project.status = ProjectStatus.ERROR
            project.error_message = str(e)
            project.save()
        except:
            pass
        
        # Retry on failure
        raise self.retry(exc=e, countdown=60)


@shared_task(bind=True, max_retries=3)
def generate_excel_report_task(self, project_id):
    """
    Generate Excel report with valuation results.
    
    Args:
        project_id: ID of the Project
        
    Returns:
        dict with status and file path
    """
    logger.info(f"Generating Excel report for project {project_id}")
    
    try:
        # Get project
        project = Project.objects.get(id=project_id)
        
        # Get financial data
        financial_data_qs = FinancialData.objects.filter(project=project)
        financial_data = {}
        for data_point in financial_data_qs:
            if data_point.metric_name not in financial_data:
                financial_data[data_point.metric_name] = {}
            financial_data[data_point.metric_name][data_point.year] = float(data_point.value)
        
        # Get assumptions
        assumptions_obj = ValuationAssumptions.objects.get(project=project)
        wacc = assumptions_obj.calculate_wacc()
        
        assumptions = {
            'wacc': wacc,
            'risk_free_rate': float(assumptions_obj.risk_free_rate),
            'equity_risk_premium': float(assumptions_obj.equity_risk_premium),
            'beta': float(assumptions_obj.beta),
            'size_premium': float(assumptions_obj.size_premium),
            'company_specific_premium': float(assumptions_obj.company_specific_premium),
            'cost_of_debt': float(assumptions_obj.cost_of_debt),
            'tax_rate': float(assumptions_obj.tax_rate),
            'debt_weight': float(assumptions_obj.debt_weight),
            'equity_weight': float(assumptions_obj.equity_weight),
            'terminal_growth_rate': float(assumptions_obj.terminal_growth_rate),
            'forecast_years': assumptions_obj.forecast_years,
            'mid_year_convention': assumptions_obj.mid_year_convention,
            'revenue_growth_rate': float(assumptions_obj.revenue_growth_rate),
            'ebitda_multiple_min': float(assumptions_obj.ebitda_multiple_min),
            'ebitda_multiple_median': float(assumptions_obj.ebitda_multiple_median),
            'ebitda_multiple_max': float(assumptions_obj.ebitda_multiple_max),
        }
        
        # Re-run calculations to get detailed results
        dcf_engine = DCFEngine()
        dcf_results = dcf_engine.calculate_dcf(financial_data, assumptions)
        
        cca_engine = CCAEngine()
        cca_results = cca_engine.calculate_cca(financial_data, assumptions)
        
        # Project data
        project_data = {
            'name': project.name,
            'client_name': project.client_name,
            'currency': project.currency,
        }
        
        # Generate Excel file
        from django.conf import settings
        
        output_filename = f"valuation_report_{project_id}.xlsx"
        output_dir = Path(settings.MEDIA_ROOT) / 'reports'
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / output_filename
        
        exporter = ExcelExporter()
        exporter.generate_valuation_excel(
            project_data=project_data,
            financial_data=financial_data,
            assumptions=assumptions,
            dcf_results=dcf_results,
            cca_results=cca_results,
            output_path=str(output_path)
        )
        
        # Save file reference to project
        with open(output_path, 'rb') as f:
            project.excel_report_path.save(output_filename, ContentFile(f.read()), save=True)
        
        logger.info(f"Excel report generated for project {project_id}: {output_path}")
        
        return {
            'status': 'success',
            'message': 'Excel report generated',
            'file_path': str(output_path)
        }
        
    except Exception as e:
        logger.error(f"Error generating Excel report for project {project_id}: {e}", exc_info=True)
        
        # Retry on failure
        raise self.retry(exc=e, countdown=60)
