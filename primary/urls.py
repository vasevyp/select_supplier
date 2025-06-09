
from django.urls import path

from .views import first_page, primary, privacy_policy


urlpatterns = [
    path('', first_page, name='start'),
    path('main', primary, name='main'),
    path('policy', privacy_policy, name='policy'),
   
]