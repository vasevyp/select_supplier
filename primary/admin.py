from django.contrib import admin
from import_export.admin import ImportExportModelAdmin
from .models import SupplierDemo, TechnologyDemo, LogisticDemo


@admin.register(SupplierDemo)
class SupplierDemoAdmin(ImportExportModelAdmin):
    # readonly_fields = ('name','website')
    list_display = ("name", "country", "category", "index", "id","created_date")
    search_fields = ("name", "product", "product_ru")
    list_filter = ("country", "category")
    save_on_top = True
    list_per_page = 50


@admin.register(TechnologyDemo)
class TechnologyDemoAdmin(ImportExportModelAdmin):
    # readonly_fields = ('name','website')
    list_display = ("name", "country", "category", "index", "id","created_date")
    search_fields = ("name", "product", "product_ru")
    list_filter = ("country", "category")
    save_on_top = True
    list_per_page = 50


@admin.register(LogisticDemo)
class LogisticDemoAdmin(ImportExportModelAdmin):
    # readonly_fields = ('name','website')
    list_display = ("name", "country", "category", "index", "id","created_date")
    search_fields = ("name", "product", "product_ru")
    list_filter = ("country", "category")
    save_on_top = True
    list_per_page = 50

