from django.contrib import admin


from import_export.admin import ImportExportModelAdmin
from .models import Country, Category, Supplier, CategoryTechnology, CategoryLogistic, Technology, Logistic


@admin.register(Country)
class CountryAdmin(ImportExportModelAdmin):
    list_display = ("country", "code", "mode", "index", "created_date")
    search_fields = ("country", "mode")
    ordering = (
        "mode",
        "country",
    )
    list_per_page = 20


@admin.register(Category)
class CategoryAdmin(ImportExportModelAdmin):
    list_display = ("category", "code", "index", "created_date")
    search_fields = ("category",)
    ordering = ("category",)
    list_per_page = 20

@admin.register(CategoryTechnology)
class CategoryTechnologyAdmin(ImportExportModelAdmin):
    list_display = ("category", "code", "index", "created_date")
    search_fields = ("category",)
    ordering = ("category",)
    list_per_page = 20
@admin.register(CategoryLogistic)
class CategoryLogisticAdmin(ImportExportModelAdmin):
    list_display = ("category", "code", "index", "created_date")
    search_fields = ("category",)
    ordering = ("category",)
    list_per_page = 20    

@admin.register(Supplier)
class SupplierAdmin(ImportExportModelAdmin):
    # readonly_fields = ('name','website')
    list_display = ("name", "country", "category", "index", "id","created_date")
    search_fields = ("name", "product", "product_ru")
    list_filter = ("country", "category")
    save_on_top = True
    list_per_page = 50

@admin.register(Technology)
class TechnologyAdmin(ImportExportModelAdmin):
    list_display = ("name", "country", "category", "index", "id","created_date")
    search_fields = ("name", "product", "product_ru")
    list_filter = ("country", "category")
    save_on_top = True
    list_per_page = 50

@admin.register(Logistic)
class LogisticAdmin(ImportExportModelAdmin):
    list_display = ("name", "country", "category", "index", "id","created_date")
    search_fields = ("name", "product", "product_ru")
    list_filter = ("country", "category")
    save_on_top = True
    list_per_page = 50        
