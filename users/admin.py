from django.contrib import admin

from .models import Profile 

@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    # readonly_fields = ('name','website')
    list_display = ("user", "company", "address", "phone")
    search_fields = ("user", "company")
    list_filter = ("user", "company")
    save_on_top = True
    list_per_page = 20

