'''urls for supplier app'''
from django.urls import path

from . views import SupplierDetailView, supplier_selection, supplier_search, Category_list, Country_list, Supplier_list
from . upload import upload_excel, export_to_excel, supplier_delete


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
    path('upload-suppliers/', upload_excel, name='upload_suppliers'),
    path('search/', supplier_search, name='supplier_search'),
    path('export/', export_to_excel, name='export_to_excel'),
    path('delete/', supplier_delete, name='supplier_delete')
    
]
