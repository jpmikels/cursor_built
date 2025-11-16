"""
Django views for the core application.
"""

import logging
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import FileResponse, HttpResponse, Http404
from django.urls import reverse

from .models import Project, FinancialData, ValuationAssumptions, ValuationResult, ProjectStatus
from .forms import ProjectUploadForm, ValuationAssumptionsForm
from .tasks import process_financial_file, run_valuation_calculation, generate_excel_report_task

logger = logging.getLogger(__name__)


@login_required
def dashboard_view(request):
    """
    Main dashboard view showing all user's projects.
    """
    projects = Project.objects.filter(created_by=request.user).order_by('-created_at')
    
    context = {
        'projects': projects,
        'title': 'Dashboard'
    }
    
    return render(request, 'core/dashboard.html', context)


@login_required
def create_project_view(request):
    """
    View 1: Upload financial data file and create a new project.
    """
    if request.method == 'POST':
        form = ProjectUploadForm(request.POST, request.FILES, user=request.user)
        
        if form.is_valid():
            # Save project
            project = form.save()
            
            logger.info(f"Project {project.id} created by user {request.user.username}")
            
            # Trigger file processing task
            if project.uploaded_file:
                file_path = project.uploaded_file.path
                
                # Queue the Celery task
                process_financial_file.delay(project.id, file_path)
                
                messages.success(
                    request,
                    f'Project "{project.name}" created successfully. File processing started.'
                )
            else:
                messages.warning(request, 'Project created but no file was uploaded.')
            
            return redirect('project_detail', project_id=project.id)
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = ProjectUploadForm(user=request.user)
    
    context = {
        'form': form,
        'title': 'Create New Project'
    }
    
    return render(request, 'core/create_project.html', context)


@login_required
def project_detail_view(request, project_id):
    """
    View showing project details and status.
    """
    project = get_object_or_404(Project, id=project_id, created_by=request.user)
    
    # Get financial data count
    financial_data_count = FinancialData.objects.filter(project=project).count()
    
    # Get unique metrics and years
    financial_data = FinancialData.objects.filter(project=project).order_by('metric_name', 'year')
    metrics = financial_data.values_list('metric_name', flat=True).distinct()
    years = financial_data.values_list('year', flat=True).distinct().order_by('year')
    
    # Get assumptions (if exist)
    try:
        assumptions = ValuationAssumptions.objects.get(project=project)
    except ValuationAssumptions.DoesNotExist:
        assumptions = None
    
    # Get results (if exist)
    try:
        results = ValuationResult.objects.get(project=project)
    except ValuationResult.DoesNotExist:
        results = None
    
    context = {
        'project': project,
        'financial_data_count': financial_data_count,
        'metrics': list(metrics),
        'years': list(years),
        'assumptions': assumptions,
        'results': results,
        'title': f'Project: {project.name}'
    }
    
    return render(request, 'core/project_detail.html', context)


@login_required
def assumptions_input_view(request, project_id):
    """
    View 2: Input valuation assumptions.
    """
    project = get_object_or_404(Project, id=project_id, created_by=request.user)
    
    # Check if project is ready for assumptions
    if project.status not in [ProjectStatus.READY, ProjectStatus.COMPLETE]:
        messages.warning(request, 'Project is not ready for assumptions input yet.')
        return redirect('project_detail', project_id=project.id)
    
    # Get or create assumptions
    assumptions, created = ValuationAssumptions.objects.get_or_create(project=project)
    
    if request.method == 'POST':
        form = ValuationAssumptionsForm(request.POST, instance=assumptions)
        
        if form.is_valid():
            assumptions = form.save()
            
            logger.info(f"Assumptions saved for project {project.id}")
            
            messages.success(request, 'Assumptions saved successfully. Starting valuation calculation...')
            
            # Trigger valuation calculation task
            run_valuation_calculation.delay(project.id)
            
            return redirect('project_detail', project_id=project.id)
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = ValuationAssumptionsForm(instance=assumptions)
    
    # Calculate current WACC for display
    calculated_wacc = assumptions.calculate_wacc()
    
    context = {
        'form': form,
        'project': project,
        'assumptions': assumptions,
        'calculated_wacc': calculated_wacc,
        'title': f'Assumptions: {project.name}'
    }
    
    return render(request, 'core/assumptions_input.html', context)


