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
from cjapp.converters import EmptyOrIntConverter

register_converter(EmptyOrIntConverter, 'int?')

urlpatterns = [
    # path('training/category/list', views.TrainingCategoryListView.as_view(), name='training_category_list'),
    # path('training/category/add', views.TrainingCategoryAddView.as_view(), name='training_category_add'),
    # path('training/category/edit/<int:pk>', views.TrainingCategoryEditView.as_view(), name='training_category_edit'),
    # path('training/booking/list', views.TrainingBookingListView.as_view(), name='training_booking_list'),
    # path('counselling/booking/add', views.counselling_booking_add_view, name='counselling_booking_add'),
    # path('counselling/booking/payment/<int:bookid>', views.counselling_booking_payment_view, name='counselling_booking_payment'),
    # path('counselling/booking/payment/submit', views.counselling_booking_payment_submit_view, name='counselling_booking_payment_submit'),
    # path('counselling/booking/cancel/<int:pk>', views.counselling_booking_cancel_view, name='counselling_booking_cancel'),
    # path('counselling/availability', views.counselling_availability_view, name='counselling_availability'),
    # path('counselling/availability/<date:date>', views.counselling_availability_view, name='counselling_availability_date'),
    # path('counselling/counsellors/category/<int:pk>', views.get_counsellors_by_category, name='counselling_counsellors_by_category'),
    # path('counselling/timeslots/<int:counsellor>', views.counselling_timeslots_view, name='counselling_timeslots'),
    
    path('notification/send', views.send_notification_view, name='send_notification'),
    path('notification/get', views.get_notifications_view, name='get_notifications'),
]
