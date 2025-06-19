from django.contrib import admin

from .models import SeoKey

@admin.register(SeoKey)
class SeoKeyAdmin(admin.ModelAdmin):
    list_display = ("meta_keywords", "meta_description")
    search_fields = ("meta_keywords", "meta_description",)
    list_filter = ("meta_keywords", "meta_description")
    # save_on_top = True
    # list_per_page = 20