@login_required
def results_dashboard_view(request, project_id):
    """
    View 3: Display valuation results dashboard.
    """
    project = get_object_or_404(Project, id=project_id, created_by=request.user)
    
    # Check if results are available
    if project.status != ProjectStatus.COMPLETE:
        messages.info(request, 'Valuation calculation is not complete yet.')
        return redirect('project_detail', project_id=project.id)
    
    # Get results
    try:
        results = ValuationResult.objects.get(project=project)
    except ValuationResult.DoesNotExist:
        messages.error(request, 'Valuation results not found.')
        return redirect('project_detail', project_id=project.id)
    
    # Get assumptions
    assumptions = ValuationAssumptions.objects.get(project=project)
    
    # Get some key financial data for context
    financial_data = {}
    for data_point in FinancialData.objects.filter(project=project):
        if data_point.metric_name not in financial_data:
            financial_data[data_point.metric_name] = {}
        financial_data[data_point.metric_name][data_point.year] = float(data_point.value)
    
    # Get latest year data
    latest_revenue = None
    latest_ebitda = None
    
    if 'revenue' in financial_data:
        years = sorted(financial_data['revenue'].keys())
        if years:
            latest_revenue = financial_data['revenue'][years[-1]]
    
    if 'ebitda' in financial_data:
        years = sorted(financial_data['ebitda'].keys())
        if years:
            latest_ebitda = financial_data['ebitda'][years[-1]]
    
    context = {
        'project': project,
        'results': results,
        'assumptions': assumptions,
        'latest_revenue': latest_revenue,
        'latest_ebitda': latest_ebitda,
        'title': f'Results: {project.name}'
    }
    
    return render(request, 'core/results_dashboard.html', context)


@login_required
def download_excel_view(request, project_id):
    """
    View: Download Excel report.
    """
    project = get_object_or_404(Project, id=project_id, created_by=request.user)
    
    # Check if report exists
    if project.excel_report_path and project.excel_report_path.name:
        try:
            # Serve the file
            response = FileResponse(
                project.excel_report_path.open('rb'),
                content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            )
            response['Content-Disposition'] = f'attachment; filename="valuation_report_{project.id}.xlsx"'
            
            logger.info(f"Excel report downloaded for project {project.id} by user {request.user.username}")
            
            return response
        except Exception as e:
            logger.error(f"Error serving Excel file for project {project.id}: {e}")
            messages.error(request, 'Error downloading report file.')
    else:
        # Report doesn't exist yet, trigger generation
        messages.info(request, 'Excel report is being generated. Please check back in a moment.')
        
        # Queue the Celery task
        generate_excel_report_task.delay(project.id)
    
    return redirect('project_detail', project_id=project.id)


@login_required
def regenerate_report_view(request, project_id):
    """
    View: Regenerate Excel report.
    """
    project = get_object_or_404(Project, id=project_id, created_by=request.user)
    
    if project.status != ProjectStatus.COMPLETE:
        messages.warning(request, 'Valuation must be complete before generating a report.')
        return redirect('project_detail', project_id=project.id)
    
    # Queue the Celery task
    generate_excel_report_task.delay(project.id)
    
    messages.info(request, 'Excel report generation started. It will be ready shortly.')
    
    return redirect('project_detail', project_id=project.id)


@login_required
def delete_project_view(request, project_id):
    """
    View: Delete a project.
    """
    project = get_object_or_404(Project, id=project_id, created_by=request.user)
    
    if request.method == 'POST':
        project_name = project.name
        project.delete()
        
        logger.info(f"Project {project_id} '{project_name}' deleted by user {request.user.username}")
        
        messages.success(request, f'Project "{project_name}" deleted successfully.')
        return redirect('dashboard')
    
    context = {
        'project': project,
        'title': f'Delete Project: {project.name}'
    }
    
    return render(request, 'core/delete_project.html', context)


@login_required
def financial_data_view(request, project_id):
    """
    View: Display financial data table.
    """
    project = get_object_or_404(Project, id=project_id, created_by=request.user)
    
    # Get financial data
    financial_data_qs = FinancialData.objects.filter(project=project).order_by('metric_name', 'year')
    
    # Organize data by metric
    data_by_metric = {}
    all_years = set()
    
    for data_point in financial_data_qs:
        if data_point.metric_name not in data_by_metric:
            data_by_metric[data_point.metric_name] = {}
        data_by_metric[data_point.metric_name][data_point.year] = float(data_point.value)
        all_years.add(data_point.year)
    
    years = sorted(list(all_years))
    
    # Create table data
    table_data = []
    for metric_name in sorted(data_by_metric.keys()):
        row = {'metric': metric_name, 'values': {}}
        for year in years:
            row['values'][year] = data_by_metric[metric_name].get(year, 0)
        table_data.append(row)
    
    context = {
        'project': project,
        'years': years,
        'table_data': table_data,
        'title': f'Financial Data: {project.name}'
    }
    
    return render(request, 'core/financial_data.html', context)
