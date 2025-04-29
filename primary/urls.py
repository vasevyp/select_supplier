
from django.urls import path

from .views import first_page, primary


urlpatterns = [
    path('', first_page, name='start'),
    path('main', primary, name='main'),
   
]