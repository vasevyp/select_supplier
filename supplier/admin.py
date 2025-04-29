from django.contrib import admin

from import_export.admin import ImportExportModelAdmin
from .models import Country, Category, Supplier

@admin.register(Country)
class CountryAdmin(ImportExportModelAdmin):
    list_display = ('index', 'code', 'country', 'mode')
    search_fields = ('country', 'mode')
    ordering = ('mode','country',)
    list_per_page = 20

  

@admin.register(Category)
class CategoryAdmin(ImportExportModelAdmin):
    list_display = ('code', 'category')
    search_fields = ('category',)
    ordering = ('category',)
    list_per_page = 20

@admin.register(Supplier)
class SupplierAdmin(ImportExportModelAdmin):
    # readonly_fields = ('name','website')
    list_display = ('name', 'website', 'country', 'category', 'id', 'index')
    search_fields = ('name', 'product', 'product_ru')
    list_filter = ('country', 'category')
    save_on_top = True
    # autocomplete_fields = ('country', 'category')
    list_per_page = 20
    
    fieldsets = (
        ('Основная информация', {
            'fields': (
                'country', 
                'category',
                'name', 
                'website',               
            )
        }),
       
        ('Описание и продукция (английский)', {
            'fields': (
                'description',
                'product',
            )
        }),
         ('Контактная информация', {
            'fields': ('contact',)
        }),
        ('Описание и продукция (русский)', {
            'fields': (
                'description_ru',
                'product_ru',
            )
        }),
    )

    # def get_queryset(self, request):
    #     return super().get_queryset(request).select_related('country', 'category')
