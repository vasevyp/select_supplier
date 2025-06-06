from django.urls import path
from django.views.generic import TemplateView
from .views import *

urlpatterns = [
   path('login-a/', admin_login, name='login_a'),
    path('logout/', user_logout, name='logout'),
    path('register/', register_view, name='register'),
    path('login/', login_view, name='login'),
    path('profile/', profile_view, name='profile'),
    path('verification-sent/', TemplateView.as_view(template_name='users/verification_sent.html'), name='verification_sent'),
    path('verify-email/<str:token>/', verify_email, name='verify_email'),
]
