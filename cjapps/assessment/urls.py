"""
URL configuration for cjproject project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.urls import path#, register_converter
from . import views

# from cjapp.converters import EmptyOrIntConverter
# register_converter(EmptyOrIntConverter, 'int?')

urlpatterns = [
    path('assessment/', views.assessment_list, name='assessment_list'),
    path('assessment/create/', views.assessment_create, name='assessment_create'),
    path('assessment/<int:pk>/update/', views.assessment_update, name='assessment_update'),
    path('assessment/<int:pk>/delete/', views.assessment_delete, name='assessment_delete'),
    path('assessment/<int:pk>/structure/', views.assessment_structure, name='assessment_structure'),
    
    path('assessment/question/search', views.search_questions, name='assessment_search_questions'),
    path('assessment/question/options/<int:pk>/', views.get_question_options, name='assessment_question_options'),
    path('assessment/question/<int:pk>/set-scores/', views.set_question_scores, name='assessment_question_set_scores'),
    
    path('assessment/take/<int:assessment_id>/', views.assessment_take, name='assessment_take'),
    path('assessment/api/session/<int:session_id>/save-answer/', views.save_question_response, name='assessment_save_answer'),
    path('assessment/api/session/<int:session_id>/control/', views.assessment_control, name='assessment_control'),
    path('assessment/api/session/<int:session_id>/question/<int:question_id>/', views.load_question, name='assessment_load_question'),
    path('assessment/api/session/<int:session_id>/resume/', views.resume_session, name='assessment_resume'),
    path('assessment/complete/<int:session_id>/', views.assessment_complete, name='assessment_complete'),

    # Validate assessment user answers
    path('assessment/session/<int:session_id>/validate/', views.validate_all_responses, name='validate_all_responses'),

]
