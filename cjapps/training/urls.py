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
from django.urls import path, register_converter #, include
from . import views
# from .converters import DateConverter
from django.urls.converters import IntConverter

class EmptyOrIntConverter(IntConverter):
    regex = '[-a-zA-Z0-9_]*'

register_converter(EmptyOrIntConverter, 'int?')

urlpatterns = [
    path('training/category/list', views.TrainingCategoryListView.as_view(), name='training_category_list'),
    path('training/category/add', views.TrainingCategoryAddView.as_view(), name='training_category_add'),
    path('training/category/edit/<int:pk>', views.TrainingCategoryEditView.as_view(), name='training_category_edit'),
    path('training/category/delete/<int:pk>', views.TrainingCategoryDeleteView.as_view(), name='training_category_delete'),
    
    path('training/booking/list', views.TrainingBookingListView.as_view(), name='training_booking_list'),
    path('training/booking/add', views.training_booking_add_view, name='training_booking_add'),
    path('training/booking/category/<int?:category_id>', views.training_by_category_view, name='training_by_category_view'),
    
    path('training/booking/payment/<int:bookid>', views.training_booking_payment_view, name='training_booking_payment'),
    path('training/booking/payment/submit', views.training_booking_payment_submit_view, name='training_booking_payment_submit'),
    path('training/booking/cancel/<int:pk>', views.training_booking_cancel_view, name='training_booking_cancel'),
    
    path('training/add', views.training_create, name='training_add'), #TrainingCreate.as_view()
    path('training/edit/<int?:training_id>', views.training_edit, name='training_edit'),
    path('training/delete/<int?:training_id>', views.training_delete, name='training_delete'),
    path('training/list', views.TrainingListView.as_view(), name='training_list'),
    
    path('training/view/<int?:pk>', views.TrainingDetailView.as_view(), name='training_view'),

    # path('training/structure/<int:parent_id>/<str:type>/<str:name>', views.training_structure, name='training_structure'), #TrainingCreate.as_view()
    # path('training/structure/<int?:training_id>', views.training_structure_save, name='training_structure_save'), #TrainingCreate.as_view()
    # path('training/content/<int?:training_id>', views.training_content_save, name='training_content_save'), #TrainingCreate.as_view()
    path('training/assignment/<int?:training_id>', views.training_assignment_save, name='training_assignment_save'), #TrainingCreate.as_view()
    path('training/assignment/links/<int?:assignment_id>', views.training_assignment_links_save, name='training_assignment_links_save'), #TrainingCreate.as_view()
    path('training/session/<int?:training_id>', views.training_session_save, name='training_session_save'), #TrainingCreate.as_view()
    # path('training/zoom', views.zoom_meeting, name='zoom_meeting'),

    
    # path('training/content/create', views.training_content_save, name='training_content_save'), #TrainingCreate.as_view()
    
    path('training/structure/json', views.training_structure_json, name='training_structure_json'), #TrainingCreate.as_view()
    path('training/structure/actions/<str:mode>', views.training_structure_actions, name='training_structure_actions'), #TrainingCreate.as_view()
    
    path('training/delivery/<int?:booking_id>', views.training_delivery_view, name='training_delivery'), #TrainingCreate.as_view()
    # path('training/delivery/<int?:training_id>/<str:action>', views.training_delivery_action_view, name='training_delivery_action'), #TrainingCreate.as_view()

    path('training/livesession/initiate', views.initiate_livesession_view, name='initiate_livesession'), #TrainingCreate.as_view()
    path('training/livesession/schedule', views.schedule_livesession_view, name='schedule_livesession'), #TrainingCreate.as_view()
    path('training/assignment/submit', views.submit_assignment_report_view, name='submit_assignment_report'), #TrainingCreate.as_view()

    # notification side scheduling
    path('training/schedule', views.schedule_livesession_view, name='schedule_training'), #TrainingCreate.as_view()

    path('training/activate/<int?:training_id>', views.training_activate_view, name='training_activate'),
    path('training/information/<int?:training_id>', views.training_information_view, name='training_information'),
    
]
