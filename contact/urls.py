# contacts/urls.py
from django.urls import path
from .views import contact_view, ContactSuccessView

# app_name = 'contact'  # Добавляем пространство имен

urlpatterns = [
    path('', contact_view, name='contact'),
    path('success/', ContactSuccessView.as_view(), name='contact_success'),
]