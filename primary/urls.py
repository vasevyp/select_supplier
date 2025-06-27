
from django.urls import path

from .views import first_page, primary, privacy_policy, contact, tariffs_page, info_page, supplier_search_primary


urlpatterns = [
    path('', first_page, name='start'),
    path('main', primary, name='main'),
    path('policy', privacy_policy, name='policy'),
    path('contact', contact, name='contact'),
    path('tariffs/', tariffs_page, name='tariffs_page'),
    path('info-page', info_page, name='info_page'),
    path('supplier-search-primary', supplier_search_primary, name='supplier_search_primary'),
   
]