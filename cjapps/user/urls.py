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
from django.urls import path, include
from . import views

from django.contrib.auth.views import (
    # PasswordResetView,
    # PasswordResetDoneView,
    # PasswordResetConfirmView,
    # PasswordResetCompleteView,
    LoginView
)

urlpatterns = [
    path('', views.homepage_view, name='homepage'),
    path('user/', include('django.contrib.auth.urls')),
    path('user/login/', LoginView.as_view(), name='login'),
    # path('user/signup/', views.signup_view, name='signup'),
    path("user/register/", views.register_view, name="register"),
    path('user/verify-email-confirm/<uidb64>/<token>/', views.verify_email_confirm, name='verify-email-confirm'),

    path('user/verify-email/', views.verify_email, name='verify-email'),
    path('user/verify-email/done/', views.verify_email_done, name='verify-email-done'),
    path('user/verify-email/complete/', views.verify_email_complete, name='verify-email-complete'),

    path("user/dashboard/", views.dashboard_view, name="dashboard"),
    path("user/profile/", views.profile_view, name="profile"),
    path("user/profile/edit/", views.profile_edit_view, name="edit_profile"),
    path("user/profile/<int:id>", views.profile_single_view, name="profile_single"),
    path("user/password/change/", views.change_password_view, name="password_change"),

    path("user/list/", views.UserListView.as_view(), name="user_list"),
    path("user/add/", views.user_add_view, name="user_add"),
    path("user/<int:pk>/edit/", views.user_edit_view, name="user_edit"),
    path("user/<int:pk>/delete/", views.user_delete_view, name="user_delete"),

    path("group/list/", views.GroupListView.as_view(), name="group_list"),
    path("group/<int:pk>/edit/", views.group_desc_edit_view, name="group_edit"),

    path("user/import/", views.user_import_view, name="user_import"), #views.ImportUserView.as_view()
]
