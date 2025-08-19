
from django.urls import path

from .views import first_page, primary, privacy_policy, tariffs_page, \
    info_page, supplier_search_demo, technology_search_demo, logistic_search_demo, \
        SupplierDemoDetailView, TechnologyDemoDetailView, LogisticDemoDetailView


urlpatterns = [
    path('', first_page, name='start'),
    path('main', primary, name='main'),
    path('policy', privacy_policy, name='policy'),
    path('tariffs/', tariffs_page, name='tariffs_page'),
    path('info-page', info_page, name='info_page'),
    path('supplier-search-demo', supplier_search_demo, name='supplier_search_demo'),
    path('technology-search-demo', technology_search_demo, name='technology_search_demo'),
    path('logistic-search-demo', logistic_search_demo, name='logistic_search_demo'),
    path('supplier-demo/<int:pk>/', SupplierDemoDetailView.as_view(), name='supplier_demo_detail'),
    path('techology-demo/<int:pk>/', TechnologyDemoDetailView.as_view(), name='technology_demo_detail'),
    path('logistic-demo/<int:pk>/', LogisticDemoDetailView.as_view(), name='logistic_demo_detail'),
   
]