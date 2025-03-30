from django.urls import path
from . import views

app_name = 'reports'

urlpatterns = [
    # Existing URLs
    path('configurations/', views.report_configuration_list, name='report_configuration_list'),
    path('configurations/create/', views.create_report_configuration, name='create_report_configuration'),
    path('configurations/<int:pk>/edit/', views.edit_report_configuration, name='edit_report_configuration'),
    path('configurations/<int:pk>/delete/', views.delete_report_configuration, name='delete_report_configuration'),
    path('configurations/<int:pk>/sections/', views.edit_report_sections, name='edit_report_sections'),
    
    # AJAX endpoints
    path('assessment/<int:assessment_id>/sections/', views.get_assessment_sections, name='get_assessment_sections'),
    path('assessment/<int:assessment_id>/subcategories/', views.get_subcategories, name='get_subcategories'),
    path('configurations/<int:config_id>/cutoff/', views.manage_cutoff, name='manage_cutoff'),
    path('configurations/<int:config_id>/band/', views.manage_band, name='manage_band'),
    path('configurations/<int:config_id>/contrast-variable/', views.manage_contrast_variable, name='manage_contrast_variable'),
    path('configurations/<int:config_id>/type-band/', views.manage_type_band, name='manage_type_band'),
    
    # Report generation
    path('generate/<int:session_id>/', views.generate_report, name='generate_report'),
    path('generate/<int:session_id>/<int:config_id>/', views.generate_report, name='generate_report_with_config'),
    path('configurations/<int:config_id>/sample/', views.select_sample_session, name='select_sample_session'),
    path('configurations/<int:config_id>/reports/', views.list_generated_reports, name='list_generated_reports'),
    
    # Candidate selection for group reports
    path('load-candidates/', views.load_candidates, name='load_candidates'),
    
    # Bulk report generation
    path('configurations/<int:config_id>/select-sessions/', views.select_sessions, name='select_sessions'),
    path('configurations/<int:config_id>/generate-bulk/', views.generate_bulk_reports, name='generate_bulk_reports'),
    
    # Assessment booking and payment
    path('bookings/', views.assessment_booking_list, name='assessment_booking_list'),
    path('book/', views.book_assessment, name='book_assessment'),
    path('payment/<int:booking_id>/', views.assessment_payment, name='assessment_payment'),
    path('payment/callback/', views.payment_callback, name='payment_callback'),

    # # Report configuration
    # path('configurations/', views.report_configuration_list, name='report_configuration_list'),
    # path('configurations/create/', views.create_report_configuration, name='create_report_configuration'),
    # path('configurations/<int:pk>/edit/', views.edit_report_configuration, name='edit_report_configuration'),
    # path('configurations/<int:pk>/delete/', views.delete_report_configuration, name='delete_report_configuration'),
    # path('configurations/<int:pk>/sections/', views.edit_report_sections, name='edit_report_sections'),
    
    # # AJAX endpoints for managing sections/cutoffs/bands/contrast variables
    # path('assessment/<int:assessment_id>/sections/', views.get_assessment_sections, name='get_assessment_sections'),
    # path('configurations/<int:config_id>/cutoffs/', views.manage_cutoff, name='manage_cutoff'),
    # path('configurations/<int:config_id>/bands/', views.manage_band, name='manage_band'),
    # path('configurations/<int:config_id>/contrast-variables/', views.manage_contrast_variable, name='manage_contrast_variable'),
    
    # # Report generation
    # path('generate/<int:session_id>/', views.generate_report, name='generate_report'),
    # path('generate/<int:session_id>/<int:config_id>/', views.generate_report, name='generate_report_with_config'),
    
    # path('configurations/<int:config_id>/select-sample/', views.select_sample_session, name='select_sample_session'),
    # path('configurations/<int:config_id>/select-sessions/', views.select_sessions, name='select_sessions'),
    # path('configurations/<int:pk>/generated-reports/', views.list_generated_reports, name='list_generated_reports'),
    # path('generate-bulk/<int:pk>/', views.generate_bulk_reports, name='generate_bulk_reports'),
    
    # path('load-candidates/', views.load_candidates, name='load_candidates'),

    # path('get_subcategories/<int:assessment_id>/', views.get_subcategories, name='get_subcategories'),
    # path('manage_type_band/<int:config_id>/', views.manage_type_band, name='manage_type_band'),


    # # Assessment booking
    # path('bookings/', views.assessment_booking_list, name='assessment_booking_list'),
    # path('book-assessment/', views.book_assessment, name='book_assessment'),
    # path('bookings/<int:booking_id>/payment/', views.assessment_payment, name='assessment_payment'),
    # path('payment-callback/', views.payment_callback, name='payment_callback'),
]
