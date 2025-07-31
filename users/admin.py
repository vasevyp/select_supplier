from django.contrib import admin

from .models import Profile 

@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    # readonly_fields = ('name','website')
    list_display = ("user", "phone")
    search_fields = ("user__username",  "phone")
    list_filter = ("user",)
    save_on_top = True
    list_per_page = 20

