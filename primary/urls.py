
from django.urls import path

from .views import first_page, primary, privacy_policy, contact, supplier_selection_primary, tariffs_page, info_page


urlpatterns = [
    path('', first_page, name='start'),
    path('main', primary, name='main'),
    path('policy', privacy_policy, name='policy'),
    path('contact', contact, name='contact'),
    path('search/', supplier_selection_primary, name='search_primary'),
    path('tariffs/', tariffs_page, name='tariffs_page'),
    path('info-page', info_page, name='info_page'),
   
]