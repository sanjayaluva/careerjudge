from django.urls import path
from . import views

app_name = 'question_bank'

urlpatterns = [
    path('question-bank/categories/', views.manage_categories, name='manage_categories'),
    path('question-bank/api/categories/', views.get_categories, name='get_categories'),
    path('question-bank/api/categories/update/', views.update_category, name='update_category'),
    path('question-bank/api/categories/create/', views.create_category, name='create_category'),
    path('question-bank/api/categories/delete/', views.delete_category, name='delete_category'),

    path('question-bank/questions/', views.question_list, name='question_list'),
    path('question-bank/questions/create/', views.create_question, name='create_question'),
    path('question-bank/questions/create/<int:task_id>/', views.create_question, name='create_question'),
    path('question-bank/questions/<int:pk>/', views.question_detail, name='question_detail'),
    path('question-bank/questions/<int:pk>/edit/', views.edit_question, name='edit_question'),
    path('question-bank/questions/<int:pk>/delete/', views.delete_question, name='delete_question'),

    path('question-bank/questions/get-rank-categories/', views.get_ranking_categories, name='get_rank_categories'),
    path('question-bank/questions/get-rank-groups/', views.get_ranking_groups, name='get_rank_groups'),

    path('fetch-jstree-data/', views.fetch_jstree_data, name='fetch_jstree_data'),  # Add this line
    path('ranking-question/', views.ranking_question_view, name='ranking_question'),
    path('create-category/', views.create_category, name='create_category'),
    path('create-subcategory/', views.create_subcategory, name='create_subcategory'),
    path('create-statement/', views.create_statement, name='create_statement'),
    path('create-rank-group/', views.create_rank_group, name='create_rank_group'),
    path('add-statement-to-rank-group/', views.add_statement_to_rank_group, name='add_statement_to_rank_group'),
]

urlpatterns += [
    path('request-deletion/', views.request_deletion, name='request_deletion'),
    path('review-deletion-request/<int:request_id>/', views.review_deletion_request, name='review_deletion_request'),
    path('deletion-requests/', views.deletion_requests_list, name='deletion_requests_list'),
]
