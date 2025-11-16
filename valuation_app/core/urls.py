"""
URL configuration for core application.
"""

from django.urls import path
from . import views

urlpatterns = [
    # Dashboard
    path('', views.dashboard_view, name='dashboard'),
    
    # Project management
    path('project/create/', views.create_project_view, name='create_project'),
    path('project/<int:project_id>/', views.project_detail_view, name='project_detail'),
    path('project/<int:project_id>/delete/', views.delete_project_view, name='delete_project'),
    
    # Workflow views
    path('project/<int:project_id>/assumptions/', views.assumptions_input_view, name='assumptions_input'),
    path('project/<int:project_id>/results/', views.results_dashboard_view, name='results_dashboard'),
    path('project/<int:project_id>/financial-data/', views.financial_data_view, name='financial_data'),
    
    # Reports
    path('project/<int:project_id>/download/', views.download_excel_view, name='download_excel'),
    path('project/<int:project_id>/regenerate-report/', views.regenerate_report_view, name='regenerate_report'),
]
