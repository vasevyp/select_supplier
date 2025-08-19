'''urls for supplier app'''
from django.urls import path

from . views import SupplierDetailView, supplier_selection, Category_list, Country_list, Supplier_list,\
technology_selection, logistic_selection, TechnologyDetailView, LogisticDetailView
from . upload import upload_suppliers, upload_technology, upload_logistic, export_to_excel, supplier_delete


urlpatterns = [
    # path('supplier_upload', supplier_upload, name='supplier_upload'),
    # path('country_upload', country_upload, name='country_upload'),
    # path('category_upload', category_upload, name='category_upload'),
    path('supplier/<int:pk>/', SupplierDetailView.as_view(), name='supplier_detail'),
    # path("supplier/<int:pk>/", supplier_detail, name="supplier_detail"),
    path('supplier_selection', supplier_selection, name="supplier_selection"),
    path('category_list', Category_list.as_view(), name='category_list'),
    path('country_list', Country_list.as_view(), name='country_list'),
    path('supplier_list', Supplier_list.as_view(), name='supplier_list'),
    path('upload-suppliers/', upload_suppliers, name='upload_suppliers'),
    path('upload-technology/', upload_technology, name='upload_technology'),
    path('upload-logistic/', upload_logistic, name='upload_logistic'),
    path('export/', export_to_excel, name='export_to_excel'),
    path('delete/', supplier_delete, name='supplier_delete'),
    path('technology-selection', technology_selection, name='technology_selection'),
    path('logistic-selection', logistic_selection, name='logistic_selection'),
    path('techology/<int:pk>/', TechnologyDetailView.as_view(), name='technology_detail'),
    path('logistic/<int:pk>/', LogisticDetailView.as_view(), name='logistic_detail'),
    
]
