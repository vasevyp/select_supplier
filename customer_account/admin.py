from django.contrib import admin

from .models import SearchResult

@admin.register(SearchResult)
class SearchResultAdmin(admin.ModelAdmin):
    # readonly_fields = ('name','website')
    list_display = ("user", "supplier_name", "supplier_email", "product", "created_at")
    search_fields = ("user__username", "supplier_name", "supplier_email", "product",)
    list_filter = ("user",  "product")
    save_on_top = True
    list_per_page = 20
